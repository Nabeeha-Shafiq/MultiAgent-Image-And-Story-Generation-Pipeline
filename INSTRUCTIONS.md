INSTRUCTIONS FOR ANTIGRAVITY — PROJECT MONTAGE PHASE 2
The Studio Floor: Video and Audio Synthesis Layer

VENV IS ALREADY CREATED IN THE PROJECT ROOT USE VENV THROUGHOUT

⚠️ GOLDEN RULE — READ THIS BEFORE WRITING A SINGLE LINE OF CODE
Every API call to Gemini TTS or Wan video generation costs real quota. You are working under extreme quota constraints. The guiding principle for this entire implementation is:

MOCK FIRST. STUB ALWAYS. REAL API ONLY WHEN THE GRADER IS WATCHING.

You must follow this hierarchy for every agent and tool you build:

TIER 1 — ALWAYS BUILD THIS FIRST (zero cost):

  Mock / stub path — returns hardcoded or file-fixture output

  Run ALL architecture, graph, and integration tests at this tier

TIER 2 — BUILD AFTER MOCKS PASS (minimal cost):

  Single-call smoke test against real API (1 dialogue line, 1 scene, shortest duration)

  Only triggered manually via --real flag, never by default

TIER 3 — FINAL DEMO ONLY (spend quota wisely):

  Full pipeline run on real API, using the rolling model strategy below

Default behavior of main.py must always be MOCK MODE. Real API calls must require an explicit flag: python main.py --real


0. CONTEXT
This is Phase 2 of CS-4015 Agentic AI (FAST-NUCES). Phase 1 is complete and produces these files which Phase 2 consumes:

outputs/

  scene_manifest.json     ← structured screenplay

  character_db.json       ← character identities + voice profiles

  image_assets/           ← AI-generated character reference images

Phase 2 must produce:

outputs/

  raw_scenes/             ← generated .mp4 files per scene

  audio/                  ← .wav files per dialogue line + merged per scene

  task_graph_logs/        ← JSON logs of task graphs and Wan task IDs


1. TECH STACK
Concern
Library
Orchestration
langgraph (StateGraph)
Voice synthesis
Google Gemini TTS via google-generativeai SDK
Video synthesis
Alibaba Cloud Wan via dashscope SDK (≥1.25.8)
Memory
ChromaDB (reuse Phase 1 collection)
Lip sync
ffmpeg (audio merge) + Wav2Lip stub
Face swap
Documented stub
Audio wrapping
Python stdlib wave module (no extra library)
HTTP
httpx
Env vars
python-dotenv



2. ENVIRONMENT VARIABLES (.env)
# ─── Google Gemini ─────────────────────────────────────────────────────────────

GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY_HERE

# ─── Alibaba Cloud DashScope ───────────────────────────────────────────────────

DASHSCOPE_API_KEY=YOUR_DASHSCOPE_API_KEY_HERE

DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/api/v1

# ─── Wan Video Model (rolling — see Section 3) ────────────────────────────────

# DO NOT hardcode model names in agent code. Read from this env var ONLY.

WAN_VIDEO_MODEL=wan2.1-t2v

# ─── ChromaDB ─────────────────────────────────────────────────────────────────

CHROMA_PERSIST_DIR=./chroma_db

# ─── Output dirs ──────────────────────────────────────────────────────────────

OUTPUT_DIR=./outputs

RAW_SCENES_DIR=./outputs/raw_scenes

AUDIO_DIR=./outputs/audio

TASK_LOG_DIR=./outputs/task_graph_logs

# ─── Execution mode ───────────────────────────────────────────────────────────

# MOCK = no real API calls (default, safe for development)

# REAL  = live API calls (use ONLY when explicitly needed)

EXECUTION_MODE=MOCK


3. WAN VIDEO MODEL — ROLLING TIER STRATEGY (CRITICAL)
The Wan text-to-video free quota is limited. Models are tiered by quality and cost. Always start from TIER 1 and only move up when you have exhausted that model's quota or when you need final demo quality.

┌──────────────────────────────────────────────────────────────────────┐

│  TIER  │  Model ID      │ Free Quota │ Duration  │ When to Use       │

├────────┼────────────────┼────────────┼───────────┼───────────────────┤

│   1    │ wan2.1-t2v     │ ~200 tokens│ shortest  │ ALL development   │

│        │ (LOWEST cost)  │            │ (3s clips)│ & arch testing    │

├────────┼────────────────┼────────────┼───────────┼───────────────────┤

