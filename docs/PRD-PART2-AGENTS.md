# PRD Part 2: Agent Specifications & CDIL

## 5. Agent Architecture

### 5.1 Shared Agent Pattern

Every domain agent follows the same internal architecture:

```
┌─────────────────────────────────────────────┐
│              DOMAIN AGENT                    │
├─────────────────────────────────────────────┤
│                                             │
│  ┌─────────────┐    ┌────────────────────┐  │
│  │ PERCEPTION   │    │ MEMORY             │  │
│  │              │    │                    │  │
│  │ • Subscribe  │    │ • Episodic: last   │  │
│  │   to CDIL    │    │   10 events        │  │
│  │ • Read       │    │ • Semantic: domain │  │
│  │   sensors    │    │   knowledge (RAG)  │  │
│  │ • Receive    │    │ • Procedural: past │  │
│  │   peer msgs  │    │   action outcomes  │  │
│  └──────┬──────┘    └────────┬───────────┘  │
│         │                    │               │
│         ▼                    ▼               │
│  ┌─────────────────────────────────────┐    │
│  │ REASONING ENGINE (LLM)              │    │
│  │                                     │    │
│  │ System Prompt + CDIL snapshot       │    │
│  │ + Tool definitions                  │    │
│  │ + Recent events context             │    │
│  │                                     │    │
│  │ Output: Structured action plan      │    │
│  │ with chain-of-thought reasoning     │    │
│  └──────────────┬──────────────────────┘    │
│                 │                            │
│                 ▼                            │
│  ┌─────────────────────────────────────┐    │
│  │ ACTION EXECUTOR                     │    │
│  │ • Execute domain-specific actions   │    │
│  │ • Publish results to event bus      │    │
│  │ • Update CDIL state                 │    │
│  │ • Log to audit chain                │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### 5.2 Agent System Prompt Template

```text
You are the {DOMAIN} Agent in the NEXUS-GOV autonomous city management system
for Hyderabad, India.

YOUR RESPONSIBILITIES:
{domain_specific_responsibilities}

CURRENT CITY STATE (from CDIL):
{cdil_snapshot_json}

RECENT EVENTS (episodic memory - last 10):
{recent_events}

MESSAGES FROM OTHER AGENTS:
{pending_messages}

YOUR AVAILABLE TOOLS:
{tool_definitions}

RULES:
1. ALWAYS explain your reasoning in plain English before taking action
2. ALWAYS check cross-domain state before acting (check flood_risk before routing)
3. NEVER take actions that contradict safety priorities:
   HUMAN LIFE > PROPERTY > EFFICIENCY > COST
4. If you detect a cross-domain impact, IMMEDIATELY message the relevant agent
5. If your confidence < 0.6, request human override instead of acting autonomously
6. Log every decision with timestamp and reasoning to the audit chain
7. Use Hyderabad-specific place names and landmarks in your reasoning

