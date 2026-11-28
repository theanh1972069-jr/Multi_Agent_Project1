# BƯỚC 1 — LỰA CHỌN DATASET VÀ ĐỊNH NGHĨA BÀI TOÁN

**Đề tài:** Multi-Agent AI System for Diabetes Risk Assessment  
**Giai đoạn:** 3/8 — ML/DL Research | **Bước:** 1/8  
**Ngày:** 2026-10-31  
**Phiên bản:** v0.1 — quyết định sơ bộ; chưa huấn luyện và chưa kết luận tính hiệu quả.  
**Trạng thái thực hiện:** Nghiên cứu nguồn và đặc tả sơ bộ; **chưa tải dữ liệu**, **chưa chạy mã**, **chưa train model**.

## 1. Mục đích và yêu cầu kế thừa

Theo SRS của dự án: xây dựng công cụ **hỗ trợ đánh giá nguy cơ / sàng lọc liên quan tiểu đường**, ưu tiên nghiên cứu vấn đề type 2; dự đoán phải đến từ ML/DL được huấn luyện, không để LLM suy ra nhãn; kết quả phải có phiên bản mô hình, cảnh báo giới hạn và không được trình bày như chẩn đoán y khoa.

**Vấn đề khoa học cần sửa cho rõ:** Hai nguồn dữ liệu dưới đây phần lớn là khảo sát cắt ngang. Vì vậy mô hình đầu tiên là **phân loại dấu hiệu/tình trạng liên quan đến tiểu đường ở thời điểm quan sát**, không phải ước lượng xác suất **phát bệnh type 2 trong tương lai**. Muốn dự đoán incidence trong 5/10 năm cần bộ dữ liệu theo dõi dọc có mốc thời gian và nhãn sự kiện mới mắc.

## 2. Quyết định chọn nguồn dữ liệu

| Dataset | Nhà cung cấp | Thời gian | Quy mô từ tài liệu chính thức | Phù hợp với |
|---|---|---|---|---|
| NHANES | CDC/NCHS | Aug 2021 – Aug 2023 | `DEMO_L` có 11.933 người; `GHB_L` có 6.715 giá trị HbA1c; `GLU_L` có 3.672 giá trị glucose lúc đói. **Đây là số trước khi ghép và lọc** | Mô hình nhãn dựa trên chỉ dấu xét nghiệm |
| BRFSS | CDC | 2025 | **356.158 bản ghi**; bộ dữ liệu tổng hợp 284 biến theo trang CDC | Mô hình nhãn **tiểu đường từng được thông báo** do người tham gia tự khai |
| Pima Indians Diabetes | Dataset baseline từng dùng trong dự án | — | 768 bản ghi chuẩn (tài liệu cũ có chỗ ghi 769, cần đối chiếu file thực tế) | Chỉ dùng làm ví dụ/baseline so sánh, **không làm tập chính** |

**Không ghép hàng NHANES + BRFSS để huấn luyện một mô hình lúc này**, vì khác phương pháp thu thập, miền dữ liệu, nhãn, missingness và sampling weights. Chúng ta sẽ đánh giá hai mô hình riêng biệt. Cũng không so sánh trực tiếp Accuracy như thể cùng một test set.

## 3. Mô hình nghiên cứu A — NHANES (ưu tiên làm trước)

### 3.1. Câu hỏi nghiên cứu sơ bộ

*Có thể dựa trên đặc điểm nhân khẩu và thông tin sức khỏe không dùng xét nghiệm để nhận diện người trưởng thành có **chỉ dấu đường huyết bất thường ở thời điểm khảo sát** theo HbA1c không?*

Đây là nhiệm vụ phân loại trạng thái xét nghiệm, không phải chẩn đoán, cũng không phải dự đoán tiểu đường type 2 trong tương lai.

### 3.2. Định nghĩa nhãn **đề xuất để kiểm tra** (chưa chốt)

