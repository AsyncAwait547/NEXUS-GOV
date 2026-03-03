import React from 'react';

const EVENT_COLORS = {
    SCENARIO_START: 'amber',
    AGENT_ACTIVATED: 'green',
    CROSS_DOMAIN_ALERT: 'red',
    CORRIDOR_CLEARED: 'green',
    POWER_REROUTED: 'amber',
    AMBULANCE_DEPLOYED: 'cyan',
    CONFLICT_DETECTED: 'red',
    CONFLICT_RESOLVED: 'cyan',
    HUMAN_OVERRIDE: 'red',
    AUDIT_VERIFIED: 'cyan'
};

export default function EventTimeline({ events }) {
    return (
        <div className="panel" style={{ overflow: 'hidden' }}>
            <div className="section-title">INCIDENT TIMELINE</div>
            <div className="event-timeline">
                <div className="timeline-track">
                    <div className="timeline-line" />
                    {events.map((event, i) => {
                        const color = event.color || EVENT_COLORS[event.kind] || 'cyan';
                        return (
                            <div
                                key={event.id || i}
                                className="timeline-node"
                                style={{ animationDelay: `${i * 50}ms` }}
                            >
                                {i % 2 === 0 && (
                                    <>
                                        <div className="timeline-label">{event.label}</div>
                                        <div className="timeline-time">{event.timestamp}</div>
                                    </>
                                )}
                                <div className={`timeline-dot ${color}`} />
                                {i % 2 !== 0 && (
                                    <>
                                        <div className="timeline-time">{event.timestamp}</div>
                                        <div className="timeline-label">{event.label}</div>
                                    </>
                                )}
                            </div>
                        );
                    })}
                    {events.length > 0 && (
                        <div className="timeline-now">
                            <div className="now-label">NOW</div>
                            <div className="now-line" />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
