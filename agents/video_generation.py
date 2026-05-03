import os
import json
from state import Phase2State
from mcp.registry import get_tool

def video_gen_node(state: Phase2State) -> dict:
    print("[Node] video_gen_node running")
    
    from config import OUTPUT_DIR
    task_graph = state.get("task_graph", [])
    char_db = state.get("character_db", {})
    raw_scenes_dir = os.path.join(OUTPUT_DIR, "raw_scenes")
    os.makedirs(raw_scenes_dir, exist_ok=True)
    
    video_paths = state.get("video_paths", {})
    if not video_paths:
        video_paths = {}
    else:
        video_paths = video_paths.copy()
        
    tool = get_tool("query_stock_footage")
    
    char_lookup = {c.get("name"): c for c in char_db.get("characters", []) if "name" in c}
    
    for task in task_graph:
        scene_id = task.get("scene_id", "unknown_scene")
        
        prompt_parts = []
        visual_cue = task.get("visual_cue", "")
        if visual_cue:
            prompt_parts.append(visual_cue)
            
        scene_desc = task.get("scene_description", "")
        if scene_desc:
            prompt_parts.append(scene_desc)
            
        environment = task.get("environment", "")
        if environment:
            prompt_parts.append(f"Setting: {environment}")
            
        # Add character appearances
        for c in task.get("characters", []):
            c_name = c.get("name")
            if c_name in char_lookup:
                appearance = char_lookup[c_name].get("appearance", "")
                if appearance:
                    prompt_parts.append(f"{c_name} appearance: {appearance}")
                    
        prompt = ". ".join(prompt_parts)
        if not prompt.strip():
            prompt = "A cinematic scene with characters interacting."
        
        output_path = os.path.join(raw_scenes_dir, f"{scene_id}_raw.mp4")
        
        res = tool.callable_fn({
            "prompt": prompt,
            "scene_id": scene_id,
            "output_path": output_path
        })
        
        video_paths[scene_id] = res

    # Commit memory
    commit_tool = get_tool("commit_memory")
    commit_tool.callable_fn({
        "memory_key": "video_paths",
        "memory_value": json.dumps(video_paths)
    })
    
    return {"video_paths": video_paths}
