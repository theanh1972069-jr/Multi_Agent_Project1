# GIAI ĐOẠN 4 — BƯỚC 2C: HOÀN THÀNH ĐỦ 7 NGUỒN TRƯỚC EMBEDDINGS

**Dự án:** Multi-Agent AI System for Diabetes Risk Assessment  
**Ngày lập kế hoạch:** 2026-11-03  
**Trạng thái:** `collecting_all_seven_sources` — chưa chuyển Bước 3.

## 1. Kết quả người dùng cung cấp

- Registry: **7 nguồn**.
- Nguồn đủ điều kiện theo registry trên máy người dùng: **4**.
- Tệp `.txt` được duyệt: **2**; tài liệu đã chuẩn bị: **2**.
- Đã tạo: **7 chunks**; QA của các chunks hiện có: `PASS`.
- Chưa tạo embedding, Vector Database, gọi LLM hoặc train.
- **Chưa xác định hai source_id đã có TXT** chỉ từ ảnh tổng hợp. Notebook trong gói sẽ đọc trạng thái thật trên máy bạn; không tự suy đoán hay ghi đè.

## 2. Danh mục phải xử lý trước khi chuyển Bước 3

| ID | Tác giả | Nội dung | URL chuẩn | Định hướng sử dụng |
|---|---|---|---|---|
| `CDC-T2D-001` | CDC | Type 2 Diabetes | https://www.cdc.gov/diabetes/about/about-type-2-diabetes.html | Kiểm tra quyền, lập bản TXT được phê duyệt |
| `CDC-RISK-002` | CDC | Diabetes Risk Factors | https://www.cdc.gov/diabetes/risk-factors/index.html | Kiểm tra quyền, lập bản TXT được phê duyệt |
| `NIDDK-DIAG-003` | NIDDK | Diabetes Tests & Diagnosis | https://www.niddk.nih.gov/health-information/diabetes/overview/tests-diagnosis | Kiểm tra quyền, lập bản TXT được phê duyệt |
| `NIDDK-T2D-004` | NIDDK | Type 2 Diabetes | https://www.niddk.nih.gov/health-information/diabetes/overview/what-is-diabetes/type-2-diabetes | Kiểm tra quyền, lập bản TXT được phê duyệt |
| `WHO-DIAB-005` | WHO | Diabetes | https://www.who.int/health-topics/diabetes | Cần xác minh điều khoản riêng của trang này trước khi nhập toàn văn; không tự suy giấy phép sách WHO cho web page |
| `LC-HBA1C-006` | Long Châu | HbA1c và tiền tiểu đường | https://nhathuoclongchau.com.vn/bai-viet/hb-a1c-bao-nhieu-la-tien-tieu-duong-nhan-biet-va-cai-thien.html | Quyền dùng toàn văn chưa xác minh, giữ reference-only cho tới khi có quyền |
| `LC-STAGES-007` | Long Châu | Các giai đoạn tiểu đường | https://nhathuoclongchau.com.vn/bai-viet/giai-doan-cua-benh-tieu-duong-nhan-biet-som-de-dieu-tri-kip-thoi.html | Trang cũ trong registry chuyển hướng sang URL này; cần xác minh quyền dùng toàn văn |

### Quyền sử dụng cần được kiểm tra

- **CDC:** Nhiều nội dung do cơ quan tạo thuộc public domain, nhưng có ngoại lệ đối với nội dung bên thứ ba; khi tái sử dụng cần ghi nguồn và tuyên bố không được CDC chứng thực: https://www.cdc.gov/Other/imagereuse.html
- **NIDDK:** Phần lớn văn bản có thể tái sử dụng nếu ghi nguồn; loại trừ các hình, tài sản/đồng tác giả bên thứ ba và logo: https://www.niddk.nih.gov/copyright
- **WHO:** Chính sách nêu giấy phép CC BY-NC-SA 3.0 IGO cho các **ấn phẩm WHO**, không mặc nhiên cho mọi trang website; cần xem giấy phép hoặc xin phép cho trang cụ thể. https://www.who.int/about/policies/publishing/copyright
- **Long Châu:** Điều khoản website bảo hộ văn bản và nội dung; không tự động sao chép/chia chunks/nhúng vector toàn văn nếu chưa có quyền phù hợp. https://nhathuoclongchau.com.vn/chinh-sach/tos

## 3. Quy trình làm theo thứ tự

