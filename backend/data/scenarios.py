"""NEXUS-GOV Scenario Definitions for the Scenario Engine."""

SCENARIOS = {
    "monsoon_flood": {
        "name": "Monsoon Flash Flood — Musi River Basin",
        "description": "Heavy rainfall causes flooding in low-elevation Hussain Sagar and Khairatabad zones",
        "timeline": [
            {
                "delay_sec": 0,
                "event": "rainfall_anomaly",
                "updates": {
                    "sensor:zone_c2:rainfall_mm_hr": 95,
                    "sensor:zone_c1:rainfall_mm_hr": 72,
                },
                "log": "Rainfall sensor HS-07 detecting 95mm/hr at Hussain Sagar basin. Threshold: 65mm/hr EXCEEDED.",
                "threat_level": 2,
            },
            {
                "delay_sec": 3,
                "event": "flood_risk_assessment",
                "updates": {
                    "zone:zone_c2:flood_risk": "HIGH",
                    "zone:zone_c1:flood_risk": "HIGH",
                    "zone:zone_c2:water_level": 0.4,
                },
                "log": "Flood Agent assessed risk: C1/C2 HIGH. Historical pattern: 95mm/hr sustained >1hr = basin overflow.",
                "threat_level": 3,
            },
            {
                "delay_sec": 5,
                "event": "cross_domain_alert",
                "updates": {
                    "road:r_c1_c2:status": "FLOODED",
                    "road:r_c2_c3:status": "FLOODED",
                    "road:r_a3_c1:status": "BLOCKED",
                },
                "log": "Roads flooded: Tank Bund Rd, Chaderghat Rd. Punjagutta Rd BLOCKED. Broadcasting to all agents.",
                "threat_level": 3,
                "broadcast": True,
            },
            {
                "delay_sec": 7,
                "event": "ambulance_repositioning",
                "updates": {
                    "ambulance:amb_3:zone": "zone_a3",
                    "ambulance:amb_3:status": "REPOSITIONING",
                    "ambulance:amb_7:zone": "zone_d3",
                    "ambulance:amb_7:status": "REPOSITIONING",
                },
                "log": "Emergency Agent: Pre-positioning AMB-3 → Ameerpet, AMB-7 → Dilsukhnagar (outside flood zone, within 5-min response).",
            },
            {
                "delay_sec": 9,
                "event": "corridor_clearing",
                "updates": {
                    "corridor:r_a3_c1:status": "CLEARING",
                    "zone:zone_a3:traffic_congestion": 0.3,
                },
                "log": "Traffic Agent: Clearing emergency corridor Khairatabad → Begumpet. 18 signals set to PRIORITY GREEN. ETA: 47min → 8min.",
            },
            {
                "delay_sec": 11,
                "event": "power_reroute",
                "updates": {
                    "substation:sub_3:load_pct": 15,
                    "substation:sub_2:load_pct": 92,
                    "substation:sub_4:load_pct": 88,
                    "zone:zone_c3:power_status": "DEGRADED",
                    "zone:zone_c3:backup_active": True,
                },
                "log": "Power Agent: LB Nagar substation in flood zone C3. Rerouting 120MW → Kukatpally + Secunderabad. Hospital backup: ACTIVATED.",
                "threat_level": 4,
            },
            {
                "delay_sec": 13,
                "event": "cascade_complete",
                "updates": {
                    "corridor:r_a3_c1:status": "CLEARED",
                },
                "log": "Meta-Orchestrator: 4-domain cascade complete. Flood(0.94)→Emergency(0.91)→Traffic(0.88)→Power(0.86). Response time: 8.2 seconds.",
                "threat_level": 4,
                "audit": {
                    "agent": "meta_orchestrator",
                    "action": "cascade_coordination",
                    "reasoning": "4-domain cascade coordinated. All priority functions protected. No conflicts detected.",
                },
            },
        ],
    },
    "industrial_fire": {
        "name": "Industrial Fire — Malkajgiri Chemical Plant",
        "description": "Chemical factory fire in Malkajgiri zone requiring multi-agent response",
        "timeline": [
            {
                "delay_sec": 0,
                "event": "fire_detected",
                "updates": {
                    "zone:zone_d1:fire_severity": 8,
                    "zone:zone_d1:evacuation_status": "ADVISORY",
                },
                "log": "🔥 INDUSTRIAL FIRE detected: Malkajgiri Chemical Plant. Zone D1 severity 8. Evacuating 500m radius.",
                "threat_level": 4,
            },
            {
                "delay_sec": 3,
                "event": "emergency_dispatch_fire",
                "updates": {
                    "ambulance:amb_6:status": "DISPATCHED",
                    "ambulance:amb_6:zone": "zone_d1",
                },
                "log": "Emergency Agent: Dispatching AMB-6 to Malkajgiri fire zone. Case type: trauma. Alerting Gandhi Hospital.",
            },
            {
                "delay_sec": 5,
                "event": "resource_conflict",
                "updates": {},
                "log": "Meta-Orchestrator: RESOURCE CONFLICT DETECTED — Emergency Agent requests AMB-3/AMB-7 for fire zone, but units assigned to flood zones C1/C2.",
                "conflict": True,
            },
            {
                "delay_sec": 7,
                "event": "conflict_resolution",
                "updates": {
                    "ambulance:amb_5:status": "DISPATCHED",
                    "ambulance:amb_5:zone": "zone_d1",
                    "ambulance:amb_8:status": "DISPATCHED",
                    "ambulance:amb_8:zone": "zone_d1",
                },
                "log": "Meta-Orchestrator: CONFLICT RESOLUTION — FLOOD_SEVERITY(8) > FIRE_SEVERITY(7). Maintaining 3 units at flood. Diverting AMB-5, AMB-8 to fire zone.",
                "audit": {
                    "agent": "meta_orchestrator",
                    "action": "conflict_resolution",
                    "reasoning": "FLOOD_SEVERITY(8) > FIRE_SEVERITY(7). U(flood_priority) = 0.685 > U(fire_priority) = 0.485. Safety-weighted resolution.",
                },
            },
            {
                "delay_sec": 9,
                "event": "power_isolation",
                "updates": {
                    "zone:zone_d1:power_status": "ISOLATED",
                    "substation:sub_4:load_pct": 65,
                },
                "log": "Power Agent: Isolating C6 grid segment near fire. Rerouting 85MW to adjacent segments. Fire department power: PRIORITIZED.",
                "threat_level": 5,
            },
        ],
    },
    "dual_crisis": {
        "name": "Simultaneous Flood + Industrial Fire",
        "description": "Worst case: two crises competing for the same resources",
        "timeline": [],  # Built dynamically from monsoon_flood + industrial_fire
    },
}


def build_dual_crisis():
    """Combine monsoon_flood and industrial_fire with fire offset."""
    flood = SCENARIOS["monsoon_flood"]["timeline"]
    fire = SCENARIOS["industrial_fire"]["timeline"]

    combined = list(flood)
    for step in fire:
        combined.append({**step, "delay_sec": step["delay_sec"] + 14})

    SCENARIOS["dual_crisis"]["timeline"] = combined


build_dual_crisis()
