import React, { useState, useEffect, useCallback } from 'react';
import TopBar from './components/TopBar';
import AgentPanel from './components/AgentPanel';
import CityMap from './components/CityMap';
import ReasoningLog from './components/ReasoningLog';
import EventTimeline from './components/EventTimeline';
import ScenarioPanel from './components/ScenarioPanel';
import AuditTrail from './components/AuditTrail';
import OverridePanel from './components/OverridePanel';
import StatusBar from './components/StatusBar';
import { useSocket } from './hooks/useSocket';
import { useSimulation } from './hooks/useSimulation';

const BACKEND_URL = `http://${window.location.hostname}:8000`;

export default function App() {
    const { connected, simulationMode, on, emit } = useSocket(BACKEND_URL);
    const { state, injectScenario, resetSimulation, applyAction } = useSimulation();
    const [showOverride, setShowOverride] = useState(false);
    const [autoDemo, setAutoDemo] = useState(false);
    const [showInit, setShowInit] = useState(true);

    // ── Wire backend Socket.IO events into simulation state ──
    useEffect(() => {
        // Agent status updates from backend
        on('agent_status_update', (data) => {
            const agentMap = {
                flood_agent: 'flood',
                emergency_agent: 'emergency',
                traffic_agent: 'traffic',
                power_agent: 'power',
                meta_orchestrator: 'meta'
            };
            if (data.agent && agentMap[data.agent]) {
                applyAction({
                    type: 'SET_AGENT',
                    agent: agentMap[data.agent],
                    data: {
                        status: data.status,
                        confidence: data.confidence || 0,
                        lastAction: data.last_action || ''
                    }
                });
            }
        });

        // Reasoning log from backend agents
        on('reasoning_log', (data) => {
            const badgeMap = { flood_agent: 'FLD', emergency_agent: 'EMG', traffic_agent: 'TRF', power_agent: 'PWR', meta_orchestrator: 'META', scenario_engine: 'SCN', system: 'SYS' };
            applyAction({
                type: 'ADD_LOG',
                entry: {
                    agent: data.agent || 'system',
                    badge: data.badge || badgeMap[data.agent] || 'SYS',
                    message: data.message || '',
                    severity: data.severity || 'info',
                    target: data.target || null,
                }
            });
        });

        // Threat level changes
        on('threat_level_update', (data) => {
            if (data.level !== undefined) {
                applyAction({ type: 'SET_THREAT', value: data.level });
            }
            if (data.scenario && data.status === 'STARTED') {
                applyAction({
                    type: 'ADD_TIMELINE',
                    event: { kind: 'SCENARIO_START', label: `Scenario: ${data.name}`, color: 'red' }
                });
            }
        });

        // Audit entries
        on('audit_entry', (data) => {
            applyAction({
                type: 'ADD_AUDIT',
                entry: {
                    blockNumber: data.id || 0,
                    agent: data.agent || 'SYS',
                    decision: `${data.action}: ${(data.reasoning || '').slice(0, 50)}`,
                    hash: data.hash ? `${data.prev_hash}...${data.hash}` : null
                }
            });
            applyAction({ type: 'ADD_DECISIONS', count: 1 });
        });

        // Crisis timeline events
        on('crisis_timeline_update', (data) => {
            applyAction({
                type: 'ADD_TIMELINE',
                event: {
                    kind: data.event || 'UPDATE',
                    label: data.label || '',
                    color: data.event === 'CONFLICT_RESOLVED' ? 'red' : data.event === 'HUMAN_OVERRIDE' ? 'amber' : 'cyan'
                }
            });
        });

        // CDIL updates — map zone/road/corridor states to UI
        on('cdil_update', (data) => {
            const key = data.key || '';
            const val = data.value || '';

            // Zone flood risk updates → map colors
            if (key.match(/^zone:zone_c[12]:flood_risk/)) {
                const zoneMap = { zone_c1: 'C1', zone_c2: 'C2' };
                const zid = key.split(':')[1];
                if (zoneMap[zid]) {
                    applyAction({ type: 'SET_ZONE', zone: zoneMap[zid], risk: val });
                }
            }

            // Corridor updates → map corridor overlay
            if (key.includes('corridor:') && key.includes(':status')) {
                applyAction({ type: 'SET_CORRIDOR', value: val === 'CLEARING' || val === 'CLEARED' });
            }

            // Flood overlay from water level
            if (key.includes(':water_level')) {
                try {
                    if (parseFloat(val) > 0.2) applyAction({ type: 'SET_FLOOD_OVERLAY', value: true });
                } catch (e) { }
            }

            // Response time from CDIL
            if (key === 'system:response_time') {
                applyAction({ type: 'SET_RESPONSE_TIME', value: val });
            }
        });

        // Map updates
        on('map_update', (data) => {
            if (data.subtype === 'ambulance_move') {
                // Would need lat/lng from CDIL — simplified mapping
                applyAction({
                    type: 'MOVE_AMBULANCE',
                    id: data.id,
                    lat: data.lat || 17.44,
                    lng: data.lng || 78.47,
                });
            }
        });

    }, [on, applyAction]);

    // Hide init overlay after animation
    useEffect(() => {
        const timer = setTimeout(() => setShowInit(false), 2800);
        return () => clearTimeout(timer);
    }, []);

    // ── Scenario injection — prefer backend API when connected ──
    const handleInjectScenario = useCallback(async (scenarioId) => {
        if (connected && !simulationMode) {
            // Call backend REST API
            try {
                const res = await fetch(`${BACKEND_URL}/api/v1/scenarios/inject`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ scenario: scenarioId })
                });
                const data = await res.json();
                if (data.error) {
                    console.warn('[NEXUS] Backend inject error:', data.error);
                    injectScenario(scenarioId); // Fallback to frontend sim
                }
            } catch (e) {
                console.warn('[NEXUS] Backend unreachable, using simulation:', e);
                injectScenario(scenarioId);
            }
        } else {
            injectScenario(scenarioId);
        }
    }, [connected, simulationMode, injectScenario]);

    const handleReset = useCallback(async () => {
        if (connected && !simulationMode) {
            try {
                await fetch(`${BACKEND_URL}/api/v1/scenarios/reset`, { method: 'POST' });
            } catch (e) { /* ignore */ }
        }
        resetSimulation();
    }, [connected, simulationMode, resetSimulation]);

    // Keyboard shortcuts
    useEffect(() => {
        const handler = (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') return;
            switch (e.key) {
                case '1': handleInjectScenario('monsoon_flood'); break;
                case '2': handleInjectScenario('industrial_fire'); break;
                case '3': handleInjectScenario('dual_crisis'); break;
                case 'r': case 'R': handleReset(); break;
                case 'o': case 'O': setShowOverride(prev => !prev); break;
                case 'v': case 'V': {
                    const btn = document.querySelector('.verify-btn');
                    if (btn) btn.click();
                    break;
                }
                default: break;
            }
        };
        window.addEventListener('keydown', handler);
        return () => window.removeEventListener('keydown', handler);
    }, [handleInjectScenario, handleReset]);

    // Auto-demo mode
    useEffect(() => {
        if (!autoDemo) return;
        const timer1 = setTimeout(() => handleInjectScenario('monsoon_flood'), 3000);
        const timer2 = setTimeout(() => {
            if (autoDemo) handleInjectScenario('industrial_fire');
        }, 15000);
        return () => {
            clearTimeout(timer1);
            clearTimeout(timer2);
        };
    }, [autoDemo, handleInjectScenario]);

    const handleOverrideExecute = useCallback(async (override) => {
        // Call backend override API when connected
        if (connected && !simulationMode) {
            try {
                await fetch(`${BACKEND_URL}/api/v1/override/force_action`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        action: override.command,
                        parameters: {},
                        reason: override.reason,
                        zones: override.zones || []
                    })
                });
            } catch (e) { /* fallback to local */ }
        }

        applyAction({
            type: 'ADD_LOG',
            entry: {
                agent: 'meta', badge: 'META',
                message: `HUMAN OVERRIDE EXECUTED: ${override.command} for agent ${override.agent}. Zones affected: ${override.zones.join(', ') || 'NONE'}. Justification: "${override.reason}"`,
                severity: 'critical'
            }
        });
        applyAction({
            type: 'ADD_AUDIT',
            entry: {
                blockNumber: state.auditChain.length + 40,
                agent: 'HUMAN',
                decision: `Override: ${override.command.slice(0, 30)}`,
                hash: null
            }
        });
        applyAction({
            type: 'ADD_TIMELINE',
            event: { kind: 'HUMAN_OVERRIDE', label: 'Human Override', color: 'red' }
        });
    }, [applyAction, state.auditChain.length, connected, simulationMode]);

    // Count active agents
    const activeAgents = Object.values(state.agents).filter(a => a.status !== 'OFFLINE').length;

    return (
        <>
            {/* Init overlay */}
            {showInit && (
                <div className="init-overlay">
                    <div className="init-text">SYSTEM INITIALIZING...</div>
                    <div className="init-bar">
                        <div className="init-bar-fill" />
                    </div>
                </div>
            )}

            {/* Crisis flash */}
            {state.crisisFlash && <div className="crisis-flash" />}

            {/* Demo Controls */}
            <div className="demo-controls">
                <div className="demo-toggle" onClick={() => setAutoDemo(!autoDemo)}>
                    <span className="demo-toggle-label">AUTO-DEMO</span>
                    <div className={`demo-switch ${autoDemo ? 'on' : ''}`}>
                        <div className="demo-switch-knob" />
                    </div>
                </div>
                <button className="demo-btn" onClick={handleReset}>RESET</button>
                <div className="connection-indicator">
                    <span style={{
                        width: 5, height: 5, borderRadius: '50%',
                        background: connected ? 'var(--accent-green)' : 'var(--accent-amber)',
                        display: 'inline-block'
                    }} />
                    {simulationMode ? 'SIM' : 'LIVE'}
                </div>
            </div>

            {/* Main Dashboard Grid */}
            <div className="dashboard">
                {/* Top Bar */}
                <TopBar
                    threatLevel={state.threatLevel}
                    lastResponseTime={state.lastResponseTime}
                />

                {/* Left Sidebar */}
                <div className="sidebar-area">
                    <AgentPanel agents={state.agents} />
                    <ScenarioPanel
                        activeScenario={state.activeScenario}
                        onInject={handleInjectScenario}
                        onReset={handleReset}
                    />
                </div>

                {/* Center Map */}
                <div className="map-area">
                    <CityMap
                        zones={state.zones}
                        ambulances={state.ambulances}
                        corridorActive={state.corridorActive}
                        floodOverlayActive={state.floodOverlayActive}
                    />
                </div>

                {/* Right Panel */}
                <div className="rightpanel-area">
                    <ReasoningLog entries={state.reasoningLog} />
                    <EventTimeline events={state.timeline} />
                </div>

                {/* Bottom Bar */}
                <div className="bottombar-area" style={{ display: 'flex', flexDirection: 'column' }}>
                    <div style={{ flex: 1, display: 'flex', alignItems: 'center', overflow: 'hidden' }}>
                        <AuditTrail auditChain={state.auditChain} />
                    </div>
                    <StatusBar
                        decisionCount={state.decisionCount}
                        lastResponseTime={state.lastResponseTime}
                        activeAgents={activeAgents}
                        reasoningLog={state.reasoningLog}
                    />
                </div>
            </div>

            {/* Override Panel */}
            {showOverride && (
                <OverridePanel
                    onClose={() => setShowOverride(false)}
                    onExecute={handleOverrideExecute}
                />
            )}
        </>
    );
}
