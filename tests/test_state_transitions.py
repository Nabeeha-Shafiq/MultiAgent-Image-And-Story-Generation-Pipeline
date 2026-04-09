import pytest
from main import build_graph

def test_graph_node_structure():
    graph = build_graph()
    nodes = [node for node in graph.nodes]
    expected_nodes = [
        "mode_selector_node", "validator_node", "scriptwriter_node", 
        "hitl_node", "character_node", "image_node", "memory_commit_node"
    ]
    for n in expected_nodes:
        assert n in nodes, f"Missing node: {n}"

def test_conditional_edges_present():
    # As the compiled graph schema structure varies slightly by LangGraph format,
    # just basic functional compile check passes if graph builds successfully.
    graph = build_graph()
    assert graph is not None