Analyze the current situation and decide what actions to take. Respond with a
structured JSON action plan.
```

---

## 5.3 Individual Agent Specifications

### 🚦 Traffic Agent

| Property | Specification |
|----------|--------------|
| **ID** | `traffic_agent` |
| **Responsibility** | Optimize signal timing, clear emergency corridors, predict congestion |
| **Data Sources** | TomTom Traffic API (real), simulated intersection sensors |
| **CDIL Reads** | `zone.*.flood_risk`, `zone.*.power_status`, `emergency.active_dispatch` |
| **CDIL Writes** | `zone.*.traffic_congestion`, `road.*.travel_time`, `corridor.*.status` |
| **Trigger Conditions** | Congestion > 0.7, emergency corridor request, flood zone road blocking |

**Tools:**

```python
traffic_tools = [
    {
        "name": "set_signal_timing",
        "description": "Change traffic signal timing at an intersection to optimize flow",
        "parameters": {
            "intersection_id": {"type": "string", "description": "ID of the intersection"},
            "green_phase_seconds": {"type": "integer", "description": "Duration of green phase"},
            "priority_direction": {"type": "string", "enum": ["N", "S", "E", "W"]}
        }
    },
    {
        "name": "clear_corridor",
        "description": "Clear a traffic corridor for emergency vehicles by setting all signals to green on the route",
        "parameters": {
            "route_road_ids": {"type": "array", "items": {"type": "string"}},
            "duration_minutes": {"type": "integer"},
            "reason": {"type": "string"}
        }
    },
    {
        "name": "predict_congestion",
        "description": "Predict traffic congestion level for a zone in the next N minutes",
        "parameters": {
            "zone_id": {"type": "string"},
            "time_horizon_minutes": {"type": "integer"}
        }
    },
    {
        "name": "reroute_traffic",
        "description": "Suggest alternate routes away from a blocked or flooded road",
        "parameters": {
            "blocked_road_ids": {"type": "array", "items": {"type": "string"}},
            "affected_zones": {"type": "array", "items": {"type": "string"}}
        }
    }
]
```

**Key Cross-Domain Behaviors:**
- When `Emergency Agent` sends `CORRIDOR_REQUEST` → immediately clear corridor → respond with `CORRIDOR_CLEARED`
- When `Flood Agent` marks zone flood_risk = HIGH → mark roads in that zone as `BLOCKED` → reroute traffic
- When `Power Agent` reports signals down → flag intersections as `UNCONTROLLED` → trigger advisory

---

### ⚡ Power Agent

| Property | Specification |
|----------|--------------|
| **ID** | `power_agent` |
| **Responsibility** | Monitor grid load, prevent outages, activate backup power, manage load shedding |
| **Data Sources** | Simulated grid data (4 substations, 12 zones), consumption patterns |
| **CDIL Reads** | `zone.*.flood_risk`, `zone.*.traffic_congestion`, `hospital.*.locations` |
| **CDIL Writes** | `zone.*.power_status`, `substation.*.load_pct`, `zone.*.backup_active` |
| **Hard Constraint** | Hospital zones NEVER have power shed. `priority: CRITICAL` |

**Tools:**

```python
power_tools = [
    {
        "name": "shed_load",
        "description": "Reduce power load in a zone by a percentage. NEVER shed hospital zones.",
        "parameters": {
            "zone_id": {"type": "string"},
            "reduction_percentage": {"type": "integer", "min": 5, "max": 50}
        }
    },
    {
        "name": "activate_backup",
        "description": "Activate backup/generator power for a zone",
        "parameters": {
            "zone_id": {"type": "string"},
            "reason": {"type": "string"}
        }
    },
    {
        "name": "reroute_power",
        "description": "Reroute power from one substation to another to balance load or avoid at-risk substation",
        "parameters": {
            "from_substation": {"type": "string"},
            "to_substation": {"type": "string"},
            "load_mw": {"type": "number"}
        }
    },
    {
        "name": "predict_demand",
        "description": "Predict power demand for a zone in the next N minutes",
        "parameters": {
            "zone_id": {"type": "string"},
            "time_horizon_minutes": {"type": "integer"}
        }
    }
]
```

**Key Cross-Domain Behaviors:**
- When `Flood Agent` marks zone at risk → proactively reroute power FROM flood-zone substations BEFORE they fail
- When `Traffic Agent` needs corridor signals ON → ensure those zones have guaranteed power
- When `Meta-Agent` resolves shed vs. signals conflict → execute resolution with logged reasoning

---

### 🚑 Emergency Agent

| Property | Specification |
|----------|--------------|
| **ID** | `emergency_agent` |
| **Responsibility** | Ambulance dispatch, hospital capacity tracking, resource pre-positioning |
| **Data Sources** | Simulated emergency calls, hospital bed data (simulated) |
| **CDIL Reads** | `zone.*.traffic_congestion`, `zone.*.flood_risk`, `corridor.*.status`, `zone.*.power_status` |
| **CDIL Writes** | `emergency.active_dispatch`, `ambulance.*.position`, `ambulance.*.status`, `hospital.*.incoming` |
| **Critical Protocol** | Always request corridor clearing BEFORE dispatching ambulance |

**Tools:**

```python
emergency_tools = [
    {
        "name": "dispatch_ambulance",
        "description": "Dispatch an ambulance from its current location to a destination, using the optimal route considering current traffic and flood conditions",
        "parameters": {
            "ambulance_id": {"type": "string"},
            "destination_zone": {"type": "string"},
            "case_type": {"type": "string", "enum": ["cardiac", "trauma", "respiratory", "general"]},
            "route_preference": {"type": "string", "enum": ["fastest", "safest", "avoid_flood"]}
        }
    },
    {
        "name": "pre_position_ambulance",
        "description": "Move an idle ambulance to a strategic position in anticipation of emergencies",
        "parameters": {
            "ambulance_id": {"type": "string"},
            "target_zone": {"type": "string"},
            "reason": {"type": "string"}
        }
    },
    {
        "name": "alert_hospital",
        "description": "Alert a hospital about an incoming patient with ETA and case details",
        "parameters": {
            "hospital_id": {"type": "string"},
            "eta_minutes": {"type": "integer"},
            "case_type": {"type": "string"},
            "severity": {"type": "integer", "min": 1, "max": 10}
        }
    },
    {
        "name": "request_corridor_clearing",
        "description": "Request the Traffic Agent to clear a corridor for emergency vehicle passage",
        "parameters": {
            "route_road_ids": {"type": "array", "items": {"type": "string"}},
            "urgency": {"type": "string", "enum": ["HIGH", "CRITICAL"]}
        }
    }
]
```

**Key Cross-Domain Behaviors:**
- When flood_risk rises → pre-position ambulances OUTSIDE flood zones but within rapid response distance
- Dispatch sequence: `request_corridor_clearing()` → wait for `CORRIDOR_CLEARED` → `dispatch_ambulance()`
- When power is down in a zone → factor in non-functioning traffic signals when routing

---

### 🌊 Flood Agent

| Property | Specification |
|----------|--------------|
| **ID** | `flood_agent` |
| **Responsibility** | Monitor rainfall, predict flooding, identify evacuation zones, trigger preemptive cascading responses |
| **Data Sources** | OpenWeatherMap API (real), simulated rain gauges, historical Hyderabad flood patterns |
| **CDIL Reads** | `zone.*.population_density`, `road.*.elevation`, `substation.*.location` |
| **CDIL Writes** | `zone.*.flood_risk`, `zone.*.water_level`, `zone.*.evacuation_status` |
| **Role** | First responder for weather events. Cascade trigger for all other agents. |

**Tools:**

```python
flood_tools = [
    {
        "name": "assess_flood_risk",
        "description": "Assess flood risk for a zone based on current rainfall, terrain, and drainage capacity",
        "parameters": {
            "zone_id": {"type": "string"},
            "current_rainfall_mm_hr": {"type": "number"},
            "duration_hours": {"type": "number"}
        }
    },
    {
        "name": "trigger_evacuation_alert",
        "description": "Trigger evacuation alert for a zone, notifying all agents and the command center",
        "parameters": {
            "zone_id": {"type": "string"},
            "severity": {"type": "string", "enum": ["ADVISORY", "WARNING", "CRITICAL"]},
            "estimated_water_level_m": {"type": "number"}
        }
    },
    {
        "name": "broadcast_to_all_agents",
        "description": "Send a CRITICAL alert to ALL other agents simultaneously",
        "parameters": {
            "event_type": {"type": "string"},
            "affected_zones": {"type": "array", "items": {"type": "string"}},
            "message": {"type": "string"},
            "recommended_actions": {"type": "object"}
        }
    },
    {
        "name": "predict_water_level",
        "description": "Predict water level in a zone based on rainfall trajectory",
        "parameters": {
            "zone_id": {"type": "string"},
            "hours_ahead": {"type": "integer"}
        }
    }
]
```

**Trigger Thresholds:**
- Rainfall > 65mm/hr sustained 1+ hours → `flood_risk = HIGH`
- Rainfall > 100mm/hr OR water level > 0.5m → `flood_risk = CRITICAL`
- On CRITICAL → auto-broadcast to ALL agents with cascading recommendations

---

### 🧠 Meta-Orchestrator

| Property | Specification |
|----------|--------------|
| **ID** | `meta_orchestrator` |
| **Responsibility** | Coordinate agents, resolve conflicts, decompose complex goals, maintain global coherence |
| **LLM** | Gemini 2.0 Flash (higher token budget — up to 8K output) |
| **Activation** | Always active. Monitors all agent messages. Intervenes on conflicts. |

**Conflict Resolution Protocol:**

```
1. Detect conflict: Two agents propose contradictory actions
   Example: Power Agent → shed_load(zone_a1)
            Traffic Agent → needs signals ON in zone_a1 for corridor

