import { readable } from 'svelte/store';
import { browser } from '$app/environment';

const WEBSOCKET_URL = "ws://127.0.0.1:5000/ws";

// The initial state of our store, including connection status and data
const initialState = {
    status: 'connecting', // Can be 'connecting', 'connected', or 'disconnected'
    data: {}
};

/**
 * A readable Svelte store that manages the WebSocket connection
 * and provides real-time analysis data to the application.
 */
export const liveData = readable(initialState, (set) => {
    if (!browser) {
        return; // Don't run WebSocket logic on the server
    }

    let socket;
    let reconnectTimer;
    // Keep the last known data to show even when disconnected
    let currentData = {}; 

    function connect() {
        clearTimeout(reconnectTimer);
        set({ status: 'connecting', data: currentData });

        socket = new WebSocket(WEBSOCKET_URL);

        socket.onopen = () => {
            console.log("WebSocket connected!");
            set({ status: 'connected', data: currentData });
        };

        socket.onmessage = (event) => {
            try {
                const newData = JSON.parse(event.data);
                currentData = newData; // Update the current data
                if (socket.readyState === WebSocket.OPEN) {
                    set({ status: 'connected', data: newData });
                }
            } catch (error) {
                console.error("Failed to parse WebSocket message:", error);
            }
        };

        socket.onclose = () => {
            console.log("WebSocket disconnected. Retrying in 3 seconds...");
            set({ status: 'disconnected', data: currentData });
            reconnectTimer = setTimeout(connect, 3000);
        };

        socket.onerror = (error) => {
            console.error("WebSocket error:", error);
            // The onclose event will be triggered automatically after an error,
            // which will handle the reconnect logic.
            socket.close();
        };
    }

    connect();

    // Cleanup function that runs when the last subscriber unsubscribes
    return () => {
        clearTimeout(reconnectTimer);
        if (socket) {
            socket.close();
        }
    };
});
