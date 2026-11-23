import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  ClipboardList,
  Info,
  Loader2,
  MessageSquareText,
  Network,
  Sparkles,
  Stethoscope,
} from 'lucide-react';
import { ApiError, apiClient } from '../api/client';
import { AgentTracePanel } from '../components/AgentTracePanel';
import { CitationCard } from '../components/CitationCard';
import { FactorChart } from '../components/FactorChart';
import { RiskBadge } from '../components/RiskBadge';
import type { AssessmentOut } from '../types/api';

interface FormState {
  age: string;
  gender: 1 | 2;
  height_cm: string;
  weight_kg: string;
  waist_cm: string;
  hip_cm: string;
  previously_diagnosed_diabetes: boolean;
  is_pregnant: boolean;
}

const INITIAL_FORM: FormState = {
  age: '38',
  gender: 2,
  height_cm: '160',
  weight_kg: '58',
  waist_cm: '78',
  hip_cm: '94',
  previously_diagnosed_diabetes: false,
  is_pregnant: false,
};

function getBmiCategory(bmi: number): { label: string; badgeClass: string } {
  if (bmi < 18.5) {
    return { label: 'Thiếu cân (BMI < 18.5)', badgeClass: 'bg-sky-50 text-sky-800 border-sky-200' };
  }
  if (bmi < 23.0) {
    return {
      label: 'Bình thường theo ngưỡng châu Á (18.5 – 22.9)',
      badgeClass: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    };
  }
  if (bmi < 25.0) {
    return {
      label: 'Thừa cân theo ngưỡng châu Á (23.0 – 24.9)',
      badgeClass: 'bg-amber-50 text-amber-800 border-amber-200',
    };
  }
  if (bmi < 30.0) {
    return {
      label: 'Thừa cân WHO / Béo phì độ I châu Á (25.0 – 29.9)',
      badgeClass: 'bg-orange-50 text-orange-800 border-orange-200',
    };
  }
  return {
    label: 'Béo phì (BMI ≥ 30.0)',
    badgeClass: 'bg-rose-50 text-rose-800 border-rose-200',
  };
}

