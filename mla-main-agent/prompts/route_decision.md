# Route Decision Prompt

## Instruction

根据 meeting 状态判断走哪个 route + target_agent。

## Step 1: Idempotency Check

检查 `var/state/dispatched.json`，如果 idempotency_key 已存在 → **skip**，不重复派发。

## Step 2: Route Decision Matrix

| 条件 | route | target_agent |
|------|-------|-------------|
| 新 event_id，start_time 在扫描窗口内 | pre_meeting | mla-pre-agent |
| 新 event_id，但 start_time > 扫描窗口结束 | 不路由，仅记录 | - |
| end_time < now，未 dispatch post，匹配到 vc meeting_id | post_meeting | mla-post-agent |
| end_time < now，未 dispatch post，未匹配到 vc | post_meeting（仅 calendar 数据） | mla-post-agent |
| 连续 3 次 scan_miss_count >= 3 | cancel_notice | mla-card-agent |
| hash 变化，非取消 | meeting_changed | mla-card-agent |

## Step 3: Idempotency Check

检查 `var/state/dispatched.json`，如果 idempotency_key 已存在 → **skip**，不重复派发。

## Output

路由时：

```json
{
  "should_route": true,
  "route": "pre_meeting",
  "target_agent": "mla-pre-agent",
  "reason": "new_meeting",
  "idempotency_key": "mla-pre_meeting-<event_id_short>-<yyyymmdd>"
}
```

不路由时：

```json
{
  "should_route": false,
  "reason": "meeting summary and description both empty, skip"
}
```
