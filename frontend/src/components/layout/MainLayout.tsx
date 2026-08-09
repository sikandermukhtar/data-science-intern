import { useEffect, type ReactNode } from "react";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";
import { useAppStore } from "@/store/useAppStore";

export default function MainLayout({ children }: { children: ReactNode }) {

    const { isSidebarOpen, toggleSidebar } = useAppStore();

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
                e.preventDefault();
                toggleSidebar();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [toggleSidebar]);

    return (
        <div className="flex h-screen w-full bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-50 overflow-hidden">
            <Sidebar />
            <main className={`flex-1 flex flex-col min-w-0 transition-all duration-200 ${isSidebarOpen ? "md:pl-64": "md:pl-0"}`}>
                <Header />
                {children}
            </main>
        </div>
    )
}