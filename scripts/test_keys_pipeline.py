import os
import sys

sys.path.insert(0, "/media/hp/ADATA HV300/agentic-ass-3")

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

keys = [
    "AIzaSyD5ZK1VgslhtU7TMk900fIY2oxyByFi-a8",
    "AIzaSyCZlzNXRK0aVEpDTXbspjvp7yeW_S0abt0",
    "AIzaSyBxuZcBC7hIL7QUn5hrnTKaXuxDJ5LFWZ4"
]

models = [
    "gemini-2.5-pro",
    "gemini-2.0-flash",
    "gemini-1.5-flash"
]

print("Starting API Key validation over multiple models...\n" + "="*50)

working_combo = None

for i, key in enumerate(keys):
    print(f"\n--- Testing Key {i+1} ---")
    os.environ["GOOGLE_API_KEY"] = key
    
    for model_name in models:
        print(f"  Model: {model_name}... ", end="", flush=True)
        try:
            llm = ChatGoogleGenerativeAI(model=model_name, max_retries=1)
            response = llm.invoke([HumanMessage(content="Reply OK")])
            print("SUCCESS \u2705")
            if not working_combo:
                working_combo = (key, model_name, i+1)
        except Exception as e:
            msg = str(e).split('\n')[0]
            print(f"FAILED \u274c ({msg[:80]}...)")

print("\n" + "="*50)

if working_combo:
    key_str, model_str, idx = working_combo
    print(f"CONCLUSION: Key {idx} works perfectly with {model_str}.")
    with open("/media/hp/ADATA HV300/agentic-ass-3/.env", "w") as f:
        f.write(f'GOOGLE_API_KEY="{key_str}"\n')
    print(f"Automatically updated .env to use Key {idx}.")
    
    with open("/media/hp/ADATA HV300/agentic-ass-3/config.py", "r") as f:
        config_data = f.read()
    import re
    config_data = re.sub(r'MODEL_NAME = ".*"', f'MODEL_NAME = "{model_str}"', config_data)
    with open("/media/hp/ADATA HV300/agentic-ass-3/config.py", "w") as f:
        f.write(config_data)
    print(f"Automatically set MODEL_NAME in config.py to {model_str}.")
else:
    print("ALL KEYS FAILED. (Likely all zero quota / banned)")