│   2    │ wan2.5-t2v     │ ~100 tokens│ up to 5s  │ Integration tests │

│        │ (MID quality)  │            │           │ once arch is done │

├────────┼────────────────┼────────────┼───────────┼───────────────────┤

│   3    │ wan2.7-t2v     │ ~50 tokens │ up to 10s │ FINAL DEMO ONLY   │

│        │ (HIGHEST)      │            │           │ Do not touch until│

│        │                │            │           │ submission day    │

└──────────────────────────────────────────────────────────────────────┘

1 token = 1 second of generated video
Implementation Rule — Model Selection Must Be Dynamic
The model name MUST be read from WAN_VIDEO_MODEL env var. Never hardcode it.

# In mcp/tools/query_stock_footage.py — CORRECT pattern

model = os.getenv("WAN_VIDEO_MODEL", "wan2.1-t2v")   # safe default = cheapest

# WRONG — never do this:

model = "wan2.7-t2v"   # ← hardcoded, violates assignment MCP constraint AND wastes quota
Quota Protection Rules — Enforce These in Code
Shortest possible duration first: For Tier 1 and Tier 2, always request minimum duration (3 seconds). Only request longer durations (5–10s) on Tier 3.

480P resolution for Tier 1 and 2: Only use 720P on Tier 3 final run.

One scene at a time during testing: The --real flag should default to processing only scene_01. To process all scenes: --real --all-scenes.

Save task_id immediately on submission (before polling): Write task_graph_logs/scene_XX_wan_task.json the moment the POST returns a task_id. If the process crashes during the 3–5 minute polling window, the next run MUST detect existing task IDs and resume polling instead of resubmitting.

Never retry a failed video generation automatically. Log the failure, skip that scene, continue with others. Manual retry only.

Prompt length for Tier 1: Keep prompts under 100 characters for Tier 1 test calls. Save detailed cinematic prompts for Tier 3.
Model Switching Procedure
When Tier 1 quota is exhausted:

# In .env, change:

WAN_VIDEO_MODEL=wan2.5-t2v

When Tier 2 quota is exhausted:

WAN_VIDEO_MODEL=wan2.7-t2v

No code changes needed. The env var swap is the only action required.


4. GEMINI TTS — QUOTA RULES
Gemini TTS is cheaper than video generation but still has limits. Rules:

Mock first: In EXECUTION_MODE=MOCK, voice_cloning_synthesizer must generate a real-but-silent WAV file using Python wave module (2 seconds, 24kHz, silence). This is free and lets the pipeline test audio path end-to-end.

For real calls: Use gemini-2.5-flash-tts (not Pro). Flash = cheaper.

Cache audio output: Before calling TTS, check if the .wav file already exists on disk. If it does, skip the API call and reuse the cached file. This is mandatory — implement a _check_cache(output_path) guard.

One line at a time: Never batch multiple dialogue lines in one TTS call. Each dialogue line = one call = one WAV file. Keep individual prompts short.


5. EXECUTION MODE SYSTEM (MANDATORY)
Every agent must check EXECUTION_MODE before making any real API call.

# utils/execution_mode.py

import os

def is_mock() -> bool:

    return os.getenv("EXECUTION_MODE", "MOCK").upper() == "MOCK"

def require_real(fn):

    """Decorator: only calls real API if EXECUTION_MODE=REAL"""

    def wrapper(*args, **kwargs):

        if is_mock():

            raise RuntimeError(

                f"[BLOCKED] Real API call attempted in MOCK mode. "

                f"Set EXECUTION_MODE=REAL to enable. Function: {fn.__name__}"

            )

        return fn(*args, **kwargs)

    return wrapper

Every MCP tool that touches a real API must use @require_real on its internal implementation, while exposing a mock path that runs without it.

Template for all MCP tools that touch real APIs:

def _my_tool(inputs: dict) -> str:

    if is_mock():

        return _my_tool_mock(inputs)     # always works, zero cost

    else:

        return _my_tool_real(inputs)     # real API, requires EXECUTION_MODE=REAL

def _my_tool_mock(inputs: dict) -> str:

    # Generate fixture / silent file / copy test asset

    # Must return a valid path that downstream agents can consume

    ...

@require_real

def _my_tool_real(inputs: dict) -> str:

    # Actual API call goes here

    ...


6. PROJECT STRUCTURE
phase2/

├── .env                          ← all keys + WAN_VIDEO_MODEL + EXECUTION_MODE

├── requirements.txt

├── main.py                       ← entry: python main.py [--real] [--all-scenes]

