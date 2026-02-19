from __future__ import annotations

import argparse
import asyncio
import sys

import uvicorn

from openclaw_hatchling.crypto.token import ensure_api_token
from openclaw_hatchling.daemon.config import HatchlingConfig, load_dotenv_from_data_dir
from openclaw_hatchling.daemon.startup import check_machine_binding
from openclaw_hatchling.storage.database import get_engine, get_session_factory, init_db
from openclaw_hatchling.storage.paths import get_data_dir


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="openclaw-hatchlingd",
        description="OpenClaw Hatchling daemon",
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


async def _startup() -> None:
    args = _parse_args()
    data_dir = get_data_dir()

    load_dotenv_from_data_dir(data_dir)
    config = HatchlingConfig.from_env(
        dev_mode=args.dev,
        allow_import=args.allow_import or args.dev,
    )

    api_token = ensure_api_token(data_dir)

    engine = get_engine(data_dir)
    await init_db(engine)
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
        else:
            print(
                "WARNING: No LLM provider configured. "
                "Set HATCHLING_LLM_BASE_URL or HATCHLING_USE_OPENCLAW_GATEWAY=true.",
                file=sys.stderr,
            )

    # Set up LLM wrapper
    from openclaw_hatchling.llm.wrapper import LLMWrapper

    llm = LLMWrapper(config)

    async def _on_budget_exhausted():
        """Transition creature to exhausted stage when daily budget runs out."""
        import time as _t
        from sqlalchemy import select as _sel
        from openclaw_hatchling.storage.models import CreatureStateRow as _CSR
        from openclaw_hatchling.storage.models import LifecycleEventRow as _LER
        from openclaw_hatchling.domain.models import LifecycleStage as _LS

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
    from openclaw_hatchling.api.app import create_app

    app = create_app(
        config=config,
        session_factory=session_factory,
        data_dir=data_dir,
    )
    app.state.llm = llm

    # Start background tick loop
    from openclaw_hatchling.daemon.tick import start_tick_loop

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
