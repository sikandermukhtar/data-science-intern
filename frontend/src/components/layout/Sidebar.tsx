import { Plus, X, Sidebar as SidebarIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/store/useAppStore";
import { useChatStore } from "@/store/useChatStore";

export default function Sidebar() {
    const { isSidebarOpen, setSidebarOpen } = useAppStore();
    const { sessions, activeSessionId, setCurrentSession, createNewSession } = useChatStore();

    return (
       <>
        {isSidebarOpen && (
            <div
                className="fixed inset-0 bg-black/50 z-40 md:hidden"
                onClick={() => setSidebarOpen(false)}
            />
        )}

        <aside className={`
            fixed inset-y-0 left-0 z-50 w-full md:w-64 bg-zinc-100 dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 transform transition-transform duration-200 ease-in-out flex flex-col
            ${isSidebarOpen ? "translate-x-0" : "-translate-x-full"}
        `}>

            <div className="p-4 flex justify-between items-center border-b border-zinc-200 dark:border-zinc-800">
                <span className="font-semibold text-sm">data-science-intern</span>
                <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={() => setSidebarOpen(false)}
                    className="hidden md:flex text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
                    title="Collapse Sidebar"
                >
                    <SidebarIcon className="w-5 h-5" />
                </Button>
                <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={() => setSidebarOpen(false)}
                    className="md:hidden text-zinc-500"
                >
                    <X className="w-5 h-5" />
                </Button>
            </div>
            
            <div className="p-2">
                <Button variant="outline" className="w-full justify-start gap-2 shadow-sm"
                    onClick={() => {
                        createNewSession();
                        if (window.innerWidth < 768) {
                            setSidebarOpen(false);
                        }
                    }}
                >
                    <Plus className="w-4 h-4" />
                    New Session
                </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-1">
                <div className="px-3 py-2 text-xs font-medium text-zinc-500">Recent</div>
                {sessions.map((session) => (
                    <button
                        key={session.id}
                        onClick={() => {
                            setCurrentSession(session.id);
                            if (window.innerWidth < 768) {
                                setSidebarOpen(false);
                            }
                        }}
                        className={`w-full text-left px-3 py-2 text-sm rounded-md transition-colors truncate ${
                            activeSessionId === session.id
                                ? "bg-zinc-200 dark:bg-zinc-850 font-medium text-zinc-900 dark:text-zinc-50"
                                : "hover:bg-zinc-200 dark:hover:bg-zinc-800/50 text-zinc-600 dark:text-zinc-400"
                        }`}
                    >
                        {session.title}
                    </button>
                ))}
            </div>
        </aside>

       </> 
    )
}