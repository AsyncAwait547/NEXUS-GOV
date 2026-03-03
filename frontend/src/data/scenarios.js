// ═══════════════════════════════════════════
// NEXUS-GOV Scenario Definitions
// Timed event sequences for simulation
// ═══════════════════════════════════════════

export const INITIAL_LOG_ENTRIES = [
    {
        agent: 'flood', badge: 'FLD', timestamp: null,
        message: 'Monitoring Hussain Sagar basin. Rainfall: 12mm/hr. Normal range.',
        severity: 'info'
    },
    {
        agent: 'power', badge: 'PWR', timestamp: null,
        message: 'Grid load: 847MW. LB Nagar sub: 78% capacity. Stable.',
        severity: 'info'
    },
    {
        agent: 'traffic', badge: 'TRF', timestamp: null,
        message: 'All 247 signals nominal. Average flow: 1,240 vehicles/hr.',
        severity: 'info'
    },
    {
        agent: 'emergency', badge: 'EMG', timestamp: null,
        message: '6 ambulances on standby. NIMS ER: 23% capacity.',
        severity: 'info'
    },
    {
        agent: 'meta', badge: 'META', timestamp: null,
        message: 'All domain agents nominal. No conflicts detected.',
        severity: 'info'
    }
];

export const MONSOON_FLOOD_SEQUENCE = [
    {
        delay: 0,
        actions: [
            { type: 'SET_THREAT', value: 2 },
            { type: 'SET_AGENT', agent: 'flood', data: { status: 'REASONING', confidence: 0.72 } },
            {
                type: 'ADD_LOG',
                entry: {
                    agent: 'flood', badge: 'FLD',
                    message: '⚠ ANOMALY DETECTED: Hussain Sagar basin. Rainfall sensor #HS-07: 95mm/hr. Threshold: 65mm/hr. EXCEEDED.',
                    severity: 'warning'
                }
            },
            { type: 'ADD_TIMELINE', event: { kind: 'SCENARIO_START', label: 'Monsoon Detected', color: 'amber' } }
        ]
    },
    {
        delay: 1500,
        actions: [
            { type: 'SET_ZONE', zone: 'C1', risk: 'HIGH' },
            { type: 'SET_ZONE', zone: 'C2', risk: 'MEDIUM' },
            { type: 'SET_FLOOD_OVERLAY', value: true },
            { type: 'SET_THREAT', value: 3 },
            { type: 'SET_AGENT', agent: 'flood', data: { status: 'ALERT', confidence: 0.94, lastAction: 'FLOOD RISK: CRITICAL for C1, HIGH for C2' } },
            {
                type: 'ADD_LOG',
                entry: {
                    agent: 'flood', badge: 'FLD',
                    message: 'Historical analysis: 95mm/hr sustained >1hr = basin overflow. Setting FLOOD RISK: CRITICAL for C1, HIGH for C2. Broadcasting to all agents.',
                    severity: 'critical'
                }
            }
        ]
    },
    {
        delay: 2500,
        actions: [
            { type: 'SET_AGENT', agent: 'emergency', data: { status: 'REASONING', confidence: 0.65 } },
            {
                type: 'ADD_LOG',
                entry: {
                    agent: 'flood', badge: 'FLD',
                    message: '→ [EMERGENCY AGENT] CRITICAL ALERT: Flood imminent C1/C2. Pre-position ambulances outside flood zones. Estimated onset: 23 minutes.',
                    severity: 'critical',
                    target: 'emergency'
                }
            },
            { type: 'ADD_TIMELINE', event: { kind: 'CROSS_DOMAIN_ALERT', label: 'Flood→Emergency', color: 'red' } }
        ]
    },
    {
        delay: 3800,
        actions: [
            { type: 'MOVE_AMBULANCE', id: 'AMB-3', lat: 17.42, lng: 78.50 },
            { type: 'MOVE_AMBULANCE', id: 'AMB-4', lat: 17.35, lng: 78.51 },
            { type: 'SET_AGENT', agent: 'emergency', data: { status: 'ALERT', confidence: 0.91, lastAction: 'Pre-positioning 4 ambulances' } },
            {
                type: 'ADD_LOG',
                entry: {
                    agent: 'emergency', badge: 'EMG',
                    message: 'Repositioning: AMB-3 → Ameerpet staging. AMB-4 → Dilsukhnagar staging. NIMS Hospital notified: prepare flood casualties. Care Hospital: standby alert.',
                    severity: 'warning'
                }
            },
            { type: 'ADD_TIMELINE', event: { kind: 'AMBULANCE_DEPLOYED', label: 'Units Repositioned', color: 'cyan' } }
        ]
    },
    {
        delay: 5000,
        actions: [
            { type: 'SET_CORRIDOR', value: true },
            { type: 'SET_AGENT', agent: 'traffic', data: { status: 'ALERT', confidence: 0.88, lastAction: 'Corridor cleared: Khairatabad→Begumpet' } },
            {
                type: 'ADD_LOG',
                entry: {
                    agent: 'traffic', badge: 'TRF',
                    message: 'Reading CDIL: C1+C2 flood zones. Proactive corridor: Khairatabad→Begumpet. Setting 18 signals to PRIORITY GREEN. Route ETA improvement: 47min → 8min.',
                    severity: 'warning'
                }
            },
            { type: 'ADD_TIMELINE', event: { kind: 'CORRIDOR_CLEARED', label: 'Emergency Corridor', color: 'green' } }
        ]
    },
    {
        delay: 6500,
        actions: [
            { type: 'SET_ZONE', zone: 'C5', risk: 'MEDIUM' },
            { type: 'SET_AGENT', agent: 'power', data: { status: 'ALERT', confidence: 0.86, lastAction: 'Rerouting 120MW away from C5' } },
            {
                type: 'ADD_LOG',
                entry: {
                    agent: 'power', badge: 'PWR',
                    message: 'LB Nagar substation in projected flood zone C5. Preemptive reroute: 120MW → Kukatpally sub + Secunderabad sub. Hospital backup power: ACTIVATED. Cascade protection: ENABLED.',
                    severity: 'warning'
                }
            },
            { type: 'ADD_TIMELINE', event: { kind: 'POWER_REROUTED', label: 'Grid Rerouted', color: 'amber' } }
        ]
    },
    {
        delay: 8000,
        actions: [
            { type: 'SET_THREAT', value: 4 },
            { type: 'SET_AGENT', agent: 'meta', data: { status: 'ALERT', confidence: 0.97, lastAction: '4-domain cascade coordinated' } },
            { type: 'ADD_DECISIONS', count: 14 },
            { type: 'SET_RESPONSE_TIME', value: '8.2s' },
            {
                type: 'ADD_LOG',
                entry: {
                    agent: 'meta', badge: 'META',
                    message: '4-domain cascade complete. Flood(0.94)→Emergency(0.91)→Traffic(0.88)→Power(0.86). No conflicts detected. Coordinated response time: 8.2 seconds. All priority functions protected.',
                    severity: 'info'
                }
            },
            {
                type: 'ADD_AUDIT',
                entry: {
                    blockNumber: 42,
                    agent: 'META',
                    decision: '4-domain cascade coordinated',
                    hash: 'a3f7c8d2...9d2e4b1a'
                }
            },
            { type: 'ADD_TIMELINE', event: { kind: 'AUDIT_VERIFIED', label: 'Chain Verified', color: 'cyan' } }
        ]
    }
];

