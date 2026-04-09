import json
from state import State

def validator_node(state: State) -> State:
    raw = state.get("raw_input", "")
    try:
        parsed_script = json.loads(raw)
        if "scenes" in parsed_script:
            return {**state, "script": parsed_script, "status": "Script validated"}
        else:
             return {**state, "script": {}, "status": "Validation Failed: No scenes found"}
    except json.JSONDecodeError:
        return {**state, "script": {}, "status": "Validation Failed: Invalid JSON format"}
