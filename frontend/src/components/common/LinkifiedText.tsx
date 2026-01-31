/**
 * LinkifiedText Component
 * 
 * Renders text content with automatic URL detection and conversion to clickable links.
 * Supports both plain URLs and markdown-style links [text](url).
 * Implements security best practices and accessibility standards.
 * 
 * @component
 * @example
 * ```tsx
 * <LinkifiedText 
 *   content="Check out https://example.com for more info"
 *   className="text-gray-900"
 * />
 * ```
 */

import React, { useMemo } from 'react';
import { ExternalLink } from 'lucide-react';
import { 
  parseLinkifiedContent, 
  sanitizeUrl, 
  extractDomain,
  type LinkifiedSegment 
} from '@/utils/linkify';

interface LinkifiedTextProps {
  /** Text content to be linkified */
  content: string;
  /** Additional CSS classes for the container */
  className?: string;
  /** Whether to show external link icon */
  showIcon?: boolean;
  /** Custom link styling classes */
  linkClassName?: string;
}

/**
 * LinkifiedText component renders text with automatic URL detection and linking
 */
export const LinkifiedText: React.FC<LinkifiedTextProps> = ({
  content,
  className = '',
  showIcon = true,
  linkClassName = '',
}) => {
  // Memoize parsed content to avoid re-parsing on every render
  const segments = useMemo(() => parseLinkifiedContent(content), [content]);

  /**
   * Renders an individual link segment with security and accessibility features
   */
  const renderLink = (segment: LinkifiedSegment) => {
    if (!segment.url) return null;

    const sanitizedUrl = sanitizeUrl(segment.url);
    if (!sanitizedUrl) {
      // If URL is dangerous, render as plain text
      return <span key={segment.id}>{segment.content}</span>;
    }

    const domain = extractDomain(sanitizedUrl);
    const isExternal = !sanitizedUrl.startsWith(window.location.origin);

    return (
      <a
        key={segment.id}
        href={sanitizedUrl}
        target="_blank"
        rel="noopener noreferrer"
        className={`
          inline-flex items-center gap-1
          text-blue-600 hover:text-blue-800
          underline decoration-1 underline-offset-2
          hover:decoration-2
          transition-all duration-150
          focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 rounded
          ${linkClassName}
        `}
        aria-label={`Open ${domain} in new tab`}
        title={sanitizedUrl}
      >
        <span className="break-all">{segment.content}</span>
        {showIcon && isExternal && (
          <ExternalLink 
            className="inline-block flex-shrink-0 w-3 h-3 opacity-70" 
            aria-hidden="true"
          />
        )}
      </a>
    );
  };

  /**
   * Renders a text segment preserving whitespace and line breaks
   */
  const renderText = (segment: LinkifiedSegment) => {
    // Preserve line breaks and whitespace
    const lines = segment.content.split('\n');
    
    return (
      <React.Fragment key={segment.id}>
        {lines.map((line, index) => (
          <React.Fragment key={`${segment.id}-${index}`}>
            {line}
            {index < lines.length - 1 && <br />}
          </React.Fragment>
        ))}
      </React.Fragment>
    );
  };

  return (
    <div className={`whitespace-pre-wrap break-words ${className}`}>
      {segments.map((segment) => {
        if (segment.type === 'link') {
          return renderLink(segment);
        }
        return renderText(segment);
      })}
    </div>
  );
};

export default LinkifiedText;
