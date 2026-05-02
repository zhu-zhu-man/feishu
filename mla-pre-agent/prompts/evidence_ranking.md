# Evidence Ranking Prompt

## Instruction

对检索到的文档和会议纪要片段进行排序和去重，挑选最相关的内容进入会前简报。

## Ranking Rules

1. **标题命中 > 摘要命中**：文档标题包含会议关键词的优先
2. **最近编辑优先**：update_time 越近越优先
3. **作者相关性**：organizer 自己的文档 +1 分
4. **类型权重**：WIKI > DOCX > MINUTES > 其他
5. **去重**：同一 token 只保留一条

## Confidence Guide

- **0.9-1.0**：直接从文档/纪要中引用的原文
- **0.75-0.89**：从相关文档推断的合理结论
- **0.5-0.74**：从多个弱信号综合推断
- **<0.5**：不纳入简报

## Source Requirements

每条 evidence 必须包含：
- `type`: doc | wiki | minutes | calendar_description | vc
- `title`: 文档/会议标题
- `url`: 可点击跳转的链接
- `token`: 文档 token（用于后续 fetch）

没有 source 的 evidence 直接丢弃。

## Priority Order

处理顺序：
1. description 中的显式文档链接（最高优先级）
2. drive +search 结果中标题命中的
3. drive +search 结果中摘要命中的
4. VC notes 中的结论和待办
5. meeting.description 本身（仅兜底）
