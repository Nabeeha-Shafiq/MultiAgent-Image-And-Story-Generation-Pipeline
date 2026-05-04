import argparse, os, time, sys
from dotenv import load_dotenv

load_dotenv()

from config import OUTPUT_DIR, MCP_SERVER_URL
from graph import build_graph
from utils.file_utils import load_json
from pprint import pprint

def register_all_tools():
    import mcp.tools.get_task_graph as get_task_graph
    import mcp.tools.voice_cloning_synthesizer as voice_cloning_synthesizer
    import mcp.tools.query_stock_footage as query_stock_footage
    import mcp.tools.face_swapper as face_swapper
    import mcp.tools.identity_validator as identity_validator
    import mcp.tools.lip_sync_aligner as lip_sync_aligner
    import mcp.tools.commit_memory as commit_memory

    get_task_graph.register()
    voice_cloning_synthesizer.register()
    query_stock_footage.register()
    face_swapper.register()
    identity_validator.register()
    lip_sync_aligner.register()
    commit_memory.register()

def start_mcp_server():
    import subprocess
    import atexit
    print("[Main] Starting local MCP Server subprocess...")
    mcp_proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "tools.mcp_server:app", "--port", "8002"])
    time.sleep(2)
    atexit.register(mcp_proc.terminate)
    print("[Main] MCP Server started.")

def build_phase1_graph():
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    from state import State
    from agents.scriptwriter import scriptwriter_node
    from agents.validator import validator_node
    from agents.hitl import hitl_node
    from agents.character import character_node
    from agents.image_synth import image_node
    from memory.db import memory_commit_node

    def mode_selector_node(state: State) -> State:
        return state

    def route_by_mode(state: State) -> str:
        return state["input_mode"]

    def route_hitl(state: State) -> str:
        decision = str(state.get("hitl_decision", "")).strip().upper()
        if decision == "REJECT":
            print("User rejected. Looping back to scriptwriter.")
            return "scriptwriter_node"
        print("User approved. Proceeding to character generation.")
        return "character_node"

    builder = StateGraph(State)
    builder.add_node("mode_selector_node", mode_selector_node)
    builder.add_node("validator_node", validator_node)
    builder.add_node("scriptwriter_node", scriptwriter_node)
    builder.add_node("hitl_node", hitl_node)
    builder.add_node("character_node", character_node)
    builder.add_node("image_node", image_node)
    builder.add_node("memory_commit_node", memory_commit_node)
    
    builder.set_entry_point("mode_selector_node")
    
    builder.add_conditional_edges(
        "mode_selector_node",
        route_by_mode,
        {"manual": "validator_node", "auto": "scriptwriter_node"}
    )
    
    builder.add_edge("validator_node", "hitl_node")
    builder.add_edge("scriptwriter_node", "hitl_node")
    
    builder.add_conditional_edges(
        "hitl_node",
        route_hitl,
        {"character_node": "character_node", "scriptwriter_node": "scriptwriter_node"}
    )
    
    builder.add_edge("character_node", "image_node")
    builder.add_edge("image_node", "memory_commit_node")
    builder.add_edge("memory_commit_node", END)
    
    return builder.compile(checkpointer=MemorySaver(), interrupt_before=["hitl_node"])

