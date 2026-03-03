// ═══════════════════════════════════════════
// Simulation State Machine Hook
// Manages all dashboard state + scenario execution
// ═══════════════════════════════════════════
import { useState, useCallback, useRef, useEffect } from 'react';
import { INITIAL_AMBULANCES } from '../data/cityModel';
import {
    INITIAL_LOG_ENTRIES,
    MONSOON_FLOOD_SEQUENCE,
    INDUSTRIAL_FIRE_SEQUENCE,
    DUAL_CRISIS_SEQUENCE
} from '../data/scenarios';

function generateHash() {
    const chars = '0123456789abcdef';
    let hash = '';
    for (let i = 0; i < 8; i++) hash += chars[Math.floor(Math.random() * 16)];
    return hash;
}

function getTimestamp() {
    const now = new Date();
    return `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
}

const INITIAL_STATE = {
    threatLevel: 1,
    activeScenario: null,
    agents: {
        flood: { status: 'ACTIVE', confidence: 0.12, lastAction: 'Monitoring Hussain Sagar basin' },
        emergency: { status: 'ACTIVE', confidence: 0.08, lastAction: '6 ambulances on standby' },
        traffic: { status: 'ACTIVE', confidence: 0.05, lastAction: 'All 247 signals nominal' },
        power: { status: 'ACTIVE', confidence: 0.09, lastAction: 'Grid load nominal 847MW' },
        meta: { status: 'ACTIVE', confidence: 0.95, lastAction: 'No conflicts detected' }
    },
    zones: {
        C1: 'LOW', C2: 'LOW', C3: 'LOW', C4: 'LOW', C5: 'LOW', C6: 'LOW',
        C7: 'LOW', C8: 'LOW', C9: 'LOW', C10: 'LOW', C11: 'LOW', C12: 'LOW'
    },
    ambulances: [...INITIAL_AMBULANCES],
    reasoningLog: [],
    timeline: [],
    auditChain: [
        { blockNumber: 40, agent: 'SYS', decision: 'System initialized', hash: `${generateHash()}...${generateHash()}` },
        { blockNumber: 41, agent: 'META', decision: 'All agents deployed', hash: `${generateHash()}...${generateHash()}` }
    ],
    corridorActive: false,
    floodOverlayActive: false,
    decisionCount: 0,
    lastResponseTime: null,
    crisisFlash: false
};

export function useSimulation() {
    const [state, setState] = useState(INITIAL_STATE);
    const timersRef = useRef([]);

    // Initialize with monitoring log entries
    useEffect(() => {
        const entries = INITIAL_LOG_ENTRIES.map(e => ({
            ...e,
            timestamp: getTimestamp(),
            id: Math.random().toString(36).substr(2, 9)
        }));
        setState(prev => ({ ...prev, reasoningLog: entries }));
    }, []);

    const applyAction = useCallback((action) => {
        setState(prev => {
            const next = { ...prev };

            switch (action.type) {
                case 'SET_THREAT':
                    next.threatLevel = action.value;
                    break;

                case 'SET_AGENT':
                    next.agents = {
                        ...prev.agents,
                        [action.agent]: { ...prev.agents[action.agent], ...action.data }
                    };
                    break;

                case 'SET_ZONE':
                    next.zones = { ...prev.zones, [action.zone]: action.risk };
                    break;

                case 'ADD_LOG':
                    next.reasoningLog = [
                        ...prev.reasoningLog,
                        {
                            ...action.entry,
                            timestamp: getTimestamp(),
                            id: Math.random().toString(36).substr(2, 9),
                            isNew: true
                        }
                    ];
                    break;

                case 'ADD_TIMELINE':
                    next.timeline = [
                        ...prev.timeline,
                        {
                            ...action.event,
                            timestamp: getTimestamp(),
                            id: Math.random().toString(36).substr(2, 9)
                        }
                    ];
                    break;

                case 'ADD_AUDIT':
                    next.auditChain = [
                        ...prev.auditChain,
                        {
                            ...action.entry,
                            hash: action.entry.hash || `${generateHash()}...${generateHash()}`
                        }
                    ];
                    break;

                case 'MOVE_AMBULANCE':
                    next.ambulances = prev.ambulances.map(a =>
                        a.id === action.id ? { ...a, lat: action.lat, lng: action.lng, status: 'MOVING' } : a
                    );
                    break;

                case 'SET_CORRIDOR':
                    next.corridorActive = action.value;
                    break;

                case 'SET_FLOOD_OVERLAY':
                    next.floodOverlayActive = action.value;
                    break;

                case 'ADD_DECISIONS':
                    next.decisionCount = prev.decisionCount + action.count;
                    break;

                case 'SET_RESPONSE_TIME':
                    next.lastResponseTime = action.value;
                    break;

                default:
                    break;
            }

            return next;
        });
    }, []);

    const runSequence = useCallback((sequence, scenarioName) => {
        // Clear previous timers
        timersRef.current.forEach(t => clearTimeout(t));
        timersRef.current = [];

        setState(prev => ({
            ...prev,
            activeScenario: scenarioName,
            crisisFlash: true
        }));

        // Clear crisis flash after 400ms
        const flashTimer = setTimeout(() => {
            setState(prev => ({ ...prev, crisisFlash: false }));
        }, 400);
        timersRef.current.push(flashTimer);

        // Play alert sound
        try {
            const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioCtx.createOscillator();
            const gainNode = audioCtx.createGain();
            oscillator.connect(gainNode);
            gainNode.connect(audioCtx.destination);
            oscillator.frequency.value = 440;
            oscillator.type = 'sine';
            gainNode.gain.value = 0.08;
            oscillator.start();
            oscillator.stop(audioCtx.currentTime + 0.2);
        } catch (e) { /* Audio not available */ }

        // Schedule each step
        sequence.forEach(step => {
            const timer = setTimeout(() => {
                step.actions.forEach(action => applyAction(action));
            }, step.delay);
            timersRef.current.push(timer);
        });
    }, [applyAction]);

    const injectScenario = useCallback((scenarioId) => {
        const sequences = {
            monsoon_flood: MONSOON_FLOOD_SEQUENCE,
            industrial_fire: INDUSTRIAL_FIRE_SEQUENCE,
            dual_crisis: DUAL_CRISIS_SEQUENCE
        };

        const seq = sequences[scenarioId];
        if (seq) runSequence(seq, scenarioId);
    }, [runSequence]);

    const resetSimulation = useCallback(() => {
        timersRef.current.forEach(t => clearTimeout(t));
        timersRef.current = [];

        const entries = INITIAL_LOG_ENTRIES.map(e => ({
            ...e,
            timestamp: getTimestamp(),
            id: Math.random().toString(36).substr(2, 9)
        }));

        setState({
            ...INITIAL_STATE,
            reasoningLog: entries,
            auditChain: [
                { blockNumber: 40, agent: 'SYS', decision: 'System initialized', hash: `${generateHash()}...${generateHash()}` },
                { blockNumber: 41, agent: 'META', decision: 'All agents deployed', hash: `${generateHash()}...${generateHash()}` }
            ]
        });
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            timersRef.current.forEach(t => clearTimeout(t));
        };
    }, []);

    return {
        state,
        injectScenario,
        resetSimulation,
        applyAction
    };
}
