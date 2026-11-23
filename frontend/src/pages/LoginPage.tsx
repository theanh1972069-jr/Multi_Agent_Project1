import React, { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Activity, AlertCircle, KeyRound, Loader2, LogIn, Mail, Sparkles } from 'lucide-react';
import { ApiError } from '../api/client';
import { DisclaimerBanner } from '../components/DisclaimerBanner';
import { useAuth } from '../context/AuthContext';

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const fromPath = (location.state as { from?: string } | null)?.from || '/dashboard';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autofillNote, setAutofillNote] = useState<string | null>(null);

  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login({ email: email.trim(), password });
      navigate(fromPath, { replace: true });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(
          err.status === 401
            ? 'Email hoặc mật khẩu không chính xác.'
            : err.status === 403
              ? 'Tài khoản này đang bị tạm khóa.'
              : err.detail,
        );
      } else {
        setError('Không thể kết nối đến máy chủ. Vui lòng thử lại.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const fillDemoUser = () => {
    setEmail('user@demo.local');
    setPassword('DemoUser123!');
    setError(null);
    setAutofillNote('Đã điền sẵn thông tin Tài khoản Người dùng Demo.');
  };

  const fillDemoAdmin = () => {
    setEmail('admin@demo.local');
    setPassword('DemoAdmin123!');
    setError(null);
    setAutofillNote('Đã điền sẵn thông tin Tài khoản Quản trị viên Demo.');
  };

  return (
    <div className="flex min-h-screen flex-col justify-center bg-gradient-to-br from-slate-50 via-teal-50/40 to-slate-100 px-4 py-10">
      <div className="mx-auto w-full max-w-md space-y-5">
        <div className="text-center">
          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-600 text-white shadow-md">
            <Activity className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">DiaGuard AI</h1>
          <p className="mt-1 text-sm text-slate-600">
            Hệ thống Multi-Agent Sàng lọc Nguy cơ &amp; Tư vấn Tiểu đường
          </p>
        </div>

        <DisclaimerBanner />

        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
          <h2 className="text-lg font-semibold text-slate-900">Đăng nhập hệ thống</h2>
          <p className="mt-1 text-xs text-slate-500">
            Đăng nhập để lưu lịch sử sàng lọc và trao đổi cùng Chatbot y khoa.
          </p>

          {/* 1-click Demo Autofill Buttons */}
          <div className="mt-4 rounded-xl border border-teal-100 bg-teal-50/60 p-3">
            <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold text-teal-900">
              <Sparkles className="h-3.5 w-3.5 text-teal-600" />
              <span>Điền nhanh tài khoản trình diễn (Demo)</span>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={fillDemoUser}
                className="rounded-lg border border-teal-200 bg-white px-3 py-2 text-xs font-medium text-teal-800 transition-colors hover:bg-teal-100/70"
              >
                Demo User
              </button>
              <button
                type="button"
                onClick={fillDemoAdmin}
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition-colors hover:bg-slate-100"
              >
                Demo Admin
              </button>
            </div>
            {autofillNote && (
              <p className="mt-2 text-[11px] font-medium text-teal-700">{autofillNote}</p>
            )}
          </div>

          {error && (
            <div
              role="alert"
              className="mt-4 flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-xs text-rose-800"
            >
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-5 space-y-4">
            <div>
              <label htmlFor="login-email" className="mb-1.5 block text-xs font-semibold text-slate-700">
                Email
              </label>
              <div className="relative">
                <Mail className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  id="login-email"
                  type="email"
                  required
                  autoComplete="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full rounded-xl border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-900 placeholder-slate-400 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                />
              </div>
            </div>

            <div>
              <label htmlFor="login-password" className="mb-1.5 block text-xs font-semibold text-slate-700">
                Mật khẩu
              </label>
              <div className="relative">
                <KeyRound className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  id="login-password"
                  type="password"
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-900 placeholder-slate-400 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Đang đăng nhập...</span>
                </>
              ) : (
                <>
                  <LogIn className="h-4 w-4" />
                  <span>Đăng nhập</span>
                </>
              )}
            </button>
          </form>

          <p className="mt-5 text-center text-xs text-slate-600">
            Chưa có tài khoản?{' '}
            <Link to="/register" className="font-semibold text-teal-700 hover:text-teal-800 hover:underline">
              Đăng ký ngay
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
