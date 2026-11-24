import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  AlertCircle,
  ArrowRight,
  BookOpenCheck,
  Bot,
  Cpu,
  Database,
  History,
  Loader2,
  MessageSquareText,
  Network,
  Stethoscope,
} from 'lucide-react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { apiClient } from '../api/client';
import { RiskBadge } from '../components/RiskBadge';
import { useAuth } from '../context/AuthContext';
import type { AssessmentOut, HealthResponse } from '../types/api';

function formatShortDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return date.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
  });
}

function formatDateTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return date.toLocaleString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function DashboardPage() {
  const { user } = useAuth();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [assessments, setAssessments] = useState<AssessmentOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [healthRes, assessmentsRes] = await Promise.all([
          apiClient.getHealth(),
          apiClient.listAssessments(),
        ]);
        if (!active) return;
        setHealth(healthRes);
        setAssessments(assessmentsRes);
      } catch {
        if (!active) return;
        setError('Không thể tải đầy đủ dữ liệu tổng quan từ máy chủ.');
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, []);

  const latestAssessment = assessments[0] ?? null;

  const trendData = useMemo(() => {
    return assessments
      .filter((item) => item.status === 'completed' && item.prediction)
      .slice()
      .reverse()
      .map((item, idx) => ({
        index: idx + 1,
        label: formatShortDate(item.created_at),
        fullDate: formatDateTime(item.created_at),
        scorePct: Number(((item.prediction?.model_score ?? 0) * 100).toFixed(1)),
        bmi: item.derived_features?.bmi ?? null,
      }));
  }, [assessments]);

  const shaPrefix = health?.ml_model.model_sha256
    ? `${health.ml_model.model_sha256.slice(0, 12)}...`
    : 'N/A';

  return (
    <div className="space-y-6">
      {/* Welcome Header & Quick Actions */}
      <div className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm md:flex-row md:items-center">
        <div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-700">
            <Activity className="h-3.5 w-3.5" />
            Bảng điều khiển sàng lọc
          </span>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900">
            Xin chào, {user?.full_name || 'bạn'}
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Theo dõi kết quả sàng lọc HbA1c ≥ 5.7% trên nền tảng NHANES và trạng thái hệ thống 5-Agent.
          </p>
        </div>

        <div className="flex flex-wrap gap-2.5">
          <Link
            to="/assessment"
            className="inline-flex items-center gap-2 rounded-xl bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-teal-700"
          >
            <Stethoscope className="h-4 w-4" />
            <span>Đánh giá nguy cơ mới</span>
          </Link>
          <Link
            to="/chat"
            className="inline-flex items-center gap-2 rounded-xl border border-teal-200 bg-teal-50 px-4 py-2.5 text-sm font-semibold text-teal-800 transition-colors hover:bg-teal-100"
          >
            <MessageSquareText className="h-4 w-4" />
            <span>Hỏi Chatbot</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* System Health Status Cards */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500">
            Trạng thái hạ tầng Multi-Agent &amp; AI
          </h2>
          {health && (
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                health.status === 'ok'
                  ? 'bg-emerald-50 text-emerald-700'
                  : 'bg-amber-50 text-amber-800'
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  health.status === 'ok' ? 'bg-emerald-500' : 'bg-amber-500'
                }`}
              />
              {health.status === 'ok' ? 'Hệ thống sẵn sàng' : 'Đang hoạt động giới hạn'}
            </span>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {/* ML Model Card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-50 text-teal-700">
                <Cpu className="h-5 w-5" />
              </div>
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                  health?.ml_model.loaded
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'bg-rose-50 text-rose-700'
                }`}
              >
                {loading ? '...' : health?.ml_model.loaded ? 'Đã xác thực' : 'Chưa nạp'}
              </span>
            </div>
            <p className="mt-3 text-xs font-medium text-slate-500">Mô hình dự báo ML</p>
            <p className="mt-0.5 truncate text-sm font-bold text-slate-900">
              {health?.ml_model.model_name || 'NHANES HbA1c v2'}
            </p>
            <p className="mt-1 font-mono text-[11px] text-slate-500">
              v{health?.ml_model.model_version || '2'} • SHA256: {shaPrefix}
            </p>
          </div>

          {/* ChromaDB Card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-50 text-sky-700">
                <Database className="h-5 w-5" />
              </div>
              <span className="rounded-full bg-sky-50 px-2 py-0.5 text-[11px] font-semibold text-sky-700">
                ChromaDB RAG
              </span>
            </div>
            <p className="mt-3 text-xs font-medium text-slate-500">Kho tài liệu y khoa</p>
            <p className="mt-0.5 text-sm font-bold text-slate-900">
              {loading ? '...' : `${health?.knowledge_base.active_documents ?? 0} tài liệu hoạt động`}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {health?.knowledge_base.total_chunks ?? 0} vector chunks đang phục vụ
            </p>
          </div>

          {/* Knowledge Graph Card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-50 text-indigo-700">
                <Network className="h-5 w-5" />
              </div>
              <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-[11px] font-semibold text-indigo-700">
                {health?.knowledge_base.kg_source === 'neo4j' ? 'Neo4j Live' : 'Local Mirror'}
              </span>
            </div>
            <p className="mt-3 text-xs font-medium text-slate-500">Knowledge Graph Tiểu đường</p>
            <p className="mt-0.5 text-sm font-bold text-slate-900">
              {health?.knowledge_base.kg_source === 'neo4j'
                ? 'Neo4j Graph DB'
                : 'Đồ thị Tri thức Nội bộ'}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              {health?.knowledge_base.neo4j_configured
                ? health.knowledge_base.neo4j_reachable
                  ? 'Kết nối Neo4j ổn định'
                  : 'Đang dùng bản dự phòng Local JSON'
                : 'Chế độ đồ thị JSON chuẩn hóa'}
            </p>
          </div>

          {/* LLM Provider Card */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700">
                <Bot className="h-5 w-5" />
              </div>
              <span
                className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                  health?.llm.reachable
                    ? 'bg-emerald-50 text-emerald-700'
                    : 'bg-amber-50 text-amber-800'
                }`}
              >
                {loading ? '...' : health?.llm.reachable ? 'Trực tuyến' : 'Chế độ dự phòng'}
              </span>
            </div>
            <p className="mt-3 text-xs font-medium text-slate-500">LLM Tư vấn (Consultation)</p>
            <p className="mt-0.5 truncate text-sm font-bold text-slate-900">
              {health?.llm.provider ? `${health.llm.provider.toUpperCase()}` : 'Ollama'}
            </p>
            <p className="mt-1 truncate font-mono text-[11px] text-slate-500">
              {health?.llm.model || 'Chưa cấu hình model'}
            </p>
          </div>
        </div>
      </section>

      {/* Main Grid: Latest Assessment + Trend Chart */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Latest Assessment Summary Card */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:col-span-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900">Lần đánh giá gần nhất</h2>
            <Link
              to="/history"
              className="inline-flex items-center gap-1 text-xs font-semibold text-teal-700 hover:text-teal-800"
            >
              <span>Xem lịch sử</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {loading ? (
            <div className="flex h-48 items-center justify-center text-sm text-slate-500">
              <Loader2 className="mr-2 h-4 w-4 animate-spin text-teal-600" />
              Đang tải dữ liệu...
            </div>
          ) : latestAssessment ? (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <RiskBadge
                  band={
                    latestAssessment.status === 'out_of_scope'
                      ? 'out_of_scope'
                      : latestAssessment.prediction?.risk_band || 'out_of_scope'
                  }
                  size="lg"
                />
                <span className="text-xs text-slate-500">
                  {formatDateTime(latestAssessment.created_at)}
                </span>
              </div>

              {latestAssessment.status === 'completed' && latestAssessment.prediction ? (
                <>
                  <div className="grid grid-cols-3 gap-3 rounded-xl bg-slate-50 p-3.5">
                    <div>
                      <p className="text-[11px] text-slate-500">Điểm nguy cơ</p>
                      <p className="mt-0.5 text-lg font-bold text-slate-900">
                        {(latestAssessment.prediction.model_score * 100).toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-[11px] text-slate-500">BMI</p>
                      <p className="mt-0.5 text-lg font-bold text-slate-900">
                        {latestAssessment.derived_features?.bmi ?? '—'}
                      </p>
                    </div>
                    <div>
                      <p className="text-[11px] text-slate-500">Vòng eo</p>
                      <p className="mt-0.5 text-lg font-bold text-slate-900">
                        {String(latestAssessment.raw_inputs?.waist_cm ?? '—')} cm
                      </p>
                    </div>
                  </div>
                  <p className="line-clamp-3 text-xs leading-relaxed text-slate-600">
                    {latestAssessment.summary_text}
                  </p>
                </>
              ) : (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-3.5 text-xs leading-relaxed text-amber-900">
                  {latestAssessment.summary_text}
                </div>
              )}

              <div className="flex flex-wrap gap-2 pt-1">
                <Link
                  to="/assessment"
                  className="inline-flex items-center gap-1.5 rounded-xl bg-teal-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-teal-700"
                >
                  <Stethoscope className="h-3.5 w-3.5" />
                  Đánh giá lại
                </Link>
                <Link
                  to={`/chat?assessmentId=${encodeURIComponent(latestAssessment.id)}`}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  <MessageSquareText className="h-3.5 w-3.5" />
                  Hỏi Chatbot về kết quả này
                </Link>
              </div>
            </div>
          ) : (
            <div className="flex h-48 flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/70 p-6 text-center">
              <Stethoscope className="mb-2 h-8 w-8 text-teal-600" />
              <p className="text-sm font-semibold text-slate-800">Chưa có lần đánh giá nào</p>
              <p className="mt-1 text-xs text-slate-500">
                Hãy nhập các chỉ số cơ thể cơ bản để chạy luồng sàng lọc 5-Agent.
              </p>
              <Link
                to="/assessment"
                className="mt-3 inline-flex items-center gap-1.5 rounded-xl bg-teal-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-teal-700"
              >
                Bắt đầu ngay
              </Link>
            </div>
          )}
        </div>

        {/* Trend Chart Card */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:col-span-7">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Xu hướng điểm sàng lọc qua thời gian
              </h2>
              <p className="text-xs text-slate-500">
                Biến thiên xác suất mô hình NHANES (%) qua các lần đánh giá hợp lệ
              </p>
            </div>
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
              {trendData.length} lượt hợp lệ
            </span>
          </div>

          {trendData.length > 0 ? (
            <div className="h-60 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData} margin={{ top: 10, right: 16, left: -12, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: '#64748b' }} />
                  <YAxis
                    domain={[0, 100]}
                    tick={{ fontSize: 11, fill: '#64748b' }}
                    tickFormatter={(v: number) => `${v}%`}
                  />
                  <Tooltip
                    formatter={(value: number) => [`${value}%`, 'Điểm nguy cơ']}
                    labelFormatter={(_, payload) =>
                      payload && payload[0]
                        ? String((payload[0].payload as { fullDate: string }).fullDate)
                        : ''
                    }
                  />
                  <Line
                    type="monotone"
                    dataKey="scorePct"
                    stroke="#0d9488"
                    strokeWidth={2.5}
                    dot={{ r: 4, fill: '#0d9488', strokeWidth: 2, stroke: '#ffffff' }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex h-60 flex-col items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50/70 p-6 text-center">
              <p className="text-sm font-medium text-slate-700">Chưa có dữ liệu xu hướng</p>
              <p className="mt-1 text-xs text-slate-500">
                Biểu đồ sẽ hiển thị sau khi bạn hoàn tất ít nhất một lần sàng lọc hợp lệ.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Navigation Tiles */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link
          to="/assessment"
          className="group rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition-all hover:border-teal-300 hover:shadow"
        >
          <div className="flex items-center justify-between">
            <Stethoscope className="h-5 w-5 text-teal-600" />
            <ArrowRight className="h-4 w-4 text-slate-400 transition-transform group-hover:translate-x-0.5 group-hover:text-teal-600" />
          </div>
          <p className="mt-3 text-sm font-semibold text-slate-900">Sàng lọc Nguy cơ</p>
          <p className="mt-1 text-xs text-slate-500">
            Nhập chỉ số cơ thể để nhận phân tích ML &amp; giải thích chuyên sâu.
          </p>
        </Link>

        <Link
          to="/chat"
          className="group rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition-all hover:border-teal-300 hover:shadow"
        >
          <div className="flex items-center justify-between">
            <MessageSquareText className="h-5 w-5 text-teal-600" />
            <ArrowRight className="h-4 w-4 text-slate-400 transition-transform group-hover:translate-x-0.5 group-hover:text-teal-600" />
          </div>
          <p className="mt-3 text-sm font-semibold text-slate-900">Chatbot Tư vấn</p>
          <p className="mt-1 text-xs text-slate-500">
            Hỏi đáp kiến thức tiểu đường có trích dẫn nguồn CDC, WHO, NIDDK.
          </p>
        </Link>

        <Link
          to="/knowledge"
          className="group rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition-all hover:border-teal-300 hover:shadow"
        >
          <div className="flex items-center justify-between">
            <BookOpenCheck className="h-5 w-5 text-teal-600" />
            <ArrowRight className="h-4 w-4 text-slate-400 transition-transform group-hover:translate-x-0.5 group-hover:text-teal-600" />
          </div>
          <p className="mt-3 text-sm font-semibold text-slate-900">Tri thức &amp; Đồ thị Y khoa</p>
          <p className="mt-1 text-xs text-slate-500">
            Khám phá tài liệu chuẩn hóa và mạng lưới quan hệ Knowledge Graph.
          </p>
        </Link>

        <Link
          to="/history"
          className="group rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition-all hover:border-teal-300 hover:shadow"
        >
          <div className="flex items-center justify-between">
            <History className="h-5 w-5 text-teal-600" />
            <ArrowRight className="h-4 w-4 text-slate-400 transition-transform group-hover:translate-x-0.5 group-hover:text-teal-600" />
          </div>
          <p className="mt-3 text-sm font-semibold text-slate-900">Lịch sử Đánh giá</p>
          <p className="mt-1 text-xs text-slate-500">
            Xem lại chi tiết điểm số, biểu đồ yếu tố và nguồn tham khảo đã lưu.
          </p>
        </Link>
      </div>
    </div>
  );
}
