"""
Claude Code Monitor - Enhanced Real-time Dashboard
Monitors all Claude Code sessions across projects with per-session detail,
agent topology, team interactions, skill usage, and sub-conversations.
"""

import ast
import asyncio
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, RedirectResponse

CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
STATS_FILE = CLAUDE_DIR / "stats-cache.json"
HISTORY_FILE = CLAUDE_DIR / "history.jsonl"
TEAMS_DIR = CLAUDE_DIR / "teams"
TASKS_DIR = CLAUDE_DIR / "tasks"

ACTIVE_SECS = 120
RECENT_SECS = 600

app = FastAPI(title="Claude Code Monitor")


# ── Utilities ──


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except Exception:
        return 0.0


def fsize(path: Path) -> int:
    try:
        return path.stat().st_size
    except Exception:
        return 0


def tail_lines(path: Path, n: int = 40) -> list[str]:
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            if size == 0:
                return []
            chunk = min(size, n * 4096)
            f.seek(size - chunk)
            data = f.read().decode("utf-8", errors="replace")
        return [l for l in data.strip().split("\n") if l.strip()][-n:]
    except Exception:
        return []


# ── Content Parsing ──


def parse_assistant_content(content_str: str) -> tuple[list[str], str]:
    """Parse assistant message content string to extract tool names and text."""
    tools = []
    text = ""
    try:
        items = ast.literal_eval(content_str)
        if isinstance(items, list):
            for item in items:
                if not isinstance(item, dict):
                    continue
                itype = item.get("type", "")
                if itype == "tool_use":
                    name = item.get("name", "")
                    if name:
                        tools.append(name)
                elif itype == "text":
                    t = item.get("text", "").strip()
                    if t:
                        text = t
    except Exception:
        # Fallback regex
        for m in re.finditer(r"'type': 'tool_use'.*?'name': '([^']+)'", content_str):
            tools.append(m.group(1))
        m = re.search(r"'type': 'text', 'text': '([^']{3,})'", content_str)
        if m:
            text = m.group(1).strip()
    return tools, text[:300]


# ── Session Live Detail ──


def get_session_live_detail(jsonl_path: Path) -> dict:
    lines = tail_lines(jsonl_path, 60)

    model = ""
    last_user_msg = ""
    last_tool = ""
    input_tokens = 0
    output_tokens = 0
    cache_read = 0
    cache_create = 0
    slug = ""
    cwd = ""
    version = ""

    for raw in lines:
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue

        if entry.get("cwd"):
            cwd = entry["cwd"]
        if entry.get("version"):
            version = entry["version"]
        if entry.get("slug"):
            slug = entry["slug"]

        entry_type = entry.get("type", "")
        msg = entry.get("message", {})

        if entry_type == "user" and isinstance(msg, dict):
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                last_user_msg = content.strip()[:200]
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text = part.get("text", "").strip()
                        if text:
                            last_user_msg = text[:200]
                            break

        elif entry_type == "assistant" and isinstance(msg, dict):
            if msg.get("model"):
                model = msg["model"]
            usage = msg.get("usage", {})
            if isinstance(usage, str):
                try:
                    usage = ast.literal_eval(usage)
                except Exception:
                    usage = {}
            if isinstance(usage, dict):
                it = usage.get("input_tokens", 0)
                ot = usage.get("output_tokens", 0)
                if it:
                    input_tokens = it
                if ot:
                    output_tokens = ot
                cache_read = usage.get("cache_read_input_tokens", 0)
                cache_create = usage.get("cache_creation_input_tokens", 0)

        elif entry_type == "progress":
            data = entry.get("data", {})
            if isinstance(data, dict) and data.get("type") == "hook_progress":
                hook_name = data.get("hookName", "")
                if ":" in hook_name:
                    last_tool = hook_name.split(":")[-1]

    return {
        "model": model,
        "lastUserMessage": last_user_msg,
        "lastTool": last_tool,
        "inputTokens": input_tokens,
        "outputTokens": output_tokens,
        "cacheRead": cache_read,
        "cacheCreate": cache_create,
        "slug": slug,
        "cwd": cwd,
        "version": version,
    }