├── state.py

├── graph.py

├── agents/

│   ├── scene_parser.py

│   ├── voice_synthesis.py

│   ├── video_generation.py

│   ├── face_swap.py

│   └── lip_sync.py

├── mcp/

│   ├── registry.py               ← mock MCP registry (tool discovery)

│   └── tools/

│       ├── get_task_graph.py

│       ├── voice_cloning_synthesizer.py

│       ├── query_stock_footage.py       ← Wan T2V, uses WAN_VIDEO_MODEL env var

│       ├── face_swapper.py              ← stub

│       ├── identity_validator.py        ← stub

│       ├── lip_sync_aligner.py          ← ffmpeg merge or stub

│       └── commit_memory.py             ← ChromaDB

├── memory/

│   └── chroma_client.py

├── utils/

│   ├── execution_mode.py         ← is_mock(), require_real decorator

│   ├── audio_utils.py            ← PCM→WAV, silence gen, audio concat

│   ├── video_utils.py            ← download mp4, merge audio+video

│   └── file_utils.py             ← load scene_manifest, character_db

└── tests/

    └── fixtures/

        ├── test_scene.mp4        ← 3-second black video for mock video path

        └── test_manifest.json    ← minimal scene_manifest for unit tests


7. SHARED STATE (state.py)
from typing import TypedDict, List, Dict, Any

class Phase2State(TypedDict):

    scene_manifest: Dict[str, Any]

    character_db: Dict[str, Any]

    task_graph: List[Dict[str, Any]]

    current_scene_index: int

    audio_paths: Dict[str, str]          # key: "scene_id_charname_index"

    video_paths: Dict[str, str]          # key: scene_id

    face_swapped_paths: Dict[str, str]

    lip_synced_paths: Dict[str, str]

    errors: List[str]

    completed_scenes: List[str]

    task_graph_logs: List[Dict[str, Any]]

    execution_mode: str                  # "MOCK" or "REAL"


8. MCP REGISTRY (ASSIGNMENT MANDATORY — NO HARDCODING)
# mcp/registry.py

from dataclasses import dataclass

from typing import Callable, Dict, Any

@dataclass

class MCPTool:

    name: str

    description: str

    input_schema: Dict[str, Any]

    callable_fn: Callable

_REGISTRY: Dict[str, MCPTool] = {}

def register_tool(name, description, schema, fn):

    _REGISTRY[name] = MCPTool(name, description, schema, fn)

def get_tool(name: str) -> MCPTool:

    if name not in _REGISTRY:

        raise ValueError(f"[MCP] Tool '{name}' not in registry. Available: {list(_REGISTRY)}")

    return _REGISTRY[name]

def list_tools():

    return list(_REGISTRY.keys())

Every agent must call registry.get_tool("name") and invoke tool.callable_fn(...). No agent may import a tool function directly.


9. VOICE SYNTHESIS AGENT
MCP Tool: voice_cloning_synthesizer
Mock path (always runs in MOCK mode)
def _voice_cloning_synthesizer_mock(inputs: dict) -> str:

    """Generate a 2-second silent WAV. Free, instant, lets pipeline test."""

    import wave, struct

    from pathlib import Path

    output_path = inputs["output_path"]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    sample_rate, channels, duration_s = 24000, 1, 2

    num_samples = sample_rate * duration_s

    with wave.open(output_path, 'wb') as wf:

        wf.setnchannels(channels)

        wf.setsampwidth(2)

        wf.setframerate(sample_rate)

        wf.writeframes(struct.pack('<' + 'h' * num_samples, *([0] * num_samples)))

    print(f"[TTS MOCK] Generated silent WAV → {output_path}")

    return output_path
Real path (EXECUTION_MODE=REAL only)
Model: gemini-2.5-flash-tts (NOT Pro — Flash is cheaper)
Output: raw PCM (16-bit, 24kHz, mono) — must be wrapped with stdlib wave
ALWAYS check if .wav file already exists before calling API (cache guard)
Voice names to use: Kore (female), Charon (male), Fenrir (villain), Puck (neutral/energetic), Orus (narrator)
If character_db has no voice_name, auto-assign from personality keywords

@require_real

