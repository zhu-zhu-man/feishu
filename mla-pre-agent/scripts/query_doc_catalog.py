"""
Query local Doc Catalog for a meeting.

Usage:
  uv run python scripts/query_doc_catalog.py < main_to_pre.json

Input (stdin): main_to_pre.v1 JSON
Output (stdout): catalog candidates with scores and match_reasons
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_DIR = os.path.join(PROJECT_ROOT, "var", "index")


def load_jsonlines(path):
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


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_query_terms(meeting):
    """Extract structured query terms from meeting summary + description."""
    summary = meeting.get("summary", "")
    description = meeting.get("description", "")

    # Load aliases to expand terms
    aliases_data = load_json(os.path.join(INDEX_DIR, "entity_aliases.json"), {})
    alias_map = aliases_data.get("aliases", {})

    # Build reverse alias map
    reverse_aliases = {}
    for canonical, variants in alias_map.items():
        for v in variants + [canonical]:
            reverse_aliases[v.lower()] = canonical

    text = f"{summary} {description}"

    # Extract known entities from text (case-insensitive matching against alias map)
    found_entities = set()
    text_lower = text.lower()
    for variant, canonical in reverse_aliases.items():
        if variant.lower() in text_lower:
            found_entities.add(canonical)

    # Split text into terms (Chinese chars as individual tokens, Latin as word boundaries)
    # Simple approach: extract all 2-4 char Chinese substrings and Latin words
    chinese_chars = re.findall(r'[一-鿿]+', text)
    latin_words = re.findall(r'[a-zA-Z0-9_]+', text)

    # Build terms from Chinese segments (split into 2-4 char chunks)
    project_terms = []
    agent_terms = []
    mechanism_terms = []

    for seg in chinese_chars:
        if len(seg) >= 2:
            mechanism_terms.append(seg)
            # Also extract shorter windows
            for i in range(len(seg) - 1):
                chunk = seg[i:i+2]
                if chunk not in mechanism_terms:
                    mechanism_terms.append(chunk)

    for word in latin_words:
        if len(word) >= 2:
            if word.lower() in ("mla", "q2", "q3", "q4", "okr"):
                project_terms.append(word)
            elif any(w in word.lower() for w in ("agent", "pre", "post", "card", "main")):
                agent_terms.append(word)
            else:
                mechanism_terms.append(word)

    # Add found entities
    for ent in found_entities:
        if any(w in ent.lower() for w in ("agent", "pre", "post", "card", "main", "mla")):
            agent_terms.append(ent)
        elif any(w in ent.lower() for w in ("guard", "receipt", "trace", "schema", "catalog", "spawn", "cli")):
            mechanism_terms.append(ent)
        else:
            project_terms.append(ent)

    return {
        "project_terms": list(set(project_terms)),
        "agent_terms": list(set(agent_terms)),
        "mechanism_terms": list(set(mechanism_terms)),
        "entities": list(found_entities),
        "aliases_expanded": [reverse_aliases[t] for t in found_entities if t in reverse_aliases],
    }


def score_doc(doc, query_terms, now=None):
    """Score a doc entry against query terms. Returns (score, reasons)."""
    if now is None:
        now = datetime.now(timezone.utc)

    score = 0.0
    reasons = []

    title = (doc.get("title") or "").lower()
    summary = (doc.get("summary") or "").lower()
    keywords = [k.lower() for k in doc.get("keywords", [])]
    entities = [e.lower() for e in doc.get("entities", [])]
    meeting_hints = [m.lower() for m in doc.get("meeting_hints", [])]

    all_terms = (
        [t.lower() for t in query_terms.get("project_terms", [])]
        + [t.lower() for t in query_terms.get("agent_terms", [])]
        + [t.lower() for t in query_terms.get("mechanism_terms", [])]
        + [e.lower() for e in query_terms.get("entities", [])]
    )

    # Remove duplicates while preserving order
    seen = set()
    all_terms_unique = []
    for t in all_terms:
        if t and t not in seen:
            seen.add(t)
            all_terms_unique.append(t)

    # Title match: +5 per term
    for term in all_terms_unique:
        if term in title:
            score += 5
            reasons.append(f"title:{term}")

    # Summary match: +3 per term
    for term in all_terms_unique:
        if term in summary:
            score += 3
            key = f"summary:{term}"
            if key not in reasons:
                reasons.append(key)

    # Keywords match: +3 per term
    for term in all_terms_unique:
        for kw in keywords:
            if term in kw:
                score += 3
                key = f"keyword:{term}"
                if key not in reasons:
                    reasons.append(key)
                break

    # Entities match: +4 per term
    for term in all_terms_unique:
        for ent in entities:
            if term in ent:
                score += 4
                key = f"entity:{term}"
                if key not in reasons:
                    reasons.append(key)
                break

    # Meeting hints match: +4 per term
    for term in all_terms_unique:
        for hint in meeting_hints:
            if term in hint:
                score += 4
                key = f"meeting_hint:{term}"
                if key not in reasons:
                    reasons.append(key)
                break

    # Project term match in any field: bonus +5
    proj_terms = [t.lower() for t in query_terms.get("project_terms", [])]
    for pt in proj_terms:
        if pt in title or pt in summary or any(pt in k for k in keywords) or any(pt in e for e in entities):
            score += 5
            key = f"project:{pt}"
            if key not in reasons:
                reasons.append(key)

    # Recency boost
    edit_time_str = doc.get("edit_time", "")
    try:
        if edit_time_str:
            edit_time = datetime.fromisoformat(edit_time_str)
            hours_ago = (now - edit_time).total_seconds() / 3600
            if hours_ago <= 24:
                score += 3
                reasons.append("recent_24h_boost")
            elif hours_ago <= 168:  # 7 days
                score += 2
                reasons.append("recent_7d_boost")
    except (ValueError, TypeError):
        pass

    return round(score, 1), reasons


def main():
    # Read input
    raw_input = sys.stdin.read()
    try:
        inp = json.loads(raw_input)
    except json.JSONDecodeError as e:
        print(json.dumps({"error": f"Invalid JSON input: {e}"}, ensure_ascii=False))
        sys.exit(1)

    meeting = inp.get("meeting", inp)
    if not meeting.get("event_id") and not meeting.get("summary"):
        print(json.dumps({"error": "Missing meeting.summary"}, ensure_ascii=False))
        sys.exit(1)

    # Load catalog
    docs = load_jsonlines(os.path.join(INDEX_DIR, "doc_summaries.jsonl"))
    meta = load_json(os.path.join(INDEX_DIR, "index_meta.json"), {})

    if not docs:
        print(json.dumps({
            "candidates": [],
            "index_meta": meta,
            "query_terms": extract_query_terms(meeting),
            "warning": "catalog_empty"
        }, ensure_ascii=False, indent=2))
        sys.exit(0)

    # Extract query terms
    query_terms = extract_query_terms(meeting)
    print(f"Query terms: {json.dumps(query_terms, ensure_ascii=False)}", file=sys.stderr)

    # Score all docs
    candidates = []
    for doc in docs:
        score, reasons = score_doc(doc, query_terms)
        if score > 0:
            candidates.append({
                "doc_token": doc["doc_token"],
                "title": doc["title"],
                "url": doc["url"],
                "doc_type": doc.get("doc_type", ""),
                "score": score,
                "match_reasons": reasons,
                "summary": doc.get("summary", ""),
            })

    # Sort by score descending
    candidates.sort(key=lambda c: c["score"], reverse=True)

    output = {
        "schema_version": "mla.catalog_query_result.v1",
        "query_terms": query_terms,
        "candidates": candidates[:10],  # top 10
        "index_meta": {
            "doc_count": len(docs),
            "last_build_at": meta.get("last_build_at"),
            "last_update_at": meta.get("last_update_at"),
        },
        "candidates_found": len(candidates),
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
