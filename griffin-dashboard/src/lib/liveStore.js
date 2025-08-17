// src/lib/liveStore.js
import { readable } from 'svelte/store';
import { browser } from '$app/environment';

const WEBSOCKET_URL = "ws://127.0.0.1:5000/ws";
// نکته: این مقسوم‌علیه ممکن است نیاز به بازبینی داشته باشد.
// بک‌اند اسپرد را به صورت پیپ (ضربدر 100000) ارسال می‌کند.
// اگر می‌خواهید اسپرد را به صورت قیمت خام نمایش دهید، این مقدار باید 100000 باشد.
const SPREAD_DIVISOR = 100000;

const initialState = {
    status: 'connecting',
    data: {}
};

function normalizeSpreadValues(data) {
    if (!data) return {};
    // Deep copy to avoid modifying the original data object
    const newData = JSON.parse(JSON.stringify(data));

    for (const symbol in newData) {
        for (const brokerName in newData[symbol]) {
            const brokerData = newData[symbol][brokerName];
            const fieldsToNormalize = ['avg_spread', 'max_spread', 'spread_std_dev', 'current_spread'];

            fieldsToNormalize.forEach(field => {
                if (brokerData.hasOwnProperty(field)) {
                    const rawValue = parseFloat(brokerData[field]);
                    if (!isNaN(rawValue)) {
                        brokerData[field] = rawValue / SPREAD_DIVISOR;
                    }
                }
            });
        }
    }
    return newData;
}


export const liveData = readable(initialState, (set) => {
    if (!browser) return;

    let socket;
    let reconnectTimer;
    // از let برای currentData استفاده می‌کنیم تا قابل تغییر باشد
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
                const messageData = JSON.parse(event.data);
                
                // --- منطق جدید برای مدیریت انواع پیام ---
                if (messageData.type === 'spread_update') {
                    // اگر پیام فقط برای آپدیت اسپرد است
                    const { symbol, broker, current_spread } = messageData;
                    if (currentData[symbol] && currentData[symbol][broker]) {
                        // فقط مقدار اسپرد لحظه‌ای را به‌روز می‌کنیم
                        currentData[symbol][broker].current_spread = current_spread / SPREAD_DIVISOR;
                        
                        // با ارسال یک کپی جدید از آبجکت، Svelte را مجبور به آپدیت می‌کنیم
                        set({ status: 'connected', data: { ...currentData } });
                    }
                } else if (messageData.type === 'full_analysis') {
                    // اگر پیام حاوی تحلیل کامل است
                    const normalizedData = normalizeSpreadValues(messageData.payload);
                    currentData = normalizedData;
                    set({ status: 'connected', data: normalizedData });
                }

            } catch (error) {
                console.error("Failed to parse or process WebSocket message:", error, event.data);
            }
        };


        socket.onclose = () => {
            console.log("WebSocket disconnected. Retrying in 3 seconds...");
            set({ status: 'disconnected', data: currentData });
            reconnectTimer = setTimeout(connect, 3000);
        };

        socket.onerror = (error) => {
            console.error("WebSocket error:", error);
            socket.close();
        };
    }

    connect();

    return () => {
        clearTimeout(reconnectTimer);
        if (socket) {
            socket.close();
        }
    };
});