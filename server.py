"""
Claude Code Monitor - Enhanced Real-time Dashboard
Monitors all Claude Code sessions across projects with per-session detail,
agent topology, team interactions, skill usage, and sub-conversations.
"""

import ast
import asyncio
import json
import re
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse

CLAUDE_DIR = Path.home() / ".claude"
PROJECTS_DIR = CLAUDE_DIR / "projects"
STATS_FILE = CLAUDE_DIR / "stats-cache.json"
HISTORY_FILE = CLAUDE_DIR / "history.jsonl"
TEAMS_DIR = CLAUDE_DIR / "teams"
TASKS_DIR = CLAUDE_DIR / "tasks"

ACTIVE_SECS = 120
RECENT_SECS = 600
TASK_TIMING_FILE = CLAUDE_DIR / "monitor-task-timing.json"

# ── Recording State ──
RECORDING_DIR = CLAUDE_DIR / "monitor" / "recordings"
_recording_active = False
_recording_id = None           # current recording UUID
_recording_meta = {}           # {id, startTime, projects, ...}
_recording_offsets = {}        # {jsonl_path_str -> byte_offset}
_async_tasks = {}              # {task_id: {status, result, error}}

app = FastAPI(title="Claude Code Monitor")

# ── Task Timing Tracker ──

_task_start: dict[str, float] = {}       # {team:taskId -> epoch_ms}
_task_durations: dict[str, list] = {}    # {team_name -> [duration_ms, ...]}


def _load_timing():
    global _task_durations
    data = read_json(TASK_TIMING_FILE)
    if isinstance(data, dict):
        _task_durations = data


