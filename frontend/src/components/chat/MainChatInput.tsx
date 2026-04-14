import { Mic, MicOff, Plus, SendHorizonal } from "lucide-react";
import React, { useCallback, useEffect, useRef, useState } from "react";
import McpServerPicker from "./McpServerPicker";
import type { McpGroupInfo } from "@/types";

interface ChatInputProps {
  onSend: (msg: string) => void;
  isEmpty: boolean;
  isLoading?: boolean;
  mcpGroups?: McpGroupInfo[];
  selectedServerIds?: Set<string>;
  onServerSelectionChange?: (ids: Set<string>) => void;
}

export default function ChatInput({
  onSend,
  isLoading = false,
  mcpGroups = [],
  selectedServerIds = new Set(),
  onServerSelectionChange,
}: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const plusBtnRef = useRef<HTMLButtonElement | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const MAX_HEIGHT = 160;

  // Voice input state
  const [isListening, setIsListening] = useState(false);
  const [isVoiceSupported, setIsVoiceSupported] = useState(false);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const sendMessageRef = useRef<((text: string) => void) | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);

    // Stop listening if user starts typing manually
    if (isListening) {
      stopListening();
    }

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, MAX_HEIGHT) + "px";
    }
  };

  const sendMessage = useCallback(
    (textOverride?: string) => {
      const text = textOverride ?? input;
      if (!text.trim() || isLoading) return;
      onSend(text.trim());
      setInput("");

      if (textareaRef.current) textareaRef.current.style.height = "auto";
    },
    [input, isLoading, onSend]
  );

  // Keep sendMessageRef in sync so the recognition callback always has the latest
  useEffect(() => {
    sendMessageRef.current = sendMessage;
  }, [sendMessage]);

  // Initialize Web Speech API
  useEffect(() => {
    const SpeechRecognitionApi =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognitionApi) return;

    setIsVoiceSupported(true);

    const recognition = new SpeechRecognitionApi();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onstart = () => setIsListening(true);

    recognition.onresult = (e: SpeechRecognitionEvent) => {
      const transcript = Array.from({ length: e.results.length })
        .map((_, i) => e.results[i][0].transcript)
        .join("");

      setIsListening(false);
      recognition.stop();

      // Put transcript in the input field
      setInput(transcript);

      // Auto-send after a short delay so the user sees the transcript
      if (transcript.trim() && sendMessageRef.current) {
        setTimeout(() => sendMessageRef.current?.(transcript), 300);
      }
    };

    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);

    recognitionRef.current = recognition;

    return () => {
      recognitionRef.current?.abort();
    };
  }, []);

  const stopListening = () => {
    recognitionRef.current?.stop();
    setIsListening(false);
  };

  const toggleListening = () => {
    if (isLoading) return;
    if (isListening) {
      stopListening();
    } else {
      recognitionRef.current?.start();
    }
  };

  const selectionCount = selectedServerIds.size;

  return (
    <div className="relative">
      {/* MCP Server Picker popup */}
      {pickerOpen && mcpGroups.length > 0 && (
        <McpServerPicker
          groups={mcpGroups}
          selected={selectedServerIds}
          onApply={(ids) => onServerSelectionChange?.(ids)}
          onClose={() => setPickerOpen(false)}
          anchorRef={plusBtnRef}
        />
      )}

      {/* Chat Input */}
      <div className="flex flex-col gap-2 border-2 border-gray-200 dark:border-gray-700 rounded-2xl p-3 shadow-lg bg-white dark:bg-gray-800 hover:border-blue-300 dark:hover:border-blue-600 transition-colors focus-within:border-blue-500 dark:focus-within:border-blue-500 focus-within:shadow-xl">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleChange}
          placeholder={
            isListening ? "Listening..." : "Type or speak your message..."
          }
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
          <div className="flex items-center gap-1">
            {/* Plus / MCP server picker button */}
            <div className="relative">
              <button
                ref={plusBtnRef}
                type="button"
                onClick={() => setPickerOpen((v) => !v)}
                title="Select MCP servers"
                className={`relative rounded-full p-2 transition-all ${
                  pickerOpen
                    ? "text-blue-600 bg-blue-50 dark:bg-blue-900/30"
                    : "text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                }`}
              >
                <Plus size={18} />
                {/* Badge showing count of selected servers */}
                {selectionCount > 0 && (
                  <span className="absolute -top-1 -right-1 min-w-[16px] h-4 px-1 bg-blue-600 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                    {selectionCount}
                  </span>
                )}
              </button>
            </div>

            {isVoiceSupported && (
              <button
                type="button"
                onClick={toggleListening}
                disabled={isLoading}
                className={`rounded-full p-2 transition-all ${
                  isListening
                    ? "text-red-500 bg-red-50 dark:bg-red-900/30 hover:bg-red-100 dark:hover:bg-red-900/50 animate-pulse"
                    : "text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
                title={isListening ? "Stop listening" : "Voice input"}
              >
                {isListening ? <MicOff size={18} /> : <Mic size={18} />}
              </button>
            )}

            {/* Show selected server chips when servers are selected */}
            {selectionCount > 0 && (
              <div className="flex items-center gap-1 ml-1 flex-wrap max-w-xs">
                {Array.from(selectedServerIds).map((id) => (
                  <span
                    key={id}
                    className="inline-flex items-center gap-1 text-[10px] bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300 px-2 py-0.5 rounded-full"
                  >
                    {id}
                    <button
                      onClick={() => {
                        const next = new Set(selectedServerIds);
                        next.delete(id);
                        onServerSelectionChange?.(next);
                      }}
                      className="hover:text-blue-900 dark:hover:text-blue-100"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || isLoading || isListening}
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

      {/* Listening indicator */}
      {isListening && (
        <div className="flex items-center justify-center gap-2 mt-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
          </span>
          <p className="text-xs text-red-500 dark:text-red-400 font-medium">
            Listening... speak now
          </p>
          <button
            onClick={stopListening}
            className="text-xs text-red-500 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 underline"
          >
            Cancel
          </button>
        </div>
      )}

      {!isListening && (
        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2 text-center">
          Press <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-gray-600 dark:text-gray-300">Enter</kbd> to send,{" "}
          <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-gray-600 dark:text-gray-300">Shift + Enter</kbd> for new line
          {isVoiceSupported && ", or click 🎤 to speak"}
        </p>
      )}
    </div>
  );
}
