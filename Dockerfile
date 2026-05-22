# 使用轻量级 Python 3.9 镜像
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖：OpenCV 运行库 + wget 用于下载模型
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件以便利用层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制服务代码
COPY main.py .

# 下载 PP-OCRv4 ONNX 模型（来源：HuggingFace SWHL/RapidOCR）
RUN mkdir -p /app/models && \
    wget -q -O /app/models/ch_PP-OCRv4_det_infer.onnx \
      "https://huggingface.co/SWHL/RapidOCR/resolve/main/PP-OCRv4/ch_PP-OCRv4_det_infer.onnx" && \
    wget -q -O /app/models/ch_ppocr_mobile_v2.0_cls_infer.onnx \
      "https://huggingface.co/SWHL/RapidOCR/resolve/main/PP-OCRv1/ch_ppocr_mobile_v2.0_cls_infer.onnx" && \
    wget -q -O /app/models/ch_PP-OCRv4_rec_infer.onnx \
      "https://huggingface.co/SWHL/RapidOCR/resolve/main/PP-OCRv4/ch_PP-OCRv4_rec_infer.onnx"

ENV RAPIDOCR_MODEL_DIR=/app/models

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
