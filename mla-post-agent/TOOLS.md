# TOOLS.md — MLA Post Agent

## CLI 接口

### vc meeting get（最快路径）

```bash
lark-cli vc meeting get --params '{"meeting_id":"<id>","query_mode":1,"with_participants":true}' --as user --format json
# query_mode=0: 会议信息  query_mode=1: + related_artifacts（note_doc_token, verbatim_doc_token）
```

### vc +search

```bash
lark-cli vc +search --query "<关键词>" --start "<yyyy-mm-dd>" --end "<yyyy-mm-dd次日>" --page-size 10 --as user --format json
```

### vc +notes

```bash
lark-cli vc +notes --meeting-ids "<meeting_id>" --as user --format json
# 返回 note_doc_token + verbatim_doc_token
```

### vc +recording

```bash
lark-cli vc +recording --meeting-ids "<meeting_id>" --as user --format json
# 返回 minute_token，再传给 vc +notes --minute-tokens
```

### docs +fetch

```bash
lark-cli docs +fetch --api-version v2 --doc "<doc_token>" --scope full --as user --format json
# ⚠ 只用 --scope full
```

### contact +get-user

```bash
lark-cli contact +get-user --user-id "<open_id>" --as user --format json
# 返回 data.user.name（display_name）
```

### task +create

```bash
lark-cli task +create \
  --summary "[会议待办] {待办内容}" \
  --description "来源：{会议标题}\n{纪要链接}" \
  --assignee "<ME>" \
  --as user
```

### sessions_spawn Card Agent

```json
{"agentId":"mla-card-agent","runtime":"subagent","context":"isolated","mode":"run","cleanup":"keep","runTimeoutSeconds":180,"task":"<task文本>"}
```

## 禁止

- `lark-cli docs +export` — 不支持
- `lark-cli docs +fetch --scope simple` — 报错，只能 full/outline/range/keyword/section
- `lark-cli im` — Card Agent 的事
