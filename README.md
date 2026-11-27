# Ace 媒体创作助手

<img src="https://avatars.githubusercontent.com/u/156096448?s=192&amp;v=4" alt="" width="64" height="64">

在 NoneBot 2 的 OneBot V11 私聊中，把描述提交给音乐、图像或视频服务，并用原任务 ID 取回结果。命令仅向超级用户开放。创作会使用所选应用的 Credits。

```sh
nb plugin install nonebot-plugin-acemusic
```

在 [Ace 应用](https://platform.acedata.cloud/console/applications?utm_source=opensource&utm_medium=referral&utm_campaign=evergreen) 中开通要用的服务。在机器人的环境文件中设置各服务的应用令牌，填入 NoneBot 的 `SUPERUSERS` 并启用 OneBot V11 适配器，再启动机器人。插件可以在未配置服务时加载。

```dotenv
ACE_MEDIA_TOKENS='{"suno":"your-suno-token","nano-banana":"your-image-token","seedance":"your-video-token"}'
```

| 类型 | 命令中的服务名称 |
| --- | --- |
| 音乐 | `acemusic`、`suno` |
| 图片 | `nano-banana`、`gpt-image`、`seedream`、`flux` |
| 视频 | `seedance`、`kling`、`veo`、`hailuo` |

- `/媒体创作 suno 黄昏时的轻快爵士配乐` 提交一次歌曲创作，并返回专用查询命令。
- `/媒体创作 nano-banana 雨后街道的水彩插画` 生成一幅场景图。`/媒体创作 seedance 小船穿过拂晓时的薄雾` 提交一段视频。
- `/媒体任务 seedance 原任务ID` 查同一服务的状态与已交付的 HTTPS 媒体链接。等待中的任务可稍后重查。需要直接下载链接的图片请使用 URL 输出。
- 原有 `ACEMUSIC_API_TOKEN`、`/创作音乐 提示词` 和 `/音乐任务 原任务ID` 继续使用 ACE Music。同一消息的重复投递复用原幂等键。请求超时后先检查 Ace 控制台的任务历史。

令牌仅配置在机器人环境中。请勿在聊天中发送令牌。

[支持](https://github.com/AceDataCloud/NoneBotPluginAceMusic/issues)
