"""
Build / update the local Doc Catalog.

Usage:
  uv run python scripts/build_doc_catalog.py --mode bootstrap
  uv run python scripts/build_doc_catalog.py --mode update --since 24h

Mechanical work only (CLI calls, dedup, save raw). Summary generation is
done by the Agent reading catalog_summary.md and processing pending_summaries.json.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_DIR = os.path.join(PROJECT_ROOT, "var", "index")
RAW_DIR = os.path.join(PROJECT_ROOT, "var", "raw")
STATE_DIR = os.path.join(PROJECT_ROOT, "var", "state")

LARK_CLI = "lark-cli"


def find_lark_cli():
    """Find lark-cli absolute path (uv venv isolates PATH from global npm)."""
    import shutil
    resolved = shutil.which("lark-cli")
    if resolved:
        return resolved
    # Try common locations
    candidates = [
        r"C:\Data\06_AppData\nodejs\npm_global\lark-cli.cmd",
        r"C:\Users\PC\AppData\Roaming\npm\lark-cli.cmd",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return LARK_CLI


def run_lark(args, timeout=60):
    """Run lark-cli and return parsed JSON."""
    lark = find_lark_cli()
    cmd = [lark] + args
    print(f"  [CMD] {' '.join(cmd)}", file=sys.stderr)
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=PROJECT_ROOT,
        )
    except subprocess.TimeoutExpired:
        return None, None, f"Timeout after {timeout}s"

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    # Some lark-cli commands return JSON on stderr when stdout is empty
    data = stdout or stderr
    exit_code = result.returncode

    try:
        parsed = json.loads(data) if data else {}
    except json.JSONDecodeError:
        return data, None, f"JSON parse error (exit={exit_code})"

    ok = parsed.get("ok", parsed.get("code") == 0)
    if not ok:
        err_msg = parsed.get("msg", parsed.get("message", "unknown error"))
        return None, None, f"CLI error (exit={exit_code}): {err_msg}"

    return parsed, cmd, None


def hash_file(path):
    """SHA256 of file content."""
    if not os.path.exists(path):
        return "sha256:missing"
    with open(path, "rb") as f:
        return "sha256:" + hashlib.sha256(f.read()).hexdigest()


def load_jsonlines(path):
    """Load JSONL file, return list of dicts."""
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


def save_jsonlines(path, entries):
    """Save list of dicts as JSONL."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def bootstrap():
    """Full catalog rebuild."""
    meta = load_json(os.path.join(INDEX_DIR, "index_meta.json"))
    existing = load_jsonlines(os.path.join(INDEX_DIR, "doc_summaries.jsonl"))
    existing_tokens = {e["doc_token"] for e in existing}

    all_docs = {}  # token -> {token, title, url, edit_time, doc_type}
    all_raw_paths = []  # list of raw paths for tracking

    # Phase 1: Collect docs from seed queries
    seed_queries = meta.get("seed_queries", ["agent", "MLA", "Q2 需求", "产品评审"])
    for query in seed_queries:
        print(f"Searching: '{query}'", file=sys.stderr)
        parsed, cmd, err = run_lark([
            "drive", "+search",
            "--query", query,
            "--doc-types", "docx,wiki",
            "--sort", "edit_time",
            "--page-size", "10",
            "--as", "user",
            "--format", "json",
        ])

        if err:
            print(f"  ERROR: {err}", file=sys.stderr)
            continue

        # Save raw
        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        raw_name = f"build_drive_{query.replace(' ', '_')}_{ts}.json"
        raw_path = os.path.join(RAW_DIR, "drive", raw_name)
        save_json(raw_path, parsed)
        all_raw_paths.append({"name": "drive_search", "query": query, "raw_path": raw_path, "raw_sha256": hash_file(raw_path)})

        data = parsed.get("data", [])
        if isinstance(data, dict):
            data = data.get("files", data.get("items", []))
        if not isinstance(data, list):
            data = []

        for doc in data:
            token = doc.get("token", doc.get("doc_token", ""))
            if not token:
                continue
            if token in all_docs:
                continue
            all_docs[token] = {
                "doc_token": token,
                "title": doc.get("title", doc.get("name", "")),
                "url": doc.get("url", doc.get("doc_url", "")),
                "doc_type": doc.get("type", doc.get("doc_type", "docx")),
                "edit_time": doc.get("edit_time", doc.get("modified_time", "")),
            }

    print(f"\nCollected {len(all_docs)} unique docs from seed queries", file=sys.stderr)
    print(f"Already in catalog: {len(existing_tokens)}", file=sys.stderr)

    new_tokens = set(all_docs.keys()) - existing_tokens
    updated_tokens = set()

    # Check for updated docs (newer edit_time)
    existing_by_token = {e["doc_token"]: e for e in existing}
    for token, doc in all_docs.items():
        if token in existing_by_token:
            old = existing_by_token[token]
            if doc.get("edit_time") and old.get("edit_time"):
                if doc["edit_time"] > old["edit_time"]:
                    updated_tokens.add(token)

    to_process = new_tokens | updated_tokens
    print(f"New: {len(new_tokens)}, Updated: {len(updated_tokens)}, Total to process: {len(to_process)}", file=sys.stderr)

    if not to_process:
        print("Nothing new to process.", file=sys.stderr)
        meta["last_build_at"] = datetime.now(timezone.utc).isoformat()
        meta["doc_count"] = len(existing)
        save_json(os.path.join(INDEX_DIR, "index_meta.json"), meta)
        return {"status": "ok", "new_docs": 0, "updated_docs": 0, "total_docs": len(existing)}

    # Phase 2: Fetch outlines for new/updated docs
    pending = []
    for token in sorted(to_process):
        doc = all_docs[token]
        print(f"Fetching outline: {doc['title'][:60]}", file=sys.stderr)
        parsed, cmd, err = run_lark([
            "docs", "+fetch",
            "--api-version", "v2",
            "--doc", token,
            "--scope", "outline",
            "--max-depth", "2",
            "--as", "user",
            "--format", "json",
        ])

        ts = datetime.now().strftime("%Y%m%dT%H%M%S")
        raw_name = f"{token}_outline_{ts}.json"
        raw_path = os.path.join(RAW_DIR, "docs", raw_name)
        save_json(raw_path, parsed if parsed else {"error": str(err)})
        all_raw_paths.append({"name": "docs_fetch", "doc_token": token, "scope": "outline", "raw_path": raw_path, "raw_sha256": hash_file(raw_path)})

        # Phase 3: Fetch keyword excerpts
        print(f"Fetching keywords: {doc['title'][:60]}", file=sys.stderr)
        parsed2, cmd2, err2 = run_lark([
            "docs", "+fetch",
            "--api-version", "v2",
            "--doc", token,
            "--scope", "keyword",
            "--keyword", "风险|阻塞|结论|待办|方案|背景|目标|架构|流程|问题|优化",
            "--context-before", "1",
            "--context-after", "2",
            "--as", "user",
            "--format", "json",
        ])

        raw_name2 = f"{token}_keyword_{ts}.json"
        raw_path2 = os.path.join(RAW_DIR, "docs", raw_name2)
        save_json(raw_path2, parsed2 if parsed2 else {"error": str(err2)})
        all_raw_paths.append({"name": "docs_fetch", "doc_token": token, "scope": "keyword", "raw_path": raw_path2, "raw_sha256": hash_file(raw_path2)})

        pending.append({
            "doc_token": token,
            "title": doc["title"],
            "url": doc["url"],
            "doc_type": doc.get("doc_type", "docx"),
            "edit_time": doc.get("edit_time", ""),
            "outline_raw_path": raw_path,
            "keyword_raw_path": raw_path2,
        })

    # Phase 4: Write pending_summaries.json for the Agent to process
    pending_path = os.path.join(INDEX_DIR, "pending_summaries.json")
    save_json(pending_path, {
        "schema_version": "mla.pending_summaries.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(pending),
        "docs": pending,
    })

    print(f"\nWrote {len(pending)} docs to pending_summaries.json", file=sys.stderr)
    print(f"Agent: read each outline/keyword raw file, follow prompts/catalog_summary.md,", file=sys.stderr)
    print(f"       and append catalog entries to var/index/doc_summaries.jsonl", file=sys.stderr)

    return {
        "status": "ok",
        "new_docs": len(new_tokens),
        "updated_docs": len(updated_tokens),
        "total_docs": len(existing) + len(new_tokens),
        "pending_summaries": len(pending),
        "pending_path": pending_path,
    }


