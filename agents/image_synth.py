import requests
from state import State
from config import MCP_SERVER_URL

def image_node(state: State) -> State:
    characters = state.get("characters", [])
    generated_images = []
    
    for char in characters:
        name = char.get("name")
        appearance = char.get("appearance", "")
        if name:
            import time
            time.sleep(2.5)  # Throttle to avoid 429 Too Many Requests from Pollinations
            mcp_payload = {
                "tool": "generate_character_image",
                "input": {
                    "prompt": f"Character portrait of {name}, {appearance}",
                    "character_name": name
                }
            }
            try:
                response = requests.post(f"{MCP_SERVER_URL}/call_tool", json=mcp_payload)
                response.raise_for_status()
                data = response.json().get("data")
                generated_images.append({
                    "name": name,
                    "image_path": data
                })
                # Update character object inline
                char["image_path"] = data
            except Exception as e:
                print(f"Failed to generate image for {name}: {e}. Creating mockup fallback.")
                fallback_path = f"./outputs/image_assets/{name.replace(' ', '_')}_mock.png"
                with open(fallback_path, "w") as f:
                    f.write("Mock Image Data Fallback")
                generated_images.append({"name": name, "image_path": fallback_path})
                char["image_path"] = fallback_path
    return {**state, "images": generated_images, "characters": characters}
