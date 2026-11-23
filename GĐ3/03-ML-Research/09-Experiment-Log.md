# EXPERIMENT LOG — GIAI ĐOẠN 3

**Dự án:** Multi-Agent AI System for Diabetes Risk Assessment  
**Tạo ngày:** 2026-10-31  
**Trạng thái:** Chưa có lần thực nghiệm nào, chưa chạy code hoặc huấn luyện mô hình.

## Quy ước ghi nhật ký

Mỗi lần thực hành thực tế tạo một bản ghi gồm: `experiment_id`, ngày/giờ, người thực hiện, dataset + phiên bản, phạm vi mẫu, mục đích, commit/version code, môi trường, seed, đặc trưng, nhãn, phương pháp, metric, đường dẫn artifact, kết quả quan sát, lỗi, quyết định, link báo cáo. Chỉ điền kết quả khi có thông tin từ người thực hiện.

## Nhật ký quyết định / nghiên cứu

| Ngày | ID | Loại | Nội dung | Trạng thái |
|---|---|---|---|---|
| 2026-10-31 | DEC-001 | Dataset | Ưu tiên NHANES 2021–2023 và BRFSS 2025 từ CDC; giữ hai tập/model riêng | Kế hoạch |
| 2026-10-31 | DEC-002 | Nhãn | NHANES: phân loại chỉ dấu HbA1c bất thường là ứng viên nghiên cứu; BRFSS: nhãn tự khai từng được bác sĩ chẩn đoán | Chờ rà soát codebook và dữ liệu |
| 2026-10-31 | DEC-003 | Workflow | Người dùng trực tiếp chạy code và train; trợ lý chỉ hướng dẫn, thông báo trước; không bịa metrics | Đã thống nhất |

## Danh sách thực nghiệm thực tế

*Chưa thực hiện. Không có điểm số, biểu đồ hoặc mô hình được ghi nhận.*

## Mẫu cho lần thực nghiệm sau (chưa điền)

### EXP-XXXX — [Tên thí nghiệm]
- **Ngày thực hiện:** Chưa thực hiện
- **Dataset và phiên bản:** Chưa xác định
- **Dữ liệu gốc / checksum:** Chưa xác định
- **Quy tắc lọc và nhãn:** Chưa chốt
- **Feature set / split / seed:** Chưa chốt
- **Mô hình và pipeline:** Chưa xác định
- **Metric:** Chưa đo
- **Kết quả / artifact:** Chưa có
- **Lỗi / cách sửa:** Chưa có
- **Kết luận:** Chưa có


## 2026-11-01 — Bước 2 (chuẩn bị, chưa thực nghiệm)

- **ID:** DEC-004
- **Quyết định:** Tất cả các bước ML dùng Jupyter Notebook, người dùng tự tải dữ liệu và chạy/huấn luyện ở máy cá nhân; ChatGPT chỉ hướng dẫn và rà soát.
- **Tệp hướng dẫn:** `notebooks/02_NHANES_Data_Understanding.ipynb`, `02-Data-Understanding.md`, `README-Buoc-2-Jupyter.md`.
- **Phạm vi:** Đọc và left join `DEMO_L`, `BMX_L`, `GHB_L`, `DIQ_L` bằng `SEQN`, ghi nhận missingness, không tạo nhãn cuối hoặc train.
- **Trạng thái:** Đã thiết kế notebook; **chưa chạy, chưa có con số thực nghiệm**.
