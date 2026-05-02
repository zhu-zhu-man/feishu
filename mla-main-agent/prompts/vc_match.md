# VC Match Prompt

## Instruction

从 `calendar +agenda` 的会议和 `vc +search` 的候选列表中匹配最可能的 VC meeting_id。

## Input

```json
{
  "calendar_event": {
    "event_id": "...",
    "summary": "项目方案、技术与分工会议",
    "start_time": {"datetime": "2026-04-25T15:12:00+08:00"},
    "organizer": {"display_name": "斯楷扬"}
  },
  "vc_candidates": [
    {
      "id": "7632590177219021767",
      "display_info": "项目方案、技术与分工会议\n4月25日 15:12 | 组织者：斯楷扬",
      "meta_data": {"app_link": "...", "description": "4月25日 15:12 | 组织者：斯楷扬 | ID: 714 313 130"}
    }
  ]
}
```

## Matching Rules

1. **标题关键词重叠**：calendar summary 和 vc display_info 共有 >= 3 个非泛词字符
2. **日期一致**：同一天
3. **时间接近**：start_time 差距 < 5 分钟
4. **组织者匹配**：display_name 相同（加分项）

## Output

```json
{
  "matched": true,
  "meeting_id": "7632590177219021767",
  "app_link": "https://applink.feishu.cn/client/vctab/open?...",
  "confidence": 0.87,
  "reason": "title exact match + time matched"
}
```

如果无匹配：

```json
{
  "matched": false,
  "meeting_id": null,
  "confidence": 0,
  "reason": "no vc candidate matched calendar event"
}
```
