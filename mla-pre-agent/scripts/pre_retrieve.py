"""
Pre-Meeting Retrieval Orchestrator.

Priority:
  0. Explicit links in meeting description → direct fetch
  1. Local Doc Catalog → query + fetch top candidates
  2. Feishu drive/docs search → fetch new results
  3. Historical meetings via vc +search
  4. calendar_description fallback

Usage:
  uv run python scripts/pre_retrieve.py < main_to_pre.json > evidence_bundle.json
"""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_DIR = os.path.join(PROJECT_ROOT, "var", "index")
RAW_DIR = os.path.join(PROJECT_ROOT, "var", "raw")

LARK_CLI = "lark-cli"


def find_lark_cli():
    import shutil
    resolved = shutil.which("lark-cli")
    if resolved:
        return resolved
    for c in [
        r"C:\Data\06_AppData\nodejs\npm_global\lark-cli.cmd",
        r"C:\Users\PC\AppData\Roaming\npm\lark-cli.cmd",
    ]:
        if os.path.exists(c):
            return c
    return LARK_CLI


def run_lark(args, timeout=60):
    lark = find_lark_cli()
    cmd = [lark] + args
    print(f"  [CMD] {' '.join(cmd)}", file=sys.stderr)
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, cwd=PROJECT_ROOT,
        )
    except subprocess.TimeoutExpired:
        return None, cmd, f"Timeout after {timeout}s"

    data = result.stdout.strip() or result.stderr.strip()
    exit_code = result.returncode

    try:
        parsed = json.loads(data) if data else {}
    except json.JSONDecodeError:
        return data, cmd, f"JSON parse error"

    ok = parsed.get("ok", parsed.get("code") == 0)
    if not ok:
        return None, cmd, parsed.get("msg", "unknown error")

    return parsed, cmd, None


def hash_file(path):
    if not os.path.exists(path):
        return "sha256:missing"
    with open(path, "rb") as f:
        return "sha256:" + hashlib.sha256(f.read()).hexdigest()


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_explicit_links(meeting):
    """Find explicit doc/wiki URLs in meeting description."""
    import re
    links = []
    desc = meeting.get("description", "")
    feishu_doc_pattern = re.compile(
        r'https?://[^\s]*?(?:feishu\.cn|bytedance\.net|larkoffice\.com)[^\s]*?(?:docx|wiki|docs|doc)[^\s]*',
        re.IGNORECASE,
    )
    for match in feishu_doc_pattern.finditer(desc):
        links.append({"url": match.group(), "type": "explicit_url"})
    return links


def fetch_doc(token, scope="outline", keyword=""):
    args = [
        "docs", "+fetch",
        "--api-version", "v2",
        "--doc", token,
        "--scope", scope,
        "--as", "user",
        "--format", "json",
    ]
    if scope == "outline":
        args.insert(4, "--max-depth")
        args.insert(5, "2")
    if scope == "keyword" and keyword:
        args.insert(4, "--keyword")
        args.insert(5, keyword)
        args.insert(6, "--context-before")
        args.insert(7, "1")
        args.insert(8, "--context-after")
        args.insert(9, "2")

    parsed, cmd, err = run_lark(args)
    return parsed, cmd, err


