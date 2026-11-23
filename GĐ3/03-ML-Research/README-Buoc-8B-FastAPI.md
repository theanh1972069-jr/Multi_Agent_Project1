# GIAI ĐOẠN 3 — BƯỚC 8B: TỰ XÂY DỰNG FASTAPI INFERENCE (JUPYTER + PYTHON)

**Trạng thái:** Bước 8A người dùng đã chạy thành công. Bước 8B là **hướng dẫn để người dùng tự thực hành**, chưa có kết quả chạy server/API nào được xác nhận.

## 0. Kết quả Bước 8A đã xác nhận

- Mô hình: `LogisticRegression` trong `Pipeline(prep, model)`, scikit-learn **1.8.0**, Python **3.13.9**.
- SHA256: `31e9c94b0f14369be7920b9315b026d0c4afedb9f7b2885d120d631d930582b1` (trùng Bước 5–7).
- Input: `RIDAGEYR`, `RIAGENDR`, `BMXBMI`; ngưỡng **0.225**; nhãn nghiên cứu **HbA1c ≥ 5.7%**.
- Validation n=705/positive=208, ROC-AUC tái lập **0.7173**. Test **không mở**, fit **không chạy**.
- 2 input giả lập hợp lệ có score **0.22552** và **0.39459**, nhãn dự đoán 1 / 1. 4/4 input sai được từ chối.
- Không suy luận nguy cơ mắc tiểu đường type 2 tương lai; đây không phải phần mềm y tế.

## 1. Mục tiêu và giới hạn

Tự tạo API nội bộ (host `127.0.0.1`) với ba endpoint:

| Phương thức | URL | Kết quả |
| --- | --- | --- |
| GET | `/health/live` | API còn hoạt động |
| GET | `/health/ready` | Đã nạp được artifact có SHA256 khớp |
| POST | `/api/v1/research/nhanes/hba1c/predict` | Chỉ trả **điểm nghiên cứu** và nhãn theo ngưỡng cố định |

Không triển khai lên Internet, không nhận thông tin sức khỏe thật, không lưu payload, không ghi log body. Không huấn luyện lại hoặc xem Test. Backend sau này cần auth/RBAC/giới hạn tốc độ/đánh giá lâm sàng trước triển khai thực tế.

## 2. Tạo thư mục và cài dependencies

Từ PowerShell trong `GĐ3/03-ML-Research`, sử dụng chính môi trường `.venv` từ Bước 5 (Python/sklearn giống lần train):

```powershell
.\.venv\Scripts\python.exe -m pip install fastapi uvicorn requests
.\.venv\Scripts\python.exe -m pip show fastapi pydantic scikit-learn
```

Tạo thư mục `backend/app/` và hai file `backend/app/__init__.py` (để trống), `backend/app/main.py` (code bên dưới). **Bạn chủ động tạo và lưu các file bằng VS Code**; tài liệu này chỉ là mã tham khảo.

```text
03-ML-Research/
├── backend/
│   └── app/
│       ├── __init__.py
│       └── main.py
├── notebooks/
│   └── 08B_NHANES_FastAPI_Client.ipynb
├── models/baseline/nhanes_hba1c_baseline_step5.joblib  # giữ nguyên
└── data/outputs/model_deployment/preflight_8a/08a_inference_manifest.json
```

## 3. Tự viết `backend/app/main.py` theo mẫu

**Cần hiểu các phần:** (a) constants/model schema cố định; (b) Pydantic kiểm tra miền hợp lệ; (c) `lifespan` kiểm hash/phiên bản rồi tải model đúng một lần khi startup; (d) `POST /predict` tạo DataFrame đúng thứ tự; (e) `predict_proba` và ngưỡng; (f) response không diễn giải thành xác suất mắc bệnh.

