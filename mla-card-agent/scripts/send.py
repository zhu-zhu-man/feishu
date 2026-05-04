"""
Card Agent — one temp file only (var/api_body.json).

Usage:
  uv run python scripts/send.py \\
    --text "..." --template post_meeting --open-id ou_xxx \\
    --summary "标题" --date "2026-04-27" --time-range "21:15 - 21:46" \\
    --organizer "姓名" --meeting-id "302614221" --duration "31 分钟" --participants "张三、李四"
"""
import argparse, json, os, re, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAR = os.path.join(ROOT, "var")
LARK = r"C:\Data\06_AppData\nodejs\npm_global\lark-cli.cmd"
if not os.path.exists(LARK):
    import shutil
    LARK = shutil.which("lark-cli") or "lark-cli"
os.makedirs(VAR, exist_ok=True)

EMOJI_MAP = {"🎯":"goal","📄":"background","📌":"history","⚠️":"risks","📋":"agenda","🔗":"links","✅":"todos","💬":"discussion","⏱":"duration"}


def parse_sections(text):
    sections, key, lines = {}, None, []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        matched = None
        for emoji, k in EMOJI_MAP.items():
            if line.startswith(emoji):
                if key and lines:
                    sections[key] = "\n".join(lines)
                key, lines = k, []
                matched = True
                break
        if not matched and key:
            lines.append(line)
    if key and lines:
        sections[key] = "\n".join(lines)
    return sections


def parse_action_items(todos_text):
    if not todos_text:
        return []
    items = []
    for line in todos_text.split("\n"):
        line = line.strip()
        m = re.match(r'([1-9]️⃣|🔟)\s*(.+?)[：:](.+)', line)
        if m:
            items.append({"id": m.group(1), "assignee": m.group(2).strip(), "task": m.group(3).strip()})
    return items


