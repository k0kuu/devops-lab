from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_does_not_require_database():
    assert client.get("/health").status_code == 200

def test_metrics_observe_server_error():
    assert client.get("/fail").status_code == 500
    metrics = client.get("/metrics").text
    assert 'route="/fail",status="500"' in metrics

def test_reject_empty_item_before_database_access():
    assert client.post("/items", json={"name": ""}).status_code == 422

def test_database_round_trip():
    assert client.get("/ready").status_code == 200
    created = client.post("/items", json={"name": "ci-item"})
    assert created.status_code == 201
    item = created.json()
    assert item in client.get("/items").json()
    assert client.delete(f"/items/{item['id']}").status_code == 200
