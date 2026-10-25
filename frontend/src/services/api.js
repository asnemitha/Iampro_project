import axios from "axios";

// Read and normalize VITE_API_URL for local dev or production
const rawUrl = import.meta.env.VITE_API_URL;
const baseURL = (typeof rawUrl === "string" && rawUrl.trim() !== "")
    ? rawUrl.trim().replace(/\/+$/, "")
    : "http://127.0.0.1:8000";

const api = axios.create({
    baseURL,
    timeout: 60000, // 60s timeout for deep scholarly retrieval
    headers: {
        "Content-Type": "application/json",
    },
});

export default api;
