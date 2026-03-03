# PRD Part 5: Execution Plan, Roles, Risk Matrix

## 13. 24-Hour Build Plan

### 13.1 Priority Classification

```
P0 (MUST HAVE — Demo fails without these):
  ✅ At least 2 agents (Flood + Emergency) communicating via event bus
  ✅ CDIL shared state (Redis Hash minimum)
  ✅ Dashboard with map showing zone states (color-coded)
  ✅ Agent reasoning log visible on dashboard (live text feed)
  ✅ One crisis scenario triggering agent cascade
  ✅ WebSocket push from backend to frontend
  ✅ Scenario injector button (trigger crisis from UI)

P1 (SHOULD HAVE — Makes demo impressive):
  ✅ All 4 domain agents + meta-orchestrator (5 total)
  ✅ Cross-agent messaging visible in reasoning log
  ✅ Human override functionality (pause + reassign)
  ✅ Audit trail with hash chain verification
  ✅ Event timeline component on dashboard
  ✅ Second crisis scenario (parallel crisis handling)
  ✅ Ambulance markers on map

P2 (NICE TO HAVE — Awards differentiators):
  ✅ Neo4j knowledge graph (instead of Redis Hash)
  ✅ Physical IoT sensor (Raspberry Pi + DHT22)
  ✅ Adversarial resilience test (sensor node failure)
  ✅ NLP natural language query interface
  ✅ Animated ambulance movement on map
  ✅ Telugu language alerts from Herald Agent
  ✅ Conflict resolution demo visible on dashboard
  ✅ Sound effects for crisis alerts
```

### 13.2 Hour-by-Hour Schedule

**Assumptions:** 4 team members, hackathon starts 10:00 AM March 14.

#### PHASE 1: Foundation (Hours 0-7, 10AM-5PM)

| Hour | Time | Member 1 (Backend Lead) | Member 2 (AI/Agent Lead) | Member 3 (Frontend Lead) | Member 4 (Integration/Demo) |
|:----:|------|------------------------|-------------------------|-------------------------|---------------------------|
| 0 | 10:00 | Docker Compose: Redis + Mosquitto + FastAPI scaffold | LangGraph setup, install deps, test Gemini API | React+Vite scaffold, CSS variables, dark theme | City model data files, zone coords, GeoJSON |
| 1 | 11:00 | CDIL Redis Hash implementation (get/set/subscribe) | Base DomainAgent class with LLM integration | Leaflet map component with CartoDB dark tiles | API contract docs, test data preparation |
| 2 | 12:00 | Redis Streams event bus (pub/sub between agents) | Flood Agent: prompt, tools, LLM function calling | Zone overlay polygons on map (color-coded) | Socket.IO server setup + test client |
| 3 | 13:00 | WebSocket server (Socket.IO) + event routing | Flood Agent testing + refinement | Agent Status Panel component | Connect Socket.IO: backend → frontend |
| 4 | 14:00 | Scenario injector endpoint + monsoon_flood scenario | Emergency Agent: prompt, tools, cross-agent msg | Agent Reasoning Log (typewriter effect) | End-to-end test: inject → agent → dashboard |
| 5 | 15:00 | FastAPI endpoints: /city/state, /agents/status | Emergency Agent testing + Flood↔Emergency comms | Hook up reasoning log to live WebSocket data | Debug full pipeline, fix data format issues |
| 6 | 16:00 | Review + bugfix, prepare checkpoint demo | Refine agent prompts for impressive reasoning | Polish map + panels for checkpoint | Prepare checkpoint talking points |
| **7** | **17:00** | **⚡ CHECKPOINT 1: Flood detects → alerts Emergency → dashboard shows reasoning** |

#### PHASE 2: Expansion (Hours 7-13, 5PM-11PM)

