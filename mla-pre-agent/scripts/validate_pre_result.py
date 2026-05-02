"""
Validate pre_result JSON against hard rules.

Usage:
  uv run python scripts/validate_pre_result.py < pre_result.json

Exit code 0 = valid, 1 = invalid (with errors on stdout)
"""

import json
import sys

REQUIRED_TOP_FIELDS = [
    "schema_version", "type", "status", "idempotency_key",
    "meeting", "brief", "retrieval_trace", "warnings",
]

VALID_STATUSES = ("ok", "partial", "error")
REQUIRED_SOURCE_TYPES = ("doc", "wiki", "minutes", "calendar_description", "vc")


def validate(pre_result):
    errors = []
    warnings = []

    # 1. Top-level required fields
    for field in REQUIRED_TOP_FIELDS:
        if field not in pre_result:
            errors.append(f"MISSING_TOP_FIELD: {field}")

    # 2. schema_version
    sv = pre_result.get("schema_version")
    if sv != "mla.pre_result.v1":
        errors.append(f"WRONG_SCHEMA_VERSION: expected mla.pre_result.v1, got {sv}")

    # 3. type
    if pre_result.get("type") != "pre_meeting_brief":
        errors.append(f"WRONG_TYPE: expected pre_meeting_brief, got {pre_result.get('type')}")

    # 4. status
    status = pre_result.get("status")
    if status not in VALID_STATUSES:
        errors.append(f"INVALID_STATUS: {status}")

    # 5. idempotency_key must be non-empty
    idem = pre_result.get("idempotency_key")
    if not idem or idem == "unknown":
        errors.append("MISSING_IDEMPOTENCY_KEY")

    # 6. retrieval_trace
    trace = pre_result.get("retrieval_trace", {})
    catalog = trace.get("catalog", {})
    commands = trace.get("commands", [])

    has_catalog = catalog.get("enabled") and catalog.get("candidates_found", 0) > 0
    has_commands = len(commands) > 0

    if not has_catalog and not has_commands:
        errors.append("NO_RETRIEVAL_EVIDENCE: neither catalog candidates nor command receipts found")

    # 7. Check command receipts
    for i, cmd in enumerate(commands):
        if "raw_path" not in cmd:
            errors.append(f"COMMAND_{i}_MISSING_RAW_PATH")
        if "raw_sha256" not in cmd:
            errors.append(f"COMMAND_{i}_MISSING_RAW_SHA256")

    # 8. docs_read > 0 or status != ok
    docs_read = trace.get("docs_read", 0)
    catalog_hits = catalog.get("candidates_found", 0)
    if docs_read == 0 and catalog_hits == 0 and status == "ok":
        errors.append("STATUS_OK_WITHOUT_RETRIEVAL: docs_read=0 and no catalog hits, status should be partial")

    # 9. NO_RELATED_DOCS warning check
    warning_codes = [w.get("code", "") for w in pre_result.get("warnings", [])]
    if docs_read == 0 and catalog_hits == 0:
        if "NO_RELATED_DOCS" not in warning_codes:
            warnings.append("MISSING_NO_RELATED_DOCS_WARNING")

    # 10. Each background_item / history_decision / open_risk must have source
    brief = pre_result.get("brief", {})
    for section, label in [
        (brief.get("background_items", []), "background_items"),
        (brief.get("history_decisions", []), "history_decisions"),
        (brief.get("open_risks", []), "open_risks"),
    ]:
        for i, item in enumerate(section):
            src = item.get("source", {})
            if not src:
                errors.append(f"{label}[{i}]: MISSING_SOURCE")
            elif "type" not in src or "title" not in src:
                errors.append(f"{label}[{i}]: SOURCE_MISSING_TYPE_OR_TITLE")

    # 11. No Markdown or prose in output
    # (Can't programmatically detect this, but it's a human review point)

    result = {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
    }
    return result


def main():
    raw_input = sys.stdin.read()
    pre_result = json.loads(raw_input)

    result = validate(pre_result)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result["valid"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
