interface SidebarProps {
  sessions: any[];
  currentSession: string | null;
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  onRenameSession: (id: string, newTitle: string) => Promise<void>;
  onShareSession: (id: string) => void;
  onDeleteSession?: (id: string) => void;
  loadingSessionId?: string | null;
  isDeletingSession?: boolean;
}

import { Loader2, MessageSquare, Plus, Edit2, Share2, MoreVertical, LogOut, Trash2 } from "lucide-react";
import { useState, useRef, useEffect } from "react";

export default function Sidebar({
  sessions,
  currentSession,
  onNewChat,
  onSelectSession,
  onRenameSession,
  onShareSession,
  onDeleteSession,
  loadingSessionId = null,
  isDeletingSession = false,
}: SidebarProps) {
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when editing starts
  useEffect(() => {
    if (editingId && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editingId]);

  const handleStartEdit = (session: any, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingId(session.session_id);
    setEditTitle(session.title || "Untitled Chat");
    setMenuOpenId(null);
  };

  const handleSaveEdit = async (sessionId: string) => {
    if (editTitle.trim() && editTitle !== sessions.find(s => s.session_id === sessionId)?.title) {
      await onRenameSession(sessionId, editTitle.trim());
    }
    setEditingId(null);
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditTitle("");
  };

  const handleKeyDown = (e: React.KeyboardEvent, sessionId: string) => {
    if (e.key === "Enter") {
      handleSaveEdit(sessionId);
    } else if (e.key === "Escape") {
      handleCancelEdit();
    }
  };

  const handleShare = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    onShareSession(sessionId);
    setMenuOpenId(null);
  };

  const handleDelete = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDeleteSession) {
      onDeleteSession(sessionId);
    }
    setMenuOpenId(null);
  };

  const toggleMenu = (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setMenuOpenId(menuOpenId === sessionId ? null : sessionId);
  };

  return (
    <aside className="w-[280px] hidden md:flex flex-col border-r border-gray-200 bg-white h-full shrink-0">
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex gap-3 items-center mb-4">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <MessageSquare className="w-5 h-5 text-white" />
            </div>
            <div className="flex flex-col">
              <h1 className="text-gray-900 text-base font-semibold">
                AgentHub
              </h1>
              <p className="text-gray-500 text-xs">
                AI Assistant
              </p>
            </div>
          </div>
          
          {/* New Chat Button */}
          <button  
            onClick={onNewChat} 
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-sm hover:shadow-md group"
          >
            <Plus className="w-4 h-4 group-hover:rotate-90 transition-transform" />
            <span className="text-sm font-medium">New Chat</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-4">
            <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-2">
              Recent Chats
            </div>
            
            <nav className="flex flex-col gap-1">
              {sessions.length === 0 ? (
                <div className="text-center py-8">
                  <MessageSquare className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-400">No conversations yet</p>
                </div>
              ) : (
                sessions.map((s) => (
                  <div
                    key={s.session_id}
                    className={`flex items-start gap-2 px-3 py-3 rounded-lg transition-all relative group ${
                      loadingSessionId === s.session_id
                        ? "bg-blue-50 opacity-60 cursor-wait"
                        : currentSession === s.session_id 
                        ? "bg-blue-50 hover:bg-blue-100 border-l-2 border-blue-600" 
                        : "hover:bg-gray-100 hover:border-l-2 hover:border-gray-300"
                    }`}
                  >
                    <button 
                      className="flex items-start gap-3 flex-1 min-w-0 text-left"
                      onClick={() => onSelectSession(s.session_id)}
                      disabled={loadingSessionId !== null || editingId === s.session_id}
                    >
                      <div className="flex-1 min-w-0">
                        {editingId === s.session_id ? (
                          <input
                            ref={inputRef}
                            type="text"
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            onBlur={() => handleSaveEdit(s.session_id)}
                            onKeyDown={(e) => handleKeyDown(e, s.session_id)}
                            className="w-full px-2 py-1 text-sm font-medium border border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            onClick={(e) => e.stopPropagation()}
                          />
                        ) : (
                          <p className={`text-sm font-medium truncate ${
                            currentSession === s.session_id ? "text-blue-900" : "text-gray-700"
                          }`}>
                            {s.title || "Untitled Chat"}
                          </p>
                        )}
                        
                        {s.last_message_at && (
                          <p className="text-xs text-gray-400 mt-1">
                            {new Date(s.last_message_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                    </button>

                    {/* Actions Menu */}
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      {loadingSessionId === s.session_id ? (
                        <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                      ) : (
                        <>
                          <button
                            onClick={(e) => handleStartEdit(s, e)}
                            className="p-1.5 rounded hover:bg-white hover:shadow-sm transition-all"
                            title="Rename"
                          >
                            <Edit2 className="w-3.5 h-3.5 text-gray-500 hover:text-blue-600" />
                          </button>
                          <button
                            onClick={(e) => handleShare(s.session_id, e)}
                            className="p-1.5 rounded hover:bg-white hover:shadow-sm transition-all"
                            title="Share"
                          >
                            <Share2 className="w-3.5 h-3.5 text-gray-500 hover:text-green-600" />
                          </button>
                          <button
                            onClick={(e) => handleDelete(s.session_id, e)}
                            className="p-1.5 rounded hover:bg-white hover:shadow-sm transition-all"
                            title="Delete"
                            disabled={isDeletingSession && currentSession === s.session_id}
                          >
                            {isDeletingSession && currentSession === s.session_id ? (
                              <Loader2 className="w-3.5 h-3.5 text-red-600 animate-spin" />
                            ) : (
                              <Trash2 className="w-3.5 h-3.5 text-gray-500 hover:text-red-600" />
                            )}
                          </button>
                          <button
                            onClick={(e) => toggleMenu(s.session_id, e)}
                            className="p-1.5 rounded hover:bg-white hover:shadow-sm transition-all"
                            title="More"
                          >
                            <MoreVertical className="w-3.5 h-3.5 text-gray-500" />
                          </button>
                        </>
                      )}
                    </div>

                    {/* Dropdown Menu */}
                    {menuOpenId === s.session_id && (
                      <div className="absolute right-2 top-12 z-10 bg-white border border-gray-200 rounded-lg shadow-lg py-1 w-40">
                        <button
                          onClick={(e) => handleStartEdit(s, e)}
                          className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                        >
                          <Edit2 className="w-4 h-4" />
                          Rename
                        </button>
                        <button
                          onClick={(e) => handleShare(s.session_id, e)}
                          className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
                        >
                          <Share2 className="w-4 h-4" />
                          Share
                        </button>
                        <div className="border-t border-gray-100 my-1"></div>
                        <button
                          onClick={(e) => handleDelete(s.session_id, e)}
                          disabled={isDeletingSession && currentSession === s.session_id}
                          className="w-full px-4 py-2 text-left text-sm hover:bg-red-50 flex items-center gap-2 text-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isDeletingSession && currentSession === s.session_id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                          {isDeletingSession && currentSession === s.session_id ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    )}
                  </div>
                ))
              )}
            </nav>
          </div>
        </div>

        {/* Footer */}
        <div className="flex flex-col gap-2 border-t border-gray-200 p-4">
          {/* User Info */}
          {(() => {
            try {
              const user = JSON.parse(localStorage.getItem("user") || "{}");
              
              // Build display name from available fields
              const displayName = user.name || 
                                  (user.firstname && user.lastname ? `${user.firstname} ${user.lastname}` : null) ||
                                  user.firstname || 
                                  user.username;
              
              const displayEmail = user.email || user.username;
              
              if (displayName || displayEmail) {
                return (
                  <div className="px-3 py-2 mb-1">
                    {displayName && (
                      <p className="text-sm font-medium text-gray-700">{displayName}</p>
                    )}
                    {displayEmail && (
                      <p className="text-xs text-gray-500">{displayEmail}</p>
                    )}
                  </div>
                );
              }
            } catch (e) {
              return null;
            }
          })()}
          
          <button 
            onClick={() => {
              localStorage.removeItem("access_token");
              localStorage.removeItem("refresh_token");
              localStorage.removeItem("user");
              window.location.href = "/";
            }}
            className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-red-50 transition-colors text-red-600 hover:text-red-700"
          >
            <LogOut className="w-4 h-4" />
            <span className="text-sm font-medium">Logout</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
