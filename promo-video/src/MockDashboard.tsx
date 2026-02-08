import React from "react";

/*
 * MockDashboard — a visual replica of the Claude Code Monitor desktop UI.
 * All project names, file paths, session IDs, and user prompts are
 * rendered with a CSS blur filter so no real data is exposed.
 */

const C = {
  bg0: "#0a0e14", bg1: "#0d1117", bg2: "#161b22", bg3: "#1c2333",
  border: "#30363d", t1: "#e6edf3", t2: "#8b949e", t3: "#484f58",
  blue: "#58a6ff", green: "#3fb950", orange: "#d29922", purple: "#bc8cff", teal: "#39d2c0",
};

const BLUR: React.CSSProperties = { filter: "blur(5px)", userSelect: "none" };
const FONT: React.CSSProperties = { fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace" };

/* ── Tiny helpers ── */
const Dot: React.FC<{ color: string; pulse?: boolean }> = ({ color, pulse }) => (
  <div style={{ width: 8, height: 8, borderRadius: "50%", background: color, flexShrink: 0, boxShadow: pulse ? `0 0 6px ${color}` : "none" }} />
);

const Badge: React.FC<{ text: string; bg: string; color: string }> = ({ text, bg, color }) => (
  <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 8, background: bg, color, fontWeight: 500 }}>{text}</span>
);