| Hour | Time | Member 1 | Member 2 | Member 3 | Member 4 |
|:----:|------|----------|----------|----------|----------|
| 7 | 17:00 | Human override API endpoints (pause/resume/override) | Traffic Agent: corridor clearing, congestion logic | Ambulance markers on map (custom icons) | Test cross-agent message flow |
| 8 | 18:00 | Audit chain implementation (hash-chained SQLite) | Power Agent: load rerouting, hospital protection | Substation markers + flood overlay (blue gradient) | Connect audit entries to dashboard |
| 9 | 19:00 | Audit verification endpoint | Meta-Orchestrator: conflict detection + resolution | Event Timeline component (horizontal) | Test 4-agent cascade scenario |
| 10 | 20:00 | Second scenario: industrial_fire | Cross-agent conflict scenario (power vs traffic) | Audit Trail panel + hash display | Full pipeline: scenario → 4 agents → dashboard |
| 11 | 21:00 | WebSocket events for all new components | Agent prompt engineering sprint (make reasoning Hyderabad-specific, impressive) | Override Panel + modal | End-to-end testing all scenarios |
| 12 | 22:00 | Review + bugfix, checkpoint prep | Review + bugfix, checkpoint prep | Threat Level indicator bar | Checkpoint prep |
| **13** | **23:00** | **⚡ CHECKPOINT 2: All 4 agents + meta + map + timeline + override** |

#### PHASE 3: Polish (Hours 13-20, 11PM-6AM)

| Hour | Time | Member 1 | Member 2 | Member 3 | Member 4 |
|:----:|------|----------|----------|----------|----------|
| 13 | 23:00 | Dual crisis scenario (parallel handling) | Agent memory (episodic — show past decisions) | Emergency corridor pulsing line on map | Test dual crisis flow |
| 14 | 00:00 | Error handling, agent timeout recovery | NLP interface (optional P2) | Glassmorphism refinement, micro-animations | Record demo walkthrough notes |
| 15 | 01:00 | (Optional) Neo4j knowledge graph integration | Prompt refinement — edge cases | (Optional) Animated ambulance movement | (Optional) Raspberry Pi edge node |
| 16 | 02:00 | Resilience: handle LLM API failures gracefully | Test adversarial scenario (what if agent gives bad output?) | Responsive layout adjustments | Prepare 3 demo scenarios end-to-end |
| 17 | 03:00 | **REST if ahead of schedule** | **REST if ahead of schedule** | Color consistency check, final CSS | Draft presentation deck (4-5 slides) |
| 18 | 04:00 | Final backend testing | Final agent testing | Final UI polish | Demo rehearsal #1 (timed) |
| 19 | 05:00 | Code cleanup, comments, README | README: architecture section | README: screenshots, setup guide | Demo rehearsal #2 (refine transitions) |
| **20** | **06:00** | **⚡ CHECKPOINT 3: Complete polished system, all scenarios, override, audit** |

#### PHASE 4: Final (Hours 20-24, 6AM-10AM)

| Hour | Time | All Members |
|:----:|------|-------------|
| 20 | 06:00 | Bug fixes from checkpoint feedback |
| 21 | 07:00 | Record backup demo video (screen recording) |
| 22 | 08:00 | Demo rehearsal #3 — full 5-minute run, time it |
| 23 | 09:00 | Final code review, ensure Docker Compose works from scratch |
| **24** | **10:00** | **🔒 CODE FREEZE — Submit demo + presentation** |

---

## 14. Role Assignments (Detailed)

### Member 1: Backend Architect
**Primary:** System infrastructure, APIs, real-time communication  
**Owns:**
- Docker Compose configuration (all services)
- FastAPI application structure and all REST endpoints
- Redis connection management (CDIL + Streams)
- Socket.IO server (event routing to frontend)
- Audit chain implementation
- Human override backend logic
- Scenario injector endpoint

**Skills needed:** Python, FastAPI, Redis, Docker, WebSocket  
**Pre-hackathon prep:** Set up FastAPI project template, test Redis Streams locally

---

### Member 2: AI/Agent Engineer
**Primary:** All agent logic, LLM integration, prompt engineering  
**Owns:**
- Base DomainAgent class (LangGraph integration)
- All 4 domain agent implementations (Flood, Emergency, Traffic, Power)
- Meta-Orchestrator with conflict resolution
- LLM prompt engineering (all system prompts)
- Function calling schema for each agent's tools
- Agent memory (episodic, last N events)
- Causal inference rule engine

**Skills needed:** Python, LangGraph, Gemini API, prompt engineering  
**Pre-hackathon prep:** Test Gemini function calling, write draft prompts, test LangGraph state machines

---

