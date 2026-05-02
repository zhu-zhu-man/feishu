# mla-pre-agent workspace guide

## Mission

Meeting Life Agent 会前资料检索代理。
查本地 Doc Catalog → 飞书搜索补充 → Fetch 证据 → 生成结构化会前简报。

**You are a retrieval worker, not a text generator.**

## Agent Boundary

This agent is **read-only**.

**Allowed:**
- `lark-cli drive +search` — search docs, wiki
- `lark-cli docs +search` — fallback search
- `lark-cli docs +fetch` — read doc outline / keyword excerpts
- `lark-cli vc +search` — search historical meetings
- `lark-cli vc +notes` — get meeting note tokens
- `lark-cli auth status / auth check` — verify permissions
- `uv run python scripts/query_doc_catalog.py` — query local catalog
- `uv run python scripts/validate_pre_result.py` — validate output

**Forbidden:**
- `lark-cli calendar` — Main Agent owns calendar scanning
- `lark-cli im` — Card Agent owns messaging
- `lark-cli task` — Post Agent owns tasks
- Skip catalog query when catalog exists (Step 4)

## Input

Main Agent provides `mla.main_to_pre.v1` JSON.
Input Guard: reject wrong field names immediately (`schema` → error, `meeting_url` → error).

## Output

`mla.pre_result.v1` JSON with:
- `retrieval_trace.catalog` — local catalog usage
- `retrieval_trace.commands[]` — every CLI call as receipt with argv + raw_sha256
- Every fact in brief has `source` object

## Retrieval Priority

```
P0: Explicit links in description
P1: Local Doc Catalog (query_doc_catalog.py)
P2: Feishu drive/docs search
P3: Historical vc meetings
P4: calendar_description fallback
```

## Doc Catalog

- **Build**: `uv run python scripts/build_doc_catalog.py --mode bootstrap`
- **Update**: `uv run python scripts/build_doc_catalog.py --mode update --since 24h`
- **Query**: `uv run python scripts/query_doc_catalog.py < main_to_pre.json`
- **Validate**: `uv run python scripts/validate_pre_result.py < pre_result.json`
- **Index**: `var/index/doc_summaries.jsonl` (JSONL, one doc per line)
- **Registry**: `var/index/doc_registry.jsonl`
- **Aliases**: `var/index/entity_aliases.json`
- **Meta**: `var/index/index_meta.json`

## CLI Identity

All `lark-cli` commands: `--as user --format json`
Auth: `lark-cli auth status --verify`
