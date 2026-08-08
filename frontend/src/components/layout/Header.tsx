import { Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAppStore } from "@/store/useAppStore";

export default function Header() {
    const { toggleSidebar } = useAppStore();

    return (
        <header className="md:hidden flex items-center p-4 border-b border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950">
            <Button variant="ghost" size="icon" onClick={toggleSidebar}>
                <Menu className="w-5 h-5" />
            </Button>
            <span className="ml-3 font-semibold text-sm">data-science-intern</span>
        </header>
    )
}