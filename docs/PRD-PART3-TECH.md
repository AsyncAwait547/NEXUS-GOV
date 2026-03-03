# PRD Part 3: AI/ML Components, Data Strategy, Tech Stack, API Contracts

## 7. AI/ML Components

### 7.1 Component Matrix

| Component | Model/Method | Purpose | Build Time | Priority |
|-----------|-------------|---------|:----------:|:--------:|
| **Domain Agent Reasoning** | Gemini 2.0 Flash API (function calling) | Each agent's "brain" — perceive, reason, act | 2-3 hrs | **P0** |
| **Meta-Orchestrator** | Gemini 2.0 Flash (higher token budget) | Conflict resolution, goal decomposition | 1-2 hrs | **P0** |
| **Flood Risk Prediction** | Rule-based thresholds + LLM reasoning | Predict flood risk from rainfall data | 1 hr | **P0** |
| **Traffic Prediction** | LLM + historical congestion patterns | Predict congestion from current state + events | 1 hr | **P1** |
| **Causal Inference** | LLM chain-of-thought + pre-defined rule engine | "If X happens in domain A → predict Y in domain B" | 1-2 hrs | **P1** |
| **Anomaly Detection** | Threshold-based + LLM interpretation | Detect unusual patterns in sensor data | 30 min | **P2** |
| **NLP Interface** | LLM with full CDIL context | Natural language queries from operators | 1 hr | **P3** |

### 7.2 LLM Strategy — Why API Calls Beat Fine-Tuning

| Approach | Fine-Tuned Models (as in original NEXUS-GOV spec) | API-Based Reasoning (our approach) |
|----------|:-:|:-:|
| Setup time | 4-6 hours per model × 4 agents = 16-24 hours | 30 min per agent × 4 = 2 hours |
| Quality at hackathon | Low (insufficient training data/time) | High (Gemini 2.0 Flash is excellent at structured reasoning) |
| Function calling | Need custom implementation | Native support in Gemini API |
| Fallback | None — if model is bad, you're stuck | Switch to Groq (Llama 3.3) in 5 minutes |
| Demo reliability | Unpredictable | Highly predictable with good prompts |

**Decision:** Use Gemini 2.0 Flash API with expertly crafted system prompts + function calling. This gives you 95% of the quality in 10% of the time.

### 7.3 LLM Function Calling Implementation

```python
# agent_base.py -- Base agent class with LLM integration
import google.generativeai as genai
import json

class DomainAgent:
    def __init__(self, agent_id, system_prompt, tools, cdil, event_bus, audit_chain):
        self.agent_id = agent_id
        self.system_prompt = system_prompt
        self.tools = tools
        self.cdil = cdil
        self.event_bus = event_bus
        self.audit = audit_chain
        self.episodic_memory = []  # Last 10 events
        
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=system_prompt,
            tools=tools
        )
        self.chat = self.model.start_chat()
    
    async def perceive(self):
        """Read current state from CDIL + pending messages"""
        cdil_state = await self.cdil.get_snapshot()
        messages = await self.event_bus.get_pending(self.agent_id)
        return cdil_state, messages
    
    async def reason_and_act(self, cdil_state, messages):
        """Send state to LLM, get action plan, execute"""
        context = f"""
        CURRENT CITY STATE:
        {json.dumps(cdil_state, indent=2)}
        
        PENDING MESSAGES FROM OTHER AGENTS:
        {json.dumps(messages, indent=2)}
        
        RECENT EVENTS (your memory):
        {json.dumps(self.episodic_memory[-10:], indent=2)}
        
        Analyze the situation. If action is needed, use your tools.
        If no action is needed, respond with "STATUS: MONITORING"
        """
        
        response = await self.chat.send_message_async(context)
        
        # Process function calls from LLM
        for part in response.parts:
            if hasattr(part, 'function_call'):
                result = await self.execute_tool(part.function_call)
                # Log to audit chain
                self.audit.log_decision(
                    agent=self.agent_id,
                    action=part.function_call.name,
                    reasoning=self.extract_reasoning(response),
                    cdil_state=cdil_state
                )
                # Update episodic memory
                self.episodic_memory.append({
                    "action": part.function_call.name,
                    "args": dict(part.function_call.args),
                    "result": result,
                    "timestamp": time.time()
                })
        
        return response
    
    async def run_cycle(self):
        """One perception-reasoning-action cycle"""
        cdil_state, messages = await self.perceive()
        response = await self.reason_and_act(cdil_state, messages)
        return response
```