/* ── Header ── */
const Header: React.FC = () => (
  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 20px", borderBottom: `1px solid ${C.border}`, background: C.bg2, ...FONT }}>
    <div style={{ fontSize: 18, fontWeight: 700, background: `linear-gradient(135deg, ${C.blue}, ${C.purple})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
      Claude Code Monitor
    </div>
    <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
      {[
        { l: "Projects", v: "12", c: C.t1 },
        { l: "Active", v: "3", c: C.green },
        { l: "Recent", v: "5", c: C.orange },
        { l: "Sessions", v: "45", c: C.blue },
        { l: "Msgs", v: "2.1K", c: C.t1 },
      ].map((ch, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11 }}>
          <span style={{ color: C.t3 }}>{ch.l}</span>
          <span style={{ color: ch.c, fontWeight: 600 }}>{ch.v}</span>
        </div>
      ))}
    </div>
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <span style={{ fontSize: 12, color: C.t3 }}>14:32:08</span>
      <Dot color={C.green} pulse />
      <span style={{ fontSize: 11, color: C.t2 }}>LIVE</span>
    </div>
  </div>
);

/* ── Flow Section (collapsed) ── */
const FlowSection: React.FC = () => (
  <div style={{ borderBottom: `1px solid ${C.border}`, background: C.bg1 }}>
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 20px", ...FONT }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: C.t2, textTransform: "uppercase", letterSpacing: 0.5, display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: 10 }}>&#9654;</span> Agent Topology & Flow
      </div>
      <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 8, background: "rgba(88,166,255,.1)", color: C.blue }}>1 team</span>
    </div>
  </div>
);

/* ── Filter Bar ── */
const FilterBar: React.FC = () => (
  <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 20px", borderBottom: `1px solid ${C.border}`, background: C.bg1, ...FONT }}>
    {["Active", "Recent", "All Projects"].map((f, i) => (
      <button key={i} style={{
        padding: "4px 14px", borderRadius: 14, border: `1px solid ${i === 0 ? C.blue : C.border}`,
        background: i === 0 ? "rgba(88,166,255,.15)" : "transparent",
        color: i === 0 ? C.blue : C.t2, fontSize: 11, cursor: "pointer", ...FONT,
      }}>
        {f}
      </button>
    ))}
    <span style={{ marginLeft: "auto", fontSize: 11, color: C.t3 }}>8 / 12 projects</span>
  </div>
);

/* ── Session row ── */
const Session: React.FC<{
  status: "active" | "recent" | "idle";
  model: string;
  branch?: string;
  summary: string;
  prompt: string;
  msgs: number;
  size: string;
  tool?: string;
  tokIn?: string;
  tokOut?: string;
  convo?: boolean;
}> = ({ status, model, summary, prompt, msgs, size, tool, tokIn, tokOut, branch, convo }) => {
  const dotColor = status === "active" ? C.green : status === "recent" ? C.orange : C.t3;
  return (
    <div style={{ padding: "8px 14px", borderBottom: `1px solid rgba(48,54,61,.3)`, background: status === "active" ? "rgba(63,185,80,.04)" : "transparent", ...FONT }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 3 }}>
        <Dot color={dotColor} pulse={status === "active"} />
        <span style={{ fontSize: 11, fontWeight: 600, color: C.t2, ...BLUR }}>#a8f3c2d1</span>
        <span style={{ fontSize: 10, color: C.purple }}>{model}</span>
        {branch && <span style={{ fontSize: 10, color: C.teal }}>{branch}</span>}
        <span style={{ marginLeft: "auto", fontSize: 10, color: C.t3 }}>{status === "active" ? "now" : "4m ago"}</span>
      </div>
      <div style={{ fontSize: 11, color: C.t2, margin: "2px 0 2px 15px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" as const, ...BLUR }}>{summary}</div>
      <div style={{ fontSize: 11, color: C.t1, margin: "2px 0 2px 15px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" as const, opacity: 0.8, ...BLUR }}>"{prompt}"</div>
      <div style={{ display: "flex", gap: 12, margin: "3px 0 0 15px", fontSize: 10, color: C.t3 }}>
        <span><span style={{ color: C.t2, fontWeight: 500 }}>{msgs}</span> msgs</span>
        <span><span style={{ color: C.t2, fontWeight: 500 }}>{size}</span> bytes</span>
      </div>
      {tool && <div style={{ margin: "3px 0 0 15px", fontSize: 10, color: C.orange, display: "flex", alignItems: "center", gap: 4 }}>&#9654; <span style={BLUR}>{tool}</span></div>}
      {tokIn && (
        <div style={{ display: "flex", gap: 10, margin: "2px 0 0 15px", fontSize: 9, color: C.t3 }}>
          <span>in:{tokIn}</span><span>out:{tokOut}</span>
        </div>
      )}
      {convo && (
        <div style={{ margin: "6px 10px 4px", border: `1px solid ${C.border}`, borderRadius: 8, background: C.bg0, overflow: "hidden" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "5px 10px", background: C.bg3, fontSize: 10, color: C.t2 }}>
            <span>&#9654; Conversation (6)</span>
          </div>
          <div style={{ padding: "6px 0" }}>
            {[
              { role: "U", color: C.blue, bg: "rgba(88,166,255,.2)", text: "Help me implement the login feature..." },
              { role: "A", color: C.purple, bg: "rgba(188,140,255,.2)", text: "I'll create the authentication module with..." },
              { role: "T", color: C.orange, bg: "rgba(210,153,34,.2)", text: "(tool result)" },
            ].map((t, i) => (
              <div key={i} style={{ display: "flex", gap: 6, padding: "3px 10px", fontSize: 10, lineHeight: 1.4 }}>
                <div style={{ flexShrink: 0, width: 14, height: 14, borderRadius: 3, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 8, fontWeight: 700, background: t.bg, color: t.color, marginTop: 1 }}>{t.role}</div>
                <div style={{ flex: 1, color: C.t2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" as const, ...BLUR }}>{t.text}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

/* ── Project Card ── */
const ProjectCard: React.FC<{
  status: "active" | "recent" | "idle";
  activeCnt?: number;
  recentCnt?: number;
  totalCnt: number;
  name: string;
  path: string;
  children: React.ReactNode;
}> = ({ status, activeCnt, recentCnt, totalCnt, name, path, children }) => {
  const borderColor = status === "active" ? C.green : status === "recent" ? C.orange : C.border;
  const shadow = status === "active" ? "0 0 20px rgba(63,185,80,.1)" : "none";
  const dotColor = status === "active" ? C.green : status === "recent" ? C.orange : C.t3;
  return (
    <div style={{ background: C.bg2, border: `1px solid ${borderColor}`, borderRadius: 10, overflow: "hidden", boxShadow: shadow, ...FONT }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", borderBottom: `1px solid ${C.border}`, background: C.bg3 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: C.t1, display: "flex", alignItems: "center", gap: 6 }}>
          <Dot color={dotColor} pulse={status === "active"} />
          <span style={BLUR}>{name}</span>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {activeCnt ? <Badge text={`${activeCnt} active`} bg="rgba(63,185,80,.15)" color={C.green} /> : null}
          {recentCnt ? <Badge text={`${recentCnt} recent`} bg="rgba(88,166,255,.1)" color={C.blue} /> : null}
          <Badge text={`${totalCnt} total`} bg="rgba(88,166,255,.1)" color={C.blue} />
        </div>
      </div>
      <div style={{ padding: "4px 14px 4px", fontSize: 10, color: C.t3, borderBottom: `1px solid rgba(48,54,61,.5)`, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" as const, ...BLUR }}>{path}</div>
      <div style={{ maxHeight: 500, overflow: "hidden" }}>{children}</div>
    </div>
  );
};

/* ── Stats Panel ── */
const StatsPanel: React.FC = () => (
  <div style={{ background: C.bg2, border: `1px solid ${C.border}`, borderRadius: 10, overflow: "hidden", ...FONT }}>
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", borderBottom: `1px solid ${C.border}`, background: C.bg3, fontSize: 12, fontWeight: 600, color: C.t2, textTransform: "uppercase", letterSpacing: 0.5 }}>
      Stats <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 8, background: "rgba(88,166,255,.1)", color: C.blue, fontWeight: 400, textTransform: "none", letterSpacing: 0 }}>2.1K msgs</span>
    </div>
    <div style={{ padding: "12px 14px", fontSize: 11 }}>
      {[
        { l: "Total Sessions", v: "156" },
        { l: "Total Messages", v: "2,148" },
        { l: "Since", v: "12/15/2025" },
        { l: "Longest", v: "4h 32m" },
        { l: "Today Msgs", v: "87", c: C.orange },
        { l: "Today Tools", v: "234", c: C.purple },
      ].map((r, i) => (
        <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "4px 0", borderBottom: `1px solid rgba(48,54,61,.3)` }}>
          <span style={{ color: C.t3 }}>{r.l}</span>
          <span style={{ color: r.c || C.t1, fontWeight: 500 }}>{r.v}</span>
        </div>
      ))}
      {/* Model bars */}
      {[
        { name: "Opus 4.6", pct: 100, cls: "linear-gradient(90deg,#6e40c9,#bc8cff)", val: "1.2M out" },
        { name: "Sonnet 4.5", pct: 65, cls: "linear-gradient(90deg,#1f6feb,#58a6ff)", val: "780K out" },
        { name: "Haiku 4.5", pct: 25, cls: "linear-gradient(90deg,#238636,#3fb950)", val: "310K out" },
      ].map((m, i) => (
        <div key={i} style={{ marginTop: 8 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, marginBottom: 3 }}>
            <span style={{ color: C.t2 }}>{m.name}</span>
            <span style={{ color: C.t3 }}>{m.val}</span>
          </div>
          <div style={{ height: 5, borderRadius: 3, background: C.bg0, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${m.pct}%`, borderRadius: 3, background: m.cls }} />
          </div>
        </div>
      ))}
      {/* Hourly chart */}
      <div style={{ marginTop: 12, fontSize: 10, color: C.t3, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 4 }}>Hourly</div>
      <div style={{ display: "flex", alignItems: "flex-end", gap: 1, height: 40 }}>
        {[2,1,0,0,0,1,5,12,18,22,15,20,25,18,14,16,20,24,19,12,8,6,4,3].map((v, i) => (
          <div key={i} style={{ flex: 1, background: C.blue, opacity: 0.5, borderRadius: "1px 1px 0 0", height: `${Math.max((v / 25) * 100, 4)}%`, minWidth: 2 }} />
        ))}
      </div>
    </div>
  </div>
);

