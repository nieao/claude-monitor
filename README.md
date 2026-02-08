# Claude Code Monitor

Real-time monitoring dashboard for all your Claude Code sessions, agent teams, and usage analytics.

<p align="center">
  <img src="promo-video/promo.gif" alt="Claude Code Monitor Demo" width="720" />
</p>

<p align="center">
  <a href="promo-video/promo.mp4">📥 Download promo video (MP4)</a>
</p>

## Features

- **Real-time Session Monitoring** — Track active, recent, and idle sessions across all projects via WebSocket streaming (3s refresh)
- **Agent Topology Visualization** — View team structures, task lists, and inter-agent message flows in real time
- **Conversation Preview** — Expand any session to see recent conversation turns (user/assistant/tool calls)
- **Global Analytics** — Model usage breakdown, token consumption, 24-hour hourly activity chart
- **Team Coordination** — Monitor team members, task assignments, inbox messages, and collaboration flows
- **Mobile Dashboard** — Touch-friendly mobile UI with bottom tab navigation, auto-detected via User-Agent

## Screenshots

### Desktop Dashboard

| Overview | Session Detail |
|----------|---------------|
| ![Overview](docs/screenshots/overview.png) | ![Session](docs/screenshots/session-detail.png) |

### Agent Topology & Team Flow

![Agent Topology](docs/screenshots/agent-topology.png)

### Mobile

| Overview | Projects | Stats |
|----------|----------|-------|
| ![Mobile Overview](docs/screenshots/mobile-overview.png) | ![Mobile Projects](docs/screenshots/mobile-projects.png) | ![Mobile Stats](docs/screenshots/mobile-stats.png) |

> Screenshots above have project names and file paths blurred for privacy.

## Quick Start

### Prerequisites

- Python 3.10+

### Install & Run

```bash
git clone https://github.com/nieao/claude-monitor.git
cd claude-monitor
pip install -r requirements.txt
python server.py
```

Dashboard opens at **http://localhost:5555**

### Windows

Double-click `start.bat` — it handles dependency checks, port cleanup, and auto-opens the browser.

## Architecture

```
~/.claude/                          Claude Code local data
├── projects/                       Session JSONL files
├── teams/                          Team configs & inboxes
├── tasks/                          Task definitions
├── stats-cache.json                Global statistics
└── history.jsonl                   Activity log
        │
        ▼  (server.py reads every 3s)
┌──────────────────────────────┐
│  FastAPI Server (port 5555)  │
│  GET  /    → Desktop UI      │
│  GET  /m   → Mobile UI       │
│  WS   /ws  → Real-time data  │
└──────────────────────────────┘
        │
        ▼  WebSocket JSON stream
┌──────────────────────────────┐
│  Browser Dashboard           │
│  index.html  (Desktop)       │
│  mobile.html (Mobile)        │
└──────────────────────────────┘
```

## Mobile Support

Access from your phone at `http://<your-ip>:5555` — mobile User-Agent is auto-detected and redirected to the mobile UI.

You can also visit `http://<your-ip>:5555/m` directly.

The mobile version features:
- Bottom tab navigation (Overview / Projects / Stats / Teams)
- Full-width cards optimized for touch
- Safe area support for notched devices
- Badge indicators for active sessions and teams

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Uvicorn |
| Frontend | Vanilla HTML / CSS / JS |
| Communication | WebSocket (3s interval) |
| Data Source | Local filesystem (`~/.claude/`) |

## Files

```
claude-monitor/
├── server.py          Backend — data collection & WebSocket
├── index.html         Desktop dashboard UI
├── mobile.html        Mobile dashboard UI
├── requirements.txt   Python dependencies
├── start.bat          Windows startup script
└── stop.bat           Windows stop script
```

## License

MIT
