import json
import unittest

import httpx
import nonebot


class PluginTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        nonebot.init(driver="~fastapi")
        assert nonebot.load_plugin("nonebot_plugin_acemusic") is not None

    async def test_submit_once_and_retrieve_original(self):
        from nonebot_plugin_acemusic.client import create_song, read_song
        calls = []
        def respond(req):
            body = json.loads(req.content)
            calls.append((body, req.headers.get("Idempotency-Key")))
            if req.url.path.endswith("/audios"):
                return httpx.Response(200, json={"task_id": "original"})
            return httpx.Response(200, json={"id": "original", "response": {"task_id": "original",
                "status": "partial_failed", "data": [{"title": "Track", "audio_url": "https://example.org/a.mp3"}]}})
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            task = await create_song(client, "example", "jazz", "same-delivery")
            status = await read_song(client, "example", task)
        self.assertIn("partial_failed", status)
        self.assertIn("https://example.org/a.mp3", status)
        self.assertEqual(calls[0][1], "same-delivery")
        self.assertNotIn("idempotency_key", calls[0][0])
        self.assertEqual(calls[1], ({"action": "retrieve", "id": "original"}, None))
