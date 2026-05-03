"""
Card Agent — one temp file only (var/api_body.json).

Usage:
  uv run python scripts/send.py "<text>" <template_name> <open_id> <summary> <date> <time_range> [organizer] [description]
"""
import json, os, subprocess, sys

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
                rest = line[len(emoji):].strip()
                if rest:
                    lines.append(rest)
                matched = True
                break
        if not matched and key:
            lines.append(line)
    if key and lines:
        sections[key] = "\n".join(lines)
    return sections


def replace(tmpl_str, k, v):
    return tmpl_str.replace(k, v.replace("\\","\\\\").replace('"','\\"').replace("\n","\\n"))


def main():
    if len(sys.argv) < 7:
        print("Usage: uv run python scripts/send.py <text> <template> <open_id> <summary> <date> <time_range> [organizer] [description]", file=sys.stderr)
        sys.exit(1)

    text, tpl_name, open_id = sys.argv[1], sys.argv[2], sys.argv[3]
    summary, date, time_range = sys.argv[4], sys.argv[5], sys.argv[6]
    organizer = sys.argv[7] if len(sys.argv) > 7 else ""
    desc = sys.argv[8] if len(sys.argv) > 8 else ""

    # Load template
    with open(os.path.join(ROOT, "templates", f"{tpl_name}_card.json"), "r", encoding="utf-8") as f:
        template = json.load(f)

    sec = parse_sections(text)
    tmpl_str = json.dumps(template, ensure_ascii=False)

    repl = {
        "{{meeting_summary}}": summary,
        "{{meeting_description}}": desc[:200],
        "{{meeting_date}}": date,
        "{{meeting_time_range}}": time_range,
        "{{organizer}}": organizer or "未知",
        "{{one_sentence_goal}}": sec.get("goal", "（未提供）"),
        "{{background_items}}": sec.get("background", "暂无"),
        "{{history_decisions}}": sec.get("history", "暂无"),
        "{{open_risks}}": sec.get("risks", "暂无"),
        "{{suggested_agenda}}": sec.get("agenda", "（未提供）"),
        "{{related_links}}": sec.get("links", "暂无"),
        "{{docs_searched}}": "0", "{{docs_read}}": "0",
        "{{retrieval_status}}": "MLA Pre Agent",
        # Post meeting template placeholders
        "{{meeting_time_block}}": f"{date} {time_range}",
        "{{participants_block}}": "暂无",
        "{{meeting_id}}": "190188144",
        "{{duration_minutes}}": "123",
        "{{core_conclusions}}": sec.get("goal", "暂无"),
        "{{decisions}}": sec.get("agenda", "暂无"),
        "{{footer}}": "由 Meeting Life Agent 自动生成"
    }
    for k, v in repl.items():
        tmpl_str = replace(tmpl_str, k, v)
    # Special case for action items rows (array type, no quotes)
    tmpl_str = tmpl_str.replace('"{{action_items_rows}}"', json.dumps([]))

    card = json.loads(tmpl_str)
    card_compact = json.dumps(card, ensure_ascii=False, separators=(",", ":"))

    # Only file: var/api_body.json
    body = {"receive_id": open_id, "msg_type": "interactive", "content": card_compact}
    body_path = os.path.join(VAR, "api_body.json")
    with open(body_path, "w", encoding="utf-8") as f:
        json.dump(body, f, ensure_ascii=False)

    # Send
    r = subprocess.run([
        LARK, "api", "POST", "/open-apis/im/v1/messages",
        "--params", '{"receive_id_type":"open_id"}',
        "--data", "@api_body.json", "--as", "bot",
    ], capture_output=True, encoding="utf-8", errors="replace", timeout=30, cwd=VAR)

    print(f"Return code: {r.returncode}")
    print(f"Stdout: {r.stdout}")
    print(f"Stderr: {r.stderr}")
    stdout = (r.stdout or "").strip() or (r.stderr or "").strip()
    try:
        resp = json.loads(stdout)
        msg_id = resp.get("data", {}).get("message_id", "?")
        ok = r.returncode == 0 and resp.get("code") == 0
    except json.JSONDecodeError:
        msg_id, ok = "?", False

    # Delete the temp file
    try:
        os.remove(body_path)
    except OSError:
        pass

    print(json.dumps({"status": "sent" if ok else "error", "message_id": msg_id}, ensure_ascii=False))


if __name__ == "__main__":
    main()
