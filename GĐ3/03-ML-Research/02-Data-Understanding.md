# GIAI ĐOẠN 3 — BƯỚC 2: DATA UNDERSTANDING (NHANES)

**Dự án:** Multi-Agent AI System for Diabetes Risk Assessment  
**Ngày chuẩn bị:** 2026-11-01  
**Phiên bản:** v0.1  
**Trạng thái:** **Đã chuẩn bị hướng dẫn và notebook; người dùng CHƯA chạy.** Không có dữ liệu thực nghiệm, train model hay metrics.

## 1. Mục tiêu

- Thiết lập môi trường Python và Jupyter Notebook tại máy người dùng.
- Đọc bốn tệp `DEMO_L`, `BMX_L`, `GHB_L`, `DIQ_L` từ NHANES 2021–2023.
- Kiểm tra số dòng, số cột, `SEQN`, thông tin thiếu, giới hạn độ tuổi của các biến.
- Ghép **left join** qua `SEQN`; thống kê sơ bộ số người trưởng thành (>=20) có HbA1c.
- Ghi kết quả thật sau khi người dùng chạy vào báo cáo dưới đây.

## 2. Nguyên tắc thực hành

**Người dùng thực hiện:** tải và giữ nguyên file `.xpt`, tạo môi trường, mở Jupyter, chạy từng cell, gửi kết quả.  
**Người hướng dẫn:** chỉ đưa hướng dẫn và notebook mẫu, không chạy thay và không huấn luyện mô hình.

Bước 2 **không** tạo nhãn cuối, impute missing, scale, split train/test, fit model hoặc chạy dự đoán.

## 3. Dữ liệu nguồn và trường quan trọng

| Tên tệp | Nội dung | Các trường chính dự kiến | Ghi chú |
|---|---|---|---|
| `DEMO_L.xpt` | Nhân khẩu học | `SEQN`, `RIDAGEYR`, `RIAGENDR`, `RIDEXPRG`, `WTMEC2YR`, `SDMVSTRA`, `SDMVPSU` | `SEQN` dùng để nối bảng; `RIDEXPRG` chỉ có ý nghĩa cho nhóm đủ điều kiện |
| `BMX_L.xpt` | Nhân trắc | `SEQN`, `BMXBMI`, `BMXWAIST` | Có thể thiếu do không được đo |
| `GHB_L.xpt` | HbA1c | `SEQN`, `LBXGH`, `WTPH2YR` | `LBXGH` là chỉ dấu ứng viên cho nhãn; `WTPH2YR` là trọng số xét nghiệm máu |
| `DIQ_L.xpt` | Tiểu đường tự khai | `SEQN`, `DIQ010`, `DIQ160` | Kiểm tra mã trả lời và skip patterns |

**Còn để sau:** `BPXO_L`, `PAQ_L`, `SMQ_L`, `GLU_L` — bổ sung sau khi xác nhận bước đọc/ghép 4 tệp thành công. Khi dùng `GLU_L`, xem trọng số `WTSAF2YR` của mẫu con glucose lúc đói.

## 4. Quy trình thực hành trên Jupyter

1. Tải các `.xpt` từ CDC vào `data/raw/`.
2. Cài và mở Jupyter Notebook bằng môi trường ảo riêng.
3. Mở `notebooks/02_NHANES_Data_Understanding.ipynb`.
4. Chạy các ô **lần lượt từ trên xuống**, không bỏ qua lỗi.
5. Sao chép output ô cuối cho người hướng dẫn.
6. Khi kết quả đã được kiểm tra, cập nhật bảng quan sát bên dưới.

## 5. Kết quả quan sát (điền sau khi người dùng chạy)

| Trường cần ghi | Kết quả | Trạng thái |
|---|---|---|
| Python / Pandas version | Chưa có | Chưa thực hiện |
| `DEMO_L`: dòng × cột | Chưa có | Chưa thực hiện |
| `BMX_L`: dòng × cột | Chưa có | Chưa thực hiện |
| `GHB_L`: dòng × cột | Chưa có | Chưa thực hiện |
| `DIQ_L`: dòng × cột | Chưa có | Chưa thực hiện |
| Bản ghi trùng/thiếu `SEQN` | Chưa có | Chưa thực hiện |
| Kích thước sau left join | Chưa có | Chưa thực hiện |
| Số người >=20 tuổi | Chưa có | Chưa thực hiện |
| Số người >=20 có `LBXGH` | Chưa có | Chưa thực hiện |
| Tỷ lệ thiếu các biến chính | Chưa có | Chưa thực hiện |
| Lỗi phát sinh và cách sửa | Chưa có | Chưa thực hiện |

## 6. Ghi chú về dữ liệu / phương pháp

- NHANES là khảo sát **cắt ngang**, không phải theo dõi bệnh mới mắc nhiều năm.
- `LBXGH` là kết quả HbA1c. Nếu dùng để định nghĩa nhãn trong bước sau, không đưa chính `LBXGH` vào đầu vào mô hình.
- Không đồng nhất người `DIQ010` trả lời 'không' với người chắc chắn không có tiểu đường; cần đọc codebook trước khi lọc.
- Không lấy `NaN` của `RIDEXPRG` làm kết luận không mang thai; biến chỉ hỏi cho nhóm đủ điều kiện.
- Khi phân tích ước lượng đại diện quần thể, áp dụng trọng số NHANES và thiết kế mẫu phù hợp; mô hình ML và đánh giá cá thể cần mô tả riêng phương pháp.
- Không sử dụng `SEQN`, trọng số khảo sát, hoặc thông tin sinh ra từ nhãn như những yếu tố dự đoán mặc định.

## 7. Tiêu chí hoàn tất

- [ ] 4 tệp `.xpt` gốc được tải về máy.
- [ ] Notebook chạy thành công trên máy của người dùng.
- [ ] `SEQN` mỗi bảng không bị trùng và merge không làm tăng/giảm số dòng từ bảng gốc DEMO.
- [ ] Ghi nhận số người trưởng thành có HbA1c và missingness thực tế.
- [ ] Kết quả gửi người hướng dẫn và kiểm tra trước khi bắt đầu EDA.

## 8. Tham khảo CDC (codebook và hướng dẫn chính thức)

- NHANES cycle: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023
- DEMO_L: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.htm
- BMX_L: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BMX_L.htm
- GHB_L: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GHB_L.htm
- DIQ_L: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DIQ_L.htm
- GLU_L: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GLU_L.htm
- NHANES sample weights: https://wwwn.cdc.gov/nchs/nhanes/tutorials/weighting.aspx

## 9. Tài nguyên kèm theo

- `notebooks/02_NHANES_Data_Understanding.ipynb`: notebook tương tác, **chưa chạy**.
- `requirements-notebook.txt`: thư viện môi trường.
- `README-Buoc-2-Jupyter.md`: hướng dẫn trên Windows.
- `09-Experiment-Log.md`: nhật ký quyết định (không có kết quả giả).
