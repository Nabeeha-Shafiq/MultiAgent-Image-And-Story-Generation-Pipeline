from typing import TypedDict, Literal, Dict, List, Any, Optional

class State(TypedDict):
    input_mode: Literal["manual", "auto"]
    raw_input: str
    script: Dict[str, Any]
    characters: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    status: str
    hitl_decision: Optional[str]

class Phase2State(TypedDict):
    scene_manifest: Dict[str, Any]
    character_db: Dict[str, Any]
    task_graph: List[Dict[str, Any]]
    current_scene_index: int
    audio_paths: Dict[str, str]          # key: "scene_id_charname_index"
    video_paths: Dict[str, str]          # key: scene_id
    face_swapped_paths: Dict[str, str]
    lip_synced_paths: Dict[str, str]
    errors: List[str]
    completed_scenes: List[str]
    task_graph_logs: List[Dict[str, Any]]
    execution_mode: str                  # "MOCK" or "REAL"
