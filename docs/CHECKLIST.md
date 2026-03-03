# NEXUS-GOV — Pre-Hackathon Preparation Checklist

**Hackathon:** NeuraX 2.0 | March 14-15, 2026  
**Abstract Deadline:** March 8, 2026  
**Shortlist Announcement:** March 9, 2026  
**Confirmation Deadline:** March 11, 2026  

---

## 🔴 URGENT — This Week (March 2-8)

### Day 1-2: Registration & Abstract (March 2-3)
- [ ] Finalize team of 4 members
- [ ] Register all members on Google Form: https://forms.gle/yby8D1xRLXTyrVRy7
- [ ] Select track: **AI & Machine Learning (Agentic AI)**
- [ ] Write and review abstract (see `ABSTRACT.md`)
- [ ] Submit abstract before March 8 deadline

### Day 2-3: API Keys (March 3-4)
- [ ] **Google Gemini API key** — https://aistudio.google.com/app/apikey
- [ ] **Groq API key** (backup LLM) — https://console.groq.com/keys
- [ ] **OpenWeatherMap API key** — https://openweathermap.org/api
- [ ] **TomTom Developer API key** — https://developer.tomtom.com/
- [ ] **NewsAPI key** — https://newsapi.org/register
- [ ] Test each API — confirm free tier limits are sufficient
- [ ] Store all keys in a `.env.template` file (NEVER commit actual keys)

### Day 3-4: Software Installation (March 4-5)
All team members install:
- [ ] **Python 3.11+** with pip and venv
- [ ] **Node.js 18+** with npm
- [ ] **Docker Desktop** (or Docker Engine + Docker Compose)
- [ ] **Git** + GitHub account
- [ ] **VS Code** with extensions: Python, ESLint, Prettier, Docker
- [ ] **Redis CLI** (for testing) — `sudo apt install redis-tools` or via Docker
- [ ] **Ollama** (offline LLM fallback) — https://ollama.ai — pull `mistral:7b`
- [ ] **OBS Studio** (backup video recording) — https://obsproject.com

---

## 🟡 PREP WEEK — Scaffolding (March 4-8)

### Repository Setup (Day 3)
- [ ] Create GitHub repository: `nexus-gov`
- [ ] Initialize with README, .gitignore, LICENSE (MIT)
- [ ] Create folder structure:
```
nexus-gov/
├── backend/
│   ├── agents/          # Agent implementations
│   ├── api/             # FastAPI routes  
│   ├── core/            # CDIL, event bus, audit chain
│   ├── data/            # City model, scenarios
│   ├── requirements.txt
│   ├── Dockerfile
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── hooks/       # Custom hooks
│   │   ├── utils/       # Constants, helpers
│   │   └── data/        # GeoJSON, zone coords
│   ├── package.json
│   ├── Dockerfile
│   └── vite.config.js
├── simulator/
│   ├── Dockerfile
│   └── simulate.py
├── config/
│   └── mosquitto.conf
├── docs/                # PRD files (already created)
├── docker-compose.yml
├── .env.template
└── README.md
```

### Docker Compose (Day 3)
- [ ] Write `docker-compose.yml` with services: redis, mosquitto, backend, frontend, simulator
- [ ] Test `docker compose up` — all containers start without errors
- [ ] Verify Redis connection from Python
- [ ] Verify MQTT connection from Python

### Backend Scaffold (Day 4)
- [ ] FastAPI project with empty route structure
- [ ] Requirements.txt with all dependencies:
  ```
  fastapi==0.110.0
  uvicorn==0.27.0
  python-socketio==5.11.0
  redis==5.0.0
  langchain==0.1.0
  langgraph==0.2.0
  google-generativeai==0.4.0
  groq==0.4.0
  paho-mqtt==2.0.0
  python-dotenv==1.0.0
  ```
- [ ] Test Gemini API call from Python (simple prompt → response)
- [ ] Test Gemini function calling (define a tool → get function call back)

### Frontend Scaffold (Day 5)
- [ ] React + Vite project initialized
- [ ] CSS variables defined (colors, typography — from PRD Part 4)
- [ ] Leaflet map rendering with CartoDB dark tiles
- [ ] Hyderabad centered at correct coordinates
- [ ] Empty component files created (no logic, just structure)
- [ ] Socket.IO client installed and tested

### Agent Prototype (Day 5-6)
- [ ] Base DomainAgent class created (empty methods)
- [ ] Test LangGraph state graph with 2 nodes
- [ ] Draft system prompt for Flood Agent
- [ ] Test Flood Agent prompt with Gemini — verify reasoning quality
- [ ] Refine prompt based on output quality

### Integration Test (Day 6)
- [ ] Socket.IO: backend emits event → frontend receives and displays
- [ ] Redis pub/sub: publish message → subscriber receives
- [ ] Full path test: simulated event → backend processes → frontend displays

