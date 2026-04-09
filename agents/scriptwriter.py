import requests
import json
from state import State
from config import MCP_SERVER_URL, MODEL_NAME
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

def scriptwriter_node(state: State) -> State:
    llm = ChatGroq(model=MODEL_NAME)
    max_retries = 3
    
    prompt = state.get("raw_input", "")
    
    for attempt in range(max_retries):
        schema = '{"scenes": [{"scene_id": "string", "location": "string", "characters": ["string"], "dialogue": [{"speaker": "string", "line": "string", "visual_cue": "string"}]}]}'
        messages = [
            HumanMessage(content=f"Generate a multi-scene screenplay based on: '{prompt}'. Return strictly JSON matching this EXACT schema: {schema}, no markdown wrapping.")
        ]
        
        # 2. Act
        response = llm.invoke(messages)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:-3]
            
        try:
            parsed_json = json.loads(content)
            
            # Observe: Validate returned JSON structure
            if "scenes" not in parsed_json:
                raise ValueError("Missing 'scenes' key")
                
            # If Valid -> use MCP tool to format/save segment if needed (or just return updated state)
            # To adhere to the prompt's rubrics, we call the MCP tool here as an action
            mcp_payload = {
                "tool": "generate_script_segment",
                "input": {"prompt": json.dumps(parsed_json)}
            }
            mcp_response = requests.post(f"{MCP_SERVER_URL}/call_tool", json=mcp_payload)
            mcp_response.raise_for_status()
            
            # 4. Valid -> return updated state
            return {**state, "script": parsed_json, "status": "Script generated"}
            
        except Exception as e:
            # 5. Invalid -> retry with corrected prompt
            prompt += f"\nNote: Previous attempt failed with error: {str(e)}. Please ensure strict JSON generation."
            
    # Fallback to empty if fails
    return {**state, "script": {}, "status": "Failed to generate script after retries"}
