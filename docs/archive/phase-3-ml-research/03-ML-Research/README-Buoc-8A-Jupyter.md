# Hướng dẫn Bước 8A — Jupyter local inference (NGƯỜI DÙNG THỰC HÀNH)

1. Giữ nguyên file model `models/baseline/nhanes_hba1c_baseline_step5.joblib` và hai tệp `data/outputs/model_training/step5_metadata.json`, `validation.csv` trên máy bạn.
2. Giải nén ZIP vào `03-ML-Research` theo đúng cấu trúc, KHÔNG ghi đè file model/data gốc. Chọn kernel Python **3.13.9**, sklearn **1.8.0** (đúng lần train).
3. Mở `notebooks/08A_NHANES_Inference_Preflight.ipynb` trong Jupyter. Đọc các ô Markdown, chạy từng ô Code bằng `Shift+Enter`.
4. Ô model loading có `joblib.load()` chỉ được chạy sau khi SHA256/versions đúng; không tải hoặc nạp `.joblib` từ nguồn không tin cậy.
5. Notebook **KHÔNG có `.fit()`**, chỉ nạp model gốc để inference, kiểm tra Validation và input **giả lập**. Test holdout không mở lại, threshold 0,225 giữ nguyên.
6. Gửi lại output cuối `BƯỚC 8A — INFERENCE PREFLIGHT` hoặc `data/outputs/model_deployment/preflight_8a/08a_inference_manifest.json` (không chứa dữ liệu cá thể). Không gửi artifact `.joblib`.
7. Khi kết quả 8A hợp lệ, chúng ta sẽ bắt đầu **8B FastAPI**: bạn tự viết/chạy server từng bước dưới hướng dẫn, chưa mở API công khai.

Giới hạn quan trọng: mô hình nghiên cứu chỉ phân loại dấu hiệu HbA1c ≥5,7% từ tuổi, BMI và mã giới tính trong NHANES; không được dùng để dự đoán nguy cơ mắc type 2 trong tương lai, chẩn đoán hay đưa ra lời khuyên điều trị. Test chỉ đánh giá một lần. Chưa có survey weighting / kiểm định ngoài mẫu / kiểm định lâm sàng.
