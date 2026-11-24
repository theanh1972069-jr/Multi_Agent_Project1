import type { KGRelation } from '../types/api';

export function formatDateTimeVi(iso: string): string {
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

export function formatShortDateVi(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return date.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
  });
}

const RELATION_LABELS_VI: Record<string, string> = {
  INCREASES_RISK_OF: 'Làm tăng nguy cơ',
  CAN_LEAD_TO: 'Có thể dẫn đến',
  MEASURED_BY: 'Được đo bằng',
  HAS_THRESHOLD: 'Có ngưỡng chẩn đoán',
  MAY_PRESENT_WITH: 'Có thể biểu hiện',
  HELPS_REDUCE: 'Giúp giảm nguy cơ',
  SUPPORTED_BY: 'Được hậu thuẫn bởi',
};

export function translateRelationVi(relation: string): string {
  return RELATION_LABELS_VI[relation] ?? relation;
}

export function getKgRelationLabels(rel: KGRelation): {
  sourceLabel: string;
  relationLabel: string;
  targetLabel: string;
} {
  const raw = rel as KGRelation & {
    source_label?: string;
    relation_label?: string;
    target_label?: string;
  };
  return {
    sourceLabel: raw.source_label || raw.source_node,
    relationLabel: raw.relation_label || translateRelationVi(raw.relation),
    targetLabel: raw.target_label || raw.target_node,
  };
}

export function formatGenderVi(gender: unknown): string {
  if (gender === 1 || gender === '1') return 'Nam';
  if (gender === 2 || gender === '2') return 'Nữ';
  return '—';
}