/* ── Activity Panel ── */
const ActivityPanel: React.FC = () => (
  <div style={{ background: C.bg2, border: `1px solid ${C.border}`, borderRadius: 10, overflow: "hidden", ...FONT }}>
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", borderBottom: `1px solid ${C.border}`, background: C.bg3, fontSize: 12, fontWeight: 600, color: C.t2, textTransform: "uppercase", letterSpacing: 0.5 }}>
      Activity <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 8, background: "rgba(88,166,255,.1)", color: C.blue, fontWeight: 400, textTransform: "none", letterSpacing: 0 }}>15</span>
    </div>
    <div style={{ padding: "12px 14px" }}>
      {[
        { t: "14:32:05", txt: "Started new session with claude-opus-4-6", proj: "my-web-app" },
        { t: "14:28:41", txt: "Completed task: implement user authentication", proj: "api-server" },
        { t: "14:25:12", txt: "Created 3 files in components directory", proj: "frontend" },
        { t: "14:20:33", txt: "Ran 24 tests, all passing", proj: "core-lib" },
        { t: "14:15:07", txt: "Git commit: fix login redirect loop", proj: "my-web-app" },
      ].map((a, i) => (
        <div key={i} style={{ display: "flex", gap: 8, padding: "5px 0", borderBottom: `1px solid rgba(48,54,61,.3)`, fontSize: 10 }}>
          <span style={{ color: C.t3, minWidth: 55 }}>{a.t}</span>
          <div>
            <div style={{ color: C.t2, lineHeight: 1.3, ...BLUR }}>{a.txt}</div>
            <div style={{ color: C.blue, opacity: 0.7, fontSize: 9, ...BLUR }}>{a.proj}</div>
          </div>
        </div>
      ))}
    </div>
  </div>
);

