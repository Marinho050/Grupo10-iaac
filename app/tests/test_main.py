from fastapi.testclient import TestClient
import pytest

from app.main import app


@pytest.fixture
def test_client():
    return TestClient(app)


def test_health_endpoint(test_client):
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == ["ok"]


def test_predict_benign(test_client):
    # conexão típica benigna (poucos logins falhados, pacote pequeno)
    input_data = {
        "Protocol": "TCP",
        "Packet_Size_Bytes": 357,
        "Connection_Duration_ms": 69,
        "Failed_Logins": 0,
        "Geo_Distance_km": 359,
    }

    response = test_client.post("/predict", json=input_data)

    assert response.status_code == 200
    body = response.json()
    assert body["predict"] in (0, 1)
    assert isinstance(body["predict_prob"], float)
    assert 0.0 <= body["predict_prob"] <= 1.0


def test_predict_likely_malicious(test_client):
    # muitos logins falhados => sinal muito forte de conexão maliciosa (ver EDA)
    input_data = {
        "Protocol": "ICMP",
        "Packet_Size_Bytes": 6121,
        "Connection_Duration_ms": 45,
        "Failed_Logins": 5,
        "Geo_Distance_km": 1044,
    }

    response = test_client.post("/predict", json=input_data)

    assert response.status_code == 200
    body = response.json()
    assert body["predict"] == 1
    assert body["predict_prob"] > 0.5
