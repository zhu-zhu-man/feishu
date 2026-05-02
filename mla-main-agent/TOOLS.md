# Tools — mla-main-agent

## lark-cli allowed commands

```bash
# Auth
lark-cli auth status --as user --format json
lark-cli auth check --scope "<scope>" --as user

# Calendar (会前窗口: now → now+30min)
lark-cli calendar +agenda --start "<iso>" --end "<iso>" --as user --format json

# Calendar (会后窗口: now-35min → now)
lark-cli calendar +agenda --start "<iso>" --end "<iso>" --as user --format json

# VC match (搜索已结束会议)
lark-cli vc +search --query "<keywords>" --start "<yyyy-mm-dd>" --end "<yyyy-mm-dd>" --page-size 10 --as user --format json

# Task check (可选)
lark-cli task +get-my-tasks --complete=false --page-limit 20 --as user --format json
```

## Forbidden commands

```bash
lark-cli docs ...       # Pre Agent
lark-cli drive ...      # Pre Agent
lark-cli im ...         # Card Agent
lark-cli task +create   # Post Agent
lark-cli base ...       # Not MVP
lark-cli event ...      # IM-only, not for calendar/VC
```

## Key Constraints (from real testing)

- `calendar +agenda` start_time is `{"datetime": "ISO", "timezone": "..."}` — use datetime, NOT timestamp
- `vc +search` only works for ended meetings, max 1 month window
- `calendar +agenda` returns app_link, vchat_url, organizer directly — no extra calls needed
- `lark-cli event` only supports 11 IM events — do NOT use for calendar/VC triggers
