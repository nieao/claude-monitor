import React from "react";

/*
 * MockMobile — visual replica of the mobile UI (Overview tab).
 * Sensitive data (project names, paths, prompts) is blurred.
 */

const C = {
  bg0: "#0a0e14", bg1: "#0d1117", bg2: "#161b22", bg3: "#1c2333",
  border: "#30363d", t1: "#e6edf3", t2: "#8b949e", t3: "#484f58",
  blue: "#58a6ff", green: "#3fb950", orange: "#d29922", purple: "#bc8cff", teal: "#39d2c0",
};

const BLUR: React.CSSProperties = { filter: "blur(4px)", userSelect: "none" };
const FONT: React.CSSProperties = { fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', sans-serif" };

const Dot: React.FC<{ color: string }> = ({ color }) => (
  <div style={{ width: 8, height: 8, borderRadius: "50%", background: color, flexShrink: 0 }} />
);

export const MockMobile: React.FC = () => {
  return (
    <div style={{ width: 390, height: 844, background: C.bg0, overflow: "hidden", display: "flex", flexDirection: "column", ...FONT }}>
      {/* Header */}
      <div style={{ height: 48, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 16px", background: C.bg2, borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
        <div style={{ fontSize: 16, fontWeight: 700, background: `linear-gradient(135deg, ${C.blue}, ${C.purple})`, WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
          Claude Monitor
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 12, color: C.t3 }}>14:32</span>
          <div style={{ width: 8, height: 8, borderRadius: "50%", background: C.green, boxShadow: `0 0 4px ${C.green}` }} />
          <span style={{ fontSize: 11, color: C.t2 }}>LIVE</span>
        </div>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: "hidden", padding: 12 }}>
        {/* Stats Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 12 }}>
          {[
            { num: "12", lbl: "Projects", c: C.blue },
            { num: "3", lbl: "Active", c: C.green },
            { num: "5", lbl: "Recent", c: C.orange },
            { num: "2.1K", lbl: "Messages", c: C.purple },
          ].map((s, i) => (
            <div key={i} style={{ background: C.bg3, border: `1px solid ${C.border}`, borderRadius: 10, padding: 12, textAlign: "center" }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: s.c, lineHeight: 1.2 }}>{s.num}</div>
              <div style={{ fontSize: 11, color: C.t3, marginTop: 2 }}>{s.lbl}</div>
            </div>
          ))}
        </div>

        {/* Live Sessions */}
        <div style={{ fontSize: 12, fontWeight: 600, color: C.t3, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 8 }}>Live Sessions</div>
        <div style={{ background: C.bg2, border: `1px solid ${C.border}`, borderRadius: 12, overflow: "hidden", marginBottom: 12 }}>
          {[
            { name: "my-fullstack-project", detail: "Implementing WebSocket monitoring...", model: "Opus 4.6", active: true },
            { name: "api-backend-service", detail: "Refactoring database queries...", model: "Opus 4.6", active: false },
            { name: "frontend-dashboard", detail: "Adding responsive mobile layout...", model: "Sonnet 4.5", active: true },
          ].map((s, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, padding: "12px 14px", borderBottom: i < 2 ? `1px solid rgba(48,54,61,.3)` : "none" }}>
              <Dot color={s.active ? C.green : C.orange} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: C.t1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" as const, ...BLUR }}>{s.name}</div>
                <div style={{ fontSize: 11, color: C.t2, marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" as const, ...BLUR }}>{s.detail}</div>
              </div>
              <div style={{ fontSize: 11, color: C.purple, whiteSpace: "nowrap" as const }}>{s.model}</div>
            </div>
          ))}
        </div>

        {/* Recent Activity */}
        <div style={{ fontSize: 12, fontWeight: 600, color: C.t3, textTransform: "uppercase", letterSpacing: 0.5, marginBottom: 8 }}>Recent Activity</div>
        <div style={{ background: C.bg2, border: `1px solid ${C.border}`, borderRadius: 12, overflow: "hidden" }}>
          <div style={{ padding: "12px 14px" }}>
            {[
              { t: "14:32", txt: "Started new session with opus-4-6", proj: "my-project" },
              { t: "14:28", txt: "Completed task: implement auth", proj: "api-server" },
              { t: "14:25", txt: "Created 3 files in components/", proj: "frontend" },
            ].map((a, i) => (
              <div key={i} style={{ display: "flex", gap: 10, padding: "10px 0", borderBottom: i < 2 ? `1px solid rgba(48,54,61,.2)` : "none", fontSize: 12 }}>
                <span style={{ fontSize: 11, color: C.t3, minWidth: 40 }}>{a.t}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ color: C.t2, lineHeight: 1.3, ...BLUR }}>{a.txt}</div>
                  <div style={{ fontSize: 10, color: C.blue, marginTop: 2, opacity: 0.7, ...BLUR }}>{a.proj}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Tab Bar */}
      <div style={{ height: 56, display: "flex", background: C.bg2, borderTop: `1px solid ${C.border}`, flexShrink: 0 }}>
        {[
          { icon: "\u25C9", label: "Overview", active: true },
          { icon: "\u2636", label: "Projects", active: false, badge: 3 },
          { icon: "\u25A4", label: "Stats", active: false },
          { icon: "\u25C9", label: "Teams", active: false, badge: 1 },
        ].map((tab, i) => (
          <div key={i} style={{
            flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 2,
            color: tab.active ? C.blue : C.t3, position: "relative",
          }}>
            {tab.active && <div style={{ position: "absolute", top: 0, left: "20%", right: "20%", height: 2, background: C.blue, borderRadius: "0 0 2px 2px" }} />}
            <span style={{ fontSize: 20 }}>{tab.icon}</span>
            <span style={{ fontSize: 10 }}>{tab.label}</span>
            {tab.badge && (
              <div style={{
                position: "absolute", top: 4, right: "calc(50% - 18px)",
                minWidth: 16, height: 16, borderRadius: 8, background: C.green,
                color: "#fff", fontSize: 9, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center",
              }}>
                {tab.badge}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
