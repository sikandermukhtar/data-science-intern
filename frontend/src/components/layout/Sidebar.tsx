import { useState } from "react";
import { Plus, X, Sidebar as SidebarIcon, Archive, ArchiveRestore, Trash2, ChevronDown, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/store/useAppStore";
import { useChatStore } from "@/store/useChatStore";

export default function Sidebar() {
    const { isSidebarOpen, setSidebarOpen } = useAppStore();
    const { 
        sessions, 
        archivedSessions, 
        activeSessionId, 
        setCurrentSession, 
        createNewSession, 
        archiveSession, 
        unarchiveSession, 
        deleteSession 
    } = useChatStore();

    const [isArchivedOpen, setIsArchivedOpen] = useState(false);

    const handleDelete = (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation();
        if (window.confirm("Are you sure you want to permanently delete this chat? This action cannot be undone.")) {
            deleteSession(sessionId);
        }
    };

    const handleArchive = (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation();
        archiveSession(sessionId);
    };

    const handleUnarchive = (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation();
        unarchiveSession(sessionId);
    };

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
                <div className="px-3 py-2 text-xs font-medium text-zinc-500">Recent Chats</div>
                {sessions.length === 0 ? (
                    <div className="px-3 py-4 text-xs text-zinc-400 text-center">No active chats</div>
                ) : (
                    sessions.map((session) => (
                        <div
                            key={session.id}
                            onClick={() => {
                                setCurrentSession(session.id);
                                if (window.innerWidth < 768) {
                                    setSidebarOpen(false);
                                }
                            }}
                            className={`group relative flex items-center justify-between w-full px-3 py-2 text-sm rounded-md transition-colors cursor-pointer ${
                                activeSessionId === session.id
                                    ? "bg-zinc-200 dark:bg-zinc-800 font-medium text-zinc-900 dark:text-zinc-50"
                                    : "hover:bg-zinc-200/70 dark:hover:bg-zinc-800/50 text-zinc-600 dark:text-zinc-400"
                            }`}
                        >
                            <span className="truncate pr-12">{session.title}</span>

                            {/* Action Buttons (Visible on Hover / Active) */}
                            <div className="absolute right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                <button
                                    onClick={(e) => handleArchive(e, session.id)}
                                    title="Archive chat"
                                    className="p-1 rounded text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors"
                                >
                                    <Archive className="w-3.5 h-3.5" />
                                </button>
                                <button
                                    onClick={(e) => handleDelete(e, session.id)}
                                    title="Delete chat"
                                    className="p-1 rounded text-zinc-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors"
                                >
                                    <Trash2 className="w-3.5 h-3.5" />
                                </button>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Archived Chats Section */}
            <div className="border-t border-zinc-200 dark:border-zinc-800 p-2">
                <button
                    onClick={() => setIsArchivedOpen(!isArchivedOpen)}
                    className="w-full flex items-center justify-between px-3 py-2 text-xs font-medium text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300 hover:bg-zinc-200/60 dark:hover:bg-zinc-800/50 rounded-md transition-colors"
                >
                    <span className="flex items-center gap-1.5">
                        <Archive className="w-3.5 h-3.5" />
                        Archived Chats ({archivedSessions.length})
                    </span>
                    {isArchivedOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                </button>

                {isArchivedOpen && (
                    <div className="mt-1 max-h-48 overflow-y-auto space-y-1 pr-1">
                        {archivedSessions.length === 0 ? (
                            <div className="px-3 py-2 text-xs text-zinc-400 italic">No archived chats</div>
                        ) : (
                            archivedSessions.map((session) => (
                                <div
                                    key={session.id}
                                    onClick={() => {
                                        setCurrentSession(session.id);
                                        if (window.innerWidth < 768) {
                                            setSidebarOpen(false);
                                        }
                                    }}
                                    className={`group relative flex items-center justify-between w-full px-3 py-1.5 text-xs rounded-md transition-colors cursor-pointer ${
                                        activeSessionId === session.id
                                            ? "bg-zinc-200 dark:bg-zinc-800 font-medium text-zinc-900 dark:text-zinc-50"
                                            : "hover:bg-zinc-200/70 dark:hover:bg-zinc-800/50 text-zinc-500 dark:text-zinc-400"
                                    }`}
                                >
                                    <span className="truncate pr-12">{session.title}</span>

                                    {/* Action Buttons: Restore & Delete */}
                                    <div className="absolute right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button
                                            onClick={(e) => handleUnarchive(e, session.id)}
                                            title="Restore chat"
                                            className="p-1 rounded text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors"
                                        >
                                            <ArchiveRestore className="w-3.5 h-3.5" />
                                        </button>
                                        <button
                                            onClick={(e) => handleDelete(e, session.id)}
                                            title="Delete permanently"
                                            className="p-1 rounded text-zinc-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-zinc-300 dark:hover:bg-zinc-700 transition-colors"
                                        >
                                            <Trash2 className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                )}
            </div>
        </aside>
       </> 
    );
}