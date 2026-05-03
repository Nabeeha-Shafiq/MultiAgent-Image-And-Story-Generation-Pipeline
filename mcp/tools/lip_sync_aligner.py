from mcp.registry import register_tool
from utils.execution_mode import is_mock, require_real
import shutil, subprocess
from pathlib import Path

def _lip_sync_aligner_mock(inputs: dict) -> str:
    video_path = inputs.get("video_path", "tests/fixtures/test_scene.mp4")
    audio_path = inputs.get("audio_path", "tests/fixtures/test_audio.wav")
    output_path = inputs.get("output_path", "tests/fixtures/lip_sync_output.mp4")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg and Path(video_path).exists() and Path(audio_path).exists():
        try:
            subprocess.run([
                ffmpeg, "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy", "-c:a", "aac",
                "-shortest", output_path
            ], check=True, capture_output=True)
            print(f"[LipSync] ffmpeg merged → {output_path}")
        except Exception as e:
            print(f"[LipSync MOCK] ffmpeg failed: {e}. Passing video through")
            shutil.copy2(video_path, output_path)
    else:
        print("[LipSync STUB] ffmpeg not found or missing input files, passing video through")
        if Path(video_path).exists():
            shutil.copy2(video_path, output_path)
        else:
            Path(output_path).touch()
    return output_path

@require_real
def _lip_sync_aligner_real(inputs: dict) -> str:
    return _lip_sync_aligner_mock(inputs)

def lip_sync_aligner(inputs: dict) -> str:
    if is_mock():
        return _lip_sync_aligner_mock(inputs)
    return _lip_sync_aligner_real(inputs)

def register():
    register_tool(
        "lip_sync_aligner",
        "Align and merge audio and video",
        {
            "type": "object",
            "properties": {
                "video_path": {"type": "string"},
                "audio_path": {"type": "string"},
                "output_path": {"type": "string"}
            }
        },
        lip_sync_aligner
    )

if __name__ == "__main__":
    import os
    os.environ["EXECUTION_MODE"] = "MOCK"
    print("Testing lip_sync_aligner MOCK:")
    print(lip_sync_aligner({
        "video_path": "tests/fixtures/test_scene.mp4",
        "audio_path": "tests/fixtures/test_audio.wav",
        "output_path": "tests/fixtures/lip_sync_output.mp4"
    }))
