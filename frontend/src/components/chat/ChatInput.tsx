import { useState } from "react";
import { ArrowUp, Paperclip, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  PromptInput,
  PromptInputAction,
  PromptInputActions,
  PromptInputTextarea,
} from "@/components/ui/prompt-input";

export default function ChatInput() {
    const [prompt, setPrompt] = useState("")
    const [files, setFiles] = useState<File[]>([]);


    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
        }
    }

    const removeFile = (indexToRemove: number) => {
        setFiles(files.filter((_, i) => i !== indexToRemove));
    };

    const handleSubmit = () => {
        if (!prompt.trim() && files.length == 0) return;
        console.log("Submitting prompt: ", prompt, "Files: ", files);
        setFiles([]);
        setPrompt("");
    }

    return (
        <div className="w-full max-w-3xl mx-auto flex flex-col gap-2">
        

        <PromptInput
            className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-sm rounded-xl overflow-hidden focus-within:ring-2 focus-within:ring-zinc-200 dark:focus-within:ring-zinc-700 transition-all"
        >
            {files.length > 0 && (
                <div className="flex flex-wrap gap-2 px-2">
                    {files.map((file, i) => (
                        <div key={i} className="flex items-center gap-2 bg-zinc-100 dark:bg-zinc-800 px-3 py-1.5 rounded-lg text-xs border border-zinc-200 dark:border-zinc-700">
                            <span className="truncate max-w-[120px] font-medium">{file.name}</span>
                            <button onClick={() => removeFile(i)} className="text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200">
                                <X className="w-3 h-3" />
                            </button>
                        </div>
                    ))}
                </div>
            )}
            <PromptInputTextarea
                placeholder="Ask data-science-intern a question or attach files..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit();
                    }
                }}
                className="min-h-[60px] px-4 py-4 resize-none border-none focus-visible:ring-0 shadow-none text-base"
            />
            <div className="flex items-center justify-between px-3 pb-3 pt-1">
                <PromptInputActions className="left-2">
                    <div className="relative">
                    <PromptInputAction tooltip="Attach files">
                        <Paperclip className="w-4 h-4 text-zinc-500" />
                    </PromptInputAction>
                    <input
                        type="file"
                        multiple
                        className="absolute inset-0 opacity-0 cursor-pointer"
                        onChange={handleFileChange}
                        title="Upload files"
                    />
                    </div>
                </PromptInputActions>

                <PromptInputActions className="right-2">
                    <Button 
                    size="icon" 
                    className="h-8 w-8 rounded-lg bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 hover:bg-zinc-800 dark:hover:bg-zinc-200"
                    onClick={handleSubmit}
                    disabled={!prompt.trim() && files.length === 0}
                    >
                    <ArrowUp className="w-4 h-4" />
                    </Button>
                </PromptInputActions>
            </div>
        </PromptInput>

        </div>
    )
}