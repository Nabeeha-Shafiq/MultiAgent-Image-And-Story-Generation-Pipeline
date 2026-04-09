# PROJECT MONTAGE: Phase 1 (The Writer's Room)

## Introduction
Phase 1 establishes the foundation of the PROJECT MONTAGE system. This phase converts raw human creative intent into a structured, machine-interpretable narrative representation format. It uses a **Multi-Agent** orchestration framework where worker agents collaborate via a persistent vector memory, enforce strictly constrained MCP tool discoveries, and generate consistent JSON templates.

### Key Features
* **Multi-Agent Collaboration Model**: Relies heavily on LangChain's `ChatGroq` framework, guided by explicit `langgraph` state checks seamlessly controlling script generation and checkpointing.
* **Stateful Memory**: ChromaDB persists generation runs inside `./memory/chroma_db/`.
* **Subprocess Context Handling**: Execution states uniquely map outputs organically to isolated timestamps inside the `./outputs/run_[timestamp]/` system.
* **Strict Schema Enforcements**: The Character Designer and Script Writer LLMs abide strictly to required fields (e.g. `scene_id`, `visual_cue`, `traits`) without deviating. 
* **Resilient Edge Fault-Tolerance**: If external visual APIs rate constrain requests, the backend proxies organically catch the error to fall back onto placeholder images.

---

## Output Result Architecture
After a success case executes, data is pushed into `./outputs/run_[timestamp]/`:
* **scene_manifest.json**: Complete formatted scenes.
* **character_db.json**: Structured physical/behavioral attributes mapping.
* **image_assets/**: Individual `.png` visual blueprints representations of characters.

---

## How to Run The Project Locally

### 1. Requirements Initialization
Create and activate your Python environment.
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Ensure your `.env` is updated carrying your required `GROQ_API_KEY`:
```env
GROQ_API_KEY="your_api_key_here"
```

### 2. Execution

You no longer need to strictly hardcode your parameters directly in `main.py`! You can pass dynamic prompts immediately inside the CLI using the `--prompt` argument:

```bash
# Provide custom story generation prompt via arguments!
PYTHONUNBUFFERED=1 PYTHONPATH=. python main.py --prompt "A high-octane heist where a rogue agent must stop an explosive device from detonating inside a busy market."
```

Or just run the system passively to trigger the default prompt pipeline:
```bash
PYTHONUNBUFFERED=1 PYTHONPATH=. python main.py
```

### 3. Execution Pipeline & Output Checklist
1. The **MCP Server** instantly spawns in the background on FastApi port `:8000`.
2. Flow will reach the `hitl_node` and print out the formatted Script outputs over your terminal, waiting automatically to verify approval checkpoint via Human-in-the-Loop constraint (Auto-approved for Phase 1 Testing Constraints).
3. The final result exports organically directly inside the `outputs` directory per run context. 
