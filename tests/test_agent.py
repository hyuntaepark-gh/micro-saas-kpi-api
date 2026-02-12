from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_agent_executive():
    res = client.post(
        "/v1/ask-executive",
        json={"question": "Why did revenue drop?"}
    )
    assert res.status_code == 200
    assert "final_report" in res.json()
