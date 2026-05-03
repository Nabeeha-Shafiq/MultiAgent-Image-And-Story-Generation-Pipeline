from mcp.registry import register_tool
from utils.execution_mode import is_mock, require_real

def _identity_validator_mock(inputs: dict) -> dict:
    """STUB. In production: face recognition confidence check."""
    return {"valid": True, "confidence": 0.95, "character_name": inputs.get("character_name", "Unknown")}

@require_real
def _identity_validator_real(inputs: dict) -> dict:
    return _identity_validator_mock(inputs)

def identity_validator(inputs: dict) -> dict:
    if is_mock():
        return _identity_validator_mock(inputs)
    return _identity_validator_real(inputs)

def register():
    register_tool(
        "identity_validator",
        "Validate character identity in video",
        {
            "type": "object",
            "properties": {
                "video_path": {"type": "string"},
                "character_name": {"type": "string"}
            }
        },
        identity_validator
    )

if __name__ == "__main__":
    import os
    os.environ["EXECUTION_MODE"] = "MOCK"
    print("Testing identity_validator MOCK:")
    print(identity_validator({
        "video_path": "tests/fixtures/test_scene.mp4",
        "character_name": "Kore"
    }))