---

## 🟢 POST-SHORTLIST — Final Prep (March 9-13)

### Day 8: Post-Shortlist (March 9)
- [ ] Confirm shortlist selection
- [ ] Team celebration 🎉
- [ ] Review and finalize build timeline

### Day 9: Confirm Attendance (March 10-11)
- [ ] Submit final confirmation by March 11 deadline
- [ ] Confirm venue details and arrival time

### Day 10: Prompt Engineering Sprint (March 10)
- [ ] Write final system prompts for all 5 agents
- [ ] Test each agent's prompt with 3 different scenarios
- [ ] Verify function calling works correctly for each agent
- [ ] Tune prompts until reasoning quality is consistently impressive

### Day 11: Data Preparation (March 11)
- [ ] Finalize Hyderabad city model JSON
- [ ] Create GeoJSON for zone boundaries (approximate polygons)
- [ ] Write all 3 scenario injection scripts
- [ ] Verify OpenWeatherMap returns real Hyderabad weather data
- [ ] Verify TomTom returns real Hyderabad traffic data

### Day 12: Pre-Build Everything (March 12)
- [ ] Pre-build ALL Docker images (`docker compose build`)
- [ ] Download Leaflet map tiles for offline use (leaflet-offline or tile cache)
- [ ] Pull Ollama Mistral 7B model locally (`ollama pull mistral:7b`)
- [ ] Test entire stack from cold start: `docker compose up` → working dashboard
- [ ] Write `run-local.sh` fallback script (no Docker, direct Python + npm)

### Day 13: Pack & Final Prep (March 13)
Physical items:
- [ ] Laptop (fully charged) + charger + backup charger
- [ ] Extension cord / power strip
- [ ] USB mouse (more precise for demo)
- [ ] Earphones/headphones (for focus during noisy venue)
- [ ] Water bottle + energy drinks
- [ ] Snacks (protein bars, nuts)
- [ ] Notebook + pen (for quick ideas)
- [ ] (Optional) Raspberry Pi 4 + DHT22 sensor + USB cable + breadboard

Digital items:
- [ ] All code committed and pushed to GitHub
- [ ] `.env` file with all API keys ready
- [ ] Docker images pre-built and cached
- [ ] Map tiles cached offline
- [ ] Ollama model downloaded
- [ ] Demo script printed (physical copy)
- [ ] Presentation deck saved (PDF backup)
- [ ] OBS Studio configured for backup video recording

Team logistics:
- [ ] Confirm travel plan to CMR Technical Campus, Kandlakoya
- [ ] Set alarms for 7:00 AM March 14
- [ ] Sleep well the night before (March 13)
- [ ] Final team sync call — review roles, timeline, fallbacks

---

## 🏁 HACKATHON DAY (March 14)

### Morning Arrival
- [ ] Arrive by 8:30 AM (registration opens at 9:00 AM)
- [ ] Set up workstations immediately
- [ ] `docker compose up` — verify all services start
- [ ] Test API keys — verify all external APIs are reachable
- [ ] Test WiFi stability and speed
- [ ] If WiFi is bad: switch to mobile hotspot plan

### Quick Reference — The Build Order
```
10:00 AM  START → Docker + Redis + FastAPI + React scaffolds
 1:00 PM  → Flood Agent + Emergency Agent working
 5:00 PM  CHECKPOINT 1 → 2 agents + map + reasoning log
 9:00 PM  → All 4 agents + meta-orchestrator
11:00 PM  CHECKPOINT 2 → Full agent cascade + override + audit
 3:00 AM  → Polish: animations, edge cases, resilience
 6:00 AM  CHECKPOINT 3 → Complete demo-ready system
 9:00 AM  → Demo rehearsal × 3, backup video recording
10:00 AM  CODE FREEZE → Submit
12:00 PM  AWARDS
```

---

## 📞 Emergency Contacts & Links

| Resource | Link |
|----------|------|
| **Hackathon Website** | https://neurax2-0.vercel.app/ |
| **Registration Form** | https://forms.gle/yby8D1xRLXTyrVRy7 |
| **Gemini API Console** | https://aistudio.google.com/ |
| **Groq Console** | https://console.groq.com/ |
| **OpenWeatherMap** | https://openweathermap.org/api |
| **TomTom Developer** | https://developer.tomtom.com/ |
| **LangGraph Docs** | https://langchain-ai.github.io/langgraph/ |
| **Leaflet Docs** | https://leafletjs.com/reference.html |
| **Socket.IO Docs** | https://socket.io/docs/v4/ |
| **FastAPI Docs** | https://fastapi.tiangolo.com/ |
| **Venue** | CMR Technical Campus, Kandlakoya, Medchal Road, Hyderabad 501401 |
