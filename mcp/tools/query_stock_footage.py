from mcp.registry import register_tool
from utils.execution_mode import is_mock, require_real
import shutil
import os
import json
import time
import httpx
from http import HTTPStatus
from pathlib import Path

def _query_stock_footage_mock(inputs: dict) -> str:
    """Copy test fixture video to output path. Zero cost."""
    output_path = inputs["output_path"]
    fixture = "tests/fixtures/test_scene.mp4"
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    if Path(fixture).exists():
        shutil.copy2(fixture, output_path)
        print(f"[VideoGen MOCK] Copied fixture → {output_path}")
    else:
        Path(output_path).touch()
        print(f"[VideoGen MOCK] Touched dummy file → {output_path}")
    return output_path

def _resume_task_if_exists(log_path: str):
    """If a task was already submitted, return its task_id to resume polling."""
    if Path(log_path).exists():
        data = json.loads(Path(log_path).read_text())
        if data.get("status") not in ("SUCCEEDED", "FAILED"):
            print(f"[VideoGen] Resuming existing task: {data['task_id']}")
            return data["task_id"]
    return None

def _save_task_log(log_path: str, data: dict):
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    Path(log_path).write_text(json.dumps(data, indent=2))

def _poll_wan_task(task_id, api_key, log_path, poll_interval=15, max_wait=600) -> str:
    from dashscope import VideoSynthesis
    elapsed = 0
    while elapsed < max_wait:
        result = VideoSynthesis.fetch(task=task_id, api_key=api_key)
        status = result.output.task_status
        _save_task_log(log_path, {"task_id": task_id, "status": status})
        if status == "SUCCEEDED":
            return result.output.video_url
        elif status == "FAILED":
            raise RuntimeError(f"Wan task {task_id} FAILED: {result.output}")
        print(f"[VideoGen] Polling {task_id}: {status} ({elapsed}s elapsed)")
        time.sleep(poll_interval)
        elapsed += poll_interval
    raise TimeoutError(f"Wan task {task_id} timed out after {max_wait}s")

def _download_video(url: str, output_path: str):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=120) as client:
        with client.stream("GET", url) as r:
            r.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in r.iter_bytes(chunk_size=8192):
                    f.write(chunk)
    print(f"[VideoGen] Downloaded → {output_path}")

@require_real
def _query_stock_footage_real(inputs: dict) -> str:
    import dashscope
    from dashscope import VideoSynthesis
    
    model = os.getenv("WAN_VIDEO_MODEL", "wan2.1-t2v")
    tier_config = {
        "wan2.1-t2v":  {"duration": 3,  "resolution": "480P"},
        "wan2.5-t2v":  {"duration": 5,  "resolution": "480P"},
        "wan2.7-t2v":  {"duration": 5,  "resolution": "720P"},
    }
    cfg = tier_config.get(model, {"duration": 3, "resolution": "480P"})
    duration   = inputs.get("duration",   cfg["duration"])
    resolution = inputs.get("resolution", cfg["resolution"])
    
    dashscope.base_http_api_url = os.getenv(
        "DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/api/v1"
    )
    api_key    = os.getenv("DASHSCOPE_API_KEY")
    output_path = inputs["output_path"]
    scene_id   = inputs["scene_id"]
    from config import OUTPUT_DIR
    log_path   = os.path.join(OUTPUT_DIR, "task_graph_logs", f"{scene_id}_wan_task.json")
    
    task_id = _resume_task_if_exists(log_path)
    if not task_id:
        prompt = inputs["prompt"]
        if model == "wan2.1-t2v":
            prompt = prompt[:100]
        
        # Map wan2.1-t2v to its actual Dashscope model string if needed
        actual_model = 'wan2.1-t2v-turbo' if model == 'wan2.1-t2v' else model
        rsp = VideoSynthesis.async_call(
            api_key=api_key, model=actual_model,
            prompt=prompt, size='832*480' if resolution == '480P' else '1280*720',
            prompt_extend=False,
            watermark=False
        )
        if rsp.status_code != HTTPStatus.OK:
            raise RuntimeError(f"Wan task submit failed: {rsp.code} | {rsp.message}")
            
        task_id = rsp.output.task_id
        _save_task_log(log_path, {
            "task_id": task_id, "model": model, "scene_id": scene_id,
            "prompt": prompt, "status": "PENDING"
        })
        print(f"[VideoGen] Task submitted: {task_id} (model={model})")
        
    video_url = _poll_wan_task(task_id, api_key, log_path)
    _download_video(video_url, output_path)
    return output_path

def query_stock_footage(inputs: dict) -> str:
    if is_mock():
        return _query_stock_footage_mock(inputs)
    return _query_stock_footage_real(inputs)

def register():
    register_tool(
        "query_stock_footage",
        "Generate video from prompt",
        {
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "scene_id": {"type": "string"},
                "output_path": {"type": "string"}
            }
        },
        query_stock_footage
    )

if __name__ == "__main__":
    os.environ["EXECUTION_MODE"] = "MOCK"
    print("Testing query_stock_footage MOCK:")
    print(query_stock_footage({
        "prompt": "Test video",
        "scene_id": "scene_01",
        "output_path": "tests/fixtures/test_video_output.mp4"
    }))
