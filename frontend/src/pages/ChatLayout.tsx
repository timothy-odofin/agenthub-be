import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Sidebar from "@/components/chat/Sidebar";
import MainChat from "@/components/chat/MainChatMessage";
import ChatInput from "@/components/chat/MainChatInput";
import ChatTopbar from "../components/chat/ChatTopbar"
import EnhancedShareModal from "@/components/modals/EnhancedShareModal";
import AddPeopleModal from "@/components/modals/AddPeopleModal";
import ConfirmationModal from "@/components/modals/ConfirmationModal";
import ModelCapabilities from "../components/ModelCapabilities";

import {
  getChatSessions,
  sendChatMessage,
  getSessionMessages,
  updateSessionTitle,
  deleteSession,
  getLLMProviders,
} from "@/api/chat";
import { API_BASE_URL } from "@/api/axiosConfig";

import type { ChatSession, ChatMessage, ModelVersion } from "@/types";

export default function ChatLayout() {
  const { sessionId: urlSessionId } = useParams<{ sessionId?: string }>();
  const navigate = useNavigate();
  
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isNewSession, setIsNewSession] = useState<boolean>(true);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isLoadingSession, setIsLoadingSession] = useState<boolean>(false);
  const [loadingSessionId, setLoadingSessionId] = useState<string | null>(null);
  const [isDeletingSession, setIsDeletingSession] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // Capabilities state
  const [capabilities, setCapabilities] = useState<any[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [isLoadingCapabilities, setIsLoadingCapabilities] = useState<boolean>(false);
  const [capabilitiesError, setCapabilitiesError] = useState<string | null>(null);
  
  // Capability selection state
  const [selectedCapability, setSelectedCapability] = useState<{
    id: string;
    defaultPrompt: string;
  } | null>(null);
  
  // Modal states
  const [shareModalOpen, setShareModalOpen] = useState<boolean>(false);
  const [addPeopleModalOpen, setAddPeopleModalOpen] = useState<boolean>(false);
  const [shareSessionId, setShareSessionId] = useState<string>("");
  const [shareSessionTitle, setShareSessionTitle] = useState<string>("");
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState<boolean>(false);
  const [sessionToDelete, setSessionToDelete] = useState<string | null>(null);
  
  // Topbar state
  const [isPinned, setIsPinned] = useState<boolean>(false);

  // LLM Providers state
  const [providers, setProviders] = useState<ModelVersion[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [selectedModelVersion, setSelectedModelVersion] = useState<string>("");

  useEffect(() => {
    console.log('=== ChatLayout mounted - Starting initial load ===');
    loadSessions();
    loadCapabilities();
    loadProviders();
  }, []);

  // Load session from URL parameter if present
  useEffect(() => {
    if (urlSessionId && urlSessionId !== currentSession) {
      openSession(urlSessionId);
    }
  }, [urlSessionId]);

  const loadCapabilities = async () => {
    try {
      console.log('🔵 Loading capabilities from API...');
      console.log('🔵 Token:', localStorage.getItem('access_token') ? 'exists' : 'missing');
      setIsLoadingCapabilities(true);
      setCapabilitiesError(null);
      
      const res = await fetch(`${API_BASE_URL}/api/v1/chat/capabilities`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('🔵 Response status:', res.status);
      const data = await res.json();
      console.log('🔵 Capabilities loaded:', data);
      
      if (data.success) {
        setCapabilities(data.capabilities);
        setCategories(data.categories);
        console.log('✅ Capabilities set successfully');
      } else {
        console.error('❌ API returned success=false');
        setCapabilitiesError('Failed to load capabilities');
      }
    } catch (err) {
      console.error('❌ Failed to load capabilities:', err);
      setCapabilitiesError('Failed to load capabilities');
    } finally {
      setIsLoadingCapabilities(false);
      console.log('🔵 Loading complete');
    }
  };

  const loadSessions = async () => {
    try {
      const res = await getChatSessions(0, 20); // Page is 0-based
      if (res.data?.success) {
        setSessions(res.data.sessions);
      }
    } catch (err) {
      console.error("Failed to load sessions:", err);
    }
  };

  const loadProviders = async () => {
    try{
      const res = await getLLMProviders();
      
      if (res.data?.success && res.data.providers) {
        setProviders(res.data.providers);
        
        // Set default provider and model
        const defaultProvider = res.data.providers.find((p: ModelVersion) => p.is_default) || res.data.providers[0];
        if (defaultProvider) {
          setSelectedProvider(defaultProvider.name);
          setSelectedModelVersion(defaultProvider.default_model);
        }
        
        console.log('✅ Providers loaded successfully:', res.data.providers);
      }
    } catch (err) {
      console.error('❌ Failed to load providers:', err);
      // Set fallback to empty array to avoid breaking the UI
      setProviders([]);
    }
  };

  const startNewChat = () => {
    // Reset to empty state - session will be created on first message
    setCurrentSession(null);
    setMessages([]);
    setIsNewSession(true);
    setError(null);
    
    // Navigate to base dashboard URL (remove session ID from URL)
    navigate('/main-dashboard');
  };

  const openSession = async (sessionId: string) => {
    try {
      setIsLoadingSession(true);
      setLoadingSessionId(sessionId);
      setError(null);
      
      // Update URL with session ID
      if (sessionId !== urlSessionId) {
        navigate(`/main-dashboard/${sessionId}`, { replace: true });
      }
      
      const res = await getSessionMessages(sessionId);
      
      if (res.data?.success) {
        setCurrentSession(sessionId);
        setMessages(res.data.messages || []);
        setIsNewSession(false);
      } else {
        setError("Failed to load session messages");
      }
    } catch (err) {
      console.error("Failed to load session:", err);
      setError("Failed to load conversation. Please try again.");
    } finally {
      setIsLoadingSession(false);
      setLoadingSessionId(null);
    }
  };

  const handleRenameSession = async (sessionId: string, newTitle: string) => {
    try {
      const res = await updateSessionTitle(sessionId, newTitle);
      
      if (res.data?.success) {
        // Update session in local state
        setSessions((prev) =>
          prev.map((s) =>
            s.session_id === sessionId ? { ...s, title: newTitle } : s
          )
        );
      } else {
        setError("Failed to rename session");
      }
    } catch (err) {
      console.error("Failed to rename session:", err);
      setError("Failed to rename conversation. Please try again.");
    }
  };

  const handleShareSession = (sessionId: string) => {
    const session = sessions.find((s) => s.session_id === sessionId);
    if (session) {
      setShareSessionId(sessionId);
      setShareSessionTitle(session.title || "Untitled Chat");
      setShareModalOpen(true);
    }
  };

  // Topbar handlers
  const handleTopbarShare = () => {
    if (currentSession) {
      const session = sessions.find((s) => s.session_id === currentSession);
      if (session) {
        setShareSessionId(currentSession);
        setShareSessionTitle(session.title || "Untitled Chat");
        setShareModalOpen(true);
      }
    }
  };

  const handleAddPeople = () => {
    if (currentSession) {
      const session = sessions.find((s) => s.session_id === currentSession);
      if (session) {
        setShareSessionId(currentSession);
        setShareSessionTitle(session.title || "Untitled Chat");
        setAddPeopleModalOpen(true);
      }
    }
  };

  const handleDelete = () => {
    if (!currentSession) return;
    setSessionToDelete(currentSession);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteSession = (sessionId: string) => {
    setSessionToDelete(sessionId);
    setDeleteConfirmOpen(true);
  };

  const confirmDelete = async () => {
    if (!sessionToDelete) return;

    try {
      setIsDeletingSession(true);
      setError(null);

      const res = await deleteSession(sessionToDelete);

      if (res.data?.success) {
        // Remove session from local state
        setSessions((prev) => prev.filter((s) => s.session_id !== sessionToDelete));
        
        // If deleting current session, clear it
        if (sessionToDelete === currentSession) {
          setCurrentSession(null);
          setMessages([]);
          setIsNewSession(true);
          navigate("/main-dashboard", { replace: true });
        }
        
        console.log("✅ Session deleted successfully:", res.data);
        
        // Close modal
        setDeleteConfirmOpen(false);
        setSessionToDelete(null);
      } else {
        setError("Failed to delete conversation");
      }
    } catch (err: any) {
      console.error("❌ Failed to delete session:", err);
      const errorMsg = err.response?.data?.message || 
                       err.response?.data?.detail || 
                       "Failed to delete conversation. Please try again.";
      setError(errorMsg);
    } finally {
      setIsDeletingSession(false);
    }
  };

  const handleArchive = () => {
    if (currentSession) {
      // Future: API call to archive session
      console.log("Archiving session:", currentSession);
      setError("Archive functionality pending backend API");
    }
  };

  const handlePin = () => {
    setIsPinned(!isPinned);
    // Future: API call to pin/unpin session
    console.log("Pin toggled:", !isPinned);
  };

  const handleCapabilityClick = (capabilityId: string, defaultPrompt: string) => {
    // Store the selected capability
    setSelectedCapability({ id: capabilityId, defaultPrompt });
  };

  const handleSelectPrompt = async (prompt: string, _capabilityId: string) => {
    // Send the selected prompt as a message
    await handleSend(prompt);
  };

  const handleSend = async (text: string) => {
    if (!text.trim() && !selectedCapability) return;

    try {
      setIsLoading(true);
      setError(null);

      // Determine the message to send
      let messageToSend = text.trim();
      let metadata: any = undefined;

      // Scenario 1: User clicked capability card directly (no typed message)
      if (selectedCapability && !text.trim()) {
        messageToSend = selectedCapability.defaultPrompt;
        metadata = {
          capability_id: selectedCapability.id,
          is_capability_selection: true,
        };
      }
      // Scenario 2: User typed message AND selected a capability
      else if (selectedCapability && text.trim()) {
        messageToSend = text.trim();
        metadata = {
          capability_id: selectedCapability.id,
          is_capability_selection: true,
        };
      }
      // Scenario 3: Normal chat (no capability selected)
      // metadata remains undefined

      // Clear selected capability after using it
      setSelectedCapability(null);

      // Add user message immediately for better UX
      const userMessage: ChatMessage = {
        role: "user",
        content: messageToSend,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Send message with current session_id (null for first message)
      const payload: any = {
        message: messageToSend,
        session_id: currentSession,
        provider: selectedProvider,
        model: selectedModelVersion,
      };

      // Only include metadata if it exists (Scenarios 1 & 2)
      if (metadata) {
        payload.metadata = metadata;
      }

      const res = await sendChatMessage(payload);

      if (res.data?.success) {
        // Capture session_id from response (important for first message)
        if (!currentSession && res.data.session_id) {
          const newSessionId = res.data.session_id;
          setCurrentSession(newSessionId);
          
          // Update URL with new session ID
          navigate(`/main-dashboard/${newSessionId}`, { replace: true });
        }

        // Add AI response
        const aiMessage: ChatMessage = {
          role: "assistant",
          content: res.data.message,
          timestamp: res.data.timestamp,
        };
        setMessages((prev) => [...prev, aiMessage]);

        // Refresh session list if this was a new session
        if (isNewSession) {
          await loadSessions();
          setIsNewSession(false);
        }
      } else {
        // Handle API error response
        const errorMsg = res.data?.errors?.join(", ") || "Failed to send message";
        setError(errorMsg);
        // Remove the optimistically added user message
        setMessages((prev) => prev.slice(0, -1));
      }
    } catch (err: any) {
      console.error("Failed to send message:", err);
      setError(err.response?.data?.detail || "Failed to send message. Please try again.");
      // Remove the optimistically added user message
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const user = JSON.parse(localStorage.getItem("user") || "{}");
  const userName = user?.name || "there";

  const isEmpty = messages.length === 0;

  return (
    <div className="flex h-screen">
      <Sidebar
        sessions={sessions}
        currentSession={currentSession}
        onNewChat={startNewChat}
        onSelectSession={openSession}
        onRenameSession={handleRenameSession}
        onShareSession={handleShareSession}
        onDeleteSession={handleDeleteSession}
        loadingSessionId={loadingSessionId}
        isDeletingSession={isDeletingSession}
      />

      {/* Modals */}
      <EnhancedShareModal
        isOpen={shareModalOpen}
        onClose={() => setShareModalOpen(false)}
        sessionId={shareSessionId}
        sessionTitle={shareSessionTitle}
      />

      <AddPeopleModal
        isOpen={addPeopleModalOpen}
        onClose={() => setAddPeopleModalOpen(false)}
        sessionId={shareSessionId}
        sessionTitle={shareSessionTitle}
      />

      <ConfirmationModal
        isOpen={deleteConfirmOpen}
        onClose={() => {
          setDeleteConfirmOpen(false);
          setSessionToDelete(null);
        }}
        onConfirm={confirmDelete}
        title="Delete Conversation"
        message="Are you sure you want to delete this conversation? This action cannot be undone and all messages will be permanently removed."
        confirmText="Delete"
        cancelText="Cancel"
        isDestructive={true}
        isLoading={isDeletingSession}
      />

      <div className="flex flex-col flex-1 bg-gray-50 dark:bg-gray-900">
        {/* Topbar - Only show when session is active */}
        {currentSession && (
          <ChatTopbar
            sessionTitle={
              sessions.find((s) => s.session_id === currentSession)?.title || "Untitled Chat"
            }
            selectedModel={selectedModelVersion}
            selectedProvider={selectedProvider}
            providers={providers}
            onModelChange={setSelectedModelVersion}
            onProviderChange={setSelectedProvider}
            onShare={handleTopbarShare}
            onAddPeople={handleAddPeople}
            onDelete={handleDelete}
            onArchive={handleArchive}
            onPin={handlePin}
            isPinned={isPinned}
            isDeleting={isDeletingSession}
          />
        )}

        {/* Error Banner */}
        {error && (
          <div className="bg-red-50 border-b border-red-200 px-4 py-3 text-red-800 text-sm">
            <div className="max-w-3xl mx-auto flex items-center justify-between">
              <span>{error}</span>
              <button
                onClick={() => setError(null)}
                className="text-red-600 hover:text-red-800 font-semibold"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* MAIN CONTENT AREA */}
        {isEmpty ? (
          /* New Chat: Show Capabilities */
          <div className="flex-1 overflow-y-auto">
            {/* Model Capabilities - Show when no messages */}
            <ModelCapabilities 
              onSelectPrompt={handleSelectPrompt}
              onCapabilityClick={handleCapabilityClick}
              capabilities={capabilities}
              categories={categories}
              loading={isLoadingCapabilities}
              error={capabilitiesError}
              onRetry={loadCapabilities}
            />
            
            {/* Centered Input */}
            <div className="flex justify-center items-center py-10">
              <div className="w-full max-w-5xl px-6">
                <ChatInput 
                  onSend={handleSend} 
                  isEmpty 
                  isLoading={isLoading}
                />
              </div>
            </div>
          </div>
        ) : (
          /* Existing Chat: Show Messages */
          <>
            <MainChat 
              messages={messages} 
              userName={userName} 
              isLoading={isLoading} 
              isLoadingSession={isLoadingSession}
            />
            <div className="sticky bottom-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 p-4">
              <div className="w-full max-w-5xl mx-auto px-6">
                <ChatInput 
                  onSend={handleSend} 
                  isEmpty={false} 
                  isLoading={isLoading}
                />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