2. Evaluate utility functions:
   U(shed_load) = 0.6 × safety(0.3) + 0.25 × efficiency(0.8) + 0.15 × cost(0.7) = 0.485
   U(keep_power) = 0.6 × safety(0.9) + 0.25 × efficiency(0.4) + 0.15 × cost(0.3) = 0.685

3. Resolution: keep_power WINS (higher utility, safety-weighted)
   → Power Agent: shed load in zone_b3 instead (non-critical residential)
   → Traffic Agent: corridor clearing proceeds

4. Log: Full reasoning chain → audit trail → dashboard notification
```

**Global Monitoring:**
- Scans all agent messages every cycle
- Detects when agents haven't responded to cross-domain events
- Detects when multiple agents are acting on the same zone simultaneously
- Can PAUSE any agent and request human override

---

## 6. Cross-Domain Inference Layer (CDIL)

### 6.1 Knowledge Graph Schema

```
NODES:
  Zone         { id, name, population, area_km2, elevation_m }
  Road         { id, name, from_zone, to_zone, lanes, flood_prone: bool }
  Substation   { id, name, zone, capacity_mw, has_backup: bool }
  Hospital     { id, name, zone, beds_total, icu_beds }
  Ambulance    { id, home_zone, status: IDLE|DISPATCHED|EN_ROUTE|AT_SCENE }
  Intersection { id, zone, signal_phases, current_phase }