def _save_timing():
    try:
        TASK_TIMING_FILE.write_text(
            json.dumps(_task_durations, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


def track_team_tasks(teams: list[dict]):
    """Track in_progress → completed transitions, record durations."""
    now = time.time() * 1000  # ms

    for team in teams:
        tname = team.get("name", "")
        for task in team.get("tasks", []):
            key = f"{tname}:{task['id']}"
            status = task.get("status", "")

            if status == "in_progress":
                if key not in _task_start:
                    _task_start[key] = now
                task["startedAt"] = _task_start[key]

            elif status == "completed":
                if key in _task_start:
                    dur = now - _task_start[key]
                    if dur > 5000:  # ignore < 5s
                        _task_durations.setdefault(tname, [])
                        _task_durations[tname].append(round(dur))
                        _task_durations[tname] = _task_durations[tname][-50:]
                        _save_timing()
                    del _task_start[key]

        durations = _task_durations.get(tname, [])
        if durations:
            team["avgTaskMs"] = round(sum(durations) / len(durations))
            team["taskCount"] = len(durations)
        else:
            team["avgTaskMs"] = 0
            team["taskCount"] = 0


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


def get_agent_reasoning(jsonl_path: Path, max_items: int = 6) -> list[dict]:
    """Extract recent assistant reasoning snippets from a session JSONL."""
    lines = tail_lines(jsonl_path, max_items * 12)
    items = []
    for raw in lines:
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if entry.get("type") != "assistant":
            continue
        msg = entry.get("message", {})
        if not isinstance(msg, dict):
            continue
        content_str = str(msg.get("content", ""))
        if len(content_str) < 10:
            continue
        tools, text = parse_assistant_content(content_str)
        if text or tools:
            items.append({
                "text": text[:500],
                "tools": tools[:5],
                "ts": entry.get("timestamp", ""),
            })
    return items[-max_items:]


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
                        "description": td.get("description", "")[:200],
                        "activeForm": td.get("activeForm", ""),
                        "status": td.get("status", ""),
                        "owner": td.get("owner", ""),
                        "blockedBy": [
                            b for b in td.get("blockedBy", [])
                            if isinstance(b, str)
                        ],
                    })
            team_tasks.sort(key=lambda t: (
                {"in_progress": 0, "pending": 1, "completed": 2}.get(t["status"], 9),
                str(t["id"]),
            ))

        # Enrich members with task progress & reasoning from inbox msgs
        all_inbox_msgs = {}
        if inboxes_dir.exists():
            for ibf in inboxes_dir.iterdir():
                if ibf.suffix != ".json":
                    continue
                rcpt = ibf.stem
                idata = read_json(ibf)
                if isinstance(idata, list):
                    all_inbox_msgs[rcpt] = idata

        for member in members:
            mname = member["name"]
            owned = [t for t in team_tasks if t.get("owner") == mname]
            comp = sum(1 for t in owned if t["status"] == "completed")
            prog = sum(1 for t in owned if t["status"] == "in_progress")
            member["taskProgress"] = {
                "completed": comp,
                "total": len(owned),
                "inProgress": prog,
            }
            active_t = [t for t in owned if t["status"] == "in_progress"]
            member["currentActivity"] = (
                active_t[0]["activeForm"]
                if active_t and active_t[0].get("activeForm")
                else ""
            )
            # Reasoning from outgoing inbox messages
            member_reasoning = []
            for rcpt, imsgs in all_inbox_msgs.items():
                for imsg in imsgs:
                    if not isinstance(imsg, dict):
                        continue
                    if imsg.get("from") != mname:
                        continue
                    itxt = imsg.get("text", "")
                    isum = imsg.get("summary", "")
                    if itxt.startswith("{"):
                        try:
                            parsed = json.loads(itxt)
                            ptype = parsed.get("type", "")
                            if ptype in (
                                "idle_notification",
                                "shutdown_request",
                                "shutdown_response",
                                "plan_approval_request",
                                "plan_approval_response",
                            ):
                                continue
                            if ptype == "task_assignment":
                                isum = f"[TaskCreate] {parsed.get('subject', '')}"
                        except json.JSONDecodeError:
                            pass
                    display = isum or itxt[:300]
                    # Skip raw JSON that wasn't handled
                    if display.startswith("{"):
                        continue
                    member_reasoning.append({
                        "text": display[:300],
                        "ts": imsg.get("timestamp", ""),
                        "to": rcpt,
                    })
            member_reasoning.sort(key=lambda r: r.get("ts", ""))
            member["reasoning"] = member_reasoning[-6:]

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
    teams = get_teams()
    track_team_tasks(teams)

    # Enrich team members with session-based reasoning
    sess_by_cwd: dict[str, list] = {}
    for proj in projects:
        proj_path = proj.get("path", "").replace("\\", "/").rstrip("/").lower()
        if not proj_path:
            continue
        for sess in proj.get("sessions", []):
            if sess["status"] != "active":
                continue
            live = sess.get("live") or {}
            cwd = (live.get("cwd", "") or "").replace("\\", "/").rstrip("/").lower()
            key = cwd or proj_path
            sess_by_cwd.setdefault(key, []).append({
                "dirName": proj.get("dirName", ""),
                "fullId": sess.get("fullId", ""),
            })

    for team in teams:
        for member in team.get("members", []):
            mcwd = member.get("cwd", "").replace("\\", "/").rstrip("/").lower()
            if not mcwd:
                continue
            matches = sess_by_cwd.get(mcwd, [])
            if matches:
                best = matches[0]
                jp = PROJECTS_DIR / best["dirName"] / (best["fullId"] + ".jsonl")
                if jp.exists():
                    member["sessionReasoning"] = get_agent_reasoning(jp, 6)

    # Capture sessions if recording is active
    capture_sessions_if_active()

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
        "teams": teams,
        "tasks": get_tasks_summary(),
        "history": get_history(15),
        "recording": {
            "active": _recording_active,
            "id": _recording_id,
            "startTime": _recording_meta.get("startTime") if _recording_active else None,
            "capturedSessions": _recording_meta.get("capturedSessions", 0) if _recording_active else 0,
            "capturedEntries": _recording_meta.get("capturedEntries", 0) if _recording_active else 0,
        },
    }


