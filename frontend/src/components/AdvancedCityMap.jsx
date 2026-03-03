import React, { useMemo, useState, useCallback, useEffect } from 'react';
import DeckGL from '@deck.gl/react';
import { Map } from 'react-map-gl/maplibre';
import { PolygonLayer, PathLayer, IconLayer, ArcLayer, ScatterplotLayer, TextLayer } from '@deck.gl/layers';
import 'maplibre-gl/dist/maplibre-gl.css';
import {
    MAP_CONFIG, CITY_ZONES, HOSPITALS, SUBSTATIONS,
    EMERGENCY_CORRIDOR, RISK_COLORS
} from '../data/cityModel';

const INITIAL_VIEW_STATE = {
    longitude: 78.486,
    latitude: 17.385,
    zoom: 11.8,
    pitch: 45,
    bearing: -15,
    transitionDuration: 1000,
};

// Risk level → RGBA color
const RISK_RGBA = {
    LOW: [57, 255, 20, 25],
    MEDIUM: [255, 149, 0, 50],
    HIGH: [255, 45, 85, 80],
    CRITICAL: [255, 45, 85, 140],
};

const RISK_STROKE_RGBA = {
    LOW: [57, 255, 20, 80],
    MEDIUM: [255, 149, 0, 120],
    HIGH: [255, 45, 85, 160],
    CRITICAL: [255, 45, 85, 220],
};

const RISK_ELEVATION = {
    LOW: 0,
    MEDIUM: 80,
    HIGH: 200,
    CRITICAL: 400,
};

// Convert Leaflet [lat, lng] polygon to Deck.gl [lng, lat] format
function convertPolygon(polygon) {
    const coords = polygon.map(([lat, lng]) => [lng, lat]);
    // Close the polygon
    if (coords.length > 0) {
        const first = coords[0];
        const last = coords[coords.length - 1];
        if (first[0] !== last[0] || first[1] !== last[1]) {
            coords.push([...first]);
        }
    }
    return coords;
}

