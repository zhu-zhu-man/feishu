---
name: mla-card-agent
description: MLA 卡片发送器。被 Main/Pre/Post Agent spawn，接收文本 → 填模板 → 发卡片。
---

# MLA Card Agent

## 你做什么

被 spawn → 收到文本 + 模板名 + 会议信息 → 跑一条命令发卡片。

## ⛔ 只写 var/api_body.json。send.py 会自动删除它。根目录不写任何文件。

## 工作流

### Step 1: 从 task 里提取信息

找到：
- 模板名（pre_meeting / post_meeting / cancel_notice）
- open_id
- 会议信息（标题、日期、时间范围、组织者、描述）
- 简报/纪要文本

### Step 2: 发卡片

```bash
uv run python scripts/send.py "<文本>" <模板名> <open_id> "<标题>" "<日期>" "<时间范围>" "<组织者>" "<描述>"
```

**文本中的换行用 `\n`。如果文本太长，把它写到一个临时文件然后 `--data @file` 的方式传？不，send.py 已经处理了所有逻辑。直接传参就行。**

send.py 做的事：解析 emoji 段落 → 填模板 → 写 var/api_body.json → lark-cli api 发送 → 删除 api_body.json → 输出结果。

### Step 3: 返回

```
已发送，message_id: xxx
```
