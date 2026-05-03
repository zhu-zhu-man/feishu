# Post Extraction Rules

## 数据源优先级

1. **AI 智能纪要（note_doc）** — 最可靠。结构化摘要、章节、待办 checkbox。
2. **逐字稿（verbatim_doc）** — 补充细节。口头分工、未写入纪要的讨论。
3. **Calendar description** — 兜底。只有会议标题和描述。

## 核心结论提取 (core_conclusions)

从 AI 纪要的「总结」章节提取：
- 每条 1-2 句话，用中文
- 优先提取带 `<b>` 标签或 bullet 的内容
- 上限 5 条
- 如无总结章节，从逐字稿中提取重复次数最多的观点

## 决策事项提取 (decisions)

从逐字稿中寻找决策信号词：
- "决定"、"确定"、"就用"、"按照"
- "先这样"、"定下来"
- 技术选型、分工、流程类内容

## 待办提取 (action_items)

从 AI 纪要的 checkbox 列表提取：
- `<checkbox done="false">` → 未完成待办
- `<checkbox done="true">` → 已完成（不放入 action_items）
- `<cite type="user" user-id="ou_xxx">` → 负责人

如果纪要无 checkbox，从逐字稿中提取分工讨论：
- 寻找 "XXX 负责"、"XXX 做"、"XXX 来"
- assignee 用 display_name，不用 open_id
- 如无法确定负责人，填 "待定"

id 格式：1️⃣, 2️⃣, 3️⃣ ...

## 关键讨论点 (key_discussion_points)

从 AI 纪要的章节标题 (`<h1>`) 提取：
- 每个章节标题 = 一个讨论点
- 去重、合并相似话题
- 上限 8 条

## 相关链接 (related_links)

优先级：
1. 逐字稿链接（来自 vc +notes 的 verbatim_doc_token 构造 URL）
2. AI 纪要链接（来自 vc +notes 的 note_doc_token 构造 URL）
3. VC 会议链接（来自 meeting.vchat_url）
4. 日历事件链接（来自 meeting.app_link）

URL 构造规则：
- Doc token `xxx` → `https://jcneyh7qlo8i.feishu.cn/docx/xxx`
- Minute token — 如果可通过 minutes +search 获取
