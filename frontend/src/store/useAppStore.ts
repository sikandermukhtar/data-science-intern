import { create } from 'zustand';

interface AppState {
    isSidebarOpen: boolean;
    toggleSidebar: () => void;
    setSidebarOpen: (isOpen: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
    isSidebarOpen: false,
    toggleSidebar: () => set((state: AppState) => ({ isSidebarOpen: !state.isSidebarOpen })),
    setSidebarOpen: (isOpen: boolean) => set({ isSidebarOpen: isOpen }),
}))