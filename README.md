# Claude Code Monitor

Real-time monitoring dashboard for all your Claude Code sessions, agent teams, and usage analytics.

Claude Code 会话实时监控面板，追踪所有会话、Agent 团队协作与用量分析。

<p align="center">
  <img src="promo-video/promo.gif" alt="Claude Code Monitor Demo" width="720" />
</p>

<p align="center">
  <a href="promo-video/promo.mp4">📥 Download promo video / 下载演示视频 (MP4)</a>
</p>

## Features / 功能特性

- **Real-time Session Monitoring / 实时会话监控** — Track active, recent, and idle sessions across all projects via WebSocket streaming (3s refresh) / 通过 WebSocket 实时追踪所有项目的活跃、最近和空闲会话（3秒刷新）
- **Agent Topology Visualization / Agent 拓扑可视化** — View team structures, task lists, and inter-agent message flows in real time / 实时查看团队结构、任务列表和 Agent 间消息流
- **Conversation Preview / 对话预览** — Expand any session to see recent conversation turns (user/assistant/tool calls) / 展开任意会话查看最近的对话（用户/助手/工具调用）
- **Global Analytics / 全局分析** — Model usage breakdown, token consumption, 24-hour hourly activity chart / 模型使用分布、Token 消耗、24小时活跃度图表
- **Team Coordination / 团队协作** — Monitor team members, task assignments, inbox messages, and collaboration flows / 监控团队成员、任务分配、收件箱消息和协作流程
- **Mobile Dashboard / 移动端面板** — Touch-friendly mobile UI with bottom tab navigation, auto-detected via User-Agent / 触屏友好的移动端 UI，底部标签导航，自动识别移动设备

## Quick Start / 快速开始

### Prerequisites / 前置要求

- Python 3.10+

### Install & Run / 安装与运行

```bash
git clone https://github.com/nieao/claude-monitor.git
cd claude-monitor
pip install -r requirements.txt
python server.py
```

Dashboard opens at / 面板地址：**http://localhost:5555**

### Windows

Double-click `start.bat` — it handles dependency checks, port cleanup, and auto-opens the browser.

双击 `start.bat` 即可启动 — 自动检查依赖、清理端口并打开浏览器。

## Architecture / 架构

```
~/.claude/                          Claude Code local data / 本地数据
├── projects/                       Session JSONL files / 会话文件
├── teams/                          Team configs & inboxes / 团队配置与收件箱
├── tasks/                          Task definitions / 任务定义
├── stats-cache.json                Global statistics / 全局统计
└── history.jsonl                   Activity log / 活动日志
        │
        ▼  (server.py reads every 3s / 每3秒读取)
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

## Mobile Support / 移动端支持

Access from your phone at `http://<your-ip>:5555` — mobile User-Agent is auto-detected and redirected to the mobile UI.

手机访问 `http://<你的IP>:5555`，自动识别移动设备并跳转到移动端 UI。也可直接访问 `http://<你的IP>:5555/m`。

- Bottom tab navigation (Overview / Projects / Stats / Teams) / 底部标签导航（概览/项目/统计/团队）
- Full-width cards optimized for touch / 全宽卡片，触屏优化
- Safe area support for notched devices / 刘海屏安全区域适配
- Badge indicators for active sessions and teams / 活跃会话和团队角标提示

## Tech Stack / 技术栈

| Layer / 层级 | Technology / 技术 |
|-------|-----------|
| Backend / 后端 | Python, FastAPI, Uvicorn |
| Frontend / 前端 | Vanilla HTML / CSS / JS |
| Communication / 通信 | WebSocket (3s interval) |
| Data Source / 数据源 | Local filesystem (`~/.claude/`) |

## Files / 文件结构

```
claude-monitor/
├── server.py          Backend — data collection & WebSocket / 后端 — 数据采集与 WebSocket
├── index.html         Desktop dashboard UI / 桌面端面板
├── mobile.html        Mobile dashboard UI / 移动端面板
├── requirements.txt   Python dependencies / Python 依赖
├── start.bat          Windows startup script / Windows 启动脚本
└── stop.bat           Windows stop script / Windows 停止脚本
```

## License / 许可证

MIT
