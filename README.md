# Meeting Life Agent (MLA)

Multi-agent system for Feishu meeting lifecycle automation.

## Agents

| Agent | Role |
|-------|------|
| `mla-main-agent` | Scheduler — scans calendar, detects changes, routes to sub-agents |
| `mla-pre-agent` | Pre-meeting researcher — local catalog + feishu search → brief |
| `mla-post-agent` | Post-meeting recorder — meeting minutes → summary + tasks |
| `mla-card-agent` | Card deliverer — sends interactive Feishu cards |

## Setup

1. Install [OpenClaw](https://docs.openclaw.ai)
2. Configure `openclaw.json` with your Feishu app credentials
3. Deploy agent workspaces
4. Build Pre Agent doc catalog: `uv run python scripts/build_doc_catalog.py --mode bootstrap`

## Agent Communication

Main Agent scans calendar → `sessions_spawn(agentId=mla-xxx-agent)` → sub-agent returns structured JSON.
