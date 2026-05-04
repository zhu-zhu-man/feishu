# TOOLS.md — MLA Post Agent

## lark-cli 速查

### 会议详情（最快路径）
```bash
lark-cli vc meeting get --params '{"meeting_id":"<id>","query_mode":1,"with_participants":true}' --as user --format json
```
`query_mode=0` 只查会议信息，`query_mode=1` 返回 `related_artifacts.note_doc_token` + `verbatim_doc_token`。

### VC 搜索
```bash
lark-cli vc +search --query "<keywords>" --start "<yyyy-mm-dd>" --end "<yyyy-mm-dd>" --page-size 10 --as user --format json
```

### 获取纪要
```bash
lark-cli vc +notes --meeting-ids "<meeting_id>" --as user --format json
```

### 妙记路线（纪要不可用时）
```bash
lark-cli vc +recording --meeting-ids "<meeting_id>" --as user --format json
lark-cli vc +notes --minute-tokens "<minute_token>" --as user --format json
```

### 读文档
```bash
lark-cli docs +fetch --api-version v2 --doc "<doc_token>" --scope full --as user --format json
```
只用 `--scope full`。simple/outline 会报参数错误。

### 解析参会人姓名
```bash
lark-cli contact +get-user --user-id "<open_id>" --as user --format json
```

### 创建待办
```bash
lark-cli task +create \
  --summary "[会议待办] {内容}" \
  --description "来源：{标题}\n{链接}" \
  --assignee "<open_id>" \
  --as user
```

## 参考

- `lark-cli docs +export` 不支持，不要用
- `lark-cli im` 禁止 — Card Agent 的事
- 不要往根目录写临时文件
