from mcp.registry import register_tool

def _get_task_graph(inputs: dict) -> list:
    scene_manifest = inputs.get("scene_manifest", {})
    character_db = inputs.get("character_db", {})
    
    scenes = scene_manifest.get("scenes", [])
    chars_list = character_db.get("characters", [])
    
    # Quick lookup dictionary for characters
    char_lookup = {c["name"]: c for c in chars_list if "name" in c}
    
    task_graph = []
    
    for scene in scenes:
        scene_id = scene.get("scene_id", "unknown_scene")
        dialogues = scene.get("dialogue", [])
        
        # Find characters mentioned in dialogues
        scene_chars = []
        seen_char_names = set()
        for d in dialogues:
            c_name = d.get("character") or d.get("speaker")
            if c_name and c_name not in seen_char_names:
                seen_char_names.add(c_name)
                if c_name in char_lookup:
                    scene_chars.append(char_lookup[c_name])
                else:
                    scene_chars.append({"name": c_name})
                    
        task = {
            "scene_id": scene_id,
            "scene_description": scene.get("scene_description", ""),
            "visual_cue": scene.get("visual_cue", ""),
            "environment": scene.get("environment", ""),
            "dialogues": dialogues,
            "characters": scene_chars,
            "status": "pending"
        }
        task_graph.append(task)
        
    return task_graph

def get_task_graph(inputs: dict) -> list:
    return _get_task_graph(inputs)

def register():
    register_tool(
        "get_task_graph",
        "Generate task graph from scene manifest",
        {
            "type": "object", 
            "properties": {
                "scene_manifest": {"type": "object"},
                "character_db": {"type": "object"}
            }
        },
        get_task_graph
    )
