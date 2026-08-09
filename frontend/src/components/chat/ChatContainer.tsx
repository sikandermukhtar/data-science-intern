import { useChatStore } from "@/store/useChatStore";
import ChatInput from "@/components/chat/ChatInput";
import { Message as PromptMessage } from "@/components/ui/message";
import { Markdown } from "@/components/ui/markdown";
import { CodeBlock, CodeBlockCode } from "@/components/ui/code-block";
import { useRef, useEffect, useState } from "react";
import { Loader2, Download, X } from "lucide-react";

export default function ChatContainer() {
  const { activeSessionId, messages, isLoading } = useChatStore();
  const activeMessages = activeSessionId ? messages[activeSessionId] || [] : [];
  const bottomRef = useRef<HTMLDivElement>(null);

  const [viewerImage, setViewerImage] = useState<{ url : string; name: string } | null>(null);
  
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setViewerImage(null);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const triggerDownload = async (url: string, filename: string) => {
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(blobUrl);
    } catch (error) {
      console.error("Direct download failed due to CORS, opening in a new tab...", error);
      window.open(url, "_blank");
    }
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeMessages, isLoading]);

  return (
    <div className="relative flex-1 flex flex-col min-h-0 bg-white dark:bg-zinc-950 overflow-hidden">
      <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 pb-36">
        {activeMessages.length === 0 ? (
          <div className="max-w-3xl mx-auto w-full text-center space-y-4 my-24">
            <h1 className="text-3xl font-semibold text-zinc-800 dark:text-zinc-200">
              What are we building today?
            </h1>
            <p className="text-zinc-500 text-sm max-w-md mx-auto">
              Ask your Data Science Intern to load a dataset, perform statistical analysis, or evaluate models.
            </p>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto w-full space-y-6">
            {activeMessages.map((msg) => {
              const isUser = msg.role === "user";

              if (msg.content === "---charts---" && msg.files) {
                return (
                  <div key={msg.id} className="grid grid-cols-1 md:grid-cols-2 gap-4 my-2 ml-12">
                    {msg.files.map((file) => (
                      <div key={file.name} className="flex flex-col gap-1.5">
                        <span className="text-xs text-zinc-500 font-medium truncate">{file.name}</span>
                        <div
                          onClick={() => setViewerImage({ url: file.url || "", name: file.name })}
                          className="group relative aspect-[4/3] max-h-[220px] w-full overflow-hidden rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900 cursor-pointer shadow-xs"
                        >
                          <img
                            src={file.url || ""}
                            alt={file.name}
                            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-[1.02]"
                          />
                          <button
                            onClick={(e) => {
                              e.stopPropagation(); // Prevents opening the lightbox
                              triggerDownload(file.url || "", file.name);
                            }}
                            className="absolute top-3 right-3 p-2 bg-black/60 hover:bg-black/80 text-white rounded-full opacity-0 group-hover:opacity-100 transition-all duration-200 shadow-md pointer-events-auto"
                            title="Download Image"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                );
              }

              return (
                <PromptMessage
                  key={msg.id}
                  role={msg.role}
                  className="w-full"
                >
                  <div className="space-y-3 min-w-0 flex-1">
                    {isUser && msg.files && msg.files.length > 0 && (
                      <div className="flex flex-wrap gap-2 my-1">
                        {msg.files.map((file) => (
                          <div
                            key={file.name}
                            className="flex items-center gap-2 bg-zinc-100 dark:bg-zinc-800 px-3 py-1.5 rounded-lg text-xs border border-zinc-200 dark:border-zinc-700"
                          >
                            <span className="font-semibold truncate max-w-[150px]">{file.name}</span>
                            <span className="text-zinc-400">({(file.size / 1024).toFixed(1)} KB)</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {isUser ? (
                      <p className="text-zinc-800 dark:text-zinc-200 whitespace-pre-wrap">{msg.content}</p>
                    ) : (
                      <Markdown
                        components={{
                          code({ node, className, children, ...props }) {
                            const match = /language-(\w+)/.exec(className || "");
                            return match ? (
                              <div className="w-full max-w-full min-w-0 my-2">
                                <CodeBlock>
                                  <CodeBlockCode
                                    code={String(children).replace(/\n$/, "")}
                                    language={match[1]}
                                  />
                                </CodeBlock>
                             </div>
                            ) : (
                              <code className={className} {...props}>
                                {children}
                              </code>
                            );
                          },
                        }}
                      >
                        {msg.content}
                      </Markdown>
                    )}
                  </div>
                </PromptMessage>
              );
            })}

            {isLoading && (
              <PromptMessage role="assistant" className="w-full">
                <div className="flex items-center gap-2 text-zinc-500 text-sm">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Thinking and running code...</span>
                </div>
              </PromptMessage>
            )}
            <div ref={bottomRef} className="h-36" />
          </div>
        )}
      </div>

      <div className="absolute bottom-0 inset-x-0 p-6 bg-transparent flex justify-center w-full pointer-events-none">
        <div className="w-full max-w-3xl pointer-events-auto">
        <ChatInput />
        </div>
      </div>

      {viewerImage && (
        <div 
          onClick={() => setViewerImage(null)}
          className="fixed inset-0 bg-black/90 z-50 flex flex-col items-center justify-center p-4 animate-fade-in"
        >
          <div className="absolute top-4 right-4 flex items-center gap-3">
            <button 
              onClick={(e) => {
                e.stopPropagation();
                triggerDownload(viewerImage.url, viewerImage.name);
              }}
              className="p-2.5 bg-zinc-900/60 hover:bg-zinc-800/80 text-white rounded-full transition-colors flex items-center justify-center"
              title="Download image"
            >
              <Download className="w-5 h-5" />
            </button>
            
            <button 
              onClick={() => setViewerImage(null)}
              className="p-2.5 bg-zinc-900/60 hover:bg-zinc-800/80 text-white rounded-full transition-colors flex items-center justify-center"
              title="Close viewer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <div 
            onClick={(e) => e.stopPropagation()} 
            className="flex flex-col items-center max-w-5xl max-h-[85vh]"
          >
            <img 
              src={viewerImage.url} 
              alt={viewerImage.name} 
              className="max-w-full max-h-[80vh] object-contain rounded-lg border border-zinc-800 shadow-2xl"
            />
            <span className="text-zinc-400 text-sm font-medium mt-3 drop-shadow-sm truncate max-w-md">
              {viewerImage.name}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}