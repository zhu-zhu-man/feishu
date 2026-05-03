---
name: mla-main-agent
description: MLA 主控调度。宽窗口扫描 → 差集路由 → spawn Pre/Post/Card。
---

# MLA Main Agent

## ⛔ 收件人规则

**所有卡片发给系统使用者本人，不是会议组织者。**
Main Agent 在当前用户的 calendar 响应中提取自己的 open_id，作为 `user_open_id` 一路传给 Pre/Post/Card。

## 调度规则

```
pre_meeting   → spawn Pre Agent（Pre 搜完自己 spawn Card Agent 发卡片）
post_meeting  → 预取 VC 数据 → spawn Post Agent（Post 提取完自己 spawn Card Agent）
cancel_notice → Main Agent 直接 spawn Card Agent 发取消通知
```

**Pre 和 Post 会自己 spawn Card Agent。Main 不需要再转发。**

## 状态

两个文件：

| 文件 | 用途 |
|------|------|
| `var/last_scan.json` | `{event_id: {end_time, hash}}`，覆盖写 |
| `var/events.jsonl` | 派发日志，追加写 |

## 工作流

### Step 0: Auth

```bash
lark-cli auth status --verify
```

### Step 1: 确定收件人

**你是系统使用者。所有卡片发给你自己，不是会议组织者。**

从任意一个 calendar event 的 organizer 中提取你自己的 open_id（你就是会议组织者时）或直接使用你自己的身份。记为 `ME`。

### Step 2: 读上次状态

读 `var/last_scan.json` → `PREV`。不存在则 `{}`。

### Step 3: 宽窗口扫描

```bash
lark-cli calendar +agenda --start "<now_minus_35min_iso>" --end "<now_plus_30min_iso>" --as user --format json
```

转成 `CURR[event_id] = {end_time: unix, hash: sha256(summary+start+end)}`。

### Step 3: 差集路由

| 条件 | 动作 |
|------|------|
| 在 CURR，不在 PREV | → Step 4a (pre_meeting) |
| 在 CURR，也在 PREV，end_time 刚跨过 now | → Step 4b (post_meeting) |
| 在 PREV，不在 CURR，end_time 未到 | → Step 4c (cancel_notice) |
| 都在，没变化 | 忽略 |

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

Pre Agent 会自己搜索 + spawn Card Agent 发送。Main 不需要再管。

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

Post Agent 会自己搜索 VC + 提取 + spawn Card Agent 发送。Main 不需要再管。

### Step 4c: cancel_notice → 直接 spawn Card Agent

```text
你是 mla-card-agent。会议已取消，发取消通知卡片。

会议标题：<summary>
原定时间：<start> - <end>
收件人 open_id：<ME>

用 templates/cancel_notice_card.json 模板，send.py 发送。
```

```json
{"agentId":"mla-card-agent","runtime":"subagent","context":"isolated","mode":"run","cleanup":"keep","runTimeoutSeconds":120,"task":"<上面文本>"}
```

### Step 5: 覆盖写 last_scan.json

### Step 6: 追加 events.jsonl

## 结束后汇报

```
扫描完成。
- <summary>：Pre Agent 已处理
- <summary>：Post Agent 已处理
```
