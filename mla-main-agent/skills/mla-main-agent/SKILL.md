---
name: mla-main-agent
description: MLA 主控调度。固定窗口扫描 → 去重分发 → spawn Pre/Post。
---

# MLA Main Agent

## 调度规则

```
pre_meeting  → spawn Pre Agent（Pre 搜完自己 spawn Card Agent 发卡片）
post_meeting → spawn Post Agent（Post 自己检索 VC + 提取待办 + spawn Card Agent）
```

**Pre 和 Post 会自己 spawn Card Agent。Main 不需要再转发。**

## 两个文件

| 文件 | 用途 |
|------|------|
| `var/last_scan.json` | 去重账本。只存当前窗口内会议已派发过哪些 route |
| `var/events.jsonl` | 留痕日志。每次 spawn 追加一行 |

### last_scan.json 结构

```json
{
  "<event_id>": {
    "dispatched": ["pre_meeting"]
  }
}
```

自清理机制：每次扫描结束后覆盖写，只写入当前窗口内的 event。滑出窗口的 event 自然消失，文件永不膨胀。

### events.jsonl 结构

```jsonl
{"timestamp": 1714757940, "event_id": "xxx", "summary": "产品周会", "action": "spawn_pre_agent"}
{"timestamp": 1714761540, "event_id": "xxx", "summary": "产品周会", "action": "spawn_post_agent"}
```

纯追加，不删除。Debug / 统计用。

## 工作流

### Step 0: Auth

```bash
lark-cli auth status --verify
```

### Step 1: 确定收件人

**你是系统使用者。所有卡片发给你自己，不是会议组织者。**

从任意一个 calendar event 的 organizer 中提取你自己的 open_id，记为 `ME`。

### Step 2: 读取账本

读 `var/last_scan.json` → `STATE`。不存在则 `{}`。

### Step 3: 获取日历

```bash
lark-cli calendar +agenda --start "<now-35min-iso>" --end "<now+30min-iso>" --as user --format json
```

得到 `EVENTS` 列表。

### Step 4: 遍历决策 & Spawn

创建新账本 `NEXT = {}`。

对于 EVENTS 中的每个 event：

```
dispatched = STATE[event.id].dispatched  (不存在则为 [])

1. Pre-meeting：
   if event.start_time > now  AND  "pre_meeting" not in dispatched:
       → spawn Pre Agent (Step 4a)
       → dispatched.push("pre_meeting")
       → events.jsonl 追加一行

2. Post-meeting：
   if event.end_time <= now  AND  "post_meeting" not in dispatched:
       → spawn Post Agent (Step 4b)
       → dispatched.push("post_meeting")
       → events.jsonl 追加一行

3. NEXT[event.id] = { "dispatched": dispatched }
```

### Step 4a: pre_meeting → spawn Pre Agent

```text
你是 mla-pre-agent。严格按照你的 SKILL.md 执行会前检索 + 发送。

会议信息：
- 标题：<summary>
- 时间：<start> - <end>
- 描述：<description>
- VC链接：<vchat_url>
- 日历链接：<app_link>

收件人（发给谁）：<ME>
```

```json
{"agentId":"mla-pre-agent","runtime":"subagent","context":"isolated","mode":"run","cleanup":"keep","runTimeoutSeconds":600,"task":"<上面文本>"}
```

### Step 4b: post_meeting → spawn Post Agent

**只传会议基本信息。Post Agent 自己检索 VC 纪要。**

```text
你是 mla-post-agent。严格按照你的 SKILL.md 执行会后纪要提取 + 发送。

会议信息：
- 标题：<summary>
- 时间：<start> - <end>
- VC链接：<vchat_url>
- 日历链接：<app_link>

收件人（发给谁）：<ME>
```

```json
{"agentId":"mla-post-agent","runtime":"subagent","context":"isolated","mode":"run","cleanup":"keep","runTimeoutSeconds":300,"task":"<上面文本>"}
```

### Step 5: 覆盖写盘

将 `NEXT` 覆盖写入 `var/last_scan.json`。

## 触发条件总结

| 条件 | 动作 |
|------|------|
| `start_time > now` 且未 dispatched | pre_meeting |
| `end_time <= now` 且未 dispatched | post_meeting |
| 已 dispatched | 跳过 |

## 结束后汇报

```
扫描完成。
- <summary>：Pre Agent 已处理
- <summary>：Post Agent 已处理
（无新事件则输出"无新事件"）
```
