# PRD Part 4: Frontend Dashboard Design

## 12. Command Center Dashboard

### 12.1 Full Layout Specification

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  🏛️ NEXUS-GOV COMMAND CENTER       HYDERABAD    THREAT ████░ LEVEL 4/5     │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
├───────────────────────────────┬──────────────────────────────────────────────┤
│                               │  AGENT STATUS                               │
│                               │  ┌─────────────────────────────────────┐    │
│      🗺️ LIVE CITY MAP         │  │ 🚦 Traffic .... ● ACTIVE  [7 acts] │    │
│      (Leaflet.js)             │  │ ⚡ Power ....... ● ACTIVE  [3 acts] │    │
│                               │  │ 🚑 Emergency .. ● ALERT   [2 disp] │    │
│   Features:                   │  │ 🌊 Flood ....... ● CRITICAL [1 evt] │    │
│   • 12 color-coded zones      │  │ 🧠 Meta ........ ● COORDINATING     │    │
│     (green/amber/red)         │  └─────────────────────────────────────┘    │
│   • Ambulance icons with      │                                             │
│     real-time movement        │  AGENT REASONING LOG (Live Feed)            │
│   • Substation markers        │  ┌─────────────────────────────────────┐    │
│     (green dot = OK,          │  │ [22:14:03] 🌊 Flood Agent:         │    │
│      red dot = down)          │  │ "Rainfall at Hussain Sagar basin   │    │
│   • Flood zone overlays       │  │  reached 95mm/hr — exceeding the   │    │
│     (blue gradient opacity)   │  │  65mm/hr threshold. Setting        │    │
│   • Emergency corridors       │  │  flood_risk = HIGH for zones C1    │    │
│     (pulsing green/white)     │  │  and C2. Broadcasting CRITICAL     │    │
│   • Hospital markers          │  │  alert to all agents."             │    │
│     with bed count badges     │  │                                     │    │
│   • Click zone for details    │  │ [22:14:05] 🚑 Emergency Agent:     │    │
│                               │  │ "Received FLOOD_ALERT. Zones C1    │    │
│                               │  │  and C2 at risk. Pre-positioning   │    │
│                               │  │  AMB-3 to zone_a3 and AMB-7 to    │    │
│                               │  │  zone_d3 (outside flood zone but   │    │
│                               │  │  within 5-min response radius).    │    │
│                               │  │  Alerting NIMS and Care Hospital." │    │
│                               │  │                                     │    │
│                               │  │ [22:14:07] 🚦 Traffic Agent:       │    │
│                               │  │ "Cross-domain alert: flood_risk    │    │
│                               │  │  HIGH in C1/C2. Clearing emergency │    │
│                               │  │  corridor on route R-C1-A1 for    │    │
│                               │  │  ambulance AMB-7. Setting all      │    │
│                               │  │  signals to green on corridor.     │    │
│                               │  │  ETA to clear: 3 minutes."         │    │
│                               │  │                                     │    │
│                               │  │ [22:14:09] ⚡ Power Agent:          │    │
│                               │  │ "Substation sub_3 (LB Nagar) is   │    │
│                               │  │  in flood zone C3. Proactively     │    │
│                               │  │  rerouting 120MW to sub_2 and      │    │
│                               │  │  sub_4. Activating backup for     │    │
│                               │  │  hospital zones."                  │    │
│                               │  └─────────────────────────────────────┘    │
├───────────────────────────────┴──────────────────────────────────────────────┤
│  ⏱️ CRISIS TIMELINE (horizontal scrolling)                                    │
│  ●━━━━━━━●━━━━━━━●━━━━━━━●━━━━━━━●━━━━━━━○━━━━━━━○                          │
│  Detect   Classify Coord   Deploy  Alert   Evac    Resolve                   │
│  22:14:03 22:14:04 22:14:05 22:14:06 22:14:07                               │
│  🌊 Flood 🧠 Sev 8 🎯 Plan 🚑 AMB-7 📢 Alert                              │
├──────────────────────────────────┬───────────────────────────────────────────┤
│  🛡️ DECISION AUDIT TRAIL         │  🔴 HUMAN OVERRIDE CONTROLS              │
│  ┌────────────────────────────┐  │  ┌─────────────────────────────────────┐ │
│  │ #0041 ⚡ Power reroute     │  │  │                                     │ │
│  │ Hash: a3f8..b2c1           │  │  │  [✋ Override Agent Decision]       │ │
│  │ Chain: ✅ VERIFIED          │  │  │                                     │ │
│  │                            │  │  │  [⛔ PAUSE ALL AGENTS]              │ │
│  │ #0042 🚑 AMB-3 reposition │  │  │                                     │ │
│  │ Hash: b7c2..d9e3           │  │  │  [🔄 Reassign Resources]           │ │
│  │ Chain: ✅ VERIFIED          │  │  │                                     │ │
│  │                            │  │  │  [📋 View Full Decision Log]        │ │
│  │ #0043 🚦 Corridor cleared  │  │  │                                     │ │
│  │ Hash: d9e3..f1a4           │  │  │  [🎬 INJECT SCENARIO ▼]            │ │
│  │ Chain: ✅ VERIFIED          │  │  │    • Monsoon Flood                  │ │
│  └────────────────────────────┘  │  │    • Industrial Fire                │ │
│  [Verify Full Chain Integrity]   │  │    • Dual Crisis                    │ │
│                                  │  └─────────────────────────────────────┘ │
└──────────────────────────────────┴───────────────────────────────────────────┘
```

### 12.2 Visual Design System

#### Color Palette

```css
:root {
  /* Backgrounds */
  --bg-primary: #0a0e1a;           /* Deep navy-black */
  --bg-secondary: #0f172a;         /* Slightly lighter panel */
  --bg-panel: rgba(15, 23, 42, 0.8); /* Glassmorphism panel */
  
  /* Status Colors */
  --color-safe: #22c55e;           /* Green — all clear */
  --color-warning: #fbbf24;        /* Amber — attention */
  --color-critical: #ef4444;        /* Red — critical/danger */
  --color-info: #3b82f6;           /* Blue — informational */
  --color-flood: #06b6d4;          /* Cyan — flood zones */
  
  /* Accent */
  --accent-primary: #00f0ff;       /* Neon cyan — primary accent */
  --accent-secondary: #8b5cf6;     /* Purple — secondary accent */
  --accent-glow: rgba(0, 240, 255, 0.15); /* Subtle glow */
  
  /* Text */
  --text-primary: #f1f5f9;         /* Bright white */
  --text-secondary: #94a3b8;       /* Muted gray */
  --text-dim: #475569;             /* Dim labels */
  
  /* Agent Colors */
  --agent-traffic: #fbbf24;        /* Amber */
  --agent-power: #f97316;          /* Orange */
  --agent-emergency: #ef4444;      /* Red */
  --agent-flood: #06b6d4;          /* Cyan */
  --agent-meta: #8b5cf6;           /* Purple */
  
  /* Borders */
  --border-subtle: rgba(0, 240, 255, 0.15);
  --border-active: rgba(0, 240, 255, 0.4);
  
  /* Glassmorphism */
  --glass-bg: rgba(15, 23, 42, 0.7);
  --glass-blur: blur(12px);
  --glass-border: 1px solid rgba(255, 255, 255, 0.08);
}
```

#### Typography

```css
/* Headers — Orbitron (techy, command-center feel) */
h1, h2, .threat-level, .panel-title {
  font-family: 'Orbitron', monospace;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

/* Body text — Inter (clean, readable) */
body, p, .agent-status, .button {
  font-family: 'Inter', -apple-system, sans-serif;
  font-weight: 400;
}

/* Data/Logs — JetBrains Mono */
.reasoning-log, .audit-hash, .timestamp, .cdil-value, code {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.85rem;
}
```

#### Animations

```css
/* Agent active indicator — pulsing dot */
@keyframes agent-pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
  50% { box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }
}

