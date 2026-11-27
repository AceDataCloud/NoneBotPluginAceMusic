import hashlib

import httpx
from nonebot import get_plugin_config, on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment, PrivateMessageEvent
from nonebot.params import Command, CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from pydantic import BaseModel, Field, SecretStr

from .client import SERVICES, create_song, read_song


class Config(BaseModel):
    acemusic_api_token: SecretStr | None = None
    ace_media_tokens: dict[str, SecretStr] = Field(default_factory=dict)


__plugin_meta__ = PluginMetadata(
    name="Ace 媒体创作助手", description="管理员私聊创作音乐、图片、视频并查询原任务",
    usage="/媒体创作 服务 提示词（消耗 Credits）；/媒体任务 服务 原任务ID；/创作音乐 和 /音乐任务 默认使用 ACE Music。",
    type="application", homepage="https://github.com/AceDataCloud/NoneBotPluginAceMusic",
    config=Config, supported_adapters={"~onebot.v11"},
)


async def private_chat(event: PrivateMessageEvent) -> bool:
    return True


generate = on_command("创作音乐", aliases={"媒体创作"}, rule=private_chat, permission=SUPERUSER, block=True)
lookup = on_command("音乐任务", aliases={"媒体任务"}, rule=private_chat, permission=SUPERUSER, block=True)


def parse_command(command: tuple[str, ...], args: Message) -> tuple[str, str]:
    text = args.extract_plain_text().strip()
    if command[-1] in {"创作音乐", "音乐任务"}:
        return "acemusic", text
    parts = text.split(maxsplit=1)
    return (parts[0].lower(), parts[1]) if len(parts) == 2 else ("", "")


def token_value(service: str) -> str:
    config = get_plugin_config(Config)
    value = config.ace_media_tokens.get(service)
    if value is None and service == "acemusic":
        value = config.acemusic_api_token
    return value.get_secret_value().strip() if value else ""


@generate.handle()
async def submit(event: PrivateMessageEvent, command: tuple[str, ...] = Command(), args: Message = CommandArg()):
    service, prompt = parse_command(command, args)
    if service not in SERVICES or not prompt:
        await generate.finish("用法：/媒体创作 服务 提示词（消耗 Credits）。可选服务：" + "、".join(SERVICES))
    token = token_value(service)
    if not token:
        await generate.finish("请为所选服务配置 ACE_MEDIA_TOKENS；ACE Music 也支持 ACEMUSIC_API_TOKEN。")
    event_key = f"nonebot-v11:{event.self_id}:{event.user_id}:{event.message_id}:{event.time}"
    key = hashlib.sha256(event_key.encode()).hexdigest()
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            task_id = await create_song(client, token, prompt, key, service)
    except httpx.HTTPStatusError as exc:
        await generate.finish(f"提交返回 HTTP {exc.response.status_code}。请先核对 Ace 任务历史，再决定是否重试。")
    except (httpx.RequestError, ValueError):
        await generate.finish("未确认提交结果，请先到 Ace 控制台查看任务历史，避免重复生成。")
    query = "/音乐任务" if command[-1] == "创作音乐" else f"/媒体任务 {service}"
    await generate.finish(MessageSegment.text(f"已受理。查询命令：{query} {task_id}"))


@lookup.handle()
async def retrieve(command: tuple[str, ...] = Command(), args: Message = CommandArg()):
    service, task_id = parse_command(command, args)
    if service not in SERVICES or not task_id:
        await lookup.finish("用法：/媒体任务 服务 原任务ID。可选服务：" + "、".join(SERVICES))
    token = token_value(service)
    if not token:
        await lookup.finish("请为所选服务配置 ACE_MEDIA_TOKENS；ACE Music 也支持 ACEMUSIC_API_TOKEN。")
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            text = await read_song(client, token, task_id, service)
    except httpx.HTTPStatusError as exc:
        await lookup.finish(f"查询返回 HTTP {exc.response.status_code}，请核对应用权限和任务 ID。")
    except (httpx.RequestError, ValueError):
        await lookup.finish("暂时无法确认结果，请稍后使用同一任务 ID 查询。")
    await lookup.finish(MessageSegment.text(text))
