import { AlertTriangle, CheckCircle2, ShieldAlert, Slash } from 'lucide-react';

interface RiskBadgeProps {
  band: string;
  size?: 'sm' | 'md' | 'lg';
}

const BAND_CONFIG: Record<
  string,
  {
    label: string;
    classes: string;
    icon: typeof CheckCircle2;
  }
> = {
  low: {
    label: 'Nguy cơ thấp',
    classes: 'border-emerald-200 bg-emerald-50 text-emerald-800',
    icon: CheckCircle2,
  },
  moderate: {
    label: 'Nguy cơ trung bình',
    classes: 'border-amber-200 bg-amber-50 text-amber-800',
    icon: AlertTriangle,
  },
  elevated: {
    label: 'Nguy cơ cao (cần lưu ý)',
    classes: 'border-rose-200 bg-rose-50 text-rose-800',
    icon: ShieldAlert,
  },
  out_of_scope: {
    label: 'Ngoài phạm vi sàng lọc',
    classes: 'border-slate-300 bg-slate-100 text-slate-700',
    icon: Slash,
  },
};

const SIZE_CLASSES: Record<'sm' | 'md' | 'lg', string> = {
  sm: 'px-2.5 py-0.5 text-xs',
  md: 'px-3 py-1 text-sm',
  lg: 'px-3.5 py-1.5 text-sm font-semibold',
};

export function RiskBadge({ band, size = 'md' }: RiskBadgeProps) {
  const cfg = BAND_CONFIG[band] ?? {
    label: band || 'Không xác định',
    classes: 'border-slate-200 bg-slate-100 text-slate-700',
    icon: Slash,
  };
  const Icon = cfg.icon;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border font-medium ${cfg.classes} ${SIZE_CLASSES[size]}`}
    >
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <span>{cfg.label}</span>
    </span>
  );
}
