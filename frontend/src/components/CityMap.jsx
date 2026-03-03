import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import {
    MAP_CONFIG, CITY_ZONES, HOSPITALS, SUBSTATIONS,
    EMERGENCY_CORRIDOR, RISK_COLORS
} from '../data/cityModel';

export default function CityMap({ zones, ambulances, corridorActive, floodOverlayActive }) {
    const mapRef = useRef(null);
    const mapInstanceRef = useRef(null);
    const zoneLayersRef = useRef({});
    const ambulanceMarkersRef = useRef({});
    const corridorLineRef = useRef(null);
    const floodCircleRef = useRef(null);
    const [mapReady, setMapReady] = useState(false);

    // Initialize map
    useEffect(() => {
        if (mapInstanceRef.current) return;

        const map = L.map(mapRef.current, {
            center: MAP_CONFIG.center,
            zoom: MAP_CONFIG.zoom,
            zoomControl: false,
            attributionControl: false,
            preferCanvas: true
        });

        L.tileLayer(MAP_CONFIG.tileLayer, {
            subdomains: 'abcd',
            maxZoom: 18,
        }).addTo(map);

        mapInstanceRef.current = map;

        // Add zone polygons
        Object.entries(CITY_ZONES).forEach(([id, zone]) => {
            const colors = RISK_COLORS.LOW;
            const polygon = L.polygon(zone.polygon, {
                color: colors.stroke,
                weight: colors.weight,
                fillColor: colors.fill,
                fillOpacity: 0.8,
                className: `zone-${id}`
            }).addTo(map);

            polygon.bindTooltip(
                `<div style="text-align:center"><b>${id}</b><br/>${zone.name}<br/><span style="font-size:9px">RISK: LOW</span></div>`,
                { className: 'zone-tooltip', direction: 'top', offset: [0, -10] }
            );

            zoneLayersRef.current[id] = polygon;
        });

        // Hospital markers
        HOSPITALS.forEach(h => {
            const icon = L.divIcon({
                className: 'custom-marker marker-hospital',
                html: '🏥',
                iconSize: [26, 26],
                iconAnchor: [13, 13]
            });
            L.marker([h.lat, h.lng], { icon })
                .bindTooltip(h.name, { className: 'zone-tooltip', direction: 'top', offset: [0, -16] })
                .addTo(map);
        });

        // Substation markers
        SUBSTATIONS.forEach(s => {
            const icon = L.divIcon({
                className: 'custom-marker marker-substation',
                html: '⚡',
                iconSize: [22, 22],
                iconAnchor: [11, 11]
            });
            L.marker([s.lat, s.lng], { icon })
                .bindTooltip(s.name, { className: 'zone-tooltip', direction: 'top', offset: [0, -14] })
                .addTo(map);
        });

        setMapReady(true);

        return () => {
            map.remove();
            mapInstanceRef.current = null;
        };
    }, []);

    // Update zone colors
    useEffect(() => {
        if (!mapReady) return;
        Object.entries(zones).forEach(([id, risk]) => {
            const layer = zoneLayersRef.current[id];
            if (!layer) return;
            const colors = RISK_COLORS[risk] || RISK_COLORS.LOW;
            layer.setStyle({
                color: colors.stroke,
                weight: colors.weight,
                fillColor: colors.fill
            });

            layer.setTooltipContent(
                `<div style="text-align:center"><b>${id}</b><br/>${CITY_ZONES[id]?.name || ''}<br/><span style="font-size:9px;color:${risk === 'CRITICAL' || risk === 'HIGH' ? '#FF2D55' : risk === 'MEDIUM' ? '#FF9500' : '#39FF14'}">RISK: ${risk}</span></div>`
            );
        });
    }, [zones, mapReady]);

    // Update ambulance markers
    useEffect(() => {
        if (!mapReady || !mapInstanceRef.current) return;
        const map = mapInstanceRef.current;

        ambulances.forEach(amb => {
            const existing = ambulanceMarkersRef.current[amb.id];
            if (existing) {
                // Animate position
                const currentLatLng = existing.getLatLng();
                const targetLatLng = L.latLng(amb.lat, amb.lng);
                if (currentLatLng.lat !== targetLatLng.lat || currentLatLng.lng !== targetLatLng.lng) {
                    // Simple smooth move
                    const steps = 30;
                    const latStep = (targetLatLng.lat - currentLatLng.lat) / steps;
                    const lngStep = (targetLatLng.lng - currentLatLng.lng) / steps;
                    let step = 0;
                    const moveInterval = setInterval(() => {
                        step++;
                        existing.setLatLng([
                            currentLatLng.lat + latStep * step,
                            currentLatLng.lng + lngStep * step
                        ]);
                        if (step >= steps) clearInterval(moveInterval);
                    }, 66); // ~2s total
                }
            } else {
                const icon = L.divIcon({
                    className: `custom-marker marker-ambulance ${amb.status === 'MOVING' ? 'moving' : ''}`,
                    html: '🚑',
                    iconSize: [24, 24],
                    iconAnchor: [12, 12]
                });
                const marker = L.marker([amb.lat, amb.lng], { icon })
                    .bindTooltip(`${amb.id} · ${amb.status}`, { className: 'zone-tooltip', direction: 'top', offset: [0, -16] })
                    .addTo(map);
                ambulanceMarkersRef.current[amb.id] = marker;
            }
        });
    }, [ambulances, mapReady]);

    // Emergency corridor
    useEffect(() => {
        if (!mapReady || !mapInstanceRef.current) return;
        const map = mapInstanceRef.current;

        if (corridorActive && !corridorLineRef.current) {
            const line = L.polyline(EMERGENCY_CORRIDOR, {
                color: '#00E5FF',
                weight: 4,
                opacity: 0.8,
                dashArray: '12 8',
                className: 'corridor-line'
            }).addTo(map);

            // Animate dash offset
            const path = line.getElement();
            if (path) {
                path.style.animation = 'none';
                path.style.strokeDashoffset = '0';
                let offset = 0;
                const animInterval = setInterval(() => {
                    offset -= 2;
                    path.style.strokeDashoffset = String(offset);
                }, 50);
                line._animInterval = animInterval;
            }

            // Add "CORRIDOR CLEARED" label at midpoint
            const mid = EMERGENCY_CORRIDOR[Math.floor(EMERGENCY_CORRIDOR.length / 2)];
            const labelIcon = L.divIcon({
                className: '',
                html: `<div style="
          font-family: var(--font-ui);
          font-size: 9px;
          color: #00E5FF;
          background: rgba(0,229,255,0.12);
          padding: 2px 8px;
          border-radius: 2px;
          border: 1px solid rgba(0,229,255,0.3);
          white-space: nowrap;
          letter-spacing: 2px;
          text-shadow: 0 0 8px rgba(0,229,255,0.5);
        ">CORRIDOR CLEARED</div>`,
                iconSize: [120, 20],
                iconAnchor: [60, 30]
            });
            const label = L.marker(mid, { icon: labelIcon, interactive: false }).addTo(map);
            line._label = label;

            corridorLineRef.current = line;
        } else if (!corridorActive && corridorLineRef.current) {
            if (corridorLineRef.current._animInterval) clearInterval(corridorLineRef.current._animInterval);
            if (corridorLineRef.current._label) mapInstanceRef.current.removeLayer(corridorLineRef.current._label);
            mapInstanceRef.current.removeLayer(corridorLineRef.current);
            corridorLineRef.current = null;
        }
    }, [corridorActive, mapReady]);

    // Flood overlay
    useEffect(() => {
        if (!mapReady || !mapInstanceRef.current) return;
        const map = mapInstanceRef.current;

        if (floodOverlayActive && !floodCircleRef.current) {
            const floodCenter = CITY_ZONES.C1.center;
            const circle = L.circle(floodCenter, {
                radius: 1500,
                color: 'rgba(0, 100, 255, 0.4)',
                fillColor: 'rgba(0, 100, 255, 0.2)',
                fillOpacity: 0.5,
                weight: 2,
                className: 'flood-overlay'
            }).addTo(map);

            // Animated concentric rings (using additional circles)
            const rings = [];
            for (let i = 0; i < 3; i++) {
                const ring = L.circle(floodCenter, {
                    radius: 800,
                    color: 'rgba(0, 100, 255, 0.3)',
                    fill: false,
                    weight: 1,
                    className: `flood-ring-${i}`
                }).addTo(map);
                rings.push(ring);
            }

            floodCircleRef.current = { circle, rings };
        } else if (!floodOverlayActive && floodCircleRef.current) {
            map.removeLayer(floodCircleRef.current.circle);
            floodCircleRef.current.rings.forEach(r => map.removeLayer(r));
            floodCircleRef.current = null;
        }
    }, [floodOverlayActive, mapReady]);

    return (
        <div className="map-wrapper">
            <div ref={mapRef} style={{ height: '100%', width: '100%' }} />
        </div>
    );
}
