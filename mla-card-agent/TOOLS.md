# TOOLS.md — MLA Card Agent

## send.py 用法

### pre_meeting（会前简报）

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
  --expert-ids "<open_id,open_id>"
```

### post_meeting（会后纪要）

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

## 参数说明

| 参数 | 必需 | 适用模板 | 说明 |
|------|------|---------|------|
| `--text` | ✓ | 全部 | emoji 段落文本，换行用 `\n` |
| `--template` | ✓ | 全部 | `pre_meeting` 或 `post_meeting` |
| `--open-id` | ✓ | 全部 | 收件人 open_id |
| `--summary` | | 全部 | 会议标题 |
| `--date` | | 全部 | 日期 `YYYY-MM-DD` |
| `--time-range` | | 全部 | 时间范围 `HH:MM - HH:MM` |
| `--organizer` | | 全部 | 组织者姓名 |
| `--meeting-id` | | 全部 | 会议号 |
| `--duration` | | post | 时长 |
| `--participants` | | 全部 | 参会人，顿号分隔 |
| `--meeting-url` | | pre | 日历/VC链接 |
| `--expert-ids` | | pre | 参会人 open_id，逗号分隔 |

## 临时文件

- 只写 `var/api_body.json`，send.py 发送后自动删除
- 根目录不放任何文件
