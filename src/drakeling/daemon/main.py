from __future__ import annotations

import argparse
import asyncio
import sys

import uvicorn

import platform

from drakeling.crypto.token import ensure_api_token
from drakeling.daemon.config import DrakelingConfig, load_dotenv_from_data_dir
from drakeling.daemon.setup import check_llm_setup
from drakeling.daemon.startup import check_machine_binding
from drakeling.storage.database import get_engine, get_session_factory, run_migrations
from drakeling.storage.paths import get_data_dir


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="drakelingd",
        description="Drakeling daemon",
    )
    parser.add_argument(
        "--dev", action="store_true",
        help="Development mode: verbose logging, no background reflection",
    )
    parser.add_argument(
        "--allow-import", action="store_true",
        help="Enable the POST /import endpoint for creature relocation",
    )
    return parser.parse_args()


def _print_token_info(token_path, token: str) -> None:
    """Print API token and location on first run."""
    path_str = str(token_path)
    if platform.system() == "Windows":
        view_cmd = f'type "{path_str}"'
    else:
        view_cmd = f'cat "{path_str}"'
    print(
        "\n"
        "  API token created:\n"
        f"    {token}\n"
        "\n"
        "  Saved to: " + path_str + "\n"
        "  To view later: " + view_cmd + "\n"
        "\n"
        "  The drakeling TUI reads this automatically.\n"
        "  For OpenClaw Skill, add it to ~/.openclaw/openclaw.json\n",
        file=sys.stderr,
    )


async def _startup() -> None:
    args = _parse_args()
    data_dir = get_data_dir()

    load_dotenv_from_data_dir(data_dir)
    config = DrakelingConfig.from_env(
        dev_mode=args.dev,
        allow_import=args.allow_import or args.dev,
    )

    check_llm_setup(config, data_dir)

    api_token, token_just_created = ensure_api_token(data_dir)
    token_path = data_dir / "api_token"

    if token_just_created and not config.dev_mode:
        _print_token_info(token_path, api_token)

    engine = get_engine(data_dir)
    await run_migrations(engine)
    session_factory = get_session_factory(engine)

    async with session_factory() as session:
        await check_machine_binding(data_dir, session)

    if config.dev_mode:
        print(f"[dev] Data directory: {data_dir}")
        print(f"[dev] API token: {api_token}")
        if config.use_openclaw_gateway:
            print(f"[dev] LLM mode: OpenClaw gateway at {config.openclaw_gateway_url}")
        elif config.llm_base_url:
            print(f"[dev] LLM mode: direct provider at {config.llm_base_url}")
        else:
            print("[dev] LLM mode: not configured (LLM calls will fail)")
    else:
        if config.use_openclaw_gateway:
            print(f"LLM mode: OpenClaw gateway ({config.openclaw_gateway_url})")
        elif config.llm_base_url:
            print(f"LLM mode: direct provider ({config.llm_base_url})")

    # Set up LLM wrapper
    from drakeling.llm.wrapper import LLMWrapper

    llm = LLMWrapper(config)

    async def _on_budget_exhausted():
        """Transition creature to exhausted stage when daily budget runs out."""
        import time as _t
        from sqlalchemy import select as _sel
        from drakeling.storage.models import CreatureStateRow as _CSR
        from drakeling.storage.models import LifecycleEventRow as _LER
        from drakeling.domain.models import LifecycleStage as _LS

        async with session_factory() as sess:
            res = await sess.execute(_sel(_CSR).limit(1))
            row = res.scalar_one_or_none()
            if row is None or row.lifecycle_stage == _LS.EXHAUSTED.value:
                return
            now = _t.time()
            row.pre_exhausted_stage = row.lifecycle_stage
            row.lifecycle_stage = _LS.EXHAUSTED.value
            row.updated_at = now
            sess.add(_LER(
                created_at=now,
                event_type="budget_exhausted",
                from_stage=row.pre_exhausted_stage,
                to_stage=_LS.EXHAUSTED.value,
            ))
            await sess.commit()
            if config.dev_mode:
                print(f"[dev] Budget exhausted — entering exhausted stage")

    llm.set_budget_exhausted_callback(_on_budget_exhausted)

    if config.use_openclaw_gateway:
        reachable = await llm.health_check()
        if not reachable:
            print(
                "WARNING: OpenClaw gateway is unreachable. "
                "LLM calls will fail until it becomes available.",
                file=sys.stderr,
            )

    # Import here to avoid circular deps at module level
    from drakeling.api.app import create_app

    app = create_app(
        config=config,
        session_factory=session_factory,
        data_dir=data_dir,
    )
    app.state.llm = llm

    # Start background tick loop
    from drakeling.daemon.tick import start_tick_loop

    tick_task = asyncio.create_task(
        start_tick_loop(session_factory, config, llm)
    )

    server_config = uvicorn.Config(
        app,
        host="127.0.0.1",
        port=config.port,
        log_level="info" if config.dev_mode else "warning",
    )
    server = uvicorn.Server(server_config)
    print("Drakeling daemon ready. In another terminal, run: drakeling")
    try:
        await server.serve()
    finally:
        tick_task.cancel()
        await llm.close()


def main() -> None:
    try:
        asyncio.run(_startup())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
