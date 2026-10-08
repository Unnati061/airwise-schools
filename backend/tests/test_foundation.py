from fastapi.testclient import TestClient

from backend.app.main import app, handler
from backend.app.solver_smoke import run_smoke

client = TestClient(app)


def test_health_and_synthetic_school():
    assert client.get("/health").json() == {
        "status": "ok", "service": "airwise-schools", "data_mode": "SYNTHETIC"
    }
    school = client.get("/school").json()
    assert school["mode"] == "SYNTHETIC"
    assert len({section["id"] for section in school["sections"]}) == 6
    assert all(section["size"] > 0 for section in school["sections"])


def test_solver_native_execution():
    result = run_smoke()
    assert result["status"] == "OPTIMAL"
    assert sorted(result["periods"]) == [1, 2, 3]
    assert result["objective"] == 6


def test_lambda_adapter_health():
    event = {
        "version": "2.0", "routeKey": "GET /health", "rawPath": "/health",
        "rawQueryString": "", "headers": {"host": "localhost"},
        "requestContext": {"http": {"method": "GET", "path": "/health",
                                    "sourceIp": "127.0.0.1", "protocol": "HTTP/1.1"}},
        "isBase64Encoded": False,
    }
    assert handler(event, {})["statusCode"] == 200