```python
"""Bước 8B — FastAPI chỉ dành cho nghiên cứu, KHÔNG triển khai công khai.
Tự tạo file backend/app/main.py theo hướng dẫn trong README.
"""
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
import hashlib
import math
import os
import platform

import joblib
import pandas as pd
import sklearn
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

EXPECTED_SHA256 = "31e9c94b0f14369be7920b9315b026d0c4afedb9f7b2885d120d631d930582b1"
EXPECTED_PYTHON = "3.13.9"
EXPECTED_SKLEARN = "1.8.0"
THRESHOLD = 0.225
FEATURES = ["RIDAGEYR", "RIAGENDR", "BMXBMI"]
WARNING = (
    "Research-only HbA1c >=5.7% indicator classification; "
    "not a diagnosis or future type 2 diabetes risk estimate."
)

class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    RIDAGEYR: int = Field(ge=20, le=80, description="80 denotes top-coded age 80+")
    RIAGENDR: Literal[1, 2]
    BMXBMI: float = Field(ge=11.1, le=74.8, allow_inf_nan=False)

class PredictionResponse(BaseModel):
    status: Literal["research_only"]
    task: str
    model_name: str
    model_sha256: str
    threshold: float
    model_score: float
    predicted_label: Literal[0, 1]
    warning: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    model_path_raw = os.getenv("NHANES_MODEL_PATH")
    if not model_path_raw:
        raise RuntimeError("Hãy đặt biến NHANES_MODEL_PATH trỏ đến model do bạn tự train.")
    model_path = Path(model_path_raw).expanduser().resolve(strict=True)
    if not model_path.is_file():
        raise RuntimeError("NHANES_MODEL_PATH không phải file.")
    computed = hashlib.sha256(model_path.read_bytes()).hexdigest()
    if computed != EXPECTED_SHA256:
        raise RuntimeError("SHA256 không khớp; từ chối nạp model.")
    if platform.python_version() != EXPECTED_PYTHON or sklearn.__version__ != EXPECTED_SKLEARN:
        raise RuntimeError("Khác Python/sklearn lúc train; từ chối nạp model.")
    # Chỉ load artifact do chính người dùng tạo/kiểm soát. SHA256 không thay thế kiểm tra nguồn gốc.
    pipeline = joblib.load(model_path)
    if list(pipeline.named_steps) != ["prep", "model"]:
        raise RuntimeError("Pipeline steps không giống Bước 8A.")
    if type(pipeline.named_steps["model"]).__name__ != "LogisticRegression":
        raise RuntimeError("Sai mô hình được chốt.")
    if list(pipeline.feature_names_in_) != FEATURES:
        raise RuntimeError("Thứ tự input của Pipeline không đúng.")
    app.state.pipeline = pipeline
    yield
    app.state.pipeline = None

app = FastAPI(
    title="NHANES HbA1c Research Inference (local only)",
    version="0.1.0",
    lifespan=lifespan,
)

@app.get("/health/live")
def live():
    return {"status": "alive"}

@app.get("/health/ready")
def ready(request: Request):
    if getattr(request.app.state, "pipeline", None) is None:
        raise HTTPException(status_code=503, detail="Model unavailable")
    return {"status": "ready", "model_sha256": EXPECTED_SHA256, "research_only": True}

@app.post("/api/v1/research/nhanes/hba1c/predict", response_model=PredictionResponse)
def predict(body: PredictionRequest, request: Request):
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Model unavailable")
    row = pd.DataFrame([body.model_dump()], columns=FEATURES)
    try:
        score = float(pipeline.predict_proba(row)[0, 1])
    except Exception:
        # Không trả stack trace/chi tiết dữ liệu sức khỏe cho client.
        raise HTTPException(status_code=503, detail="Inference unavailable")
    if not math.isfinite(score) or not 0.0 <= score <= 1.0:
        raise HTTPException(status_code=503, detail="Invalid model output")
    return PredictionResponse(
        status="research_only",
        task="classify_hba1c_ge_5_7_indicator",
        model_name="LogisticRegression",
        model_sha256=EXPECTED_SHA256,
        threshold=THRESHOLD,
        model_score=score,
        predicted_label=int(score >= THRESHOLD),
        warning=WARNING,
    )
```

