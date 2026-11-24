import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Bot,
  ChevronDown,
  ChevronUp,
  Cpu,
  Loader2,
  MessageSquarePlus,
  MessageSquareText,
  Network,
  Send,
  ShieldAlert,
  Sparkles,
  Stethoscope,
  User as UserIcon,
} from 'lucide-react';
import { ApiError, apiClient } from '../api/client';
import { AgentTracePanel } from '../components/AgentTracePanel';
import { CitationCard } from '../components/CitationCard';
import { MarkdownText } from '../components/MarkdownText';
import { RiskBadge } from '../components/RiskBadge';
import type { AssessmentOut, ChatMessageOut, ChatSessionOut } from '../types/api';
import { formatDateTimeVi, getKgRelationLabels } from '../utils/format';

const STARTER_QUESTIONS: string[] = [
  'Tiền tiểu đường là gì và làm sao phòng ngừa?',
  'Chỉ số vòng eo và WHtR ảnh hưởng thế nào đến nguy cơ tiểu đường?',
  'Giải thích giúp tôi kết quả sàng lọc gần nhất',
  'Triệu chứng cảnh báo đường huyết cao cần đi khám ngay?',
];

const SAFETY_FLAG_META: Record<
  string,
  { title: string; description: string; isEmergency: boolean }
> = {
  emergency: {
    title: 'Cảnh báo tình huống cấp cứu y tế',
    description:
      'Nếu bạn hoặc người thân đang có triệu chứng cấp tính nghiêm trọng, hãy gọi cấp cứu 115 hoặc đến cơ sở y tế gần nhất ngay lập tức.',
    isEmergency: true,
  },
  prescription_request: {
    title: 'Giới hạn an toàn: Không kê đơn thuốc',
    description:
      'Hệ thống không cung cấp chỉ định dùng thuốc, thay đổi liều insulin hay phác đồ điều trị. Vui lòng trao đổi trực tiếp với bác sĩ chuyên khoa.',
    isEmergency: false,
  },
  diagnosis_override: {
    title: 'Giới hạn an toàn: Không thay thế chẩn đoán lâm sàng',
    description:
      'Công cụ chỉ hỗ trợ sàng lọc và cung cấp thông tin tham khảo từ tài liệu chuẩn hóa, không thay thế xét nghiệm HbA1c/FPG hoặc kết luận của bác sĩ.',
    isEmergency: false,
  },
  prompt_injection: {
    title: 'Bộ lọc an toàn đã kích hoạt',
    description:
      'Yêu cầu chứa chỉ thị vượt phạm vi đã bị chặn để đảm bảo tuân thủ nguyên tắc an toàn y khoa.',
    isEmergency: false,
  },
};

function formatAssessmentOptionLabel(item: AssessmentOut): string {
  const dateStr = formatDateTimeVi(item.created_at);
  if (item.status === 'completed' && item.prediction) {
    const pct = (item.prediction.model_score * 100).toFixed(1);
    const bandVi =
      item.prediction.risk_band === 'elevated'
        ? 'Nguy cơ cao'
        : item.prediction.risk_band === 'moderate'
          ? 'Nguy cơ trung bình'
          : 'Nguy cơ thấp';
    return `${dateStr} • ${pct}% (${bandVi})`;
  }
  return `${dateStr} • Ngoài phạm vi / Chưa chấm điểm`;
}

