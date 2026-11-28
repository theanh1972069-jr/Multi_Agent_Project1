# Hướng dẫn chạy Bước 3 — EDA bằng Jupyter Notebook

1. Dùng lại thư mục `03-ML-Research/` và 4 file XPT trong `data/raw/` của Bước 2.
2. Đưa `03_NHANES_EDA.ipynb` vào `notebooks/`, cùng cấp với notebook Bước 2.
3. Chọn đúng Python kernel `.venv`. Để cài matplotlib (nếu chưa có), dùng Terminal tại thư mục dự án: ` .\.venv\Scripts\python.exe -m pip install matplotlib `. Hoặc trong Jupyter: `%pip install matplotlib` rồi restart kernel.
4. Chạy từng cell theo thứ tự bằng `Shift+Enter` hoặc **Run All** (khi đã kiểm tra đường dẫn và đọc từng phần).
5. Quan sát biểu đồ; nếu `SAVE_FIGURES=True`, notebook lưu hình vào `data/outputs/eda/` **trên máy của bạn**, không phải môi trường ChatGPT.
6. Gửi đoạn output cuối (phần `BƯỚC 3 — NHANES EDA`) và các hình `eda_02_bmi.png`, `eda_03_hba1c.png`, `eda_04_missingness.png` để cùng phân tích.
7. Không huấn luyện trong Bước 3. Tới Bước 4, người hướng dẫn sẽ giải thích rõ dữ liệu nào được xử lý và vì sao trước khi bạn chạy.

**Nếu lỗi:** `ModuleNotFoundError` => cài bằng `%pip`; `FileNotFoundError` => kiểm tra đường dẫn `data/raw`; `TypeError` khi vẽ biểu đồ => gửi nguyên traceback để kiểm tra phiên bản matplotlib.

**Lưu ý phân tích:** Chỉ thống kê mô tả không trọng số. `RIDEXPRG` chỉ có cho phụ nữ 20–44 tuổi và `DIQ160` có skip logic. Đừng thay missing bằng 0 hoặc cho là khỏe mạnh.
