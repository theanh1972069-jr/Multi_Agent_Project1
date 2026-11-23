# GIAI ĐOẠN 3 — BƯỚC 6: MODEL EVALUATION

**Trạng thái:** Bước 6A đã chuẩn bị notebook **chưa chạy**. Bước 6B (Final Holdout Test) chưa thực hiện. Người dùng tự chạy và gửi kết quả; không tự tạo metric.

## 1. Cơ sở thực nghiệm từ Bước 5

- Dữ liệu: `screening_candidate` NHANES 2021–2023, n=4.698; 1.387 nhãn 1 (`LBXGH >= 5.7`), 3.311 nhãn 0.
- Train/Validation/Test: 3.288 / 705 / 705, chia phân tầng seed 42.
- Features: `RIDAGEYR`, `RIAGENDR`, `BMXBMI`; mục tiêu **dấu hiệu HbA1c >= 5.7%**, KHÔNG phải type 2 được xác nhận hoặc nguy cơ mắc bệnh tương lai.
- Model chọn tạm thời theo ROC-AUC Validation cao nhất: `LogisticRegression`, model artifact trên máy của người dùng: `models/baseline/nhanes_hba1c_baseline_step5.joblib`.
- Validation Logistic ở threshold 0,5: ROC-AUC=0,7173; Average Precision (AP)=0,4415; Precision=0,4416; Recall=0,1635; F1=0,2386; Accuracy=0,6922; Brier=0,1868; TN/FP/FN/TP=454/43/174/34.
- Validation RandomForest: ROC-AUC=0,7128, AP=0,4516, Recall=0,2067, F1=0,2905, Brier=0,1854. Chưa kết luận Logistic là tối ưu.

## 2. Chẩn đoán vấn đề

- 174/208 dương tính thực tế bị Logistic bỏ sót trên validation, tương ứng 83,65% tại threshold=0,5.
- Dummy đạt Accuracy 0,7050 nhưng Recall 0; do vậy Accuracy đơn lẻ không đủ.
- Ngưỡng 0,5 không phải ngưỡng y khoa mặc định, cần xem trade-off Precision, Recall, False Negative và False Positive.
- `pr_auc_val` trong Bước 5 dùng `average_precision_score`: báo cáo đúng là **Average Precision (AP)**, không đồng nhất với AUC hình thang của PR curve.

## 3. Bước 6A — Validation-only (người dùng tự chạy)

**Notebook:** `notebooks/06A_NHANES_Model_Evaluation_Validation.ipynb`.

| Nhiệm vụ | Nội dung | Output |
|---|---|---|
| Tái hiện baseline | Load model `.joblib` đã train; xác nhận số mẫu và confusion matrix | Bảng metrics validation |
| ROC / PR | Plot ROC và Precision–Recall, so sánh prevalence | `06a_roc_curve.png`, `06a_precision_recall_curve.png` |
| Thử ngưỡng | Dùng Validation với threshold 0,10–0,60, bước 0,025; in Precision, Recall, Specificity, F1, F2, FP, FN | `06a_validation_thresholds.csv`, `06a_threshold_tradeoff.png` |
| Calibration | Reliability diagram 6 bins, score distribution | `06a_reliability_diagram.png`, `06a_score_distribution.png` |
| Phân tích nhóm | Theo nhóm tuổi, mã giới tính trong NHANES | `06a_validation_subgroups.csv` |
| Tổng kết | Đánh dấu threshold chưa chốt, test chưa mở | `06a_validation_summary.json` |

**Quy tắc:** KHÔNG `.fit()`, không train lại, KHÔNG đọc test, KHÔNG tự tối ưu threshold theo Test. Ngưỡng Recall ≥ 0,70 trong danh sách thử chỉ là **mục tiêu kỹ thuật minh họa**, không phải chuẩn lâm sàng.

## 4. Bước 6B — Test holdout (chưa làm)

Chỉ thực hiện khi đã (1) xem hết kết quả 6A, (2) **chốt trước** model và decision threshold, (3) thống nhất quy tắc lựa chọn và hạn chế. Sau đó mới đánh giá tập Test **một lần** để báo cáo khả năng tổng quát hóa nội bộ. Nếu kết quả Test không tốt, không được dùng chính Test để điều chỉnh model rồi báo nó như holdout độc lập.

## 5. Giới hạn khoa học cần ghi trong báo cáo

1. Dữ liệu NHANES cắt ngang; đầu ra chỉ phản ánh phân loại dấu hiệu HbA1c tại thời điểm quan sát.
2. Baseline chưa có trọng số khảo sát, chưa mô hình hóa cụm/tầng mẫu: **không suy rộng** metrics thành hiệu năng đại diện dân số Mỹ. Xem tài liệu CDC về survey design.
3. Còn bất định mang thai do hạn chế công bố biến RIDEXPRG. Chưa có đánh giá xác thực ngoài dân số NHANES / người Việt Nam.
4. Không sử dụng làm chẩn đoán, kê thuốc hay công cụ quyết định lâm sàng.
5. Độ lệch Brier thấp không tự động chứng minh calibration tốt; phải xem reliability diagram.

## 6. Điền kết quả sau khi người dùng chạy (để trống)

- [ ] Xác minh metrics Validation tái hiện.
- [ ] Đính kèm đồ thị ROC / PR và calibration.
- [ ] Tổng hợp bảng threshold; nhận xét trade-off FN/FP.
- [ ] So sánh nhóm tuổi / mã giới tính ở mức mô tả.
- [ ] Chốt model, threshold và quy tắc chọn trước khi dùng Test.
- [ ] Final Test holdout ở Bước 6B.
- [ ] External validation và phân tích NHANES survey weights (nghiên cứu sau).

## 7. Tài liệu tham khảo

- scikit-learn threshold tuning: https://scikit-learn.org/stable/auto_examples/model_selection/plot_tuned_decision_threshold.html
- scikit-learn model evaluation / AP: https://scikit-learn.org/stable/modules/model_evaluation.html
- scikit-learn calibration: https://scikit-learn.org/stable/modules/calibration.html
- CDC NHANES sample design: https://wwwn.cdc.gov/nchs/nhanes/tutorials/SampleDesign.aspx
- CDC NHANES weighting: https://wwwn.cdc.gov/nchs/nhanes/tutorials/weighting.aspx
