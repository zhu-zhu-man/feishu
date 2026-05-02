# Brief Generation Prompt

## Instruction

基于检索结果生成会前简报 JSON。严格遵循 pre_result.schema.json 格式。

## Retrieval Trace Rule (CRITICAL)

`retrieval_trace` 的每个数字必须等于实际执行的 CLI 调用次数：

```json
"retrieval_trace": {
  "keywords": ["实际使用的关键词列表"],
  "docs_searched": <drive +search + docs +search 返回的文档总数>,
  "docs_read": <docs +fetch 调用次数>,
  "meetings_searched": <vc +search 返回的会议数>,
  "minutes_read": <vc +notes + docs +fetch 读取的纪要数>
}
```

**禁止写 0** 如果你确实执行了 CLI 调用。

## Brief Section Rules

### one_sentence_goal
一句话，30-80 字，基于 meeting.summary + description。

### background_items
- 每条 30-100 字
- 必须有 source
- importance: high（核心背景）| medium（补充信息）| low（边缘相关）
- 最多 5 条

### history_decisions
- 每条 20-60 字
- 必须来自 VC notes 的实际内容
- 标注状态：✓ 已闭环 / ⏳ 待跟进
- 最多 3 条

### open_risks
- 每条必须说明 risk + why_now（为什么这次会议要关注）
- 必须有 source
- 最多 3 条

### suggested_agenda
- 3-5 条建议议题
- 基于检索到的上下文推断

### related_links
- 包含 calendar 链接、VC 链接、相关文档链接
- 每条有 title + url + type

## Warnings

如实记录遇到的问题：
- `NO_RELATED_DOCS`：文档搜索无结果
- `NO_HISTORY_MEETINGS`：历史会议无结果
- `NO_NOTES_AVAILABLE`：历史会议无纪要
- `QUERY_TOO_LONG`：搜索词超长被截断
- `AUTH_REQUIRED`：缺少权限
