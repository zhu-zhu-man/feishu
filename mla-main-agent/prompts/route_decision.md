# Route Decision Prompt

## Instruction

根据 meeting 状态判断走哪个 route + target_agent。

## Decision Matrix

| 条件 | route | target_agent |
|------|-------|-------------|
| 新 event_id，start_time 在未来 30min 内 | pre_meeting | mla-pre-agent |
| 新 event_id，但 start_time > 30min 后 | 不路由，仅记录 | - |
| end_time < now，未 dispatch post，匹配到 vc meeting_id | post_meeting | mla-post-agent |
| end_time < now，未 dispatch post，未匹配到 vc | post_meeting（仅 calendar 数据） | mla-post-agent |
| 连续 3 次 scan_miss_count >= 3 | cancel_notice | mla-card-agent |
| hash 变化，非取消 | meeting_changed | mla-card-agent |

## Output

```json
{
  "should_route": true,
  "route": "pre_meeting",
  "target_agent": "mla-pre-agent",
  "reason": "new meeting in pre window",
  "idempotency_key": "mla-pre_meeting-b7ff9576-20260501"
}
```

不路由时：

```json
{
  "should_route": false,
  "reason": "meeting too far in future, skip for now"
}
```