export function ChatPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryAssessmentId = searchParams.get('assessmentId');

  const [sessions, setSessions] = useState<ChatSessionOut[]>([]);
  const [assessments, setAssessments] = useState<AssessmentOut[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState<string>(queryAssessmentId || '');
  const [messages, setMessages] = useState<ChatMessageOut[]>([]);

  const [loadingInit, setLoadingInit] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [creatingSession, setCreatingSession] = useState(false);
  const [sending, setSending] = useState(false);
  const [pendingUserText, setPendingUserText] = useState<string | null>(null);
  const [inputText, setInputText] = useState('');
  const [error, setError] = useState<string | null>(null);

  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});
  const [expandedTraces, setExpandedTraces] = useState<Record<string, boolean>>({});

  const handledQueryAssessmentRef = useRef<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const loadMessages = useCallback(async (sessionId: string) => {
    setLoadingMessages(true);
    setError(null);
    try {
      const list = await apiClient.listChatMessages(sessionId);
      setMessages(list);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.detail : 'Không thể tải lịch sử tin nhắn của phiên tư vấn.',
      );
    } finally {
      setLoadingMessages(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    async function init() {
      setLoadingInit(true);
      setError(null);
      try {
        const [sessionList, assessmentList] = await Promise.all([
          apiClient.listChatSessions(),
          apiClient.listAssessments(),
        ]);
        if (!active) return;

        setSessions(sessionList);
        setAssessments(assessmentList);

        if (queryAssessmentId) {
          setSelectedAssessmentId(queryAssessmentId);
          const existingLinked = sessionList.find(
            (s) => s.linked_assessment_id === queryAssessmentId,
          );
          if (existingLinked) {
            setActiveSessionId(existingLinked.id);
            handledQueryAssessmentRef.current = queryAssessmentId;
          } else if (handledQueryAssessmentRef.current !== queryAssessmentId) {
            handledQueryAssessmentRef.current = queryAssessmentId;
            try {
              const linkedAssessment = assessmentList.find((a) => a.id === queryAssessmentId);
              const title = linkedAssessment
                ? `Tư vấn kết quả (${formatDateTimeVi(linkedAssessment.created_at)})`
                : 'Tư vấn kết quả sàng lọc';
              const created = await apiClient.createChatSession({
                title,
                linked_assessment_id: queryAssessmentId,
              });
              if (!active) return;
              setSessions((prev) => [created, ...prev]);
              setActiveSessionId(created.id);
            } catch {
              if (sessionList.length > 0) {
                setActiveSessionId(sessionList[0].id);
              }
            }
          }
        } else if (sessionList.length > 0) {
          setActiveSessionId(sessionList[0].id);
          if (sessionList[0].linked_assessment_id) {
            setSelectedAssessmentId(sessionList[0].linked_assessment_id);
          }
        }
      } catch (err) {
        if (!active) return;
        setError(
          err instanceof ApiError
            ? err.detail
            : 'Không thể tải danh sách phiên tư vấn từ máy chủ.',
        );
      } finally {
        if (active) setLoadingInit(false);
      }
    }
    void init();
    return () => {
      active = false;
    };
  }, [queryAssessmentId]);

  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      return;
    }
    void loadMessages(activeSessionId);
  }, [activeSessionId, loadMessages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages.length, pendingUserText]);

  const activeSession = useMemo(
    () => sessions.find((s) => s.id === activeSessionId) ?? null,
    [sessions, activeSessionId],
  );

  const selectedAssessment = useMemo(
    () => assessments.find((a) => a.id === selectedAssessmentId) ?? null,
    [assessments, selectedAssessmentId],
  );

  const handleSelectSession = (session: ChatSessionOut) => {
    setError(null);
    setActiveSessionId(session.id);
    if (session.linked_assessment_id) {
      setSelectedAssessmentId(session.linked_assessment_id);
    } else if (!queryAssessmentId) {
      setSelectedAssessmentId('');
    }
    if (queryAssessmentId && session.linked_assessment_id !== queryAssessmentId) {
      setSearchParams({}, { replace: true });
    }
  };

  const handleCreateSession = async (customAssessmentId?: string) => {
    setCreatingSession(true);
    setError(null);
    try {
      const targetAssessmentId =
        customAssessmentId !== undefined ? customAssessmentId : selectedAssessmentId;
      const matched = assessments.find((a) => a.id === targetAssessmentId);
      const title = matched
        ? `Tư vấn kết quả (${formatDateTimeVi(matched.created_at)})`
        : 'Cuộc trò chuyện mới';
      const created = await apiClient.createChatSession({
        title,
        linked_assessment_id: targetAssessmentId || null,
      });
      setSessions((prev) => [created, ...prev]);
      setActiveSessionId(created.id);
      setMessages([]);
      return created;
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Không thể tạo phiên trò chuyện mới.');
      return null;
    } finally {
      setCreatingSession(false);
    }
  };

  const sendText = async (rawText: string) => {
    const trimmed = rawText.trim();
    if (!trimmed || sending) return;

    setError(null);
    setSending(true);
    setPendingUserText(trimmed);
    setInputText('');

    try {
      let targetSessionId = activeSessionId;
      if (!targetSessionId) {
        const created = await apiClient.createChatSession({
          title: trimmed.slice(0, 60),
          linked_assessment_id: selectedAssessmentId || null,
        });
        setSessions((prev) => [created, ...prev]);
        setActiveSessionId(created.id);
        targetSessionId = created.id;
      }

      const assistantReply = await apiClient.postChatMessage(targetSessionId, {
        content: trimmed,
        linked_assessment_id: selectedAssessmentId || null,
      });

      const refreshed = await apiClient.listChatMessages(targetSessionId);
      // Merge transient metadata from the live reply onto the matching saved assistant message
      const merged = refreshed.map((item) =>
        item.id === assistantReply.id
          ? {
              ...item,
              kg_source: assistantReply.kg_source ?? item.kg_source,
              llm_used: assistantReply.llm_used,
              llm_fallback: assistantReply.llm_fallback,
            }
          : item,
      );
      setMessages(merged);

      // Refresh session order/timestamps
      const updatedSessions = await apiClient.listChatSessions();
      setSessions(updatedSessions);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.detail
          : 'Không thể gửi tin nhắn. Vui lòng thử lại sau.',
      );
      setInputText(trimmed);
    } finally {
      setPendingUserText(null);
      setSending(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await sendText(inputText);
  };

  const toggleCitations = (id: string) => {
    setExpandedCitations((prev) => ({
      ...prev,
      [id]: !(prev[id] ?? true),
    }));
  };

  const toggleTrace = (id: string) => {
    setExpandedTraces((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Chatbot Tư vấn Tiểu đường (RAG + KG)
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Hỏi đáp kiến thức tiểu đường và giải thích kết quả sàng lọc với trích dẫn nguồn y khoa chuẩn hóa.
          </p>
        </div>
        <Link
          to="/assessment"
          className="inline-flex items-center gap-1.5 self-start rounded-xl border border-teal-200 bg-teal-50 px-3.5 py-2 text-xs font-semibold text-teal-800 hover:bg-teal-100"
        >
          <Stethoscope className="h-4 w-4" />
          <span>Mở Sàng lọc Nguy cơ 5-Agent</span>
        </Link>
      </div>

      <div className="grid gap-5 lg:grid-cols-12">
        {/* LEFT SIDEBAR: Sessions & Linked Assessment Context */}
        <aside className="flex flex-col gap-4 lg:col-span-4 xl:col-span-3">
          {/* Linked Assessment Selector */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <label
              htmlFor="linked-assessment-select"
              className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-slate-800"
            >
              <Stethoscope className="h-3.5 w-3.5 text-teal-600" />
              <span>Gắn kết quả sàng lọc (tùy chọn)</span>
            </label>
            <select
              id="linked-assessment-select"
              value={selectedAssessmentId}
              onChange={(e) => setSelectedAssessmentId(e.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
            >
              <option value="">Không gắn kết quả cụ thể</option>
              {assessments.map((item) => (
                <option key={item.id} value={item.id}>
                  {formatAssessmentOptionLabel(item)}
                </option>
              ))}
            </select>

            {selectedAssessment && (
              <div className="mt-2.5 rounded-xl border border-teal-100 bg-teal-50/60 p-2.5 text-[11px] text-slate-700">
                <div className="flex flex-wrap items-center justify-between gap-1.5">
                  <RiskBadge
                    band={
                      selectedAssessment.status === 'out_of_scope'
                        ? 'out_of_scope'
                        : selectedAssessment.prediction?.risk_band || 'out_of_scope'
                    }
                    size="sm"
                  />
                  {selectedAssessment.derived_features?.bmi && (
                    <span className="font-mono text-slate-600">
                      BMI {selectedAssessment.derived_features.bmi}
                    </span>
                  )}
                </div>
                <p className="mt-1.5 line-clamp-2 text-slate-600">
                  {selectedAssessment.summary_text}
                </p>
              </div>
            )}
          </div>

          {/* Sessions List */}
          <div className="flex flex-1 flex-col rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <button
              type="button"
              onClick={() => void handleCreateSession()}
              disabled={creatingSession}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-teal-600 px-3.5 py-2.5 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-teal-700 disabled:opacity-60"
            >
              {creatingSession ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <MessageSquarePlus className="h-4 w-4" />
              )}
              <span>Cuộc trò chuyện mới</span>
            </button>

            <div className="mt-3 flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              <span>Phiên tư vấn ({sessions.length})</span>
            </div>

            <div className="mt-2 max-h-[400px] space-y-1.5 overflow-y-auto pr-0.5">
              {loadingInit ? (
                <div className="flex items-center justify-center py-8 text-xs text-slate-500">
                  <Loader2 className="mr-2 h-4 w-4 animate-spin text-teal-600" />
                  Đang tải...
                </div>
              ) : sessions.length === 0 ? (
                <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-center text-xs text-slate-500">
                  Chưa có phiên hội thoại nào. Hãy chọn câu hỏi gợi ý hoặc bấm &ldquo;Cuộc trò chuyện mới&rdquo;.
                </p>
              ) : (
                sessions.map((session) => {
                  const isSelected = session.id === activeSessionId;
                  return (
                    <button
                      key={session.id}
                      type="button"
                      onClick={() => handleSelectSession(session)}
                      className={`w-full rounded-xl border px-3 py-2.5 text-left transition-colors ${
                        isSelected
                          ? 'border-teal-500 bg-teal-50/70 text-teal-950'
                          : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <span className="line-clamp-1 text-xs font-semibold">{session.title}</span>
                        {session.linked_assessment_id && (
                          <span className="shrink-0 rounded bg-teal-100 px-1.5 py-0.5 text-[10px] font-medium text-teal-800">
                            Có KQ
                          </span>
                        )}
                      </div>
                      <p className="mt-1 text-[10px] text-slate-400">
                        {formatDateTimeVi(session.updated_at)}
                      </p>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        </aside>

        {/* MAIN CHAT PANE */}
        <section className="flex min-h-[600px] flex-col rounded-2xl border border-slate-200 bg-white shadow-sm lg:col-span-8 xl:col-span-9">
          {/* Header bar */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 px-5 py-3.5">
            <div className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-teal-50 text-teal-700">
                <MessageSquareText className="h-4 w-4" />
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-900">
                  {activeSession ? activeSession.title : 'Phiên tư vấn mới'}
                </h2>
                <p className="text-[11px] text-slate-500">
                  {selectedAssessment
                    ? `Đang tham chiếu kết quả ngày ${formatDateTimeVi(selectedAssessment.created_at)}`
                    : 'Chế độ hỏi đáp tri thức tiểu đường tổng quát'}
                </p>
              </div>
            </div>
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-600">
              Grounded RAG + KG + Safety Guard
            </span>
          </div>

          {/* Starter Question Chips */}
          <div className="border-b border-slate-100 bg-slate-50/70 px-5 py-3">
            <div className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold text-slate-600">
              <Sparkles className="h-3.5 w-3.5 text-teal-600" />
              <span>Câu hỏi gợi ý nhanh</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {STARTER_QUESTIONS.map((q) => (
                <button
                  key={q}
                  type="button"
                  disabled={sending}
                  onClick={() => void sendText(q)}
                  className="rounded-full border border-teal-200 bg-white px-3 py-1.5 text-xs font-medium text-teal-800 transition-colors hover:border-teal-400 hover:bg-teal-50 disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {/* Messages Container */}
          <div className="flex-1 space-y-4 overflow-y-auto px-5 py-5">
            {loadingMessages ? (
              <div className="flex h-48 items-center justify-center text-sm text-slate-500">
                <Loader2 className="mr-2 h-5 w-5 animate-spin text-teal-600" />
                Đang tải nội dung hội thoại...
              </div>
            ) : messages.length === 0 && !pendingUserText ? (
              <div className="flex h-64 flex-col items-center justify-center rounded-2xl border border-dashed border-slate-200 bg-slate-50/60 p-6 text-center">
                <Bot className="mb-3 h-10 w-10 text-teal-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Bắt đầu trao đổi với Trợ lý Y khoa DiaGuard AI
                </h3>
                <p className="mt-1 max-w-md text-xs leading-relaxed text-slate-500">
                  Mọi câu trả lời đều đi qua lớp kiểm tra an toàn y khoa, truy xuất tài liệu CDC / NIDDK / WHO / Long Châu và đối chiếu Knowledge Graph.
                </p>
              </div>
            ) : (
              messages.map((msg) => {
                if (msg.role === 'user') {
                  return (
                    <div key={msg.id} className="flex justify-end">
                      <div className="flex max-w-[82%] items-start gap-2.5">
                        <div className="rounded-2xl rounded-tr-sm bg-teal-600 px-4 py-3 text-sm leading-relaxed text-white shadow-sm">
                          <p className="whitespace-pre-line">{msg.content}</p>
                          <p className="mt-1.5 text-right text-[10px] text-teal-100">
                            {formatDateTimeVi(msg.created_at)}
                          </p>
                        </div>
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-teal-100 text-teal-800">
                          <UserIcon className="h-4 w-4" />
                        </div>
                      </div>
                    </div>
                  );
                }

                const safetyInfo = msg.safety_flag
                  ? SAFETY_FLAG_META[msg.safety_flag] ?? {
                      title: `Cảnh báo an toàn (${msg.safety_flag})`,
                      description:
                        'Hệ thống đã áp dụng cơ chế kiểm soát an toàn y khoa cho phản hồi này.',
                      isEmergency: false,
                    }
                  : null;
                const citationsOpen = expandedCitations[msg.id] ?? true;
                const traceOpen = expandedTraces[msg.id] ?? false;
                const answerText = msg.answer || msg.content;

                return (
                  <div key={msg.id} className="flex justify-start">
                    <div className="flex w-full max-w-[92%] items-start gap-2.5">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-900 text-teal-400">
                        <Bot className="h-4 w-4" />
                      </div>

                      <div className="min-w-0 flex-1 space-y-3 rounded-2xl rounded-tl-sm border border-slate-200 bg-slate-50/60 p-4 shadow-sm">
                        {/* Top metadata badges */}
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex flex-wrap items-center gap-1.5">
                            <span className="text-xs font-bold text-slate-900">DiaGuard AI</span>
                            {msg.llm_used && (
                              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-700">
                                <Cpu className="h-3 w-3" />
                                Grounded LLM
                              </span>
                            )}
                            {msg.llm_fallback && !msg.llm_used && (
                              <span className="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-semibold text-amber-800">
                                Template dự phòng ngoại tuyến
                              </span>
                            )}
                            {msg.kg_source && (
                              <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-[10px] font-semibold text-indigo-700">
                                KG: {msg.kg_source === 'neo4j' ? 'Neo4j' : 'Local Mirror'}
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] text-slate-400">
                            {formatDateTimeVi(msg.created_at)}
                            {msg.total_latency_ms > 0 ? ` • ${msg.total_latency_ms} ms` : ''}
                          </span>
                        </div>

                        {/* Safety Alert Banner */}
                        {safetyInfo && (
                          <div
                            role="alert"
                            className={`flex items-start gap-2.5 rounded-xl border p-3 text-xs ${
                              safetyInfo.isEmergency
                                ? 'border-rose-300 bg-rose-50 text-rose-900'
                                : 'border-amber-300 bg-amber-50 text-amber-900'
                            }`}
                          >
                            {safetyInfo.isEmergency ? (
                              <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-rose-600" />
                            ) : (
                              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                            )}
                            <div>
                              <p className="font-bold">{safetyInfo.title}</p>
                              <p className="mt-0.5 leading-relaxed">{safetyInfo.description}</p>
                            </div>
                          </div>
                        )}

                        {/* Grounded Answer Body */}
                        <div className="rounded-xl bg-white p-3.5 text-sm leading-relaxed text-slate-800">
                          <MarkdownText content={answerText} />
                        </div>

                        {/* Redirect CTA to Assessment Page */}
                        {msg.redirect_to_assessment && (
                          <div>
                            <Link
                              to="/assessment"
                              className="inline-flex items-center gap-2 rounded-xl bg-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition-colors hover:bg-teal-700"
                            >
                              <Stethoscope className="h-4 w-4" />
                              <span>Chuyển đến màn hình Sàng lọc Nguy cơ 5-Agent</span>
                              <ArrowRight className="h-3.5 w-3.5" />
                            </Link>
                          </div>
                        )}

                        {/* Knowledge Graph Relation Chips */}
                        {msg.kg_relations && msg.kg_relations.length > 0 && (
                          <div className="space-y-1.5">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                                <Network className="h-3.5 w-3.5 text-indigo-600" />
                                Quan hệ Knowledge Graph ({msg.kg_relations.length})
                              </span>
                              {msg.kg_source && (
                                <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2 py-0.5 text-[10px] font-medium text-indigo-700">
                                  {msg.kg_source === 'neo4j' ? 'neo4j' : 'local_mirror'}
                                </span>
                              )}
                            </div>
                            <div className="flex flex-wrap gap-1.5">
                              {msg.kg_relations.map((rel, idx) => {
                                const { sourceLabel, relationLabel, targetLabel } =
                                  getKgRelationLabels(rel);
                                return (
                                  <span
                                    key={`${sourceLabel}-${rel.relation}-${targetLabel}-${idx}`}
                                    title={rel.description}
                                    className="inline-flex items-center gap-1 rounded-lg border border-indigo-100 bg-indigo-50/80 px-2.5 py-1 text-[11px] text-indigo-950"
                                  >
                                    <span className="font-semibold">{sourceLabel}</span>
                                    <span className="text-indigo-600">—[{relationLabel}]→</span>
                                    <span className="font-semibold">{targetLabel}</span>
                                  </span>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* Collapsible Citations */}
                        {msg.citations && msg.citations.length > 0 && (
                          <div className="border-t border-slate-200/80 pt-2.5">
                            <button
                              type="button"
                              onClick={() => toggleCitations(msg.id)}
                              className="flex w-full items-center justify-between text-left text-xs font-semibold text-slate-700 hover:text-teal-700"
                            >
                              <span className="inline-flex items-center gap-1.5">
                                <BookOpen className="h-3.5 w-3.5 text-teal-600" />
                                Nguồn tài liệu trích dẫn ({msg.citations.length})
                              </span>
                              {citationsOpen ? (
                                <ChevronUp className="h-4 w-4" />
                              ) : (
                                <ChevronDown className="h-4 w-4" />
                              )}
                            </button>
                            {citationsOpen && (
                              <div className="mt-2.5 space-y-2">
                                {msg.citations.map((cit) => (
                                  <CitationCard key={cit.chunk_id} citation={cit} />
                                ))}
                              </div>
                            )}
                          </div>
                        )}

                        {/* Collapsible Agent Trace */}
                        {msg.agent_steps && msg.agent_steps.length > 0 && (
                          <div className="border-t border-slate-200/80 pt-2.5">
                            <button
                              type="button"
                              onClick={() => toggleTrace(msg.id)}
                              className="flex w-full items-center justify-between text-left text-xs font-semibold text-slate-600 hover:text-slate-900"
                            >
                              <span>
                                Chi tiết xử lý Multi-Agent ({msg.agent_steps.length} bước)
                              </span>
                              {traceOpen ? (
                                <ChevronUp className="h-4 w-4" />
                              ) : (
                                <ChevronDown className="h-4 w-4" />
                              )}
                            </button>
                            {traceOpen && (
                              <div className="mt-2.5">
                                <AgentTracePanel
                                  steps={msg.agent_steps}
                                  totalLatencyMs={msg.total_latency_ms}
                                  title="Execution Trace (Chat Pipeline)"
                                />
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}

            {/* Optimistic Pending Turn */}
            {pendingUserText && (
              <>
                <div className="flex justify-end">
                  <div className="flex max-w-[82%] items-start gap-2.5">
                    <div className="rounded-2xl rounded-tr-sm bg-teal-600 px-4 py-3 text-sm text-white shadow-sm">
                      <p className="whitespace-pre-line">{pendingUserText}</p>
                    </div>
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-teal-100 text-teal-800">
                      <UserIcon className="h-4 w-4" />
                    </div>
                  </div>
                </div>
                <div className="flex justify-start">
                  <div className="flex items-center gap-2.5 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-600">
                    <Loader2 className="h-4 w-4 animate-spin text-teal-600" />
                    <span>
                      Multi-Agent đang kiểm tra an toàn, truy xuất RAG + Knowledge Graph...
                    </span>
                  </div>
                </div>
              </>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Error & Input Box */}
          <div className="border-t border-slate-100 bg-white p-4">
            {error && (
              <div
                role="alert"
                className="mb-3 flex items-center gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2 text-xs text-rose-800"
              >
                <AlertTriangle className="h-4 w-4 shrink-0 text-rose-600" />
                <span>{error}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="flex items-end gap-2.5">
              <textarea
                rows={2}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    void sendText(inputText);
                  }
                }}
                placeholder="Nhập câu hỏi về tiểu đường, chỉ số HbA1c, dinh dưỡng, hoặc kết quả sàng lọc..."
                className="flex-1 resize-none rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
              />
              <button
                type="submit"
                disabled={sending || !inputText.trim()}
                className="inline-flex h-11 shrink-0 items-center gap-2 rounded-xl bg-teal-600 px-4 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {sending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
                <span className="hidden sm:inline">Gửi</span>
              </button>
            </form>
            <p className="mt-1.5 text-[11px] text-slate-400">
              Nhấn Enter để gửi, Shift + Enter để xuống dòng.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
