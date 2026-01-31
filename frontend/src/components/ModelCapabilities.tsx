import React, { useState } from 'react';
import { Database, Loader2, Globe, Github, Activity, FileText, Grid } from 'lucide-react';

interface Capability {
  id: string;
  category: string;
  name: string;
  title: string;
  description: string;
  icon: string;
  example_prompts: string[];
  tags: string[];
}

interface ModelCapabilitiesProps {
  onSelectPrompt: (prompt: string, capabilityId: string) => void;
  onCapabilityClick: (capabilityId: string, defaultPrompt: string) => void;
  capabilities: Capability[];
  categories: string[];
  loading: boolean;
  error: string | null;
  onRetry?: () => void;
}

const iconMap: { [key: string]: any } = {
  database: Database,
  globe: Globe,
  github: Github,
  datadog: Activity,
  jira: Grid,
  confluence: FileText,
  default: Database,
};

const ModelCapabilities: React.FC<ModelCapabilitiesProps> = ({ 
  onSelectPrompt, 
  onCapabilityClick,
  capabilities,
  categories,
  loading,
  error,
  onRetry
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const filteredCapabilities = selectedCategory === 'all' 
    ? capabilities 
    : capabilities.filter(cap => cap.category === selectedCategory);

  const getIcon = (iconName: string) => {
    const Icon = iconMap[iconName] || iconMap.default;
    return Icon;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 mb-4">{error}</p>
        {onRetry && (
          <button 
            onClick={onRetry}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Try Again
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 bg-gradient-to-b from-white to-gray-50">
      {/* Header */}
      <div className="text-center mb-10 max-w-2xl">
        <h1 className="text-[2.5rem] font-normal text-gray-900 mb-2 tracking-tight">
          How can I help you today?
        </h1>
      </div>

      {/* Category Pills - Horizontal scroll on mobile */}
      {categories.length > 0 && (
        <div className="w-full max-w-6xl mb-8 overflow-x-auto">
          <div className="flex gap-2 justify-center min-w-max px-4">
            <button
              onClick={() => setSelectedCategory('all')}
              className={`px-5 py-2.5 rounded-full text-[0.9375rem] font-medium transition-all whitespace-nowrap ${
                selectedCategory === 'all'
                  ? 'bg-gray-900 text-white shadow-sm'
                  : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50 hover:border-gray-300'
              }`}
            >
              All
            </button>
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-5 py-2.5 rounded-full text-[0.9375rem] font-medium capitalize transition-all whitespace-nowrap ${
                  selectedCategory === category
                    ? 'bg-gray-900 text-white shadow-sm'
                    : 'bg-white text-gray-700 border border-gray-200 hover:bg-gray-50 hover:border-gray-300'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Capabilities Grid - ChatGPT style cards */}
      <div className="w-full max-w-6xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 px-4">
        {filteredCapabilities.map((capability) => {
          const Icon = getIcon(capability.icon);
          
          return (
            <button
              key={capability.id}
              onClick={() => {
                // Use first example prompt when card is clicked
                const firstPrompt = capability.example_prompts[0] || '';
                onCapabilityClick(capability.id, firstPrompt);
                onSelectPrompt(firstPrompt, capability.id);
              }}
              className="text-left bg-white rounded-3xl border border-gray-200 p-5 shadow-sm hover:shadow-md hover:border-gray-300 transition-all cursor-pointer"
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-sm">
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-gray-900 text-base leading-snug mb-1.5">
                    {capability.title}
                  </h3>
                  <p className="text-[0.8125rem] text-gray-600 leading-relaxed">
                    {capability.description}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Empty State */}
      {filteredCapabilities.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 text-base">No capabilities found in this category</p>
        </div>
      )}
    </div>
  );
};

export default ModelCapabilities;