### Member 3: Frontend Developer
**Primary:** Dashboard UI, map, all visual components  
**Owns:**
- React + Vite project setup
- Full CSS system (dark theme, glassmorphism, animations)
- Leaflet map with all overlays and markers
- Agent Status Panel + Reasoning Log
- Event Timeline component
- Audit Trail panel
- Override Panel + modals
- Threat Level indicator

**Skills needed:** React, CSS, Leaflet.js, Socket.IO client, Framer Motion  
**Pre-hackathon prep:** Set up React project, test Leaflet with dark tiles, build component shells

---

### Member 4: Integration Engineer + Demo Lead
**Primary:** End-to-end integration, testing, demo preparation  
**Owns:**
- Socket.IO integration testing (backend ↔ frontend)
- End-to-end flow testing (scenario → agents → dashboard)
- All scenario testing (monsoon, fire, dual crisis)
- Demo script writing and rehearsal (3 rehearsals minimum)
- Presentation deck (4-5 slides)
- Backup video recording
- (Optional) Raspberry Pi edge node setup
- README documentation

**Skills needed:** Testing, presentation, debugging, documentation  
**Pre-hackathon prep:** Write demo script, prepare presentation template, test screen recording tool

---

## 15. Risk Matrix & Fallback Strategies

### 15.1 Technical Risks

| # | Risk | Prob | Impact | Fallback Plan |
|---|------|:----:|:------:|---------------|
| R1 | **LLM API rate-limited or down** | Medium | 🔴 CRITICAL | 1. Switch to Groq (Llama 3.3) — different provider, same function calling. 2. Pre-cache agent responses for all 3 demo scenarios. 3. Have cached responses ready to inject manually. |
| R2 | **Neo4j too complex to set up** | High | 🟢 LOW | Use Redis Hash for CDIL. Functionally identical for demo. Neo4j is P2. |
| R3 | **Agent reasoning is gibberish/wrong** | Medium | 🔴 HIGH | Heavy prompt engineering. Use few-shot examples in system prompt. Add explicit "do NOT hallucinate actions" guardrails. Test all scenarios pre-checkpoint. |
| R4 | **WebSocket disconnects randomly** | Low | 🟡 MEDIUM | Auto-reconnect logic in useSocket hook. Dashboard shows last-known state. |
| R5 | **Docker build fails at venue** | Low | 🔴 CRITICAL | Pre-build ALL Docker images before arriving. Also prepare `run-local.sh` that starts all services without Docker (direct Python + npm). |
| R6 | **WiFi fails at hackathon venue** | Medium | 🔴 CRITICAL | 1. Pre-cache all map tiles (Leaflet offline plugin). 2. Pre-cache LLM responses for demo. 3. Run local Ollama with Mistral 7B as LLM fallback. 4. Record backup demo video. |
| R7 | **Not all 4 agents ready by Checkpoint 2** | Medium | 🟡 MEDIUM | Prioritize Flood + Emergency (the most dramatic pair). Traffic can be simplified to rule-based. Power can be rule-based. The agent reasoning log still works. |
| R8 | **Raspberry Pi connection fails** | High | 🟢 LOW | It's P2. Drop it entirely. Software simulation is the primary demo. |
| R9 | **Team member burns out at 3AM** | High | 🟡 MEDIUM | Front-load ALL P0 features before midnight. Hours 13-20 are polish only. Anyone can sleep 2 hours and still contribute to final phase. |
| R10 | **Agent conflict resolution doesn't work** | Medium | 🟡 MEDIUM | If Meta-Agent can't resolve automatically, show the conflict on dashboard and demo the human override resolving it. Still impressive. |

### 15.2 Nuclear Fallback — Minimum Viable Demo

If everything goes wrong and you arrive at Checkpoint 2 (11PM) with less than expected:

```
MINIMUM VIABLE NEXUS-GOV:
  ✅ 2 agents (Flood + Emergency) communicating via Redis Streams
  ✅ Redis Hash as CDIL (no Neo4j)
  ✅ Dashboard with Leaflet map (static zone colors, no animations)
  ✅ Agent reasoning log (text feed from WebSocket)
  ✅ 1 crisis scenario (monsoon flood)
  ✅ Scenario injector button

THIS STILL WINS BECAUSE:
  • It's genuine multi-agent coordination (most teams have ZERO)
  • The reasoning log shows real AI thinking cross-domain
  • The cross-domain story is intact ("flood agent alerts emergency agent")
  • The narrative carries the demo
  • The dashboard looks professional (dark theme + map)
```

