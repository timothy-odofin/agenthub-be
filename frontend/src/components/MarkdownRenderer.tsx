import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Block code: rendered inside a <pre> by react-markdown
          pre({ children }) {
            return (
              <div className="relative group my-4">
                <div className="absolute right-2 top-2 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                  <button
                    onClick={(e) => {
                      const pre = (e.currentTarget as HTMLElement).closest('.group')?.querySelector('pre');
                      navigator.clipboard.writeText(pre?.textContent?.replace(/\n$/, '') ?? '');
                    }}
                    className="px-2 py-1 text-xs bg-gray-500 hover:bg-gray-400 text-white rounded"
                  >
                    Copy
                  </button>
                </div>
                <pre className="bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-100 text-sm font-mono p-4 rounded-lg overflow-x-auto border border-gray-200 dark:border-gray-700 leading-relaxed">
                  {children}
                </pre>
              </div>
            );
          },
          // Inline code: <code> NOT inside a <pre> (react-markdown wraps block code in <pre><code>)
          code({ node, className, children, ...props }: any) {
            // If this <code> is a direct child of a <pre>, it's a block — render transparently
            // so the parent <pre> controls all styling (background, text colour, font)
            const isBlock =
              node?.parent?.type === 'element' && node?.parent?.tagName === 'pre';

            if (isBlock) {
              return (
                <code className="bg-transparent text-inherit font-mono text-sm" {...props}>
                  {children}
                </code>
              );
            }

            // Inline code: styled as a pill
            return (
              <code
                className="bg-gray-100 dark:bg-gray-800 text-red-600 dark:text-red-400 px-1.5 py-0.5 rounded text-sm font-mono"
                {...props}
              >
                {children}
              </code>
            );
          },
          // Customize paragraphs
          p({ children }) {
            return <p className="mb-4 leading-relaxed last:mb-0">{children}</p>;
          },
          // Customize headings
          h1({ children }) {
            return <h1 className="text-2xl font-bold mb-4 mt-6 first:mt-0">{children}</h1>;
          },
          h2({ children }) {
            return <h2 className="text-xl font-bold mb-3 mt-5 first:mt-0">{children}</h2>;
          },
          h3({ children }) {
            return <h3 className="text-lg font-semibold mb-2 mt-4 first:mt-0">{children}</h3>;
          },
          // Customize lists
          ul({ children }) {
            return <ul className="list-disc list-inside mb-4 space-y-1">{children}</ul>;
          },
          ol({ children }) {
            return <ol className="list-decimal list-inside mb-4 space-y-1">{children}</ol>;
          },
          li({ children }) {
            return <li className="leading-relaxed">{children}</li>;
          },
          // Customize links
          a({ href, children }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline"
              >
                {children}
              </a>
            );
          },
          // Customize blockquotes
          blockquote({ children }) {
            return (
              <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic my-4 text-gray-700 dark:text-gray-300">
                {children}
              </blockquote>
            );
          },
          // Customize tables
          table({ children }) {
            return (
              <div className="overflow-x-auto mb-4">
                <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-600">
                  {children}
                </table>
              </div>
            );
          },
          th({ children }) {
            return (
              <th className="border border-gray-300 dark:border-gray-600 bg-gray-100 dark:bg-gray-800 px-4 py-2 text-left font-semibold">
                {children}
              </th>
            );
          },
          td({ children }) {
            return <td className="border border-gray-300 dark:border-gray-600 px-4 py-2">{children}</td>;
          },
          // Customize horizontal rule
          hr() {
            return <hr className="my-6 border-t border-gray-300 dark:border-gray-600" />;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
