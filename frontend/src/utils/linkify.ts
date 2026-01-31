/**
 * Linkify Utility
 * 
 * Provides functionality to detect and convert URLs in text to clickable links.
 * Handles various URL formats including http(s), www, and markdown-style links.
 * 
 * @module utils/linkify
 */

export interface LinkifiedSegment {
  type: 'text' | 'link';
  content: string;
  url?: string;
  id: string;
}

/**
 * Comprehensive URL detection regex pattern
 * Matches:
 * - http:// and https:// URLs
 * - www. prefixed URLs
 * - URLs with ports
 * - URLs with query parameters and fragments
 * - URLs with authentication
 */
const URL_REGEX = /(?:(?:https?:\/\/)|(?:www\.))[^\s<>"']+(?:[^\s<>"'.,;:!?)\]])/gi;

/**
 * Markdown link pattern [text](url)
 */
const MARKDOWN_LINK_REGEX = /\[([^\]]+)\]\(([^)]+)\)/g;

/**
 * Validates if a string is a proper URL
 * @param url - String to validate
 * @returns boolean indicating if the string is a valid URL
 */
export const isValidUrl = (url: string): boolean => {
  try {
    const urlObj = new URL(url.startsWith('www.') ? `https://${url}` : url);
    return urlObj.protocol === 'http:' || urlObj.protocol === 'https:';
  } catch {
    return false;
  }
};

/**
 * Normalizes URL by adding protocol if missing
 * @param url - URL string to normalize
 * @returns Normalized URL with protocol
 */
export const normalizeUrl = (url: string): string => {
  if (url.startsWith('www.')) {
    return `https://${url}`;
  }
  return url;
};

/**
 * Extracts domain from URL for display purposes
 * @param url - Full URL string
 * @returns Domain name or original URL if extraction fails
 */
export const extractDomain = (url: string): string => {
  try {
    const urlObj = new URL(normalizeUrl(url));
    return urlObj.hostname;
  } catch {
    return url;
  }
};

/**
 * Parses text content and identifies linkable segments
 * Handles both plain URLs and markdown-style links [text](url)
 * 
 * @param text - Raw text content to parse
 * @returns Array of linkified segments with metadata
 */
export const parseLinkifiedContent = (text: string): LinkifiedSegment[] => {
  if (!text || typeof text !== 'string') {
    return [{ type: 'text', content: '', id: '0' }];
  }

  const segments: LinkifiedSegment[] = [];
  let lastIndex = 0;
  let segmentId = 0;

  // First pass: Handle markdown links
  let processedText = text;
  const markdownMatches: Array<{ text: string; url: string; start: number; end: number }> = [];
  
  let markdownMatch;
  const markdownRegex = new RegExp(MARKDOWN_LINK_REGEX);
  
  while ((markdownMatch = markdownRegex.exec(text)) !== null) {
    markdownMatches.push({
      text: markdownMatch[1],
      url: markdownMatch[2],
      start: markdownMatch.index,
      end: markdownMatch.index + markdownMatch[0].length,
    });
  }

  // Replace markdown links with placeholders to avoid double-processing
  const placeholders: Map<string, { text: string; url: string }> = new Map();
  markdownMatches.forEach((match, index) => {
    const placeholder = `__MARKDOWN_LINK_${index}__`;
    placeholders.set(placeholder, { text: match.text, url: match.url });
    processedText = processedText.replace(
      text.substring(match.start, match.end),
      placeholder
    );
  });

  // Second pass: Handle plain URLs
  const urlRegex = new RegExp(URL_REGEX);
  let match;

  while ((match = urlRegex.exec(processedText)) !== null) {
    const url = match[0];
    const startIndex = match.index;

    // Add text before URL
    if (startIndex > lastIndex) {
      const textContent = processedText.substring(lastIndex, startIndex);
      // Check if this text contains markdown placeholders
      const placeholderMatch = textContent.match(/__MARKDOWN_LINK_\d+__/);
      
      if (placeholderMatch) {
        const parts = textContent.split(/__MARKDOWN_LINK_\d+__/);
        const placeholderKeys = textContent.match(/__MARKDOWN_LINK_\d+__/g) || [];
        
        parts.forEach((part, idx) => {
          if (part) {
            segments.push({
              type: 'text',
              content: part,
              id: `${segmentId++}`,
            });
          }
          
          if (idx < placeholderKeys.length) {
            const placeholderData = placeholders.get(placeholderKeys[idx]);
            if (placeholderData) {
              segments.push({
                type: 'link',
                content: placeholderData.text,
                url: normalizeUrl(placeholderData.url),
                id: `${segmentId++}`,
              });
            }
          }
        });
      } else if (textContent.trim()) {
        segments.push({
          type: 'text',
          content: textContent,
          id: `${segmentId++}`,
        });
      }
    }

    // Add URL as link
    if (isValidUrl(url)) {
      segments.push({
        type: 'link',
        content: url,
        url: normalizeUrl(url),
        id: `${segmentId++}`,
      });
    } else {
      segments.push({
        type: 'text',
        content: url,
        id: `${segmentId++}`,
      });
    }

    lastIndex = urlRegex.lastIndex;
  }

  // Add remaining text
  if (lastIndex < processedText.length) {
    const remainingText = processedText.substring(lastIndex);
    const placeholderMatch = remainingText.match(/__MARKDOWN_LINK_\d+__/);
    
    if (placeholderMatch) {
      const parts = remainingText.split(/__MARKDOWN_LINK_\d+__/);
      const placeholderKeys = remainingText.match(/__MARKDOWN_LINK_\d+__/g) || [];
      
      parts.forEach((part, idx) => {
        if (part) {
          segments.push({
            type: 'text',
            content: part,
            id: `${segmentId++}`,
          });
        }
        
        if (idx < placeholderKeys.length) {
          const placeholderData = placeholders.get(placeholderKeys[idx]);
          if (placeholderData) {
            segments.push({
              type: 'link',
              content: placeholderData.text,
              url: normalizeUrl(placeholderData.url),
              id: `${segmentId++}`,
            });
          }
        }
      });
    } else if (remainingText.trim()) {
      segments.push({
        type: 'text',
        content: remainingText,
        id: `${segmentId++}`,
      });
    }
  }

  // If no segments were created, return original text
  if (segments.length === 0) {
    segments.push({
      type: 'text',
      content: text,
      id: '0',
    });
  }

  return segments;
};

/**
 * Sanitizes URL to prevent XSS attacks
 * @param url - URL to sanitize
 * @returns Sanitized URL or null if dangerous
 */
export const sanitizeUrl = (url: string): string | null => {
  const dangerous = /^(javascript|data|vbscript):/i;
  
  if (dangerous.test(url)) {
    return null;
  }
  
  return url;
};
