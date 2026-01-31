import { Paperclip, SendHorizonal } from "lucide-react";
import React, { useRef, useState } from "react";

interface ChatInputProps {
  onSend: (msg: string) => void;
  isEmpty: boolean;
  isLoading?: boolean;
}

export default function ChatInput({
  onSend,
  isLoading = false,
}: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const MAX_HEIGHT = 160;

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, MAX_HEIGHT) + "px";
    }
  };

  const sendMessage = () => {
    if (!input.trim() || isLoading) return;
    onSend(input.trim());
    setInput("");

    if (textareaRef.current) textareaRef.current.style.height = "auto";
  };

  return (
    <div className="relative">
      {/* Chat Input */}
      <div className="flex flex-col gap-2 border-2 border-gray-200 dark:border-gray-700 rounded-2xl p-3 shadow-lg bg-white dark:bg-gray-800 hover:border-blue-300 dark:hover:border-blue-600 transition-colors focus-within:border-blue-500 dark:focus-within:border-blue-500 focus-within:shadow-xl">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleChange}
          placeholder="Type your message..."
          rows={1}
          disabled={isLoading}
          className="w-full resize-none border-none outline-none px-2 py-2 rounded-lg overflow-y-auto max-h-[160px] disabled:opacity-50 text-gray-800 dark:text-gray-100 placeholder:text-gray-400 dark:placeholder:text-gray-500 bg-transparent"
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
        />

        <div className="flex justify-between items-center">
          <button
            type="button"
            className="text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 rounded-full p-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition"
            title="Attach file (coming soon)"
          >
            <Paperclip size={18} />
          </button>

          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="bg-blue-600 text-white rounded-full px-4 py-2 hover:bg-blue-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed transition-all flex items-center gap-2 shadow-md hover:shadow-lg"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                <span className="text-sm font-medium">Sending...</span>
              </>
            ) : (
              <>
                <span className="text-sm font-medium">Send</span>
                <SendHorizonal size={16} />
              </>
            )}
          </button>
        </div>
      </div>
      
      <p className="text-xs text-gray-400 dark:text-gray-500 mt-2 text-center">
        Press <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-gray-600 dark:text-gray-300">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-gray-600 dark:text-gray-300">Shift + Enter</kbd> for new line
      </p>
    </div>
  );
}
