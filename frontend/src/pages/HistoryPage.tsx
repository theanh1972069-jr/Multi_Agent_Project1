import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  CheckCircle2,
  ClipboardList,
  Eye,
  Filter,
  Loader2,
  MessageSquareText,
  Network,
  Stethoscope,
  X,
} from 'lucide-react';
import { ApiError, apiClient } from '../api/client';
import { AgentTracePanel } from '../components/AgentTracePanel';
import { CitationCard } from '../components/CitationCard';
import { FactorChart } from '../components/FactorChart';
import { RiskBadge } from '../components/RiskBadge';
import type { AssessmentOut } from '../types/api';
import { formatDateTimeVi, formatGenderVi, getKgRelationLabels } from '../utils/format';

type RiskFilter = 'all' | 'elevated' | 'moderate' | 'low' | 'out_of_scope';

function matchesFilter(item: AssessmentOut, filter: RiskFilter): boolean {
  if (filter === 'all') return true;
  if (filter === 'out_of_scope') {
    return item.status !== 'completed' || !item.prediction;
  }
  return item.status === 'completed' && item.prediction?.risk_band === filter;
}

export function HistoryPage() {
  const navigate = useNavigate();
  const [assessments, setAssessments] = useState<AssessmentOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<RiskFilter>('all');
  const [selected, setSelected] = useState<AssessmentOut | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const list = await apiClient.listAssessments();
        if (!active) return;
        setAssessments(list);
      } catch (err) {
        if (!active) return;
        setError(
          err instanceof ApiError ? err.detail : 'Không thể tải lịch sử đánh giá nguy cơ.',
        );
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, []);

  const stats = useMemo(() => {
    const completed = assessments.filter((a) => a.status === 'completed' && a.prediction);
    const outOfScope = assessments.filter((a) => a.status !== 'completed' || !a.prediction);
    const avgScore =
      completed.length > 0
        ? (completed.reduce((acc, cur) => acc + (cur.prediction?.model_score ?? 0), 0) /
            completed.length) *
          100
        : null;
    const elevatedCount = completed.filter((a) => a.prediction?.risk_band === 'elevated').length;
    return {
      total: assessments.length,
      completedCount: completed.length,
      outOfScopeCount: outOfScope.length,
      elevatedCount,
      avgScore,
    };
  }, [assessments]);

  const filtered = useMemo(
    () => assessments.filter((item) => matchesFilter(item, filter)),
    [assessments, filter],
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Lịch sử Đánh giá Nguy cơ
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Theo dõi các lần sàng lọc đã thực hiện, xem lại biểu đồ yếu tố ML và tiếp tục hỏi Chatbot.
          </p>
        </div>
        <Link
          to="/assessment"
          className="inline-flex items-center gap-2 self-start rounded-xl bg-teal-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-teal-700"
        >
          <Stethoscope className="h-4 w-4" />
          <span>Đánh giá mới</span>
        </Link>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">Tổng số lượt sàng lọc</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">{stats.total}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">Hồ sơ hợp lệ (NHANES)</p>
          <p className="mt-1 text-2xl font-bold text-teal-700">{stats.completedCount}</p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">Điểm sàng lọc trung bình</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">
            {stats.avgScore !== null ? `${stats.avgScore.toFixed(1)}%` : '—'}
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-xs font-medium text-slate-500">Mức nguy cơ cao / Ngoài phạm vi</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">
            <span className="text-rose-600">{stats.elevatedCount}</span>
            <span className="mx-1.5 text-sm font-normal text-slate-400">/</span>
            <span className="text-amber-600">{stats.outOfScopeCount}</span>
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <span className="mr-1 inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500">
          <Filter className="h-3.5 w-3.5" />
          Lọc theo mức độ:
        </span>
        {(
          [
            { key: 'all', label: `Tất cả (${assessments.length})` },
            { key: 'elevated', label: 'Nguy cơ cao' },
            { key: 'moderate', label: 'Nguy cơ trung bình' },
            { key: 'low', label: 'Nguy cơ thấp' },
            { key: 'out_of_scope', label: 'Ngoài phạm vi' },
          ] as Array<{ key: RiskFilter; label: string }>
        ).map((item) => (
          <button
            key={item.key}
            type="button"
            onClick={() => setFilter(item.key)}
            className={`rounded-full border px-3 py-1 text-xs font-semibold transition-colors ${
              filter === item.key
                ? 'border-teal-600 bg-teal-600 text-white'
                : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
            }`}
          >
            {item.label}
          </button>
        ))}
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

      {/* Assessments Table */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <div className="flex h-48 items-center justify-center text-sm text-slate-500">
            <Loader2 className="mr-2 h-5 w-5 animate-spin text-teal-600" />
            Đang tải lịch sử đánh giá...
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex h-48 flex-col items-center justify-center p-6 text-center">
            <p className="text-sm font-semibold text-slate-800">
              Không có bản ghi đánh giá nào phù hợp
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Thực hiện một lượt đánh giá mới hoặc thay đổi bộ lọc để xem dữ liệu.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
              <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-4 py-3">Thời gian</th>
                  <th className="px-4 py-3">Phân tầng nguy cơ</th>
                  <th className="px-4 py-3">Tuổi / Giới</th>
                  <th className="px-4 py-3">BMI</th>
                  <th className="px-4 py-3">Vòng eo / WHtR</th>
                  <th className="px-4 py-3">Điểm ML</th>
                  <th className="px-4 py-3">Độ trễ</th>
                  <th className="px-4 py-3 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {filtered.map((item) => {
                  const band =
                    item.status === 'completed' && item.prediction
                      ? item.prediction.risk_band
                      : 'out_of_scope';
                  return (
                    <tr key={item.id} className="hover:bg-slate-50/70">
                      <td className="whitespace-nowrap px-4 py-3 font-medium text-slate-800">
                        {formatDateTimeVi(item.created_at)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3">
                        <RiskBadge band={band} size="sm" />
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-slate-700">
                        {String(item.raw_inputs?.age ?? '—')} tuổi •{' '}
                        {formatGenderVi(item.raw_inputs?.gender)}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 font-mono text-slate-800">
                        {item.derived_features?.bmi ?? '—'}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 font-mono text-slate-700">
                        {String(item.raw_inputs?.waist_cm ?? '—')} cm
                        {item.derived_features?.whtr ? ` (${item.derived_features.whtr})` : ''}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 font-bold text-slate-900">
                        {item.prediction
                          ? `${(item.prediction.model_score * 100).toFixed(1)}%`
                          : '—'}
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 font-mono text-slate-500">
                        {item.total_latency_ms} ms
                      </td>
                      <td className="whitespace-nowrap px-4 py-3 text-right">
                        <div className="inline-flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => setSelected(item)}
                            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100"
                          >
                            <Eye className="h-3.5 w-3.5" />
                            <span>Xem chi tiết</span>
                          </button>
                          <button
                            type="button"
                            onClick={() =>
                              navigate(`/chat?assessmentId=${encodeURIComponent(item.id)}`)
                            }
                            className="inline-flex items-center gap-1 rounded-lg border border-teal-200 bg-teal-50 px-2.5 py-1.5 text-xs font-semibold text-teal-800 hover:bg-teal-100"
                          >
                            <MessageSquareText className="h-3.5 w-3.5" />
                            <span>Hỏi Chatbot</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Assessment Detail Modal */}
      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-label="Chi tiết kết quả đánh giá nguy cơ"
        >
          <div className="flex max-h-[90vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-slate-50 shadow-2xl">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4">
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="text-base font-bold text-slate-900">
                  Chi tiết Đánh giá • {formatDateTimeVi(selected.created_at)}
                </h2>
                <RiskBadge
                  band={
                    selected.status === 'completed' && selected.prediction
                      ? selected.prediction.risk_band
                      : 'out_of_scope'
                  }
                  size="sm"
                />
              </div>
              <button
                type="button"
                onClick={() => setSelected(null)}
                aria-label="Đóng chi tiết"
                className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-900"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 space-y-5 overflow-y-auto p-6">
              {/* Metrics Summary */}
              {selected.status === 'completed' && selected.prediction && (
                <div className="grid grid-cols-2 gap-3 rounded-2xl border border-slate-200 bg-white p-4 sm:grid-cols-5">
                  <div>
                    <p className="text-[11px] text-slate-500">Điểm ML</p>
                    <p className="mt-0.5 text-lg font-bold text-slate-900">
                      {(selected.prediction.model_score * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] text-slate-500">BMI</p>
                    <p className="mt-0.5 text-sm font-bold text-slate-900">
                      {selected.derived_features?.bmi ?? '—'}
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] text-slate-500">Vòng eo</p>
                    <p className="mt-0.5 text-sm font-bold text-slate-900">
                      {String(selected.raw_inputs?.waist_cm ?? '—')} cm
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] text-slate-500">WHtR</p>
                    <p className="mt-0.5 text-sm font-bold text-slate-900">
                      {selected.derived_features?.whtr ?? '—'}
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] text-slate-500">WHR</p>
                    <p className="mt-0.5 text-sm font-bold text-slate-900">
                      {selected.derived_features?.whr ?? 'Không nhập'}
                    </p>
                  </div>
                </div>
              )}

              {/* Factor Chart */}
              {selected.status === 'completed' &&
                selected.prediction?.feature_contributions &&
                selected.prediction.feature_contributions.length > 0 && (
                  <FactorChart contributions={selected.prediction.feature_contributions} />
                )}

              {/* Explanation, Recommendations, KG, Citations, Limitations */}
              <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-center gap-2">
                  <ClipboardList className="h-4 w-4 text-teal-600" />
                  <h3 className="text-sm font-bold text-slate-900">
                    Giải thích &amp; Khuyến nghị
                  </h3>
                </div>
                <div className="whitespace-pre-line rounded-xl bg-slate-50 p-4 text-sm leading-relaxed text-slate-800">
                  {selected.summary_text}
                </div>

                {selected.recommendations.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Khuyến nghị hành động
                    </h4>
                    <ul className="space-y-1.5">
                      {selected.recommendations.map((rec, idx) => (
                        <li
                          key={idx}
                          className="flex items-start gap-2 text-xs leading-relaxed text-slate-700"
                        >
                          <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-teal-600" />
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {selected.kg_relations.length > 0 && (
                  <div className="border-t border-slate-100 pt-3">
                    <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                      <Network className="h-3.5 w-3.5 text-indigo-600" />
                      <span>Quan hệ Knowledge Graph</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {selected.kg_relations.map((rel, idx) => {
                        const { sourceLabel, relationLabel, targetLabel } =
                          getKgRelationLabels(rel);
                        return (
                          <span
                            key={`${sourceLabel}-${rel.relation}-${targetLabel}-${idx}`}
                            className="rounded-lg border border-indigo-100 bg-indigo-50/70 px-2.5 py-1 text-[11px] text-indigo-950"
                          >
                            <span className="font-semibold">{sourceLabel}</span>{' '}
                            <span className="text-indigo-600">—[{relationLabel}]→</span>{' '}
                            <span className="font-semibold">{targetLabel}</span>
                          </span>
                        );
                      })}
                    </div>
                  </div>
                )}

                {selected.citations.length > 0 && (
                  <div className="border-t border-slate-100 pt-3">
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Nguồn tài liệu trích dẫn ({selected.citations.length})
                    </h4>
                    <div className="space-y-2">
                      {selected.citations.map((cit) => (
                        <CitationCard key={cit.chunk_id} citation={cit} />
                      ))}
                    </div>
                  </div>
                )}

                {selected.limitations.length > 0 && (
                  <div className="border-t border-slate-100 pt-3">
                    <p className="text-[11px] font-semibold text-slate-500">Giới hạn mô hình:</p>
                    <ul className="mt-1 list-disc space-y-0.5 pl-4 text-[11px] text-slate-500">
                      {selected.limitations.map((lim, i) => (
                        <li key={i}>{lim}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Agent Trace */}
              <AgentTracePanel
                steps={selected.agent_steps}
                totalLatencyMs={selected.total_latency_ms}
              />
            </div>

            {/* Modal Footer */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-200 bg-white px-6 py-3.5">
              <span className="font-mono text-[11px] text-slate-400">
                Request ID: {selected.request_id}
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setSelected(null)}
                  className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Đóng
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const id = selected.id;
                    setSelected(null);
                    navigate(`/chat?assessmentId=${encodeURIComponent(id)}`);
                  }}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-teal-600 px-4 py-2 text-xs font-semibold text-white hover:bg-teal-700"
                >
                  <MessageSquareText className="h-3.5 w-3.5" />
                  <span>Hỏi Chatbot về kết quả này</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
