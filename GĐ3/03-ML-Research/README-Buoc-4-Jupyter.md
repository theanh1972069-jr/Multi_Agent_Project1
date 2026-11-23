# Bước 4 – Chạy trong Jupyter Notebook

1. Giải nén ZIP vào **đúng thư mục dự án** `03-ML-Research/`, giữ nguyên `data/raw/` với bốn tệp XPT mà bạn đã tải.
2. Mở Jupyter Notebook từ `03-ML-Research/`; chọn kernel Python đã dùng ở Bước 3.
3. Mở `notebooks/04_NHANES_Data_Preprocessing.ipynb`.
4. Chạy các ô từ trên xuống bằng **Shift+Enter**. Không tự chạy code huấn luyện hoặc tự sửa nhãn để mô hình ra accuracy cao.
5. Chương trình sẽ ghi file vào `data/processed/` và `data/outputs/preprocessing/` trên **máy của bạn**; chúng chưa tồn tại trong ZIP vì bạn chưa chạy code.
6. Gửi phần `===== BƯỚC 4 — NHANES DATA PREPROCESSING =====` và bảng `step4_cohort_summary.csv` để tôi cập nhật tài liệu theo kết quả thật.

**Các ô notebook chưa được thực thi; không có mô hình được train hoặc lưu.**

## Thư mục quan trọng

```text
03-ML-Research/
├── notebooks/04_NHANES_Data_Preprocessing.ipynb
├── 03-NHANES-EDA.md
├── 04-Data-Preprocessing.md
├── 09-Experiment-Log.md
├── assets/                              # ảnh bạn cung cấp ở Bước 3
├── data/raw/                            # giữ nguyên 4 tệp XPT bạn tải từ CDC
├── data/processed/                      # notebook sẽ xuất CSV sau khi chạy
└── data/outputs/preprocessing/          # notebook sẽ xuất bảng QA + JSON
```
