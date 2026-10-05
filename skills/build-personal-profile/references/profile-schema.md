# 画像 JSON 格式

UTF-8 JSON。`version` 固定为 1，`person`、`entries`、`questions` 必填。

```json
{
  "version": 1,
  "person": {
    "name": "我的画像",
    "intro": "这是一份可以补充和修正的综合个人画像。"
  },
  "entries": [
    {
      "id": "local-output-preference",
      "category": "偏好",
      "title": "这次希望通过本地网页查看画像",
      "detail": "本次画像需要本地可交互网页，便于查看与调整。",
      "status": "已知",
      "evidence": "本次对话：用户要求「输出是一个本地可交互的网页」。"
    }
  ],
  "questions": ["最近最想实现的个人目标是什么？"]
}
```

`person.name` 与 `person.intro` 为字符串。`entries` 可为空；每条包含全部六个字符串字段，`id` 非空且唯一，更新时保留原 ID。`title` 和 `evidence` 不可为空。`category` 仅支持“兴趣”“工作方式”“偏好”“目标”；`status` 仅支持“已知”“待确认”。`questions` 是补充问题的字符串数组，可为空。

依据写具体出处及其含义。例如“项目 README 介绍了比赛”只能支持项目上下文，不能支持“用户是支付宝员工”。不做百分比人格评分。条目标题宜短，描述宜具体；推断保留不确定性。页面中的用户手工新增默认是已知自述，可自行改为待确认。

渲染器可在任意工作目录使用。输入不合法时给出中文错误；目标已存在时拒绝覆盖，`--force` 可显式允许覆盖。完整网页不依赖 JSON 文件，HTML 已内嵌全部数据。
