import React, { useState, useEffect } from 'react';

export default function TopBar({ threatLevel, lastResponseTime }) {
    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const interval = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(interval);
    }, []);

    const formatTime = (d) => {
        return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`;
    };

    const formatDate = (d) => {
        const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
        return `${String(d.getDate()).padStart(2, '0')} ${months[d.getMonth()]} ${d.getFullYear()}`;
    };

    const getSegmentClass = (index) => {
        if (index >= threatLevel) return 'threat-segment';
        if (index < 2) return 'threat-segment active-green';
        if (index === 2) return 'threat-segment active-amber';
        return 'threat-segment active-red';
    };

    return (
        <div className="topbar topbar-area">
            <div className="topbar-left">
                <div>
                    <div className="topbar-logo">⬡ NEXUS-GOV</div>
                    <div className="topbar-subtitle">HYDERABAD INFRASTRUCTURE COMMAND</div>
                </div>
                <div className="topbar-status">
                    <span className="pulse-dot"></span>
                    ALL SYSTEMS NOMINAL
                </div>
                {lastResponseTime && (
                    <div style={{
                        fontFamily: 'var(--font-mono)',
                        fontSize: '10px',
                        color: 'var(--accent-cyan)',
                        background: 'rgba(0,229,255,0.08)',
                        padding: '2px 8px',
                        borderRadius: '2px',
                        border: '1px solid rgba(0,229,255,0.2)'
                    }}>
                        RESPONSE: {lastResponseTime}
                    </div>
                )}
            </div>

            <div className="threat-level">
                <span className="threat-label">THREAT LEVEL</span>
                <div className="threat-segments">
                    {[0, 1, 2, 3, 4].map(i => (
                        <div key={i} className={getSegmentClass(i)} style={{ animationDelay: `${i * 100}ms` }} />
                    ))}
                </div>
            </div>

            <div className="topbar-right">
                <div className="topbar-clock">
                    <div className="clock-time">{formatTime(time)}</div>
                    <div className="clock-date">{formatDate(time)}</div>
                </div>
                <span className="sim-tag">SIMULATION ACTIVE</span>
            </div>
        </div>
    );
}
