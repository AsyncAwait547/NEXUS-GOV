// ═══════════════════════════════════════════
// NEXUS-GOV City Model — Hyderabad
// Zones, Hospitals, Substations, Ambulances
// ═══════════════════════════════════════════

export const MAP_CONFIG = {
    center: [17.385, 78.486],
    zoom: 12,
    tileLayer: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '© OSM © CARTO'
};

export const CITY_ZONES = {
    C1: {
        name: 'Hussain Sagar / Khairatabad',
        center: [17.4239, 78.4738],
        polygon: [
            [17.435, 78.458], [17.438, 78.475], [17.432, 78.492],
            [17.418, 78.495], [17.410, 78.480], [17.412, 78.462]
        ]
    },
    C2: {
        name: 'Banjara Hills / Jubilee Hills',
        center: [17.4120, 78.4350],
        polygon: [
            [17.425, 78.420], [17.428, 78.440], [17.420, 78.452],
            [17.405, 78.450], [17.400, 78.432], [17.408, 78.418]
        ]
    },
    C3: {
        name: 'Begumpet / Secunderabad',
        center: [17.4437, 78.4983],
        polygon: [
            [17.455, 78.486], [17.458, 78.502], [17.450, 78.515],
            [17.435, 78.512], [17.432, 78.496], [17.440, 78.484]
        ]
    },
    C4: {
        name: 'Ameerpet / SR Nagar',
        center: [17.4375, 78.4483],
        polygon: [
            [17.448, 78.435], [17.450, 78.452], [17.443, 78.462],
            [17.430, 78.460], [17.428, 78.443], [17.435, 78.433]
        ]
    },
    C5: {
        name: 'LB Nagar / Saroor Nagar',
        center: [17.3457, 78.5522],
        polygon: [
            [17.358, 78.538], [17.360, 78.558], [17.352, 78.570],
            [17.338, 78.565], [17.335, 78.548], [17.342, 78.536]
        ]
    },
    C6: {
        name: 'Malkajgiri / Uppal',
        center: [17.4565, 78.5275],
        polygon: [
            [17.470, 78.515], [17.472, 78.535], [17.462, 78.545],
            [17.448, 78.540], [17.445, 78.522], [17.455, 78.512]
        ]
    },
    C7: {
        name: 'Kukatpally / KPHB',
        center: [17.4948, 78.3996],
        polygon: [
            [17.508, 78.385], [17.510, 78.405], [17.502, 78.418],
            [17.488, 78.415], [17.485, 78.398], [17.492, 78.383]
        ]
    },
    C8: {
        name: 'Gachibowli / Hitec City',
        center: [17.4401, 78.3489],
        polygon: [
            [17.452, 78.335], [17.455, 78.355], [17.447, 78.368],
            [17.433, 78.365], [17.430, 78.348], [17.437, 78.333]
        ]
    },
    C9: {
        name: 'Dilsukhnagar / Malakpet',
        center: [17.3688, 78.5247],
        polygon: [
            [17.380, 78.510], [17.382, 78.530], [17.375, 78.542],
            [17.362, 78.538], [17.358, 78.520], [17.365, 78.508]
        ]
    },
    C10: {
        name: 'Mehdipatnam / Tolichowki',
        center: [17.3935, 78.4420],
        polygon: [
            [17.405, 78.428], [17.408, 78.448], [17.400, 78.460],
            [17.385, 78.456], [17.382, 78.438], [17.390, 78.426]
        ]
    },
    C11: {
        name: 'Miyapur / Bachupally',
        center: [17.5100, 78.3600],
        polygon: [
            [17.522, 78.345], [17.525, 78.365], [17.518, 78.378],
            [17.505, 78.375], [17.500, 78.358], [17.508, 78.343]
        ]
    },
    C12: {
        name: 'Patancheruvu / Medak Road',
        center: [17.5320, 78.2700],
        polygon: [
            [17.545, 78.255], [17.548, 78.275], [17.540, 78.288],
            [17.525, 78.285], [17.522, 78.268], [17.530, 78.253]
        ]
    }
};

export const HOSPITALS = [
    { id: 'nims', name: 'NIMS Hospital', lat: 17.4156, lng: 78.4747 },
    { id: 'care', name: 'Care Hospital', lat: 17.4248, lng: 78.4482 },
    { id: 'yashoda', name: 'Yashoda Hospital', lat: 17.4032, lng: 78.5150 },
    { id: 'apollo', name: 'Apollo Hospital', lat: 17.4080, lng: 78.4615 }
];

export const SUBSTATIONS = [
    { id: 'lbnagar_sub', name: 'LB Nagar Sub', lat: 17.3457, lng: 78.5522 },
    { id: 'kukatpally_sub', name: 'Kukatpally Sub', lat: 17.4948, lng: 78.3996 },
    { id: 'secunderabad_sub', name: 'Secunderabad Sub', lat: 17.4437, lng: 78.4983 },
    { id: 'ameerpet_sub', name: 'Ameerpet Sub', lat: 17.4375, lng: 78.4483 }
];

export const INITIAL_AMBULANCES = [
    { id: 'AMB-1', lat: 17.39, lng: 78.49, status: 'STANDBY' },
    { id: 'AMB-2', lat: 17.37, lng: 78.47, status: 'STANDBY' },
    { id: 'AMB-3', lat: 17.41, lng: 78.50, status: 'STANDBY' },
    { id: 'AMB-4', lat: 17.38, lng: 78.46, status: 'STANDBY' },
    { id: 'AMB-5', lat: 17.36, lng: 78.52, status: 'STANDBY' },
    { id: 'AMB-6', lat: 17.43, lng: 78.48, status: 'STANDBY' }
];

export const EMERGENCY_CORRIDOR = [
    [17.4239, 78.4738],
    [17.4300, 78.4800],
    [17.4375, 78.4883],
    [17.4437, 78.4983]
];

export const RISK_COLORS = {
    LOW: { fill: 'rgba(57, 255, 20, 0.06)', stroke: 'rgba(57, 255, 20, 0.25)', weight: 1 },
    MEDIUM: { fill: 'rgba(255, 149, 0, 0.10)', stroke: 'rgba(255, 149, 0, 0.35)', weight: 1.5 },
    HIGH: { fill: 'rgba(255, 45, 85, 0.15)', stroke: 'rgba(255, 45, 85, 0.50)', weight: 2 },
    CRITICAL: { fill: 'rgba(255, 45, 85, 0.28)', stroke: 'rgba(255, 45, 85, 0.70)', weight: 2.5 }
};

export const AGENT_COLORS = {
    flood: '#0066FF',
    emergency: '#FF2D55',
    traffic: '#39FF14',
    power: '#FF9500',
    meta: '#00E5FF'
};

export const AGENT_BADGES = {
    flood: 'FLD',
    emergency: 'EMG',
    traffic: 'TRF',
    power: 'PWR',
    meta: 'META'
};
