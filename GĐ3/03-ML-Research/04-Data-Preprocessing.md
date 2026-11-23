# GIAI ĐOẠN 3 – BƯỚC 4: DATA CLEANING & PREPROCESSING

**Dự án:** Multi-Agent AI System for Diabetes Risk Assessment  
**Trạng thái:** Notebook đã biên soạn, **chờ người dùng tự chạy trên NHANES**. Chưa train.  
**File thực hành:** `notebooks/04_NHANES_Data_Preprocessing.ipynb`.

## 1. Mục tiêu

1. Đọc lại và nối bốn file XPT theo `SEQN`, lọc người từ 20 tuổi trở lên.
2. Kiểm tra nhãn HbA1c có sẵn và phân loại ba khoảng `<5.7`, `[5.7,6.5)`, `>=6.5` **chỉ để mô tả tình trạng xét nghiệm**.
3. So sánh các quần thể: tất cả người có HbA1c; người trả lời chưa từng được bác sĩ thông báo mắc tiểu đường (`DIQ010=2`); tập sàng lọc không có tiền sử được khai + loại mã có ghi nhận mang thai hiện tại (`RIDEXPRG=1`). **Không tự diễn giải `RIDEXPRG=NaN` là không mang thai**.
4. Đề xuất tạm thời target `a1c_ge_57_candidate = 1` khi `LBXGH >= 5.7%`, còn lại `0`. Không khẳng định type 2, không xác nhận chẩn đoán, không dự báo biến cố tương lai.
5. Chuẩn bị **đặc trưng cơ bản đề xuất** `RIDAGEYR`, `RIAGENDR`, `BMXBMI`. Không sử dụng `LBXGH`, `DIQ010`, `DIQ160`, `SEQN`, `WTPH2YR`, `RIDEXPRG`, `SDMVSTRA`, `SDMVPSU` làm predictor; có thể giữ metadata riêng để đối chiếu/khi đánh giá survey.
6. Kiểm tra thiếu BMI trong các cohort. Chưa điền giá trị thiếu hoặc loại outlier tự động; chỉ cắm cờ review theo ngưỡng bách phân vị (dùng thống kê EDA, không dùng làm quy tắc hậu xử lý học từ toàn bộ dataset cho huấn luyện).
7. Xuất các bảng và tổng kết theo yêu cầu, **chưa tách train/test, chưa gọi fit/transform, chưa huấn luyện**.

## 2. Đầu vào và kết quả EDA có thật

- NHANES Aug 2021–Aug 2023: `DEMO_L.xpt`, `BMX_L.xpt`, `GHB_L.xpt`, `DIQ_L.xpt` ở `data/raw/`.
- Người >=20: **7.809**; có HbA1c **5.767**; có BMI **5.970**; có cả BMI + HbA1c **5.686**; thiếu BMI trong nhóm đã có HbA1c **81**.
- HbA1c có trung vị **5,5%**, khoảng **3,2–17,1%**. BMI trung vị **28,5**, khoảng **11,1–74,8**.
- Cỡ mẫu cụ thể sau lọc `DIQ010=2` và phân bố nhãn **chưa biết**, chỉ ghi sau khi người dùng chạy notebook.

## 3. Tập dữ liệu dự kiến và quyết định chưa chốt

| Tập dữ liệu | Điều kiện | Mục tiêu |
|---|---|---|
| `all_measured` | `RIDAGEYR >= 20` và `LBXGH` có giá trị | Kiểm tra đầy đủ nhóm xét nghiệm (bao gồm đã biết tiểu đường) |
| `self_report_no_diabetes` | `all_measured` và `DIQ010 == 2` | Nghiên cứu chỉ dấu HbA1c tăng ở người **tự khai chưa từng được bác sĩ chẩn đoán** |
| `screening_candidate` | `self_report_no_diabetes` và `RIDEXPRG != 1` | Tập tham khảo không gồm ca **ghi nhận rõ** đang mang thai; không tự coi người NaN là không mang thai |

