// src/api/client.js — Centralized axios instance for all FastAPI calls.
// Will be fully implemented in Phase 17.
import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8001",
  headers: {
    "Content-Type": "application/json",
  },
});

export default apiClient;
