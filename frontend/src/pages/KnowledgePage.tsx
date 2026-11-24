import { useEffect, useMemo, useState } from 'react';
import {
  AlertCircle,
  BookOpenCheck,
  ExternalLink,
  FileText,
  Filter,
  Globe,
  Layers,
  Loader2,
  Network,
  Search,
  Sparkles,
} from 'lucide-react';
import { ApiError, apiClient } from '../api/client';
import type {
  KnowledgeGraphEdge,
  KnowledgeGraphNode,
  KnowledgeGraphOut,
  KnowledgeSourceOut,
} from '../types/api';
import { formatDateTimeVi, translateRelationVi } from '../utils/format';

interface CategoryStyle {
  label: string;
  pillClass: string;
  fill: string;
  stroke: string;
  textFill: string;
}

const CATEGORY_STYLES: Record<string, CategoryStyle> = {
  Condition: {
    label: 'Bệnh lý / Giai đoạn',
    pillClass: 'border-rose-200 bg-rose-50 text-rose-800',
    fill: '#fff1f2',
    stroke: '#e11d48',
    textFill: '#881337',
  },
  Disease: {
    label: 'Bệnh lý',
    pillClass: 'border-rose-200 bg-rose-50 text-rose-800',
    fill: '#fff1f2',
    stroke: '#e11d48',
    textFill: '#881337',
  },
  RiskFactor: {
    label: 'Yếu tố nguy cơ',
    pillClass: 'border-amber-200 bg-amber-50 text-amber-800',
    fill: '#fffbeb',
    stroke: '#d97706',
    textFill: '#78350f',
  },
  Biomarker: {
    label: 'Chỉ dấu xét nghiệm',
    pillClass: 'border-sky-200 bg-sky-50 text-sky-800',
    fill: '#f0f9ff',
    stroke: '#0284c7',
    textFill: '#0c4a6e',
  },
  Symptom: {
    label: 'Triệu chứng',
    pillClass: 'border-purple-200 bg-purple-50 text-purple-800',
    fill: '#faf5ff',
    stroke: '#9333ea',
    textFill: '#581c87',
  },
  Complication: {
    label: 'Biến chứng',
    pillClass: 'border-orange-200 bg-orange-50 text-orange-800',
    fill: '#fff7ed',
    stroke: '#ea580c',
    textFill: '#7c2d12',
  },
  LifestyleRecommendation: {
    label: 'Khuyến nghị lối sống',
    pillClass: 'border-emerald-200 bg-emerald-50 text-emerald-800',
    fill: '#ecfdf5',
    stroke: '#059669',
    textFill: '#064e3b',
  },
  SourceDocument: {
    label: 'Tài liệu nguồn',
    pillClass: 'border-indigo-200 bg-indigo-50 text-indigo-800',
    fill: '#eef2ff',
    stroke: '#4f46e5',
    textFill: '#312e81',
  },
};

const DEFAULT_STYLE: CategoryStyle = {
  label: 'Khái niệm khác',
  pillClass: 'border-slate-200 bg-slate-100 text-slate-700',
  fill: '#f8fafc',
  stroke: '#475569',
  textFill: '#0f172a',
};

function getCategoryStyle(type: string): CategoryStyle {
  return CATEGORY_STYLES[type] ?? DEFAULT_STYLE;
}

function truncateLabel(text: string, maxLen = 22): string {
  if (text.length <= maxLen) return text;
  return `${text.slice(0, maxLen - 1)}…`;
}

interface PositionedNode {
  node: KnowledgeGraphNode;
  x: number;
  y: number;
}

const TYPE_COLUMN_ORDER: Record<string, number> = {
  RiskFactor: 0,
  LifestyleRecommendation: 0,
  Condition: 1,
  Disease: 1,
  Biomarker: 2,
  Symptom: 2,
  Complication: 3,
  SourceDocument: 3,
};

