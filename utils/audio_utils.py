import wave, struct, os
from pathlib import Path

def merge_wav_files(wav_paths: list, output_path: str, silence_ms: int = 300):
    """
    Concatenate multiple WAV files with short silence gaps between them.
    All inputs must be same format (24kHz, mono, 16-bit) — guaranteed by TTS tool.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 24000
    silence_samples = int(sample_rate * silence_ms / 1000)
    silence_bytes = struct.pack('<' + 'h' * silence_samples, *([0] * silence_samples))
    all_frames = b""
    for path in wav_paths:
        if not os.path.exists(path):
            continue
        with wave.open(path, 'rb') as wf:
            all_frames += wf.readframes(wf.getnframes())
        all_frames += silence_bytes
    
    if all_frames:
        with wave.open(output_path, 'wb') as out:
            out.setnchannels(1)
            out.setsampwidth(2)
            out.setframerate(sample_rate)
            out.writeframes(all_frames)
    return output_path

def generate_silence_wav(output_path: str, duration_seconds: float = 2.0):
    """Generate a silent WAV file. Used in mock mode."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    sample_rate = 24000
    num_samples = int(sample_rate * duration_seconds)
    with wave.open(output_path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack('<' + 'h' * num_samples, *([0] * num_samples)))
    return output_path
