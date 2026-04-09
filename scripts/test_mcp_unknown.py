import pytest
from fastapi.testclient import TestClient
from tools.mcp_server import app

def test_unknown_mcp_tool():
    client = TestClient(app)
    response = client.post("/call_tool", json={"tool": "nonexistent_tool", "input": {}})
    # It should not crash the pipeline. It should return a graceful error dict.
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "Unknown tool" in data["error"] or "not found" in data["error"].lower()
    print("SUCCESS: Unknown tool returns a handled dict rather than 500 unhandled trace.")

if __name__ == "__main__":
    test_unknown_mcp_tool()
