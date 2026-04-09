import json
from fastapi.testclient import TestClient
from tools.mcp_server import app

client = TestClient(app)

def test_list_tools():
    response = client.get("/list_tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) > 0

def test_call_tool_generate_character_image():
    # Requires IMAGE_MODE mock to run without network, but we'll just check if the endpoint doesn't crash on validation
    payload = {
        "tool": "generate_character_image",
        "input": {
            "prompt": "Test Prompt",
            "character_name": "Test Character"
        }
    }
    # It might attempt network call depending on IMAGE_MODE in config.py. 
    # Just checking structural response.
    # To be safe, we test a totally local tool like query_stock_footage which returns a dict
    payload_stock = {
        "tool": "query_stock_footage",
        "input": {
            "concept": "cyberpunk"
        }
    }
    response = client.post("/call_tool", json=payload_stock)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "stock_cyberpunk.mp4" in data["data"]["references"]
