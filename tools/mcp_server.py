from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from tools.implementations import execute_tool, get_available_tools
import uvicorn

app = FastAPI(title="Local MCP Server", description="Dynamic Tool Discovery")

class ToolCallRequest(BaseModel):
    tool: str
    input: Dict[str, Any]

@app.get("/list_tools")
def list_tools():
    """Returns available tools and their schemas."""
    return {"tools": get_available_tools()}

@app.post("/call_tool")
def call_tool(request: ToolCallRequest):
    """Executes a tool call."""
    try:
        result = execute_tool(request.tool, request.input)
        return {"status": "success", "data": result}
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"error": f"Tool not found: {request.tool} - {str(e)}"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
