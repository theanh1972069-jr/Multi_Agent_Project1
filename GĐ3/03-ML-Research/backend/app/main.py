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
