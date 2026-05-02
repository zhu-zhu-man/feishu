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
    "app_link": "...",
    "organizer": {"display_name": "...", "open_id": "..."},
    "self_rsvp_status": "...",
    "status": "confirmed"
  },
  "new": {
    "summary": "...",
    "start_time": {"datetime": "...", "timezone": "..."},
    "end_time": {"datetime": "...", "timezone": "..."},
    "description": "...",
    "vchat_url": "...",
    "app_link": "...",
    "organizer": {"display_name": "...", "open_id": "..."},
    "self_rsvp_status": "...",
    "status": "confirmed"
  }
}
```

## Compare Fields

| Field | Impact | Action |
|-------|--------|--------|
| start_time.datetime | 时间变更 | 应通知 |
| end_time.datetime | 时长变更 | 应通知 |
| summary | 标题变更 | 应通知 |
| vchat_url | VC 链接变更 | 应通知 |
| description | 描述变更 | 低优先级，记录即可 |
| self_rsvp_status | 用户状态变化 | 若变为 declined → 取消通知 |
| organizer.open_id | 组织者变更 | 中优先级 |
| app_link | 链接变更 | 低优先级 |
| status | 取消 | 紧急通知 |

## Output

```json
{
  "changed": true,
  "change_type": ["time_changed", "description_changed"],
  "old_start": "2026-05-01T10:00:00+08:00",
  "new_start": "2026-05-01T11:00:00+08:00",
  "should_notify": true
}
```

`change_type` 枚举值：
- `time_changed` — start_time 或 end_time 变化
- `summary_changed` — 标题变化
- `vc_changed` — 视频会议链接变化
- `description_changed` — 描述变化
- `organizer_changed` — 组织者变化
- `rsvp_changed` — 用户 RSVP 状态变化
- `cancelled` — 会议被取消
- `restored` — 已取消会议恢复
