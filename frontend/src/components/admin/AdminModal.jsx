import React, { useState, useEffect } from 'react';
import { X, Sliders, Database, Users, Shield } from 'lucide-react';
import AdminConfigTab from './AdminConfigTab';
import AdminIngestionTab from './AdminIngestionTab';
import AdminAnalyticsTab from './AdminAnalyticsTab';

export default function AdminModal({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState('config'); // 'config' | 'ingestion' | 'analytics'

  // Đóng modal bằng phím Escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-3 md:p-6 animate-in fade-in duration-200">
      <div className="relative w-full max-w-4xl h-[90vh] bg-aged-paper border border-pebble rounded-card shadow-2xl flex flex-col overflow-hidden text-charcoal">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-pebble bg-white shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-pill bg-deep-teal text-white flex items-center justify-center shadow-subtle shrink-0">
              <Shield size={17} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-semibold tracking-tight text-charcoal leading-none">
                  Bảng Điều Khiển Quản Trị Viên
                </h2>
                <span className="text-[10px] bg-deep-teal/10 text-deep-teal px-2 py-0.5 rounded-pill font-medium uppercase border border-deep-teal/20">
                  Admin System
                </span>
              </div>
              <p className="text-[11px] text-stone mt-0.5">
                Quản lý siêu tham số RAG, tệp tri thức pháp lý và giám sát người dùng
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-stone hover:text-charcoal rounded-pill hover:bg-subtle-fill transition-colors"
            title="Đóng bảng quản trị (Esc)"
          >
            <X size={18} />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1 px-6 py-2 border-b border-pebble bg-white/70 backdrop-blur-sm shrink-0">
          <button
            type="button"
            onClick={() => setActiveTab('config')}
            className={`px-3.5 py-1.5 rounded-pill text-xs font-medium flex items-center gap-1.5 transition-all ${activeTab === 'config'
                ? 'bg-charcoal text-white shadow-subtle'
                : 'text-stone hover:text-charcoal hover:bg-subtle-fill'
              }`}
          >
            <Sliders size={13} />
            <span>1. Cấu hình RAG (config.yaml)</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('ingestion')}
            className={`px-3.5 py-1.5 rounded-pill text-xs font-medium flex items-center gap-1.5 transition-all ${activeTab === 'ingestion'
                ? 'bg-charcoal text-white shadow-subtle'
                : 'text-stone hover:text-charcoal hover:bg-subtle-fill'
              }`}
          >
            <Database size={13} />
            <span>2. Tri thức & Re-index</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('analytics')}
            className={`px-3.5 py-1.5 rounded-pill text-xs font-medium flex items-center gap-1.5 transition-all ${activeTab === 'analytics'
                ? 'bg-charcoal text-white shadow-subtle'
                : 'text-stone hover:text-charcoal hover:bg-subtle-fill'
              }`}
          >
            <Users size={13} />
            <span>3. Người dùng & Giám sát</span>
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'config' && <AdminConfigTab />}
          {activeTab === 'ingestion' && <AdminIngestionTab />}
          {activeTab === 'analytics' && <AdminAnalyticsTab />}
        </div>

        {/* Modal Footer Note */}
        <div className="px-6 py-2.5 border-t border-pebble bg-white/50 flex items-center justify-between text-[11px] text-stone shrink-0">
        </div>
      </div>
    </div>
  );
}
