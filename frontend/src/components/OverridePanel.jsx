import React, { useState } from 'react';

const AGENTS = [
    { id: 'flood', name: 'Flood Agent' },
    { id: 'emergency', name: 'Emergency Agent' },
    { id: 'traffic', name: 'Traffic Agent' },
    { id: 'power', name: 'Power Agent' },
    { id: 'meta', name: 'Meta-Orchestrator' }
];

const ZONES = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12'];

export default function OverridePanel({ onClose, onExecute }) {
    const [selectedAgent, setSelectedAgent] = useState('flood');
    const [command, setCommand] = useState('');
    const [selectedZones, setSelectedZones] = useState([]);
    const [reason, setReason] = useState('');
    const [executed, setExecuted] = useState(false);

    const toggleZone = (zone) => {
        setSelectedZones(prev =>
            prev.includes(zone) ? prev.filter(z => z !== zone) : [...prev, zone]
        );
    };

    const handleExecute = () => {
        if (!command) return;
        onExecute({
            agent: selectedAgent,
            command,
            zones: selectedZones,
            reason,
            timestamp: new Date().toISOString()
        });
        setExecuted(true);
        setTimeout(() => {
            setExecuted(false);
            onClose();
        }, 2000);
    };

    return (
        <>
            <div className="override-overlay" onClick={onClose} />
            <div className="override-panel">
                <div className="override-title">
                    <span style={{
                        width: 8, height: 8, borderRadius: '50%',
                        background: 'var(--accent-red)',
                        animation: 'pulseDot 0.8s infinite'
                    }} />
                    HUMAN OVERRIDE ACTIVE
                </div>

                {executed ? (
                    <div style={{
                        flex: 1, display: 'flex', flexDirection: 'column',
                        alignItems: 'center', justifyContent: 'center', gap: 12
                    }}>
                        <div style={{
                            fontFamily: 'var(--font-display)',
                            fontSize: 16,
                            color: 'var(--accent-green)',
                            textShadow: '0 0 20px rgba(57,255,20,0.4)'
                        }}>
                            ✓ OVERRIDE EXECUTED
                        </div>
                        <div style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: 10,
                            color: 'var(--text-dim)'
                        }}>
                            Decision logged to audit chain
                        </div>
                    </div>
                ) : (
                    <>
                        <div className="override-field">
                            <label className="override-label">TARGET AGENT</label>
                            <select
                                className="override-select"
                                value={selectedAgent}
                                onChange={e => setSelectedAgent(e.target.value)}
                            >
                                {AGENTS.map(a => (
                                    <option key={a.id} value={a.id}>{a.name}</option>
                                ))}
                            </select>
                        </div>

                        <div className="override-field">
                            <label className="override-label">OVERRIDE COMMAND</label>
                            <textarea
                                className="override-textarea"
                                placeholder="Enter override command..."
                                value={command}
                                onChange={e => setCommand(e.target.value)}
                            />
                        </div>

                        <div className="override-field">
                            <label className="override-label">AFFECTED ZONES</label>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                                {ZONES.map(z => (
                                    <button
                                        key={z}
                                        onClick={() => toggleZone(z)}
                                        style={{
                                            background: selectedZones.includes(z) ? 'rgba(0,229,255,0.15)' : 'var(--bg-card)',
                                            border: `1px solid ${selectedZones.includes(z) ? 'var(--accent-cyan)' : 'var(--border-dim)'}`,
                                            color: selectedZones.includes(z) ? 'var(--accent-cyan)' : 'var(--text-dim)',
                                            padding: '4px 8px',
                                            borderRadius: 2,
                                            fontFamily: 'var(--font-mono)',
                                            fontSize: 10,
                                            cursor: 'pointer',
                                            transition: 'all 0.2s ease'
                                        }}
                                    >
                                        {z}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="override-field">
                            <label className="override-label">JUSTIFICATION</label>
                            <input
                                className="override-input"
                                placeholder="Reason for override..."
                                value={reason}
                                onChange={e => setReason(e.target.value)}
                            />
                        </div>

                        <div className="override-actions">
                            <button className="btn-execute" onClick={handleExecute}>
                                EXECUTE OVERRIDE
                            </button>
                            <button className="btn-cancel" onClick={onClose}>
                                CANCEL
                            </button>
                        </div>
                    </>
                )}
            </div>
        </>
    );
}
