import React from 'react';
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { ArrowLeft, Construction, Loader2 } from 'lucide-react';
import { Layout } from './components/Layout';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AssessmentPage } from './pages/AssessmentPage';
import { DashboardPage } from './pages/DashboardPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';

function RequireAuth({
  children,
  adminOnly = false,
}: {
  children: React.ReactNode;
  adminOnly?: boolean;
}) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 text-sm text-slate-600">
        <Loader2 className="mr-2 h-5 w-5 animate-spin text-teal-600" />
        Đang kiểm tra phiên đăng nhập...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: `${location.pathname}${location.search}` }} replace />;
  }

  if (adminOnly && user.role !== 'admin') {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
}

function PlaceholderRoute({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
        <Construction className="h-6 w-6" />
      </div>
      <h1 className="text-xl font-bold text-slate-900">{title}</h1>
      <p className="mx-auto mt-2 max-w-lg text-sm text-slate-600">{description}</p>
      <div className="mt-5 flex justify-center gap-3">
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          <ArrowLeft className="h-4 w-4" />
          Về Tổng quan
        </Link>
        <Link
          to="/assessment"
          className="inline-flex items-center gap-2 rounded-xl bg-teal-600 px-4 py-2 text-sm font-semibold text-white hover:bg-teal-700"
        >
          Mở Đánh giá nguy cơ
        </Link>
      </div>
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route
            path="/dashboard"
            element={
              <RequireAuth>
                <Layout>
                  <DashboardPage />
                </Layout>
              </RequireAuth>
            }
          />
          <Route
            path="/assessment"
            element={
              <RequireAuth>
                <Layout>
                  <AssessmentPage />
                </Layout>
              </RequireAuth>
            }
          />
          <Route
            path="/chat"
            element={
              <RequireAuth>
                <Layout>
                  <PlaceholderRoute
                    title="Chatbot Tư vấn Tiểu đường"
                    description="Màn hình hội thoại AI đa phiên với trích dẫn RAG + Knowledge Graph sẽ được hoàn thiện trong bước tiếp theo."
                  />
                </Layout>
              </RequireAuth>
            }
          />
          <Route
            path="/knowledge"
            element={
              <RequireAuth>
                <Layout>
                  <PlaceholderRoute
                    title="Tra cứu Tri thức & Đồ thị Y khoa"
                    description="Màn hình tra cứu tài liệu y khoa chuẩn hóa và trực quan hóa Diabetes Knowledge Graph sẽ được hoàn thiện trong bước tiếp theo."
                  />
                </Layout>
              </RequireAuth>
            }
          />
          <Route
            path="/history"
            element={
              <RequireAuth>
                <Layout>
                  <PlaceholderRoute
                    title="Lịch sử Đánh giá Nguy cơ"
                    description="Bảng lịch sử đánh giá cá nhân và chi tiết biểu đồ đặc trưng đã lưu sẽ được hoàn thiện trong bước tiếp theo."
                  />
                </Layout>
              </RequireAuth>
            }
          />
          <Route
            path="/admin"
            element={
              <RequireAuth adminOnly>
                <Layout>
                  <PlaceholderRoute
                    title="Quản trị Hệ thống Multi-Agent"
                    description="Bảng điều khiển quản lý tài liệu RAG, giám sát độ trễ Multi-Agent và tài khoản người dùng sẽ được hoàn thiện trong bước tiếp theo."
                  />
                </Layout>
              </RequireAuth>
            }
          />

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