.agent-dot.active {
  animation: agent-pulse 2s infinite;
}

.agent-dot.critical {
  animation: agent-pulse 0.8s infinite;
  background: var(--color-critical);
}

/* Emergency corridor pulsing line on map */
@keyframes corridor-pulse {
  0%, 100% { opacity: 1; stroke-width: 4; }
  50% { opacity: 0.5; stroke-width: 6; }
}

/* Reasoning log typewriter effect */
@keyframes typewriter {
  from { width: 0; }
  to { width: 100%; }
}

.reasoning-entry.new {
  overflow: hidden;
  white-space: nowrap;
  animation: typewriter 1.5s steps(60, end);
}

/* Threat level bar pulsing */
@keyframes threat-glow {
  0%, 100% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.3); }
  50% { box-shadow: 0 0 25px rgba(239, 68, 68, 0.6); }
}

.threat-bar.critical {
  animation: threat-glow 1.5s infinite;
}

/* Panel entry animation */
@keyframes slide-in {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.panel {
  animation: slide-in 0.3s ease-out;
}
```

### 12.3 Component Architecture

```
src/
├── components/
│   ├── Layout/
│   │   ├── CommandCenter.jsx      # Main layout container
│   │   ├── Header.jsx             # Top bar with title + threat level
│   │   └── PanelContainer.jsx     # Glassmorphism panel wrapper
│   │
│   ├── Map/
│   │   ├── CityMap.jsx            # Main Leaflet map component
│   │   ├── ZoneOverlay.jsx        # GeoJSON zone polygons (color-coded by risk)
│   │   ├── FloodOverlay.jsx       # Blue gradient overlay for flood zones
│   │   ├── AmbulanceMarker.jsx    # Custom ambulance icon with status color
│   │   ├── SubstationMarker.jsx   # Power substation marker (green/red dot)
│   │   ├── HospitalMarker.jsx     # Hospital with bed count badge
│   │   ├── CorridorLine.jsx       # Pulsing emergency corridor polyline
│   │   └── ZonePopup.jsx          # Click-to-view zone details popup
│   │
│   ├── Agents/
│   │   ├── AgentStatusPanel.jsx   # All 5 agents overview
│   │   ├── AgentCard.jsx          # Single agent: name, status, action count
│   │   ├── AgentDot.jsx           # Animated status indicator dot
│   │   └── ReasoningLog.jsx       # Live chain-of-thought feed with typewriter
│   │
│   ├── Timeline/
│   │   ├── EventTimeline.jsx      # Horizontal crisis progression timeline
│   │   └── TimelineNode.jsx       # Individual event node with label
│   │
│   ├── Audit/
│   │   ├── AuditTrail.jsx         # Hash-chained decision log panel
│   │   ├── AuditEntry.jsx         # Single entry: agent, action, hash, verified
│   │   └── ChainVerifier.jsx      # "Verify Chain Integrity" button + result
│   │
│   ├── Override/
│   │   ├── OverridePanel.jsx      # Human override controls
│   │   ├── OverrideModal.jsx      # Confirmation dialog for overrides
│   │   └── ScenarioInjector.jsx   # Dropdown to trigger demo scenarios
│   │
│   └── Shared/
│       ├── ThreatIndicator.jsx    # Global threat level bar (top right)
│       ├── StatusBadge.jsx        # Reusable status badge component
│       ├── GlassPanel.jsx         # Reusable glassmorphism container
│       └── LiveClock.jsx          # Real-time clock display
│
├── hooks/
│   ├── useSocket.js               # Socket.IO connection + event handlers
│   ├── useCDIL.js                 # CDIL state subscription + updates
│   ├── useAgents.js               # Agent status tracking
│   └── useAudit.js                # Audit trail data
│
├── utils/
│   ├── constants.js               # Zone coords, colors, agent configs
│   ├── mapConfig.js               # Leaflet config, tile layer URLs
│   └── formatters.js              # Timestamp, hash, number formatting
│
├── data/
│   └── hyderabad-zones.geojson    # Zone boundary polygons for Leaflet
│
├── App.jsx                        # Main app shell
├── App.css                        # Global styles + CSS variables
└── main.jsx                       # Vite entry point
```

### 12.4 Hyderabad Zone Coordinates (for Map)

```javascript
// data/zones.js — Approximate zone center coordinates
export const ZONE_COORDS = {
  "zone_a1": { center: [17.4375, 78.4983], name: "Begumpet" },
  "zone_a2": { center: [17.4399, 78.4983], name: "Secunderabad" },
  "zone_a3": { center: [17.4375, 78.4483], name: "Ameerpet" },
  "zone_b1": { center: [17.4948, 78.3996], name: "Kukatpally" },
  "zone_b2": { center: [17.4435, 78.3772], name: "HITEC City" },
  "zone_b3": { center: [17.4401, 78.3489], name: "Gachibowli" },
  "zone_c1": { center: [17.4156, 78.4701], name: "Khairatabad" },
  "zone_c2": { center: [17.4239, 78.4738], name: "Hussain Sagar" },
  "zone_c3": { center: [17.3457, 78.5522], name: "LB Nagar" },
  "zone_d1": { center: [17.4710, 78.5275], name: "Malkajgiri" },
  "zone_d2": { center: [17.4065, 78.5587], name: "Uppal" },
  "zone_d3": { center: [17.3688, 78.5247], name: "Dilsukhnagar" },
};

export const MAP_CONFIG = {
  center: [17.385, 78.486],  // Hyderabad center
  zoom: 12,
  tileLayer: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
  attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>'
};

// Zone colors based on risk level
export const RISK_COLORS = {
  LOW: "rgba(34, 197, 94, 0.2)",       // Green translucent
  MODERATE: "rgba(251, 191, 36, 0.3)",  // Amber translucent
  HIGH: "rgba(239, 68, 68, 0.4)",       // Red translucent
  CRITICAL: "rgba(220, 38, 38, 0.6)",   // Deep red
};
```

### 12.5 Key Component Implementations

#### GlassPanel (Reusable Container)

```jsx
// components/Shared/GlassPanel.jsx
export function GlassPanel({ title, icon, children, className = "" }) {
  return (
    <div className={`glass-panel ${className}`}>
      {title && (
        <div className="glass-panel-header">
          {icon && <span className="panel-icon">{icon}</span>}
          <h3 className="panel-title">{title}</h3>
        </div>
      )}
      <div className="glass-panel-content">
        {children}
      </div>
    </div>
  );
}
```

```css
.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: var(--glass-border);
  border-radius: 12px;
  padding: 16px;
  transition: border-color 0.3s ease;
}

