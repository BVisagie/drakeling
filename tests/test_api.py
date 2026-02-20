"""Integration tests for the API endpoints."""
import pytest
import time
from pathlib import Path
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from drakeling.api.app import create_app
from drakeling.daemon.config import DrakelingConfig
from drakeling.storage.database import get_engine, get_session_factory, run_migrations
from drakeling.storage.models import CreatureStateRow


@pytest.fixture
async def app_and_client(tmp_path):
    """Create a test app with an in-memory-like SQLite DB and return (app, client)."""
    # Write an API token
    token = "test-token-12345"
    (tmp_path / "api_token").write_text(token)

    config = DrakelingConfig(dev_mode=True, allow_import=True)
    engine = get_engine(tmp_path)
    await run_migrations(engine)
    session_factory = get_session_factory(engine)

    app = create_app(
        config=config,
        session_factory=session_factory,
        data_dir=tmp_path,
    )
    # Provide a mock LLM that returns None (no provider configured)
    app.state.llm = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        client.headers["Authorization"] = f"Bearer {token}"
        yield app, client

    await engine.dispose()


class TestAuth:
    @pytest.mark.asyncio
    async def test_missing_token_returns_401(self, app_and_client):
        _, client = app_and_client
        resp = await client.get("/status", headers={"Authorization": ""})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_token_returns_401(self, app_and_client):
        _, client = app_and_client
        resp = await client.get(
            "/status", headers={"Authorization": "Bearer wrong-token"}
        )
        assert resp.status_code == 401


class TestBirth:
    @pytest.mark.asyncio
    async def test_birth_creates_creature(self, app_and_client):
        app, client = app_and_client
        resp = await client.post(
            "/birth", json={"colour": "gold", "name": "Ember"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Ember"
        assert data["colour"] == "gold"
        assert data["lifecycle_stage"] == "egg"

    @pytest.mark.asyncio
    async def test_duplicate_birth_returns_409(self, app_and_client):
        _, client = app_and_client
        await client.post("/birth", json={"colour": "red", "name": "Blaze"})
        resp = await client.post("/birth", json={"colour": "blue", "name": "Azure"})
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_invalid_colour_rejected(self, app_and_client):
        _, client = app_and_client
        resp = await client.post("/birth", json={"colour": "purple", "name": "Test"})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_name_rejected(self, app_and_client):
        _, client = app_and_client
        resp = await client.post("/birth", json={"colour": "red", "name": ""})
        assert resp.status_code == 422


class TestStatus:
    @pytest.mark.asyncio
    async def test_no_creature_returns_404(self, app_and_client):
        _, client = app_and_client
        resp = await client.get("/status")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_status_after_birth(self, app_and_client):
        _, client = app_and_client
        await client.post("/birth", json={"colour": "white", "name": "Frost"})
        resp = await client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Frost"
        assert data["colour"] == "white"
        assert data["lifecycle_stage"] == "egg"
        assert "mood" in data
        assert "budget_exhausted" in data


class TestCare:
    @pytest.mark.asyncio
    async def test_care_updates_stats(self, app_and_client):
        _, client = app_and_client
        await client.post("/birth", json={"colour": "green", "name": "Fern"})
        resp = await client.post("/care", json={"type": "gentle_attention"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"]["mood"] > 0.5  # boosted from 0.5
        assert data["state"]["loneliness"] == 0.0

    @pytest.mark.asyncio
    async def test_invalid_care_type(self, app_and_client):
        _, client = app_and_client
        await client.post("/birth", json={"colour": "red", "name": "Rex"})
        resp = await client.post("/care", json={"type": "hug"})
        assert resp.status_code == 422


class TestTalk:
    @pytest.mark.asyncio
    async def test_talk_forbidden_during_egg(self, app_and_client):
        _, client = app_and_client
        await client.post("/birth", json={"colour": "blue", "name": "Sky"})
        resp = await client.post("/talk", json={"message": "hello"})
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_talk_message_too_long(self, app_and_client):
        _, client = app_and_client
        await client.post("/birth", json={"colour": "red", "name": "Test"})
        resp = await client.post("/talk", json={"message": "x" * 501})
        assert resp.status_code == 422


class TestRest:
    @pytest.mark.asyncio
    async def test_rest_forbidden_during_egg(self, app_and_client):
        _, client = app_and_client
        await client.post("/birth", json={"colour": "gold", "name": "Test"})
        resp = await client.post("/rest", json={})
        assert resp.status_code == 409


class TestNeedsAttention:
    @pytest.mark.asyncio
    async def test_no_creature_returns_404(self, app_and_client):
        _, client = app_and_client
        resp = await client.get("/needs-attention")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_returns_structured_response(self, app_and_client):
        _, client = app_and_client
        await client.post("/birth", json={"colour": "red", "name": "Test"})
        resp = await client.get("/needs-attention")
        assert resp.status_code == 200
        data = resp.json()
        assert "needs_attention" in data
        assert "reason" in data
        assert "urgency" in data
