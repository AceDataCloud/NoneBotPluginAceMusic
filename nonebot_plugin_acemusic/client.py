from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx


@dataclass(frozen=True)
class Service:
    endpoint: str
    options: dict
    result_key: str
    label: str


SERVICES = {
    "acemusic": Service("/acemusic/audios", {"action": "generate", "custom": False, "model": "acemusic-v1.1"}, "audio_url", "音轨"),
    "suno": Service("/suno/audios", {"action": "generate", "custom": False, "model": "chirp-v6"}, "audio_url", "音轨"),
    "nano-banana": Service("/nano-banana/images", {"action": "generate", "model": "nano-banana-2"}, "image_url", "图片"),
    "gpt-image": Service("/openai/images/generations", {"model": "gpt-image-2", "response_format": "url"}, "url", "图片"),
    "seedream": Service("/seedream/images", {"model": "doubao-seedream-5-0-lite-260128", "response_format": "url"}, "image_url", "图片"),
    "flux": Service("/flux/images", {"action": "generate", "model": "flux-dev", "size": "1024x1024"}, "image_url", "图片"),
    "seedance": Service("/seedance/videos", {"model": "doubao-seedance-1-5-pro-251215"}, "video_url", "视频"),
    "kling": Service("/kling/videos", {"action": "text2video"}, "video_url", "视频"),
    "veo": Service("/veo/videos", {"action": "text2video"}, "video_url", "视频"),
    "hailuo": Service("/hailuo/videos", {"action": "generate", "model": "minimax-t2v"}, "video_url", "视频"),
}


async def request(client: httpx.AsyncClient, token: str, path: str, payload: dict, *, key: str | None = None) -> dict:
    headers = {"Authorization": "Bearer " + token}
    if key is not None:
        headers["Idempotency-Key"] = key
    response = await client.post("https://api.acedata.cloud" + path, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, dict):
        raise ValueError("Invalid response")
    return result


async def create_song(client: httpx.AsyncClient, token: str, prompt: str, key: str, service: str = "acemusic") -> str:
    spec = SERVICES[service]
    text_input = {"prompt": prompt}
    if service == "seedance":
        text_input = {"content": [{"type": "text", "text": prompt}]}
    result = await request(client, token, spec.endpoint, {**spec.options, **text_input, "async": True}, key=key)
    task_id = result.get("task_id")
    if result.get("success") is False or not isinstance(task_id, str) or not task_id.strip():
        raise ValueError("No confirmed task ID")
    return task_id


def https_url(value) -> bool:
    if not isinstance(value, str) or any(c.isspace() for c in value):
        return False
    try:
        url = urlsplit(value)
        return bool(url.scheme == "https" and url.hostname and url.username is None and url.password is None)
    except ValueError:
        return False


async def read_song(client: httpx.AsyncClient, token: str, task_id: str, service: str = "acemusic") -> str:
    spec = SERVICES[service]
    prefix = spec.endpoint.split("/")[1]
    result = await request(client, token, f"/{prefix}/tasks", {"action": "retrieve", "id": task_id})
    inner = result.get("response") or {}
    if result.get("id") != task_id or not isinstance(inner, dict) or inner.get("task_id") not in (None, task_id):
        raise ValueError("Task identity mismatch")
    data = inner.get("data")
    state = inner.get("status") or inner.get("state") or result.get("state") or result.get("status")
    if service == "kling":
        rows = [inner]
    elif service == "seedance" and isinstance(data, dict):
        rows = [data.get("content")]
        state = state or data.get("status")
    else:
        rows = data if isinstance(data, list) else []
    links = []
    row_states = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        row_state = row.get("status") or row.get("state")
        if isinstance(row_state, str):
            row_states.add(row_state)
        url = row.get(spec.result_key)
        if https_url(url):
            links.append(f'{row.get("title") or spec.label}：{url}')
    if not state:
        if inner.get("success") is False or inner.get("error"):
            state = "failed"
        elif row_states:
            state = ", ".join(sorted(row_states))
        else:
            state = "completed" if result.get("finished_at") or links or inner.get("success") is True else "pending"
    return "\n".join([f"任务 {task_id} · {state}", *links])
