import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY ?? "";

const apiClient = axios.create({
  baseURL: BASE_URL,
});

if (API_KEY) {
  apiClient.defaults.headers.common["X-API-Key"] = API_KEY;
}

export default apiClient;