- Nghiên cứu ban đầu trên **người trưởng thành** (dự kiến từ 20 tuổi), kiểm tra phạm vi đủ điều kiện ở codebook.
- Để nghiên cứu dấu hiệu **chưa được chẩn đoán**, cân nhắc loại người tự khai đã được bác sĩ thông báo mắc tiểu đường (`DIQ010=1`); loại trường hợp thai kỳ khi có dữ liệu tin cậy và loại/ghi nhận các trường hợp HbA1c không phù hợp để diễn giải.
- Nhãn nhị phân thử nghiệm: `lab_abnormal_hba1c = 1` nếu HbA1c (`LBXGH`) >= 5,7%; `0` nếu < 5,7%. Đây là **quy ước nghiên cứu dựa trên chỉ dấu HbA1c**, không phải chẩn đoán.
- Phương án đánh giá bổ sung: chia ba mức HbA1c (<5,7%; 5,7–6,4%; >=6,5%) hoặc đối chiếu với glucose lúc đói (`LBXGLU`); xem xét khác biệt về số mẫu, nhãn bất nhất và trọng số.
- **Không đưa `LBXGH` vào X khi `LBXGH` tạo y**. Nếu nghiên cứu nhãn kết hợp HbA1c/FPG, không đưa bất kỳ xét nghiệm dùng để tạo nhãn vào X. Dùng thông tin khác để đánh giá khả năng nhận diện trước xét nghiệm.
- Trường hợp người đã được điều trị và HbA1c bình thường không thể tự động được coi là không có bệnh. Các tiêu chí loại trừ hoặc phân tích nhóm riêng cần công bố rõ.

### 3.3. Tệp và đặc trưng ban đầu cần đối chiếu

| Tệp | Vai trò | Ví dụ biến | Ghi chú |
|---|---|---|---|
| `DEMO_L.xpt` | Join / dân số | `SEQN`, `RIDAGEYR`, `RIAGENDR`, `RIDEXPRG`, weights | `SEQN` là khóa nối các tệp |
| `BMX_L.xpt` | Đầu vào | `BMXBMI`, `BMXWAIST` | Kiểm tra đo thiếu |
| `BPXO_L.xpt` | Đầu vào | `BPXOSY1`, `BPXODI1` (có các lần đo khác) | Chốt cách tổng hợp sau khi đọc codebook |
| `PAQ_L.xpt` | Đầu vào | Các biến hoạt động thể lực | Không giả định tất cả đối tượng trả lời |
| `SMQ_L.xpt` | Đầu vào | Tiền sử hút thuốc | Chọn sau khi xem đủ câu hỏi |
| `DIQ_L.xpt` | Loại trừ / đối chiếu | `DIQ010` | Không khẳng định phân biệt type 1 và type 2 |
| `GHB_L.xpt` | Tạo nhãn | `LBXGH`, `WTPH2YR` | Phlebotomy weight |
| `GLU_L.xpt` | Phân tích độ nhạy | `LBXGLU`, `WTSAF2YR` | Fasting subsample, mẫu nhỏ hơn |

> Chọn đúng trọng số và tính đến thiết kế mẫu phức tạp (strata, PSU) khi ước lượng chỉ số tổng thể. Đặc biệt, phân tích có glucose lúc đói phải xem fasting subsample weight; không lấy trọng số của bộ toàn mẫu thay thế tùy tiện. Tách bước ước lượng quần thể khỏi đánh giá dự đoán cá thể và báo cáo rõ phương pháp.

## 4. Mô hình nghiên cứu B — BRFSS (bổ sung, đánh giá riêng)

### 4.1. Câu hỏi nghiên cứu sơ bộ

*Dựa trên thông tin người dùng tự khai, mô hình có nhận diện được nhóm từng được bác sĩ/chuyên gia y tế thông báo mắc tiểu đường (so với nhóm không) không?*

Đây là **nhãn tự khai về chẩn đoán trong quá khứ**; không phải kết quả xét nghiệm, không tự xác định type 2, và không đánh giá trực tiếp khả năng dự báo mới mắc.

### 4.2. Xây dựng nhãn và feature

