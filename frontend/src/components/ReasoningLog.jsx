import React, { useEffect, useRef, useState } from 'react';

function TypewriterText({ text, speed = 12, onComplete }) {
    const [displayed, setDisplayed] = useState('');
    const [done, setDone] = useState(false);

    useEffect(() => {
        let i = 0;
        setDisplayed('');
        setDone(false);
        const interval = setInterval(() => {
            i++;
            setDisplayed(text.slice(0, i));
            if (i >= text.length) {
                clearInterval(interval);
                setDone(true);
                if (onComplete) onComplete();
            }
        }, speed);
        return () => clearInterval(interval);
    }, [text, speed]);

    return (
        <span>
            {displayed}
            {!done && <span className="log-cursor" />}
        </span>
    );
}

export default function ReasoningLog({ entries }) {
    const scrollRef = useRef(null);
    const [animatedIds, setAnimatedIds] = useState(new Set());

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [entries]);

    const handleComplete = (id) => {
        setAnimatedIds(prev => new Set([...prev, id]));
    };

    return (
        <div className="panel" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div className="section-title">AGENT REASONING FEED</div>
            <div className="reasoning-log" ref={scrollRef}>
                {entries.map((entry, i) => {
                    const isLast = i === entries.length - 1;
                    const shouldAnimate = entry.isNew && isLast && !animatedIds.has(entry.id);

                    return (
                        <div
                            key={entry.id}
                            className="log-entry"
                            style={{ borderLeftColor: getBadgeColor(entry.badge) }}
                        >
                            <div className="log-entry-header">
                                <span className="log-timestamp">[{entry.timestamp}]</span>
                                <span className={`log-agent-badge badge-${entry.badge}`}>{entry.badge}</span>
                                {entry.target && (
                                    <>
                                        <span className="log-arrow">→</span>
                                        <span className={`log-agent-badge badge-${getTargetBadge(entry.target)}`}>
                                            {getTargetBadge(entry.target)}
                                        </span>
                                    </>
                                )}
                                {entry.severity === 'critical' && (
                                    <span style={{
                                        width: 6, height: 6, borderRadius: '50%',
                                        background: 'var(--accent-red)',
                                        animation: 'pulseDot 0.6s infinite',
                                        flexShrink: 0
                                    }} />
                                )}
                                {entry.severity === 'warning' && (
                                    <span style={{
                                        width: 6, height: 6, borderRadius: '50%',
                                        background: 'var(--accent-amber)',
                                        flexShrink: 0
                                    }} />
                                )}
                            </div>
                            <div className="log-message">
                                {shouldAnimate ? (
                                    <TypewriterText
                                        text={entry.message}
                                        speed={12}
                                        onComplete={() => handleComplete(entry.id)}
                                    />
                                ) : (
                                    entry.message
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

function getBadgeColor(badge) {
    const colors = {
        FLD: '#0066FF',
        EMG: '#FF2D55',
        TRF: '#39FF14',
        PWR: '#FF9500',
        META: '#00E5FF'
    };
    return colors[badge] || 'var(--text-dim)';
}

function getTargetBadge(target) {
    const map = {
        flood: 'FLD',
        emergency: 'EMG',
        traffic: 'TRF',
        power: 'PWR',
        meta: 'META'
    };
    return map[target] || target;
}
