# Hướng dẫn Bước 2 — Jupyter Notebook trên Windows

**Mục tiêu:** Đọc/kiểm tra NHANES tại máy của bạn. **Chưa train.**

## A. Cấu trúc thư mục (giải nén ZIP)

```text
03-ML-Research/
├── notebooks/
│   └── 02_NHANES_Data_Understanding.ipynb
├── data/
│   └── raw/
│       ├── DEMO_L.xpt      ← tải từ CDC
│       ├── BMX_L.xpt       ← tải từ CDC
│       ├── GHB_L.xpt       ← tải từ CDC
│       └── DIQ_L.xpt       ← tải từ CDC
├── requirements-notebook.txt
├── README-Buoc-2-Jupyter.md
├── 01-Dataset-Selection.md
├── 02-Data-Understanding.md
└── 09-Experiment-Log.md
```

4 file `.xpt` **không được đính kèm trong ZIP**; bạn tự tải file chính thức từ CDC. Xem link ngay trong notebook.

## B. Tạo môi trường ảo

Mở PowerShell hoặc terminal VS Code, `cd` vào thư mục **`03-ML-Research`** đã giải nén.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-notebook.txt
```

Cách gọi trực tiếp `.venv\Scripts\python.exe` **không cần kích hoạt PowerShell** nên tránh lỗi `ExecutionPolicy`.

## C. Khởi động Jupyter Notebook

```powershell
.\.venv\Scripts\python.exe -m notebook
```

Trình duyệt mở lên (hoặc nhấp liên kết `http://localhost:...` mà Jupyter in ra). Trong Jupyter, mở thư mục `notebooks`, chọn `02_NHANES_Data_Understanding.ipynb`.

Nếu sử dụng VS Code: cài hai extension **Python** và **Jupyter**, mở file notebook, chọn `Select Kernel` → môi trường `.venv` đã cài.

## D. Tải dữ liệu

Mở trang danh sách CDC, tìm tên tệp và bấm **Data [XPT]** (cột **Data File**):

- Demographics: https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Demographics&Cycle=2021-2023
- Examination: https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Examination&Cycle=2021-2023
- Laboratory: https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Laboratory&Cycle=2021-2023
- Questionnaire: https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Component=Questionnaire&Cycle=2021-2023

Trang **Doc** dưới đây là codebook để đối chiếu các biến:

- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.htm
- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BMX_L.htm
- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GHB_L.htm
- https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DIQ_L.htm

Lưu file vào **`data/raw/`** (giữ đúng tên, `.xpt` hoặc `.XPT`). Không đổi thành `.csv`.

## E. Chạy từng ô và kiểm tra

1. Kiểm tra kernel và đường dẫn data.
2. Kiểm tra 4 file; nếu `FileNotFoundError`, sửa đường dẫn/file, không bỏ qua.
3. Đọc bằng `pd.read_sas(..., format='xport')`.
4. Kiểm tra `SEQN` có trùng/thiếu hay không.
5. Left join 4 file theo `SEQN` và đếm người trưởng thành có HbA1c.
6. Gửi output cuối cho người hướng dẫn; chưa chạy các bước train.

**Lưu ý:** Nếu `Path.cwd()` của bạn không phải thư mục gốc hay `notebooks/`, chỉnh `PROJECT_ROOT` ở ô 1 thành đường dẫn dự án trên máy (ví dụ `Path(r'D:\Projects\Diabetes\03-ML-Research')`).

## F. Ghi chép

Chỉ ghi các số liệu sau khi bạn đã chạy thật vào `02-Data-Understanding.md`. Không coi con số ghi trên codebook là số liệu ghép/lọc thực tế. Khi đủ kết quả, cập nhật `09-Experiment-Log.md`.
