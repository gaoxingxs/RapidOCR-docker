"""RapidOCR FastAPI 服务化封装

提供基于 RapidOCR 的 HTTP OCR 服务接口：
- POST /ocr           上传图片文件进行识别
- POST /ocr/base64    通过 base64 字符串进行识别
- GET  /health        健康检查
"""

import base64
import io
import logging
import os
import time
from typing import List, Optional

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel
from rapidocr_onnxruntime import RapidOCR

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("rapidocr-service")

# 模型目录：优先使用本地 models 目录（离线部署），否则使用 rapidocr 默认路径
MODEL_DIR = os.environ.get("RAPIDOCR_MODEL_DIR", "./models")


def _build_engine() -> RapidOCR:
    """构建 RapidOCR 引擎，优先加载本地离线模型。"""
    det_path = os.path.join(MODEL_DIR, "ch_PP-OCRv4_det_infer.onnx")
    cls_path = os.path.join(MODEL_DIR, "ch_ppocr_mobile_v2.0_cls_infer.onnx")
    rec_path = os.path.join(MODEL_DIR, "ch_PP-OCRv4_rec_infer.onnx")

    if all(os.path.isfile(p) for p in (det_path, cls_path, rec_path)):
        logger.info("使用本地离线模型: %s", MODEL_DIR)
        return RapidOCR(
            det_model_path=det_path,
            cls_model_path=cls_path,
            rec_model_path=rec_path,
        )

    logger.info("本地模型不完整，使用 RapidOCR 内置默认模型")
    return RapidOCR()


# 全局引擎，加载一次复用
ocr_engine = _build_engine()

app = FastAPI(
    title="RapidOCR Service",
    description="基于 RapidOCR 的离线 OCR 服务",
    version="1.0.0",
)


class OCRItem(BaseModel):
    """单条 OCR 识别结果。"""

    text: str
    score: float
    box: List[List[float]]


class OCRResponse(BaseModel):
    """OCR 接口响应体。"""

    success: bool
    elapsed_ms: float
    count: int
    items: List[OCRItem]


class Base64Request(BaseModel):
    """base64 入参。"""

    image_base64: str


def _run_ocr(image_bytes: bytes) -> OCRResponse:
    """对图像字节进行 OCR 识别并组装响应。"""
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"无法解析图像: {exc}") from exc

    image_array = np.asarray(image)

    start = time.perf_counter()
    result, _elapse = ocr_engine(image_array)
    elapsed_ms = (time.perf_counter() - start) * 1000

    items: List[OCRItem] = []
    if result:
        for box, text, score in result:
            items.append(OCRItem(text=text, score=float(score), box=box))

    return OCRResponse(
        success=True,
        elapsed_ms=round(elapsed_ms, 2),
        count=len(items),
        items=items,
    )


@app.get("/health")
def health() -> dict:
    """健康检查接口。"""
    return {"status": "ok", "service": "rapidocr"}


@app.get("/")
def root() -> dict:
    """根路径返回服务信息。"""
    return {
        "service": "RapidOCR Service",
        "version": "1.0.0",
        "endpoints": ["/ocr", "/ocr/base64", "/health", "/docs"],
    }


@app.post("/ocr", response_model=OCRResponse)
async def ocr_file(file: UploadFile = File(...)) -> OCRResponse:
    """通过 multipart 文件上传进行 OCR 识别。"""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件内容为空")
    return _run_ocr(content)


@app.post("/ocr/base64", response_model=OCRResponse)
def ocr_base64(payload: Base64Request) -> OCRResponse:
    """通过 base64 字符串进行 OCR 识别。"""
    raw = payload.image_base64
    # 兼容 data URI 前缀
    if "," in raw and raw.strip().startswith("data:"):
        raw = raw.split(",", 1)[1]
    try:
        image_bytes = base64.b64decode(raw)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"base64 解码失败: {exc}") from exc
    return _run_ocr(image_bytes)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request, exc: Exception):
    """统一异常处理，避免服务因偶发错误中断。"""
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": str(exc)},
    )
