import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  Activity,
  BookOpenCheck,
  History,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquareText,
  ShieldCheck,
  Stethoscope,
  X,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { DisclaimerBanner } from './DisclaimerBanner';

interface NavItem {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  adminOnly?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { to: '/dashboard', label: 'Tổng quan', icon: LayoutDashboard },
  { to: '/assessment', label: 'Đánh giá nguy cơ', icon: Stethoscope },
  { to: '/chat', label: 'Chatbot Tư vấn', icon: MessageSquareText },
  { to: '/knowledge', label: 'Tri thức & Đồ thị', icon: BookOpenCheck },
  { to: '/history', label: 'Lịch sử đánh giá', icon: History },
  { to: '/admin', label: 'Quản trị hệ thống', icon: ShieldCheck, adminOnly: true },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const visibleItems = NAV_ITEMS.filter((item) => !item.adminOnly || user?.role === 'admin');

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const renderNavLinks = (onNavigate?: () => void) => (
    <nav className="space-y-1">
      {visibleItems.map((item) => {
        const Icon = item.icon;
        return (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
              }`
            }
          >
            <Icon className="h-4 w-4 shrink-0" />
            <span>{item.label}</span>
          </NavLink>
        );
      })}
    </nav>
  );

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 lg:flex">
      {/* Desktop Sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-white lg:flex">
        <div className="flex items-center gap-2.5 border-b border-slate-100 px-5 py-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-600 text-white shadow-sm">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-bold tracking-tight text-slate-900">DiaGuard AI</p>
            <p className="text-[11px] text-slate-500">Multi-Agent Screening</p>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-4">{renderNavLinks()}</div>

        <div className="border-t border-slate-100 p-4">
          <div className="mb-3 rounded-xl bg-slate-50 p-3">
            <p className="truncate text-sm font-semibold text-slate-900">
              {user?.full_name || 'Người dùng'}
            </p>
            <p className="truncate text-xs text-slate-500">{user?.email}</p>
            <span className="mt-1.5 inline-block rounded-full bg-teal-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-teal-800">
              {user?.role === 'admin' ? 'Quản trị viên' : 'Thành viên'}
            </span>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-rose-50 hover:border-rose-200 hover:text-rose-700"
          >
            <LogOut className="h-4 w-4" />
            <span>Đăng xuất</span>
          </button>
        </div>
      </aside>

      {/* Mobile Header */}
      <header className="sticky top-0 z-30 flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 lg:hidden">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-600 text-white">
            <Activity className="h-4 w-4" />
          </div>
          <span className="text-sm font-bold text-slate-900">DiaGuard AI</span>
        </div>
        <button
          type="button"
          onClick={() => setMobileMenuOpen((prev) => !prev)}
          aria-label="Mở menu điều hướng"
          className="rounded-lg border border-slate-200 p-2 text-slate-700 hover:bg-slate-100"
        >
          {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </header>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-40 flex lg:hidden">
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="relative z-50 flex w-72 max-w-[85vw] flex-col bg-white shadow-xl">
            <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-600 text-white">
                  <Activity className="h-4 w-4" />
                </div>
                <span className="text-sm font-bold text-slate-900">DiaGuard AI</span>
              </div>
              <button
                type="button"
                onClick={() => setMobileMenuOpen(false)}
                className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-3 py-4">
              {renderNavLinks(() => setMobileMenuOpen(false))}
            </div>
            <div className="border-t border-slate-100 p-4">
              <p className="truncate text-sm font-semibold text-slate-900">{user?.full_name}</p>
              <p className="mb-3 truncate text-xs text-slate-500">{user?.email}</p>
              <button
                type="button"
                onClick={handleLogout}
                className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-rose-50 hover:text-rose-700"
              >
                <LogOut className="h-4 w-4" />
                <span>Đăng xuất</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="min-w-0 flex-1">
        <div className="mx-auto max-w-7xl space-y-6 px-4 py-5 sm:px-6 lg:px-8 lg:py-7">
          <DisclaimerBanner />
          {children}
        </div>
      </main>
    </div>
  );
}