1. **Giữ nguyên** hai TXT đã hoàn thành. Sao lưu `registry/source_registry.csv`, `data/raw_approved/` và báo cáo Step 2 trước khi thay đổi.
2. Mở notebook `notebooks/02C_Collect_Approved_Sources.ipynb`. Chạy **chỉ ô A–B** để thấy ID nào đã có `.txt` và ID nào thiếu; không cần đoán.
3. Với tối đa bốn nguồn **CDC/NIDDK**: kiểm tra nguồn/chính sách/đoạn văn thực tế, điền các trường registry theo người rà soát và thời gian thực, rồi tùy chọn chạy công cụ tải bản **nháp** vào `data/raw_staging/`. Notebook không tự xác nhận quyền, không ghi vào `data/raw_approved/` và không sửa registry.
4. Kiểm tra nội dung bản nháp; loại header/footer, quảng cáo, phần do bên thứ ba sở hữu, chỉ giữ nội dung có quyền. Sau khi rà soát thủ công, di chuyển tệp đủ điều kiện sang `data/raw_approved/<source_id>.txt` bằng VS Code/File Explorer.
5. Với **WHO**: xác minh trang cụ thể có quyền sao chép/lưu vector phục vụ nguyên mẫu nghiên cứu hay không. Nếu không đủ rõ, giữ `reference_only` và xin phép hoặc xác định **ấn phẩm WHO thay thế có giấy phép rõ ràng**, nhưng phải ghi nhận thay đổi nguồn, không tự đổi URL lén lút.
6. Với **2 bài Long Châu**: yêu cầu quyền lưu trữ, chia chunks và tạo embeddings để nghiên cứu cục bộ. Cho đến khi được phép, chỉ lưu URL/tiêu đề, hoặc tạo **ghi chú kiến thức tự biên soạn** và kiểm chứng độc lập với CDC/NIDDK (không sao chép hay viết lại sát toàn văn Long Châu). Ghi chú đó không đồng nghĩa đã ingest hai bài Long Châu.
7. Chỉ cập nhật `license_review_status=verified`, `approval_status=approved_research`, `content_review_status=owner_reviewed_research_only` khi đã xác minh thực tế. Không ghi thời gian hay người duyệt giả.
8. Chạy lại `02_RAG_Document_Preparation.ipynb` → xem `step2_preparation_report.json` → kiểm tra thủ công vài chunks mỗi nguồn → ghi nhật ký. **Không làm Embedding/ChromaDB khi chưa chốt trạng thái cả 7 nguồn.**

## 4. Tiêu chí hoàn thành mà người dùng chọn

- Cả **7 source_id** đều có bản ghi minh bạch: URL, xuất xứ, ngày truy cập, quyền tái sử dụng, người rà soát, trạng thái.
- **Để có đủ 7 nguồn toàn văn trong Vector DB**, từng nguồn cần có quyền dùng toàn văn và `.txt` được rà soát, không chỉ có registry. Nếu có nguồn không được phép, không thể bảo đảm `7/7 indexed` bằng cách vượt qua chặn quyền; phải xin phép hoặc thay thế bằng nguồn được phép và ghi rõ sự thay thế.
- Các nguồn đã phê duyệt tạo được chunks `>0`, metadata trích dẫn đầy đủ, QA kỹ thuật và thủ công đạt.
- Trước khi Bước 3 bắt đầu, quyết định rõ mục tiêu là `7/7 full-text indexed` hay `7/7 sources covered (some link-only)`; không đánh đồng hai khái niệm.

## 5. Mẫu yêu cầu quyền sử dụng gửi bên sở hữu

**Chủ đề:** Xin phép sử dụng tài liệu giáo dục sức khỏe cho nghiên cứu RAG phi thương mại

Kính gửi bộ phận quản lý nội dung, tôi đang thực hiện dự án nghiên cứu học thuật xây dựng hệ thống tra cứu kiến thức về bệnh tiểu đường. Tôi muốn xin phép sử dụng văn bản của bài viết tại [URL], trong phạm vi lưu trữ nội bộ, tách đoạn, tạo embeddings và truy xuất có trích dẫn bằng mô hình RAG, không công bố lại toàn văn và không dùng vào mục đích thương mại. Vui lòng cho biết phạm vi được phép, yêu cầu ghi nguồn, thời hạn sử dụng và các hạn chế cần tuân thủ. Xin cảm ơn.

## 6. Tài liệu cần gửi khi hoàn thành

- Output từ ô kiểm kê 7 nguồn trong notebook 02C.
- Output mới từ `02_RAG_Document_Preparation.ipynb` và `step2_preparation_report.json`.
- Danh mục quyền sử dụng, trạng thái của tất cả 7 IDs, không cần chuyển nội dung toàn văn có bản quyền vào chat.

**Không có thao tác train, embedding, vector DB hay LLM nào trong Bước 2C.**
