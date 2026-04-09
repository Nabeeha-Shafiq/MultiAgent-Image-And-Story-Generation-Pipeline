import os
import sys
sys.path.insert(0, "/media/hp/ADATA HV300/agentic-ass-3")
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

keys = ["AIzaSyD5ZK1VgslhtU7TMk900fIY2oxyByFi-a8"]
models = ["gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-1.5-pro-latest", "gemini-1.0-pro"]

print("Testing Legacy / Alternate model strings with Key 1...\n" + "="*50)

for model_name in models:
    print(f"  Model: {model_name}... ", end="", flush=True)
    os.environ["GOOGLE_API_KEY"] = keys[0]
    try:
        llm = ChatGoogleGenerativeAI(model=model_name, max_retries=1)
        response = llm.invoke([HumanMessage(content="Reply OK")])
        print("SUCCESS \u2705")
    except Exception as e:
        msg = str(e).split('\n')[0]
        if "404" in msg:
             print("FAILED \u274c (NOT FOUND)")
        elif "429" in msg or "RESOURCE_EXHAUSTED" in msg:
             print("FAILED \u274c (RATE LIMITED 429)")
        else:
             print(f"FAILED \u274c ({msg[:60]}...)")
