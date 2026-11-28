# GIAI ĐOẠN 3 — ML/DL RESEARCH ROADMAP

**Dự án:** Multi-Agent AI System for Diabetes Risk Assessment  
**Phiên bản:** v0.1 — 2026-10-31  
**Tình trạng:** Đã khởi động Bước 1; chưa bắt đầu lập trình, tải dữ liệu hay huấn luyện mô hình.

## Nguyên tắc phối hợp

- **Người thực hành:** Chủ dự án trực tiếp tải dataset, lập trình, chạy thử, huấn luyện và đánh giá mô hình trên máy cá nhân.
- **Người hướng dẫn (ChatGPT):** Giải thích, hướng dẫn từng bước, cung cấp ví dụ khi được yêu cầu, rà soát kết quả và giúp khắc phục lỗi.
- **Trước mọi bước có lập trình/huấn luyện:** Thông báo rõ mục đích, file cần tạo, lệnh cần chạy, kết quả mong đợi và điểm cần kiểm tra. Không tự chạy code hoặc train thay người dùng.
- **Mọi giá trị thực nghiệm:** Chỉ ghi khi người dùng cung cấp kết quả thật hoặc việc chạy đã được đồng ý và diễn ra minh bạch. Chưa có kết quả thì ghi `Chưa thực hiện`, tuyệt đối không bịa metrics.
- Mỗi bước cập nhật một file Markdown; `09-Experiment-Log.md` lưu nhật ký kết quả/ quyết định. Cuối giai đoạn có thể xuất báo cáo `.docx` theo yêu cầu.

## 8 bước thực hiện

| Bước | Chủ đề | Đầu ra tài liệu | Trạng thái |
|---|---|---|---|
| 1 | Lựa chọn dataset & định nghĩa nhiệm vụ | `01-Dataset-Selection.md` | Bản nháp hoàn thành, chờ rà soát |
| 2 | Tải dữ liệu, kiểm tra cấu trúc, codebook | `02-Data-Understanding.md` | Chưa thực hiện |
| 3 | EDA, chất lượng dữ liệu, phân bố | `03-EDA.md` | Chưa thực hiện |
| 4 | Cleaning, splitting, preprocessing | `04-Data-Preprocessing.md` | Chưa thực hiện |
| 5 | Huấn luyện & so sánh baseline | `05-Model-Training.md` | Chưa thực hiện |
| 6 | Đánh giá, calibration, sensitivity | `06-Model-Evaluation.md` | Chưa thực hiện |
| 7 | Explainability, cảnh báo & giới hạn | `07-Model-Explainability.md` | Chưa thực hiện |
| 8 | Model manifest, đóng gói, Prediction API | `08-Model-Deployment.md` | Chưa thực hiện |

## Quan hệ với Giai đoạn 2

- Giai đoạn 2 có 6 bản thiết kế v0.1. `06-Technical-Design.md` đang chứa **feature schema Pima dự thảo**; không xem là hợp đồng đầu vào cuối cùng của NHANES/BRFSS.
- Giai đoạn 3 phải xác định lại: tên mô hình, nhãn, feature list, đơn vị, missing-value policy, giới hạn dân số, preprocessing, version, metric, output schema, score calibration trước khi chốt API.
- Hai mô hình nghiên cứu ban đầu dự kiến: **NHANES lab-referenced** và **BRFSS self-report**, huấn luyện và đánh giá riêng, chưa gộp dữ liệu.

## Điều kiện được chuyển từ Bước 1 sang Bước 2

- [x] Xác định nguồn dữ liệu chính thức (CDC)
- [x] Phân biệt rõ 2 loại nhãn; không tự gọi là dự báo tiến triển type 2
- [x] Thống nhất nguyên tắc không gộp hai bộ ngay
- [x] Lập bản danh sách file/codebook cần xem
- [ ] Người dùng rà soát phạm vi bản v0.1
- [ ] Bước 2 mới tải dữ liệu và chạy mã để kiểm tra số dòng thực tế sau ghép/lọc

**Cảnh báo y khoa:** Mục đích hiện tại là nghiên cứu/sàng lọc, không chẩn đoán bệnh và chưa đủ cơ sở xác nhận nguy cơ bệnh trong tương lai.
