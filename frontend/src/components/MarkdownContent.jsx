import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Scale, FileText } from 'lucide-react';

export default function MarkdownContent({ content, isStreaming, isLastAi }) {
  if (!content) return null;

  return (
    <div className="markdown-body text-charcoal text-sm leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="text-xl font-bold text-charcoal mt-5 mb-2.5 pb-1 border-b border-pebble/60 flex items-center gap-2">
              <Scale size={18} className="text-deep-teal shrink-0" />
              <span>{children}</span>
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-base font-semibold text-charcoal mt-4 mb-2 flex items-center gap-1.5">
              <span className="w-1.5 h-4 bg-deep-teal rounded-pill shrink-0 inline-block" />
              <span>{children}</span>
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-[14.5px] font-semibold text-charcoal mt-3.5 mb-1.5 text-deep-teal flex items-center gap-1.5">
              <span>{children}</span>
            </h3>
          ),
          p: ({ children }) => (
            <p className="my-1.5 leading-relaxed text-charcoal/95">
              {children}
            </p>
          ),
          ul: ({ children }) => (
            <ul className="list-disc pl-5 space-y-1.5 my-2 marker:text-deep-teal">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal pl-5 space-y-1.5 my-2 marker:text-deep-teal marker:font-semibold">
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li className="leading-relaxed pl-0.5">
              {children}
            </li>
          ),
          strong: ({ children }) => {
            const text = String(children);
            // Highlight fine amounts or "Mức phạt:"
            if (text.toLowerCase().includes('mức phạt') || text.includes('đồng') || text.includes('triệu')) {
              return (
                <strong className="font-semibold text-charcoal bg-amber-50 text-amber-950 px-1 py-0.5 rounded border border-amber-200/60 inline-block my-0.5">
                  {children}
                </strong>
              );
            }
            return <strong className="font-semibold text-charcoal">{children}</strong>;
          },
          em: ({ children }) => {
            const text = String(children);
            // Format legal source tags *(Nguồn: ...)* as a clean statutory badge
            if (text.includes('Nguồn:') || text.includes('Điều') || text.includes('Văn bản')) {
              return (
                <span className="inline-flex items-center gap-1 text-[11.5px] text-deep-teal bg-deep-teal/5 border border-deep-teal/20 px-2 py-0.5 rounded-chip font-medium not-italic my-1">
                  <FileText size={11} className="shrink-0" />
                  <span>{children}</span>
                </span>
              );
            }
            return <em className="italic text-ash-gray">{children}</em>;
          },
          hr: () => <hr className="my-4 border-t border-pebble/60" />,
          blockquote: ({ children }) => (
            <blockquote className="border-l-3 border-deep-teal pl-3 py-1 my-2.5 bg-subtle-fill/30 text-ash-gray italic rounded-r text-[13px]">
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-3 border border-pebble rounded-card shadow-subtle">
              <table className="w-full text-xs text-left border-collapse">
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className="bg-subtle-fill/80 text-charcoal font-semibold border-b border-pebble">
              {children}
            </thead>
          ),
          th: ({ children }) => (
            <th className="px-3 py-2 border-r border-pebble/40 last:border-r-0">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-2 border-t border-pebble/40 border-r border-pebble/40 last:border-r-0">
              {children}
            </td>
          ),
          code: ({ inline, children }) => (
            inline ? (
              <code className="bg-subtle-fill/60 px-1.5 py-0.5 rounded text-xs font-mono text-deep-teal">
                {children}
              </code>
            ) : (
              <pre className="p-3 my-2 bg-charcoal text-aged-paper rounded-card overflow-x-auto text-xs font-mono">
                <code>{children}</code>
              </pre>
            )
          )
        }}
      >
        {content}
      </ReactMarkdown>
      {isLastAi && isStreaming && (
        <span className="inline-block w-1.5 h-4 ml-1 bg-deep-teal align-middle animate-pulse" />
      )}
    </div>
  );
}
