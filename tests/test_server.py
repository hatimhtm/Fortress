"""Tests for fortress.server (FastAPI app)."""

import pytest

fastapi = pytest.importorskip("fastapi")
TestClient = pytest.importorskip("fastapi.testclient").TestClient

from fortress.server import create_app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(create_app())


class TestHealthz:
    def test_returns_ok(self, client):
        response = client.get("/healthz")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestGenerate:
    def test_default(self, client):
        response = client.post("/v1/generate")
        assert response.status_code == 200
        body = response.json()
        assert len(body["password"]) == 20
        assert body["entropy_bits"] > 100
        assert body["strength"] in {"Strong", "Very Strong", "Excellent"}

    def test_custom_length(self, client):
        response = client.post("/v1/generate?length=64")
        assert response.status_code == 200
        assert len(response.json()["password"]) == 64

    def test_invalid_length_returns_422(self, client):
        response = client.post("/v1/generate?length=0")
        assert response.status_code == 422


class TestPassphrase:
    def test_default(self, client):
        response = client.post("/v1/passphrase")
        assert response.status_code == 200
        body = response.json()
        assert len(body["passphrase"].split("-")) == 6
        assert body["entropy_bits"] > 70

    def test_words_must_be_positive(self, client):
        response = client.post("/v1/passphrase?words=0")
        assert response.status_code == 422


class TestPin:
    def test_default(self, client):
        response = client.post("/v1/pin")
        assert response.status_code == 200
        body = response.json()
        assert len(body["pin"]) == 6 and body["pin"].isdigit()

    def test_invalid_length(self, client):
        response = client.post("/v1/pin?length=100")
        assert response.status_code == 422


class TestCheck:
    def test_common_password_flagged(self, client):
        response = client.post("/v1/check", json={"password": "password"})
        assert response.status_code == 200
        body = response.json()
        assert body["is_common"] is True

    def test_random_password_not_flagged(self, client):
        response = client.post(
            "/v1/check",
            json={"password": "M^vT8L#qXz4!nP9w"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["is_common"] is False
        assert body["entropy_bits"] > 80

    def test_pwned_lookup_disabled_by_default(self, client):
        response = client.post("/v1/check", json={"password": "z9p$L"})
        body = response.json()
        assert body["pwned_count"] is None
        assert body["pwned_error"] is None
