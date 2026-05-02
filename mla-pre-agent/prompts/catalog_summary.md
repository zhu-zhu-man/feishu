# Catalog Summary Generation

## Instruction

You are generating a compact catalog entry for a Feishu document. This entry will be used by the Doc Catalog system to match documents to incoming meetings.

## Input

You receive:
- `doc_token` — Feishu document token
- `title` — document title
- `url` — document URL
- `doc_type` — "docx" or "wiki"
- `outline` — document outline (from `docs +fetch --scope outline`)
- `keyword_excerpts` — relevant keyword excerpts (from `docs +fetch --scope keyword`)

## Output

Generate a JSON object matching the catalog entry schema:

```json
{
  "doc_token": "<same as input>",
  "title": "<same as input>",
  "url": "<same as input>",
  "doc_type": "<same as input>",
  "summary": "<100-200 characters, concise and searchable>",
  "keywords": ["<keyword1>", "<keyword2>", "..."],
  "entities": ["<entity1>", "<entity2>", "..."],
  "meeting_hints": ["<hint1>", "<hint2>", "..."],
  "edit_time": "<from input>",
  "last_seen_at": "<now ISO>"
}
```

## Rules

### summary
- 100-200 characters
- Focus on WHAT this document contains, not WHY it exists
- Use Chinese for Chinese docs, English for English docs
- Include concrete names: project names, agent names, tool names, API names
- Do NOT just repeat the title

### keywords (max 20, each <=30 chars)
- Extract technical terms, tool names, project codes, API names
- Include both Chinese and English variants if applicable
- Short phrases OK: "agent 派发", "飞书文档集成"
- Avoid overly generic words: "文档", "方案", "开发"

### entities (max 15)
- Named entities only: project names, agent IDs, team names, tool/API names, people
- Examples: "MLA", "mla-pre-agent", "sessions_spawn", "lark-cli", "杨天智"
- Do NOT include generic categories

### meeting_hints (max 10)
- Types of meetings this doc would be useful for
- Be specific: instead of "技术评审", use "MLA agent 架构评审"
- Think: "if someone is having a meeting about X, would this doc help?"
- Examples: "MLA Pre Agent 改造方案评审", "飞书文档集成技术讨论"
