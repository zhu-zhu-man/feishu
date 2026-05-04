# TOOLS.md — MLA Pre Agent

## lark-cli 速查

### 文档搜索
```bash
lark-cli drive +search --query "<keywords>" --doc-types "docx,wiki" --sort edit_time --page-size 10 --as user --format json
```

### 读文档大纲
```bash
lark-cli docs +fetch --api-version v2 --doc "<token_or_url>" --scope outline --max-depth 2 --as user --format json
```

### 关键词精读
```bash
lark-cli docs +fetch --api-version v2 --doc "<token_or_url>" --scope keyword --keyword "关键词1|关键词2" --context-before 1 --context-after 2 --as user --format json
```

### 搜索历史会议
```bash
lark-cli vc +search --query "<keywords>" --start "<yyyy-mm-dd>" --end "<yyyy-mm-dd>" --page-size 10 --as user --format json
```

### 获取会议纪要
```bash
lark-cli vc +notes --meeting-ids "<id1,id2>" --as user --format json
```

### 读纪要文档
```bash
lark-cli docs +fetch --api-version v2 --doc "<note_doc_token>" --doc-format markdown --as user --format json
```

### 解析文档 URL
```bash
lark-cli drive metas batch_query --data '{"request_docs":[{"doc_type":"docx","doc_token":"<token>"}],"with_url":true}' --as user --format json
```
