import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { FeatureContribution } from '../types/api';

interface FactorChartProps {
  contributions: FeatureContribution[];
}

interface ChartDatum extends FeatureContribution {
  displayLabel: string;
}

function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: ChartDatum }>;
}) {
  if (!active || !payload || payload.length === 0) {
    return null;
  }
  const item = payload[0].payload;
  const isIncrease = item.direction === 'increase';

  return (
    <div className="rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-xs shadow-lg">
      <p className="font-semibold text-slate-900">{item.label_vi}</p>
      <p className="mt-1 text-slate-600">
        Giá trị đầu vào: <span className="font-mono font-medium text-slate-900">{item.value ?? '—'}</span>
      </p>
      <p className="mt-0.5 text-slate-600">
        Đóng góp thống kê:{' '}
        <span className={`font-mono font-semibold ${isIncrease ? 'text-rose-600' : 'text-teal-700'}`}>
          {item.contribution > 0 ? `+${item.contribution.toFixed(4)}` : item.contribution.toFixed(4)}
        </span>
      </p>
      <p className={`mt-1 font-medium ${isIncrease ? 'text-rose-600' : 'text-teal-700'}`}>
        {isIncrease ? '▲ Đẩy điểm sàng lọc tăng lên' : '▼ Giúp điểm sàng lọc giảm xuống'}
      </p>
    </div>
  );
}

export function FactorChart({ contributions }: FactorChartProps) {
  if (!contributions || contributions.length === 0) {
    return null;
  }

  const data: ChartDatum[] = contributions.map((item) => ({
    ...item,
    displayLabel: item.label_vi || item.feature,
  }));

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-900">
            Phân tích đóng góp từng đặc trưng (Explainable ML)
          </h3>
          <p className="mt-0.5 text-xs text-slate-500">
            Mức độ tác động thống kê của từng chỉ số đến điểm sàng lọc HbA1c ≥ 5.7%
          </p>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="inline-flex items-center gap-1.5 text-slate-600">
            <span className="h-2.5 w-2.5 rounded-sm bg-rose-500" />
            Tăng nguy cơ
          </span>
          <span className="inline-flex items-center gap-1.5 text-slate-600">
            <span className="h-2.5 w-2.5 rounded-sm bg-teal-600" />
            Giảm nguy cơ
          </span>
        </div>
      </div>

      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 6, right: 24, left: 10, bottom: 6 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
            <XAxis
              type="number"
              tick={{ fontSize: 11, fill: '#64748b' }}
              tickFormatter={(v: number) => v.toFixed(2)}
            />
            <YAxis
              type="category"
              dataKey="displayLabel"
              width={165}
              tick={{ fontSize: 12, fill: '#334155' }}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: '#f8fafc' }} />
            <ReferenceLine x={0} stroke="#64748b" strokeWidth={1.5} />
            <Bar dataKey="contribution" radius={[4, 4, 4, 4]} barSize={20}>
              {data.map((entry) => (
                <Cell
                  key={entry.feature}
                  fill={entry.direction === 'increase' ? '#e11d48' : '#0d9488'}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p className="mt-2 text-[11px] leading-relaxed text-slate-500">
        Lưu ý: Đây là đóng góp thống kê cục bộ của mô hình học máy trên tập khảo sát NHANES, không đồng nghĩa quan hệ nhân quả bệnh lý.
      </p>
    </div>
  );
}
