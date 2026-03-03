import React, { useRef, useEffect } from 'react';

export default function CrisisTicker({ events }) {
    const tickerRef = useRef(null);

    useEffect(() => {
        if (!tickerRef.current) return;
        // Reset animation when new events arrive
        tickerRef.current.style.animation = 'none';
        void tickerRef.current.offsetHeight; // force reflow
        tickerRef.current.style.animation = '';
    }, [events?.length]);

    if (!events || events.length === 0) return null;

    // Get severity of latest event
    const latestSeverity = events[0]?.severity || 'info';
    const bannerClass = latestSeverity === 'critical'
        ? 'crisis-ticker threat-critical'
        : latestSeverity === 'warning'
            ? 'crisis-ticker threat-warning'
            : 'crisis-ticker';

    return (
        <div className={bannerClass}>
            <div className="ticker-label">
                <span className="ticker-label-icon">🚨</span>
                <span className="ticker-label-text">LIVE</span>
            </div>
            <div className="ticker-track">
                <div className="ticker-content" ref={tickerRef}>
                    {events.slice(0, 12).map((event, i) => (
                        <span key={i} className="ticker-item">
                            {event.badge && (
                                <span className={`ticker-badge badge-${event.badge}`}>
                                    {event.badge}
                                </span>
                            )}
                            <span className="ticker-message">{event.message}</span>
                            {i < Math.min(events.length, 12) - 1 && (
                                <span className="ticker-separator">◆</span>
                            )}
                        </span>
                    ))}
                </div>
            </div>
        </div>
    );
}