**Cần rà soát trước Bước 5:** nên dùng tập nào làm train/evaluation? Bộ dự đoán chỉ dấu HbA1c không thể tự nhận là dự đoán type 2 trong tương lai. Lựa chọn tập chính và cách xử lý BMI thiếu sẽ được quyết định sau khi biết phân bố nhãn/cỡ mẫu.

## 4. Quy tắc kỹ thuật quan trọng

- **Không impute nhãn HbA1c:** quan sát không có `LBXGH` không thể tạo nhãn đo được. Chỉ tính nhãn cho người có xét nghiệm.
- **Không target leakage:** các predictor không chứa HbA1c, câu hỏi chẩn đoán hay bất cứ cách mã hóa trực tiếp kết quả nhãn.
- **Không fit preprocessing trên toàn bộ dataset:** nếu chọn điền khuyết BMI, scale hay encoding thì phải tách dữ liệu trước, fit trên train, áp dụng cho validation/test bằng cùng pipeline ở Bước 5.
- `DIQ160` có skip logic, không được tự điền `No`; `RIDEXPRG` chỉ được công bố cho phụ nữ 20–44; `RIDAGEYR=80` đại diện 80 trở lên.
- Trọng số `WTPH2YR` không là predictor và cần cân nhắc cho phân tích đại diện quần thể; sử dụng thêm biến thiết kế khảo sát khi cần ước lượng chuẩn có sai số.
- `DIQ010=2` không xác nhận không mắc tiểu đường; đó chỉ là trả lời về tiền sử **được thông báo**.
- Chưa tự khẳng định các giá trị cực đoan là lỗi; không áp dụng quy tắc cắt ngoại lệ theo percentile trên toàn bộ dữ liệu cho train/test.

## 5. Đầu ra từ notebook (sẽ được người dùng tạo trên máy)

- `data/processed/nhanes_step4_all_measured_REVIEW_ONLY.csv`
- `data/processed/nhanes_step4_screening_candidate_REVIEW_ONLY.csv`
- `data/outputs/preprocessing/step4_cohort_summary.csv`
- `data/outputs/preprocessing/step4_feature_missing.csv`
- `data/outputs/preprocessing/step4_summary.json`

`*_REVIEW_ONLY.csv` chỉ là **dữ liệu ứng viên**, chưa phải bộ train và chưa được dùng làm kết quả dự đoán. `SEQN` chỉ là mã đối chiếu, không được đưa vào bộ đặc trưng khi huấn luyện.

## 6. Bảng ghi kết quả thực nghiệm (đợi người dùng gửi)

| Chỉ số | Kết quả người dùng chạy |
|---|---|
| `all_measured` n | Chờ chạy (tham chiếu từ Bước 3: 5.767) |
| `self_report_no_diabetes` n | Chưa chạy |
| `screening_candidate` n | Chưa chạy |
| Dương tính/âm tính nhãn HbA1c >=5.7 trong mỗi cohort | Chưa chạy |
| Tỷ lệ BMI thiếu ở screening candidate | Chưa chạy |
| Trường hợp mang thai có mã 1 và bị loại khỏi candidate | Chưa chạy |
| Tệp CSV / JSON đã xuất | Chưa có trên máy người dùng |
| Quyết định xử lý missing và cohort chính | Chưa chốt |

## 7. Tiêu chí hoàn thành

- [ ] Bạn chạy notebook tới ô tổng hợp cuối.
- [ ] Kiểm tra số dòng mỗi cohort, nhãn và missingness sau lọc.
- [ ] Không xóa ngoại lệ hay điền BMI tùy tiện; ghi rõ các giá trị cần review.
- [ ] Xác định ranh giới không dùng label leakage và metadata.
- [ ] Gửi kết quả ô cuối + `step4_cohort_summary.csv` cho tôi để phân tích.
- [ ] Cập nhật `09-Experiment-Log.md`, thống nhất lựa chọn train cohort và kế hoạch split cho Bước 5.

## 8. Nguồn tham khảo

- CDC DEMO_L: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.htm
- CDC GHB_L: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GHB_L.htm
- CDC DIQ_L: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DIQ_L.htm
- NIDDK A1C: https://www.niddk.nih.gov/health-information/diagnostic-tests/a1c-test
