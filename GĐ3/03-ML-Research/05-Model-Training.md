# GIAI ĐOẠN 3 — BƯỚC 5: MODEL TRAINING (BASELINE NHANES)

**Trạng thái:** Đã soạn quy trình và notebook; **người dùng chưa train**, chưa có mô hình hoặc metrics thực tế.  
**Notebook:** `notebooks/05_NHANES_Model_Training.ipynb`.  
**Nguồn dữ liệu:** NHANES August 2021–August 2023, subset do chính người dùng chuẩn bị ở Bước 4.

## 1. Quyết định kỹ thuật dựa trên kết quả Bước 4

| Thành phần | Quyết định baseline | Lưu ý |
|---|---|---|
| Cohort | `screening_candidate`, 4.698 người | Trả lời DIQ010=2, loại mã thai kỳ xác định RIDEXPRG=1; 3.724 tình trạng mang thai không công bố vẫn còn |
| Nhãn | `a1c_ge_57_candidate`, 1.387 nhãn 1 và 3.311 nhãn 0 | Chỉ dấu **HbA1c ≥ 5,7%**, không phải xác nhận type 2 hay nguy cơ mắc bệnh tương lai |
| Features | `RIDAGEYR`, `RIAGENDR`, `BMXBMI` | Baseline tối giản; không nhét `LBXGH`, `DIQ010`, `DIQ160`, `SEQN`, `RIDEXPRG`, survey weights vào X |
| Missing BMI | 57/4.698 (1,21%) | Median imputation trong pipeline chỉ fit trên training |
| Outliers | 45 BMI được gắn cờ ở Bước 4 | Không tự loại/clipping dựa trên phân vị toàn dữ liệu |
| Split | Train / validation / test = 70% / 15% / 15% (stratified), seed 42 | Không dùng test để chọn model hoặc threshold |
| Models | DummyClassifier, LogisticRegression, RandomForestClassifier | So sánh validation ROC-AUC và các chỉ số khác; chưa kết luận mô hình nào tốt hơn |
| Data weighting | Chưa áp dụng khi train baseline | Chưa đại diện cho quần thể; sau này cần phân tích WTPH2YR và thiết kế mẫu SDMVSTRA/SDMVPSU |

## 2. Thứ tự chạy notebook — do người dùng tự thực hiện

1. Đọc `data/processed/nhanes_step4_screening_candidate_REVIEW_ONLY.csv` (được xuất từ Bước 4), xác nhận tên cột, số mẫu, phân bố nhãn, mã SEQN không trùng.
2. Chỉ định X từ đúng ba đặc trưng; y từ nhãn `a1c_ge_57_candidate`. KHÔNG đưa mã SEQN vào X.
3. Tách holdout test 15% bằng `train_test_split(..., stratify=y, random_state=42)`; từ 85% còn lại tách validation theo tỷ lệ 15/85.
4. Xây `ColumnTransformer` kết hợp `SimpleImputer`, `StandardScaler` và `OneHotEncoder` nằm **bên trong** `Pipeline`.
5. **DỪNG VÀ ĐỌC CẢNH BÁO TRƯỚC CELL FIT**. Sau đó bạn tự chạy ba model baseline.
6. Tính metric **trên validation**, chọn model theo ROC-AUC làm tiêu chí nghiên cứu ban đầu; xem thêm recall, precision, F1, PR-AUC, Brier score và ma trận nhầm lẫn.
7. Lưu model baseline thắng validation cùng metadata, split files (bao gồm test holdout **chưa được đánh giá**) và báo cáo validation JSON/CSV. Không chạy metrics test.
8. Gửi toàn bộ output cuối cho ChatGPT để phân tích và ghi log.

## 3. Yêu cầu kiểm soát chất lượng

- Không train trên toàn tập, không dùng leakage, không kiểm định trên test trong Bước 5.
- Mọi bước fit của imputer/scaler/encoder **nằm trong pipeline** và chỉ học từ training set.
- Không dùng NHANES cross-sectional để nói kết quả là nguy cơ phát bệnh trong tương lai.
- Không dùng mô hình này để chẩn đoán hoặc quyết định điều trị.
- `RIDAGEYR=80` đại diện **80 tuổi trở lên**, không phải chính xác 80.
- `RIDEXPRG` công bố có giới hạn: chỉ loại mã thai kỳ có chứng cứ; phân tích độ nhạy theo nhóm và các mẫu thiếu vẫn cần làm.
- Vì cohort được chọn từ nhóm có HbA1c, kết quả chưa có trọng số và chưa xác thực ngoài quần thể NHANES, metrics không chứng minh tính hữu dụng lâm sàng.
- Cần xem bias theo nhóm tuổi / giới tính và calibration trước khi cân nhắc triển khai.

## 4. Cần người dùng gửi lại để hoàn tất Bước 5

- Summary train/validation/test (số bản ghi; **không chia sẻ dữ liệu cá nhân**).
- Bảng metrics validation của 3 mô hình; confusion matrix validation.
- Baseline được chọn, đường dẫn artifact, phiên bản `scikit-learn`.
- Các lỗi và thời gian train nếu có. **Chỉ ghi các số liệu thực tế**, không tạo số giả.

## 5. Nguồn chính thức

- CDC GHB_L: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/GHB_L.htm
- CDC DEMO_L: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.htm
- CDC DIQ_L: https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DIQ_L.htm
- NIDDK A1C: https://www.niddk.nih.gov/health-information/diagnostic-tests/a1c-test
- Scikit-learn: https://scikit-learn.org/stable/common_pitfalls.html
