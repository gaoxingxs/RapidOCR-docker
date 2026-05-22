# 使用轻量级 Python 3.9 镜像
FROM python:3.9-slim

WORKDIR /app

# 安装 OpenCV 运行所需的系统级底层库（解决 libGL/libglib 报错）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖文件以便利用层缓存
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制服务代码
COPY main.py .

# 创建模型目录（离线部署时可通过 volume 挂载或构建前放入 ONNX 模型）
RUN mkdir -p /app/models

ENV RAPIDOCR_MODEL_DIR=/app/models

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
