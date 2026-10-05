# 小红书 MCP 发布速查

仅在用户明确要求发布时读取本页。内容创作仍按 `content-playbook.md` 完成。

## 发布前准备

- 调用 `check_login_status` 确认账号可用；未登录时调用 `get_login_qrcode` 完成登录。
- 图文至少准备 1 张图片；优先使用本地绝对路径，也支持 HTTP/HTTPS 图片地址。
- 视频只支持 1 个本地视频文件的绝对路径。
- `tags` 传不带 `#` 的字符串数组，正文中不要重复写话题标签。

## 图文：`publish_content`

必填：

- `title`：最多 20 个中文字或英文单词
- `content`：正文，不含话题标签
- `images`：至少 1 个图片路径或 URL

可选：

- `tags`
- `schedule_at`：ISO 8601，距当前时间 1 小时至 14 天
- `is_original`：是否声明原创
- `visibility`：`公开可见`、`仅自己可见`、`仅互关好友可见`
- `products`：账号具备商品功能时传商品名或商品 ID 数组

## 视频：`publish_with_video`

必填 `title`、`content`、`video`；可选 `tags`、`schedule_at`、`visibility`、`products`。`video` 必须是本地绝对路径。

## 参数示例

```json
{
  "title": "用 Codex 发出第一篇笔记",
  "content": "配置完成后，我先发了一条最简单的测试内容……",
  "images": ["/Users/name/Pictures/xhs-cover.png"],
  "tags": ["Codex", "MCP", "小红书自动化"],
  "visibility": "公开可见"
}
```

发布后把 MCP 返回的状态和笔记 ID 告诉用户。
