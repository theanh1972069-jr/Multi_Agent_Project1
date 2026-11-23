import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  Clock,
  Cpu,
  Database,
  FileSearch,
  MessageSquareHeart,
  MinusCircle,
  XCircle,
} from 'lucide-react';
import type { AgentStep } from '../types/api';

interface AgentTracePanelProps {
  steps: AgentStep[];
  totalLatencyMs?: number;
  title?: string;
}

const CANONICAL_AGENTS = [
  {
    key: 'orchestrator',
    title: 'Orchestrator Agent',
    subtitle: 'Điều phối & Kiểm soát an toàn',
    icon: Bot,
  },
  {
    key: 'data_analysis',
    title: 'Data Analysis Agent',
    subtitle: 'Kiểm tra phạm vi NHANES & Chỉ số',
    icon: FileSearch,
  },
  {
    key: 'prediction',
    title: 'Prediction Agent',
    subtitle: 'Mô hình ML NHANES (SHA256)',
    icon: Cpu,
  },
  {
    key: 'knowledge',
    title: 'Knowledge Agent',
    subtitle: 'Truy xuất ChromaDB RAG + KG',
    icon: Database,
  },
  {
    key: 'consultation',
    title: 'Consultation Agent',
    subtitle: 'Tổng hợp giải thích Grounded AI',
    icon: MessageSquareHeart,
  },
] as const;

function getStatusPresentation(status?: string) {
  switch (status) {
    case 'completed':
      return {
        label: 'Hoàn tất',
        badgeClass: 'border-emerald-200 bg-emerald-50 text-emerald-700',
        nodeClass: 'border-emerald-500 bg-emerald-50 text-emerald-700',
        Icon: CheckCircle2,
      };
    case 'out_of_scope':
    case 'needs_input':
      return {
        label: status === 'out_of_scope' ? 'Ngoài phạm vi' : 'Cần bổ sung',
        badgeClass: 'border-amber-200 bg-amber-50 text-amber-800',
        nodeClass: 'border-amber-500 bg-amber-50 text-amber-700',
        Icon: AlertTriangle,
      };
    case 'failed':
      return {
        label: 'Lỗi',
        badgeClass: 'border-rose-200 bg-rose-50 text-rose-700',
        nodeClass: 'border-rose-500 bg-rose-50 text-rose-700',
        Icon: XCircle,
      };
    default:
      return {
        label: 'Đã bỏ qua',
        badgeClass: 'border-slate-200 bg-slate-100 text-slate-500',
        nodeClass: 'border-slate-200 bg-slate-50 text-slate-400',
        Icon: MinusCircle,
      };
  }
}

export function AgentTracePanel({
  steps,
  totalLatencyMs,
  title = 'Luồng xử lý 5-Agent (Execution Trace)',
}: AgentTracePanelProps) {
  const stepMap = new Map<string, AgentStep>();
  for (const step of steps) {
    stepMap.set(step.agent_name, step);
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
          <p className="text-xs text-slate-500">
            Orchestrator → Data Analysis → Prediction → Knowledge → Consultation
          </p>
        </div>
        {typeof totalLatencyMs === 'number' && totalLatencyMs >= 0 && (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700">
            <Clock className="h-3.5 w-3.5 text-teal-600" />
            Tổng: {totalLatencyMs} ms
          </span>
        )}
      </div>

      {/* Horizontal quick pipeline overview */}
      <div className="mb-4 grid grid-cols-5 gap-1.5">
        {CANONICAL_AGENTS.map((agent, idx) => {
          const step = stepMap.get(agent.key);
          const statusInfo = getStatusPresentation(step?.status);
          const AgentIcon = agent.icon;
          return (
            <div
              key={agent.key}
              className={`flex flex-col items-center rounded-xl border p-2 text-center transition-colors ${
                step ? 'border-slate-200 bg-slate-50/70' : 'border-dashed border-slate-200 bg-slate-50/30 opacity-65'
              }`}
            >
              <div
                className={`mb-1 flex h-7 w-7 items-center justify-center rounded-full border ${statusInfo.nodeClass}`}
              >
                <AgentIcon className="h-3.5 w-3.5" />
              </div>
              <span className="line-clamp-1 text-[11px] font-semibold text-slate-800">
                {idx + 1}. {agent.key === 'data_analysis' ? 'Data' : agent.title.split(' ')[0]}
              </span>
              <span className="text-[10px] text-slate-500">
                {step ? `${step.latency_ms} ms` : '—'}
              </span>
            </div>
          );
        })}
      </div>

      {/* Detailed step list */}
      <div className="space-y-2.5">
        {CANONICAL_AGENTS.map((agent) => {
          const step = stepMap.get(agent.key);
          const statusInfo = getStatusPresentation(step?.status);
          const StatusIcon = statusInfo.Icon;

          return (
            <div
              key={agent.key}
              className={`rounded-xl border px-3.5 py-2.5 text-xs ${
                step ? 'border-slate-200 bg-white' : 'border-dashed border-slate-200 bg-slate-50/50 opacity-70'
              }`}
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-900">{agent.title}</span>
                  <span className="text-slate-400">•</span>
                  <span className="text-slate-500">{agent.subtitle}</span>
                </div>
                <div className="flex items-center gap-2">
                  {step && (
                    <span className="font-mono text-[11px] text-slate-500">{step.latency_ms} ms</span>
                  )}
                  <span
                    className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${statusInfo.badgeClass}`}
                  >
                    <StatusIcon className="h-3 w-3" />
                    {statusInfo.label}
                  </span>
                </div>
              </div>
              {step?.summary ? (
                <p className="mt-1.5 leading-relaxed text-slate-600">{step.summary}</p>
              ) : (
                <p className="mt-1 italic text-slate-400">
                  Không thực thi do luồng đã dừng hoặc điều hướng ở bước trước.
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
