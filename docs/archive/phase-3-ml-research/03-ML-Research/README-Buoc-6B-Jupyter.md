# HƯỚNG DẪN BƯỚC 6B — FINAL TEST HOLDOUT

**Chưa thực thi. Người dùng tự chạy; KHÔNG train lại.**

## 1. Chuẩn bị

1. Giữ nguyên mô hình và các tệp đã tạo trong Bước 5 và 6A trên máy.
2. Giải nén file ZIP, sao chép `06B_NHANES_Final_Test_Holdout.ipynb` vào thư mục `notebooks/` của `03-ML-Research`. Sao chép `06b_locked_evaluation_plan.json` vào thư mục gốc `03-ML-Research/`.
3. Dùng lại kernel Python 3.13.9, scikit-learn 1.8.0 và môi trường Bước 5/6A; không cài lại model bằng cách train.

## 2. Quyết định cố định (phải đọc trước Test)

- Model: LogisticRegression đã lưu ở `models/baseline/nhanes_hba1c_baseline_step5.joblib`.
- Threshold: **0,225** (chọn trên Validation, mục tiêu thử nghiệm Recall >=80%, không phải chuẩn y tế).
- Features: tuổi, mã giới tính khảo sát, BMI.
- Target: nhãn HbA1c >=5,7%, không phải chẩn đoán, không phải nguy cơ mắc bệnh về sau.
- Nếu Test không tốt: ghi nhận giới hạn, không thay ngưỡng hoặc train lại để đo lại trên chính Test.

## 3. Chạy

Chạy hai ô preflight **không đọc Test**, xác nhận model + file + Validation khớp; đọc kỹ cảnh báo rồi mới chạy ô `FINAL TEST`. Ô này chỉ gọi `.predict_proba()` (không `.fit()`).

## 4. Đầu ra

`data/outputs/model_evaluation/test_6b_FINAL/06b_test_final_results.json`. Không gửi tập Test ở dạng cá thể. Gửi output cuối cho tôi để giúp phân tích, điền tài liệu và quyết định Giai đoạn 3 tiếp theo.

## 5. Cảnh báo khoa học

Phép kiểm tra Test là nội bộ một chu kỳ NHANES, chưa dùng trọng số khảo sát/thiết kế cụm/tầng, chưa đủ xác thực y khoa, chưa kiểm định ngoài dữ liệu. Nghiên cứu chỉ hướng đến chỉ dấu HbA1c, không chẩn đoán type 2.
