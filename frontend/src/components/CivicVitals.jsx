import React, { useState, useEffect } from 'react';

const VITALS = [
    { key: 'grid_load', label: 'GRID LOAD', icon: '⚡', unit: '%' },
    { key: 'traffic_flow', label: 'TRAFFIC FLOW', icon: '🚗', unit: '' },
    { key: 'flood_basins', label: 'FLOOD BASINS', icon: '🌊', unit: '' },
    { key: 'air_quality', label: 'AIR QUALITY', icon: '💨', unit: 'AQI' },
    { key: 'seismic', label: 'SEISMIC', icon: '📡', unit: '' },
    { key: 'emergency_response', label: 'ER RESPONSE', icon: '🚑', unit: 'min' },
];

function getStatusFromValue(key, value) {
    if (typeof value === 'string') {
        const upper = value.toUpperCase();
        if (['CRITICAL', 'OVERLOAD', 'FAILING', 'HIGH'].includes(upper)) return 'critical';
        if (['WARNING', 'ELEVATED', 'MEDIUM', 'CONGESTED'].includes(upper)) return 'warning';
        return 'normal';
    }
    if (typeof value === 'number') {
        if (key === 'grid_load' && value > 90) return 'critical';
        if (key === 'grid_load' && value > 70) return 'warning';
        if (key === 'air_quality' && value > 200) return 'critical';
        if (key === 'air_quality' && value > 100) return 'warning';
        return 'normal';
    }
    return 'normal';
}

function formatValue(key, value) {
    if (value === null || value === undefined) return '—';
    if (typeof value === 'number') return Math.round(value);
    return value;
}

export default function CivicVitals({ cdilSnapshot }) {
    const [vitals, setVitals] = useState({});

    useEffect(() => {
        if (!cdilSnapshot) return;

        // Extract vital metrics from CDIL snapshot
        const extracted = {};
        Object.entries(cdilSnapshot).forEach(([key, val]) => {
            if (key.includes('power:load') || key.includes('grid:load'))
                extracted.grid_load = val;
            if (key.includes('traffic:flow') || key.includes('traffic:congestion'))
                extracted.traffic_flow = val;
            if (key.includes('flood:basin') || key.includes('flood_risk'))
                extracted.flood_basins = val;
            if (key.includes('air:quality') || key.includes('air:aqi'))
                extracted.air_quality = val;
            if (key.includes('seismic'))
                extracted.seismic = val;
            if (key.includes('response_time'))
                extracted.emergency_response = val;
        });
        setVitals(prev => ({ ...prev, ...extracted }));
    }, [cdilSnapshot]);

    return (
        <div className="civic-vitals panel">
            <div className="section-title">CITY VITALS</div>
            <div className="vitals-grid">
                {VITALS.map(v => {
                    const value = vitals[v.key];
                    const status = getStatusFromValue(v.key, value);
                    return (
                        <div key={v.key} className={`vital-row vital-${status}`}>
                            <div className="vital-left">
                                <span className="vital-icon">{v.icon}</span>
                                <span className="vital-label">{v.label}</span>
                            </div>
                            <div className="vital-right">
                                <span className={`vital-value status-${status}`}>
                                    {formatValue(v.key, value)}
                                </span>
                                {v.unit && <span className="vital-unit">{v.unit}</span>}
                                <span className={`vital-dot ${status}`} />
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Pulse bar at bottom */}
            <div className="vitals-pulse">
                {[...Array(20)].map((_, i) => (
                    <div
                        key={i}
                        className="pulse-bar"
                        style={{
                            animationDelay: `${i * 0.08}s`,
                            height: `${4 + Math.sin(i * 0.7) * 8}px`,
                        }}
                    />
                ))}
            </div>
        </div>
    );
}