# ── Session Conversation Extraction ──


def get_session_conversation(jsonl_path: Path, max_turns: int = 12) -> list[dict]:
    """Extract recent conversation turns from a session JSONL."""
    lines = tail_lines(jsonl_path, max_turns * 8)

    turns = []
    for raw in lines:
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue

        entry_type = entry.get("type", "")
        ts = entry.get("timestamp", "")

        if entry_type == "user":
            msg = entry.get("message", {})
            if not isinstance(msg, dict):
                continue
            content = msg.get("content", "")
            text = ""
            has_tool_result = False
            if isinstance(content, str) and content.strip():
                text = content.strip()
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            t = part.get("text", "").strip()
                            if t:
                                text = t
                        elif part.get("type") == "tool_result":
                            has_tool_result = True
            if text:
                turns.append({"role": "user", "text": text[:200], "ts": ts})
            elif has_tool_result:
                turns.append({"role": "tool_result", "text": "(tool result)", "ts": ts})

        elif entry_type == "assistant":
            msg = entry.get("message", {})
            if not isinstance(msg, dict):
                continue
            content_str = str(msg.get("content", ""))
            if len(content_str) < 10:
                continue
            tools, text = parse_assistant_content(content_str)
            if tools or text:
                turn = {"role": "assistant", "ts": ts}
                if tools:
                    turn["tools"] = tools
                if text:
                    turn["text"] = text[:200]
                turns.append(turn)

    return turns[-max_turns:]


# ── Project & Session Scanning ──


def get_all_projects() -> list[dict]:
    if not PROJECTS_DIR.exists():
        return []

    now = time.time()
    projects = []

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        index_data = read_json(project_dir / "sessions-index.json")

        if index_data and isinstance(index_data, dict):
            original_path = index_data.get("originalPath", "")
            entries = index_data.get("entries", [])
        else:
            original_path = ""
            entries = []

        if original_path:
            project_name = Path(original_path).name or original_path
            project_path = original_path
        else:
            dirname = project_dir.name
            segments = [s for s in dirname.split("-") if s]
            project_name = segments[-1] if segments else dirname
            project_path = dirname

        session_meta = {}
        for e in entries:
            sid = e.get("sessionId", "")
            if sid:
                session_meta[sid] = {
                    "summary": e.get("summary", ""),
                    "firstPrompt": e.get("firstPrompt", ""),
                    "messageCount": e.get("messageCount", 0),
                    "created": e.get("created", ""),
                    "modified": e.get("modified", ""),
                    "gitBranch": e.get("gitBranch", ""),
                    "isSidechain": e.get("isSidechain", False),
                }

        sessions = []
        has_active = False
        has_recent = False
        latest_mtime = 0.0

        for f in project_dir.iterdir():
            if f.suffix != ".jsonl":
                continue

            sid = f.stem
            mt = mtime(f)
            age = now - mt
            latest_mtime = max(latest_mtime, mt)

            if age < ACTIVE_SECS:
                status = "active"
                has_active = True
            elif age < RECENT_SECS:
                status = "recent"
                has_recent = True
            else:
                status = "idle"

            meta = session_meta.get(sid, {})

            session = {
                "sessionId": sid[:8],
                "fullId": sid,
                "status": status,
                "age": age,
                "mtime": mt,
                "fileSize": fsize(f),
                "summary": meta.get("summary", ""),
                "firstPrompt": meta.get("firstPrompt", ""),
                "messageCount": meta.get("messageCount", 0),
                "created": meta.get("created", ""),
                "modified": meta.get("modified", ""),
                "gitBranch": meta.get("gitBranch", ""),
                "isSidechain": meta.get("isSidechain", False),
                "live": None,
                "conversation": None,
            }

            if status in ("active", "recent"):
                session["live"] = get_session_live_detail(f)
                session["conversation"] = get_session_conversation(f, 12)

            sessions.append(session)

        status_order = {"active": 0, "recent": 1, "idle": 2}
        sessions.sort(key=lambda s: (status_order.get(s["status"], 9), -s["mtime"]))

        active_count = sum(1 for s in sessions if s["status"] == "active")
        recent_count = sum(1 for s in sessions if s["status"] == "recent")

        projects.append({
            "name": project_name,
            "path": project_path,
            "dirName": project_dir.name,
            "totalSessions": len(sessions),
            "activeSessions": active_count,
            "recentSessions": recent_count,
            "hasActive": has_active,
            "hasRecent": has_recent,
            "latestMtime": latest_mtime,
            "sessions": sessions,
        })

    projects.sort(key=lambda p: (
        0 if p["hasActive"] else (1 if p["hasRecent"] else 2),
        -p["latestMtime"],
    ))

    return projects


