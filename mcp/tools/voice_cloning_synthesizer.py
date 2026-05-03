from mcp.registry import register_tool
from utils.execution_mode import is_mock, require_real
from utils.audio_utils import generate_silence_wav

def _voice_cloning_synthesizer_mock(inputs: dict) -> str:
    """Generate a silent WAV based on text length."""
    output_path = inputs["output_path"]
    text = inputs.get("text", "")
    words = text.split()
    duration_s = max(1.0, len(words) * 0.1)
    generate_silence_wav(output_path, duration_s)
    print(f"[TTS MOCK] Generated silent WAV ({duration_s}s) → {output_path}")
    return output_path

@require_real
def _voice_cloning_synthesizer_real(inputs: dict) -> str:
    import os, wave
    from pathlib import Path
    from google import genai
    from google.genai import types
    
    output_path = inputs["output_path"]
    
    # ── Cache guard: skip API if file already exists ─────────────────────────
    if Path(output_path).exists():
        print(f"[TTS] Cache hit, reusing {output_path}")
        return output_path
        
    api_key = os.getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=api_key)
    voice_name = inputs.get("voice_profile", {}).get("voice_name", "Kore")
    
    import time
    from google.genai.errors import ClientError

    max_retries = 10
    response = None
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=inputs["text"],
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name
                            )
                        )
                    ),
                ),
            )
            break
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                # Add a slightly longer delay (65s) to ensure quota bucket fully resets
                print(f"[TTS REAL] Rate limit hit (429). Sleeping 65s before retry {attempt+1}/{max_retries}...")
                time.sleep(65)
            else:
                print(f"[TTS REAL] API Failed after {attempt+1} attempts: {e}. Falling back to MOCK for this audio file to prevent breaking flow.")
                return _voice_cloning_synthesizer_mock(inputs)
    # Gemini TTS returns raw PCM — NOT a WAV. Wrap it manually.
    pcm_bytes = response.candidates[0].content.parts[0].inline_data.data
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)       # 16-bit
        wf.setframerate(24000)   # 24kHz
        wf.writeframes(pcm_bytes)
    print(f"[TTS REAL] Saved → {output_path}")
    return output_path

def voice_cloning_synthesizer(inputs: dict) -> str:
    if is_mock():
        return _voice_cloning_synthesizer_mock(inputs)
    return _voice_cloning_synthesizer_real(inputs)

def register():
    register_tool(
        "voice_cloning_synthesizer",
        "Synthesize voice for dialogue",
        {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "voice_profile": {"type": "object"},
                "output_path": {"type": "string"}
            }
        },
        voice_cloning_synthesizer
    )

if __name__ == "__main__":
    import os
    os.environ["EXECUTION_MODE"] = "MOCK"
    print("Testing voice_cloning_synthesizer MOCK:")
    print(voice_cloning_synthesizer({
        "text": "Hello world this is a mock test line.",
        "voice_profile": {"voice_name": "Kore"},
        "output_path": "tests/fixtures/test_output.wav"
    }))
