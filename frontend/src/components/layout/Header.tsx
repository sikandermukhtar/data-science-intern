import { Menu, Sidebar as SidebarIcon } from "lucide-react"; 
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/store/useAppStore";

export default function Header() {
    const { isSidebarOpen, toggleSidebar } = useAppStore();

    return (
        <header className="flex items-center p-4 border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
            <Button 
                variant="ghost" 
                size="icon" 
                onClick={toggleSidebar}
                className={`md:hidden ${isSidebarOpen ? "hidden" : ""}`}
            >
                <Menu className="w-5 h-5" />
            </Button>

            {!isSidebarOpen && (
                <Button 
                    variant="ghost" 
                    size="icon" 
                    onClick={toggleSidebar}
                    className="hidden md:flex mr-2 text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200"
                    title="Toggle Sidebar (Ctrl+B)"
                >
                    <SidebarIcon className="w-5 h-5" />
                </Button>
            )}
            <span className="ml-3 font-semibold text-sm">data-science-intern</span>
        </header>
    )
}