import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  Cpu,
  Database,
  FileText,
  FileUp,
  Loader2,
  RefreshCw,
  ShieldCheck,
  Trash2,
  Users,
} from 'lucide-react';
import { ApiError, apiClient } from '../api/client';
import { AgentTracePanel } from '../components/AgentTracePanel';
import { useAuth } from '../context/AuthContext';
import type {
  AdminAgentRunOut,
  AdminDocumentOut,
  AdminStatsOut,
  User,
} from '../types/api';
import { formatDateTimeVi } from '../utils/format';

type AdminTab = 'documents' | 'monitoring' | 'users';

const AGENT_DISPLAY_NAMES: Record<string, string> = {
  orchestrator: '1. Orchestrator Agent',
  data_analysis: '2. Data Analysis Agent',
  prediction: '3. Prediction Agent',
  knowledge: '4. Knowledge Agent',
  consultation: '5. Consultation Agent',
};

export function AdminPage() {
  const { user: currentUser } = useAuth();
  const [activeTab, setActiveTab] = useState<AdminTab>('documents');

  const [documents, setDocuments] = useState<AdminDocumentOut[]>([]);
  const [stats, setStats] = useState<AdminStatsOut | null>(null);
  const [agentRuns, setAgentRuns] = useState<AdminAgentRunOut[]>([]);
  const [users, setUsers] = useState<User[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  // Upload form state
  const [title, setTitle] = useState('');
  const [publisher, setPublisher] = useState('');
  const [language, setLanguage] = useState('vi');
  const [sourceUrl, setSourceUrl] = useState('');
  const [sourceId, setSourceId] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // Row action states
  const [busyDocId, setBusyDocId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [expandedRunId, setExpandedRunId] = useState<string | null>(null);
  const [busyUserId, setBusyUserId] = useState<string | null>(null);

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [docsRes, statsRes, runsRes, usersRes] = await Promise.all([
        apiClient.listAdminDocuments(),
        apiClient.getAdminStats(),
        apiClient.listAdminAgentRuns(50),
        apiClient.listAdminUsers(),
      ]);
      setDocuments(docsRes);
      setStats(statsRes);
      setAgentRuns(runsRes);
      setUsers(usersRes);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : 'Không thể tải dữ liệu quản trị từ máy chủ.',
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setNotice(null);

    if (!selectedFile) {
      setError('Vui lòng chọn tệp tài liệu (.pdf, .txt hoặc .md).');
      return;
    }

    const ext = selectedFile.name.split('.').pop()?.toLowerCase() ?? '';
    if (!['pdf', 'txt', 'md'].includes(ext)) {
      setError('Chỉ hỗ trợ định dạng tệp .pdf, .txt hoặc .md.');
      return;
    }

    if (selectedFile.size > 5 * 1024 * 1024) {
      setError('Kích thước tệp vượt quá giới hạn tối đa 5 MB.');
      return;
    }

    const formData = new FormData();
    formData.append('title', title.trim());
    formData.append('publisher', publisher.trim());
    formData.append('language', language);
    if (sourceUrl.trim()) formData.append('source_url', sourceUrl.trim());
    if (sourceId.trim()) formData.append('source_id', sourceId.trim());
    formData.append('file', selectedFile);

    setUploading(true);
    try {
      const created = await apiClient.uploadAdminDocument(formData);
      setDocuments((prev) => [created, ...prev]);
      setTitle('');
      setPublisher('');
      setSourceUrl('');
      setSourceId('');
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      setNotice(
        `Đã nạp thành công tài liệu "${created.title}" (${created.chunk_count} chunks) vào ChromaDB.`,
      );
      const refreshedStats = await apiClient.getAdminStats();
      setStats(refreshedStats);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail : 'Không thể tải lên và nạp tài liệu.',
      );
    } finally {
      setUploading(false);
    }
  };

  const handleToggleDocumentStatus = async (doc: AdminDocumentOut) => {
    const nextStatus = doc.status === 'active' ? 'inactive' : 'active';
    setBusyDocId(doc.id);
    setError(null);
    setNotice(null);
    try {
      const updated = await apiClient.updateAdminDocumentStatus(doc.id, {
        status: nextStatus,
      });
      setDocuments((prev) => prev.map((d) => (d.id === doc.id ? updated : d)));
      setNotice(
        `Đã chuyển tài liệu "${updated.source_id}" sang trạng thái ${
          updated.status === 'active' ? 'Hoạt động (Active)' : 'Tạm ẩn (Inactive)'
        } trên RAG & KG.`,
      );
      const refreshedStats = await apiClient.getAdminStats();
      setStats(refreshedStats);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail : 'Không thể cập nhật trạng thái tài liệu.',
      );
    } finally {
      setBusyDocId(null);
    }
  };

  const handleDeleteDocument = async (doc: AdminDocumentOut) => {
    setBusyDocId(doc.id);
    setError(null);
    setNotice(null);
    try {
      await apiClient.deleteAdminDocument(doc.id);
      setDocuments((prev) => prev.filter((d) => d.id !== doc.id));
      setConfirmDeleteId(null);
      setNotice(`Đã xóa vĩnh viễn tài liệu "${doc.title}" khỏi SQL, ChromaDB và KG.`);
      const refreshedStats = await apiClient.getAdminStats();
      setStats(refreshedStats);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Không thể xóa tài liệu.');
    } finally {
      setBusyDocId(null);
    }
  };

  const handleToggleUserActive = async (targetUser: User) => {
    if (targetUser.id === currentUser?.id) return;
    setBusyUserId(targetUser.id);
    setError(null);
    setNotice(null);
    try {
      const updated = await apiClient.updateAdminUser(targetUser.id, {
        is_active: !targetUser.is_active,
      });
      setUsers((prev) => prev.map((u) => (u.id === targetUser.id ? updated : u)));
      setNotice(
        `Đã ${updated.is_active ? 'kích hoạt' : 'tạm khóa'} tài khoản ${updated.email}.`,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Không thể cập nhật tài khoản.');
    } finally {
      setBusyUserId(null);
    }
  };

  const handleChangeUserRole = async (targetUser: User, newRole: 'user' | 'admin') => {
    if (targetUser.id === currentUser?.id || targetUser.role === newRole) return;
    setBusyUserId(targetUser.id);
    setError(null);
    setNotice(null);
    try {
      const updated = await apiClient.updateAdminUser(targetUser.id, {
        role: newRole,
      });
      setUsers((prev) => prev.map((u) => (u.id === targetUser.id ? updated : u)));
      setNotice(`Đã cập nhật vai trò của ${updated.email} thành "${updated.role}".`);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Không thể thay đổi vai trò người dùng.');
    } finally {
      setBusyUserId(null);
    }
  };

  const maxAgentLatency = Math.max(
    1,
    ...Object.values(stats?.per_agent_latency_ms ?? {}),
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col justify-between gap-3 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:flex-row sm:items-center">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
            <ShieldCheck className="h-3.5 w-3.5" />
            Admin Control Portal
          </span>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900">
            Quản trị Hệ thống Multi-Agent &amp; Tri thức
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Quản lý tài liệu RAG/KG, giám sát hiệu năng 5-Agent và phân quyền người dùng.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadAll()}
          disabled={loading}
          className="inline-flex items-center gap-2 self-start rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>Làm mới dữ liệu</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
        <button
          type="button"
          onClick={() => setActiveTab('documents')}
          className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-colors ${
            activeTab === 'documents'
              ? 'bg-teal-600 text-white shadow-sm'
              : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
          }`}
        >
          <FileText className="h-4 w-4" />
          <span>Tài liệu Tri thức ({documents.length})</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('monitoring')}
          className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-colors ${
            activeTab === 'monitoring'
              ? 'bg-teal-600 text-white shadow-sm'
              : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
          }`}
        >
          <Activity className="h-4 w-4" />
          <span>Giám sát Multi-Agent ({stats?.total_agent_runs ?? agentRuns.length})</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('users')}
          className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-colors ${
            activeTab === 'users'
              ? 'bg-teal-600 text-white shadow-sm'
              : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
          }`}
        >
          <Users className="h-4 w-4" />
          <span>Quản lý Người dùng ({users.length})</span>
        </button>
      </div>

      {error && (
        <div
          role="alert"
          className="flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800"
        >
          <AlertCircle className="h-4 w-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {notice && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
          <span>{notice}</span>
        </div>
      )}

      {loading ? (
        <div className="flex h-64 items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-500">
          <Loader2 className="mr-2 h-5 w-5 animate-spin text-teal-600" />
          Đang tải bảng điều khiển quản trị...
        </div>
      ) : activeTab === 'documents' ? (
        <div className="grid gap-6 lg:grid-cols-12">
          {/* Upload Form */}
          <form
            onSubmit={handleUpload}
            className="space-y-4 self-start rounded-2xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-4"
          >
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-teal-50 text-teal-700">
                <FileUp className="h-4 w-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-900">Nạp tài liệu y khoa mới</h2>
                <p className="text-[11px] text-slate-500">Hỗ trợ .pdf, .txt, .md (tối đa 5 MB)</p>
              </div>
            </div>

            <div>
              <label htmlFor="doc-title" className="mb-1 block text-xs font-semibold text-slate-700">
                Tiêu đề tài liệu *
              </label>
              <input
                id="doc-title"
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="VD: Hướng dẫn dinh dưỡng tiểu đường Bộ Y tế"
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
              />
            </div>

            <div>
              <label
                htmlFor="doc-publisher"
                className="mb-1 block text-xs font-semibold text-slate-700"
              >
                Đơn vị phát hành *
              </label>
              <input
                id="doc-publisher"
                type="text"
                required
                value={publisher}
                onChange={(e) => setPublisher(e.target.value)}
                placeholder="VD: Bộ Y tế / ADA / CDC"
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label
                  htmlFor="doc-language"
                  className="mb-1 block text-xs font-semibold text-slate-700"
                >
                  Ngôn ngữ
                </label>
                <select
                  id="doc-language"
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                >
                  <option value="vi">Tiếng Việt (vi)</option>
                  <option value="en">Tiếng Anh (en)</option>
                </select>
              </div>
              <div>
                <label
                  htmlFor="doc-source-id"
                  className="mb-1 block text-xs font-semibold text-slate-700"
                >
                  Source ID <span className="font-normal text-slate-400">(tùy chọn)</span>
                </label>
                <input
                  id="doc-source-id"
                  type="text"
                  value={sourceId}
                  onChange={(e) => setSourceId(e.target.value)}
                  placeholder="VD: BYT-008"
                  className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                />
              </div>
            </div>

            <div>
              <label htmlFor="doc-url" className="mb-1 block text-xs font-semibold text-slate-700">
                Đường dẫn nguồn <span className="font-normal text-slate-400">(tùy chọn)</span>
              </label>
              <input
                id="doc-url"
                type="url"
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                placeholder="https://..."
                className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
              />
            </div>

            <div>
              <label htmlFor="doc-file" className="mb-1 block text-xs font-semibold text-slate-700">
                Tệp tài liệu (.pdf, .txt, .md) *
              </label>
              <input
                ref={fileInputRef}
                id="doc-file"
                type="file"
                accept=".pdf,.txt,.md"
                onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
                className="block w-full rounded-xl border border-slate-300 bg-slate-50 px-3 py-2 text-xs text-slate-700 file:mr-3 file:rounded-lg file:border-0 file:bg-teal-600 file:px-3 file:py-1.5 file:text-xs file:font-semibold file:text-white hover:file:bg-teal-700"
              />
              {selectedFile && (
                <p className="mt-1 text-[11px] text-slate-500">
                  Đã chọn: {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={uploading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-teal-700 disabled:opacity-60"
            >
              {uploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Đang tách chunk &amp; nhúng vector...</span>
                </>
              ) : (
                <>
                  <FileUp className="h-4 w-4" />
                  <span>Tải lên &amp; Nạp tri thức</span>
                </>
              )}
            </button>
          </form>

          {/* Documents Table */}
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm lg:col-span-8">
            <div className="border-b border-slate-100 px-5 py-4">
              <h2 className="text-sm font-bold text-slate-900">
                Danh sách Tài liệu trong ChromaDB &amp; SQL ({documents.length})
              </h2>
              <p className="text-xs text-slate-500">
                Bật/tắt trạng thái sẽ cập nhật ngay lập tức phạm vi truy xuất của RAG và Knowledge Graph.
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Tài liệu</th>
                    <th className="px-4 py-3">Source ID</th>
                    <th className="px-4 py-3">Đơn vị / Ngôn ngữ</th>
                    <th className="px-4 py-3">Chunks</th>
                    <th className="px-4 py-3">Trạng thái</th>
                    <th className="px-4 py-3 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {documents.map((doc) => {
                    const isBusy = busyDocId === doc.id;
                    const isConfirming = confirmDeleteId === doc.id;
                    return (
                      <tr key={doc.id} className="hover:bg-slate-50/70">
                        <td className="max-w-xs px-4 py-3">
                          <p className="font-semibold text-slate-900">{doc.title}</p>
                          <p className="mt-0.5 text-[10px] text-slate-400">
                            {formatDateTimeVi(doc.updated_at)}
                          </p>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 font-mono text-[11px] text-slate-700">
                          {doc.source_id}
                        </td>
                        <td className="px-4 py-3 text-slate-600">
                          <span className="font-medium text-slate-800">{doc.publisher}</span>
                          <span className="ml-1.5 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] uppercase">
                            {doc.language}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 font-mono font-semibold text-slate-800">
                          {doc.chunk_count}
                        </td>
                        <td className="whitespace-nowrap px-4 py-3">
                          <span
                            className={`inline-flex rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${
                              doc.status === 'active'
                                ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                                : 'border-slate-300 bg-slate-100 text-slate-600'
                            }`}
                          >
                            {doc.status === 'active' ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="whitespace-nowrap px-4 py-3 text-right">
                          {isConfirming ? (
                            <div className="inline-flex items-center gap-1.5">
                              <button
                                type="button"
                                disabled={isBusy}
                                onClick={() => void handleDeleteDocument(doc)}
                                className="rounded-lg bg-rose-600 px-2.5 py-1 text-[11px] font-semibold text-white hover:bg-rose-700 disabled:opacity-50"
                              >
                                Xác nhận xóa
                              </button>
                              <button
                                type="button"
                                onClick={() => setConfirmDeleteId(null)}
                                className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-medium text-slate-600 hover:bg-slate-50"
                              >
                                Hủy
                              </button>
                            </div>
                          ) : (
                            <div className="inline-flex items-center gap-1.5">
                              <button
                                type="button"
                                disabled={isBusy}
                                onClick={() => void handleToggleDocumentStatus(doc)}
                                className={`rounded-lg border px-2.5 py-1 text-[11px] font-semibold transition-colors disabled:opacity-50 ${
                                  doc.status === 'active'
                                    ? 'border-amber-200 bg-amber-50 text-amber-800 hover:bg-amber-100'
                                    : 'border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                                }`}
                              >
                                {doc.status === 'active' ? 'Tạm ẩn' : 'Kích hoạt'}
                              </button>
                              <button
                                type="button"
                                disabled={isBusy}
                                onClick={() => setConfirmDeleteId(doc.id)}
                                aria-label={`Xóa ${doc.title}`}
                                className="rounded-lg border border-rose-200 bg-white p-1.5 text-rose-600 hover:bg-rose-50 disabled:opacity-50"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : activeTab === 'monitoring' ? (
        <div className="space-y-6">
          {/* KPI Grid */}
          {stats && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
              <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-xs font-medium text-slate-500">Người dùng</p>
                <p className="mt-1 text-2xl font-bold text-slate-900">{stats.total_users}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-xs font-medium text-slate-500">Lượt sàng lọc</p>
                <p className="mt-1 text-2xl font-bold text-slate-900">{stats.total_assessments}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-xs font-medium text-slate-500">Tài liệu Active / Tổng</p>
                <p className="mt-1 text-2xl font-bold text-teal-700">
                  {stats.active_documents}{' '}
                  <span className="text-sm font-normal text-slate-400">
                    / {stats.total_documents}
                  </span>
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-xs font-medium text-slate-500">Tổng Vector Chunks</p>
                <p className="mt-1 text-2xl font-bold text-slate-900">{stats.total_chunks}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-xs font-medium text-slate-500">Phiên chạy Agent</p>
                <p className="mt-1 text-2xl font-bold text-slate-900">{stats.total_agent_runs}</p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-xs font-medium text-slate-500">Độ trễ trung bình</p>
                <p className="mt-1 text-2xl font-bold text-indigo-700">
                  {Math.round(stats.avg_latency_ms)} ms
                </p>
              </div>
            </div>
          )}

          {/* Per-agent Latency Breakdown & Status Counts */}
          {stats && (
            <div className="grid gap-5 lg:grid-cols-12">
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-7">
                <div className="mb-4 flex items-center gap-2">
                  <Clock className="h-4 w-4 text-teal-600" />
                  <h2 className="text-sm font-bold text-slate-900">
                    Độ trễ trung bình theo từng Agent (ms)
                  </h2>
                </div>
                {Object.keys(stats.per_agent_latency_ms).length === 0 ? (
                  <p className="text-xs text-slate-500">Chưa có dữ liệu thực thi Agent.</p>
                ) : (
                  <div className="space-y-3">
                    {Object.entries(stats.per_agent_latency_ms).map(([agentKey, ms]) => {
                      const pct = Math.min(100, Math.round((ms / maxAgentLatency) * 100));
                      return (
                        <div key={agentKey}>
                          <div className="mb-1 flex items-center justify-between text-xs">
                            <span className="font-semibold text-slate-800">
                              {AGENT_DISPLAY_NAMES[agentKey] ?? agentKey}
                            </span>
                            <span className="font-mono text-slate-600">{ms.toFixed(1)} ms</span>
                          </div>
                          <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                            <div
                              className="h-full rounded-full bg-teal-600"
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-5">
                <div className="mb-4 flex items-center gap-2">
                  <Database className="h-4 w-4 text-indigo-600" />
                  <h2 className="text-sm font-bold text-slate-900">
                    Phân bổ trạng thái thực thi
                  </h2>
                </div>
                {Object.keys(stats.agent_status_counts).length === 0 ? (
                  <p className="text-xs text-slate-500">Chưa có bản ghi chạy nào.</p>
                ) : (
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(stats.agent_status_counts).map(([st, count]) => (
                      <div
                        key={st}
                        className="rounded-xl border border-slate-200 bg-slate-50 p-3"
                      >
                        <p className="text-[11px] font-semibold uppercase text-slate-500">{st}</p>
                        <p className="mt-1 text-xl font-bold text-slate-900">{count}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Recent Agent Runs Table */}
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-100 px-5 py-4">
              <h2 className="text-sm font-bold text-slate-900">
                Nhật ký thực thi Multi-Agent gần đây ({agentRuns.length})
              </h2>
              <p className="text-xs text-slate-500">
                Chỉ hiển thị metadata ẩn danh (không chứa chỉ số sức khỏe thô). Nhấn vào từng dòng để xem execution trace.
              </p>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
                <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Request ID</th>
                    <th className="px-4 py-3">Tác vụ</th>
                    <th className="px-4 py-3">Trạng thái</th>
                    <th className="px-4 py-3">LLM Provider / Model</th>
                    <th className="px-4 py-3">Độ trễ</th>
                    <th className="px-4 py-3">Thời gian</th>
                    <th className="px-4 py-3 text-right">Trace</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {agentRuns.map((run) => {
                    const isExpanded = expandedRunId === run.id;
                    return (
                      <React.Fragment key={run.id}>
                        <tr className="hover:bg-slate-50/70">
                          <td className="whitespace-nowrap px-4 py-3 font-mono text-[11px] font-semibold text-slate-800">
                            {run.request_id}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3">
                            <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[11px] font-medium text-slate-700">
                              {run.task_type}
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-4 py-3">
                            <span
                              className={`rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${
                                run.status === 'completed'
                                  ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                                  : run.status === 'failed'
                                    ? 'border-rose-200 bg-rose-50 text-rose-700'
                                    : 'border-amber-200 bg-amber-50 text-amber-800'
                              }`}
                            >
                              {run.status}
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-slate-600">
                            <span className="inline-flex items-center gap-1 font-mono text-[11px]">
                              <Cpu className="h-3.5 w-3.5 text-slate-400" />
                              {run.llm_provider} / {run.llm_model}
                            </span>
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 font-mono font-semibold text-slate-800">
                            {run.total_latency_ms} ms
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-slate-500">
                            {formatDateTimeVi(run.created_at)}
                          </td>
                          <td className="whitespace-nowrap px-4 py-3 text-right">
                            <button
                              type="button"
                              onClick={() =>
                                setExpandedRunId(isExpanded ? null : run.id)
                              }
                              className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-100"
                            >
                              <span>{run.agent_steps.length} bước</span>
                              {isExpanded ? (
                                <ChevronUp className="h-3.5 w-3.5" />
                              ) : (
                                <ChevronDown className="h-3.5 w-3.5" />
                              )}
                            </button>
                          </td>
                        </tr>
                        {isExpanded && (
                          <tr className="bg-slate-50/70">
                            <td colSpan={7} className="p-4">
                              <AgentTracePanel
                                steps={run.agent_steps}
                                totalLatencyMs={run.total_latency_ms}
                                title={`Trace cho ${run.request_id}`}
                              />
                            </td>
                          </tr>
                        )}
                      </React.Fragment>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        /* TAB 3: User Management */
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-100 px-5 py-4">
            <h2 className="text-sm font-bold text-slate-900">
              Danh sách Tài khoản Người dùng ({users.length})
            </h2>
            <p className="text-xs text-slate-500">
              Quản trị viên không thể tự khóa hoặc hạ quyền tài khoản đang đăng nhập của chính mình.
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-3">Họ và tên</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Vai trò</th>
                  <th className="px-4 py-3">Trạng thái</th>
                  <th className="px-4 py-3">Ngày tạo</th>
                  <th className="px-4 py-3 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((u) => {
                  const isSelf = u.id === currentUser?.id;
                  const isBusy = busyUserId === u.id;
                  return (
                    <tr key={u.id} className="hover:bg-slate-50/70">
                      <td className="whitespace-nowrap px-4 py-3 font-semibold text-slate-900">
                        {u.full_name}
                        {isSelf && (
                          <span className="ml-2 rounded-full bg-teal-100 px-2 py-0.5 text-[10px] font-semibold text-teal-800">
                            Bạn
                          </span>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-slate-600">{u.email}</td>
                      <td className="whitespace-nowrap px-4 py-3">
                        <select
                          aria-label={`Vai trò cho ${u.email}`}
                          disabled={isSelf || isBusy}
                          value={u.role}
                          onChange={(e) =>
                            void handleChangeUserRole(
                              u,
                              e.target.value as 'user' | 'admin',
                            )
                          }
                          className="rounded-lg border border-slate-300 bg-white px-2.5 py-1 text-xs font-medium text-slate-800 disabled:cursor-not-allowed disabled:bg-slate-100 disabled:text-slate-400"
                        >
                          <option value="user">user</option>
                          <option value="admin">admin</option>
                        </select>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3">
                        <span
                          className={`inline-flex rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${
                            u.is_active
                              ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                              : 'border-rose-200 bg-rose-50 text-rose-700'
                          }`}
                        >
                          {u.is_active ? 'Đang hoạt động' : 'Đã khóa'}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-slate-500">
                        {formatDateTimeVi(u.created_at)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-right">
                        <button
                          type="button"
                          disabled={isSelf || isBusy}
                          title={
                            isSelf
                              ? 'Không thể tự khóa tài khoản quản trị đang sử dụng'
                              : undefined
                          }
                          onClick={() => void handleToggleUserActive(u)}
                          className={`rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
                            u.is_active
                              ? 'border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100'
                              : 'border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                          }`}
                        >
                          {u.is_active ? 'Tạm khóa' : 'Kích hoạt'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
