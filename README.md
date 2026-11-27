# NoneBot ACE Music 音乐助手

在 NoneBot 2 的 OneBot V11 私聊中生成歌曲，或查询已提交任务的音频。安装插件后无需密钥即可加载。命令仅向 NoneBot 的超级用户开放，因为机器人使用同一应用的额度和私有任务历史。

```sh
nb plugin install nonebot-plugin-acemusic
```

在 [Ace 应用](https://platform.acedata.cloud/console/applications) 中开通 ACE Music，把令牌配置为机器人环境变量 `ACEMUSIC_API_TOKEN`。在 NoneBot 的 `SUPERUSERS` 中指定获准使用的账号，启用 OneBot V11 适配器，再启动机器人。请勿在聊天中发送令牌。

- `/创作音乐 黄昏时的轻快爵士配乐`：提交一次计费生成并返回任务 ID。相同消息投递使用相同幂等键。请求超时后先检查 Ace 控制台的历史。
- `/音乐任务 <原任务ID>`：查询状态和已交付的音频链接。可重复查询，部分失败时保留仍可用的音轨。

[ACE Music 服务](https://platform.acedata.cloud/services/024e09b4-52cf-5e98-a91a-efedf43104c4) · [支持](https://github.com/AceDataCloud/NoneBotPluginAceMusic/issues)
