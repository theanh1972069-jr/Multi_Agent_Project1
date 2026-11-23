import { ShieldAlert } from 'lucide-react';

export function DisclaimerBanner() {
  return (
    <div
      role="status"
      className="flex items-start gap-3 rounded-xl border border-teal-200 bg-teal-50/90 px-4 py-3 text-sm text-teal-950 shadow-sm"
    >
      <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-teal-700" />
      <p className="leading-relaxed">
        <span className="font-semibold">Lưu ý y khoa: </span>
        Hệ thống AI hỗ trợ sàng lọc tham khảo &amp; tra cứu kiến thức tiểu đường — Kết quả chỉ báo HbA1c ≥ 5.7%
        trên dữ liệu khảo sát NHANES, không thay thế chẩn đoán hay chỉ định của bác sĩ.
      </p>
    </div>
  );
}
