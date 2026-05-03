import os
import chromadb
import uuid
from mcp.registry import register_tool

def commit_memory(inputs: dict) -> str:
    """Always real - uses ChromaDB locally, no API cost."""
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    key = inputs.get("memory_key", "default_key")
    val = inputs.get("memory_value", "")
    
    try:
        client = chromadb.PersistentClient(path=persist_dir)
        collection = client.get_or_create_collection(name="phase2_memory")
        
        doc_id = str(uuid.uuid4())
        
        collection.upsert(
            ids=[doc_id],
            documents=[val],
            metadatas=[{"key": key}]
        )
        return f"Memory committed for key '{key}' with id '{doc_id}'"
    except Exception as e:
        return f"Memory commit failed: {e}"

def register():
    register_tool(
        "commit_memory",
        "Commit state or memory to ChromaDB",
        {
            "type": "object",
            "properties": {
                "memory_key": {"type": "string"},
                "memory_value": {"type": "string"}
            }
        },
        commit_memory
    )
