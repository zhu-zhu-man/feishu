# Tools — mla-pre-agent

## lark-cli allowed commands

```bash
# Auth
lark-cli auth status --as user --format json
lark-cli auth check --scope "<scope>" --as user

# Search docs (preferred)
lark-cli drive +search --query "<keywords>" --doc-types docx,wiki --sort edit_time --page-size 10 --as user --format json

# Search docs (fallback)
lark-cli docs +search --query "<keywords>" --filter '{"doc_types":["DOCX","WIKI"],"sort_type":"EDIT_TIME"}' --as user --format json

# Read doc outline
lark-cli docs +fetch --api-version v2 --doc "<token_or_url>" --scope outline --max-depth 2 --as user --format json

# Read doc keyword excerpts
lark-cli docs +fetch --api-version v2 --doc "<token_or_url>" --scope keyword --keyword "关键词1|关键词2" --context-before 1 --context-after 2 --as user --format json

# Search historical meetings
lark-cli vc +search --query "<keywords>" --start "<yyyy-mm-dd>" --end "<yyyy-mm-dd>" --page-size 10 --as user --format json

# Get meeting notes
lark-cli vc +notes --meeting-ids "<id1,id2>" --as user --format json

# Read note document
lark-cli docs +fetch --api-version v2 --doc "<note_doc_token>" --doc-format markdown --as user --format json

# Resolve doc URLs
lark-cli drive metas batch_query --data '{"request_docs":[{"doc_type":"docx","doc_token":"<token>"}],"with_url":true}' --as user --format json
```

## Forbidden commands

```bash
lark-cli calendar ...   # Main Agent only
lark-cli im ...         # Card Agent only
lark-cli task ...       # Post Agent only
lark-cli base ...       # Not in MVP
lark-cli sheets ...     # Not in MVP
lark-cli api ...        # Use shortcuts
```
