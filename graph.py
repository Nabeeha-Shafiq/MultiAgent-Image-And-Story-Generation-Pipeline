from langgraph.graph import StateGraph, END
from state import Phase2State

from agents.scene_parser import scene_parser_node
from agents.voice_synthesis import voice_synth_node
from agents.video_generation import video_gen_node
from agents.face_swap import face_swap_node
from agents.lip_sync import lip_sync_node

def memory_commit_node(state: Phase2State) -> dict:
    print("[Node] memory_commit_node running")
    import json
    from mcp.registry import get_tool
    tool = get_tool("commit_memory")
    summary_data = {
        "completed_scenes": state.get("completed_scenes", []),
        "lip_synced_paths": state.get("lip_synced_paths", {}),
        "errors": state.get("errors", [])
    }
    res = tool.callable_fn({
        "memory_key": "final_state_summary", 
        "memory_value": json.dumps(summary_data)
    })
    print(f"  commit_memory output: {res}")
    print("\n" + "="*50)
    print("FINAL SUMMARY TABLE")
    print("="*50)
    print(f"{'-'*50}")
    print(f"{'Scene ID':<15} | {'Audio':<7} | {'Video':<7} | {'LipSync':<7}")
    print(f"{'-'*50}")
    task_graph = state.get("task_graph", [])
    for task in task_graph:
        scene_id = task.get("scene_id", "unknown")
        has_audio = "✓" if f"{scene_id}_merged" in state.get("audio_paths", {}) else "✗"
        has_video = "✓" if scene_id in state.get("video_paths", {}) else "✗"
        has_lipsync = "✓" if scene_id in state.get("lip_synced_paths", {}) else "✗"
        print(f"{scene_id:<15} | {has_audio:<7} | {has_video:<7} | {has_lipsync:<7}")
    print("="*50 + "\n")
    return {}

def build_graph():
    graph = StateGraph(Phase2State)

    graph.add_node("scene_parser_node",  scene_parser_node)
    graph.add_node("voice_synth_node",   voice_synth_node)
    graph.add_node("video_gen_node",     video_gen_node)
    graph.add_node("face_swap_node",     face_swap_node)
    graph.add_node("lip_sync_node",      lip_sync_node)
    graph.add_node("memory_commit_node", memory_commit_node)

    graph.set_entry_point("scene_parser_node")

    # Parallel branches: both voice and video start after parsing
    graph.add_conditional_edges(
        "scene_parser_node",
        lambda state: ["voice_synth_node", "video_gen_node"],
        {"voice_synth_node": "voice_synth_node", "video_gen_node": "video_gen_node"}
    )

    # Both converge at face_swap
    graph.add_edge("voice_synth_node", "face_swap_node")
    graph.add_edge("video_gen_node",   "face_swap_node")
    
    graph.add_edge("face_swap_node",     "lip_sync_node")
    graph.add_edge("lip_sync_node",      "memory_commit_node")
    graph.add_edge("memory_commit_node", END)

    return graph.compile()
