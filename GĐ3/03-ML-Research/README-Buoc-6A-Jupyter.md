# HƯỚNG DẪN CHẠY BƯỚC 6A — VALIDATION EVALUATION (JUPYTER)

**Chưa train ở bước này.** Notebook chỉ nạp model do bạn tự train Bước 5. Không mở file Test.

## 1. Giữ nguyên file Bước 5

```
03-ML-Research/
├── notebooks/
│   └── 06A_NHANES_Model_Evaluation_Validation.ipynb
├── models/baseline/nhanes_hba1c_baseline_step5.joblib   # trên máy bạn
└── data/outputs/model_training/
    ├── validation.csv
    ├── step5_metadata.json
    └── step5_validation_metrics.csv
```

Các file model/dữ liệu do bạn tự tạo đã có trên máy. Bộ tài liệu tải về chỉ cung cấp notebook / hướng dẫn / Markdown, **không đính kèm model**.

## 2. Mở Jupyter

Trong thư mục `03-ML-Research` đang dùng, chạy kernel Python 3.13.9 của Bước 5, vào `notebooks/06A_NHANES_Model_Evaluation_Validation.ipynb`. Chạy từ trên xuống bằng `Shift+Enter`. **Không cần chạy lại notebook Bước 5 hay `.fit()` lại model.**

Nếu lỗi do thiếu thư viện, tạo ô riêng:

```python
%pip install pandas numpy matplotlib scikit-learn joblib
```

Sau đó restart kernel. Lưu ý phải dùng sklearn tương thích với phiên bản đã lưu trong `step5_metadata.json` (ảnh Bước 5 là 1.8.0).

## 3. Kết quả cần gửi lại

- Output cuối `BƯỚC 6A — VALIDATION EVALUATION`.
- `data/outputs/model_evaluation/validation_6a/06a_validation_thresholds.csv`.
- `06a_threshold_tradeoff.png` và `06a_reliability_diagram.png`.
- Nếu có cảnh báo/error, gửi nguyên thông báo lỗi và ô đang chạy.

**KHÔNG** gửi file Test hoặc bản ghi sức khỏe cá thể. Sau khi phân tích kết quả này, chúng ta cùng quyết định threshold rồi **mới** đánh giá Test holdout ở Bước 6B.
