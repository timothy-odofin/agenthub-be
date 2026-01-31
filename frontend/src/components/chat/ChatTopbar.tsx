import { useState, useRef, useEffect } from "react";
import { Share2, UserPlus, MoreVertical, ChevronDown, Trash2, Archive, Pin, Sparkles, Loader2, Search, Check } from "lucide-react";
import type { ModelVersion } from "@/types";

interface ChatTopbarProps {
  sessionTitle: string;
  selectedModel: string;
  selectedProvider: string;
  providers: ModelVersion[];
  onModelChange: (model: string) => void;
  onProviderChange: (provider: string) => void;
  onShare: () => void;
  onAddPeople: () => void;
  onDelete: () => void;
  onArchive: () => void;
  onPin: () => void;
  isPinned?: boolean;
  isDeleting?: boolean;
}

// Remove static model data - now using providers from API

export default function ChatTopbar({
  sessionTitle,
  selectedModel,
  selectedProvider,
  providers,
  onModelChange,
  onProviderChange,
  onShare,
  onAddPeople,
  onDelete,
  onArchive,
  onPin,
  isPinned = false,
  isDeleting = false,
}: ChatTopbarProps) {
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [moreMenuOpen, setMoreMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const modelDropdownRef = useRef<HTMLDivElement>(null);
  const moreMenuRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        modelDropdownRef.current &&
        !modelDropdownRef.current.contains(event.target as Node)
      ) {
        setModelDropdownOpen(false);
        setSearchQuery("");
      }
      if (
        moreMenuRef.current &&
        !moreMenuRef.current.contains(event.target as Node)
      ) {
        setMoreMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (modelDropdownOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [modelDropdownOpen]);

  const currentProvider = providers.find((p) => p.name === selectedProvider);

  // Filter providers and models based on search query
  const filteredProviders = providers.map((provider) => {
    const matchesProviderName = provider.display_name.toLowerCase().includes(searchQuery.toLowerCase());
    const filteredModels = provider.model_versions.filter((model) =>
      model.toLowerCase().includes(searchQuery.toLowerCase())
    );
    
    return {
      ...provider,
      filteredModels,
      shouldShow: matchesProviderName || filteredModels.length > 0,
    };
  }).filter((p) => p.shouldShow);

  const handleModelSelect = (provider: string, model: string) => {
    onProviderChange(provider);
    onModelChange(model);
    setModelDropdownOpen(false);
    setSearchQuery("");
  };

  const handleMoreAction = (action: () => void) => {
    action();
    setMoreMenuOpen(false);
  };

  return (
    <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-6 py-3">
      <div className="flex items-center justify-between">
        {/* Left: Model Selector */}
        <div className="flex items-center gap-4">
          <div className="relative" ref={modelDropdownRef}>
            <button
              onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors group"
            >
              <Sparkles className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <div className="flex flex-col items-start">
                <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  {currentProvider?.display_name || "Select Model"}
                </span>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {selectedModel}
                </span>
              </div>
              <ChevronDown
                className={`w-4 h-4 text-gray-500 dark:text-gray-400 transition-transform ${
                  modelDropdownOpen ? "rotate-180" : ""
                }`}
              />
            </button>

            {/* Model Dropdown with Search */}
            {modelDropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-80 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                {/* Search Input */}
                <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                    <input
                      ref={searchInputRef}
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search models..."
                      className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder:text-gray-400"
                    />
                  </div>
                </div>

                {/* Providers and Models List */}
                <div className="max-h-96 overflow-y-auto">
                  {filteredProviders.length === 0 ? (
                    <div className="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
                      No models found
                    </div>
                  ) : (
                    filteredProviders.map((provider) => (
                      <div key={provider.name} className="border-b border-gray-100 dark:border-gray-700 last:border-b-0">
                        {/* Provider Header */}
                        <div className="px-4 py-2 bg-gray-50 dark:bg-gray-900">
                          <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
                            {provider.display_name}
                          </p>
                        </div>

                        {/* Models */}
                        <div className="py-1">
                          {(searchQuery ? provider.filteredModels : provider.model_versions).map((model) => (
                            <button
                              key={model}
                              onClick={() => handleModelSelect(provider.name, model)}
                              className={`w-full px-4 py-2.5 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                                selectedProvider === provider.name && selectedModel === model
                                  ? "bg-blue-50 dark:bg-blue-900/20"
                                  : ""
                              }`}
                            >
                              <div className="flex items-center gap-3">
                                <Sparkles
                                  className={`w-4 h-4 flex-shrink-0 ${
                                    selectedProvider === provider.name && selectedModel === model
                                      ? "text-blue-600 dark:text-blue-400"
                                      : "text-gray-400"
                                  }`}
                                />
                                <span
                                  className={`text-sm ${
                                    selectedProvider === provider.name && selectedModel === model
                                      ? "font-semibold text-blue-900 dark:text-blue-100"
                                      : "text-gray-700 dark:text-gray-300"
                                  }`}
                                >
                                  {model}
                                </span>
                              </div>
                              {selectedProvider === provider.name && selectedModel === model && (
                                <Check className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                              )}
                            </button>
                          ))}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Session Title (truncated) */}
          <div className="hidden md:block">
            <h2 className="text-sm font-medium text-gray-700 dark:text-gray-300 truncate max-w-md">
              {sessionTitle}
            </h2>
          </div>
        </div>

        {/* Right: Action Buttons */}
        <div className="flex items-center gap-2">
          {/* Share Button */}
          <button
            onClick={onShare}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <Share2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            <span className="hidden sm:inline text-sm font-medium text-gray-700 dark:text-gray-300">
              Share
            </span>
          </button>

          {/* Add People Button */}
          <button
            onClick={onAddPeople}
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          >
            <UserPlus className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            <span className="hidden sm:inline text-sm font-medium text-gray-700 dark:text-gray-300">
              Add People
            </span>
          </button>

          {/* More Menu */}
          <div className="relative" ref={moreMenuRef}>
            <button
              onClick={() => setMoreMenuOpen(!moreMenuOpen)}
              className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <MoreVertical className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            </button>

            {/* More Dropdown */}
            {moreMenuOpen && (
              <div className="absolute top-full right-0 mt-2 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-1 z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                <button
                  onClick={() => handleMoreAction(onPin)}
                  className="w-full px-4 py-2.5 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left"
                >
                  <Pin className={`w-4 h-4 ${isPinned ? "text-blue-600 dark:text-blue-400" : "text-gray-600 dark:text-gray-400"}`} />
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {isPinned ? "Unpin" : "Pin to top"}
                  </span>
                </button>
                <button
                  onClick={() => handleMoreAction(onArchive)}
                  className="w-full px-4 py-2.5 flex items-center gap-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors text-left"
                >
                  <Archive className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  <span className="text-sm text-gray-700 dark:text-gray-300">Archive</span>
                </button>
                <div className="border-t border-gray-100 dark:border-gray-700 my-1"></div>
                <button
                  onClick={() => handleMoreAction(onDelete)}
                  disabled={isDeleting}
                  className="w-full px-4 py-2.5 flex items-center gap-3 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors text-left disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isDeleting ? (
                    <Loader2 className="w-4 h-4 text-red-600 dark:text-red-400 animate-spin" />
                  ) : (
                    <Trash2 className="w-4 h-4 text-red-600 dark:text-red-400" />
                  )}
                  <span className="text-sm text-red-600 dark:text-red-400">
                    {isDeleting ? "Deleting..." : "Delete"}
                  </span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