export function AssessmentPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AssessmentOut | null>(null);

  const liveBmi = useMemo(() => {
    const h = Number(form.height_cm);
    const w = Number(form.weight_kg);
    if (!Number.isFinite(h) || !Number.isFinite(w) || h <= 0 || w <= 0) {
      return null;
    }
    const bmi = w / (h / 100) ** 2;
    return Number.isFinite(bmi) ? Number(bmi.toFixed(1)) : null;
  }, [form.height_cm, form.weight_kg]);

  const liveWhtr = useMemo(() => {
    const h = Number(form.height_cm);
    const waist = Number(form.waist_cm);
    if (!Number.isFinite(h) || !Number.isFinite(waist) || h <= 0 || waist <= 0) {
      return null;
    }
    const ratio = waist / h;
    return Number.isFinite(ratio) ? Number(ratio.toFixed(2)) : null;
  }, [form.height_cm, form.waist_cm]);

  const bmiCategory = liveBmi !== null ? getBmiCategory(liveBmi) : null;

  const applyPreset = (preset: 'low' | 'high' | 'out_of_scope') => {
    setError(null);
    if (preset === 'low') {
      setForm({
        age: '28',
        gender: 2,
        height_cm: '162',
        weight_kg: '54',
        waist_cm: '72',
        hip_cm: '92',
        previously_diagnosed_diabetes: false,
        is_pregnant: false,
      });
    } else if (preset === 'high') {
      setForm({
        age: '58',
        gender: 1,
        height_cm: '168',
        weight_kg: '89',
        waist_cm: '104',
        hip_cm: '100',
        previously_diagnosed_diabetes: false,
        is_pregnant: false,
      });
    } else {
      setForm({
        age: '45',
        gender: 1,
        height_cm: '170',
        weight_kg: '74',
        waist_cm: '90',
        hip_cm: '98',
        previously_diagnosed_diabetes: true,
        is_pregnant: false,
      });
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const hipParsed = form.hip_cm.trim() ? Number(form.hip_cm) : null;
      const payload = {
        age: Number(form.age),
        gender: form.gender,
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        waist_cm: Number(form.waist_cm),
        hip_cm: hipParsed !== null && Number.isFinite(hipParsed) ? hipParsed : null,
        previously_diagnosed_diabetes: form.previously_diagnosed_diabetes,
        is_pregnant: form.gender === 2 ? form.is_pregnant : null,
      };
      const res = await apiClient.createAssessment(payload);
      setResult(res);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError('Không thể gửi yêu cầu đánh giá. Vui lòng kiểm tra kết nối backend.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Đánh giá Nguy cơ Tiểu đường (5-Agent)
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Nhập các chỉ số nhân trắc học để chạy chuỗi kiểm tra phạm vi NHANES, dự báo ML giải thích được và tư vấn dẫn nguồn y khoa.
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-12">
        {/* LEFT COLUMN: Screening Form & Presets */}
        <div className="space-y-5 lg:col-span-5">
          {/* Quick-fill Presets */}
          <div className="rounded-2xl border border-teal-100 bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-teal-600" />
              <h2 className="text-sm font-semibold text-slate-900">Hồ sơ mẫu điền nhanh</h2>
            </div>
            <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
              <button
                type="button"
                onClick={() => applyPreset('low')}
                className="rounded-xl border border-emerald-200 bg-emerald-50/70 px-3 py-2 text-left text-xs font-semibold text-emerald-800 transition-colors hover:bg-emerald-100"
              >
                Hồ sơ nguy cơ thấp
              </button>
              <button
                type="button"
                onClick={() => applyPreset('high')}
                className="rounded-xl border border-rose-200 bg-rose-50/70 px-3 py-2 text-left text-xs font-semibold text-rose-800 transition-colors hover:bg-rose-100"
              >
                Hồ sơ nguy cơ cao
              </button>
              <button
                type="button"
                onClick={() => applyPreset('out_of_scope')}
                className="rounded-xl border border-amber-200 bg-amber-50/70 px-3 py-2 text-left text-xs font-semibold text-amber-800 transition-colors hover:bg-amber-100"
              >
                Ngoài phạm vi sàng lọc
              </button>
            </div>
          </div>

          {/* Input Form */}
          <form
            onSubmit={handleSubmit}
            className="space-y-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
          >
            <div>
              <h2 className="text-base font-bold text-slate-900">1. Phạm vi sàng lọc NHANES</h2>
              <p className="mt-0.5 text-xs text-slate-500">
                Áp dụng cho người trưởng thành 20–80 tuổi chưa từng được chẩn đoán tiểu đường và không mang thai.
              </p>

              <div className="mt-3 space-y-2.5">
                <label className="flex cursor-pointer items-start gap-2.5 rounded-xl border border-slate-200 bg-slate-50/70 p-3 text-xs text-slate-700 hover:bg-slate-100/70">
                  <input
                    type="checkbox"
                    checked={form.previously_diagnosed_diabetes}
                    onChange={(e) =>
                      setForm((prev) => ({
                        ...prev,
                        previously_diagnosed_diabetes: e.target.checked,
                      }))
                    }
                    className="mt-0.5 h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                  />
                  <span>
                    <strong className="font-semibold text-slate-900">
                      Đã từng được bác sĩ chẩn đoán tiểu đường
                    </strong>
                    <span className="mt-0.5 block text-[11px] text-slate-500">
                      Nếu chọn mục này, hệ thống sẽ dừng dự báo ML và hướng dẫn theo dõi chuyên khoa.
                    </span>
                  </span>
                </label>

                {form.gender === 2 && (
                  <label className="flex cursor-pointer items-start gap-2.5 rounded-xl border border-slate-200 bg-slate-50/70 p-3 text-xs text-slate-700 hover:bg-slate-100/70">
                    <input
                      type="checkbox"
                      checked={form.is_pregnant}
                      onChange={(e) =>
                        setForm((prev) => ({ ...prev, is_pregnant: e.target.checked }))
                      }
                      className="mt-0.5 h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                    />
                    <span>
                      <strong className="font-semibold text-slate-900">Hiện đang mang thai</strong>
                      <span className="mt-0.5 block text-[11px] text-slate-500">
                        Phụ nữ mang thai cần quy trình tầm soát tiểu đường thai kỳ chuyên biệt.
                      </span>
                    </span>
                  </label>
                )}
              </div>
            </div>

            <div className="border-t border-slate-100 pt-4">
              <h2 className="text-base font-bold text-slate-900">2. Chỉ số nhân trắc học</h2>

              <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <label htmlFor="age" className="mb-1 block text-xs font-semibold text-slate-700">
                    Tuổi (năm) *
                  </label>
                  <input
                    id="age"
                    type="number"
                    min={1}
                    max={120}
                    step={1}
                    required
                    value={form.age}
                    onChange={(e) => setForm((prev) => ({ ...prev, age: e.target.value }))}
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                  />
                  <p className="mt-1 text-[11px] text-slate-400">Ngưỡng chuẩn: 20 – 80 tuổi</p>
                </div>

                <div>
                  <label className="mb-1 block text-xs font-semibold text-slate-700">
                    Giới tính sinh học *
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() =>
                        setForm((prev) => ({ ...prev, gender: 1, is_pregnant: false }))
                      }
                      className={`rounded-xl border px-3 py-2 text-sm font-medium transition-colors ${
                        form.gender === 1
                          ? 'border-teal-600 bg-teal-50 text-teal-800'
                          : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      Nam
                    </button>
                    <button
                      type="button"
                      onClick={() => setForm((prev) => ({ ...prev, gender: 2 }))}
                      className={`rounded-xl border px-3 py-2 text-sm font-medium transition-colors ${
                        form.gender === 2
                          ? 'border-teal-600 bg-teal-50 text-teal-800'
                          : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      Nữ
                    </button>
                  </div>
                </div>

                <div>
                  <label htmlFor="height_cm" className="mb-1 block text-xs font-semibold text-slate-700">
                    Chiều cao (cm) *
                  </label>
                  <input
                    id="height_cm"
                    type="number"
                    min={100}
                    max={250}
                    step="0.1"
                    required
                    value={form.height_cm}
                    onChange={(e) => setForm((prev) => ({ ...prev, height_cm: e.target.value }))}
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                  />
                  <p className="mt-1 text-[11px] text-slate-400">Hợp lệ: 120 – 230 cm</p>
                </div>

                <div>
                  <label htmlFor="weight_kg" className="mb-1 block text-xs font-semibold text-slate-700">
                    Cân nặng (kg) *
                  </label>
                  <input
                    id="weight_kg"
                    type="number"
                    min={20}
                    max={300}
                    step="0.1"
                    required
                    value={form.weight_kg}
                    onChange={(e) => setForm((prev) => ({ ...prev, weight_kg: e.target.value }))}
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                  />
                  <p className="mt-1 text-[11px] text-slate-400">Hợp lệ: 30 – 250 kg</p>
                </div>

                <div>
                  <label htmlFor="waist_cm" className="mb-1 block text-xs font-semibold text-slate-700">
                    Vòng eo (cm) *
                  </label>
                  <input
                    id="waist_cm"
                    type="number"
                    min={40}
                    max={200}
                    step="0.1"
                    required
                    value={form.waist_cm}
                    onChange={(e) => setForm((prev) => ({ ...prev, waist_cm: e.target.value }))}
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                  />
                  <p className="mt-1 text-[11px] text-slate-400">Đo ngang rốn (50 – 180 cm)</p>
                </div>

                <div>
                  <label htmlFor="hip_cm" className="mb-1 block text-xs font-semibold text-slate-700">
                    Vòng hông (cm) <span className="font-normal text-slate-400">(tùy chọn)</span>
                  </label>
                  <input
                    id="hip_cm"
                    type="number"
                    min={50}
                    max={200}
                    step="0.1"
                    value={form.hip_cm}
                    onChange={(e) => setForm((prev) => ({ ...prev, hip_cm: e.target.value }))}
                    placeholder="Bỏ trống nếu không đo"
                    className="w-full rounded-xl border border-slate-300 px-3 py-2 text-sm focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                  />
                  <p className="mt-1 text-[11px] text-slate-400">Hợp lệ: 60 – 180 cm</p>
                </div>
              </div>

              {/* Realtime Calculated BMI & WHtR Preview */}
              {liveBmi !== null && bmiCategory && (
                <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3.5">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="text-xs text-slate-600">
                      BMI ước tính:{' '}
                      <span className="text-sm font-bold text-slate-900">{liveBmi} kg/m²</span>
                      {liveWhtr !== null && (
                        <span className="ml-3 text-slate-500">
                          • WHtR: <strong className="text-slate-800">{liveWhtr}</strong>
                        </span>
                      )}
                    </div>
                    <span
                      className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${bmiCategory.badgeClass}`}
                    >
                      {bmiCategory.label}
                    </span>
                  </div>
                </div>
              )}
            </div>

            {error && (
              <div
                role="alert"
                className="flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-xs text-rose-800"
              >
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-teal-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Đang chạy luồng 5-Agent...</span>
                </>
              ) : (
                <>
                  <Stethoscope className="h-4 w-4" />
                  <span>Phân tích &amp; Đánh giá nguy cơ</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* RIGHT COLUMN: Trace, Risk Card, FactorChart, Explanation & Citations */}
        <div className="space-y-5 lg:col-span-7">
          {!result && !submitting && (
            <div className="flex min-h-[420px] flex-col items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center">
              <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
                <Bot className="h-6 w-6" />
              </div>
              <h3 className="text-base font-bold text-slate-900">
                Sẵn sàng thực thi quy trình 5-Agent
              </h3>
              <p className="mt-1.5 max-w-md text-xs leading-relaxed text-slate-500">
                Điền thông tin bên trái hoặc chọn một hồ sơ mẫu, sau đó nhấn{' '}
                <strong>Phân tích &amp; Đánh giá nguy cơ</strong> để xem chi tiết từng Agent, biểu đồ đóng góp đặc trưng và trích dẫn y khoa.
              </p>
            </div>
          )}

          {submitting && (
            <div className="flex min-h-[300px] flex-col items-center justify-center rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
              <Loader2 className="mb-3 h-8 w-8 animate-spin text-teal-600" />
              <p className="text-sm font-semibold text-slate-900">
                Hệ thống Multi-Agent đang xử lý...
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Orchestrator → Data Analysis → Prediction ML → Knowledge RAG+KG → Consultation AI
              </p>
            </div>
          )}

          {result && !submitting && (
            <>
              {/* 1. 5-Agent Execution Trace */}
              <AgentTracePanel
                steps={result.agent_steps}
                totalLatencyMs={result.total_latency_ms}
              />

              {/* 2. Risk Result Card (completed vs out_of_scope vs needs_input) */}
              {result.status === 'completed' && result.prediction ? (
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                        Kết quả sàng lọc mô hình NHANES
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-3">
                        <span className="text-3xl font-bold tracking-tight text-slate-900">
                          {(result.prediction.model_score * 100).toFixed(1)}%
                        </span>
                        <RiskBadge band={result.prediction.risk_band} size="lg" />
                      </div>
                    </div>

                    <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-right text-xs">
                      <p className="font-semibold text-slate-700">
                        {result.prediction.model_name} (v{result.prediction.model_version})
                      </p>
                      <p className="mt-0.5 font-mono text-[11px] text-slate-500">
                        SHA256: {result.prediction.model_sha256.slice(0, 12)}...
                      </p>
                    </div>
                  </div>

                  {/* Thresholds & Derived Metrics */}
                  <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                    <div className="rounded-xl bg-slate-50 p-3">
                      <p className="text-[11px] text-slate-500">Ngưỡng phân tầng</p>
                      <p className="mt-0.5 font-mono text-xs font-semibold text-slate-900">
                        &lt; {result.prediction.threshold_low} | ≥ {result.prediction.threshold_high}
                      </p>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-3">
                      <p className="text-[11px] text-slate-500">BMI</p>
                      <p className="mt-0.5 text-sm font-bold text-slate-900">
                        {result.derived_features?.bmi ?? '—'}
                      </p>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-3">
                      <p className="text-[11px] text-slate-500">WHtR (Eo/Cao)</p>
                      <p className="mt-0.5 text-sm font-bold text-slate-900">
                        {result.derived_features?.whtr ?? '—'}
                      </p>
                    </div>
                    <div className="rounded-xl bg-slate-50 p-3">
                      <p className="text-[11px] text-slate-500">WHR (Eo/Hông)</p>
                      <p className="mt-0.5 text-sm font-bold text-slate-900">
                        {result.derived_features?.whr ?? 'Không nhập'}
                      </p>
                    </div>
                  </div>

                  {result.prediction.warning && (
                    <div className="mt-4 flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50/80 px-3.5 py-2.5 text-xs leading-relaxed text-amber-950">
                      <Info className="mt-0.5 h-4 w-4 shrink-0 text-amber-700" />
                      <span>{result.prediction.warning}</span>
                    </div>
                  )}
                </div>
              ) : result.status === 'out_of_scope' ? (
                <div className="rounded-2xl border border-amber-300 bg-amber-50 p-6 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2.5">
                      <AlertTriangle className="h-6 w-6 text-amber-700" />
                      <h3 className="text-base font-bold text-amber-950">
                        Hồ sơ nằm ngoài phạm vi sàng lọc NHANES
                      </h3>
                    </div>
                    <RiskBadge band="out_of_scope" />
                  </div>
                  <p className="mt-3 text-sm leading-relaxed text-amber-900">
                    {result.summary_text}
                  </p>
                  <p className="mt-2 text-xs text-amber-800">
                    Hệ thống đã tự động bỏ qua bước chấm điểm ML để tránh đưa ra con số sai lệch ngoài nhóm dân số khảo sát NHANES.
                  </p>
                </div>
              ) : (
                <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 shadow-sm">
                  <div className="flex items-center gap-2.5">
                    <AlertTriangle className="h-5 w-5 text-rose-700" />
                    <h3 className="text-base font-bold text-rose-950">
                      Cần kiểm tra lại thông tin đầu vào
                    </h3>
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-rose-900">{result.summary_text}</p>
                </div>
              )}

              {/* 3. Factor Contributions Chart */}
              {result.status === 'completed' &&
                result.prediction?.feature_contributions &&
                result.prediction.feature_contributions.length > 0 && (
                  <FactorChart contributions={result.prediction.feature_contributions} />
                )}

              {/* 4. Grounded Explanation, Recommendations, KG & Citations */}
              <div className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <ClipboardList className="h-5 w-5 text-teal-600" />
                    <h3 className="text-base font-bold text-slate-900">
                      Giải thích &amp; Khuyến nghị tham khảo
                    </h3>
                  </div>
                  {result.status === 'completed' && (
                    <span
                      className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium ${
                        result.llm_used
                          ? 'bg-teal-50 text-teal-700'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {result.llm_used
                        ? 'Consultation AI (Grounded)'
                        : 'Chế độ tổng hợp chuẩn hóa'}
                    </span>
                  )}
                </div>

                {result.status === 'completed' && (
                  <div className="whitespace-pre-line rounded-xl bg-slate-50 p-4 text-sm leading-relaxed text-slate-800">
                    {result.summary_text}
                  </div>
                )}

                {result.recommendations.length > 0 && (
                  <div>
                    <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Gợi ý hành động tiếp theo
                    </h4>
                    <ul className="space-y-2">
                      {result.recommendations.map((rec, idx) => (
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

                {result.kg_relations.length > 0 && (
                  <div className="border-t border-slate-100 pt-4">
                    <div className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                      <Network className="h-3.5 w-3.5 text-indigo-600" />
                      <span>Quan hệ tri thức y khoa (Knowledge Graph)</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {result.kg_relations.slice(0, 6).map((rel, idx) => (
                        <div
                          key={`${rel.source_node}-${rel.target_node}-${idx}`}
                          className="rounded-lg border border-indigo-100 bg-indigo-50/70 px-2.5 py-1.5 text-[11px] text-indigo-950"
                        >
                          <span className="font-semibold">{rel.source_node}</span>{' '}
                          <span className="text-indigo-600">→ [{rel.relation}] →</span>{' '}
                          <span className="font-semibold">{rel.target_node}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {result.citations.length > 0 && (
                  <div className="border-t border-slate-100 pt-4">
                    <h4 className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Nguồn tài liệu y khoa trích dẫn ({result.citations.length})
                    </h4>
                    <div className="space-y-2.5">
                      {result.citations.map((citation) => (
                        <CitationCard key={citation.chunk_id} citation={citation} />
                      ))}
                    </div>
                  </div>
                )}

                {result.limitations.length > 0 && (
                  <div className="border-t border-slate-100 pt-3">
                    <p className="text-[11px] font-semibold text-slate-500">Giới hạn mô hình:</p>
                    <ul className="mt-1 list-disc space-y-0.5 pl-4 text-[11px] text-slate-500">
                      {result.limitations.map((lim, i) => (
                        <li key={i}>{lim}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="border-t border-slate-100 pt-4">
                  <button
                    type="button"
                    onClick={() =>
                      navigate(`/chat?assessmentId=${encodeURIComponent(result.id)}`)
                    }
                    className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-slate-800 sm:w-auto"
                  >
                    <MessageSquareText className="h-4 w-4 text-teal-400" />
                    <span>Hỏi tiếp Chatbot về kết quả này</span>
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