export default function AdvancedCityMap({ zones, ambulances, corridorActive, floodOverlayActive }) {
    const [hoverInfo, setHoverInfo] = useState(null);
    const [pulsePhase, setPulsePhase] = useState(0);
    const [dashOffset, setDashOffset] = useState(0);

    // Animate pulse + corridor dash
    useEffect(() => {
        let frame;
        let start = performance.now();
        const animate = (now) => {
            const elapsed = (now - start) / 1000;
            setPulsePhase(elapsed);
            setDashOffset(Math.floor(elapsed * 12) % 24);
            frame = requestAnimationFrame(animate);
        };
        frame = requestAnimationFrame(animate);
        return () => cancelAnimationFrame(frame);
    }, []);

    // ── Zone data for Deck.gl ──
    const zoneData = useMemo(() => {
        return Object.entries(CITY_ZONES).map(([id, zone]) => {
            const risk = zones[id] || 'LOW';
            return {
                id,
                name: zone.name,
                risk,
                polygon: convertPolygon(zone.polygon),
                center: [zone.center[1], zone.center[0]], // [lng, lat]
            };
        });
    }, [zones]);

    // ── 1. Zone Polygons (3D extruded) ──
    const zoneLayer = new PolygonLayer({
        id: 'city-zones',
        data: zoneData,
        getPolygon: d => d.polygon,
        getFillColor: d => RISK_RGBA[d.risk] || RISK_RGBA.LOW,
        getLineColor: d => RISK_STROKE_RGBA[d.risk] || RISK_STROKE_RGBA.LOW,
        getLineWidth: d => d.risk === 'CRITICAL' ? 3 : d.risk === 'HIGH' ? 2 : 1,
        lineWidthUnits: 'pixels',
        extruded: true,
        getElevation: d => RISK_ELEVATION[d.risk] || 0,
        elevationScale: 1,
        material: {
            ambient: 0.6,
            diffuse: 0.8,
            shininess: 40,
        },
        pickable: true,
        autoHighlight: true,
        highlightColor: [0, 229, 255, 60],
        transitions: {
            getElevation: { duration: 800, easing: t => t * (2 - t) },
            getFillColor: { duration: 600 },
        },
        onHover: (info) => setHoverInfo(info.object ? info : null),
    });

    // ── 2. Zone Labels ──
    const zoneLabelLayer = new TextLayer({
        id: 'zone-labels',
        data: zoneData,
        getPosition: d => d.center,
        getText: d => d.id,
        getSize: 14,
        getColor: [228, 244, 248, 200],
        fontFamily: 'Rajdhani, sans-serif',
        fontWeight: 700,
        getTextAnchor: 'middle',
        getAlignmentBaseline: 'center',
        billboard: false,
        getPixelOffset: [0, 0],
    });

    // ── 3. Hospital Icons ──
    const hospitalData = useMemo(() =>
        HOSPITALS.map(h => ({ ...h, position: [h.lng, h.lat] })), []
    );

    const hospitalLayer = new ScatterplotLayer({
        id: 'hospitals',
        data: hospitalData,
        getPosition: d => d.position,
        getFillColor: [255, 45, 85, 200],
        getLineColor: [255, 45, 85, 255],
        getRadius: 120,
        lineWidthMinPixels: 2,
        stroked: true,
        filled: true,
        pickable: true,
        radiusMinPixels: 5,
        radiusMaxPixels: 12,
    });

    const hospitalLabelLayer = new TextLayer({
        id: 'hospital-labels',
        data: hospitalData,
        getPosition: d => d.position,
        getText: d => `🏥 ${d.name}`,
        getSize: 11,
        getColor: [255, 100, 130, 220],
        fontFamily: 'Rajdhani, sans-serif',
        getTextAnchor: 'start',
        getPixelOffset: [12, 0],
        billboard: true,
        characterSet: [...Array.from({ length: 95 }, (_, i) => String.fromCharCode(i + 32)), '🏥'],
    });

    // ── 4. Substation Icons + Power Grid Arcs ──
    const substationData = useMemo(() =>
        SUBSTATIONS.map(s => ({ ...s, position: [s.lng, s.lat] })), []
    );

    const substationLayer = new ScatterplotLayer({
        id: 'substations',
        data: substationData,
        getPosition: d => d.position,
        getFillColor: [255, 149, 0, 200],
        getLineColor: [255, 149, 0, 255],
        getRadius: 100,
        lineWidthMinPixels: 2,
        stroked: true,
        filled: true,
        pickable: true,
        radiusMinPixels: 5,
        radiusMaxPixels: 10,
    });

    const substationLabelLayer = new TextLayer({
        id: 'substation-labels',
        data: substationData,
        getPosition: d => d.position,
        getText: d => `⚡ ${d.name}`,
        getSize: 10,
        getColor: [255, 180, 60, 200],
        fontFamily: 'Rajdhani, sans-serif',
        getTextAnchor: 'start',
        getPixelOffset: [12, 0],
        billboard: true,
        characterSet: [...Array.from({ length: 95 }, (_, i) => String.fromCharCode(i + 32)), '⚡'],
    });

    // Power grid arcs between substations
    const powerArcData = useMemo(() => {
        if (substationData.length < 2) return [];
        const arcs = [];
        for (let i = 0; i < substationData.length - 1; i++) {
            arcs.push({
                source: substationData[i].position,
                target: substationData[i + 1].position,
                name: `${substationData[i].name} → ${substationData[i + 1].name}`,
            });
        }
        // Connect last to first for ring topology
        arcs.push({
            source: substationData[substationData.length - 1].position,
            target: substationData[0].position,
            name: `${substationData[substationData.length - 1].name} → ${substationData[0].name}`,
        });
        return arcs;
    }, [substationData]);

    const powerArcLayer = new ArcLayer({
        id: 'power-grid',
        data: powerArcData,
        getSourcePosition: d => d.source,
        getTargetPosition: d => d.target,
        getSourceColor: [0, 255, 100, 160],
        getTargetColor: [255, 165, 0, 160],
        getWidth: 2,
        getHeight: 0.3,
        greatCircle: false,
        pickable: true,
    });

    // ── 5. Ambulance Layer ──
    const ambulanceData = useMemo(() =>
        ambulances.map(a => ({
            ...a,
            position: [a.lng, a.lat],
            color: a.status === 'MOVING' ? [255, 45, 85, 255] : [0, 229, 255, 200],
        })), [ambulances]
    );

    const ambulanceLayer = new ScatterplotLayer({
        id: 'ambulances',
        data: ambulanceData,
        getPosition: d => d.position,
        getFillColor: d => d.color,
        getRadius: 80,
        filled: true,
        stroked: true,
        getLineColor: [255, 255, 255, 180],
        lineWidthMinPixels: 1,
        pickable: true,
        radiusMinPixels: 4,
        radiusMaxPixels: 8,
        transitions: {
            getPosition: { duration: 2000, easing: t => t * (2 - t) },
        },
    });

    const ambulanceLabelLayer = new TextLayer({
        id: 'ambulance-labels',
        data: ambulanceData,
        getPosition: d => d.position,
        getText: d => `🚑 ${d.id}`,
        getSize: 10,
        getColor: d => d.status === 'MOVING' ? [255, 100, 130, 255] : [200, 200, 200, 180],
        fontFamily: 'JetBrains Mono, monospace',
        fontWeight: 700,
        getTextAnchor: 'start',
        getPixelOffset: [10, 0],
        billboard: true,
        characterSet: [...Array.from({ length: 95 }, (_, i) => String.fromCharCode(i + 32)), '🚑'],
    });

    // ── 6. Emergency Corridor (animated path) ──
    const corridorData = useMemo(() => {
        if (!corridorActive) return [];
        return [{
            path: EMERGENCY_CORRIDOR.map(([lat, lng]) => [lng, lat]),
            name: 'Emergency Corridor',
        }];
    }, [corridorActive]);

    const corridorLayer = new PathLayer({
        id: 'emergency-corridor',
        data: corridorData,
        getPath: d => d.path,
        getColor: [0, 229, 255, 200],
        getWidth: 8,
        widthUnits: 'pixels',
        pickable: true,
        getDashArray: [12, 8],
        dashJustified: true,
        dashGapPickable: true,
        extensions: [],
    });

    const corridorGlowLayer = new PathLayer({
        id: 'corridor-glow',
        data: corridorData,
        getPath: d => d.path,
        getColor: [0, 229, 255, 40],
        getWidth: 30,
        widthUnits: 'pixels',
    });

    // ── 7. Flood Pulse Rings ──
    const floodPulseData = useMemo(() => {
        if (!floodOverlayActive) return [];
        const center = CITY_ZONES.C1.center;
        const centerPos = [center[1], center[0]];
        return [0, 1, 2].map(i => ({
            position: centerPos,
            ring: i,
        }));
    }, [floodOverlayActive]);

    const floodPulseLayer = new ScatterplotLayer({
        id: 'flood-pulse',
        data: floodPulseData,
        getPosition: d => d.position,
        getFillColor: [0, 100, 255, 0],
        getLineColor: [0, 130, 255, Math.max(0, 120 - Math.floor(pulsePhase * 40) % 120)],
        getRadius: d => 800 + d.ring * 400 + ((pulsePhase * 300 + d.ring * 200) % 600),
        stroked: true,
        filled: false,
        lineWidthMinPixels: 2,
        lineWidthMaxPixels: 3,
        radiusMinPixels: 15,
        parameters: { depthTest: false },
    });

    // ── Assemble Layers ──
    const layers = [
        zoneLayer,
        zoneLabelLayer,
        powerArcLayer,
        hospitalLayer,
        hospitalLabelLayer,
        substationLayer,
        substationLabelLayer,
        corridorGlowLayer,
        corridorLayer,
        floodPulseLayer,
        ambulanceLayer,
        ambulanceLabelLayer,
    ];

    // ── Tooltip ──
    const renderTooltip = () => {
        if (!hoverInfo || !hoverInfo.object) return null;
        const { x, y, object } = hoverInfo;
        return (
            <div className="deckgl-tooltip" style={{
                position: 'absolute',
                left: x + 12,
                top: y - 12,
                pointerEvents: 'none',
                zIndex: 10,
            }}>
                <div className="tooltip-title">{object.id || object.name}</div>
                {object.name && <div className="tooltip-sub">{object.name}</div>}
                {object.risk && (
                    <div className={`tooltip-risk risk-${object.risk.toLowerCase()}`}>
                        RISK: {object.risk}
                    </div>
                )}
            </div>
        );
    };

    return (
        <div className="map-wrapper" style={{ position: 'relative', width: '100%', height: '100%' }}>
            <DeckGL
                initialViewState={INITIAL_VIEW_STATE}
                controller={{ dragRotate: true, touchRotate: true }}
                layers={layers}
                getTooltip={null}
                useDevicePixels={false}
                glOptions={{ preserveDrawingBuffer: true }}
            >
                <Map
                    mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
                    attributionControl={false}
                />
            </DeckGL>
            {renderTooltip()}

            {/* Map overlays */}
            {corridorActive && (
                <div className="map-overlay-badge corridor-badge">
                    <span className="badge-pulse" />
                    CORRIDOR CLEARED
                </div>
            )}
            {floodOverlayActive && (
                <div className="map-overlay-badge flood-badge">
                    <span className="badge-pulse red" />
                    FLOOD ZONE ACTIVE
                </div>
            )}
        </div>
    );
}