def _voice_cloning_synthesizer_real(inputs: dict) -> str:

    import google.generativeai as genai, os, wave

    from pathlib import Path

    output_path = inputs["output_path"]

    # ── Cache guard: skip API if file already exists ─────────────────────────

    if Path(output_path).exists():

        print(f"[TTS] Cache hit, reusing {output_path}")

        return output_path

    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

    voice_name = inputs.get("voice_profile", {}).get("voice_name", "Kore")

    client = genai.GenerativeModel(model_name="gemini-2.5-flash-tts")

    response = client.generate_content(

        contents=inputs["text"],

        generation_config=genai.GenerationConfig(

            response_modalities=["AUDIO"],

            speech_config=genai.SpeechConfig(

                voice_config=genai.VoiceConfig(

                    prebuilt_voice_config=genai.PrebuiltVoiceConfig(

                        voice_name=voice_name

                    )

                )

            ),

        ),

    )

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


10. VIDEO GENERATION AGENT
MCP Tool: query_stock_footage
Mock path
def _query_stock_footage_mock(inputs: dict) -> str:

    """Copy test fixture video to output path. Zero cost."""

    import shutil

    from pathlib import Path

    output_path = inputs["output_path"]

    fixture = "tests/fixtures/test_scene.mp4"

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(fixture, output_path)

    print(f"[VideoGen MOCK] Copied fixture → {output_path}")

    return output_path
Real path (EXECUTION_MODE=REAL only)
@require_real

def _query_stock_footage_real(inputs: dict) -> str:

    import dashscope, os, time, httpx

    from http import HTTPStatus

    from dashscope import VideoSynthesis

    from pathlib import Path

    # ── Read model from env var — NEVER hardcode ──────────────────────────────

    model = os.getenv("WAN_VIDEO_MODEL", "wan2.1-t2v")    # default = cheapest

    # ── Duration and resolution depend on tier ────────────────────────────────

    # Tier 1 (wan2.1-t2v) → 3s, 480P  | Tier 2 (wan2.5) → 5s, 480P

    # Tier 3 (wan2.7-t2v) → 5-10s, 720P

    tier_config = {

        "wan2.1-t2v":  {"duration": 3,  "resolution": "480P"},

        "wan2.5-t2v":  {"duration": 5,  "resolution": "480P"},

        "wan2.7-t2v":  {"duration": 5,  "resolution": "720P"},

    }

    cfg = tier_config.get(model, {"duration": 3, "resolution": "480P"})

    duration   = inputs.get("duration",   cfg["duration"])

    resolution = inputs.get("resolution", cfg["resolution"])

    dashscope.base_http_api_url = os.getenv(

        "DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/api/v1"

    )

    api_key    = os.getenv("DASHSCOPE_API_KEY")

    output_path = inputs["output_path"]

    scene_id   = inputs["scene_id"]

    log_path   = f"outputs/task_graph_logs/{scene_id}_wan_task.json"

    # ── Resume existing task if log exists (avoids resubmission) ─────────────

    task_id = _resume_task_if_exists(log_path)

    if not task_id:

        # Truncate prompt to 100 chars on Tier 1 to avoid wasted quota

        prompt = inputs["prompt"]

        if model == "wan2.1-t2v":

            prompt = prompt[:100]

        rsp = VideoSynthesis.async_call(

            api_key=api_key, model=model,

            prompt=prompt, resolution=resolution,

            duration=duration, prompt_extend=False,

            watermark=False

        )

        if rsp.status_code != HTTPStatus.OK:

            raise RuntimeError(f"Wan task submit failed: {rsp.code} | {rsp.message}")

        task_id = rsp.output.task_id

        # ── Save task_id IMMEDIATELY before polling ───────────────────────────

        _save_task_log(log_path, {

            "task_id": task_id, "model": model, "scene_id": scene_id,

            "prompt": prompt, "status": "PENDING"

        })

        print(f"[VideoGen] Task submitted: {task_id} (model={model})")

    # ── Poll for completion ───────────────────────────────────────────────────

    video_url = _poll_wan_task(task_id, api_key, log_path)

    # ── Download immediately (URL expires in 24h) ────────────────────────────

    _download_video(video_url, output_path)

    return output_path


def _resume_task_if_exists(log_path: str):

    """If a task was already submitted, return its task_id to resume polling."""

    import json

    from pathlib import Path

    if Path(log_path).exists():

        data = json.loads(Path(log_path).read_text())

        if data.get("status") not in ("SUCCEEDED", "FAILED"):

            print(f"[VideoGen] Resuming existing task: {data['task_id']}")

            return data["task_id"]

    return None


def _save_task_log(log_path: str, data: dict):

    import json

    from pathlib import Path

    Path(log_path).parent.mkdir(parents=True, exist_ok=True)

    Path(log_path).write_text(json.dumps(data, indent=2))


