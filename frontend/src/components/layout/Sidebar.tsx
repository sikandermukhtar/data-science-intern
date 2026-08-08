import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/store/useAppStore";

export default function Sidebar() {
    const { isSidebarOpen, setSidebarOpen } = useAppStore();

    return (
       <>
        {isSidebarOpen && (
            <div
                className="fixed inset-0 bg-black/50 z-40 md:hidden"
                onClick={() => setSidebarOpen(false)}
            />
        )}

        <aside className={`
            fixed md:static inset-y-0 left-0 z-50 w-64 bg-zinc-100 dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 transform transition-transform duration-200 ease-in-out flex flex-col
            ${isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
        `}>
            <div className="p-4 flex justify-between items-center border-b border-zinc-200 dark:border-zinc-800">
                <span className="font-semibold text-sm">data-science-intern</span>
            </div>
            <div className="p-2">
                <Button variant="outline" className="w-full justify-start gap-2 shadow-sm">
                    <Plus className="w-4 h-4" />
                    New Session
                </Button>
            </div>
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
                <div className="px-3 py-2 text-xs font-medium text-zinc-500">Today</div>
                <button className="w-full text-left px-3 py-2 text-sm rounded-md hover:bg-zinc-200 dark:hover:bg-zinc-800 transition-colors truncate">
                    Setup React Project
                </button>
            </div>
        </aside>

       </> 
    )
}