- Biến trung tâm cần kiểm tra trong codebook 2025: **`DIABETE4`**. Đọc **đầy đủ mã trả lời** (có thể có mang thai/tiền tiểu đường/không biết/từ chối), quy tắc loại trừ và cách xử lý các nhóm trước khi cố định `y`.
- Biến minh họa ứng viên `X`: tuổi (`_AGE80` hoặc `_AGEG5YR`), BMI (`_BMI5`, có tỉ lệ mã hóa), giới (`_SEX`), vận động (`_TOTINDA`), smoking (`_SMOKER3`), sức khỏe chung (`GENHLTH`). Kiểm tra codebook năm 2025 trước khi sử dụng.
- Không dùng `DIABAGE4`, thông tin điều trị tiểu đường hay trường phản ánh trực tiếp tình trạng bệnh làm đặc trưng dự đoán nếu mục tiêu là sàng lọc trước chẩn đoán.
- Biến **`DIABTYPE`** (type 1 / type 2) là nội dung của **module Diabetes tùy chọn** tại một số địa bàn; không mặc định có sẵn và hợp lệ cho toàn bộ 356.158 bản ghi. Không đổi nhãn `DIABETE4` thành 'type 2' nếu chưa có dữ liệu xác nhận.
- Lưu ý trọng số BRFSS (`_LLCPWT` và các biến thiết kế mẫu tương ứng) và dữ liệu thiếu; kiểm tra phạm vi địa lý 2025 (47 tiểu bang + DC, Guam, Puerto Rico; không có đủ dữ liệu một số địa bàn).

## 5. Tiêu chí chọn mô hình và đánh giá về sau (chưa chạy)

- Thiết lập **baseline** như Logistic Regression; sau đó so sánh Random Forest, Gradient Boosting/XGBoost nếu thích hợp. Không mặc định DL tốt hơn ML với dữ liệu bảng.
- Chia train/validation/test trước mọi fitting theo quy trình chống rò rỉ; giữ nguyên test set cuối. Chọn chiến lược phù hợp với thiết kế mẫu và kiểm tra biến trùng/đại diện. `Pipeline` preprocessing chỉ được fit ở train.
- Đánh giá Recall, Precision, F1, ROC-AUC; thêm PR-AUC khi nhãn ít, confusion matrix, hiệu chỉnh xác suất, độ ổn định và fairness theo nhóm dân số. Báo cáo baseline và khoảng tin cậy nếu khả thi.
- Không trình bày output như **xác suất mắc bệnh type 2 trong tương lai** nếu không có nhãn incidence và external validation. Không áp dụng trực tiếp cho dân số Việt Nam nếu chưa kiểm định trên quần thể phù hợp.

## 6. Ảnh hưởng đến thiết kế Giai đoạn 2

- Bản phác thảo cũ nhập 8 feature từ **Pima** không thể sử dụng nguyên xi cho NHANES/BRFSS.
- Cần định nghĩa 2 `model_manifest` riêng: `nhanes-hba1c-screening-research` và `brfss-self-report-diabetes-research` (tên **dự kiến**), mỗi model có `population_scope`, feature names/types/units, label definition, supported_missingness, preprocessing version, scores, calibration status và `model_version`.
- Prediction Agent phải **route theo khả năng nhập dữ liệu của model và phạm vi được đánh giá**, không tự chuyển score của 2 model thành một xác suất duy nhất.
- Form Web/Mobile, OpenAPI, `assessment_features` và `prediction_results` sẽ điều chỉnh sau khi chốt feature set thực tế, không cập nhật trước khi bước Data Understanding và EDA kết thúc.

## 7. Rủi ro và giới hạn

1. Hai nguồn đều chủ yếu **cắt ngang**, không có nhãn bệnh mới mắc trong các năm tiếp theo.
2. BRFSS dựa vào tự khai, chịu sai số ghi nhớ và khác biệt về tiếp cận xét nghiệm/chẩn đoán.
3. NHANES có thiết kế mẫu phức tạp, không phải toàn bộ người tham gia đều có HbA1c/FPG. Hệ thống lọc bệnh đã biết, thai kỳ và missingness có thể làm tập nghiên cứu nhỏ đi đáng kể.
4. Chưa chứng minh áp dụng cho Việt Nam hoặc các nhóm ngoài miền dữ liệu; phải đánh giá ngoại kiểm phù hợp.
5. Chưa được quảng cáo là hệ thống chẩn đoán bệnh, kê đơn hoặc dự báo nguy cơ 5–10 năm.

