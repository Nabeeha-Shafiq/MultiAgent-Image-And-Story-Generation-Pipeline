from dataclasses import dataclass
from typing import Callable, Dict, Any

@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    callable_fn: Callable

_REGISTRY: Dict[str, MCPTool] = {}

def register_tool(name, description, schema, fn):
    _REGISTRY[name] = MCPTool(name, description, schema, fn)

def get_tool(name: str) -> MCPTool:
    if name not in _REGISTRY:
        raise ValueError(f"[MCP] Tool '{name}' not in registry. Available: {list(_REGISTRY)}")
    return _REGISTRY[name]

def list_tools():
    return list(_REGISTRY.keys())