### 7.4 Causal Inference Engine

Instead of complex tools like DoWhy, implement causal reasoning as a **rule engine + LLM enhancement**:

```python
# causal_engine.py
CAUSAL_RULES = [
    {
        "condition": {"key": "zone:*:flood_risk", "value": "HIGH"},
        "effects": [
            {"key": "road:*:status", "value": "FLOODED", "filter": "roads_in_zone", "confidence": 0.85},
            {"key": "zone:*:traffic_congestion", "delta": +0.3, "filter": "adjacent_zones", "confidence": 0.75},
        ],
        "description": "Flooding blocks roads and increases traffic in adjacent zones"
    },
    {
        "condition": {"key": "substation:*:is_flooded", "value": True},
        "effects": [
            {"key": "zone:*:power_status", "value": "DOWN", "filter": "zones_served_by_substation", "confidence": 0.90},
            {"key": "intersection:*:signal_status", "value": "DARK", "filter": "intersections_in_zone", "confidence": 0.95},
        ],
        "description": "Flooded substation causes power outage and dark signals"
    },
    {
        "condition": {"key": "zone:*:power_status", "value": "DOWN"},
        "effects": [
            {"key": "zone:*:traffic_congestion", "delta": +0.2, "filter": "same_zone", "confidence": 0.70},
        ],
        "description": "Power outage darkens signals, increasing congestion"
    },
    {
        "condition": {"key": "zone:*:traffic_congestion", "threshold": 0.8},
        "effects": [
            {"key": "ambulance:*:travel_time_multiplier", "value": 2.5, "filter": "ambulances_in_zone", "confidence": 0.80},
        ],
        "description": "High congestion drastically increases ambulance response time"
    }
]

class CausalEngine:
    def __init__(self, cdil):
        self.cdil = cdil
        self.rules = CAUSAL_RULES
    
    async def propagate_effects(self, trigger_key, trigger_value):
        """When a CDIL value changes, propagate causal effects"""
        effects_applied = []
        for rule in self.rules:
            if self.matches(rule["condition"], trigger_key, trigger_value):
                for effect in rule["effects"]:
                    affected_keys = self.resolve_filter(effect["filter"], trigger_key)
                    for key in affected_keys:
                        await self.cdil.update(key, effect["value"], 
                                              source="causal_engine",
                                              confidence=effect["confidence"])
                        effects_applied.append({
                            "rule": rule["description"],
                            "key": key, 
                            "value": effect["value"]
                        })
        return effects_applied
```

---

## 8. Data Strategy

### 8.1 Real Data Sources (Free APIs)

| Source | API | Data | Free Tier | API Key Required |
|--------|-----|------|-----------|:---:|
| **Weather/Rainfall** | OpenWeatherMap | Current rainfall, forecast, humidity | 1,000 calls/day | Yes (free signup) |
| **Traffic Flow** | TomTom Traffic | Real-time speed/congestion by location | 2,500 calls/day | Yes (free signup) |
| **News/Incidents** | NewsAPI | Breaking incident reports | 100 calls/day | Yes (free signup) |
| **Geocoding** | OpenStreetMap Nominatim | Address ↔ coordinates | Unlimited (rate limited) | No |
| **Map Tiles** | CartoDB Dark Matter | Dark-themed map rendering | Unlimited | No |
| **Routing** | OSRM (OpenStreetMap) | Route calculation | Unlimited (self-hosted) | No |

### 8.2 Scenario Injector

Pre-built crisis scenarios for controlled demo:

