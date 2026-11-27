import hashlib

import httpx
from nonebot import get_plugin_config, on_command
from nonebot.adapters.onebot.v11 import Message, PrivateMessageEvent
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from pydantic import BaseModel, SecretStr

from .client import create_song, read_song


class Config(BaseModel):
    acemusic_api_token: SecretStr | None = None


__plugin_meta__ = PluginMetadata(
    name="ACE Music 音乐助手", description="管理员私聊生成音乐并查询原任务",
    usage="/创作音乐 提示词（消耗 Credits）；/音乐任务 原任务ID（查询）",
    type="application", homepage="https://github.com/AceDataCloud/NoneBotPluginAceMusic",
    config=Config, supported_adapters={"~onebot.v11"},
)


async def private_chat(event: PrivateMessageEvent) -> bool:
    return True


generate = on_command("创作音乐", rule=private_chat, permission=SUPERUSER, block=True)
lookup = on_command("音乐任务", rule=private_chat, permission=SUPERUSER, block=True)


def token_value() -> str:
    value = get_plugin_config(Config).acemusic_api_token
    return value.get_secret_value().strip() if value else ""


@generate.handle()
async def submit(event: PrivateMessageEvent, args: Message = CommandArg()):
    token = token_value()
    prompt = args.extract_plain_text().strip()
    if not token or not prompt:
        await generate.finish("请配置 ACEMUSIC_API_TOKEN，再发送 /创作音乐 提示词。提交将使用应用的 Credits。")
    event_key = f"nonebot-v11:{event.self_id}:{event.user_id}:{event.message_id}:{event.time}"
    key = hashlib.sha256(event_key.encode()).hexdigest()
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            task_id = await create_song(client, token, prompt, key)
    except httpx.HTTPStatusError as exc:
        await generate.finish(f"提交返回 HTTP {exc.response.status_code}。请先核对 Ace 任务历史，再决定是否重试。")
    except (httpx.RequestError, ValueError):
        await generate.finish("未确认提交结果，请先到 Ace 控制台查看任务历史，避免重复生成。")
    await generate.finish(f"已受理。查询命令：/音乐任务 {task_id}")


@lookup.handle()
async def retrieve(args: Message = CommandArg()):
    token = token_value()
    task_id = args.extract_plain_text().strip()
    if not token or not task_id:
        await lookup.finish("请配置 ACEMUSIC_API_TOKEN，再发送 /音乐任务 原任务ID。")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            text = await read_song(client, token, task_id)
    except httpx.HTTPStatusError as exc:
        await lookup.finish(f"查询返回 HTTP {exc.response.status_code}，请核对应用权限和任务 ID。")
    except (httpx.RequestError, ValueError):
        await lookup.finish("暂时无法确认结果，请稍后使用同一任务 ID 查询。")
    await lookup.finish(text)
