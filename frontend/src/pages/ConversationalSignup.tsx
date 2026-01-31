import { useEffect, useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { Bot, User, Loader2, ArrowRight, Sparkles } from "lucide-react";
import { SignupProgress } from "@/components/SignupProgress";
import { startConversationAuth, conversationalAuth } from "@/api/auth";

interface Message {
  id: string;
  role: "assistant" | "user";
  content: string;
  timestamp: Date;
}

interface ConversationState {
  sessionId: string | null;
  currentStep: string;
  nextStep: string;
  progress: number;
  fieldsRemaining: number;
  isValid: boolean;
  validationError: string | null;
}

export default function ConversationalSignup() {
  const navigate = useNavigate();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const hasInitialized = useRef<boolean>(false);

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isTyping, setIsTyping] = useState<boolean>(false);
  const [isInitializing, setIsInitializing] = useState<boolean>(true);
  const [conversationState, setConversationState] = useState<ConversationState>({
    sessionId: null,
    currentStep: "start",
    nextStep: "start",
    progress: 0,
    fieldsRemaining: 5,
    isValid: true,
    validationError: null,
  });

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  // Focus input when ready for user input
  useEffect(() => {
    if (!isLoading && !isTyping && !isInitializing) {
      inputRef.current?.focus();
    }
  }, [isLoading, isTyping, isInitializing]);

  // Start conversation on mount
  useEffect(() => {
    if (!hasInitialized.current) {
      hasInitialized.current = true;
      startConversation();
    }
  }, []);

  const startConversation = async () => {
    setIsInitializing(true);
    try {
      const res = await startConversationAuth();
      const data = res.data;

      setConversationState({
        sessionId: data.session_id,
        currentStep: data.next_step,
        nextStep: data.next_step,
        progress: data.progress_percentage || 0,
        fieldsRemaining: data.fields_remaining || 5,
        isValid: true,
        validationError: null,
      });

      // Add bot's welcome message with typing effect
      addBotMessage(data.message);
      setIsInitializing(false);
    } catch (err: any) {
      console.error("Failed to start conversation:", err);
      addBotMessage(
        "Sorry, I'm having trouble starting the signup process. Please try again later."
      );
      setIsInitializing(false);
    }
  };

  const addBotMessage = (content: string) => {
    setIsTyping(true);
    setTimeout(() => {
      const newMessage: Message = {
        id: `bot-${Date.now()}`,
        role: "assistant",
        content,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, newMessage]);
      setIsTyping(false);
    }, 800);
  };

  const addUserMessage = (content: string) => {
    // Hide password in display if current step is password
    const displayContent = conversationState.currentStep === "password" 
      ? "••••••••" 
      : content;
    
    const newMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: displayContent,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userInput = input.trim();
    setInput("");
    addUserMessage(userInput);
    setIsLoading(true);

    try {
      const payload = {
        message: userInput,
        session_id: conversationState.sessionId,
        current_step: conversationState.currentStep,
      };

      const res = await conversationalAuth(payload);
      const data = res.data;

      // Update conversation state
      setConversationState({
        sessionId: data.session_id,
        currentStep: data.next_step,
        nextStep: data.next_step,
        progress: data.progress_percentage || 0,
        fieldsRemaining: data.fields_remaining || 0,
        isValid: data.is_valid ?? true,
        validationError: data.validation_error || null,
      });

      // Add bot response
      addBotMessage(data.message);

      // Check if signup is complete
      if (data.next_step === "complete" && data.access_token) {
        setTimeout(() => {
          // Store tokens
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          localStorage.setItem("user", JSON.stringify({ user_id: data.user_id }));

          // Redirect to main dashboard
          navigate("/main-dashboard");
        }, 2000);
      }

      setIsLoading(false);
    } catch (err: any) {
      console.error("Failed to send message:", err);
      const errorMessage =
        err.response?.data?.message ||
        "Something went wrong. Please try again.";
      addBotMessage(errorMessage);
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const getPlaceholder = () => {
    switch (conversationState.currentStep) {
      case "email":
        return "Type your email address...";
      case "username":
        return "Choose a username...";
      case "password":
        return "Create a strong password...";
      case "firstname":
        return "Type your first name...";
      case "lastname":
        return "Type your last name...";
      default:
        return "Type your message...";
    }
  };

  const isComplete = conversationState.nextStep === "complete";

  return (
    <div className="h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex flex-col overflow-hidden">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 shadow-sm px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center shadow-lg">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">AgentHub</h1>
            <p className="text-xs text-gray-500">Let's create your account</p>
          </div>
        </div>
        <button
          onClick={() => navigate("/")}
          className="text-sm text-gray-600 hover:text-gray-900 transition-colors"
        >
          Already have an account?{" "}
          <span className="text-blue-600 font-semibold">Sign in</span>
        </button>
      </header>

      {/* Progress Bar */}
      {!isComplete && (
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <SignupProgress
            progress={conversationState.progress}
            fieldsRemaining={conversationState.fieldsRemaining}
            currentStep={conversationState.currentStep}
          />
        </div>
      )}

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex items-start gap-4 ${
                message.role === "user" ? "flex-row-reverse" : ""
              }`}
            >
              {/* Avatar */}
              <div
                className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                  message.role === "assistant"
                    ? "bg-gradient-to-br from-blue-600 to-purple-600 shadow-lg"
                    : "bg-gray-200"
                }`}
              >
                {message.role === "assistant" ? (
                  <Bot className="w-5 h-5 text-white" />
                ) : (
                  <User className="w-5 h-5 text-gray-700" />
                )}
              </div>

              {/* Message Bubble */}
              <div
                className={`flex-1 max-w-[80%] ${
                  message.role === "user" ? "text-right" : ""
                }`}
              >
                <div
                  className={`inline-block px-5 py-3 rounded-2xl ${
                    message.role === "assistant"
                      ? "bg-white shadow-md border border-gray-200 text-gray-800"
                      : "bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg"
                  }`}
                >
                  <p className="text-[15px] leading-relaxed whitespace-pre-wrap">
                    {message.content}
                  </p>
                </div>
                <p className="text-xs text-gray-400 mt-1 px-1">
                  {message.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </p>
              </div>
            </div>
          ))}

          {/* Typing Indicator - Bot is typing */}
          {isTyping && (
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center shadow-lg">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-white shadow-md border border-gray-200 rounded-2xl px-5 py-3">
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}

          {/* Processing Indicator - Waiting for backend response */}
          {isLoading && !isTyping && (
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center shadow-lg">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-white shadow-md border border-gray-200 rounded-2xl px-5 py-3">
                <div className="flex gap-1.5 items-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}

          {/* Validation Error */}
          {!conversationState.isValid && conversationState.validationError && (
            <div className="flex justify-center">
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded-lg text-sm">
                {conversationState.validationError}
              </div>
            </div>
          )}

          {/* Completion Message */}
          {isComplete && (
            <div className="flex justify-center">
              <div className="bg-green-50 border border-green-200 text-green-700 px-6 py-4 rounded-xl text-center shadow-lg">
                <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <p className="font-semibold text-lg">Account created successfully!</p>
                <p className="text-sm mt-1">Redirecting to your dashboard...</p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      {!isComplete && (
        <footer className="bg-white border-t border-gray-200 px-4 py-4">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
            <div className="flex items-center gap-3 bg-gray-50 border-2 border-gray-200 rounded-2xl px-4 py-2 focus-within:border-blue-500 transition-colors">
              <input
                ref={inputRef}
                type={conversationState.currentStep === "password" ? "password" : "text"}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={getPlaceholder()}
                disabled={isLoading}
                className="flex-1 bg-transparent outline-none text-gray-900 placeholder-gray-400 text-[15px] disabled:opacity-50"
              />
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 flex items-center justify-center hover:shadow-lg transition-all disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <Loader2 className="w-5 h-5 text-white animate-spin" />
                ) : (
                  <ArrowRight className="w-5 h-5 text-white" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-400 text-center mt-2">
              Press Enter to send • Your data is encrypted and secure
            </p>
          </form>
        </footer>
      )}
    </div>
  );
}