def _poll_wan_task(task_id, api_key, log_path,

                   poll_interval=15, max_wait=600) -> str:

    import time

    from dashscope import VideoSynthesis

    elapsed = 0

    while elapsed < max_wait:

        result = VideoSynthesis.fetch(task_id=task_id, api_key=api_key)

        status = result.output.task_status

        _save_task_log(log_path, {"task_id": task_id, "status": status})

        if status == "SUCCEEDED":

            return result.output.video_url

        elif status == "FAILED":

            raise RuntimeError(f"Wan task {task_id} FAILED: {result.output}")

        print(f"[VideoGen] Polling {task_id}: {status} ({elapsed}s elapsed)")

        time.sleep(poll_interval)

        elapsed += poll_interval

    raise TimeoutError(f"Wan task {task_id} timed out after {max_wait}s")


def _download_video(url: str, output_path: str):

    import httpx

    from pathlib import Path

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with httpx.Client(timeout=120) as client:

        with client.stream("GET", url) as r:

            r.raise_for_status()

            with open(output_path, "wb") as f:

                for chunk in r.iter_bytes(chunk_size=8192):

                    f.write(chunk)

    print(f"[VideoGen] Downloaded → {output_path}")


11. FACE SWAP AGENT
MCP Tools: face_swapper, identity_validator — both are documented stubs.

def _face_swapper(inputs: dict) -> str:

    """

    STUB. In production: InsightFace / DeepFaceLab.

    For demo: pass video through unchanged and log intent.

    """

    import shutil

    from pathlib import Path

    output_path = inputs["output_path"]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(inputs["video_path"], output_path)

    print(f"[FaceSwap STUB] {inputs['character_name']} ref={inputs['character_reference_image']}")

    return output_path

def _identity_validator(inputs: dict) -> dict:

    """STUB. In production: face recognition confidence check."""

    return {"valid": True, "confidence": 0.95, "character_name": inputs["character_name"]}


12. LIP SYNC AGENT
MCP Tool: lip_sync_aligner

Uses ffmpeg to merge audio onto video as the real (non-stub) implementation. This is free and produces a real synchronized output for the demo.

def _lip_sync_aligner(inputs: dict) -> str:

    import shutil, subprocess

    from pathlib import Path

    video_path  = inputs["video_path"]

    audio_path  = inputs["audio_path"]

    output_path = inputs["output_path"]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    ffmpeg = shutil.which("ffmpeg")

    if ffmpeg:

        subprocess.run([

            ffmpeg, "-y",

            "-i", video_path,

            "-i", audio_path,

            "-c:v", "copy", "-c:a", "aac",

            "-shortest", output_path

        ], check=True, capture_output=True)

        print(f"[LipSync] ffmpeg merged → {output_path}")

    else:

        print("[LipSync STUB] ffmpeg not found, passing video through")

        shutil.copy2(video_path, output_path)

    return output_path


13. AUDIO MERGE UTILITY
Before lip sync, all dialogue WAVs for a scene must be concatenated.

# utils/audio_utils.py

import wave, struct, os

def merge_wav_files(wav_paths: list, output_path: str, silence_ms: int = 300):

    """

    Concatenate multiple WAV files with short silence gaps between them.

    All inputs must be same format (24kHz, mono, 16-bit) — guaranteed by TTS tool.

    """

    from pathlib import Path

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

    with wave.open(output_path, 'wb') as out:

        out.setnchannels(1)

        out.setsampwidth(2)

        out.setframerate(sample_rate)

        out.writeframes(all_frames)

    return output_path


def generate_silence_wav(output_path: str, duration_seconds: int = 2):

    """Generate a silent WAV file. Used in mock mode."""

    import struct

    from pathlib import Path

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    sample_rate, num_samples = 24000, 24000 * duration_seconds

    with wave.open(output_path, 'wb') as wf:

        wf.setnchannels(1)

        wf.setsampwidth(2)

        wf.setframerate(sample_rate)

        wf.writeframes(struct.pack('<' + 'h' * num_samples, *([0] * num_samples)))

    return output_path


14. LANGGRAPH WORKFLOW (graph.py)
from langgraph.graph import StateGraph, END

from state import Phase2State

