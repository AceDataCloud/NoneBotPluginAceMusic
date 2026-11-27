import httpx


async def request(client: httpx.AsyncClient, token: str, resource: str, payload: dict, *, key: str | None = None) -> dict:
    headers = {"Authorization": "Bearer " + token}
    if key is not None:
        headers["Idempotency-Key"] = key
    response = await client.post("https://api.acedata.cloud/acemusic/" + resource,
                                 headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, dict):
        raise ValueError("Invalid response")
    return result


async def create_song(client: httpx.AsyncClient, token: str, prompt: str, key: str) -> str:
    result = await request(client, token, "audios", {"action": "generate", "custom": False,
                           "async": True, "model": "acemusic-v1.1", "prompt": prompt}, key=key)
    task_id = result.get("task_id")
    if result.get("success") is False or not isinstance(task_id, str) or not task_id:
        raise ValueError("No confirmed task ID")
    return task_id


async def read_song(client: httpx.AsyncClient, token: str, task_id: str) -> str:
    result = await request(client, token, "tasks", {"action": "retrieve", "id": task_id})
    inner = result.get("response") or {}
    if result.get("id") != task_id or not isinstance(inner, dict) or inner.get("task_id") not in (None, task_id):
        raise ValueError("Task identity mismatch")
    state = inner.get("status") or result.get("state") or result.get("status") or "pending"
    lines = [f"任务 {task_id} · {state}"]
    for row in inner.get("data") or []:
        if isinstance(row, dict) and isinstance(row.get("audio_url"), str) and row["audio_url"].startswith("https://"):
            lines.append(f'{row.get("title") or "音轨"}：{row["audio_url"]}')
    return "\n".join(lines)
