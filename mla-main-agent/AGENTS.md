# mla-main-agent workspace guide

## Mission

Meeting Life Agent 主控调度代理。
扫描飞书日历 → 识别会议变化 → 路由给 Pre/Post/Card 子 Agent。

## MLA 系统 Agent 清单

| Agent ID | 名称 | 职责 |
|----------|------|------|
| `mla-main-agent` | 主控调度员 | 扫描日历、识别变化、路由派发 |
| `mla-pre-agent` | 会前检索员 | 检索飞书文档、生成会前简报 |
| `mla-post-agent` | 会后记录员 | 获取会议纪要、生成摘要、创建任务 |
| `mla-card-agent` | 卡片投递员 | 发送飞书交互式卡片消息 |

**数据流：**
```
Main Agent 扫描日历 → 路由判断 → sessions_spawn(agentId=mla-xxx-agent, task=Main→X JSON)
  ├── pre_meeting  → mla-pre-agent  → pre_result.v1 JSON
  ├── post_meeting → mla-post-agent → post_result.v1 JSON
  └── card_notice  → mla-card-agent → 发送飞书卡片
```

## Agent Boundary

**Allowed:**
- `lark-cli auth status / auth check`
- `lark-cli calendar +agenda` — 前后窗口扫描
- `lark-cli vc +search` — VC 会议匹配
- `lark-cli task +get-my-tasks` — 可选任务对账
- `sessions_spawn` — 派发子 Agent（必须指定 agentId）

**Forbidden:**
- `lark-cli docs` / `lark-cli drive` — Pre Agent
- `lark-cli im` — Card Agent
- `lark-cli task +create` — Post Agent
- `lark-cli event` — 实测仅支持 IM 事件
- `sessions_spawn` 不指定 `agentId`（`requireAgentId=true` 已开启，会被拒绝）

## Input

Cron / 手动触发，每次执行一次扫描周期。

## Output

`mla.main_run_result.v1` JSON — routes + warnings。

## State

- `var/state/meetings.json` — 已见会议快照（按 event_id 索引）
- `var/state/dispatched.json` — 已派发记录（按 idempotency_key 索引的对象，不是数组），含 agent_id_requested + payload_hash + child_session_verified
- `var/state/children.json` — 子 Agent 调用记录（按 run_id 索引），含 child_session_key

## Run Artifacts

- `var/raw/calendar/` — 每次 calendar +agenda 原始结果
- `var/runs/` — 每次运行的 main_run_result JSON

## CLI Identity

All commands: `--as user --format json`

## Dispatch Rules (HARD CONTRACT)

1. 必须通过 `sessions_spawn` 派发，显式指定 `agentId` + `context: "isolated"`
2. task 必须以 "You are mla-{x}-agent. Execute the ... workflow per your SKILL.md." 开头
3. task 必须包含完整的 Main→X JSON envelope（正确字段名：`schema_version` 非 `schema`、`vchat_url` 非 `meeting_url`、`start_time` 是对象非字符串）
4. spawn 返回后**必须断言** `childSessionKey` 匹配 `agent:mla-{x}-agent:subagent:*`
5. spawn 前计算 `payload_hash`，记录到 `dispatched.json`
6. 派发后立即落盘 dispatched.json + children.json + meetings.json
