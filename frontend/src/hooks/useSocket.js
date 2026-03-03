// ═══════════════════════════════════════════
// Socket.IO Hook — connects to NEXUS-GOV backend
// ═══════════════════════════════════════════
import { useEffect, useState, useCallback, useRef } from 'react';
import { io } from 'socket.io-client';

export function useSocket(url = `http://${window.location.hostname}:8000`) {
    const [connected, setConnected] = useState(false);
    const [simulationMode, setSimulationMode] = useState(true);
    const socketRef = useRef(null);
    const listenersRef = useRef({});

    useEffect(() => {
        const socket = io(url, {
            transports: ['polling', 'websocket'],
            upgrade: true,
            withCredentials: false,
            timeout: 5000,
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
        });
        socketRef.current = socket;

        socket.on('connect', () => {
            console.log('[NEXUS-WS] Connected to backend:', socket.id);
            setConnected(true);
            setSimulationMode(false);
        });

        socket.on('disconnect', () => {
            console.log('[NEXUS-WS] Disconnected from backend');
            setConnected(false);
            setSimulationMode(true);
        });

        socket.on('connect_error', (err) => {
            console.log('[NEXUS-WS] Connection error:', err.message, '— falling back to simulation');
            setSimulationMode(true);
        });

        socket.on('connection_ack', (data) => {
            console.log('[NEXUS-WS] Server ACK:', data.message);
        });

        // Register any stored listeners
        Object.entries(listenersRef.current).forEach(([event, handler]) => {
            socket.on(event, handler);
        });

        return () => {
            socket.disconnect();
            socketRef.current = null;
        };
    }, [url]);

    const on = useCallback((event, handler) => {
        listenersRef.current[event] = handler;
        if (socketRef.current) {
            socketRef.current.off(event);
            socketRef.current.on(event, handler);
        }
    }, []);

    const emit = useCallback((event, data) => {
        if (socketRef.current && socketRef.current.connected) {
            socketRef.current.emit(event, data);
        }
    }, []);

    return { connected, simulationMode, on, emit, socket: socketRef.current };
}