def run_phase1(prompt: str):
    print("\n=== PHASE 1: WRITER'S ROOM ===")
    graph = build_phase1_graph()
    
    initial_state = {
        "input_mode": "auto",
        "raw_input": prompt,
        "script": {},
        "characters": [],
        "images": [],
        "status": "started",
        "hitl_decision": None
    }
    
    config = {"configurable": {"thread_id": "run-1"}}
    
    print("--- FIRST INVOKE (Generating Script) ---")
    for event in graph.stream(initial_state, config):
        for key, value in event.items():
            if isinstance(value, dict):
                print(f"Node '{key}' execution returned status: {value.get('status', '')}")
            else:
                print(f"Node '{key}' execution completed.")
                
    current_state = graph.get_state(config)
    print("\n[HITL INTERRUPT] PAUSED BEFORE HUMAN-IN-THE-LOOP")
    print("Generated Script Output:")
    pprint(current_state.values.get("script", {}))
    
    print("\nPlease review the generated script above.")
    user_decision = input("Type APPROVE to continue or REJECT to regenerate: ").strip()
    if not user_decision:
        user_decision = "APPROVE"
    
    print("\n--- SECOND INVOKE (Resuming Graph) ---")
    graph.update_state(config, {"hitl_decision": user_decision})
    for event in graph.stream(None, config):
        for key, value in event.items():
            if key != "__end__":
                print(f"Node '{key}' execution complete.")
                
    print(f"Phase 1 complete. Artifacts written to {OUTPUT_DIR}/")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--real",       action="store_true",
                        help="Enable real API calls (EXECUTION_MODE=REAL)")
    parser.add_argument("--all-scenes", action="store_true",
                        help="Process all scenes (default: scene_01 only)")
    parser.add_argument("--model",      type=str, default=None,
                        help="Override WAN_VIDEO_MODEL env var")
    parser.add_argument("--prompt",     type=str, default=None,
                        help="Prompt to generate story for Phase 1. Forces Phase 1 generation.")
    parser.add_argument("--phase1-only", action="store_true",
                        help="Only execute Phase 1 and exit.")
    args = parser.parse_args()

    if args.real:
        os.environ["EXECUTION_MODE"] = "REAL"
    if args.model:
        os.environ["WAN_VIDEO_MODEL"] = args.model

    mode  = os.getenv("EXECUTION_MODE", "MOCK")
    model = os.getenv("WAN_VIDEO_MODEL", "wan2.1-t2v")
    
    start_mcp_server()
    register_all_tools()
    
    manifest_path = os.path.join(OUTPUT_DIR, "scene_manifest.json")
    char_db_path = os.path.join(OUTPUT_DIR, "character_db.json")
    
    force_phase1 = args.prompt is not None or args.phase1_only
    prompt_to_use = args.prompt if args.prompt else "A tense standoff in a neon-lit cyberpunk alleyway between a rogue AI detective named Kael and a corporate saboteur named Vex."

    # Run Phase 1 if outputs don't exist OR if explicitly forced
    if force_phase1 or not os.path.exists(manifest_path) or not os.path.exists(char_db_path):
        if not force_phase1 and os.path.exists("outputs/scene_manifest.json") and os.path.exists("outputs/character_db.json"):
            import shutil
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            shutil.copy("outputs/scene_manifest.json", manifest_path)
            shutil.copy("outputs/character_db.json", char_db_path)
            if os.path.exists("outputs/image_assets"):
                shutil.copytree("outputs/image_assets", os.path.join(OUTPUT_DIR, "image_assets"), dirs_exist_ok=True)
            print(f"\n[Main] Copied existing Phase 1 artifacts from outputs/ to {OUTPUT_DIR}")
        else:
            if not os.getenv("GROQ_API_KEY"):
                print("\n[ERROR] GROQ_API_KEY is not set in your .env file or environment.")
                print("Please add GROQ_API_KEY to your .env file to run Phase 1 (The Writer's Room).")
                sys.exit(1)
            run_phase1(prompt_to_use)
    else:
        print(f"\n[Main] Phase 1 artifacts found in {OUTPUT_DIR}. Skipping Writer's Room.")

    if args.phase1_only:
        print("\n=== PHASE 1 COMPLETE (--phase1-only flag used) ===")
        print(f"Artifacts written to {OUTPUT_DIR}/")
        sys.exit(0)

    print(f"\n=== PHASE 2: STUDIO FLOOR | mode={mode} | wan_model={model} ===")

    for d in [os.path.join(OUTPUT_DIR, "raw_scenes"), 
              os.path.join(OUTPUT_DIR, "audio"), 
              os.path.join(OUTPUT_DIR, "task_graph_logs"),
              os.path.join(OUTPUT_DIR, "image_assets")]:
        os.makedirs(d, exist_ok=True)

    scene_manifest = load_json(manifest_path)
    character_db = load_json(char_db_path)

    if not args.all_scenes:
        if "scenes" in scene_manifest and len(scene_manifest["scenes"]) > 0:
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

    print("\n[Main] Running final movie stitcher...")
    import subprocess
    try:
        subprocess.run(["./stitch_movie.sh", OUTPUT_DIR], check=True)
    except Exception as e:
        print(f"[Main] Failed to stitch movie: {e}")

if __name__ == "__main__":
    main()
