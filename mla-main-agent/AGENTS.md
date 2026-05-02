# mla-main-agent workspace guide

## Mission

Meeting Life Agent 主控调度代理。
扫描飞书日历 → 识别会议变化 → 路由给 Pre/Post/Card 子 Agent。

## Agent Boundary

**Allowed:**
- `lark-cli auth status / auth check`
- `lark-cli calendar +agenda` — 前后窗口扫描
- `lark-cli vc +search` — VC 会议匹配
- `lark-cli task +get-my-tasks` — 可选任务对账

**Forbidden:**
- `lark-cli docs` / `lark-cli drive` — Pre Agent
- `lark-cli im` — Card Agent
- `lark-cli task +create` — Post Agent
- `lark-cli event` — 实测仅支持 IM 事件

## Input

Cron / 手动触发，每次执行一次扫描周期。

## Output

`mla.main_run_result.v1` JSON — routes + warnings。

## State

- `var/state/meetings.json` — 已见会议快照
- `var/state/dispatched.json` — 已派发记录（防重复）
- `var/state/children.json` — 子 Agent 调用记录

## CLI Identity

All commands: `--as user --format json`