REAL-TIME STATE (updated by agents):
  zone:a1:flood_risk         = LOW|MODERATE|HIGH|CRITICAL
  zone:a1:traffic_congestion = 0.0 - 1.0
  zone:a1:power_status       = ACTIVE|DEGRADED|DOWN|BACKUP
  zone:a1:evacuation_status  = NORMAL|ADVISORY|EVACUATING
  road:r1:status             = OPEN|CONGESTED|BLOCKED|FLOODED
  road:r1:travel_time_min    = float
  substation:s1:load_pct     = 0-100
  substation:s1:is_flooded   = true|false
  hospital:h1:beds_available = integer
  hospital:h1:icu_available  = integer
  ambulance:a1:zone          = zone_id
  ambulance:a1:status        = IDLE|DISPATCHED|EN_ROUTE
  corridor:c1:status         = INACTIVE|CLEARING|CLEARED

CAUSAL LINKS (predefined):
  flood_risk(zone) = HIGH     →  road_status(roads_in_zone) = FLOODED
  road_status(road) = FLOODED →  traffic_congestion(adjacent_zones) += 0.3
  flood_risk(zone) = HIGH     →  substation_risk(substations_in_zone) = HIGH
  power_status(zone) = DOWN   →  signal_status(intersections_in_zone) = DARK
  traffic_congestion(zone) > 0.8 → ambulance_travel_time(zone) × 2.5
