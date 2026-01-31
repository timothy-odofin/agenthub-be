import { useState, useRef, useEffect } from "react";
import { ChevronDown, Check } from "lucide-react";
import type { ModelVersion } from "@/types";

interface ModelSelectorProps {
  providers: ModelVersion[];
  selectedProvider: string;
  selectedModel: string;
  onProviderChange: (provider: string) => void;
  onModelChange: (model: string) => void;
  disabled?: boolean;
}

export default function ModelSelector({
  providers,
  selectedProvider,
  selectedModel,
  onProviderChange,
  onModelChange,
  disabled = false,
}: ModelSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const currentProvider = providers.find((p) => p.name === selectedProvider);
  const displayName = currentProvider?.display_name || "Select Model";

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const handleProviderSelect = (provider: ModelVersion) => {
    onProviderChange(provider.name);
    onModelChange(provider.default_model);
    setIsOpen(false);
  };

  const handleModelSelect = (provider: ModelVersion, model: string) => {
    onProviderChange(provider.name);
    onModelChange(model);
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className="flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed min-w-[180px]"
      >
        <div className="flex flex-col items-start flex-1">
          <span className="text-xs text-gray-500 dark:text-gray-400">Model</span>
          <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate max-w-[140px]">
            {displayName}
          </span>
        </div>
        <ChevronDown
          size={16}
          className={`text-gray-500 transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </button>

      {isOpen && (
        <div className="absolute left-0 top-full mt-2 w-72 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-50 max-h-[400px] overflow-y-auto">
          {providers.map((provider) => (
            <div key={provider.name} className="border-b border-gray-100 dark:border-gray-700 last:border-b-0">
              {/* Provider Header */}
              <button
                type="button"
                onClick={() => handleProviderSelect(provider)}
                className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors flex items-center justify-between"
              >
                <div className="flex flex-col">
                  <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {provider.display_name}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Default: {provider.default_model}
                  </span>
                </div>
                {selectedProvider === provider.name && (
                  <Check size={16} className="text-blue-600 dark:text-blue-400" />
                )}
              </button>

              {/* Model Versions - Show when provider is selected or expanded */}
              {selectedProvider === provider.name && (
                <div className="bg-gray-50 dark:bg-gray-900 px-2 py-2">
                  {provider.model_versions.map((model) => (
                    <button
                      key={model}
                      type="button"
                      onClick={() => handleModelSelect(provider, model)}
                      className="w-full px-3 py-2 text-left hover:bg-white dark:hover:bg-gray-800 rounded transition-colors flex items-center justify-between group"
                    >
                      <span className="text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100">
                        {model}
                      </span>
                      {selectedModel === model && (
                        <Check size={14} className="text-blue-600 dark:text-blue-400" />
                      )}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