```python
# scenarios.py
SCENARIOS = {
    "monsoon_flood": {
        "name": "Monsoon Flash Flood — Musi River Basin",
        "description": "Heavy rainfall causes flooding in low-elevation Hussain Sagar and Khairatabad zones",
        "trigger": {
            "type": "rainfall_spike",
            "zone": "zone_c2",
            "intensity_mm_hr": 95,
            "duration_hrs": 2
        },
        "cascading_timeline": [
            {"delay_sec": 0,  "event": "rainfall_anomaly",   "zones": ["zone_c2"]},
            {"delay_sec": 5,  "event": "flood_risk_high",    "zones": ["zone_c2", "zone_c1"]},
            {"delay_sec": 10, "event": "roads_flooded",      "roads": ["r_c1_c2", "r_c2_c3"]},
            {"delay_sec": 15, "event": "substation_at_risk",  "substation": "sub_3"},
            {"delay_sec": 20, "event": "traffic_gridlock",    "zones": ["zone_c1", "zone_c3", "zone_d3"]},
            {"delay_sec": 30, "event": "emergency_call",      "zone": "zone_c1", "type": "cardiac"},
        ],
        "expected_agent_responses": [
            "Flood Agent: detect + classify + alert all agents",
            "Emergency Agent: pre-position ambulances outside C1/C2",
            "Traffic Agent: clear corridor for ambulance access",
            "Power Agent: reroute power from sub_3 to sub_2/sub_4",
            "Meta-Agent: coordinate if conflicts arise"
        ]
    },
    "industrial_fire": {
        "name": "Industrial Fire — Jeedimetla Area",
        "description": "Chemical factory fire in Malkajgiri industrial zone",
        "trigger": {
            "type": "fire_alert",
            "zone": "zone_d1",
            "severity": 8
        },
        "cascading_timeline": [
            {"delay_sec": 0,  "event": "fire_detected",       "zone": "zone_d1"},
            {"delay_sec": 5,  "event": "emergency_dispatch",   "type": "fire", "zone": "zone_d1"},
            {"delay_sec": 10, "event": "traffic_surge",        "zones": ["zone_d1", "zone_a2"]},
            {"delay_sec": 15, "event": "power_load_spike",     "substation": "sub_4"},
        ]
    },
    "dual_crisis": {
        "name": "Simultaneous Flood + Industrial Fire",
        "description": "Worst case: two crises competing for the same resources",
        "purpose": "Demo adversarial scenario — agents handle parallel crises with resource contention",
        "triggers": [
            {"type": "rainfall_spike", "zone": "zone_c2", "intensity_mm_hr": 110, "delay_sec": 0},
            {"type": "fire_alert", "zone": "zone_d1", "severity": 7, "delay_sec": 15}
        ],
        "key_conflict": "Ambulances needed in BOTH zones. Meta-Agent must prioritize based on severity and available resources."
    }
}
```

---

## 9. Tech Stack — Definitive Choices

| Layer | Technology | Version | Why |
|-------|-----------|---------|-----|
| **Language** | Python | 3.11+ | LangChain/LangGraph native |
| **API Framework** | FastAPI | 0.110+ | Async, WebSocket, auto-docs |
| **Agent Framework** | LangGraph | 0.2+ | State-machine agent orchestration |
| **LLM Primary** | Google Gemini 2.0 Flash | API | Free, fast, function calling |
| **LLM Fallback** | Groq (Llama 3.3 70B) | API | Free, ultra-fast inference |
| **Event Bus** | Redis Streams | 7.0+ | Ordered messaging, consumer groups |
| **CDIL Primary** | Redis Hash | 7.0+ | Fast state access |
| **CDIL Optional** | Neo4j Community | 5.x | Graph queries if time permits |
| **Audit Chain** | SQLite + hashlib | built-in | Hash-chained immutable log |
| **MQTT Broker** | Mosquitto | 2.x | IoT sensor ingestion |
| **Frontend** | React + Vite | 18.x / 5.x | Fast dev, component-based |
| **Maps** | Leaflet.js + CartoDB Dark | 1.9+ | Free, dark tiles, no API key |
| **Real-time** | Socket.IO (python-socketio) | 5.x | Agent events → dashboard |
| **Charts** | Recharts | latest | Timeline, gauges |
| **Animation** | Framer Motion | latest | Micro-animations |
| **Styling** | Vanilla CSS | - | Glassmorphism dark theme |
| **Containers** | Docker Compose | 2.x | Multi-service orchestration |
| **IoT Hardware** | Raspberry Pi 4 + DHT22 | optional | Physical sensor prop |