**Giới hạn đầu vào**: RIDAGEYR phải là số nguyên 20..80 (80=nhóm 80+); RIAGENDR là mã 1/2; BMXBMI hữu hạn và trong 11.1..74.8. Đây chỉ là phạm vi nghiên cứu quan sát, KHÔNG phải giới hạn y khoa. Không chấp nhận trường ngoài, chuỗi thay số, NaN/Inf hoặc thiếu một trường.

**Lưu ý về an toàn:** `joblib.load` dựa trên pickle, có thể thực thi mã từ file độc hại. Chỉ dùng file do chính bạn tạo, và kiểm tra SHA256/phiên bản **trước** khi load. SHA256 chứng minh file trùng bản được ghi nhận, không tự chứng minh an toàn nếu nguồn gốc file không tin cậy.

## 4. Tự chạy server ở PowerShell (KHÔNG chạy trong notebook)

Ở thư mục `03-ML-Research`, mở terminal riêng, giữ nó chạy trong khi thử API:

```powershell
$env:NHANES_MODEL_PATH = (Resolve-Path ".\models\baseline\nhanes_hba1c_baseline_step5.joblib").Path
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Mở trong trình duyệt: `http://127.0.0.1:8000/docs` (Swagger UI), `http://127.0.0.1:8000/health/ready`.

Không dùng `--host 0.0.0.0` và không mở cổng mạng ngoài trong giai đoạn nghiên cứu. Nếu khởi động lỗi: kiểm biến môi trường, đường dẫn model, SHA256, Python/sklearn trước; không tắt các kiểm tra để chạy cho được.

## 5. Kiểm thử bằng Jupyter

Notebook `notebooks/08B_NHANES_FastAPI_Client.ipynb` sẽ gửi yêu cầu `requests.get` và `requests.post` tới local API khi **bạn** chạy ô lệnh. Các phép kiểm thử:

1. `GET /health/live` và `/health/ready` trả 200.
2. Hai ví dụ giả lập giống Bước 8A: (45, 1, 28.5) và (60, 2, 34.8); kiểm model hash, threshold, score gần 0.22552 và 0.39459, nhãn 1/1.
3. 6 trường hợp JSON sai: tuổi <20, mã giới tính ngoài 1/2, BMI quá miền, thiếu BMI, thừa trường, tuổi là chuỗi; mong đợi HTTP 422.
4. Kiểm tra status `research_only`, warning rõ và không có khóa `diabetes_probability`.
5. Xuất `data/outputs/model_deployment/fastapi_8b/08b_api_smoke_results.json`, chỉ ghi metrics kỹ thuật, **không ghi dữ liệu sức khỏe cá thể**.

## 6. Tiêu chí chấp nhận

- [ ] Khởi động server localhost thành công, thấy `/docs`.
- [ ] SHA256 khớp, Python 3.13.9, sklearn 1.8.0; không đọc Test và không `.fit()`.
- [ ] Đọciness/liveness OK; 2/2 dự đoán giả lập gần điểm Bước 8A.
- [ ] 6/6 yêu cầu không hợp lệ bị trả 422.
- [ ] Kết quả dùng đúng `model_score`, không gọi `diabetes_risk`; warning hiện đầy đủ.
- [ ] Notebook xuất báo cáo smoke test mà không chứa dữ liệu cá thể.

## 7. Báo cáo lại để ghi hồ sơ

Gửi output cuối **`BƯỚC 8B — LOCAL FASTAPI SMOKE TEST`** hoặc JSON tổng hợp; nếu lỗi gửi stack trace ở terminal đã loại bỏ thông tin nhạy cảm. Khi Bước 8B được xác nhận, chúng ta mới làm 8C kết nối Prediction Agent/LangGraph.

## 8. Nguồn kỹ thuật

- FastAPI lifespan: https://fastapi.tiangolo.com/advanced/events/
- FastAPI request body: https://fastapi.tiangolo.com/tutorial/body/
- FastAPI validation/errors: https://fastapi.tiangolo.com/tutorial/handling-errors/
- scikit-learn model persistence: https://scikit-learn.org/stable/model_persistence.html
