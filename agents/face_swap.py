import os
import json
import glob
from state import Phase2State
from mcp.registry import get_tool

def get_primary_character_for_scene(scene_id: str, task_graph: list) -> str:
    for task in task_graph:
        if task.get("scene_id") == scene_id:
            chars = task.get("characters", [])
            if chars:
                return chars[0].get("name", "Unknown")
    return "Unknown"

def find_reference_image(char_name: str) -> str:
    from config import OUTPUT_DIR
    image_dir = os.path.join(OUTPUT_DIR, "image_assets")
    if not os.path.exists(image_dir):
        return None
    # Look for an image with the character name in it
    for ext in ["*.png", "*.jpg", "*.jpeg"]:
        matches = glob.glob(os.path.join(image_dir, f"*{char_name}*{ext}"))
        if matches:
            return matches[0]
    return None

def face_swap_node(state: Phase2State) -> dict:
    print("[Node] face_swap_node running")
    
    video_paths = state.get("video_paths", {})
    task_graph = state.get("task_graph", [])
    face_swapped_paths = state.get("face_swapped_paths", {})
    if not face_swapped_paths:
        face_swapped_paths = {}
    else:
        face_swapped_paths = face_swapped_paths.copy()
        
    from config import OUTPUT_DIR
    raw_scenes_dir = os.path.join(OUTPUT_DIR, "raw_scenes")
    
    face_swapper_tool = get_tool("face_swapper")
    validator_tool = get_tool("identity_validator")
    
    for scene_id, video_path in video_paths.items():
        char_name = get_primary_character_for_scene(scene_id, task_graph)
        ref_image = find_reference_image(char_name)
        
        output_path = os.path.join(raw_scenes_dir, f"{scene_id}_faceswapped.mp4")
        
        if ref_image:
            # Validate identity first
            val_res = validator_tool.callable_fn({
                "video_path": video_path,
                "character_name": char_name
            })
            if val_res.get("valid"):
                swap_res = face_swapper_tool.callable_fn({
                    "video_path": video_path,
                    "output_path": output_path,
                    "character_name": char_name,
                    "character_reference_image": ref_image
                })
                face_swapped_paths[scene_id] = swap_res
            else:
                print(f"  Identity validation failed for {char_name} in {scene_id}, skipping swap.")
                face_swapped_paths[scene_id] = video_path
        else:
            print(f"  No reference image found for {char_name} (scene {scene_id}), using raw video.")
            face_swapped_paths[scene_id] = video_path
            
    # Commit memory
    commit_tool = get_tool("commit_memory")
    commit_tool.callable_fn({
        "memory_key": "face_swapped_paths",
        "memory_value": json.dumps(face_swapped_paths)
    })
    
    return {"face_swapped_paths": face_swapped_paths}
