import React from "react";
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  interpolate,
  spring,
  useVideoConfig,
} from "remotion";
import { MockDashboard } from "./MockDashboard";
import { MockMobile } from "./MockMobile";

/* ── Color Tokens ── */
const C = {
  bg: "#0a0e14",
  bg1: "#0d1117",
  bg2: "#161b22",
  t1: "#e6edf3",
  t2: "#8b949e",
  t3: "#484f58",
  blue: "#58a6ff",
  green: "#3fb950",
  orange: "#d29922",
  purple: "#bc8cff",
  red: "#f85149",
};

/* ── Scene 1: Hook (0-60 frames / 0-2s) ── */
const HookScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(frame, [0, 20, 45, 60], [0, 1, 1, 0], {
    extrapolateRight: "clamp",
  });
  const scale = spring({ frame, fps, from: 0.8, to: 1, config: { stiffness: 80, damping: 12 } });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: C.bg,
        justifyContent: "center",
        alignItems: "center",
        opacity,
      }}
    >
      <div
        style={{
          transform: `scale(${scale})`,
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: 52, fontWeight: 700, color: C.t1, fontFamily: "Inter, sans-serif" }}>
          When you run multiple
        </div>
        <div
          style={{
            fontSize: 52,
            fontWeight: 700,
            fontFamily: "Inter, sans-serif",
            background: `linear-gradient(135deg, ${C.blue}, ${C.purple})`,
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            marginTop: 8,
          }}
        >
          Claude Code sessions...
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ── Scene 2: Pain Points (60-210 frames / 2-7s) ── */
const PainPointsScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const points = [
    { icon: "?", text: "No visibility into active sessions", delay: 0 },
    { icon: "!", text: "Can't track token consumption", delay: 20 },
    { icon: "~", text: "Team agent status is invisible", delay: 40 },
  ];

  const fadeOut = interpolate(frame, [120, 150], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg, justifyContent: "center", alignItems: "center", opacity: fadeOut }}>
      <div style={{ display: "flex", flexDirection: "column", gap: 32, maxWidth: 800 }}>
        {points.map((p, i) => {
          const s = spring({ frame, fps, from: 0, to: 1, delay: p.delay, config: { stiffness: 100, damping: 14 } });
          const x = interpolate(s, [0, 1], [60, 0]);
          return (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 24,
                opacity: s,
                transform: `translateX(${x}px)`,
              }}
            >
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: 12,
                  background: `rgba(248, 81, 73, 0.15)`,
                  border: `2px solid ${C.red}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: 28,
                  fontWeight: 700,
                  color: C.red,
                  flexShrink: 0,
                  fontFamily: "monospace",
                }}
              >
                {p.icon}
              </div>
              <div style={{ fontSize: 32, color: C.t1, fontWeight: 500, fontFamily: "Inter, sans-serif" }}>
                {p.text}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/* ── Scene 3: Solution Reveal (210-270 frames / 7-9s) ── */
const SolutionScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const s = spring({ frame, fps, from: 0, to: 1, config: { stiffness: 80, damping: 12 } });
  const lineW = interpolate(s, [0, 1], [0, 100]);

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg, justifyContent: "center", alignItems: "center" }}>
      <div style={{ textAlign: "center", opacity: s, transform: `scale(${interpolate(s, [0, 1], [0.7, 1])})` }}>
        <div
          style={{
            fontSize: 72,
            fontWeight: 800,
            fontFamily: "Inter, sans-serif",
            background: `linear-gradient(135deg, ${C.blue}, ${C.purple})`,
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          Claude Code Monitor
        </div>
        <div
          style={{
            width: `${lineW}%`,
            height: 3,
            background: `linear-gradient(90deg, ${C.blue}, ${C.purple})`,
            margin: "16px auto 20px",
            borderRadius: 2,
          }}
        />
        <div style={{ fontSize: 28, color: C.t2, fontFamily: "Inter, sans-serif" }}>
          Real-time monitoring dashboard
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ── Scene 4: Dashboard Showcase (270-420 frames / 9-14s) ── */
const DashboardScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const s = spring({ frame, fps, from: 0, to: 1, config: { stiffness: 60, damping: 14 } });
  const scale = interpolate(s, [0, 1], [0.9, 0.72]);
  const y = interpolate(s, [0, 1], [80, 20]);

  /* Feature labels that appear */
  const features = [
    { text: "Live Sessions", x: 160, y: 230, delay: 20, color: C.green },
    { text: "Token Analytics", x: 1400, y: 750, delay: 40, color: C.purple },
    { text: "Conversation Preview", x: 200, y: 600, delay: 60, color: C.orange },
    { text: "Agent Topology", x: 800, y: 160, delay: 80, color: C.blue },
  ];

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <div
        style={{
          transform: `scale(${scale}) translateY(${y}px)`,
          transformOrigin: "top center",
          opacity: s,
          borderRadius: 16,
          overflow: "hidden",
          boxShadow: "0 20px 80px rgba(0,0,0,0.6)",
          border: `1px solid ${C.t3}`,
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
        }}
      >
        <MockDashboard />
      </div>
      {/* Feature callout labels */}
      {features.map((f, i) => {
        const fs = spring({ frame, fps, from: 0, to: 1, delay: f.delay, config: { stiffness: 120, damping: 12 } });
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: f.x,
              top: f.y,
              opacity: fs,
              transform: `scale(${fs}) translateY(${interpolate(fs, [0, 1], [10, 0])}px)`,
            }}
          >
            <div
              style={{
                background: C.bg2,
                border: `2px solid ${f.color}`,
                borderRadius: 10,
                padding: "8px 18px",
                fontSize: 18,
                fontWeight: 600,
                color: f.color,
                fontFamily: "Inter, sans-serif",
                boxShadow: `0 4px 20px ${f.color}33`,
                whiteSpace: "nowrap",
              }}
            >
              {f.text}
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

/* ── Scene 5: Mobile (420-480 frames / 14-16s) ── */
const MobileScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const s = spring({ frame, fps, from: 0, to: 1, config: { stiffness: 80, damping: 12 } });
  const phoneY = interpolate(s, [0, 1], [120, 0]);

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg, justifyContent: "center", alignItems: "center" }}>
      {/* Text */}
      <div
        style={{
          position: "absolute",
          left: 180,
          top: "50%",
          transform: "translateY(-50%)",
          opacity: s,
        }}
      >
        <div style={{ fontSize: 44, fontWeight: 700, color: C.t1, fontFamily: "Inter, sans-serif", marginBottom: 12 }}>
          Mobile Ready
        </div>
        <div style={{ fontSize: 22, color: C.t2, fontFamily: "Inter, sans-serif", lineHeight: 1.6 }}>
          Auto-detect mobile devices
          <br />
          Bottom tab navigation
          <br />
          Touch-friendly interface
        </div>
      </div>
      {/* Phone frame */}
      <div
        style={{
          position: "absolute",
          right: 240,
          transform: `translateY(${phoneY}px)`,
          opacity: s,
        }}
      >
        <div
          style={{
            width: 320,
            height: 650,
            borderRadius: 36,
            border: `3px solid ${C.t3}`,
            overflow: "hidden",
            boxShadow: `0 20px 60px rgba(0,0,0,0.5), 0 0 40px ${C.blue}15`,
            background: C.bg,
          }}
        >
          <div style={{ transform: "scale(0.82)", transformOrigin: "top left", width: 390, height: 793 }}>
            <MockMobile />
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ── Scene 6: CTA (480-540 frames / 16-18s) ── */
const CTAScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const s = spring({ frame, fps, from: 0, to: 1, config: { stiffness: 80, damping: 12 } });
  const badgeS = spring({ frame, fps, from: 0, to: 1, delay: 15, config: { stiffness: 120, damping: 10 } });

  return (
    <AbsoluteFill style={{ backgroundColor: C.bg, justifyContent: "center", alignItems: "center" }}>
      <div style={{ textAlign: "center", opacity: s, transform: `scale(${interpolate(s, [0, 1], [0.8, 1])})` }}>
        <div
          style={{
            fontSize: 64,
            fontWeight: 800,
            fontFamily: "Inter, sans-serif",
            background: `linear-gradient(135deg, ${C.blue}, ${C.purple})`,
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            marginBottom: 24,
          }}
        >
          Claude Code Monitor
        </div>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 12,
            background: C.bg2,
            border: `1px solid ${C.t3}`,
            borderRadius: 12,
            padding: "14px 32px",
            opacity: badgeS,
            transform: `translateY(${interpolate(badgeS, [0, 1], [20, 0])}px)`,
          }}
        >
          <span style={{ fontSize: 24, color: C.t1, fontFamily: "monospace" }}>github.com/nieao/claude-monitor</span>
        </div>
        <div style={{ marginTop: 28, fontSize: 22, color: C.t2, fontFamily: "Inter, sans-serif" }}>
          Open Source &middot; Free &middot; Real-time
        </div>
      </div>
    </AbsoluteFill>
  );
};

/* ── Main Composition ── */
export const PromoVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: C.bg }}>
      <Sequence from={0} durationInFrames={60}>
        <HookScene />
      </Sequence>
      <Sequence from={60} durationInFrames={150}>
        <PainPointsScene />
      </Sequence>
      <Sequence from={210} durationInFrames={60}>
        <SolutionScene />
      </Sequence>
      <Sequence from={270} durationInFrames={150}>
        <DashboardScene />
      </Sequence>
      <Sequence from={420} durationInFrames={60}>
        <MobileScene />
      </Sequence>
      <Sequence from={480} durationInFrames={60}>
        <CTAScene />
      </Sequence>
    </AbsoluteFill>
  );
};
