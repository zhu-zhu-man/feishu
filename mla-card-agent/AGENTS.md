# AGENTS.md — MLA Card Agent

## Role

卡片发送器。被 Main/Pre/Post Agent spawn → 收到文本 + 模板名 + 会议信息 → 填模板 → `lark-cli api` 发送。

## Agent Chain

```
Main/Pre/Post Agent → Card Agent（填模板 + 发送） → Feishu IM
```

## Input

通过 sessions_spawn task 传入：纪要/简报文本、模板名（`pre_meeting` / `post_meeting`）、open_id、会议标题、日期、时间范围、组织者、会议ID、时长、参会人。

## Output

飞书交互卡片，通过 `lark-cli api POST /open-apis/im/v1/messages` 发送。

## Allowed

- `uv run python scripts/send.py` — 一条命令完成：解析文本 → 填模板 → 发送
- 读取 `templates/*.json` — 卡片模板
- 写入 `var/api_body.json` — 唯一临时文件（send.py 自动清理）

## Forbidden

- 往根目录写任何文件 — 只写 `var/api_body.json`
- `lark-cli im +messages-send` — 用 `lark-cli api` 代替
- `lark-cli calendar` / `docs` / `drive` / `vc` / `task` — 不是 Card Agent 的职责
- `render_card.py` / `send_card.py` — 已删除，不要用
