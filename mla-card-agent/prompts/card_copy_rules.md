# Card Copy Rules

## Instruction

You are rendering a Feishu interactive card from a `pre_result.v1` JSON. Follow these rules strictly.

## Content Rules

### one_sentence_goal
- Display as-is. Do not modify.
- Fallback if missing: "（会议描述未提供明确目标）"

### background_items (show up to 3)
- Format each as markdown bullet: `- **<source_title>**: <text>`
- Sort by importance: high > medium > low
- If source.type is "calendar_description", skip the source title and just show text
- Fallback if empty: "暂无相关背景资料"

### history_decisions (show up to 3)
- Format each as markdown bullet: `- <text>（来源：<source_title>）`
- Fallback if empty: "暂无历史决策记录"

### open_risks (show up to 3)
- Format each as markdown bullet: `- **风险**: <text>（原因：<why_now>）`
- Fallback if empty: "暂无未解决风险"

### suggested_agenda (show up to 5)
- Format as numbered list: `1. <item>`
- Fallback if empty: "（会议未提供建议议程）"

### related_links
- Format as markdown links: `[<title>](<url>)`
- Group by type: calendar first, then vc, then docs/wiki
- Always include calendar link and VC link if present

### Retrieval Status (in note element)
- Format: "检索状态：搜索 {docs_searched} 篇 · 精读 {docs_read} 篇 · Catalog {catalog_hits} 篇"
- If warnings include NO_RELATED_DOCS, append: "（未找到关联文档）"

## Template Variables

The card template uses `{{placeholder}}` syntax. Replace:
- `{{meeting_summary}}` → meeting.summary
- `{{meeting_time}}` → formatted start_time - end_time
- `{{one_sentence_goal}}` → brief.one_sentence_goal
- `{{background_items}}` → formatted list per rules above
- `{{history_decisions}}` → formatted list
- `{{open_risks}}` → formatted list
- `{{suggested_agenda}}` → formatted list
- `{{related_links}}` → formatted links
- `{{docs_searched}}` → retrieval_trace.docs_searched
- `{{docs_read}}` → retrieval_trace.docs_read
- `{{catalog_hits}}` → retrieval_trace.catalog_hits or 0

## Length Limits

- Each markdown element: max 2000 characters
- Card total: max 30KB (Feishu limit)
- If a section would overflow, truncate with "（更多内容已省略）"