### Docker Compose Configuration

```yaml
version: "3.9"
services:
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command: redis-server --appendonly yes
    volumes: ["redis-data:/data"]

  mosquitto:
    image: eclipse-mosquitto:2
    ports: ["1883:1883", "9001:9001"]
    volumes: ["./config/mosquitto.conf:/mosquitto/config/mosquitto.conf"]

  neo4j:  # Optional — drop if time-constrained
    image: neo4j:5-community
    ports: ["7474:7474", "7687:7687"]
    environment:
      NEO4J_AUTH: neo4j/nexusgov2026
      NEO4J_PLUGINS: '[]'
    profiles: ["full"]  # Only starts with --profile full

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [redis, mosquitto]
    environment:
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      GROQ_API_KEY: ${GROQ_API_KEY}
      REDIS_URL: redis://redis:6379
      MQTT_BROKER: mosquitto
      MQTT_PORT: 1883
    volumes: ["./backend:/app"]

  simulator:
    build: ./simulator
    depends_on: [redis, mosquitto]
    environment:
      REDIS_URL: redis://redis:6379
      MQTT_BROKER: mosquitto

  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    depends_on: [backend]
    volumes: ["./frontend:/app", "/app/node_modules"]

volumes:
  redis-data:
```

---

## 10. API Contracts

### 10.1 REST Endpoints

```
# City State
GET  /api/v1/city/state                    → Full CDIL snapshot (all zones, roads, etc.)
GET  /api/v1/city/zones                    → All zone states
GET  /api/v1/city/zones/{zone_id}          → Specific zone state

# Agents
GET  /api/v1/agents                        → All agent statuses
GET  /api/v1/agents/{agent_id}/status      → Specific agent status
GET  /api/v1/agents/{agent_id}/reasoning   → Agent's reasoning log (last N entries)
GET  /api/v1/agents/{agent_id}/memory      → Agent's episodic memory

# Events
GET  /api/v1/events/timeline               → Event timeline (ordered)
GET  /api/v1/events/messages                → Inter-agent messages

# Audit
GET  /api/v1/audit/chain                   → Full audit trail
GET  /api/v1/audit/verify                  → Chain integrity verification
GET  /api/v1/audit/chain/{hash}            → Specific decision by hash

# Actions
POST /api/v1/scenarios/inject              → Trigger a crisis scenario
     Body: {"scenario": "monsoon_flood"}
POST /api/v1/override/{agent_id}           → Override agent decision
     Body: {"action": "cancel", "decision_hash": "abc123", "reason": "..."}
POST /api/v1/override/pause-all            → Pause all agents
POST /api/v1/override/resume-all           → Resume all agents

# Sensors (if hardware connected)
GET  /api/v1/sensors                       → All sensor readings
POST /api/v1/sensors/simulate              → Inject simulated sensor data
```

### 10.2 WebSocket Event Schema

```
Connection: ws://localhost:8000/ws/events

// Server → Client Events:

// Agent status change
{"type": "agent_status", "agent": "flood_agent", "status": "CRITICAL", "action_count": 5}

// Agent reasoning (live streamed text)  
{"type": "agent_reasoning", "agent": "traffic_agent", "text": "Clearing corridor R-C1-A1 for ambulance AMB-7. Estimated clear time: 3 minutes.", "timestamp": "2026-03-14T22:14:07+05:30"}

// CDIL state change
{"type": "cdil_update", "key": "zone:c2:flood_risk", "value": "HIGH", "agent": "flood_agent", "confidence": 0.89}

// Map marker update (ambulance moved)
{"type": "map_update", "subtype": "ambulance_move", "id": "amb_3", "lat": 17.385, "lng": 78.486, "status": "EN_ROUTE"}

// Map overlay update (flood zone)
{"type": "map_update", "subtype": "flood_zone", "zone_id": "zone_c2", "risk_level": "HIGH"}

// Map overlay update (corridor)
{"type": "map_update", "subtype": "corridor", "road_ids": ["r_c1_a1", "r_a1_a2"], "status": "CLEARING"}

// Audit entry
{"type": "audit_entry", "hash": "a3f8b2c1", "prev_hash": "7d2e9f01", "agent": "power_agent", "action": "reroute_power", "reasoning": "..."}

// Timeline event
{"type": "timeline_event", "phase": "classify", "label": "Flash Flood - Severity 8", "timestamp": "..."}

// Inter-agent message (for display in reasoning log)
{"type": "agent_message", "from": "flood_agent", "to": "emergency_agent", "priority": "CRITICAL", "summary": "Flash flood alert for zones C1, C2"}

// Threat level change
{"type": "threat_level", "level": 4, "max": 5, "reason": "Active flood + emergency dispatch"}
```