def build_graph():

    graph = StateGraph(Phase2State)

    graph.add_node("scene_parser_node",  scene_parser_node)

    graph.add_node("voice_synth_node",   voice_synth_node)

    graph.add_node("video_gen_node",     video_gen_node)

    graph.add_node("face_swap_node",     face_swap_node)

    graph.add_node("lip_sync_node",      lip_sync_node)

    graph.add_node("memory_commit_node", memory_commit_node)

    graph.set_entry_point("scene_parser_node")

    # Parallel branches: both voice and video start after parsing

    graph.add_conditional_edges(

        "scene_parser_node",

        lambda state: ["voice_synth_node", "video_gen_node"],

        {"voice_synth_node": "voice_synth_node", "video_gen_node": "video_gen_node"}

    )

    # Both converge at face_swap

    graph.add_edge("voice_synth_node", "face_swap_node")

    graph.add_edge("video_gen_node",   "face_swap_node")

    graph.add_edge("face_swap_node",     "lip_sync_node")

    graph.add_edge("lip_sync_node",      "memory_commit_node")

    graph.add_edge("memory_commit_node", END)

    return graph.compile()


15. MAIN ENTRY POINT (main.py)
import argparse, json, os

from dotenv import load_dotenv

load_dotenv()

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--real",       action="store_true",

                        help="Enable real API calls (EXECUTION_MODE=REAL)")

    parser.add_argument("--all-scenes", action="store_true",

                        help="Process all scenes (default: scene_01 only)")

    parser.add_argument("--model",      type=str, default=None,

                        help="Override WAN_VIDEO_MODEL env var")

    args = parser.parse_args()

    # Apply flags before anything else

    if args.real:

        os.environ["EXECUTION_MODE"] = "REAL"

    if args.model:

        os.environ["WAN_VIDEO_MODEL"] = args.model

    mode  = os.getenv("EXECUTION_MODE", "MOCK")

    model = os.getenv("WAN_VIDEO_MODEL", "wan2.1-t2v")

    print(f"[Main] Starting Phase 2 | mode={mode} | wan_model={model}")

    register_all_tools()

    for d in [os.getenv("RAW_SCENES_DIR"), os.getenv("AUDIO_DIR"), os.getenv("TASK_LOG_DIR")]:

        os.makedirs(d, exist_ok=True)

    scene_manifest = load_json("outputs/scene_manifest.json")

    character_db   = load_json("outputs/character_db.json")

    # Limit to scene_01 unless --all-scenes

    if not args.all_scenes:

        scene_manifest = {"scenes": scene_manifest["scenes"][:1]}

    initial_state = {

        "scene_manifest": scene_manifest,

        "character_db": character_db,

        "task_graph": [], "current_scene_index": 0,

        "audio_paths": {}, "video_paths": {},

        "face_swapped_paths": {}, "lip_synced_paths": {},

        "errors": [], "completed_scenes": [], "task_graph_logs": [],

        "execution_mode": mode

    }

    graph = build_graph()

    final = graph.invoke(initial_state)

    print("\n=== PHASE 2 COMPLETE ===")

    print(f"Mode: {mode}")

    print(f"Audio files:  {list(final['audio_paths'].values())}")

    print(f"Final videos: {list(final['lip_synced_paths'].values())}")

    if final["errors"]:

        print(f"Errors: {final['errors']}")

if __name__ == "__main__":

    main()


16. REQUIREMENTS.TXT
langgraph>=0.2.0

langchain>=0.2.0

langchain-google-genai>=1.0.0

google-generativeai>=0.8.0

dashscope>=1.25.8

chromadb>=0.4.0

httpx>=0.27.0

python-dotenv>=1.0.0

ffmpeg-python>=0.2.0


17. CHECKLIST — BEFORE RUNNING --real FOR THE FIRST TIME
EXECUTION_MODE=MOCK full pipeline run completes without errors
All output directories exist with mock files in them
.wav files are valid (open them in any audio player — should be silent)
.mp4 files are present (fixture copies)
LangGraph graph visualized/logged correctly
WAN_VIDEO_MODEL=wan2.1-t2v (cheapest tier) is set in .env
Only running --real on scene_01 (single scene, not --all-scenes)
Prompt length for Tier 1 call is under 100 characters
task_graph_logs/ directory exists (for task_id persistence)


18. CRITICAL REMINDERS
EXECUTION_MODE=MOCK is the default forever until you're ready to submit.
Never call Wan 2.7 during development. Save those ~50 tokens for the demo.
Cache TTS audio: always check if .wav exists before calling Gemini.
Save Wan task_id before polling, not after. Crashes happen.
Model name in code must always be os.getenv("WAN_VIDEO_MODEL").
On failure, log to state["errors"] and skip — never auto-retry video gen.
ffmpeg for lip sync is free and produces real output — don't stub this one.