function computeNodePositions(
  nodes: KnowledgeGraphNode[],
  edges: KnowledgeGraphEdge[],
  selectedId: string | null,
  focusNeighborsOnly: boolean,
): { positioned: PositionedNode[]; visibleEdges: KnowledgeGraphEdge[] } {
  const width = 920;
  const height = 520;

  if (focusNeighborsOnly && selectedId) {
    const centerNode = nodes.find((n) => n.id === selectedId);
    if (centerNode) {
      const incidentEdges = edges.filter(
        (e) => e.source === selectedId || e.target === selectedId,
      );
      const neighborIds = new Set<string>();
      for (const edge of incidentEdges) {
        if (edge.source !== selectedId) neighborIds.add(edge.source);
        if (edge.target !== selectedId) neighborIds.add(edge.target);
      }
      const neighbors = nodes.filter((n) => neighborIds.has(n.id));
      const positioned: PositionedNode[] = [
        { node: centerNode, x: width / 2, y: height / 2 },
      ];
      const count = neighbors.length;
      const rx = 310;
      const ry = 190;
      neighbors.forEach((n, idx) => {
        const angle = (2 * Math.PI * idx) / Math.max(1, count) - Math.PI / 2;
        positioned.push({
          node: n,
          x: width / 2 + rx * Math.cos(angle),
          y: height / 2 + ry * Math.sin(angle),
        });
      });
      return { positioned, visibleEdges: incidentEdges };
    }
  }

  // Group into 4 clean vertical columns for full graph overview
  const columns: KnowledgeGraphNode[][] = [[], [], [], []];
  for (const node of nodes) {
    const colIdx = TYPE_COLUMN_ORDER[node.type] ?? 2;
    columns[colIdx].push(node);
  }

  const colX = [125, 355, 590, 810];
  const positioned: PositionedNode[] = [];
  columns.forEach((colNodes, colIdx) => {
    const count = colNodes.length;
    if (count === 0) return;
    const topPad = 42;
    const usableH = height - topPad * 2;
    colNodes.forEach((node, rowIdx) => {
      const y =
        count === 1
          ? height / 2
          : topPad + (usableH * rowIdx) / Math.max(1, count - 1);
      positioned.push({ node, x: colX[colIdx], y });
    });
  });

  const visibleIdSet = new Set(positioned.map((p) => p.node.id));
  const visibleEdges = edges.filter(
    (e) => visibleIdSet.has(e.source) && visibleIdSet.has(e.target),
  );
  return { positioned, visibleEdges };
}