## 8. Danh sách quyết định cần ghi nhận

| Mã | Quyết định / Vấn đề | Trạng thái |
|---|---|---|
| D-01 | Dùng NHANES 2021–2023 và BRFSS 2025 từ CDC | Đề xuất đã kiểm chứng nguồn |
| D-02 | Huấn luyện **2 model riêng**, không trộn dataset ngay | Đề xuất đã thống nhất trong hội thoại |
| D-03 | NHANES label thử nghiệm: HbA1c >=5,7% ở người chưa từng được chẩn đoán (và điều kiện loại trừ khác) | **Chờ phân tích thực tế** |
| D-04 | BRFSS label: tự khai từng được báo có diabetes, không gắn nhãn type 2 tùy tiện | **Chờ đọc codebook và kiểm tra phân bố** |
| D-05 | Thiết kế bảng feature, population, weights, missingness | **Chờ Bước 2–4** |
| D-06 | Cập nhật hợp đồng API/manifest từ Pima schema sang các model thực | **Chờ hoàn tất training/evaluation** |

## 9. Nguồn gốc tài liệu và liên kết chính thức

### Nguồn nghiên cứu / dữ liệu thực tế

1. CDC/NCHS — NHANES Aug 2021–Aug 2023: <https://wwwn.cdc.gov/nchs/nhanes/ContinuousNhanes/default.aspx?Cycle=2021-2023>
2. CDC/NCHS — NHANES toàn bộ tệp 2021–2023: <https://wwwn.cdc.gov/nchs/nhanes/search/datapage.aspx?Cycle=2021-2023>
3. NHANES DEMO_L (codebook): <https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.htm>
4. NHANES DIQ_L: <https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DIQ_L.htm>
5. NHANES GHB_L: <https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GHB_L.htm>
6. NHANES GLU_L: <https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GLU_L.htm>
7. NHANES weight tutorial: <https://wwwn.cdc.gov/nchs/nhanes/tutorials/weighting.aspx>
8. CDC — BRFSS 2025 data & codebook: <https://www.cdc.gov/brfss/annual_data/annual_2025.html>
9. BRFSS 2025 variable layout: <https://www.cdc.gov/brfss/annual_data/2025/llcp_varlayout_25_onecolumn.html>
10. BRFSS 2025 calculated variables: <https://www.cdc.gov/brfss/annual_data/2025/summary_matrix_25.html>
11. BRFSS 2025 optional modules by category: <https://www.cdc.gov/brfss/questionnaires/modules/category2025.htm>
12. CDC — diabetes A1c test thresholds: <https://www.cdc.gov/diabetes/diabetes-testing/prediabetes-a1c-test.html>
13. NIDDK — Diabetes tests & diagnosis, confirmatory testing and diabetes type distinction: <https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis>

### Nguồn thiết kế nội bộ

- `06-Technical-Design.md` trong bộ tài liệu Giai đoạn 2 (đang dùng schema Pima nháp; cần cập nhật sau nghiên cứu).
- SRS / Problem Statement trong tài liệu gốc 45 trang.

## 10. Điều kiện hoàn tất Bước 1 và chuyển sang Bước 2

**Đã hoàn thành:** Kiểm tra nguồn CDC, phân biệt nhãn, lập kế hoạch sử dụng hai mô hình, xác định rủi ro và danh sách file cần đọc.

**Chưa làm:** tải file `.xpt`/BRFSS data; ghép dữ liệu; đếm nhãn sau lọc; code; huấn luyện; xuất mô hình/metrics; xác nhận label cuối.

**Bước 2 — Data Understanding:** Thông báo trước khi code, hướng dẫn người dùng trực tiếp tải file dữ liệu từ CDC, xem codebook, chạy Python để kiểm tra các cột, `SEQN`, kích thước/giá trị thiếu, nhãn dự kiến. Người dùng gửi kết quả thật; cập nhật `02-Data-Understanding.md` và `09-Experiment-Log.md`.
