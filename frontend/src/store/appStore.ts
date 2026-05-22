import { create } from "zustand";

interface AppState {
  sessionId: string | null;
  fileName: string | null;
  totalRows: number;
  isCleaned: boolean;
  isProcessing: boolean;
  theme: "light" | "dark";
  setSession: (sessionId: string, fileName: string, totalRows: number) => void;
  setCleaned: (val: boolean) => void;
  setProcessing: (val: boolean) => void;
  toggleTheme: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  sessionId: null,
  fileName: null,
  totalRows: 0,
  isCleaned: false,
  isProcessing: false,
  theme: "dark",
  setSession: (sessionId, fileName, totalRows) =>
    set({ sessionId, fileName, totalRows, isCleaned: false }),
  setCleaned: (val) => set({ isCleaned: val }),
  setProcessing: (val) => set({ isProcessing: val }),
  toggleTheme: () =>
    set((state) => ({ theme: state.theme === "dark" ? "light" : "dark" })),
}));
