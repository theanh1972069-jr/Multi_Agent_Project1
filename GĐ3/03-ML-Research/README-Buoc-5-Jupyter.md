# Cách dùng — Giai đoạn 3, Bước 5 (Jupyter)

**Đây là notebook THỰC SỰ CÓ TRAIN MODEL** nếu bạn chạy các cell `FIT / TRAIN`. Code đã được kiểm tra cú pháp nhưng **chưa được ChatGPT chạy train**, và chưa có metric hoặc model thực nghiệm.

1. Giữ nguyên thư mục dự án `03-ML-Research/` đã dùng ở Bước 4. Giữ nguồn dữ liệu XPT trong `data/raw/`.
2. Đảm bảo bạn đã chạy cell xuất file ở Bước 4 và có `data/processed/nhanes_step4_screening_candidate_REVIEW_ONLY.csv`.
3. Cài thêm trong môi trường Jupyter: `%pip install "scikit-learn>=1.6" "joblib>=1.4"`, sau đó restart kernel.
4. Mở `notebooks/05_NHANES_Model_Training.ipynb`, chạy cell lần lượt.
5. Trước phần **FIT / TRAIN**, đọc cảnh báo; đây là bước bạn trực tiếp huấn luyện ba baseline.
6. Chỉ đánh giá validation (test **chưa được dùng**). Gửi cho ChatGPT output cell cuối và lỗi nếu có. Không đăng/đẩy nguyên dữ liệu quan sát lên nguồn công khai không cần thiết.

**Output dự kiến do máy bạn tạo:** `data/outputs/model_training/step5_validation_metrics.csv`, `step5_metadata.json`, split CSV; `models/baseline/nhanes_hba1c_baseline_step5.joblib`.

**Cảnh báo:** Mục tiêu phân loại HbA1c >= 5,7% không phải chẩn đoán tiểu đường type 2 hoặc dự báo tương lai. Chưa phân tích survey weights và thiếu xác thực bên ngoài.