def update_catalog(since_hours=24):
    """Incremental update: search recently edited docs."""
    meta = load_json(os.path.join(INDEX_DIR, "index_meta.json"))

    since_iso = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).strftime("%Y-%m-%dT%H:%M:%S+08:00")

    print(f"Incremental update, since={since_iso}", file=sys.stderr)

    # Use a broad query to find recently edited docs
    parsed, cmd, err = run_lark([
        "drive", "+search",
        "--query", "agent",
        "--doc-types", "docx,wiki",
        "--sort", "edit_time",
        "--page-size", "10",
        "--as", "user",
        "--format", "json",
    ])

    if err:
        print(f"ERROR: {err}", file=sys.stderr)
        return {"status": "error", "error": err}

    existing = load_jsonlines(os.path.join(INDEX_DIR, "doc_summaries.jsonl"))
    existing_tokens = {e["doc_token"] for e in existing}

    # The rest follows the same pattern as bootstrap
    print(f"Found {len(parsed.get('data', []))} recent docs", file=sys.stderr)

    # For simplicity, re-run bootstrap targeting recent docs
    # In production, this would do a more targeted diff
    result = bootstrap()
    result["mode"] = "update"
    return result


def main():
    parser = argparse.ArgumentParser(description="Build/update Doc Catalog")
    parser.add_argument("--mode", choices=["bootstrap", "update"], default="bootstrap")
    parser.add_argument("--since", type=str, default="24h", help="For update mode: time window (e.g., 24h, 7d)")
    args = parser.parse_args()

    # Verify auth first
    print("Checking auth...", file=sys.stderr)
    _, _, auth_err = run_lark(["auth", "status", "--verify"], timeout=15)
    if auth_err:
        print(f"AUTH ERROR: {auth_err}", file=sys.stderr)
        sys.exit(1)

    if args.mode == "update":
        hours = 24
        if args.since.endswith("h"):
            hours = int(args.since[:-1])
        elif args.since.endswith("d"):
            hours = int(args.since[:-1]) * 24
        result = update_catalog(since_hours=hours)
    else:
        result = bootstrap()

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
