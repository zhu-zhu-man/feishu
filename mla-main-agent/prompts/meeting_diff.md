# Meeting Diff Prompt

## Instruction

比较两个 meeting snapshot（旧 vs 新），判断是否变化。

## Input

```json
{
  "old": {
    "summary": "...",
    "start_time": {"datetime": "...", "timezone": "..."},
    "end_time": {"datetime": "...", "timezone": "..."},
    "description": "...",
    "vchat_url": "...",
    "status": "confirmed"
  },
  "new": {
    "summary": "...",
    "start_time": {"datetime": "...", "timezone": "..."},
    "end_time": {"datetime": "...", "timezone": "..."},
    "description": "...",
    "vchat_url": "...",
    "status": "confirmed"
  }
}
```

## Compare Fields

| Field | Impact |
|-------|--------|
| start_time.datetime | 时间变更 → 应通知 |
| end_time.datetime | 时长变更 → 应通知 |
| summary | 标题变更 → 应通知 |
| vchat_url | VC 链接变更 → 应通知 |
| description | 描述变更 → 低优先级 |
| status | 取消 → 紧急通知 |

## Output

```json
{
  "changed": true,
  "change_type": ["time_changed"],
  "old_start": "2026-05-01T10:00:00+08:00",
  "new_start": "2026-05-01T11:00:00+08:00",
  "should_notify": true
}
```
