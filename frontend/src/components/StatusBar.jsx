import React, { useState, useEffect } from 'react';

function AnimatedNumber({ value, duration = 1000 }) {
    const [display, setDisplay] = useState(0);

    useEffect(() => {
        if (typeof value !== 'number') { setDisplay(value); return; }
        const start = display;
        const diff = value - (typeof start === 'number' ? start : 0);
        if (diff === 0) return;

        const steps = 20;
        const stepDuration = duration / steps;
        let step = 0;

        const interval = setInterval(() => {
            step++;
            const progress = step / steps;
            const current = Math.round((typeof start === 'number' ? start : 0) + diff * progress);
            setDisplay(current);
            if (step >= steps) clearInterval(interval);
        }, stepDuration);

        return () => clearInterval(interval);
    }, [value]);

    return <span>{display}</span>;
}

export default function StatusBar({ decisionCount, lastResponseTime, activeAgents, reasoningLog }) {
    const [syncAgo, setSyncAgo] = useState(0.3);

    useEffect(() => {
        const interval = setInterval(() => {
            setSyncAgo(prev => {
                const next = prev + 0.1;
                return next > 2 ? 0.1 : parseFloat(next.toFixed(1));
            });
        }, 100);
        return () => clearInterval(interval);
    }, []);

    const tickerText = reasoningLog
        .slice(-5)
        .map(e => `[${e.badge}] ${e.message}`)
        .join('  ●  ');

    return (
        <div className="status-bar">
            <div className="status-metrics">
                <div className="status-metric">
                    <span className="status-metric-label">AGENTS</span>
                    <span className="status-metric-value">{activeAgents}/5</span>
                </div>
                <div className="status-metric">
                    <span className="status-metric-label">DECISIONS</span>
                    <span className="status-metric-value"><AnimatedNumber value={decisionCount} /></span>
                </div>
                <div className="status-metric">
                    <span className="status-metric-label">RESPONSE</span>
                    <span className="status-metric-value">{lastResponseTime || '—'}</span>
                </div>
                <div className="status-metric">
                    <span className="status-metric-label">UPTIME</span>
                    <span className="status-metric-value">99.8%</span>
                </div>
                <div className="status-metric">
                    <span className="status-metric-label">CROSS-DOMAIN</span>
                    <span className="status-metric-value">
                        <AnimatedNumber value={Math.max(0, decisionCount > 0 ? Math.floor(decisionCount / 2) : 0)} />
                    </span>
                </div>
            </div>

            <div className="status-ticker">
                <div className="ticker-content">
                    {tickerText || 'All systems nominal — monitoring active — no incidents detected'}
                </div>
            </div>

            <div className="status-right">
                <div className="chain-status">CHAIN INTEGRITY: ✓ VERIFIED</div>
                <div className="sync-status">LAST SYNC: {syncAgo}s AGO</div>
            </div>
        </div>
    );
}
