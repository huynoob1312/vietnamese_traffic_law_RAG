import React, { useState, useEffect } from 'react';
import { adminAPI } from '../../services/api';
import { Users, MessageSquare, MessagesSquare, AlertCircle, Shield, ShieldAlert, RefreshCw, CheckCircle2 } from 'lucide-react';

export default function AdminAnalyticsTab() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [lowConfidence, setLowConfidence] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updatingUserId, setUpdatingUserId] = useState(null);
  const [toast, setToast] = useState(null);

  const loadAllData = async () => {
    setLoading(true);
    try {
      const [statsData, usersData, auditData] = await Promise.all([
        adminAPI.getStats(),
        adminAPI.getUsers(),
        adminAPI.getLowConfidenceQueries(),
      ]);
      setStats(statsData);
      setUsers(usersData);
      setLowConfidence(auditData);
    } catch (err) {
      console.error('Lỗi khi tải dữ liệu thống kê:', err);
      setToast({
        type: 'error',
        message: err.response?.data?.detail || 'Không thể tải số liệu thống kê',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  const handleToggleRole = async (user) => {
    const newRole = user.role === 'admin' ? 'user' : 'admin';
    const confirmMsg =
      newRole === 'admin'
        ? `Nâng cấp tài khoản "${user.username}" thành Quản trị viên (Admin)?`
        : `Hạ quyền tài khoản "${user.username}" thành Thành viên thường (User)?`;

    if (!window.confirm(confirmMsg)) return;

    setUpdatingUserId(user.user_id);
    setToast(null);
    try {
      await adminAPI.updateUserRole(user.user_id, newRole);
      setToast({
        type: 'success',
        message: `Đã đổi vai trò của "${user.username}" thành ${newRole.toUpperCase()}`,
      });
      // Cập nhật lại UI local
      setUsers((prev) =>
        prev.map((u) => (u.user_id === user.user_id ? { ...u, role: newRole } : u))
      );
    } catch (err) {
      setToast({
        type: 'error',
        message: err.response?.data?.detail || 'Không thể thay đổi quyền hạn',
      });
    } finally {
      setUpdatingUserId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-stone space-y-3">
        <RefreshCw size={24} className="animate-spin text-charcoal" />
        <span className="text-xs">Đang tải số liệu thống kê & danh sách người dùng...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-4">
      {/* Toast Alert */}
      {toast && (
        <div
          className={`p-3 rounded-card text-xs flex items-center justify-between border ${
            toast.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}
        >
          <div className="flex items-center gap-2">
            {toast.type === 'success' ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
            <span>{toast.message}</span>
          </div>
          <button
            type="button"
            onClick={() => setToast(null)}
            className="text-xs underline hover:opacity-75"
          >
            Đóng
          </button>
        </div>
      )}

      {/* 4 Metric Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white border border-pebble rounded-card p-3.5 shadow-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between text-stone mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Tổng Người dùng</span>
            <Users size={16} className="text-charcoal" />
          </div>
          <span className="text-2xl font-semibold text-charcoal">{stats?.total_users || 0}</span>
          <span className="text-[10px] text-stone mt-1">Đã đăng ký tài khoản</span>
        </div>

        <div className="bg-white border border-pebble rounded-card p-3.5 shadow-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between text-stone mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Phiên Tra Cứu</span>
            <MessageSquare size={16} className="text-charcoal" />
          </div>
          <span className="text-2xl font-semibold text-charcoal">{stats?.total_sessions || 0}</span>
          <span className="text-[10px] text-stone mt-1">Tổng phiên hội thoại</span>
        </div>

        <div className="bg-white border border-pebble rounded-card p-3.5 shadow-subtle flex flex-col justify-between">
          <div className="flex items-center justify-between text-stone mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Tổng Tin Nhắn</span>
            <MessagesSquare size={16} className="text-charcoal" />
          </div>
          <span className="text-2xl font-semibold text-charcoal">{stats?.total_messages || 0}</span>
          <span className="text-[10px] text-stone mt-1">Lượt hỏi đáp tích lũy</span>
        </div>

        <div className="bg-white border border-amber-200 rounded-card p-3.5 shadow-subtle flex flex-col justify-between bg-amber-50/30">
          <div className="flex items-center justify-between text-amber-800 mb-2">
            <span className="text-[11px] font-medium uppercase tracking-wider">Thiếu Nguồn Luật</span>
            <AlertCircle size={16} className="text-amber-600" />
          </div>
          <span className="text-2xl font-semibold text-amber-900">
            {stats?.zero_citation_count || 0}
          </span>
          <span className="text-[10px] text-amber-700 mt-1">Câu hỏi có 0 trích dẫn</span>
        </div>
      </div>

      {/* Users Management Table */}
      <div className="bg-white border border-pebble rounded-card p-4 space-y-3 shadow-subtle">
        <div className="flex items-center justify-between border-b border-pebble pb-2">
          <div>
            <h3 className="text-xs font-semibold text-charcoal uppercase tracking-wider">
              Danh sách Tài khoản Người dùng ({users.length})
            </h3>
            <p className="text-[11px] text-stone mt-0.5">
              Xem vai trò và phân quyền trực tiếp giữa User và Quản trị viên (Admin)
            </p>
          </div>
          <button
            type="button"
            onClick={loadAllData}
            className="p-1 text-stone hover:text-charcoal rounded-pill hover:bg-subtle-fill transition-colors"
            title="Làm mới"
          >
            <RefreshCw size={14} />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-pebble text-stone font-medium text-[11px] uppercase">
                <th className="py-2 px-2">ID</th>
                <th className="py-2 px-2">Tên tài khoản</th>
                <th className="py-2 px-2">Vai trò</th>
                <th className="py-2 px-2 text-center">Số phiên</th>
                <th className="py-2 px-2">Ngày tạo</th>
                <th className="py-2 px-2 text-right">Phân quyền</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-pebble/60 text-charcoal">
              {users.map((u) => {
                const isAdmin = u.role === 'admin';
                const isUpdating = updatingUserId === u.user_id;
                const formattedDate = new Date(u.created_at).toLocaleDateString('vi-VN');

                return (
                  <tr key={u.user_id} className="hover:bg-subtle-fill/30 transition-colors">
                    <td className="py-2.5 px-2 text-stone font-mono text-[11px]">{u.user_id}</td>
                    <td className="py-2.5 px-2 font-medium">{u.username}</td>
                    <td className="py-2.5 px-2">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-pill text-[10px] font-medium uppercase ${
                          isAdmin
                            ? 'bg-deep-teal/10 text-deep-teal border border-deep-teal/20'
                            : 'bg-subtle-fill text-stone'
                        }`}
                      >
                        {isAdmin && <Shield size={10} />}
                        {u.role}
                      </span>
                    </td>
                    <td className="py-2.5 px-2 text-center">{u.session_count}</td>
                    <td className="py-2.5 px-2 text-stone text-[11px]">{formattedDate}</td>
                    <td className="py-2.5 px-2 text-right">
                      <button
                        type="button"
                        onClick={() => handleToggleRole(u)}
                        disabled={isUpdating}
                        className={`px-2.5 py-1 rounded-pill text-[11px] font-medium transition-all ${
                          isAdmin
                            ? 'text-amber-700 hover:bg-amber-50 border border-amber-300'
                            : 'text-deep-teal hover:bg-deep-teal/10 border border-deep-teal/30'
                        }`}
                      >
                        {isUpdating
                          ? 'Đang đổi...'
                          : isAdmin
                          ? 'Hạ xuống User'
                          : 'Nâng lên Admin'}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Low-confidence / Zero-citation Audit Table */}
      <div className="bg-white border border-pebble rounded-card p-4 space-y-3 shadow-subtle">
        <div className="flex items-center justify-between border-b border-pebble pb-2">
          <div>
            <h3 className="text-xs font-semibold text-charcoal uppercase tracking-wider flex items-center gap-1.5">
              <ShieldAlert size={14} className="text-amber-600" />
              Câu hỏi Cần Bổ sung Nguồn luật (Khoảng trống Tri thức)
            </h3>
            <p className="text-[11px] text-stone mt-0.5">
              Danh sách các câu hỏi mà AI trả lời nhưng không tìm thấy Điều/Khoản luật trích dẫn liên quan
            </p>
          </div>
        </div>

        {lowConfidence.length === 0 ? (
          <div className="py-8 text-center text-xs text-stone italic">
            Không có câu hỏi nào bị thiếu nguồn luật trích dẫn 🎉
          </div>
        ) : (
          <div className="divide-y divide-pebble/60 max-h-[300px] overflow-y-auto">
            {lowConfidence.map((item) => (
              <div key={item.message_id} className="py-3 px-1 space-y-1.5">
                <div className="flex items-center justify-between text-[11px] text-stone">
                  <span>
                    Người hỏi: <strong className="text-charcoal font-medium">{item.username}</strong>
                  </span>
                  <span>{new Date(item.created_at).toLocaleString('vi-VN')}</span>
                </div>
                <div className="text-xs text-charcoal font-medium bg-aged-paper p-2 rounded-input border border-pebble">
                  Q: {item.user_question}
                </div>
                <div className="text-[11px] text-stone pl-2 border-l-2 border-amber-400 italic">
                  AI: {item.ai_answer}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