# ── Global Stats ──


def get_stats() -> dict:
    data = read_json(STATS_FILE)
    if not data:
        return {}
    return {
        "totalSessions": data.get("totalSessions", 0),
        "totalMessages": data.get("totalMessages", 0),
        "longestSession": data.get("longestSession", {}),
        "firstSessionDate": data.get("firstSessionDate", ""),
        "modelUsage": data.get("modelUsage", {}),
        "dailyActivity": data.get("dailyActivity", [])[-14:],
        "hourCounts": data.get("hourCounts", {}),
    }


# ── Teams (Enhanced with inbox messages & tasks) ──


def get_teams() -> list[dict]:
    teams = []
    if not TEAMS_DIR.exists():
        return teams

    now = time.time()
    for team_dir in TEAMS_DIR.iterdir():
        if not team_dir.is_dir():
            continue
        config = read_json(team_dir / "config.json")
        if not config:
            continue

        members = []
        inboxes_dir = team_dir / "inboxes"

        for member in config.get("members", []):
            name = member.get("name", "unknown")
            inbox_file = inboxes_dir / f"{name}.json" if inboxes_dir.exists() else None
            inbox_mt = mtime(inbox_file) if inbox_file and inbox_file.exists() else 0
            config_mt = mtime(team_dir / "config.json")
            is_active = (now - max(inbox_mt, config_mt)) < ACTIVE_SECS

            inbox_data = read_json(inbox_file) if inbox_file and inbox_file.exists() else None
            msg_count = len(inbox_data) if isinstance(inbox_data, list) else 0

            members.append({
                "name": name,
                "agentType": member.get("agentType", "unknown"),
                "model": member.get("model", "unknown"),
                "color": member.get("color", "gray"),
                "active": is_active,
                "inboxMessages": msg_count,
                "cwd": member.get("cwd", ""),
                "joinedAt": member.get("joinedAt", 0),
            })

        # Collect message flow from all inboxes
        message_flow = []
        if inboxes_dir.exists():
            for inbox_file in inboxes_dir.iterdir():
                if inbox_file.suffix != ".json":
                    continue
                recipient = inbox_file.stem
                msgs = read_json(inbox_file)
                if not isinstance(msgs, list):
                    continue
                for msg in msgs[-5:]:
                    if not isinstance(msg, dict):
                        continue
                    text = msg.get("text", "")
                    summary = msg.get("summary", "")
                    # Classify message type
                    msg_type = "message"
                    display_text = summary or text[:120]
                    if text.startswith("{"):
                        try:
                            parsed = json.loads(text)
                            ptype = parsed.get("type", "")
                            if ptype == "idle_notification":
                                msg_type = "idle"
                                display_text = "idle"
                            elif ptype == "task_assignment":
                                msg_type = "task"
                                display_text = parsed.get("subject", "")[:100]
                            elif ptype == "shutdown_request":
                                msg_type = "shutdown"
                                display_text = "shutdown request"
                        except json.JSONDecodeError:
                            pass

                    message_flow.append({
                        "from": msg.get("from", ""),
                        "to": recipient,
                        "type": msg_type,
                        "text": display_text,
                        "timestamp": msg.get("timestamp", ""),
                    })

        message_flow.sort(key=lambda m: m.get("timestamp", ""), reverse=True)

        # Load team tasks
        team_tasks = []
        team_task_dir = TASKS_DIR / team_dir.name
        if team_task_dir.exists():
            for tf in team_task_dir.glob("*.json"):
                td = read_json(tf)
                if isinstance(td, dict):
                    team_tasks.append({
                        "id": td.get("id", tf.stem),
                        "subject": td.get("subject", "")[:80],
                        "status": td.get("status", ""),
                        "owner": td.get("owner", ""),
                    })
            team_tasks.sort(key=lambda t: (
                {"in_progress": 0, "pending": 1, "completed": 2}.get(t["status"], 9),
                str(t["id"]),
            ))

        lead_id = config.get("leadAgentId", "")
        lead_name = lead_id.split("@")[0] if "@" in lead_id else ""

        teams.append({
            "name": config.get("name", team_dir.name),
            "description": config.get("description", ""),
            "memberCount": len(members),
            "members": members,
            "messageFlow": message_flow[:20],
            "tasks": team_tasks,
            "leadName": lead_name,
            "createdAt": config.get("createdAt", 0),
        })

    return teams


