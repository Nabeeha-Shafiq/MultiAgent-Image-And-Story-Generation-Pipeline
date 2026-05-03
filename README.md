# Project Montage: Autonomous AI Movie Pipeline

Project Montage is an end-to-end Multi-Agent framework orchestrating the generation of short movies from a single text prompt. It is split into two robust phases: **The Writer's Room (Phase 1)** and **The Studio Floor (Phase 2)**. 

## 🎬 Architecture Overview

The system operates using LangGraph for agent orchestration, generating everything autonomously while supporting Human-In-The-Loop (HITL) checkpoints. 

* **Phase 1 (The Writer's Room)**: Takes a raw creative prompt and employs LLM agents (via Groq/Llama) to build a structured multi-scene JSON screenplay (`scene_manifest.json`), design character identities (`character_db.json`), and generate initial character reference images.
* **Phase 2 (The Studio Floor)**: Takes the screenplay and concurrently generates Text-to-Speech audio (via Gemini TTS) and AI Video scenes (via Wan 2.1). It then performs face-swapping using the reference images, syncs the lip movements to the generated audio, and finally stitches all the scenes together into a final `.mp4` movie.

All assets are tracked through persistent vector memory (ChromaDB) and orchestrated using Model Context Protocol (MCP) tools.

---

## 🛠️ Main Files & Workflow

1. **`main.py`**: The unified entry point. It intelligently detects if Phase 1 has already been run. If no assets exist, it executes Phase 1 to generate the script/characters, and then immediately pipes those outputs into the Phase 2 media generation graph.
2. **`config.py`**: Handles environment variables and dynamic directory generation (`OUTPUT_DIR`).
3. **`graph.py`**: Contains the LangGraph configuration for Phase 2's parallel audio and video generation nodes.
4. **`stitch_movie.sh`**: The final post-processing shell script that takes all generated `*_final.mp4` raw scenes and stitches them into `final_movie.mp4` using ffmpeg.
5. **`agents/`**: Contains the individual nodes (Scriptwriter, Character Designer, Video Generator, Lip Sync, etc.).
6. **`mcp/tools/`**: The decoupled executable actions for interacting with external AI models (Gemini TTS, Wan2.1, etc.).

---

## 🚀 Setup & Execution

### 1. Requirements Initialization

Ensure you have ffmpeg installed on your system. Then set up the Python environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

You will need a `.env` file populated with your API keys (provided separately):
```env
GROQ_API_KEY="..."
GOOGLE_API_KEY="..."
DASHSCOPE_API_KEY="..."
DASHSCOPE_BASE_URL="https://dashscope-intl.aliyuncs.com/api/v1"
```

### 2. Output Expectations

To prevent clutter, every execution groups its entire asset lifecycle into an isolated, timestamped output folder.
Example: `./outputs/3MAY-754PM-RUN/`

Inside this folder, you will find:
* `scene_manifest.json` & `character_db.json` (Phase 1)
* `image_assets/` (Character references)
* `audio/` (Per-character and merged scene WAV files)
* `raw_scenes/` (Wan AI generated MP4s and faceswapped variants)
* `task_graph_logs/` (JSON audit logs of the pipeline)
* `final_movie.mp4` (The ultimate stitched result)

> **Resiliency Note**: If the Gemini TTS API hits its quota limit (`429`), the system will gracefully retry up to 10 times with extended cooldowns. If it still fails, it automatically falls back to generating a "silent" mock WAV file instead of crashing, ensuring your movie pipeline never breaks!

---

## ⚡ Quick Reference — Commands Summary

You can control exactly how the pipeline operates, including what models to use depending on your API quotas.

**Development (always safe, zero cost using Mock tools):**
```bash
python main.py
```

**All scenes in mock mode:**
```bash
python main.py --all-scenes
```

**Single scene real API (Tier 1 — use during development/testing):**
```bash
python main.py --real --model wan2.1-t2v
```

**All scenes real API Tier 1 (use when Tier 1 quota remains and you want full output):**
```bash
python main.py --real --all-scenes --model wan2.1-t2v
```

**All scenes real API Tier 2 (when Tier 1 is exhausted):**
```bash
python main.py --real --all-scenes --model wan2.5-t2v
```

**All scenes real API Tier 3 — FINAL DEMO ONLY:**
```bash
python main.py --real --all-scenes --model wan2.7-t2v
```

### Custom Prompts
You can inject a custom creative prompt directly via the CLI using the `--prompt` argument. This triggers Phase 1 generation.
```bash
python main.py --real --all-scenes --prompt "A tense standoff in a neon-lit cyberpunk alleyway between Kael and a saboteur named Vex."
```

### Checking Quota
* **Video Generation Quota**: Log into your Alibaba Cloud console manually.
* **TTS Generation Quota**: Check the Google AI Studio usage dashboard.
