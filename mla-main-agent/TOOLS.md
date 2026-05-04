# TOOLS.md — MLA Main Agent

## lark-cli 速查

### Auth
```bash
lark-cli auth status --verify
```

### 日历扫描（固定窗口 [now-35min, now+30min]）
```bash
lark-cli calendar +agenda --start "<iso>" --end "<iso>" --as user --format json
```

## 关键约束

- `calendar +agenda` 返回字段包含 `app_link`、`vchat_url`、`organizer`，不需要额外调用
- `calendar +agenda` 时间参数用 ISO 8601 格式（`2026-05-04T12:00:00+08:00`），不是 unix timestamp
- spawn 必须指定 `agentId`，`context: "isolated"`
- 不要自己调 `vc`、`docs`、`drive`、`im`、`task` — 那是子 Agent 的事