def get_tasks_summary() -> dict:
    total = completed = in_progress = pending = 0
    if not TASKS_DIR.exists():
        return {"total": 0, "completed": 0, "inProgress": 0, "pending": 0}

    for task_dir in TASKS_DIR.iterdir():
        if not task_dir.is_dir():
            continue
        for tf in task_dir.glob("*.json"):
            data = read_json(tf)
            if isinstance(data, dict):
                status = data.get("status", "")
                total += 1
                if status == "completed":
                    completed += 1
                elif status == "in_progress":
                    in_progress += 1
                elif status == "pending":
                    pending += 1

    return {
        "total": total,
        "completed": completed,
        "inProgress": in_progress,
        "pending": pending,
    }


def get_history(count: int = 15) -> list[dict]:
    if not HISTORY_FILE.exists():
        return []

    activities = []
    try:
        lines = tail_lines(HISTORY_FILE, count + 5)
        for raw in lines[-count:]:
            raw = raw.strip()
            if not raw:
                continue
            try:
                entry = json.loads(raw)
                ts = entry.get("timestamp", 0)
                activities.append({
                    "display": entry.get("display", "")[:200],
                    "timestamp": ts,
                    "time": datetime.fromtimestamp(
                        ts / 1000, tz=timezone.utc
                    ).strftime("%H:%M:%S") if ts else "",
                    "project": Path(entry.get("project", "")).name
                    if entry.get("project") else "",
                    "sessionId": entry.get("sessionId", "")[:8],
                })
            except Exception:
                continue
    except Exception:
        pass

    activities.reverse()
    return activities


# ── Collect All ──


def collect_all() -> dict:
    projects = get_all_projects()
    total_active = sum(p["activeSessions"] for p in projects)
    total_recent = sum(p["recentSessions"] for p in projects)
    active_projects = sum(1 for p in projects if p["hasActive"])

    return {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "summary": {
            "totalProjects": len(projects),
            "activeProjects": active_projects,
            "totalActiveSessions": total_active,
            "totalRecentSessions": total_recent,
        },
        "projects": projects,
        "stats": get_stats(),
        "teams": get_teams(),
        "tasks": get_tasks_summary(),
        "history": get_history(15),
    }


MOBILE_UA = re.compile(r"Mobile|Android|iPhone|iPad|iPod|webOS|BlackBerry|Opera Mini|IEMobile", re.I)


@app.get("/")
async def index(request: Request):
    ua = request.headers.get("user-agent", "")
    if MOBILE_UA.search(ua):
        return RedirectResponse("/m")
    return FileResponse(Path(__file__).parent / "index.html", media_type="text/html")


@app.get("/m")
async def mobile():
    return FileResponse(Path(__file__).parent / "mobile.html", media_type="text/html")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json(collect_all())
            await asyncio.sleep(3)
    except (WebSocketDisconnect, Exception):
        pass


if __name__ == "__main__":
    import uvicorn

    print("\n  >> Claude Code Monitor (Enhanced)")
    print("  Desktop:  http://localhost:5555")
    print("  Mobile:   http://localhost:5555/m\n")
    uvicorn.run(app, host="0.0.0.0", port=5555, log_level="warning")
