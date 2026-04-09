import json
from state import State
from config import MODEL_NAME, MCP_SERVER_URL
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage

def character_node(state: State) -> State:
    llm = ChatGroq(model=MODEL_NAME)
    script_data = state.get("script", {})
    
    if not script_data:
        return state
        
    schema = {"characters": [{"name": "string", "traits": ["string"], "appearance": "string"}]}
    prompt = f"Given this script: {json.dumps(script_data)}, extract character metadata returning strictly a JSON object matching this schema: {json.dumps(schema)}. No markdown wrappers."
    
    for attempt in range(3):
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            
            parsed_characters = json.loads(content)
            if "characters" in parsed_characters:
                return {**state, "characters": parsed_characters["characters"]}
        except Exception as e:
            prompt += f" Error in previous attempt: {str(e)}."
            
    return state
