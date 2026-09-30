import React, { useState } from 'react';
import { BookOpen, ChevronDown, ChevronUp, FileText } from 'lucide-react';

export default function CitationCard({ citations }) {
  const [isOpen, setIsOpen] = useState(false);

  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-3 pt-2 border-t border-pebble/60 text-xs">
      {/* Toggle button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-pill bg-white hover:bg-subtle-fill border border-pebble text-charcoal font-medium transition-colors shadow-subtle"
      >
        <BookOpen size={13} className="text-deep-teal" />
        <span>Căn cứ pháp lý ({citations.length} nguồn tham chiếu)</span>
        {isOpen ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
      </button>

      {/* Expanded citation list */}
      {isOpen && (
        <div className="mt-2.5 space-y-2 animate-in fade-in duration-200">
          {citations.map((cite, index) => {
            const docName = cite.source || cite.document_name || 'Văn bản QPPL';
            const dieu = cite.dieu ? `Điều ${cite.dieu}` : '';
            const khoan = cite.khoan ? `Khoản ${cite.khoan}` : '';
            const diem = cite.diem ? `Điểm ${cite.diem}` : '';
            const legalPosition = [dieu, khoan, diem].filter(Boolean).join(', ');

            return (
              <div
                key={index}
                className="p-3 bg-white rounded-card border border-pebble shadow-subtle hover:border-deep-teal/40 transition-colors"
              >
                <div className="flex items-start justify-between gap-2 mb-1">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-chip bg-aged-paper border border-pebble text-[11px] font-medium text-charcoal">
                      <FileText size={11} className="text-deep-teal" />
                      {docName}
                    </span>
                    {legalPosition && (
                      <span className="text-[11px] font-medium text-charcoal">
                        {legalPosition}
                      </span>
                    )}
                  </div>
                </div>

                {cite.content && (
                  <p className="text-ash-gray text-[12px] leading-relaxed line-clamp-4 hover:line-clamp-none transition-all mt-1 bg-aged-paper/40 p-2 rounded-input border border-pebble/40">
                    {cite.content}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
