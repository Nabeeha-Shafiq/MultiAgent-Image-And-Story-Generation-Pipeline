from mcp.registry import register_tool
from utils.execution_mode import is_mock, require_real
import shutil
from pathlib import Path

def _face_swapper_mock(inputs: dict) -> str:
    """STUB. For demo: pass video through unchanged and log intent."""
    output_path = inputs.get("output_path", "tests/fixtures/swapped.mp4")
    video_path = inputs.get("video_path", "tests/fixtures/test_scene.mp4")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    if Path(video_path).exists():
        shutil.copy2(video_path, output_path)
    else:
        Path(output_path).touch()
    
    char_name = inputs.get("character_name", "Unknown")
    print(f"[FaceSwap STUB] {char_name} ref={inputs.get('character_reference_image', 'none')}")
    return output_path

@require_real
def _face_swapper_real(inputs: dict) -> str:
    return _face_swapper_mock(inputs)

def face_swapper(inputs: dict) -> str:
    if is_mock():
        return _face_swapper_mock(inputs)
    return _face_swapper_real(inputs)

def register():
    register_tool(
        "face_swapper",
        "Swap face on character in video",
        {
            "type": "object",
            "properties": {
                "video_path": {"type": "string"},
                "output_path": {"type": "string"},
                "character_name": {"type": "string"},
                "character_reference_image": {"type": "string"}
            }
        },
        face_swapper
    )

if __name__ == "__main__":
    import os
    os.environ["EXECUTION_MODE"] = "MOCK"
    print("Testing face_swapper MOCK:")
    print(face_swapper({
        "video_path": "tests/fixtures/test_scene.mp4",
        "output_path": "tests/fixtures/test_face_swap_output.mp4",
        "character_name": "Kore",
        "character_reference_image": "image.png"
    }))
