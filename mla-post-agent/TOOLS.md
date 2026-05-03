# TOOLS.md — MLA Post Agent

## lark-cli Commands

### Auth
```bash
lark-cli auth status --verify
```

### VC Search
```bash
lark-cli vc +search --query "<keywords>" --start "<yyyy-mm-dd>" --end "<yyyy-mm-dd>" --page-size 10 --as user --format json
```
Save raw to `var/vc_search.json`

### VC Notes
```bash
lark-cli vc +notes --meeting-ids "<meeting_id>" --as user --format json
```
Returns note_doc_token + verbatim_doc_token. Save to `var/vc_notes.json`

### Docs Fetch
```bash
lark-cli docs +fetch --doc "<token>" --scope full --as user --format json
```
Save to `var/docs_fetch.json`

### Contact
```bash
lark-cli contact +get-user --user-id "<open_id>" --as user --format json
```

## Scripts

```bash
uv run python scripts/validate_post_result.py < post_result.json
```

## Cross-Agent Contracts

- Input: `mla.main_to_post.v1` (from Main Agent)
- Output: `mla.post_result.v1` (consumed by Card Agent)
- Card Agent fills `templates/post_meeting_card.json` from post_result
