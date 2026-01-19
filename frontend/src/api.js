const API_BASE_URL = 'https://api.xierra.xyz/api';
const WS_BASE_URL = 'wss://api.xierra.xyz/ws';

export const api = {
    startDownload: async (url, format = "best", quality = "best") => {
        const response = await fetch(`${API_BASE_URL}/downloads`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url, format, quality }),
        });
        return response.json();
    },

    getDownloads: async () => {
        const response = await fetch(`${API_URL}/api/downloads`);
        return response.json();
    },

    deleteDownload: async (filename) => {
        const response = await fetch(`${API_URL}/api/downloads/${filename}`, {
            method: "DELETE",
        });
        return response.json();
    },

    connectWebSocket: (onMessage) => {
        const ws = new WebSocket(`ws://localhost:8000/ws`);
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onMessage(data);
        };
        return ws;
    }
};
