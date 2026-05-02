# Keyword Extraction Prompt

## Instruction

从会议标题和描述中提取搜索关键词。遵循宽→窄策略。

## Rules

1. **保留词类**：项目名、产品名（MLA、Agent、OpenClaw、飞书）、技术名词（全链路、压测、并发）、业务词（会前、会后、卡片、任务）
2. **去除词类**：会议、讨论、同步、确认、今天、明天、请大家、测试会议、输出、方案、含
3. **宽关键词优先**：第一轮用 1-2 个核心概念词，长度 <= 20 字符
4. **drive +search query 限制**：最多 30 字符，超长会被 API 拒绝（错误码 99992402）
5. **多轮策略**：宽→中等→窄，不要一步到位

## Output Format

```json
{
  "wide_queries": ["agent", "MLA", "会议助手"],
  "medium_queries": ["agent 会议闭环", "MLA 全链路"],
  "narrow_queries": ["会前检索 会后任务"],
  "vc_query": "agent 会议"
}
```

## Example

Input: summary="【会议助手测试会议19】输出全链路压测方案（含并发用户模型）"

Bad (too long, too specific):
- "Meeting Life Agent 全链路压测方案 并发用户模型" → 超 30 字符，被拒

Good (wide first):
- Round 1: "agent" → 22 条结果
- Round 2: "agent 会议" → 从结果中筛选
- VC: "agent" → 2 条结果
