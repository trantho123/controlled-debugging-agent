import json
from contextlib import asynccontextmanager
from pathlib import Path
from runpy import run_path

import httpx
import pytest
from mcp import Client

import app as mcp_app


EXPECTED_WEATHER = {
    "city": "Da Nang",
    "temperature": 30,
    "condition": "Sunny",
}


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_get_weather_tool_calls_graphql(monkeypatch: pytest.MonkeyPatch) -> None:
    requests: list[httpx.Request] = []

    def graphql_response(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={"data": {"weather": EXPECTED_WEATHER}},
        )

    @asynccontextmanager
    async def use_graphql_stub():
        transport = httpx.MockTransport(graphql_response)
        async with httpx.AsyncClient(transport=transport) as client:
            yield client

    monkeypatch.setattr(mcp_app, "get_graphql_client", use_graphql_stub)

    async with Client(mcp_app.mcp) as client:
        result = await client.call_tool("get_weather", {"city": "Da Nang"})

    assert result.is_error is False
    assert result.structured_content == EXPECTED_WEATHER
    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert requests[0].url.path == "/graphql"
    assert json.loads(requests[0].content) == {
        "query": mcp_app.GET_WEATHER_QUERY,
        "variables": {"city": "Da Nang"},
    }


@pytest.mark.anyio
async def test_get_weather_end_to_end(monkeypatch: pytest.MonkeyPatch) -> None:
    services_path = Path(__file__).parents[1]
    weather_rest_module = run_path(str(services_path / "weather-rest" / "app.py"))
    graphql_module = run_path(str(services_path / "graphql-service" / "app.py"))

    weather_rest_app = weather_rest_module["app"]
    graphql_app = graphql_module["app"]
    graphql_weather_client = graphql_module["get_weather_rest_client"]

    async def use_weather_rest_app():
        transport = httpx.ASGITransport(app=weather_rest_app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://weather-rest",
        ) as client:
            yield client

    @asynccontextmanager
    async def use_graphql_app():
        transport = httpx.ASGITransport(app=graphql_app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://graphql-service",
        ) as client:
            yield client

    graphql_app.dependency_overrides[graphql_weather_client] = use_weather_rest_app
    monkeypatch.setattr(mcp_app, "get_graphql_client", use_graphql_app)

    try:
        async with Client(mcp_app.mcp) as client:
            result = await client.call_tool("get_weather", {"city": "Da Nang"})
    finally:
        graphql_app.dependency_overrides.clear()

    assert result.is_error is False
    assert result.structured_content == EXPECTED_WEATHER
