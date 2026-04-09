import subprocess
import time
import atexit
import sys
import os
from pprint import pprint

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import State
from agents.scriptwriter import scriptwriter_node
from agents.validator import validator_node
from agents.hitl import hitl_node
from agents.character import character_node
from agents.image_synth import image_node
from memory.db import memory_commit_node

# --- MCP SERVER STARTUP ---
def start_mcp_server():
    print("Starting local MCP Server subprocess...")
    # Use python executable running this script to find uvicorn ideally, or assume it's in PATH
    mcp_proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "tools.mcp_server:app", "--port", "8000"])
    time.sleep(2)  # Give it time to boot
    atexit.register(mcp_proc.terminate)  # Clean shutdown
    print("MCP Server started.")

# --- LANGGRAPH DEFINITION ---
def mode_selector_node(state: State) -> State:
    # Just a pass-through node for the start edge
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

def build_graph():
    builder = StateGraph(State)
    
    # Add nodes
    builder.add_node("mode_selector_node", mode_selector_node)
    builder.add_node("validator_node", validator_node)
    builder.add_node("scriptwriter_node", scriptwriter_node)
    builder.add_node("hitl_node", hitl_node)
    builder.add_node("character_node", character_node)
    builder.add_node("image_node", image_node)
    builder.add_node("memory_commit_node", memory_commit_node)
    
    # Set entry point
    builder.set_entry_point("mode_selector_node")
    
    # Add conditional edges
    builder.add_conditional_edges(
        "mode_selector_node",
        route_by_mode,
        {
            "manual": "validator_node",
            "auto": "scriptwriter_node"
        }
    )
    
    builder.add_edge("validator_node", "hitl_node")
    builder.add_edge("scriptwriter_node", "hitl_node")
    
    # HITL edge with conditional routing
    builder.add_conditional_edges(
        "hitl_node",
        route_hitl,
        {
            "character_node": "character_node",
            "scriptwriter_node": "scriptwriter_node"
        }
    )
    
    builder.add_edge("character_node", "image_node")
    builder.add_edge("image_node", "memory_commit_node")
    builder.add_edge("memory_commit_node", END)
    
    graph = builder.compile(
        checkpointer=MemorySaver(),
        interrupt_before=["hitl_node"]
    )
    return graph

if __name__ == "__main__":
    import time
    import argparse

    parser = argparse.ArgumentParser(description="MultiAgent Story Pipeline")
    parser.add_argument("--prompt", type=str, help="The prompt for autonomous script generation.", default=None)
    args = parser.parse_args()

    run_id = f"run_{int(time.time())}"
    os.environ["RUN_ID"] = run_id
    
    start_mcp_server()
    graph = build_graph()
    
    if args.prompt:
        TEST_PROMPT = args.prompt
    else:
        # Graceful fallback or interactive
        print("No --prompt provided.")
        TEST_PROMPT = "A tense standoff in a neon-lit cyberpunk alleyway between a rogue AI detective named Kael and a corporate saboteur named Vex."
        print(f"Defaulting to: {TEST_PROMPT}")
    
    initial_state = {
        "input_mode": "auto",
        "raw_input": TEST_PROMPT,
        "script": {},
        "characters": [],
        "images": [],
        "status": "started",
        "hitl_decision": None
    }
    
    config = {"configurable": {"thread_id": "run-1"}}
    
    print("\n--- FIRST INVOKE (Generating Script) ---")
    for event in graph.stream(initial_state, config):
        for key, value in event.items():
            if isinstance(value, dict):
                print(f"Node '{key}' execution returned status: {value.get('status', '')}")
            else:
                print(f"Node '{key}' execution completed.")
    # We should be paused before HITL. Let's get the state to show the user.
    current_state = graph.get_state(config)
    print("\n[HITL INTERRUPT] PAUSED BEFORE HUMAN-IN-THE-LOOP")
    print("Generated Script Output:")
    pprint(current_state.values.get("script", {}))
    
    # User review trigger for automated testing
    user_decision = "APPROVE"
    print("Auto-approving for test run.")
    
    # Second invoke resumes from checkpoint
    print("\n--- SECOND INVOKE (Resuming Graph) ---")
    graph.update_state(config, {"hitl_decision": user_decision})
    for event in graph.stream(None, config):
        for key, value in event.items():
            if key != "__end__":
                print(f"Node '{key}' execution complete.")
                
    final_state = graph.get_state(config)
    print("\n--- WORKFLOW COMPLETE ---")
    print(f"Files should be located in ./outputs/{run_id}/")