/* ── Teams Panel ── */
const TeamsPanel: React.FC = () => (
  <div style={{ background: C.bg2, border: `1px solid ${C.border}`, borderRadius: 10, overflow: "hidden", ...FONT }}>
    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", borderBottom: `1px solid ${C.border}`, background: C.bg3, fontSize: 12, fontWeight: 600, color: C.t2, textTransform: "uppercase", letterSpacing: 0.5 }}>
      Teams & Tasks <span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 8, background: "rgba(88,166,255,.1)", color: C.blue, fontWeight: 400, textTransform: "none", letterSpacing: 0 }}>1 team</span>
    </div>
    <div style={{ padding: "12px 14px", fontSize: 11 }}>
      <div style={{ marginBottom: 10 }}>
        <div style={{ color: C.t3, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 6, fontSize: 11 }}>Tasks</div>
        <div style={{ display: "flex", gap: 12 }}>
          <span style={{ color: C.green }}>5 done</span>
          <span style={{ color: C.orange }}>2 in progress</span>
          <span style={{ color: C.t2 }}>1 pending</span>
        </div>
      </div>
      <div>
        <div style={{ color: C.blue, marginBottom: 4, fontSize: 11, ...BLUR }}>feature-team</div>
        {[
          { name: "team-lead", type: "team-lead", active: true },
          { name: "researcher", type: "general-purpose", active: true },
          { name: "implementer", type: "general-purpose", active: false },
        ].map((m, i) => (
          <div key={i} style={{ display: "flex", alignItems: "center", gap: 6, padding: "3px 0" }}>
            <Dot color={m.active ? C.green : C.t3} />
            <span style={{ color: C.t1, fontWeight: 500 }}>{m.name}</span>
            <span style={{ color: C.t3, fontSize: 10 }}>{m.type}</span>
          </div>
        ))}
      </div>
    </div>
  </div>
);

/* ── Full Dashboard ── */
export const MockDashboard: React.FC = () => {
  return (
    <div style={{ width: 1920, height: 1080, background: C.bg0, overflow: "hidden", ...FONT }}>
      <Header />
      <FlowSection />
      <FilterBar />
      {/* Main project grid */}
      <div style={{ padding: "16px 20px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14, alignItems: "start" }}>
          <ProjectCard status="active" activeCnt={2} totalCnt={8} name="my-fullstack-project" path="C:\Users\dev\projects\my-fullstack-project">
            <Session status="active" model="Opus 4.6" branch="main" summary="Implementing real-time WebSocket monitoring dashboard" prompt="Add the WebSocket endpoint that streams session data every 3 seconds" msgs={45} size="128K" tool="Edit src/components/Dashboard.tsx" tokIn="856K" tokOut="124K" convo />
            <Session status="active" model="Sonnet 4.5" branch="feature/auth" summary="Adding OAuth2 authentication flow" prompt="Create the login page with Google OAuth integration" msgs={23} size="64K" tool="Write auth/providers.ts" tokIn="432K" tokOut="67K" />
          </ProjectCard>
          <ProjectCard status="recent" recentCnt={1} totalCnt={5} name="api-backend-service" path="C:\Users\dev\projects\api-backend-service">
            <Session status="recent" model="Opus 4.6" summary="Refactoring database query layer for performance" prompt="Optimize the user search query to use indexes" msgs={34} size="96K" tool="Read prisma/schema.prisma" tokIn="654K" tokOut="98K" />
            <div style={{ padding: "8px 14px", fontSize: 11, color: C.t3, display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 8 }}>&#9654;</span> 4 idle sessions
            </div>
          </ProjectCard>
          <ProjectCard status="idle" totalCnt={3} name="design-system-lib" path="C:\Users\dev\packages\design-system-lib">
            <div style={{ padding: "8px 14px", fontSize: 11, color: C.t3, display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 8 }}>&#9654;</span> 3 idle sessions
            </div>
          </ProjectCard>
          <ProjectCard status="idle" totalCnt={6} name="data-pipeline-tools" path="D:\work\data-pipeline-tools">
            <div style={{ padding: "8px 14px", fontSize: 11, color: C.t3, display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 8 }}>&#9654;</span> 6 idle sessions
            </div>
          </ProjectCard>
        </div>
      </div>
      {/* Bottom panels */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14, padding: "0 20px 20px" }}>
        <StatsPanel />
        <ActivityPanel />
        <TeamsPanel />
      </div>
    </div>
  );
};
