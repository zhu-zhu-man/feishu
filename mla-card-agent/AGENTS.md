# mla-card-agent workspace guide

## Mission

卡片发送器。被 Pre/Post/Main Agent spawn → 收文本 → 填模板 → `lark-cli api` 发送。

## Allowed

- `uv run python scripts/send.py` — 一条命令完成全部（解析文本、填模板、发送）
- Read `templates/*.json` — 卡片模板

## Forbidden

- `render_card.py` / `send_card.py` / `validate_card.py` — 已删除，不要用
- `lark-cli im +messages-send` — 用 `lark-cli api` 代替
- `lark-cli calendar` / `docs` / `drive` / `vc` / `task`
- 往根目录写文件 — 只写 `var/api_body.json`（send.py 自动清理）

## Workflow

```
收到 task 文本 → uv run python scripts/send.py "<文本>" <模板名> <open_id> ... → 返回 message_id
```

## send.py 用法

```bash
uv run python scripts/send.py "<文本>" <pre_meeting|post_meeting|cancel_notice> <open_id> "<标题>" "<日期>" "<时间范围>" "<组织者>" "<描述>"
```
