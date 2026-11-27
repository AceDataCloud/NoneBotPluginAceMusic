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

    async def test_service_specific_commands_and_result_fields(self):
        from nonebot.adapters.onebot.v11 import Message
        from nonebot_plugin_acemusic import parse_command
        from nonebot_plugin_acemusic.client import SERVICES, create_song, read_song

        self.assertEqual(parse_command(("创作音乐",), Message("music prompt")), ("acemusic", "music prompt"))
        for service, spec in SERVICES.items():
            task = "sample-task-id"
            url = f"https://example.org/{service}/result"
            calls = []
            def respond(req):
                body = json.loads(req.content)
                calls.append(req.url.path)
                self.assertEqual(req.headers["Authorization"], "Bearer example")
                if req.url.path == spec.endpoint:
                    self.assertTrue(body["async"])
                    self.assertEqual(req.headers["Idempotency-Key"], "same-delivery")
                    self.assertEqual(body["content"][0]["text"] if service == "seedance" else body["prompt"], "hello")
                    return httpx.Response(200, json={"task_id": task})
                self.assertEqual(body, {"id": task, "action": "retrieve"})
                entry = {spec.result_key: url}
                result = {"data": [entry, {spec.result_key: "javascript:alert(1)"}]}
                if service == "seedance":
                    result = {"data": {"content": entry, "status": "succeeded"}}
                elif service == "kling":
                    result = {"state": "succeeded", **entry}
                return httpx.Response(200, json={"id": task, "finished_at": 1, "response": result})
            with self.subTest(service=service):
                self.assertEqual(parse_command(("媒体任务",), Message(f"{service} {task}")), (service, task))
                async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
                    self.assertEqual(await create_song(client, "example", "hello", "same-delivery", service), task)
                    text = await read_song(client, "example", task, service)
                self.assertIn(url, text)
                self.assertNotIn("javascript", text)
                self.assertEqual(calls, [spec.endpoint, "/" + spec.endpoint.split("/")[1] + "/tasks"])
