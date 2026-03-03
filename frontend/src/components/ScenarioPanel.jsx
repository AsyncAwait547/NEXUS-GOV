import React, { useState, useCallback } from 'react';

const SCENARIOS = [
    {
        id: 'monsoon_flood',
        name: '🌧 MONSOON FLOOD',
        subtitle: 'Hussain Sagar Basin Overflow',
        accentColor: '#0066FF'
    },
    {
        id: 'industrial_fire',
        name: '🔥 INDUSTRIAL FIRE',
        subtitle: 'Malkajgiri Chemical Plant',
        accentColor: '#FF2D55'
    },
    {
        id: 'dual_crisis',
        name: '⚡ DUAL CRISIS',
        subtitle: 'Parallel Event Response',
        accentColor: '#9B59B6'
    }
];

export default function ScenarioPanel({ activeScenario, onInject, onReset }) {
    const [injecting, setInjecting] = useState(null);
    const [resetConfirm, setResetConfirm] = useState(false);

    const handleInject = useCallback((scenarioId) => {
        if (activeScenario) return;
        setInjecting(scenarioId);

        setTimeout(() => {
            onInject(scenarioId);
            setInjecting(null);
        }, 800);
    }, [activeScenario, onInject]);

    const handleReset = useCallback(() => {
        if (!resetConfirm) {
            setResetConfirm(true);
            setTimeout(() => setResetConfirm(false), 3000);
            return;
        }
        setResetConfirm(false);
        onReset();
    }, [resetConfirm, onReset]);

    return (
        <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: '10px 8px' }}>
            <div className="section-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                SCENARIO INJECTION
                <span style={{
                    fontSize: 8,
                    color: 'var(--accent-amber)',
                    border: '1px solid rgba(255,149,0,0.3)',
                    padding: '1px 6px',
                    borderRadius: 2,
                    letterSpacing: 1
                }}>⚠ SIMULATION</span>
            </div>

            {SCENARIOS.map(scenario => {
                const isActive = activeScenario === scenario.id;
                const isInjecting = injecting === scenario.id;
                const isDisabled = activeScenario && !isActive;

                return (
                    <button
                        key={scenario.id}
                        className={`scenario-btn ${isActive ? 'active' : ''} ${isInjecting ? 'injecting' : ''}`}
                        onClick={() => handleInject(scenario.id)}
                        disabled={isDisabled}
                        style={{
                            opacity: isDisabled ? 0.35 : 1,
                            borderColor: isActive ? 'var(--accent-green)' : undefined
                        }}
                        onMouseEnter={(e) => {
                            if (!isDisabled) {
                                e.currentTarget.style.boxShadow = `0 0 16px ${scenario.accentColor}33`;
                            }
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.boxShadow = 'none';
                        }}
                    >
                        <div className="scenario-btn-accent" style={{ background: scenario.accentColor }} />
                        <div className="scenario-btn-content">
                            <div className="scenario-btn-name">
                                {isInjecting ? 'INJECTING...' : isActive ? '✓ SCENARIO ACTIVE' : scenario.name}
                            </div>
                            <div className="scenario-btn-sub">{scenario.subtitle}</div>
                        </div>
                    </button>
                );
            })}

            <button
                className="reset-btn"
                onClick={handleReset}
                style={{
                    background: resetConfirm ? 'rgba(255,45,85,0.12)' : undefined,
                    borderColor: resetConfirm ? 'var(--accent-red)' : undefined
                }}
            >
                {resetConfirm ? '⚠ CONFIRM RESET?' : 'RESET SIMULATION'}
            </button>
        </div>
    );
}