---

## 11. Blockchain Audit Layer

### Hash-Chained SQLite Implementation

```python
# audit_chain.py
import hashlib, json, time, sqlite3
from datetime import datetime

class AuditChain:
    def __init__(self, db_path="data/audit.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent TEXT NOT NULL,
                action TEXT NOT NULL,
                parameters TEXT,
                reasoning TEXT NOT NULL,
                cdil_state_hash TEXT NOT NULL,
                prev_hash TEXT NOT NULL,
                current_hash TEXT NOT NULL
            )
        """)
        self.conn.commit()
        self.prev_hash = self._get_last_hash() or "GENESIS_BLOCK"
    
    def _get_last_hash(self):
        row = self.conn.execute(
            "SELECT current_hash FROM decisions ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None
    
    def log_decision(self, agent: str, action: str, reasoning: str, 
                     cdil_state: dict, parameters: dict = None) -> dict:
        timestamp = datetime.now().isoformat()
        cdil_hash = hashlib.sha256(
            json.dumps(cdil_state, sort_keys=True).encode()
        ).hexdigest()[:16]
        
        data_string = f"{timestamp}|{agent}|{action}|{reasoning}|{cdil_hash}|{self.prev_hash}"
        current_hash = hashlib.sha256(data_string.encode()).hexdigest()[:16]
        
        self.conn.execute(
            """INSERT INTO decisions 
               (timestamp, agent, action, parameters, reasoning, cdil_state_hash, prev_hash, current_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (timestamp, agent, action, json.dumps(parameters), reasoning, 
             cdil_hash, self.prev_hash, current_hash)
        )
        self.conn.commit()
        self.prev_hash = current_hash
        
        return {
            "hash": current_hash,
            "prev_hash": self.prev_hash,
            "agent": agent,
            "action": action,
            "timestamp": timestamp
        }
    
    def verify_chain_integrity(self) -> tuple:
        """Verify no decisions have been tampered with. Returns (is_valid, message)"""
        rows = self.conn.execute(
            "SELECT * FROM decisions ORDER BY id"
        ).fetchall()
        
        if not rows:
            return True, "Empty chain — no decisions recorded yet"
        
        prev = "GENESIS_BLOCK"
        for row in rows:
            data_string = f"{row[1]}|{row[2]}|{row[3]}|{row[5]}|{row[6]}|{row[7]}"
            expected_hash = hashlib.sha256(data_string.encode()).hexdigest()[:16]
            
            if expected_hash != row[8]:
                return False, f"TAMPER DETECTED at decision #{row[0]} by {row[2]}"
            if row[7] != prev:
                return False, f"CHAIN BREAK at decision #{row[0]} — prev_hash mismatch"
            prev = row[8]
        
        return True, f"Chain integrity VERIFIED. {len(rows)} decisions audited."
    
    def get_recent(self, n: int = 20) -> list:
        rows = self.conn.execute(
            "SELECT * FROM decisions ORDER BY id DESC LIMIT ?", (n,)
        ).fetchall()
        return [
            {
                "id": r[0], "timestamp": r[1], "agent": r[2], "action": r[3],
                "parameters": json.loads(r[4]) if r[4] else None,
                "reasoning": r[5], "hash": r[8], "prev_hash": r[7]
            }
            for r in reversed(rows)
        ]
```

**Demo talking point:** *"Every autonomous decision is cryptographically chained. If anyone tampers with a single record, the chain breaks. This gives governments the accountability they need to trust autonomous AI."*

---

*Continued in [PRD-PART4-FRONTEND.md](./PRD-PART4-FRONTEND.md)*