def main():
    raw_input = sys.stdin.read()
    inp = json.loads(raw_input)

    meeting = inp.get("meeting", {})
    idempotency_key = inp.get("idempotency_key", "unknown")
    event_id = meeting.get("event_id", "unknown")

    trace_commands = []
    fetched_evidence = []
    catalog_results = {"enabled": False, "candidates_found": 0, "top_matches": []}
    feishu_results = []
    warnings = []

    ts = datetime.now().strftime("%Y%m%dT%H%M%S")

    # === Priority 0: Explicit links ===
    explicit_links = extract_explicit_links(meeting)
    for link in explicit_links:
        print(f"Priority 0: Explicit link {link['url'][:80]}", file=sys.stderr)
        # Try to resolve the link to a doc token
        # This is complex; for now, record as found
        warnings.append({
            "code": "EXPLICIT_LINK_FOUND",
            "message": f"Explicit doc link in description: {link['url'][:100]}",
        })

    # === Priority 1: Local Catalog ===
    catalog_enabled = os.path.exists(os.path.join(INDEX_DIR, "doc_summaries.jsonl"))
    catalog_candidates = []

    if catalog_enabled:
        print("Priority 1: Local catalog", file=sys.stderr)
        # Call query_doc_catalog.py
        query_script = os.path.join(PROJECT_ROOT, "scripts", "query_doc_catalog.py")
        try:
            result = subprocess.run(
                ["uv", "run", "python", query_script],
                input=json.dumps(inp),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                cwd=PROJECT_ROOT,
            )
            cat_output = json.loads(result.stdout) if result.stdout else {}
            catalog_candidates = cat_output.get("candidates", [])
            catalog_results = {
                "enabled": True,
                "index_path": os.path.join(INDEX_DIR, "doc_summaries.jsonl"),
                "index_doc_count": cat_output.get("index_meta", {}).get("doc_count", 0),
                "index_updated_at": cat_output.get("index_meta", {}).get("last_build_at"),
                "candidates_found": len(catalog_candidates),
                "top_matches": catalog_candidates[:5],
            }
            print(f"  Found {len(catalog_candidates)} catalog matches", file=sys.stderr)
        except Exception as e:
            warnings.append({"code": "CATALOG_QUERY_FAILED", "message": str(e)})

    # === Priority 2: Feishu drive/docs search ===
    print("Priority 2: Feishu search", file=sys.stderr)
    # Use query terms from catalog output or extract from meeting
    search_queries = []
    if catalog_candidates:
        # Extract terms from top match reasons
        reasons_set = set()
        for c in catalog_candidates[:5]:
            for r in c.get("match_reasons", []):
                parts = r.split(":", 1)
                if len(parts) == 2:
                    reasons_set.add(parts[1])
        search_queries = list(reasons_set)[:6]
    else:
        # Fallback: use meeting summary keywords
        summary = meeting.get("summary", "")
        search_queries = [summary[:30]] if summary else ["agent"]

    for query in search_queries[:6]:  # max 6 queries
        query_short = query[:30]
        parsed, cmd, err = run_lark([
            "drive", "+search",
            "--query", query_short,
            "--doc-types", "docx,wiki",
            "--sort", "edit_time",
            "--page-size", "10",
            "--as", "user",
            "--format", "json",
        ])

        raw_name = f"{event_id}_drive_{query_short.replace(' ','_')[:20]}_{ts}.json"
        raw_path = os.path.join(RAW_DIR, "drive", raw_name)
        save_json(raw_path, parsed if parsed else {"error": str(err)})

        cmd_argv = cmd if cmd else ["lark-cli", "drive", "+search", "--query", query_short]
        result_count = 0
        if parsed and not err:
            data = parsed.get("data", [])
            if isinstance(data, dict):
                data = data.get("files", data.get("items", []))
            result_count = len(data) if isinstance(data, list) else 0

        trace_commands.append({
            "name": "drive_search",
            "query": query_short,
            "argv": cmd_argv,
            "raw_path": raw_path,
            "raw_sha256": hash_file(raw_path),
            "status": "ok" if not err else "error",
            "result_count": result_count,
        })

        if parsed and not err:
            data = parsed.get("data", [])
            if isinstance(data, dict):
                data = data.get("files", data.get("items", []))
            if isinstance(data, list):
                for doc in data[:5]:
                    token = doc.get("token", doc.get("doc_token", ""))
                    if token and not any(c.get("doc_token") == token for c in catalog_candidates):
                        feishu_results.append({
                            "doc_token": token,
                            "title": doc.get("title", doc.get("name", "")),
                            "url": doc.get("url", doc.get("doc_url", "")),
                            "source": "drive_search",
                        })

    # === Priority 3: Fetch evidence for top candidates ===
    print("Priority 3: Fetch evidence", file=sys.stderr)
    merge_list = catalog_candidates[:3] + feishu_results[:2]
    # Deduplicate
    seen_tokens = set()
    unique_candidates = []
    for c in merge_list:
        token = c.get("doc_token", "")
        if token and token not in seen_tokens:
            seen_tokens.add(token)
            unique_candidates.append(c)

    for candidate in unique_candidates[:5]:
        token = candidate["doc_token"]
        title = candidate.get("title", "")
        print(f"  Fetching: {title[:60]}", file=sys.stderr)

        # Outline
        outline, cmd_outline, err_outline = fetch_doc(token, "outline")
        raw_outline = os.path.join(RAW_DIR, "docs", f"{token}_outline_{ts}.json")
        save_json(raw_outline, outline if outline else {"error": str(err_outline)})
        trace_commands.append({
            "name": "docs_fetch",
            "argv": cmd_outline if cmd_outline else [],
            "raw_path": raw_outline,
            "raw_sha256": hash_file(raw_outline),
            "status": "ok" if not err_outline else "error",
            "result_count": 1 if outline else 0,
        })

        # Keyword excerpts
        kw = "|".join(search_queries[:5]) if search_queries else "结论|风险|方案|架构"
        kw_parsed, cmd_kw, err_kw = fetch_doc(token, "keyword", kw)
        raw_kw = os.path.join(RAW_DIR, "docs", f"{token}_keyword_{ts}.json")
        save_json(raw_kw, kw_parsed if kw_parsed else {"error": str(err_kw)})
        trace_commands.append({
            "name": "docs_fetch",
            "argv": cmd_kw if cmd_kw else [],
            "raw_path": raw_kw,
            "raw_sha256": hash_file(raw_kw),
            "status": "ok" if not err_kw else "error",
            "result_count": 1 if kw_parsed else 0,
        })

        fetched_evidence.append({
            "doc_token": token,
            "title": title,
            "url": candidate.get("url", ""),
            "fetch_type": "outline+keyword",
            "raw_path": raw_outline,
            "raw_sha256": hash_file(raw_outline),
            "excerpts": [],
        })

    # === Assemble evidence bundle ===
    bundle = {
        "schema_version": "mla.evidence_bundle.v1",
        "idempotency_key": idempotency_key,
        "meeting": {
            "event_id": event_id,
            "summary": meeting.get("summary", ""),
            "description": meeting.get("description", ""),
        },
        "catalog_candidates": catalog_candidates[:5],
        "feishu_search_candidates": feishu_results[:5],
        "fetched_evidence": fetched_evidence,
        "retrieval_trace": {
            "catalog": catalog_results,
            "commands": trace_commands,
        },
    }

    print(json.dumps(bundle, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
