from fastapi.testclient import TestClient

from app import app


client = TestClient(app)


def test_get_weather_returns_mock_weather_for_da_nang() -> None:
    response = client.get("/weather/Da%20Nang")

    assert response.status_code == 200
    assert response.json() == {
        "city": "Da Nang",
        "temperature": 30,
        "condition": "Sunny",
    }


def test_get_weather_returns_404_for_unknown_city() -> None:
    response = client.get("/weather/Atlantis")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Weather data not found for city: Atlantis"
    }
