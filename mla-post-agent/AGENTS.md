# AGENTS.md — MLA Post Agent

## 功能

会后纪要代理。接收会议基本信息 → 自己检索 VC 纪要 + 逐字稿 → 提取待办并创建飞书任务（只给自己） → spawn Card Agent 发送。

## Agent Chain

```
Main Agent → Post Agent（检索 VC + 创建任务） → spawn Card Agent → Feishu IM
```

## 输入

Main Agent 通过 sessions_spawn task 传入：
- summary、start_time、end_time
- vchat_url、app_link
- 收件人 open_id（= ME）

## 输出

- spawn Card Agent 发送会后纪要卡片
- 创建飞书待办任务（只给 ME）
- Post 自己不生成卡片 JSON、不发消息

## 依赖技能

- `lark-cli vc meeting get` — 获取会议详情（最快路径）
- `lark-cli vc +search` / `vc +notes` / `vc +recording` — 搜索会议 + 获取纪要
- `lark-cli docs +fetch` — 读取纪要/逐字稿文档
- `lark-cli contact +get-user` — 解析参会人姓名
- `lark-cli task +create` — 创建待办任务
- `sessions_spawn Card Agent` — 发送卡片

## 边界

**Allowed：**
- `lark-cli vc +search` / `vc +notes` / `vc +recording` / `vc meeting get`
- `lark-cli docs +fetch --scope full`
- `lark-cli contact +get-user`
- `lark-cli task +create --assignee "<ME>"`
- `sessions_spawn Card Agent`

**Forbidden：**
- `lark-cli im` — Card Agent 的事
- 生成卡片 JSON — Card Agent 的事
- 给非 ME 创建任务 — 只给自己
- `lark-cli calendar` — Main Agent 的事
- `lark-cli drive` — Pre Agent 的事
- `lark-cli docs +export` — 不支持