def replace(tmpl_str, k, v):
    return tmpl_str.replace(k, v.replace("\\","\\\\").replace('"','\\"').replace("\n","\\n"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--text", required=True)
    p.add_argument("--template", required=True, choices=["pre_meeting", "post_meeting"])
    p.add_argument("--open-id", required=True)
    p.add_argument("--summary", default="")
    p.add_argument("--date", default="")
    p.add_argument("--time-range", default="")
    p.add_argument("--organizer", default="")
    p.add_argument("--meeting-id", default="")
    p.add_argument("--duration", default="")
    p.add_argument("--participants", default="")
    p.add_argument("--meeting-url", default="")
    p.add_argument("--expert-ids", default="")
    p.add_argument("--expert-names", default="")
    p.add_argument("--expert-reasons", default="")
    args = p.parse_args()

    text = args.text.replace("\\n", "\n")
    tpl_name = args.template
    open_id = args.open_id
    summary = args.summary
    date = args.date
    time_range = args.time_range
    organizer = args.organizer
    meeting_id = args.meeting_id
    duration = args.duration
    participants = args.participants

    with open(os.path.join(ROOT, "templates", f"{tpl_name}_card.json"), "r", encoding="utf-8") as f:
        template = json.load(f)

    sec = parse_sections(text)
    tmpl_str = json.dumps(template, ensure_ascii=False)
    action_items = parse_action_items(sec.get("todos", ""))
    action_count = len(action_items) if action_items else 0

    meeting_time_block = f"**{summary}**\n{date} {time_range} (GMT+8)"
    participants_block = participants or organizer or "暂无"
    dur = duration or sec.get("duration", "")
    action_items_rows = json.dumps(action_items, ensure_ascii=False)

    if tpl_name == "pre_meeting":
        meeting_url = args.meeting_url or ""
        pcount = participants if participants.isdigit() else str(len([x for x in participants.replace("、","，").split("，") if x.strip()])) if participants else "0"

        # History: split 📌 section by "已闭环" / "待跟进" markers
        history_text = sec.get("history", "")
        if "已闭环" in history_text and "待跟进" in history_text:
            parts_closed = history_text.split("待跟进")
            h_closed = parts_closed[0].replace("已闭环", "").strip().strip("：:").strip()
            h_pending = parts_closed[1].strip().strip("：:").strip() if len(parts_closed) > 1 else ""
        elif "已闭环" in history_text:
            h_closed = history_text.replace("已闭环", "").strip().strip("：:").strip()
            h_pending = "暂无"
        elif "待跟进" in history_text:
            h_closed = "暂无"
            h_pending = history_text.replace("待跟进", "").strip().strip("：:").strip()
        else:
            h_closed = history_text if history_text else "暂无历史会议结论"
            h_pending = "暂无待跟进事项"

        # History URLs: extract from 🔗 section
        links_text = sec.get("links", "")
        link_urls = re.findall(r'https?://\S+', links_text)
        h_closed_url = link_urls[0] if len(link_urls) > 0 else meeting_url
        h_pending_url = link_urls[1] if len(link_urls) > 1 else (link_urls[0] if len(link_urls) > 0 else meeting_url)

        # Add status labels back
        h_closed = f"**✓ 已闭环**\n{h_closed}"
        h_pending = f"**⏳ 待跟进**\n{h_pending}"

        # Docs: each line carries its own URL at the end
        # Format: · 标题：描述 · by 作者 · YY/MM/DD · https://url
        bg_lines = [l.strip().lstrip("·- ").strip() for l in sec.get("background", "").split("\n") if l.strip()]
        doc_columns = []
        for line in bg_lines:
            # Extract URL from end of line
            url = meeting_url
            url_m = re.search(r'\s+https?://\S+$', line)
            if url_m:
                url = url_m.group().strip()
                line = line[:url_m.start()].strip()
            # Parse metadata: · by 作者 · YY/MM/DD
            author, date = "", ""
            meta_m = re.search(r'·\s*by\s+(.+?)\s*·\s*(\d{2}/\d{2}/\d{2})', line)
            if meta_m:
                author = meta_m.group(1).strip()
                date = meta_m.group(2).strip()
                line = line[:meta_m.start()].strip()
            # Split title + desc
            m = re.split(r'[：:]', line, maxsplit=1)
            title = m[0].strip()
            desc = m[1].strip() if len(m) > 1 else ""
            header = f"**{title}**"
            if author: header += f" · by {author}"
            if date: header += f" · {date}"
            content = header + (f"\n{desc}" if desc else "")
            doc_columns.append({
                "tag": "column", "width": "weighted", "weight": 1,
                "background_style": "grey-50", "padding": "8px",
                "elements": [{
                    "tag": "interactive_container",
                    "behaviors": [{"type": "open_url", "default_url": url}],
                    "elements": [{"tag": "markdown", "content": content}]
                }]
            })
        doc_rows_json = json.dumps(doc_columns, ensure_ascii=False)

        # Expert rows: from --expert-names + --expert-ids + --expert-reasons
        expert_names = [x.strip() for x in args.expert_names.replace("、","，").split("，") if x.strip()] if args.expert_names else []
        expert_ids = [x.strip() for x in args.expert_ids.split(",") if x.strip()] if args.expert_ids else []
        expert_reasons = [x.strip() for x in args.expert_reasons.split("；") if x.strip()] if args.expert_reasons else []
        if expert_names and expert_ids and len(expert_ids) == len(expert_names):
            lines = []
            for i in range(len(expert_names)):
                reason = f" — {expert_reasons[i]}" if i < len(expert_reasons) else ""
                lines.append(f"<person id='{expert_ids[i]}' show_name=true show_avatar=true style='normal'></person>{reason}")
            expert_rows = "\n".join(lines)
        elif expert_names:
            expert_rows = "\n".join([f"• {n}" for n in expert_names])
        else:
            expert_rows = "暂无"

        # Risk items
        risk_items = sec.get("risks", "暂无风险提示")
        risk_items = "\n".join([f"• {l.strip().lstrip('·- ').strip()}" for l in risk_items.split("\n") if l.strip()])

        repl = {
            "{{meeting_summary}}": summary,
            "{{meeting_date}}": date,
            "{{meeting_time_range}}": time_range,
            "{{meeting_url}}": meeting_url,
            "{{participant_count}}": pcount,
            "{{history_closed}}": h_closed,
            "{{history_closed_url}}": h_closed_url,
            "{{history_pending}}": h_pending,
            "{{history_pending_url}}": h_pending_url,
            "{{risk_items}}": risk_items,
            "{{expert_rows}}": expert_rows,
            "{{footer}}": "🤖 MLA Pre Agent · 数据来源：飞书文档搜索 + AI 总结",
        }
        for k, v in repl.items():
            tmpl_str = replace(tmpl_str, k, v)

        tmpl_str = tmpl_str.replace('"{{doc_rows}}"', doc_rows_json)
    else:
        repl = {
            "{{meeting_time_block}}": meeting_time_block,
            "{{participants_block}}": participants_block,
            "{{meeting_id}}": meeting_id or "—",
            "{{duration_minutes}}": dur or "—",
            "{{core_conclusions}}": sec.get("goal", "暂无"),
            "{{decisions}}": sec.get("agenda", "暂无"),
            "{{key_discussion_points}}": sec.get("discussion", "暂无"),
            "{{related_links}}": sec.get("links", "暂无"),
            "{{footer}}": f"🤖 MLA Post Agent · {action_count}项待办 · 数据来源：飞书会议转写 + AI 总结",
        }

    for k, v in repl.items():
        tmpl_str = replace(tmpl_str, k, v)

    tmpl_str = tmpl_str.replace('"{{action_items_rows}}"', action_items_rows)

    card = json.loads(tmpl_str)
    card_compact = json.dumps(card, ensure_ascii=False, separators=(",", ":"))

    body = {"receive_id": open_id, "msg_type": "interactive", "content": card_compact}
    body_path = os.path.join(VAR, "api_body.json")
    with open(body_path, "w", encoding="utf-8") as f:
        json.dump(body, f, ensure_ascii=False)

    r = subprocess.run([
        LARK, "api", "POST", "/open-apis/im/v1/messages",
        "--params", '{"receive_id_type":"open_id"}',
        "--data", "@api_body.json", "--as", "bot",
    ], capture_output=True, encoding="utf-8", errors="replace", timeout=30, cwd=VAR)

    stdout = (r.stdout or "").strip() or (r.stderr or "").strip()
    try:
        resp = json.loads(stdout)
        msg_id = resp.get("data", {}).get("message_id", "?")
        ok = r.returncode == 0 and resp.get("code") == 0
    except json.JSONDecodeError:
        msg_id, ok = "?", False

    try:
        os.remove(body_path)
    except OSError:
        pass

    print(json.dumps({"status": "sent" if ok else "error", "message_id": msg_id}, ensure_ascii=False))


if __name__ == "__main__":
    main()