export function KnowledgePage() {
  const [activeTab, setActiveTab] = useState<'graph' | 'sources'>('graph');
  const [sources, setSources] = useState<KnowledgeSourceOut[]>([]);
  const [graph, setGraph] = useState<KnowledgeGraphOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [focusNeighborsOnly, setFocusNeighborsOnly] = useState(false);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [sourcesRes, graphRes] = await Promise.all([
          apiClient.listKnowledgeSources(),
          apiClient.getKnowledgeGraph(),
        ]);
        if (!active) return;
        setSources(sourcesRes);
        setGraph(graphRes);
        const defaultNode =
          graphRes.nodes.find((n) => n.id === 'cond_prediabetes') ??
          graphRes.nodes[0] ??
          null;
        if (defaultNode) {
          setSelectedNodeId(defaultNode.id);
        }
      } catch (err) {
        if (!active) return;
        setError(
          err instanceof ApiError
            ? err.detail
            : 'Không thể tải dữ liệu Tri thức & Knowledge Graph từ máy chủ.',
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

  const nodes = graph?.nodes ?? [];
  const edges = graph?.edges ?? [];

  const sourceMap = useMemo(() => {
    const map = new Map<string, KnowledgeSourceOut>();
    for (const s of sources) {
      map.set(s.source_id, s);
    }
    return map;
  }, [sources]);

  const nodeMap = useMemo(() => {
    const map = new Map<string, KnowledgeGraphNode>();
    for (const n of nodes) {
      map.set(n.id, n);
    }
    return map;
  }, [nodes]);

  const availableCategories = useMemo(() => {
    const counts = new Map<string, number>();
    for (const n of nodes) {
      counts.set(n.type, (counts.get(n.type) ?? 0) + 1);
    }
    return Array.from(counts.entries());
  }, [nodes]);

  const filteredNodes = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    return nodes.filter((node) => {
      if (categoryFilter !== 'ALL' && node.type !== categoryFilter) {
        return false;
      }
      if (!q) return true;
      const haystack = [
        node.id,
        node.label,
        node.description ?? '',
        ...(node.keywords ?? []),
      ]
        .join(' ')
        .toLowerCase();
      return haystack.includes(q);
    });
  }, [nodes, categoryFilter, searchQuery]);

  const filteredNodeIds = useMemo(
    () => new Set(filteredNodes.map((n) => n.id)),
    [filteredNodes],
  );

  // Include selected node + its direct neighbors if focusNeighborsOnly is toggled
  const graphNodesForSvg = useMemo(() => {
    if (focusNeighborsOnly && selectedNodeId) {
      const neighborIds = new Set<string>([selectedNodeId]);
      for (const e of edges) {
        if (e.source === selectedNodeId) neighborIds.add(e.target);
        if (e.target === selectedNodeId) neighborIds.add(e.source);
      }
      return nodes.filter((n) => neighborIds.has(n.id));
    }
    return filteredNodes;
  }, [focusNeighborsOnly, selectedNodeId, edges, nodes, filteredNodes]);

  const { positioned, visibleEdges } = useMemo(
    () => computeNodePositions(graphNodesForSvg, edges, selectedNodeId, focusNeighborsOnly),
    [graphNodesForSvg, edges, selectedNodeId, focusNeighborsOnly],
  );

  const posMap = useMemo(() => {
    const map = new Map<string, PositionedNode>();
    for (const item of positioned) {
      map.set(item.node.id, item);
    }
    return map;
  }, [positioned]);

  const selectedNode = selectedNodeId ? nodeMap.get(selectedNodeId) ?? null : null;

  const selectedRelations = useMemo(() => {
    if (!selectedNodeId) return { outgoing: [] as KnowledgeGraphEdge[], incoming: [] as KnowledgeGraphEdge[] };
    return {
      outgoing: edges.filter((e) => e.source === selectedNodeId),
      incoming: edges.filter((e) => e.target === selectedNodeId),
    };
  }, [edges, selectedNodeId]);

  const selectedNeighborIds = useMemo(() => {
    const set = new Set<string>();
    if (!selectedNodeId) return set;
    set.add(selectedNodeId);
    for (const e of selectedRelations.outgoing) set.add(e.target);
    for (const e of selectedRelations.incoming) set.add(e.source);
    return set;
  }, [selectedNodeId, selectedRelations]);

  return (
    <div className="space-y-6">
      {/* Page Header & Metrics */}
      <div className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm lg:flex-row lg:items-center">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-700">
              <Network className="h-3.5 w-3.5" />
              Hybrid Knowledge Base
            </span>
            {graph && (
              <span className="inline-flex items-center gap-1.5 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-800">
                {graph.kg_source === 'neo4j' ? 'Neo4j Graph DB' : 'Local JSON Mirror'}
              </span>
            )}
          </div>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900">
            Tri thức Y khoa &amp; Đồ thị Tiểu đường
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Khám phá mạng lưới quan hệ y khoa chuẩn hóa và các tài liệu đang hoạt động trong kho vector ChromaDB.
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3">
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-center">
            <p className="text-[11px] font-medium text-slate-500">Tài liệu Active</p>
            <p className="mt-0.5 text-lg font-bold text-slate-900">{sources.length}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-center">
            <p className="text-[11px] font-medium text-slate-500">Thực thể KG</p>
            <p className="mt-0.5 text-lg font-bold text-slate-900">{nodes.length}</p>
          </div>
          <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-center">
            <p className="text-[11px] font-medium text-slate-500">Quan hệ KG</p>
            <p className="mt-0.5 text-lg font-bold text-slate-900">{edges.length}</p>
          </div>
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-3">
        <button
          type="button"
          onClick={() => setActiveTab('graph')}
          className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-colors ${
            activeTab === 'graph'
              ? 'bg-teal-600 text-white shadow-sm'
              : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
          }`}
        >
          <Network className="h-4 w-4" />
          <span>Đồ thị Tri thức Y khoa (KG Explorer)</span>
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('sources')}
          className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-colors ${
            activeTab === 'sources'
              ? 'bg-teal-600 text-white shadow-sm'
              : 'border border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
          }`}
        >
          <BookOpenCheck className="h-4 w-4" />
          <span>Danh mục Tài liệu Y khoa ({sources.length})</span>
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

      {loading ? (
        <div className="flex h-64 items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-500">
          <Loader2 className="mr-2 h-5 w-5 animate-spin text-teal-600" />
          Đang tải tri thức y khoa và đồ thị quan hệ...
        </div>
      ) : activeTab === 'graph' ? (
        <div className="space-y-5">
          {/* Filters & Search */}
          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="relative flex-1 lg:max-w-sm">
                <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Tìm khái niệm (ví dụ: HbA1c, vòng eo, tiền tiểu đường)..."
                  className="w-full rounded-xl border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-900 placeholder-slate-400 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20"
                />
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => setFocusNeighborsOnly((prev) => !prev)}
                  disabled={!selectedNode}
                  className={`inline-flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-semibold transition-colors disabled:opacity-50 ${
                    focusNeighborsOnly
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-800'
                      : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  <span>
                    {focusNeighborsOnly
                      ? 'Đang thu gọn quanh nút chọn'
                      : 'Tập trung lân cận nút chọn'}
                  </span>
                </button>
              </div>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-1.5">
              <span className="mr-1 inline-flex items-center gap-1 text-xs font-medium text-slate-500">
                <Filter className="h-3.5 w-3.5" />
                Nhóm:
              </span>
              <button
                type="button"
                onClick={() => setCategoryFilter('ALL')}
                className={`rounded-full border px-3 py-1 text-xs font-semibold transition-colors ${
                  categoryFilter === 'ALL'
                    ? 'border-teal-600 bg-teal-600 text-white'
                    : 'border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                }`}
              >
                Tất cả ({nodes.length})
              </button>
              {availableCategories.map(([cat, count]) => {
                const style = getCategoryStyle(cat);
                const active = categoryFilter === cat;
                return (
                  <button
                    key={cat}
                    type="button"
                    onClick={() => {
                      setCategoryFilter(cat);
                      setFocusNeighborsOnly(false);
                    }}
                    className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
                      active
                        ? 'border-slate-900 bg-slate-900 text-white'
                        : `${style.pillClass} hover:opacity-85`
                    }`}
                  >
                    {style.label} ({count})
                  </button>
                );
              })}
            </div>
          </div>

          {/* Graph Canvas + Node Inspector */}
          <div className="grid gap-5 xl:grid-cols-12">
            {/* SVG Visualization */}
            <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm xl:col-span-7">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h2 className="text-sm font-bold text-slate-900">
                    Sơ đồ quan hệ trực quan ({positioned.length} nút, {visibleEdges.length} cạnh)
                  </h2>
                  <p className="text-[11px] text-slate-500">
                    Nhấp vào bất kỳ nút nào trên đồ thị để làm nổi bật quan hệ và nguồn tài liệu bảo chứng.
                  </p>
                </div>
              </div>

              {positioned.length === 0 ? (
                <div className="flex h-80 items-center justify-center rounded-xl border border-dashed border-slate-200 bg-slate-50 text-xs text-slate-500">
                  Không có thực thể nào khớp với bộ lọc hiện tại.
                </div>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-slate-100 bg-slate-50/70">
                  <svg
                    viewBox="0 0 920 520"
                    className="h-[460px] w-full min-w-[680px] select-none"
                    role="img"
                    aria-label="Đồ thị Tri thức Tiểu đường"
                  >
                    <defs>
                      <marker
                        id="kg-arrow"
                        markerWidth="8"
                        markerHeight="8"
                        refX="7"
                        refY="3"
                        orient="auto"
                      >
                        <path d="M0,0 L0,6 L7,3 z" fill="#94a3b8" />
                      </marker>
                      <marker
                        id="kg-arrow-active"
                        markerWidth="9"
                        markerHeight="9"
                        refX="8"
                        refY="3.5"
                        orient="auto"
                      >
                        <path d="M0,0 L0,7 L8,3.5 z" fill="#0d9488" />
                      </marker>
                    </defs>

                    {/* Edges */}
                    {visibleEdges.map((edge, idx) => {
                      const from = posMap.get(edge.source);
                      const to = posMap.get(edge.target);
                      if (!from || !to) return null;
                      const isConnected =
                        selectedNodeId !== null &&
                        (edge.source === selectedNodeId || edge.target === selectedNodeId);
                      const dimmed = selectedNodeId !== null && !isConnected;
                      const midX = (from.x + to.x) / 2;
                      const midY = (from.y + to.y) / 2;

                      return (
                        <g key={`${edge.source}-${edge.relation}-${edge.target}-${idx}`}>
                          <line
                            x1={from.x}
                            y1={from.y}
                            x2={to.x}
                            y2={to.y}
                            stroke={isConnected ? '#0d9488' : '#cbd5e1'}
                            strokeWidth={isConnected ? 2.2 : 1.1}
                            strokeOpacity={dimmed ? 0.22 : isConnected ? 0.95 : 0.65}
                            markerEnd={isConnected ? 'url(#kg-arrow-active)' : 'url(#kg-arrow)'}
                          />
                          {(isConnected || focusNeighborsOnly) && (
                            <g transform={`translate(${midX}, ${midY})`}>
                              <rect
                                x={-48}
                                y={-9}
                                width={96}
                                height={18}
                                rx={6}
                                fill="#ffffff"
                                stroke="#ccfbf1"
                                strokeWidth={1}
                              />
                              <text
                                textAnchor="middle"
                                dominantBaseline="central"
                                fontSize={9}
                                fontWeight={600}
                                fill="#0f766e"
                              >
                                {truncateLabel(translateRelationVi(edge.relation), 18)}
                              </text>
                            </g>
                          )}
                        </g>
                      );
                    })}

                    {/* Nodes */}
                    {positioned.map(({ node, x, y }) => {
                      const style = getCategoryStyle(node.type);
                      const isSelected = node.id === selectedNodeId;
                      const isNeighbor = selectedNeighborIds.has(node.id);
                      const dimmed =
                        selectedNodeId !== null &&
                        !isSelected &&
                        !isNeighbor &&
                        !focusNeighborsOnly;
                      const pillWidth = 152;
                      const pillHeight = 34;

                      return (
                        <g
                          key={node.id}
                          transform={`translate(${x}, ${y})`}
                          onClick={() => setSelectedNodeId(node.id)}
                          className="cursor-pointer"
                          opacity={dimmed ? 0.35 : 1}
                        >
                          <rect
                            x={-pillWidth / 2}
                            y={-pillHeight / 2}
                            width={pillWidth}
                            height={pillHeight}
                            rx={10}
                            fill={isSelected ? style.stroke : style.fill}
                            stroke={style.stroke}
                            strokeWidth={isSelected ? 2.5 : 1.4}
                          />
                          <text
                            textAnchor="middle"
                            y={-2}
                            fontSize={10.5}
                            fontWeight={700}
                            fill={isSelected ? '#ffffff' : style.textFill}
                          >
                            {truncateLabel(node.label, 21)}
                          </text>
                          <text
                            textAnchor="middle"
                            y={11}
                            fontSize={8.5}
                            fill={isSelected ? '#f8fafc' : '#64748b'}
                          >
                            {node.type}
                          </text>
                        </g>
                      );
                    })}
                  </svg>
                </div>
              )}
            </div>

            {/* Selected Node Inspector */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm xl:col-span-5">
              {selectedNode ? (
                <div className="space-y-4">
                  <div>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span
                        className={`rounded-full border px-2.5 py-0.5 text-[11px] font-semibold ${getCategoryStyle(selectedNode.type).pillClass}`}
                      >
                        {getCategoryStyle(selectedNode.type).label} ({selectedNode.type})
                      </span>
                      <span className="font-mono text-[11px] text-slate-400">
                        {selectedNode.id}
                      </span>
                    </div>
                    <h2 className="mt-2 text-lg font-bold text-slate-900">{selectedNode.label}</h2>
                    {selectedNode.description && (
                      <p className="mt-1.5 text-xs leading-relaxed text-slate-600">
                        {selectedNode.description}
                      </p>
                    )}
                  </div>

                  {/* Outgoing & Incoming Relations */}
                  <div className="space-y-3 border-t border-slate-100 pt-3">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Quan hệ kết nối ({selectedRelations.outgoing.length + selectedRelations.incoming.length})
                    </h3>

                    <div className="max-h-60 space-y-2 overflow-y-auto pr-1">
                      {selectedRelations.outgoing.map((edge, idx) => {
                        const targetNode = nodeMap.get(edge.target);
                        return (
                          <button
                            key={`out-${edge.target}-${edge.relation}-${idx}`}
                            type="button"
                            onClick={() => setSelectedNodeId(edge.target)}
                            className="w-full rounded-xl border border-slate-200 bg-slate-50/70 p-2.5 text-left transition-colors hover:border-teal-300 hover:bg-teal-50/40"
                          >
                            <div className="flex flex-wrap items-center gap-1 text-xs">
                              <span className="font-semibold text-teal-700">
                                → [{translateRelationVi(edge.relation)}]
                              </span>
                              <span className="font-bold text-slate-900">
                                {targetNode?.label ?? edge.target}
                              </span>
                            </div>
                            {edge.description && (
                              <p className="mt-1 text-[11px] text-slate-600">{edge.description}</p>
                            )}
                          </button>
                        );
                      })}

                      {selectedRelations.incoming.map((edge, idx) => {
                        const sourceNode = nodeMap.get(edge.source);
                        return (
                          <button
                            key={`in-${edge.source}-${edge.relation}-${idx}`}
                            type="button"
                            onClick={() => setSelectedNodeId(edge.source)}
                            className="w-full rounded-xl border border-slate-200 bg-slate-50/70 p-2.5 text-left transition-colors hover:border-indigo-300 hover:bg-indigo-50/40"
                          >
                            <div className="flex flex-wrap items-center gap-1 text-xs">
                              <span className="font-bold text-slate-900">
                                {sourceNode?.label ?? edge.source}
                              </span>
                              <span className="font-semibold text-indigo-700">
                                —[{translateRelationVi(edge.relation)}]→ (nút này)
                              </span>
                            </div>
                            {edge.description && (
                              <p className="mt-1 text-[11px] text-slate-600">{edge.description}</p>
                            )}
                          </button>
                        );
                      })}

                      {selectedRelations.outgoing.length === 0 &&
                        selectedRelations.incoming.length === 0 && (
                          <p className="text-xs italic text-slate-400">
                            Không có cạnh kết nối nào thuộc các nguồn tài liệu đang hoạt động.
                          </p>
                        )}
                    </div>
                  </div>

                  {/* Backing Sources */}
                  <div className="border-t border-slate-100 pt-3">
                    <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Tài liệu y khoa bảo chứng ({selectedNode.source_ids?.length ?? 0})
                    </h3>
                    <div className="space-y-1.5">
                      {(selectedNode.source_ids ?? []).map((sid) => {
                        const doc = sourceMap.get(sid);
                        return (
                          <div
                            key={sid}
                            className="flex items-center justify-between gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs"
                          >
                            <div className="min-w-0">
                              <p className="truncate font-semibold text-slate-900">
                                {doc ? doc.title : sid}
                              </p>
                              <p className="text-[11px] text-slate-500">
                                {sid}
                                {doc ? ` • ${doc.publisher}` : ''}
                              </p>
                            </div>
                            {doc?.source_url && (
                              <a
                                href={doc.source_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex shrink-0 items-center gap-1 rounded-lg border border-teal-200 bg-white px-2 py-1 text-[11px] font-medium text-teal-700 hover:bg-teal-50"
                              >
                                <span>Mở</span>
                                <ExternalLink className="h-3 w-3" />
                              </a>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex h-64 items-center justify-center text-xs text-slate-500">
                  Chọn một thực thể để xem chi tiết quan hệ y khoa.
                </div>
              )}
            </div>
          </div>

          {/* Structured Node Cards List */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="mb-3 text-sm font-bold text-slate-900">
              Danh sách thực thể ({filteredNodes.length})
            </h3>
            <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
              {filteredNodes.map((node) => {
                const style = getCategoryStyle(node.type);
                const isSelected = node.id === selectedNodeId;
                const isHighlighted = filteredNodeIds.has(node.id) && isSelected;
                return (
                  <button
                    key={node.id}
                    type="button"
                    onClick={() => setSelectedNodeId(node.id)}
                    className={`rounded-xl border p-3 text-left transition-all ${
                      isHighlighted
                        ? 'border-teal-600 bg-teal-50/70 ring-2 ring-teal-500/20'
                        : 'border-slate-200 bg-white hover:border-teal-300 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${style.pillClass}`}
                      >
                        {style.label}
                      </span>
                      <span className="font-mono text-[10px] text-slate-400">
                        {node.source_ids?.length ?? 0} nguồn
                      </span>
                    </div>
                    <p className="mt-1.5 text-xs font-bold text-slate-900">{node.label}</p>
                    {node.description && (
                      <p className="mt-1 line-clamp-2 text-[11px] text-slate-500">
                        {node.description}
                      </p>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        /* TAB 2: Active Medical Documents */
        <div className="grid gap-4 md:grid-cols-2">
          {sources.length === 0 ? (
            <div className="col-span-full rounded-2xl border border-dashed border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
              Hiện chưa có tài liệu nào ở trạng thái hoạt động (active).
            </div>
          ) : (
            sources.map((src) => (
              <div
                key={src.id}
                className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition-shadow hover:shadow"
              >
                <div>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-50 px-2.5 py-0.5 text-[11px] font-semibold text-teal-800">
                      <FileText className="h-3.5 w-3.5" />
                      {src.source_id}
                    </span>
                    <div className="flex items-center gap-1.5">
                      <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium uppercase text-slate-700">
                        <Globe className="h-3 w-3" />
                        {src.language}
                      </span>
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">
                        <Layers className="h-3 w-3" />
                        {src.chunk_count} chunks
                      </span>
                    </div>
                  </div>

                  <h3 className="mt-3 text-base font-bold text-slate-900">{src.title}</h3>
                  <p className="mt-1 text-xs font-medium text-teal-700">
                    Đơn vị xuất bản: {src.publisher}
                  </p>
                </div>

                <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-3 text-xs">
                  <span className="text-[11px] text-slate-400">
                    Cập nhật: {formatDateTimeVi(src.updated_at)}
                  </span>
                  {src.source_url ? (
                    <a
                      href={src.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-lg border border-teal-200 bg-teal-50/70 px-3 py-1.5 text-xs font-semibold text-teal-800 hover:bg-teal-100"
                    >
                      <span>Xem tài liệu gốc</span>
                      <ExternalLink className="h-3.5 w-3.5" />
                    </a>
                  ) : (
                    <span className="text-[11px] italic text-slate-400">Tài liệu nội bộ</span>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
