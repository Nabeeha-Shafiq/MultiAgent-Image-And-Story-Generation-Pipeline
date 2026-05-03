import os
import json
from state import Phase2State
from mcp.registry import get_tool

def lip_sync_node(state: Phase2State) -> dict:
    print("[Node] lip_sync_node running")
    
    face_swapped_paths = state.get("face_swapped_paths", {})
    audio_paths = state.get("audio_paths", {})
    lip_synced_paths = state.get("lip_synced_paths", {})
    if not lip_synced_paths:
        lip_synced_paths = {}
    else:
        lip_synced_paths = lip_synced_paths.copy()
        
    from config import OUTPUT_DIR
    audio_dir = os.path.join(OUTPUT_DIR, "audio")
    raw_scenes_dir = os.path.join(OUTPUT_DIR, "raw_scenes")
    
    tool = get_tool("lip_sync_aligner")
    
    for scene_id, video_path in face_swapped_paths.items():
        merged_audio = audio_paths.get(f"{scene_id}_merged")
        if not merged_audio:
            # Fallback construct path if missing from dict but exists
            fallback_path = os.path.join(audio_dir, f"{scene_id}_merged.wav")
            if os.path.exists(fallback_path):
                merged_audio = fallback_path
                
        output_path = os.path.join(raw_scenes_dir, f"{scene_id}_final.mp4")
        
        if merged_audio and os.path.exists(merged_audio):
            res = tool.callable_fn({
                "video_path": video_path,
                "audio_path": merged_audio,
                "output_path": output_path
            })
            lip_synced_paths[scene_id] = res
        else:
            print(f"  No merged audio found for {scene_id}, skipping lip sync.")
            lip_synced_paths[scene_id] = video_path

    # Commit memory
    commit_tool = get_tool("commit_memory")
    commit_tool.callable_fn({
        "memory_key": "lip_synced_paths",
        "memory_value": json.dumps(lip_synced_paths)
    })
    
    completed_scenes = state.get("completed_scenes", [])
    completed_scenes = completed_scenes + list(lip_synced_paths.keys())
    
    return {"lip_synced_paths": lip_synced_paths, "completed_scenes": list(set(completed_scenes))}