.glass-panel:hover {
  border-color: var(--border-active);
}

.glass-panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border-subtle);
}

.panel-title {
  font-family: 'Orbitron', monospace;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--accent-primary);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
```

#### useSocket Hook

```javascript
// hooks/useSocket.js
import { useEffect, useState, useCallback, useRef } from 'react';
import { io } from 'socket.io-client';

export function useSocket(url = 'http://localhost:8000') {
  const [connected, setConnected] = useState(false);
  const [agentStatuses, setAgentStatuses] = useState({});
  const [reasoningLog, setReasoningLog] = useState([]);
  const [cdilState, setCdilState] = useState({});
  const [mapUpdates, setMapUpdates] = useState([]);
  const [auditEntries, setAuditEntries] = useState([]);
  const [timelineEvents, setTimelineEvents] = useState([]);
  const [threatLevel, setThreatLevel] = useState({ level: 1, max: 5 });
  const socketRef = useRef(null);

  useEffect(() => {
    const socket = io(url, { transports: ['websocket'] });
    socketRef.current = socket;

    socket.on('connect', () => setConnected(true));
    socket.on('disconnect', () => setConnected(false));

    socket.on('agent_status', (data) => {
      setAgentStatuses(prev => ({ ...prev, [data.agent]: data }));
    });

    socket.on('agent_reasoning', (data) => {
      setReasoningLog(prev => [...prev.slice(-50), data]); // Keep last 50
    });

    socket.on('cdil_update', (data) => {
      setCdilState(prev => ({ ...prev, [data.key]: data }));
    });

    socket.on('map_update', (data) => {
      setMapUpdates(prev => [...prev.slice(-100), data]);
    });

    socket.on('audit_entry', (data) => {
      setAuditEntries(prev => [...prev.slice(-30), data]);
    });

    socket.on('timeline_event', (data) => {
      setTimelineEvents(prev => [...prev, data]);
    });

    socket.on('threat_level', (data) => {
      setThreatLevel(data);
    });

    return () => socket.disconnect();
  }, [url]);

  const injectScenario = useCallback((scenarioId) => {
    socketRef.current?.emit('inject_scenario', { scenario: scenarioId });
  }, []);

  const overrideAgent = useCallback((agentId, action, reason) => {
    socketRef.current?.emit('override', { agent: agentId, action, reason });
  }, []);

  const pauseAll = useCallback(() => {
    socketRef.current?.emit('pause_all');
  }, []);

  return {
    connected,
    agentStatuses,
    reasoningLog,
    cdilState,
    mapUpdates,
    auditEntries,
    timelineEvents,
    threatLevel,
    injectScenario,
    overrideAgent,
    pauseAll,
  };
}
```

---

*Continued in [PRD-PART5-EXECUTION.md](./PRD-PART5-EXECUTION.md)*
