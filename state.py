from typing import TypedDict, Literal, Dict, List, Any, Optional

class State(TypedDict):
    input_mode: Literal["manual", "auto"]
    raw_input: str
    script: Dict[str, Any]
    characters: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    status: str
    hitl_decision: Optional[str]
