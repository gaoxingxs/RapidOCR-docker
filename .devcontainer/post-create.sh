#!/usr/bin/env bash
# Codespace 容器创建后自动执行：安装系统依赖 + Python 依赖
set -euo pipefail

echo "[post-create] 安装 OpenCV 运行所需的系统库"
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    fonts-dejavu-core
sudo rm -rf /var/lib/apt/lists/*

echo "[post-create] 安装 Python 依赖"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install requests

echo "[post-create] 完成。可执行 'uvicorn main:app --host 0.0.0.0 --port 8000' 启动服务，再用 'python test_client.py' 测试。"
