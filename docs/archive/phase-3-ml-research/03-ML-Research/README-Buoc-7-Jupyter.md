# Hướng dẫn Bước 7 — Explainability trên Jupyter Notebook

1. Giữ nguyên `models/baseline/nhanes_hba1c_baseline_step5.joblib`, `data/outputs/model_training/validation.csv`, `step5_metadata.json` trên máy bạn.
2. Giải nén ZIP vào thư mục `03-ML-Research`. Không ghi đè file model hoặc dataset.
3. Mở `notebooks/07_NHANES_Model_Explainability.ipynb` bằng cùng kernel của Bước 5–6 (Python 3.13.9, scikit-learn 1.8.0).
4. Chạy từng ô từ trên xuống. **Không có `.fit()`, không đọc Test, không cần train lại.** Notebook có thể nạp `.joblib` (chỉ dùng model bạn tự tạo), rồi áp dụng lên Validation.
5. Nếu SHA256 khác `31e9c94b0f14369be7920b9315b026d0c4afedb9f7b2885d120d631d930582b1`, notebook sẽ dừng. Không sửa hash để ép chạy; liên hệ kiểm tra đường dẫn.
6. Xuất kết quả vào `data/outputs/model_explainability/validation_7/`. Gửi output cuối `BƯỚC 7 — NHANES MODEL EXPLAINABILITY`, ảnh coefficients và permutation importance.

**Chú ý nghiên cứu:** Test holdout đã mở một lần ở Bước 6B. Bước 7 là giải thích sau đánh giá, không sử dụng để đổi feature, mô hình hoặc ngưỡng rồi kiểm lại cùng Test. NHANES chưa trọng số khảo sát; nhãn HbA1c ≥5,7%, không phải chẩn đoán/forecast type 2.