### 15.3 LLM Fallback Chain

```
Primary:   Gemini 2.0 Flash (free, fast, function calling)
    ↓ if rate limited or down
Fallback:  Groq Llama 3.3 70B (free, ultra-fast, good reasoning)
    ↓ if also down
Emergency: Ollama + Mistral 7B (local, no internet needed, slower)
    ↓ if no GPU available
Nuclear:   Pre-cached responses for all 3 demo scenarios
           (hardcoded but formatted to look like live LLM output)
```

---

## 16. Pre-Hackathon Preparation (March 2-13)

### Day-by-Day Schedule

| Day | Date | Action Items |
|-----|------|-------------|
| **Day 1** | Mar 2 (Today) | ✅ Finalize concept. ✅ Create PRD (this document). |
| **Day 2** | Mar 3 | 📝 Write abstract (see ABSTRACT.md). Register on Google Form. Get API keys (Gemini, OpenWeatherMap, TomTom, NewsAPI). |
| **Day 3** | Mar 4 | 🏗️ Set up Git repo. Create Docker Compose with Redis + Mosquitto. FastAPI skeleton. React+Vite scaffold. |
| **Day 4** | Mar 5 | 🤖 Prototype base DomainAgent class. Test Gemini function calling. Test LangGraph state machine. |
| **Day 5** | Mar 6 | 🗺️ Build dashboard shell: Leaflet map with zones, dark theme CSS, component structure (empty but styled). |
| **Day 6** | Mar 7 | 🔌 Test Socket.IO integration (backend ↔ frontend). Test Redis Streams pub/sub. |
| **Day 7** | Mar 8 | 📤 **SUBMIT ABSTRACT** (deadline). Write demo script draft. |
| **Day 8** | Mar 9 | 📢 **Shortlist announcement**. If selected: celebrate + continue prep. |
| **Day 9** | Mar 10 | ✍️ Refine agent prompts. Write all scenario data. Test Hyderabad zone coordinates on map. |
| **Day 10** | Mar 11 | 📋 **Confirm attendance** (deadline). Assign final roles. Finalize build timeline. |
| **Day 11** | Mar 12 | 🐳 Pre-build ALL Docker images. Test `docker compose up` from clean state. Install Ollama + Mistral 7B as offline fallback. |
| **Day 12** | Mar 13 | 🎒 Pack: laptops (charged), chargers, extension cords, Raspberry Pi (optional), water bottles, snacks. Download map tiles offline. Final prep meeting. |
| **Day 13** | Mar 14 | 🚀 **HACKATHON DAY. Execute the plan.** |

### Pre-Registration Checklist

- [ ] Register team on Google Form: https://forms.gle/yby8D1xRLXTyrVRy7
- [ ] Submit abstract by March 8
- [ ] All 4 members registered
- [ ] Track selected: AI & Machine Learning (Agentic AI)

### API Keys to Obtain (Free)

- [ ] **Google Gemini API** — https://aistudio.google.com/app/apikey
- [ ] **Groq API** — https://console.groq.com/keys (backup LLM)
- [ ] **OpenWeatherMap** — https://openweathermap.org/api (free tier)
- [ ] **TomTom Traffic** — https://developer.tomtom.com/ (free tier)
- [ ] **NewsAPI** — https://newsapi.org/ (free developer tier)

### Software to Pre-Install

- [ ] Docker Desktop or Docker Engine + Compose
- [ ] Python 3.11+ with venv
- [ ] Node.js 18+ with npm
- [ ] Git
- [ ] VS Code with Python + React extensions
- [ ] Ollama (offline LLM backup) — https://ollama.ai
- [ ] OBS Studio (for backup video recording)

### Boilerplate to Pre-Build (Allowed)

- [ ] Docker Compose file (services defined, not application code)
- [ ] FastAPI project structure (empty routes, no business logic)
- [ ] React project structure (empty components, CSS variables defined)
- [ ] City model data file (zone coordinates, hospital names, etc. — this is data, not code)
- [ ] Leaflet map configuration (tile layer, center coordinates)
- [ ] GeoJSON file for Hyderabad zone boundaries

---

*Continued in [PRD-PART6-DEMO.md](./PRD-PART6-DEMO.md)*
