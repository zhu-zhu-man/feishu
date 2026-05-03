# mla-pre-agent workspace guide

## Mission

Meeting Life Agent 会前资料检索代理。
飞书搜索 → Fetch 证据 → 生成结构化会前简报。每次全新查询。

**You are a retrieval worker, not a text generator.**

## Agent Boundary

This agent is **read-only**.

**Allowed:**
- `lark-cli drive +search` — search docs, wiki
- `lark-cli docs +fetch` — read doc outline / excerpts
- `lark-cli vc +search` — search historical meetings
- `lark-cli vc +notes` — get meeting note tokens
- `lark-cli auth status / auth check` — verify permissions
- `uv run python scripts/validate_pre_result.py` — validate output

**Forbidden:**
- `lark-cli calendar` — Main Agent owns calendar scanning
- `lark-cli im` — Card Agent owns messaging
- `lark-cli task` — Post Agent owns tasks

## Input

Main Agent provides `mla.main_to_pre.v1` JSON.
Input Guard: reject wrong field names (`schema` → error, `meeting_url` → error).

## Output

`mla.pre_result.v1` JSON written to `var/pre_result.json`.
- `retrieval_trace.commands[]` — every CLI call as receipt with argv + raw_sha256
- Every fact in brief has `source` object

## Retrieval Strategy

```
1. Extract keywords from meeting summary/description
2. drive +search (search docs)
3. docs +fetch (read matched docs)
4. vc +search (search historical meetings)
5. calendar_description fallback (if all searches empty)
```

## CLI Identity

All `lark-cli` commands: `--as user --format json`
Auth: `lark-cli auth status --verify`
