import React from 'react';
import { CloudRain, Ambulance, Navigation, Zap, Brain } from 'lucide-react';

const AGENT_CONFIG = [
    { key: 'flood', name: 'FLOOD AGENT', icon: CloudRain, domain: 'HYDROLOGY' },
    { key: 'emergency', name: 'EMERGENCY AGENT', icon: Ambulance, domain: 'EMERGENCY MGMT' },
    { key: 'traffic', name: 'TRAFFIC AGENT', icon: Navigation, domain: 'MOBILITY' },
    { key: 'power', name: 'POWER AGENT', icon: Zap, domain: 'ENERGY GRID' },
    { key: 'meta', name: 'META-ORCHESTRATOR', icon: Brain, domain: 'COORDINATION' }
];

function AgentCard({ agent, data }) {
    const IconComp = agent.icon;
    const isMeta = agent.key === 'meta';
    const isThinking = data.status === 'REASONING';
    const statusColor = {
        ACTIVE: 'var(--accent-cyan)',
        ALERT: 'var(--accent-amber)',
        CRITICAL: 'var(--accent-red)',
        REASONING: 'var(--accent-cyan)',
        OFFLINE: 'var(--text-dim)'
    }[data.status] || 'var(--text-dim)';

    return (
        <div className={`agent-card ${isThinking ? 'reasoning' : ''} ${isMeta ? 'meta' : ''}`}>
            <div className={`agent-card-accent status-${data.status}`}
                style={isMeta ? { background: data.status === 'ACTIVE' ? 'var(--accent-gold)' : undefined } : {}}
            />
            <div className="agent-card-header">
                <IconComp
                    size={16}
                    className="agent-icon"
                    style={{ color: isMeta ? 'var(--accent-gold)' : 'var(--accent-cyan)' }}
                />
                <span className="agent-name" style={isMeta ? { color: 'var(--accent-gold)' } : {}}>
                    {agent.name}
                    {isThinking && (
                        <span className="thinking-dots">
                            <span></span><span></span><span></span>
                        </span>
                    )}
                </span>
                <span className="agent-domain">{agent.domain}</span>
            </div>
            <div className="agent-status-row">
                <span className={`status-dot ${data.status}`}></span>
                <span className="status-text" style={{ color: statusColor }}>{data.status}</span>
            </div>
            <div className="agent-last-action">{data.lastAction}</div>
            <div className="confidence-bar">
                <div className="confidence-fill" style={{ width: `${Math.round(data.confidence * 100)}%` }}></div>
            </div>
        </div>
    );
}

export default function AgentPanel({ agents }) {
    return (
        <div className="panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6, overflow: 'auto', padding: '10px 8px' }}>
            <div className="section-title">DEPLOYED AGENTS</div>
            {AGENT_CONFIG.map(agent => (
                <AgentCard key={agent.key} agent={agent} data={agents[agent.key]} />
            ))}
        </div>
    );
}
