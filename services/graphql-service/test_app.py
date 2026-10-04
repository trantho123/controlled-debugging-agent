from pathlib import Path
from runpy import run_path

import httpx
from fastapi.testclient import TestClient

from app import app, get_weather_rest_client


weather_rest_path = Path(__file__).parents[1] / "weather-rest" / "app.py"
weather_rest_app = run_path(str(weather_rest_path))["app"]


def test_weather_query_returns_data_from_weather_rest_api() -> None:
    async def use_weather_rest_app():
        transport = httpx.ASGITransport(app=weather_rest_app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://weather-rest",
        ) as client:
            yield client

    app.dependency_overrides[get_weather_rest_client] = use_weather_rest_app

    try:
        response = TestClient(app).post(
            "/graphql",
            json={
                "query": """
                    query {
                        weather(city: "Da Nang") {
                            city
                            temperature
                            condition
                        }
                    }
                """
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "data": {
            "weather": {
                "city": "Da Nang",
                "temperature": 30,
                "condition": "Sunny",
            }
        }
    }
