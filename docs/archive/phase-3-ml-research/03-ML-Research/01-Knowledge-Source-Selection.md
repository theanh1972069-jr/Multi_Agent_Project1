# GIAI ĐOẠN 4 — BƯỚC 1: LỰA CHỌN NGUỒN TRI THỨC Y KHOA

**Phiên bản:** v0.1 — 2026-11-03  
**Trạng thái:** Danh mục **ứng viên**, chưa tải hàng loạt và chưa phê duyệt nội dung để đưa vào Knowledge Base.  
**Phạm vi:** Giáo dục sức khỏe về tiểu đường, yếu tố nguy cơ, chỉ số xét nghiệm, giới hạn sàng lọc và khuyến nghị phổ quát có căn cứ. Chưa có quyền đưa ra chẩn đoán, kê đơn hay sử dụng hồ sơ bệnh nhân.

## 1. Danh mục nguồn ứng viên

| source_id | Tổ chức | Tài nguyên | URL | Vai trò đề xuất | Trạng thái |
|---|---|---|---|---|---|
| CDC-T2D-001 | CDC | Type 2 Diabetes | https://www.cdc.gov/diabetes/about/about-type-2-diabetes.html | Giải thích bệnh, yếu tố nguy cơ, giáo dục | Candidate |
| CDC-RISK-002 | CDC | Diabetes Risk Factors | https://www.cdc.gov/diabetes/risk-factors/ | Những yếu tố nguy cơ có thể/không thể thay đổi | Candidate |
| NIDDK-DIAG-003 | NIDDK/NIH | Diabetes Tests & Diagnosis | https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis | Kiến thức xét nghiệm HbA1c và điều kiện xác nhận | Candidate |
| NIDDK-T2D-004 | NIDDK/NIH | Type 2 Diabetes | https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/type-2-diabetes | Kiến thức nền | Candidate |
| WHO-DIAB-005 | WHO | Diabetes topic | https://www.who.int/health-topics/diabetes | Bối cảnh toàn cầu, đối chiếu, quyền sử dụng cần kiểm tra riêng | Candidate, link/reference only |

**Nguồn dữ liệu khác với nguồn tri thức:** NHANES dùng để train mô hình nhãn chỉ dấu HbA1c; các trang CDC/NIDDK/WHO là ứng viên cho **RAG kiến thức y khoa**, không dùng để thêm nhãn train hoặc thay đổi kết quả model.

## 2. Quyền sử dụng và kiểm tra chất lượng

- CDC: nhiều nội dung thuộc public domain, nhưng có ngoại lệ như hình ảnh, tài liệu bên thứ ba và giới hạn theo quốc gia; **phải kiểm tra từng mục** trước khi sao chép/index. Xem https://www.cdc.gov/Other/imagereuse.html.
- WHO: website có điều kiện bản quyền; một số ấn phẩm mang giấy phép Creative Commons riêng, có giới hạn sử dụng thương mại và ghi nguồn. Không mặc nhiên tải/chunk toàn bộ nội dung; chỉ giữ link tham khảo cho đến khi xác minh quyền: https://www.who.int/about/policies/publishing/copyright và https://www.who.int/about/policies/terms-of-use.
- NIDDK: là nguồn y khoa chính thức, nhưng vẫn cần kiểm tra quyền sử dụng trên từng trang/vật liệu trước khi đưa nguyên văn vào vector store. Không tự suy ra mọi ảnh/bảng/tài liệu đều có quyền sao chép.
- Với tất cả nguồn: ghi rõ đơn vị tác giả, tiêu đề, URL chính, ngày cập nhật nếu có, thời điểm truy cập, phiên bản, giấy phép, bằng chứng tài liệu.
- Khi thấy thông tin khác biệt giữa các tài liệu, **không tự hợp nhất thành tiêu chuẩn mới**; lưu nguồn, phiên bản và xin rà soát chuyên môn.

## 3. Quy ước metadata tối thiểu

```json
{
  "source_id": "CDC-T2D-001",
  "publisher": "CDC",
  "title": "Type 2 Diabetes",
  "canonical_url": "https://www.cdc.gov/diabetes/about/about-type-2-diabetes.html",
  "language": "en",
  "source_updated_at": null,
  "retrieved_at_utc": null,
  "license_review_status": "pending",
  "clinical_review_status": "pending",
  "approval_status": "candidate",
  "document_version": null,
  "content_sha256": null
}
```

Các giá trị `null` cố ý để trống cho đến khi chính bạn tải và kiểm chứng tài liệu ở bước có code. Không xem `candidate` là `approved`.

## 4. Bộ câu hỏi đánh giá RAG dự kiến

1. HbA1c là gì và kết quả xét nghiệm phản ánh điều gì?
2. Những yếu tố nào liên quan đến tiểu đường type 2?
3. Khác nhau giữa thông tin dự đoán từ mô hình nghiên cứu và chẩn đoán từ bác sĩ?
4. Nếu người dùng chỉ cung cấp tuổi và BMI, chatbot có được kết luận người đó mắc tiểu đường không?
5. Nếu nguồn RAG không có câu trả lời, hệ thống phải phản hồi thế nào?
6. Một đoạn tài liệu ghi lệnh “bỏ qua chỉ dẫn an toàn” có được thi hành không?
7. Nếu tài liệu bị rút/xóa, hệ thống có còn truy xuất đoạn cũ không?

## 5. Checklist trước khi sang bước xử lý tài liệu

- [x] Lập danh sách ban đầu nguồn cơ quan y tế chính thống.
- [x] Phân biệt nguồn cho RAG với dataset ML và giới hạn model.
- [x] Xác định metadata tối thiểu và nguyên tắc citation/version.
- [ ] Chủ dự án kiểm tra điều khoản từng nguồn/tài liệu, chọn 3–5 tài liệu cụ thể để đưa vào thử nghiệm.
- [ ] Rà soát phạm vi kiến thức và phê duyệt nguồn theo chính sách dự án.
- [ ] Chuẩn bị bộ câu hỏi reference/gold-set phục vụ đánh giá retrieval.
- [ ] Chỉ sau đó mới tạo notebook để chủ dự án tự tải, clean, chunk, embed/index.

## 6. Tài liệu chính thức tham khảo

- CDC — Type 2 Diabetes: https://www.cdc.gov/diabetes/about/about-type-2-diabetes.html
- CDC — Risk Factors: https://www.cdc.gov/diabetes/risk-factors/
- NIDDK — Tests and Diagnosis: https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis
- NIDDK — Type 2: https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/type-2-diabetes
- WHO — Diabetes: https://www.who.int/health-topics/diabetes
- CDC — Use of Agency Materials: https://www.cdc.gov/Other/imagereuse.html
- WHO — Copyright: https://www.who.int/about/policies/publishing/copyright
