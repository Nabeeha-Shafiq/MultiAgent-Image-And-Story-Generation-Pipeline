import os
import json
from state import Phase2State
from mcp.registry import get_tool
from utils.audio_utils import merge_wav_files

def get_voice_name(character_name: str, char_db: dict) -> str:
    characters = char_db.get("characters", [])
    for c in characters:
        if c.get("name") == character_name:
            if "voice_name" in c and c["voice_name"]:
                return c["voice_name"]
            
            # Auto-assign logic
            gender = c.get("gender", "").lower()
            traits = " ".join(c.get("personality_traits", [])).lower()
            if "villain" in traits or "villain" in gender:
                return "Fenrir"
            elif gender == "male":
                return "Charon"
            elif gender == "female":
                return "Kore"
            return "Puck"
            
    # Default fallback
    return "Puck"

def voice_synth_node(state: Phase2State) -> dict:
    print("[Node] voice_synth_node running")
    
    from config import OUTPUT_DIR
    task_graph = state.get("task_graph", [])
    char_db = state.get("character_db", {})
    audio_dir = os.path.join(OUTPUT_DIR, "audio")
    os.makedirs(audio_dir, exist_ok=True)
    
    audio_paths = state.get("audio_paths", {})
    if not audio_paths:
        audio_paths = {}
    else:
        audio_paths = audio_paths.copy()
        
    tool = get_tool("voice_cloning_synthesizer")
    
    for task in task_graph:
        scene_id = task.get("scene_id", "unknown_scene")
        dialogues = task.get("dialogues", [])
        
        scene_wav_paths = []
        for i, d in enumerate(dialogues):
            char_name = d.get("character") or d.get("speaker", "Unknown")
            text = d.get("text") or d.get("line", "")
            
            # File name format: scene_id_charname_lineindex.wav
            filename = f"{scene_id}_{char_name}_{i}.wav"
            output_path = os.path.join(audio_dir, filename)
            
            voice_name = get_voice_name(char_name, char_db)
            voice_profile = {"voice_name": voice_name}
            
            res = tool.callable_fn({
                "text": text,
                "voice_profile": voice_profile,
                "output_path": output_path
            })
            
            audio_paths[f"{scene_id}_{char_name}_{i}"] = res
            scene_wav_paths.append(res)
            
        if scene_wav_paths:
            merged_output_path = os.path.join(audio_dir, f"{scene_id}_merged.wav")
            merged_res = merge_wav_files(scene_wav_paths, merged_output_path)
            audio_paths[f"{scene_id}_merged"] = merged_res
            print(f"  Merged {len(scene_wav_paths)} audio files for {scene_id} -> {merged_output_path}")

    # Commit memory
    commit_tool = get_tool("commit_memory")
    commit_tool.callable_fn({
        "memory_key": "audio_paths",
        "memory_value": json.dumps(audio_paths)
    })
    
    return {"audio_paths": audio_paths}