export const INDUSTRIAL_FIRE_SEQUENCE = [
    {
        delay: 0,
        actions: [
            { type: 'SET_ZONE', zone: 'C6', risk: 'CRITICAL' },
            { type: 'SET_THREAT', value: 4 },
            { type: 'SET_AGENT', agent: 'emergency', data: { status: 'REASONING', confidence: 0.70 } },
            {
                type: 'ADD_LOG',
                entry: {
                    agent: 'emergency', badge: 'EMG',
                    message: '🔥 INDUSTRIAL FIRE detected: Malkajgiri Chemical Plant. Zone C6 CRITICAL. Evacuating 500m radius. Multiple casualties reported.',
                    severity: 'critical'
                }
            },
            { type: 'ADD_TIMELINE', event: { kind: 'SCENARIO_START', label: 'Fire Detected', color: 'red' } }
        ]
    },
    {
        delay: 1800,
        actions: [
            {
                type: 'ADD_LOG',
                entry: {
                    agent: 'emergency', badge: 'EMG',
                    message: '→ [META-ORCH] RESOURCE CONFLICT: Need AMB-3, AMB-4 for fire zone C6, but units assigned to flood zones C1/C2. Requesting conflict resolution.',
                    severity: 'critical',
                    target: 'meta'
                }
            },
            { type: 'SET_AGENT', agent: 'meta', data: { status: 'REASONING', confidence: 0.82 } },
            { type: 'ADD_TIMELINE', event: { kind: 'CONFLICT_DETECTED', label: 'Resource Conflict', color: 'red' } }
        ]
    },
    {
        delay: 3200,
        actions: [
            {
                type: 'ADD_LOG',
                entry: {
                    agent: 'meta', badge: 'META',
                    message: 'CONFLICT RESOLUTION: FLOOD_SEVERITY(8) > FIRE_SEVERITY(7). Maintaining 3 units at flood zones. Diverting AMB-5, AMB-6 to fire zone C6. Decision hash: b7c2d9e3.',
                    severity: 'warning'
                }
            },
            { type: 'MOVE_AMBULANCE', id: 'AMB-5', lat: 17.456, lng: 78.527 },
            { type: 'MOVE_AMBULANCE', id: 'AMB-6', lat: 17.460, lng: 78.530 },
            { type: 'SET_AGENT', agent: 'emergency', data: { status: 'ALERT', confidence: 0.89, lastAction: 'AMB-5, AMB-6 → fire zone C6' } },
            { type: 'SET_AGENT', agent: 'meta', data: { status: 'ALERT', confidence: 0.95, lastAction: 'Conflict resolved: priority flood' } },
            { type: 'ADD_TIMELINE', event: { kind: 'CONFLICT_RESOLVED', label: 'Conflict Resolved', color: 'cyan' } },
            { type: 'ADD_DECISIONS', count: 6 },
            {
                type: 'ADD_AUDIT',
                entry: {
                    blockNumber: 43,
                    agent: 'META',
                    decision: 'Conflict: flood > fire priority',
                    hash: 'b7c2d9e3...f1a4c8b2'
                }
            }
        ]
    },
    {
        delay: 5000,
        actions: [
            { type: 'SET_THREAT', value: 5 },
            { type: 'SET_AGENT', agent: 'power', data: { status: 'ALERT', confidence: 0.83, lastAction: 'Isolating C6 grid segment' } },
            {
                type: 'ADD_LOG',
                entry: {
                    agent: 'power', badge: 'PWR',
                    message: 'Chemical plant fire risk to C6 grid segment. Isolating feeder lines. Rerouting 85MW to adjacent segments. Fire department power needs: PRIORITIZED.',
                    severity: 'warning'
                }
            },
            { type: 'ADD_TIMELINE', event: { kind: 'POWER_REROUTED', label: 'C6 Grid Isolated', color: 'amber' } }
        ]
    }
];

export const DUAL_CRISIS_SEQUENCE = [
    ...MONSOON_FLOOD_SEQUENCE,
    ...INDUSTRIAL_FIRE_SEQUENCE.map(step => ({
        ...step,
        delay: step.delay + 9000
    }))
];
