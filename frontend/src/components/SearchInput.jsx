import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Sparkles } from 'lucide-react';

export default function SearchInput({ onSend, isStreaming, placeholder }) {
  const [query, setQuery] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        160
      )}px`;
    }
  }, [query]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!query.trim() || isStreaming) return;
    onSend(query.trim());
    setQuery('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-content mx-auto">
      <div className="bg-white border border-pebble rounded-input shadow-subtle p-3 transition-all focus-within:border-deep-teal/70">
        <textarea
          ref={textareaRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || 'Hỏi bất kỳ điều gì về Luật Giao thông Việt Nam...'}
          rows={1}
          disabled={isStreaming}
          className="w-full text-base font-normal text-charcoal placeholder-stone bg-transparent border-0 outline-none resize-none leading-relaxed block max-h-40"
        />

        {/* Action bar inside input container */}
        <div className="flex items-center justify-between pt-2 mt-1 border-t border-pebble/40">
          <div className="flex items-center gap-1.5">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-chip bg-aged-paper border border-pebble text-xs font-medium text-charcoal select-none">
              <Sparkles size={11} className="text-deep-teal" />
              Tra cứu chuẩn xác
            </span>
          </div>

          <button
            type="button"
            onClick={handleSubmit}
            disabled={!query.trim() || isStreaming}
            className={`w-7 h-7 rounded-pill flex items-center justify-center transition-all ${
              query.trim() && !isStreaming
                ? 'bg-charcoal hover:bg-black text-white cursor-pointer active:scale-95'
                : 'bg-stone/30 text-stone/60 cursor-not-allowed'
            }`}
            title="Gửi câu hỏi (Enter)"
            aria-label="Gửi câu hỏi"
          >
            <ArrowUp size={14} strokeWidth={2.5} />
          </button>
        </div>
      </div>
    </div>
  );
}
