import os
import json
from state import Phase2State
from mcp.registry import get_tool

def scene_parser_node(state: Phase2State) -> dict:
    print("[Node] scene_parser_node running")
    
    tool1 = get_tool("get_task_graph")
    task_graph = tool1.callable_fn({
        "scene_manifest": state.get("scene_manifest", {}),
        "character_db": state.get("character_db", {})
    })
    
    print(f"Parsed Task Graph:\n{json.dumps(task_graph, indent=2)}")
    
    # Save a task graph log JSON
    from config import OUTPUT_DIR
    task_log_dir = os.path.join(OUTPUT_DIR, "task_graph_logs")
    os.makedirs(task_log_dir, exist_ok=True)
    log_path = os.path.join(task_log_dir, "task_graph_root.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(task_graph, f, indent=2)
        
    # Memory commit via tool
    tool2 = get_tool("commit_memory")
    res2 = tool2.callable_fn({
        "memory_key": "task_graph_root", 
        "memory_value": json.dumps(task_graph)
    })
    print(f"  commit_memory output: {res2}")
    
    return {"task_graph": task_graph}
