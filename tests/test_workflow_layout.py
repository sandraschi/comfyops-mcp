"""Tests for workflow 2D placement optimization algorithm (api_to_ui)."""

from comfyops_mcp.workflow_utils import api_to_ui, is_ui_format


def test_api_to_ui_layout_placement():
    headless_api_wf = {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "flux1.safetensors"}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": "A cybernetic cat"}},
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["2", 0],
                "seed": 42,
            },
        },
    }

    ui_wf = api_to_ui(headless_api_wf)
    assert is_ui_format(ui_wf) is True
    assert len(ui_wf["nodes"]) == 3
    assert len(ui_wf["links"]) >= 2

    # Check 2D topological placement coordinates
    nodes_by_id = {node["id"]: node for node in ui_wf["nodes"]}
    # Checkpoint (depth 0) should be to the left of KSampler (depth 2)
    assert nodes_by_id[1]["pos"][0] < nodes_by_id[3]["pos"][0]
    assert nodes_by_id[2]["pos"][0] < nodes_by_id[3]["pos"][0]