```

### 6.2 Hyderabad City Model (Digital Twin Data)

```python
HYDERABAD_MODEL = {
    "zones": [
        {"id": "zone_a1", "name": "Begumpet",       "population": 85000,  "elevation_m": 536},
        {"id": "zone_a2", "name": "Secunderabad",    "population": 120000, "elevation_m": 540},
        {"id": "zone_a3", "name": "Ameerpet",        "population": 95000,  "elevation_m": 530},
        {"id": "zone_b1", "name": "Kukatpally",      "population": 200000, "elevation_m": 545},
        {"id": "zone_b2", "name": "HITEC City",      "population": 150000, "elevation_m": 560},
        {"id": "zone_b3", "name": "Gachibowli",      "population": 110000, "elevation_m": 555},
        {"id": "zone_c1", "name": "Khairatabad",     "population": 70000,  "elevation_m": 510},
        {"id": "zone_c2", "name": "Hussain Sagar",   "population": 40000,  "elevation_m": 505},
        {"id": "zone_c3", "name": "LB Nagar",        "population": 180000, "elevation_m": 520},
        {"id": "zone_d1", "name": "Malkajgiri",      "population": 160000, "elevation_m": 538},
        {"id": "zone_d2", "name": "Uppal",           "population": 140000, "elevation_m": 525},
        {"id": "zone_d3", "name": "Dilsukhnagar",    "population": 130000, "elevation_m": 515},
    ],
    "roads": [
        {"id": "r_a1_a2", "name": "Rasoolpura Rd",   "from": "zone_a1", "to": "zone_a2", "lanes": 4, "flood_prone": False},
        {"id": "r_a1_a3", "name": "Begumpet-Ameerpet", "from": "zone_a1", "to": "zone_a3", "lanes": 6, "flood_prone": False},
        {"id": "r_a3_c1", "name": "Punjagutta Rd",   "from": "zone_a3", "to": "zone_c1", "lanes": 4, "flood_prone": True},
        {"id": "r_c1_c2", "name": "Tank Bund Rd",    "from": "zone_c1", "to": "zone_c2", "lanes": 6, "flood_prone": True},
        {"id": "r_c2_c3", "name": "Chaderghat Rd",   "from": "zone_c2", "to": "zone_c3", "lanes": 4, "flood_prone": True},
        {"id": "r_b1_b2", "name": "JNTU-HITEC Rd",   "from": "zone_b1", "to": "zone_b2", "lanes": 6, "flood_prone": False},
        {"id": "r_b2_b3", "name": "Cyber Towers Rd", "from": "zone_b2", "to": "zone_b3", "lanes": 4, "flood_prone": False},
        {"id": "r_d1_d2", "name": "Malkajgiri-Uppal","from": "zone_d1", "to": "zone_d2", "lanes": 4, "flood_prone": True},
    ],
    "substations": [
        {"id": "sub_1", "name": "Begumpet SS",      "zone": "zone_a1", "capacity_mw": 200, "backup": True},
        {"id": "sub_2", "name": "Kukatpally SS",     "zone": "zone_b1", "capacity_mw": 350, "backup": True},
        {"id": "sub_3", "name": "LB Nagar SS",       "zone": "zone_c3", "capacity_mw": 250, "backup": False},
        {"id": "sub_4", "name": "Secunderabad SS",   "zone": "zone_a2", "capacity_mw": 300, "backup": True},
    ],
    "hospitals": [
        {"id": "hosp_1", "name": "NIMS Hospital",    "zone": "zone_c1", "beds": 1500, "icu": 200},
        {"id": "hosp_2", "name": "Gandhi Hospital",  "zone": "zone_a2", "beds": 1200, "icu": 150},
        {"id": "hosp_3", "name": "Yashoda Hospital", "zone": "zone_b1", "beds": 500,  "icu": 80},
        {"id": "hosp_4", "name": "Apollo Hospital",  "zone": "zone_b3", "beds": 800,  "icu": 120},
        {"id": "hosp_5", "name": "KIMS Hospital",    "zone": "zone_a2", "beds": 600,  "icu": 90},
        {"id": "hosp_6", "name": "Care Hospital",    "zone": "zone_c3", "beds": 450,  "icu": 60},
    ],
    "ambulances": [
        {"id": "amb_1", "home": "zone_a1"}, {"id": "amb_2", "home": "zone_b1"},
        {"id": "amb_3", "home": "zone_c3"}, {"id": "amb_4", "home": "zone_b3"},
        {"id": "amb_5", "home": "zone_a2"}, {"id": "amb_6", "home": "zone_d1"},
        {"id": "amb_7", "home": "zone_c1"}, {"id": "amb_8", "home": "zone_d3"},
    ]
}
```

### 6.3 Agent Communication Protocol

**Message Schema:**

```json
{
  "id": "uuid-v4",
  "timestamp": "2026-03-14T22:14:03.456+05:30",
  "from": "flood_agent",
  "to": "emergency_agent | ALL",
  "type": "ALERT | REQUEST | RESPONSE | OVERRIDE | CONFLICT | STATUS",
  "priority": "LOW | MEDIUM | HIGH | CRITICAL",
  "payload": {
    "event": "flash_flood",
    "affected_zones": ["zone_c1", "zone_c2"],
    "data": {}
  },
  "reasoning": "Plain English explanation of why this message was sent",
  "cdil_updates": [
    {"key": "zone:c2:flood_risk", "value": "HIGH", "confidence": 0.89}
  ]
}
```

**Communication Patterns:**

| Pattern | Example | Implementation |
|---------|---------|----------------|
| **Broadcast** | Flood Agent → ALL agents | Publish to `nexus:broadcast` stream |
| **Direct** | Emergency → Traffic (corridor request) | Publish to `nexus:agent:{target_id}` stream |
| **Request-Response** | Emergency requests corridor → Traffic confirms cleared | Request with `correlation_id`, response references same ID |
| **Conflict Report** | Power + Traffic conflict → Meta-Agent | Both publish to `nexus:conflicts` stream |

---

*Continued in [PRD-PART3-TECH.md](./PRD-PART3-TECH.md)*
