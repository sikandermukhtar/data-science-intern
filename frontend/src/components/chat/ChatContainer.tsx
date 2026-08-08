import ChatInput from "@/components/chat/ChatInput";

export default function ChatContainer() {
  return (
    <>
      {/* Chat Feed Placeholder */}
      <div className="flex-1 overflow-y-auto p-4 md:p-8 flex flex-col justify-end">
        <div className="max-w-3xl mx-auto w-full text-center space-y-4 mb-12">
          <h1 className="text-3xl font-semibold text-zinc-800 dark:text-zinc-200">
            What are we building today?
          </h1>
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4">
        <ChatInput />
      </div>
    </>
  );
}