# ── Recording Engine ──


def _recording_dir(rid: str) -> Path:
    return RECORDING_DIR / rid


def _save_recording_meta(rid: str, meta: dict):
    d = _recording_dir(rid)
    d.mkdir(parents=True, exist_ok=True)
    (d / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _load_recording_meta(rid: str) -> dict | None:
    p = _recording_dir(rid) / "meta.json"
    return read_json(p)


def start_recording() -> str:
    global _recording_active, _recording_id, _recording_meta, _recording_offsets
    rid = str(uuid.uuid4())[:8]
    _recording_active = True
    _recording_id = rid
    _recording_offsets = {}

    # Snapshot current byte offsets for all JSONL files
    if PROJECTS_DIR.exists():
        for project_dir in PROJECTS_DIR.iterdir():
            if not project_dir.is_dir():
                continue
            for f in project_dir.iterdir():
                if f.suffix == ".jsonl":
                    _recording_offsets[str(f)] = fsize(f)

    _recording_meta = {
        "id": rid,
        "startTime": datetime.now(tz=timezone.utc).isoformat(),
        "endTime": None,
        "status": "recording",
        "capturedSessions": 0,
        "capturedEntries": 0,
    }
    d = _recording_dir(rid)
    d.mkdir(parents=True, exist_ok=True)
    (d / "raw").mkdir(exist_ok=True)
    (d / "output").mkdir(exist_ok=True)
    _save_recording_meta(rid, _recording_meta)
    return rid


def stop_recording() -> dict:
    global _recording_active, _recording_id, _recording_meta, _recording_offsets
    if not _recording_active or not _recording_id:
        return {"error": "not recording"}
    # Final capture
    _do_capture()
    _recording_meta["endTime"] = datetime.now(tz=timezone.utc).isoformat()
    _recording_meta["status"] = "completed"
    _save_recording_meta(_recording_id, _recording_meta)
    result = dict(_recording_meta)
    _recording_active = False
    _recording_id = None
    _recording_meta = {}
    _recording_offsets = {}
    return result


def _do_capture():
    """Read new bytes from all session JSONL files since last offset."""
    global _recording_offsets, _recording_meta
    if not _recording_active or not _recording_id:
        return
    rid = _recording_id
    raw_dir = _recording_dir(rid) / "raw"
    captured_sessions = set()
    total_new = 0

    if not PROJECTS_DIR.exists():
        return

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        for f in project_dir.iterdir():
            if f.suffix != ".jsonl":
                continue
            key = str(f)
            old_offset = _recording_offsets.get(key, 0)
            current_size = fsize(f)
            if current_size <= old_offset:
                continue
            # Read new bytes
            try:
                with open(f, "rb") as fh:
                    fh.seek(old_offset)
                    new_data = fh.read(current_size - old_offset)
            except Exception:
                continue

            if not new_data.strip():
                continue

            # Avoid cutting in the middle of a UTF-8 char or a JSON line:
            # Find the last newline and only consume up to there
            last_nl = new_data.rfind(b"\n")
            if last_nl == -1:
                # No complete line yet, skip and retry next cycle
                continue
            complete_data = new_data[: last_nl + 1]
            _recording_offsets[key] = old_offset + len(complete_data)

            # Write to raw file
            safe_name = project_dir.name + "_" + f.stem + ".jsonl"
            raw_file = raw_dir / safe_name
            try:
                with open(raw_file, "ab") as out:
                    out.write(complete_data)
            except Exception:
                continue

            lines = complete_data.decode("utf-8", errors="replace").strip().split("\n")
            total_new += len([l for l in lines if l.strip()])
            captured_sessions.add(f.stem[:8])

    _recording_meta["capturedSessions"] = max(
        _recording_meta.get("capturedSessions", 0), len(captured_sessions)
    )
    _recording_meta["capturedEntries"] = (
        _recording_meta.get("capturedEntries", 0) + total_new
    )
    _save_recording_meta(rid, _recording_meta)


def capture_sessions_if_active():
    """Called from collect_all() when recording is active."""
    if _recording_active:
        _do_capture()


def generate_documents(rid: str) -> dict:
    """Parse raw JSONL files and generate conversation.json + conversation.md."""
    raw_dir = _recording_dir(rid) / "raw"
    out_dir = _recording_dir(rid) / "output"
    out_dir.mkdir(exist_ok=True)

    if not raw_dir.exists():
        return {"error": "no raw data"}

    conversations = []
    for raw_file in sorted(raw_dir.glob("*.jsonl")):
        session_id = raw_file.stem
        turns = []
        try:
            text = raw_file.read_text(encoding="utf-8", errors="replace")
            for line in text.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                entry_type = entry.get("type", "")
                ts = entry.get("timestamp", "")
                msg = entry.get("message", {})
                if not isinstance(msg, dict):
                    continue

                if entry_type == "user":
                    content = msg.get("content", "")
                    text_content = ""
                    if isinstance(content, str):
                        text_content = content.strip()
                    elif isinstance(content, list):
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                text_content = part.get("text", "").strip()
                                break
                    if text_content:
                        turns.append({
                            "role": "user",
                            "text": text_content,
                            "timestamp": ts,
                        })

                elif entry_type == "assistant":
                    content_str = str(msg.get("content", ""))
                    tools, text_out = parse_assistant_content(content_str)
                    turn = {"role": "assistant", "timestamp": ts}
                    if text_out:
                        turn["text"] = text_out
                    if tools:
                        turn["tools"] = tools
                    if text_out or tools:
                        turns.append(turn)
        except Exception:
            continue

        if turns:
            conversations.append({"sessionId": session_id, "turns": turns})

    # Write JSON
    json_data = {
        "recordingId": rid,
        "generatedAt": datetime.now(tz=timezone.utc).isoformat(),
        "sessions": conversations,
    }
    (out_dir / "conversation.json").write_text(
        json.dumps(json_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Write MD
    md_lines = [f"# Recording {rid}\n"]
    md_lines.append(f"Generated: {json_data['generatedAt']}\n")
    for conv in conversations:
        md_lines.append(f"\n## Session: {conv['sessionId']}\n")
        for turn in conv["turns"]:
            role = turn["role"].upper()
            ts = turn.get("timestamp", "")
            ts_str = f" ({ts})" if ts else ""
            if turn["role"] == "user":
                md_lines.append(f"\n**USER**{ts_str}:\n{turn['text']}\n")
            elif turn["role"] == "assistant":
                md_lines.append(f"\n**ASSISTANT**{ts_str}:")
                if turn.get("text"):
                    md_lines.append(f"\n{turn['text']}\n")
                if turn.get("tools"):
                    md_lines.append(
                        f"\nTools: {', '.join(turn['tools'])}\n"
                    )
    (out_dir / "conversation.md").write_text(
        "\n".join(md_lines), encoding="utf-8"
    )

    # Update meta
    meta = _load_recording_meta(rid) or {}
    meta["hasDocuments"] = True
    _save_recording_meta(rid, meta)

    return {
        "ok": True,
        "files": ["conversation.json", "conversation.md"],
        "sessions": len(conversations),
    }


async def run_claude_cli(prompt: str, input_text: str) -> str:
    """Run claude CLI with --print flag, pipe input via stdin."""
    proc = await asyncio.create_subprocess_exec(
        "claude", "--print", "-p", prompt,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(input=input_text.encode("utf-8"))
    if proc.returncode != 0:
        err = stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Claude CLI failed: {err}")
    return stdout.decode("utf-8", errors="replace")


async def generate_summary(rid: str, custom_prompt: str = "") -> dict:
    """Generate a phase summary using Claude CLI."""
    out_dir = _recording_dir(rid) / "output"
    md_file = out_dir / "conversation.md"
    if not md_file.exists():
        # Generate docs first
        generate_documents(rid)
    if not md_file.exists():
        return {"error": "no conversation data"}

    content = md_file.read_text(encoding="utf-8", errors="replace")
    prompt = custom_prompt or "请对以下对话记录进行阶段性总结，提取关键决策、完成的任务、遇到的问题和下一步计划。使用中文输出，格式为 Markdown。"
    result = await run_claude_cli(prompt, content)
    (out_dir / "summary.md").write_text(result, encoding="utf-8")

    meta = _load_recording_meta(rid) or {}
    meta["hasSummary"] = True
    _save_recording_meta(rid, meta)
    return {"ok": True, "file": "summary.md"}


async def generate_skill(rid: str) -> dict:
    """Generate a skill document using Claude CLI."""
    out_dir = _recording_dir(rid) / "output"
    # Prefer summary, fallback to conversation
    src = out_dir / "summary.md"
    if not src.exists():
        src = out_dir / "conversation.md"
    if not src.exists():
        return {"error": "no content to generate skill from"}

    content = src.read_text(encoding="utf-8", errors="replace")
    prompt = "请基于以下总结/对话记录，生成一份标准化的 Claude Code Skill 文档。包含 skill 名称、触发条件、执行步骤和注意事项。使用中文输出，格式为 Markdown。"
    result = await run_claude_cli(prompt, content)
    (out_dir / "skill.md").write_text(result, encoding="utf-8")

    meta = _load_recording_meta(rid) or {}
    meta["hasSkill"] = True
    _save_recording_meta(rid, meta)
    return {"ok": True, "file": "skill.md"}


def list_recordings() -> list[dict]:
    """List all recordings with metadata."""
    if not RECORDING_DIR.exists():
        return []
    recordings = []
    for d in sorted(RECORDING_DIR.iterdir(), reverse=True):
        if not d.is_dir():
            continue
        meta = read_json(d / "meta.json")
        if not isinstance(meta, dict):
            continue
        # Check output files
        out_dir = d / "output"
        meta["files"] = []
        if out_dir.exists():
            for f in out_dir.iterdir():
                if f.is_file():
                    meta["files"].append(f.name)
        recordings.append(meta)
    return recordings


# ── Recording API Endpoints ──


@app.get("/api/recording/status")
async def recording_status():
    return {
        "active": _recording_active,
        "recordingId": _recording_id,
        "startTime": _recording_meta.get("startTime"),
        "capturedSessions": _recording_meta.get("capturedSessions", 0),
        "capturedEntries": _recording_meta.get("capturedEntries", 0),
    }


@app.post("/api/recording/start")
async def recording_start():
    if _recording_active:
        return {"error": "already recording", "recordingId": _recording_id}
    rid = start_recording()
    return {"ok": True, "recordingId": rid}


@app.post("/api/recording/stop")
async def recording_stop():
    result = stop_recording()
    return result


@app.get("/api/recording/list")
async def recording_list():
    return list_recordings()


@app.post("/api/recording/{rid}/generate")
async def recording_generate(rid: str):
    d = _recording_dir(rid)
    if not d.exists():
        return {"error": "recording not found"}
    return generate_documents(rid)


@app.post("/api/recording/{rid}/summarize")
async def recording_summarize(rid: str, request: Request):
    d = _recording_dir(rid)
    if not d.exists():
        return {"error": "recording not found"}
    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    custom_prompt = body.get("prompt", "")
    task_id = str(uuid.uuid4())[:8]
    _async_tasks[task_id] = {"status": "running", "result": None, "error": None}

    async def _run():
        try:
            result = await generate_summary(rid, custom_prompt)
            _async_tasks[task_id] = {"status": "done", "result": result, "error": None}
        except Exception as e:
            _async_tasks[task_id] = {"status": "error", "result": None, "error": str(e)}

    asyncio.create_task(_run())
    return {"ok": True, "taskId": task_id}


@app.post("/api/recording/{rid}/gen-skill")
async def recording_gen_skill(rid: str):
    d = _recording_dir(rid)
    if not d.exists():
        return {"error": "recording not found"}
    task_id = str(uuid.uuid4())[:8]
    _async_tasks[task_id] = {"status": "running", "result": None, "error": None}

    async def _run():
        try:
            result = await generate_skill(rid)
            _async_tasks[task_id] = {"status": "done", "result": result, "error": None}
        except Exception as e:
            _async_tasks[task_id] = {"status": "error", "result": None, "error": str(e)}

    asyncio.create_task(_run())
    return {"ok": True, "taskId": task_id}


@app.get("/api/recording/{rid}/files/{filename}")
async def recording_file(rid: str, filename: str):
    d = _recording_dir(rid) / "output"
    # Sanitize filename
    safe = Path(filename).name
    fp = d / safe
    if not fp.exists() or not fp.is_file():
        return PlainTextResponse("not found", status_code=404)
    media = "application/json" if safe.endswith(".json") else "text/markdown"
    return FileResponse(fp, media_type=media, filename=safe)


@app.get("/api/recording/task/{task_id}")
async def recording_task_status(task_id: str):
    task = _async_tasks.get(task_id)
    if not task:
        return {"error": "task not found"}
    return task


MOBILE_UA = re.compile(r"Mobile|Android|iPhone|iPad|iPod|webOS|BlackBerry|Opera Mini|IEMobile", re.I)


# ── Inbox API ──


@app.get("/api/teams/{team_name}/inbox/{agent_name}")
async def get_inbox(team_name: str, agent_name: str):
    inbox_file = TEAMS_DIR / team_name / "inboxes" / f"{agent_name}.json"
    if not inbox_file.exists():
        return []
    data = read_json(inbox_file)
    if not isinstance(data, list):
        return []
    result = []
    for msg in data:
        if not isinstance(msg, dict):
            continue
        text = msg.get("text", "")
        summary = msg.get("summary", "")
        msg_type = "message"
        display_text = summary or text[:200]
        if text.startswith("{"):
            try:
                parsed = json.loads(text)
                ptype = parsed.get("type", "")
                if ptype == "idle_notification":
                    msg_type = "idle"
                    display_text = "idle"
                elif ptype == "task_assignment":
                    msg_type = "task"
                    display_text = parsed.get("subject", "")[:200]
                elif ptype == "shutdown_request":
                    msg_type = "shutdown"
                    display_text = "shutdown request"
            except json.JSONDecodeError:
                pass
        result.append({
            "from": msg.get("from", ""),
            "to": agent_name,
            "type": msg_type,
            "text": display_text,
            "rawText": text[:500],
            "summary": summary,
            "timestamp": msg.get("timestamp", ""),
        })
    return result


@app.post("/api/teams/{team_name}/send")
async def send_message(team_name: str, request: Request):
    body = await request.json()
    to = body.get("to", "")
    text = body.get("text", "")
    summary = body.get("summary", "")
    if not to or not text:
        return {"error": "missing 'to' or 'text'"}
    inboxes_dir = TEAMS_DIR / team_name / "inboxes"
    if not inboxes_dir.exists():
        return {"error": f"team '{team_name}' inboxes not found"}
    inbox_file = inboxes_dir / f"{to}.json"
    data = []
    if inbox_file.exists():
        existing = read_json(inbox_file)
        if isinstance(existing, list):
            data = existing
    msg = {
        "from": "human-operator",
        "text": text,
        "summary": summary or text[:80],
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }
    data.append(msg)
    inbox_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True, "message": msg}


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

    _load_timing()
    print("\n  >> Claude Code Monitor (Enhanced)")
    print("  Desktop:  http://localhost:5555")
    print("  Mobile:   http://localhost:5555/m\n")
    uvicorn.run(app, host="0.0.0.0", port=5555, log_level="warning")
