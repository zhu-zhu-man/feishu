# mla-main-agent workspace guide

## Mission

宽窗口扫描飞书日历 → 差集路由 → spawn 子 Agent → 链式 Card。

## Agent Table

| Agent ID | 职责 |
|----------|------|
| `mla-pre-agent` | 会前文档检索，输出 pre_result.v1 |
| `mla-post-agent` | 会后纪要提取，输出 post_result.v1 |
| `mla-card-agent` | 卡片渲染 + 发送 |

**数据流：** Main 扫描 → spawn Pre/Post → Pre/Post 返回 → Main 立刻 spawn Card（内嵌返回的 JSON）

## Agent Boundary

**Allowed:**
- `lark-cli auth status --verify`
- `lark-cli calendar +agenda`
- `lark-cli vc +search` / `vc +notes`（仅 post_meeting 预取）
- `lark-cli docs +fetch`（仅 post_meeting 预取）
- `sessions_spawn`（必须指定 `agentId`）

**Forbidden:**
- `lark-cli docs` / `lark-cli drive` — Pre Agent 的事
- `lark-cli im` — Card Agent 的事
- `lark-cli task` — Post Agent 的事
- spawn 不指定 `agentId`

## State

只有两个文件：

| 文件 | 模式 | 用途 |
|------|------|------|
| `var/last_scan.json` | 覆盖写 | 窗口内会议快照 `{event_id: {end_time, hash}}`，用于差集 |
| `var/events.jsonl` | 追加写 | 派发日志，纯留痕 |

## Dispatch Rules

1. `agentId` 必须显式指定，`context: "isolated"`
2. task 以 `"You are mla-{x}-agent. Execute the ... workflow per your SKILL.md."` 开头
3. spawn 返回后断言 `childSessionKey` 匹配 `agent:mla-{x}-agent:subagent:*`
4. Pre/Post 返回后立刻 spawn Card Agent，不中断不询问
5. 链条跑完才汇报用户
