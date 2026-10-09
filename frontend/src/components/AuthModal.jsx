import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { X, Lock, User, AlertCircle, CheckCircle2 } from 'lucide-react';

export default function AuthModal({ isOpen, onClose }) {
  const { login, register } = useAuth();
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!username.trim()) {
      setError('Vui lòng nhập tên tài khoản.');
      return;
    }

    if (username.trim().length < 3) {
      setError('Tên tài khoản phải có ít nhất 3 ký tự.');
      return;
    }

    if (!password) {
      setError('Vui lòng nhập mật khẩu.');
      return;
    }

    if (password.length < 6) {
      setError('Mật khẩu phải có ít nhất 6 ký tự.');
      return;
    }

    if (isRegister && password !== confirmPassword) {
      setError('Mật khẩu xác nhận không khớp.');
      return;
    }

    setLoading(true);
    try {
      if (isRegister) {
        await register(username.trim(), password);
        setSuccess('Đăng ký tài khoản thành công!');
      } else {
        await login(username.trim(), password);
        setSuccess('Đăng nhập thành công!');
      }
      setTimeout(() => {
        onClose();
        setUsername('');
        setPassword('');
        setConfirmPassword('');
        setError('');
        setSuccess('');
      }, 700);
    } catch (err) {
      const errMsg =
        err.response?.data?.detail ||
        (isRegister ? 'Đăng ký không thành công. Tài khoản có thể đã tồn tại.' : 'Sai tên tài khoản hoặc mật khẩu.');
      setError(errMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleTabSwitch = (toRegister) => {
    setIsRegister(toRegister);
    setError('');
    setSuccess('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-sm bg-white rounded-card border border-pebble shadow-subtle p-6 text-charcoal">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-ash-gray hover:text-charcoal transition-colors p-1 rounded-pill hover:bg-subtle-fill"
          aria-label="Đóng"
        >
          <X size={18} />
        </button>

        {/* Tab switcher */}
        <div className="flex border-b border-pebble mb-6 mt-1">
          <button
            type="button"
            onClick={() => handleTabSwitch(false)}
            className={`flex-1 py-2 text-sm font-medium transition-colors relative ${
              !isRegister ? 'text-charcoal' : 'text-ash-gray hover:text-charcoal'
            }`}
          >
            Đăng nhập
            {!isRegister && (
              <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-deep-teal rounded-pill" />
            )}
          </button>
          <button
            type="button"
            onClick={() => handleTabSwitch(true)}
            className={`flex-1 py-2 text-sm font-medium transition-colors relative ${
              isRegister ? 'text-charcoal' : 'text-ash-gray hover:text-charcoal'
            }`}
          >
            Đăng ký
            {isRegister && (
              <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-deep-teal rounded-pill" />
            )}
          </button>
        </div>

        {/* Status notification */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-input flex items-center gap-2 text-xs text-red-700">
            <AlertCircle size={15} className="shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 bg-teal-50 border border-deep-teal/30 rounded-input flex items-center gap-2 text-xs text-deep-teal">
            <CheckCircle2 size={15} className="shrink-0" />
            <span>{success}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-ash-gray mb-1">
              Tên tài khoản
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-stone pointer-events-none">
                <User size={16} />
              </span>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Nhập tên tài khoản"
                className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-pebble rounded-input text-charcoal placeholder-stone focus:outline-none focus:border-deep-teal transition-colors"
                autoComplete="username"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-ash-gray mb-1">
              Mật khẩu
            </label>
            <div className="relative">
              <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-stone pointer-events-none">
                <Lock size={16} />
              </span>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Tối thiểu 6 ký tự"
                className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-pebble rounded-input text-charcoal placeholder-stone focus:outline-none focus:border-deep-teal transition-colors"
                autoComplete={isRegister ? 'new-password' : 'current-password'}
                required
              />
            </div>
          </div>

          {isRegister && (
            <div>
              <label className="block text-xs font-medium text-ash-gray mb-1">
                Xác nhận mật khẩu
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-stone pointer-events-none">
                  <Lock size={16} />
                </span>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Nhập lại mật khẩu"
                  className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-pebble rounded-input text-charcoal placeholder-stone focus:outline-none focus:border-deep-teal transition-colors"
                  autoComplete="new-password"
                  required
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-2.5 px-4 bg-charcoal hover:bg-black text-white text-sm font-medium rounded-pill shadow-subtle transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {loading ? (
              <span className="inline-block w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
            ) : isRegister ? (
              'Tạo tài khoản'
            ) : (
              'Đăng nhập'
            )}
          </button>
        </form>

        <p className="mt-4 text-center text-xs text-stone">
          Hệ thống tra cứu tự động Luật Giao thông Việt Nam RAG
        </p>
      </div>
    </div>
  );
}
