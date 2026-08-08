import type { ReactNode } from "react";
import Sidebar from "@/components/layout/Sidebar";
import Header from "@/components/layout/Header";

export default function MainLayout({ children }: { children: ReactNode }) {
    return (
        <div className="flex h-screen w-full bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-50 overflow-hidden">
            <Sidebar />
            <main className="flex-1 flex flex-col min-w-0">
                <Header />
                {children}
            </main>
        </div>
    )
}