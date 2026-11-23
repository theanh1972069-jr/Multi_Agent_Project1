# GIAI ĐOẠN 3 — BƯỚC 8: MODEL DEPLOYMENT (THIẾT KẾ & THỰC HÀNH)

**Trạng thái:** Bước 8A đã chuẩn bị, **đang chờ người dùng tự chạy Jupyter**. Bước 8B/8C chưa thực hiện.

## 1. Mục tiêu

- **8A:** Nạp mô hình `.joblib` **đã huấn luyện ở Bước 5** trong môi trường có cùng phiên bản thư viện; kiểm tra SHA256/metadata/schema; dự đoán thử **dữ liệu giả lập** và xuất manifest của artifact. Không train, không thay threshold, không đọc lại Test.
- **8B:** Sau khi nhận kết quả 8A, người dùng **tự xây dựng và chạy** FastAPI inference endpoint với Pydantic request/response và test cục bộ. Chưa triển khai công khai.
- **8C:** Tích hợp Prediction Agent (LangGraph) để chỉ gọi endpoint nội bộ có kiểm soát, có timeout, logging an toàn và giới hạn quyền.

## 2. Model đã chốt — KHÔNG được sửa

| Thuộc tính | Giá trị |
|---|---|
| File do người dùng tạo | `models/baseline/nhanes_hba1c_baseline_step5.joblib` |
| SHA256 | `31e9c94b0f14369be7920b9315b026d0c4afedb9f7b2885d120d631d930582b1` |
| Thuật toán | LogisticRegression qua scikit-learn Pipeline |
| Input theo thứ tự | `RIDAGEYR`, `RIAGENDR`, `BMXBMI` |
| Nhãn 1 | HbA1c >= 5,7% tại thời điểm khảo sát, không phải chẩn đoán type 2 |
| Ngưỡng quyết định | 0,225 (đã chốt trên Validation trước Test) |
| Test holdout (đã thực hiện đúng 1 lần) | N=705, Recall=0,8413, Precision=0,4070, Specificity=0,4869, ROC-AUC=0,7406 |
| Hạn chế | Chưa có survey weighting / external / clinical validation; hiệu quả phân nhóm cần nghiên cứu thêm |

## 3. Input contract (chỉ dùng trong mô hình nghiên cứu)

Input JSON dùng **tên trường gốc** để bảo đảm pipeline nhận đúng schema:

```json
{
  "RIDAGEYR": 45,
  "RIAGENDR": 1,
  "BMXBMI": 28.5
}
```

- `RIDAGEYR`: giá trị nguyên 20..80 theo dữ liệu NHANES; **80 là mã gộp tuổi 80 trở lên**, không phải một tuổi chính xác 80.
- `RIAGENDR`: đúng mã phân loại khảo sát `1` hoặc `2`, không chuyển sang true/false hoặc chuỗi tự do.
- `BMXBMI`: số thực hữu hạn. Bước 8A dùng khoảng kiểm tra nghiên cứu **11,1 đến 74,8 kg/m²** dựa trên phạm vi quan sát có báo cáo trong Bước 4; không phải quy tắc an toàn lâm sàng.
- **Không nhận thông tin nhận dạng, SEQN, glucose, HbA1c hoặc tiền sử từ input dự đoán baseline.**
- Nếu thiếu một đặc trưng hoặc vượt miền nghiên cứu: từ chối và thông báo rõ, **không dự đoán bừa**.
- Dù pipeline có median imputer, endpoint MVP chủ động yêu cầu đủ cả ba trường; thay đổi chính sách missingness phải được thiết kế và kiểm thử riêng.

## 4. Output contract dự kiến

```json
{
  "status": "research_only",
  "task": "classify_hba1c_ge_5_7_indicator",
  "model_name": "LogisticRegression",
  "model_sha256": "31e9c94b0f14369be7920b9315b026d0c4afedb9f7b2885d120d631d930582b1",
  "threshold": 0.225,
  "model_score": 0.0,
  "predicted_label": 0,
  "warning": "Research-only score; not a diagnosis or future type 2 diabetes risk estimate."
}
```

**Quan trọng:** `model_score` phía trên chỉ là **minh họa schema** với 0.0; không phải kết quả dự đoán của bất kỳ cá nhân nào. Bước 8A sinh điểm thực tế khi người dùng tự chạy ví dụ tổng hợp (synthetic), không được đưa ví dụ này vào tài liệu kết quả lâm sàng.

## 5. Điều kiện an toàn bắt buộc

1. Chỉ nạp `joblib` có nguồn gốc đáng tin và đã so khớp hash; tệp dạng pickle có thể thực thi mã khi tải. Không cho API người dùng upload model.
2. Cố định môi trường thư viện đã train (`scikit-learn 1.8.0`, cùng Python/dependencies). Nếu khác phiên bản: dừng, không cố load.
3. Không mở public endpoint, không dùng với dữ liệu sức khỏe thật trước khi kiểm định an toàn và đánh giá lâm sàng.
4. Không log payload sức khỏe, không hiển thị `SEQN` hoặc dữ liệu nhận dạng trong báo cáo.
5. Mọi phản hồi ứng dụng về sau phải có trạng thái research-only và ghi đúng **dự đoán chỉ dấu HbA1c**, không được thay thế bằng tên bệnh/type 2.
6. Test holdout đã dùng, không tiếp tục tuning, thay đổi threshold hoặc gọi lại Test. Bất kỳ vòng phát triển mô hình mới nào phải thiết lập kế hoạch đánh giá mới.

## 6. Tiêu chí hoàn thành Bước 8A

- [ ] SHA256 artifact và version môi trường khớp.
- [ ] Validation ROC-AUC tái hiện xấp xỉ 0,7173 mà không `.fit()`.
- [ ] Validation 705 và positives=208; không đọc Test.
- [ ] Synthetic inputs hợp lệ tạo được điểm finite trong [0,1] và label tại threshold 0,225.
- [ ] Inputs sai kiểu, thiếu, quá phạm vi bị từ chối rõ ràng.
- [ ] Manifest nghiên cứu được tạo, không chứa dữ liệu cá nhân.
- [ ] Người dùng gửi output console cuối `BƯỚC 8A — INFERENCE PREFLIGHT` để cập nhật log.

## 7. Tài liệu nguồn

- scikit-learn model persistence: https://scikit-learn.org/stable/model_persistence.html
- FastAPI Pydantic request models: https://fastapi.tiangolo.com/tutorial/body/
- CDC NHANES sample design: https://wwwn.cdc.gov/nchs/nhanes/tutorials/sampledesign.aspx
