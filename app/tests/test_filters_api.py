from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


client = TestClient(app)


def test_create_filter_normalizes_stack():
    payload = {
        "level": "Junior",
        "stack": ["Python", " fastapi ", "Python"],
        "source": "DOU",
        "discord_webhook": "https://discord.com/api/webhooks/test/test",
        "active": True,
    }

    response = client.post(
        "/filters/",
        json=payload,
        headers={"x-api-key": settings.api_key},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["level"] == "junior"
    assert data["stack"] == ["fastapi", "python"]
    assert data["source"] == "dou"
    assert data["discord_webhook"] == payload["discord_webhook"]
    assert data["active"] is True
    assert "_id" in data or "id" in data