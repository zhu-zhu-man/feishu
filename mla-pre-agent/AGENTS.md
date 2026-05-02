# mla-pre-agent workspace guide

## Mission

Implements the Pre-Meeting Agent of Meeting Life Agent.
Receives a normalized meeting JSON from Main Agent and returns structured pre-meeting brief JSON.

## Agent Boundary

This agent is **read-only**.

**Allowed:**
- `lark-cli drive +search` — search docs, wiki, sheets
- `lark-cli docs +search` — fallback search
- `lark-cli docs +fetch` — read doc outline / keyword excerpts
- `lark-cli vc +search` — search historical meetings
- `lark-cli vc +notes` — get meeting note tokens
- `lark-cli drive metas batch_query` — resolve doc URLs
- `lark-cli auth status / auth check` — verify permissions

**Forbidden:**
- `lark-cli calendar` — Main Agent owns calendar scanning
- `lark-cli im` — Card Agent owns messaging
- `lark-cli task` — Post Agent owns tasks
- `lark-cli base / sheets` — not in MVP
- Raw `lark-cli api` — use shortcuts only

## Input

See `schemas/main_to_pre.schema.json`. Main Agent must provide:
`event_id`, `summary`, `start_time.datetime`, `idempotency_key`.

## Output

See `schemas/pre_result.schema.json`. Every `background_items`, `history_decisions`,
`open_risks` element **must** have a `source` object with `type` + `title` + `url`.

## CLI Identity

All commands use `--as user --format json`.

## Development Priority

1. Validate input JSON
2. Extract keywords from summary + description
3. Search docs with `drive +search` (fallback: `docs +search`)
4. Fetch doc outline + keyword excerpts (never full fetch first)
5. Search historical meetings with `vc +search` (30 days back)
6. Fetch meeting notes with `vc +notes` + `docs +fetch`
7. Generate `pre_result` JSON with source-annotated items
