import { useEffect, useRef, useState } from "react";
import { Bot, User, Copy, ThumbsUp, ThumbsDown, RotateCcw, Edit2, Check } from "lucide-react";
import LinkifiedText from "../common/LinkifiedText";
import MarkdownRenderer from "../MarkdownRenderer";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  id?: string;
}

interface MainChatProps {
  messages: ChatMessage[];
  userName: string;
  isLoading?: boolean;
  isLoadingSession?: boolean;
  onRetry?: (messageIndex: number) => void;
  onEditMessage?: (messageIndex: number, newContent: string) => void;
  onFeedback?: (messageIndex: number, feedback: "good" | "bad") => void;
}

/** Tiny icon button used in message action toolbars */
function ActionBtn({
  onClick,
  title,
  children,
  active = false,
  danger = false,
}: {
  onClick: () => void;
  title: string;
  children: React.ReactNode;
  active?: boolean;
  danger?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={`p-1.5 rounded-md transition-all duration-150 ${
        danger
          ? "text-red-400 hover:text-red-600 hover:bg-red-50"
          : active
          ? "text-blue-600 bg-blue-50"
          : "text-gray-400 hover:text-gray-700 hover:bg-gray-100"
      }`}
    >
      {children}
    </button>
  );
}

export default function MainChat({
  messages,
  userName,
  isLoading = false,
  isLoadingSession = false,
  onRetry,
  onEditMessage,
  onFeedback,
}: MainChatProps) {
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Track copy "flash" state per message
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  // Track feedback per message index
  const [feedbackMap, setFeedbackMap] = useState<Record<number, "good" | "bad">>({});
  // Track which user message is being inline-edited
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState("");

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Format timestamp
  const formatTime = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "";
    }
  };

  const handleCopy = (content: string, index: number) => {
    navigator.clipboard.writeText(content).catch(() => {});
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 1500);
  };

  const handleFeedback = (index: number, type: "good" | "bad") => {
    setFeedbackMap((prev) => {
      // Toggle off if already selected
      if (prev[index] === type) {
        const next = { ...prev };
        delete next[index];
        return next;
      }
      return { ...prev, [index]: type };
    });
    onFeedback?.(index, type);
  };

  const startEdit = (index: number, content: string) => {
    setEditingIndex(index);
    setEditDraft(content);
  };

  const commitEdit = (index: number) => {
    const trimmed = editDraft.trim();
    if (trimmed && trimmed !== messages[index].content) {
      onEditMessage?.(index, trimmed);
    }
    setEditingIndex(null);
    setEditDraft("");
  };

  const cancelEdit = () => {
    setEditingIndex(null);
    setEditDraft("");
  };

  // Loading skeleton for session history
  if (isLoadingSession) {
    return (
      <div className="flex-1 overflow-y-auto bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-5xl mx-auto px-6 py-8">
          <div className="flex flex-col items-center justify-center py-12">
            <div className="w-12 h-12 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-4"></div>
            <p className="text-gray-600 text-sm">Loading conversation...</p>
          </div>
          <div className="flex flex-col gap-6 mt-8">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex gap-2 animate-pulse">
                <div className="w-7 h-7 rounded-full bg-gray-200 flex-shrink-0"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                  {i % 2 === 0 && <div className="h-4 bg-gray-200 rounded w-2/3"></div>}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col justify-center items-center text-center px-4 bg-gradient-to-b from-gray-50 to-white">
        <div className="mb-6">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mx-auto mb-4 shadow-lg">
            <Bot className="w-10 h-10 text-white" />
          </div>
        </div>
        <h1 className="text-3xl md:text-4xl font-bold text-gray-800 mb-3">
          Hello, {userName}! 👋
        </h1>
        <p className="text-lg text-gray-600 max-w-md mb-8">
          How can I help you today?
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl">
          <div className="p-4 bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer">
            <p className="text-sm text-gray-700">💡 Explain a concept</p>
          </div>
          <div className="p-4 bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer">
            <p className="text-sm text-gray-700">🔍 Help me research</p>
          </div>
          <div className="p-4 bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer">
            <p className="text-sm text-gray-700">✍️ Write something</p>
          </div>
          <div className="p-4 bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer">
            <p className="text-sm text-gray-700">🤔 Brainstorm ideas</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-5xl mx-auto px-6 py-6 flex flex-col gap-6">
        {messages.map((msg, i) => (
          <div
            key={msg.id || i}
            className={`flex gap-2 animate-fadeIn ${
              msg.role === "user" ? "flex-row-reverse" : "flex-row"
            }`}
          >
            {/* Avatar */}
            <div
              className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center self-start mt-0.5 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : "bg-gradient-to-br from-purple-500 to-blue-600 text-white"
              }`}
            >
              {msg.role === "user" ? (
                <User className="w-3.5 h-3.5" />
              ) : (
                <Bot className="w-3.5 h-3.5" />
              )}
            </div>

            {/* Message Content + Action Bar */}
            <div
              className={`flex flex-col min-w-0 ${
                msg.role === "user" ? "items-end" : "items-start flex-1"
              }`}
            >
              {msg.role === "assistant" ? (
                /* ── Assistant message ── */
                <div className="w-full">
                  <MarkdownRenderer
                    content={msg.content}
                    className="text-[15px] leading-relaxed text-gray-800"
                  />
                  {msg.timestamp && (
                    <span className="text-xs text-gray-400 mt-1 block">
                      {formatTime(msg.timestamp)}
                    </span>
                  )}

                  {/* Assistant action toolbar */}
                  <div className="flex items-center gap-0.5 mt-2">
                    {/* Copy */}
                    <ActionBtn
                      onClick={() => handleCopy(msg.content, i)}
                      title="Copy response"
                      active={copiedIndex === i}
                    >
                      {copiedIndex === i ? (
                        <Check className="w-3.5 h-3.5 text-green-500" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </ActionBtn>

                    {/* Good response */}
                    <ActionBtn
                      onClick={() => handleFeedback(i, "good")}
                      title="Good response"
                      active={feedbackMap[i] === "good"}
                    >
                      <ThumbsUp className="w-3.5 h-3.5" />
                    </ActionBtn>

                    {/* Bad response */}
                    <ActionBtn
                      onClick={() => handleFeedback(i, "bad")}
                      title="Bad response"
                      active={feedbackMap[i] === "bad"}
                      danger={feedbackMap[i] === "bad"}
                    >
                      <ThumbsDown className="w-3.5 h-3.5" />
                    </ActionBtn>

                    {/* Retry / regenerate */}
                    <ActionBtn
                      onClick={() => onRetry?.(i)}
                      title="Retry / regenerate"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                    </ActionBtn>
                  </div>
                </div>
              ) : (
                /* ── User message ── */
                <>
                  {editingIndex === i ? (
                    /* Inline edit mode */
                    <div className="flex flex-col gap-2 w-full max-w-2xl">
                      <textarea
                        className="w-full px-4 py-2.5 rounded-2xl rounded-tr-sm border border-blue-400 bg-white text-gray-800 text-[15px] leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-blue-400 shadow-sm"
                        rows={3}
                        value={editDraft}
                        onChange={(e) => setEditDraft(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            commitEdit(i);
                          }
                          if (e.key === "Escape") cancelEdit();
                        }}
                        autoFocus
                      />
                      <div className="flex gap-2 justify-end">
                        <button
                          onClick={cancelEdit}
                          className="text-xs text-gray-500 hover:text-gray-700 px-3 py-1 rounded-lg border border-gray-200 hover:bg-gray-50 transition-all"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => commitEdit(i)}
                          className="text-xs text-white bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded-lg transition-all"
                        >
                          Send
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="px-4 py-2.5 rounded-2xl shadow-sm bg-blue-600 text-white rounded-tr-sm max-w-2xl">
                      <LinkifiedText
                        content={msg.content}
                        className="text-[15px] leading-relaxed text-white"
                        linkClassName="text-blue-100 hover:text-white decoration-blue-200 hover:decoration-white"
                        showIcon={false}
                      />
                    </div>
                  )}

                  {msg.timestamp && editingIndex !== i && (
                    <span className="text-xs text-gray-400 mt-1 px-1">
                      {formatTime(msg.timestamp)}
                    </span>
                  )}

                  {/* User action toolbar */}
                  {editingIndex !== i && (
                    <div className="flex items-center gap-0.5 mt-1">
                      {/* Edit */}
                      <ActionBtn
                        onClick={() => startEdit(i, msg.content)}
                        title="Edit message"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </ActionBtn>

                      {/* Retry (re-send this user message) */}
                      <ActionBtn
                        onClick={() => onRetry?.(i)}
                        title="Retry"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                      </ActionBtn>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        ))}

        {/* AI Typing Indicator */}
        {isLoading && (
          <div className="flex gap-3 animate-fadeIn">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center text-white">
              <Bot className="w-4 h-4" />
            </div>
            <div className="px-4 py-3 rounded-2xl rounded-tl-sm shadow-sm bg-white border border-gray-200">
              <div className="flex gap-1.5 items-center">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
