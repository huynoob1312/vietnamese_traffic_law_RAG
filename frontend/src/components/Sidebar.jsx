import React from 'react';
import { useAuth } from '../context/AuthContext';
import { useChat } from '../context/ChatContext';
import { Plus, MessageSquare, Trash2, LogOut, LogIn, Scale, Shield } from 'lucide-react';

export default function Sidebar({ onOpenAuth, onOpenAdmin }) {
  const { user, isAuthenticated, logout } = useAuth();
  const { sessions, activeSessionId, selectSession, createNewChat, deleteSession } = useChat();

  return (
    <aside className="w-[220px] shrink-0 h-screen sticky top-0 bg-aged-paper border-r border-pebble flex flex-col justify-between p-3 select-none text-charcoal">
      {/* Top Section: Brand & New Chat */}
      <div className="flex flex-col gap-3 min-h-0">
        {/* Brand header */}
        <div className="flex items-center gap-2 px-2 py-1">
          <div className="w-7 h-7 rounded-pill bg-charcoal text-white flex items-center justify-center shrink-0">
            <Scale size={15} />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium tracking-tight leading-none text-charcoal">
              Tra Cứu Luật
            </span>
            <span className="text-[11px] text-stone mt-0.5">Giao thông VN</span>
          </div>
        </div>

        {/* New Chat Button */}
        <button
          onClick={createNewChat}
          className="w-full h-9 px-3 rounded-pill bg-white hover:bg-subtle-fill border border-pebble flex items-center gap-2 text-sm text-charcoal shadow-subtle transition-all active:scale-[0.99]"
        >
          <Plus size={16} className="text-charcoal shrink-0" />
          <span className="font-normal truncate">Hội thoại mới</span>
        </button>

        {/* Sessions History List */}
        <div className="flex-1 overflow-y-auto mt-2 pr-1 space-y-1">
          <div className="px-2 pb-1 text-[11px] font-medium text-stone uppercase tracking-wider">
            Lịch sử tra cứu
          </div>

          {!isAuthenticated ? (
            <div className="p-3 bg-white/70 border border-pebble rounded-card text-xs text-ash-gray mt-2 space-y-2">
              <p className="leading-relaxed">
                Đăng nhập để tự động lưu và đồng bộ lịch sử tra cứu của bạn.
              </p>
              <button
                onClick={onOpenAuth}
                className="w-full py-1.5 px-3 bg-charcoal hover:bg-black text-white rounded-pill text-xs font-medium transition-colors"
              >
                Đăng nhập ngay
              </button>
            </div>
          ) : sessions.length === 0 ? (
            <div className="px-2 py-4 text-xs text-stone italic text-center">
              Chưa có phiên tra cứu nào
            </div>
          ) : (
            sessions.map((session) => {
              const sid = session.session_id || session.id;
              const isActive = sid === activeSessionId;
              return (
                <div
                  key={sid}
                  onClick={() => selectSession(sid)}
                  className={`group relative flex items-center justify-between h-9 px-2.5 rounded-pill cursor-pointer transition-colors text-xs ${
                    isActive
                      ? 'bg-subtle-fill font-medium text-charcoal'
                      : 'hover:bg-subtle-fill/60 text-charcoal/90 font-normal'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0 mr-1">
                    {isActive ? (
                      <span className="w-1.5 h-1.5 rounded-full bg-deep-teal shrink-0" />
                    ) : (
                      <MessageSquare size={13} className="text-stone shrink-0" />
                    )}
                    <span className="truncate">{session.title || 'Phiên tra cứu'}</span>
                  </div>

                  {/* Delete button on hover */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteSession(sid);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-stone hover:text-red-600 rounded-full transition-all shrink-0"
                    title="Xóa phiên"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Bottom Section: User Profile or Sign In */}
      <div className="pt-3 border-t border-pebble mt-2">
        {isAuthenticated && user?.role === 'admin' && (
          <button
            onClick={onOpenAdmin}
            className="w-full h-8 mb-2 px-3 rounded-pill bg-deep-teal/10 hover:bg-deep-teal/20 border border-deep-teal/30 flex items-center justify-center gap-1.5 text-xs font-medium text-deep-teal transition-all active:scale-[0.99] shadow-subtle"
            title="Mở Bảng Quản trị Hệ thống"
          >
            <Shield size={13} className="text-deep-teal shrink-0" />
            <span>Quản trị hệ thống</span>
          </button>
        )}

        {isAuthenticated && user ? (
          <div className="flex items-center justify-between p-1.5 rounded-pill bg-white border border-pebble">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-7 h-7 rounded-pill bg-charcoal text-white flex items-center justify-center text-xs font-medium uppercase shrink-0">
                {user.username ? user.username[0] : 'U'}
              </div>
              <div className="flex flex-col min-w-0">
                <span className="text-xs font-medium text-charcoal truncate">
                  {user.username}
                </span>
                <span className="text-[10px] text-stone uppercase">
                  {user.role || 'Member'}
                </span>
              </div>
            </div>
            <button
              onClick={logout}
              className="p-1.5 text-stone hover:text-charcoal rounded-pill hover:bg-subtle-fill transition-colors mr-1"
              title="Đăng xuất"
            >
              <LogOut size={15} />
            </button>
          </div>
        ) : (
          <button
            onClick={onOpenAuth}
            className="w-full h-8 px-3 rounded-pill bg-white hover:bg-subtle-fill border border-pebble flex items-center justify-center gap-1.5 text-xs font-medium text-charcoal transition-colors"
          >
            <LogIn size={14} className="text-ash-gray" />
            <span>Đăng nhập / Đăng ký</span>
          </button>
        )}
      </div>
    </aside>
  );
}
