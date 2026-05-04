# TOOLS.md — MLA Card Agent

## 依赖工具

### send.py

唯一执行工具。解析 emoji 段落文本 → 填卡片模板 → `lark-cli api` 发送。

**接口：**

```
uv run python scripts/send.py \
  --text <str>          # 必需，emoji 段落文本，换行用 \n
  --template <str>      # 必需，pre_meeting | post_meeting
  --open-id <str>       # 必需，收件人 open_id
  --summary <str>       # 会议标题
  --date <str>          # YYYY-MM-DD
  --time-range <str>    # HH:MM - HH:MM
  --organizer <str>     # 组织者姓名
  --meeting-id <str>    # 会议号
  --duration <str>      # 时长（仅 post_meeting）
  --participants <str>  # 参会人（顿号分隔）
  --meeting-url <str>   # 日历/VC 链接（仅 pre_meeting）
  --expert-names <str>   # 推荐专家姓名（顿号分隔，仅 pre_meeting）
  --expert-ids <str>     # 推荐专家 open_id（逗号分隔，仅 pre_meeting）
  --expert-reasons <str> # 推荐理由（分号分隔，和专家顺序对应）
```

**pre_meeting 命令模板：**

```bash
uv run python scripts/send.py \
  --text "<简报内容>" \
  --template pre_meeting \
  --open-id "<open_id>" \
  --summary "<标题>" \
  --date "<日期>" \
  --time-range "<时间范围>" \
  --organizer "<组织者>" \
  --meeting-id "<会议ID>" \
  --participants "<参会人>" \
  --meeting-url "<app_link>" \
  --expert-names "<推荐专家姓名>" \
  --expert-ids "<推荐专家open_id>"
```

**post_meeting 命令模板：**

```bash
uv run python scripts/send.py \
  --text "<纪要内容>" \
  --template post_meeting \
  --open-id "<open_id>" \
  --summary "<标题>" \
  --date "<日期>" \
  --time-range "<时间范围>" \
  --organizer "<组织者>" \
  --meeting-id "<会议ID>" \
  --duration "<时长>" \
  --participants "<参会人>"
```

### 卡片模板

send.py 自动读取，无需手动操作：
- `templates/pre_meeting_card.json`
- `templates/post_meeting_card.json`

### 临时文件

send.py 写入 `var/api_body.json`，发送后自动删除。不碰其他路径。
