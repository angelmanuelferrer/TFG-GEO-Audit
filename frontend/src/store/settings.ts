import { create } from "zustand";

// La URL del backend y la API key se configuran en frontend/.env (VITE_API_BASE_URL, VITE_API_KEY).
// Este store solo guarda preferencias de UI que no son sensibles.

interface SettingsState {
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (v: boolean) => void;
}

export const useSettingsStore = create<SettingsState>()((set) => ({
  sidebarCollapsed: false,
  setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
}));
