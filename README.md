# RapidOCR-docker

基于 [RapidOCR](https://github.com/RapidAI/RapidOCR) 的 OCR 服务化封装项目，使用 FastAPI 提供 HTTP 接口，并通过 Docker 一键部署，专门面向**内网/离线**环境设计。

## 项目结构

```
.
├── main.py                  # FastAPI 服务主程序
├── requirements.txt         # Python 依赖
├── Dockerfile               # 镜像构建文件
├── test_client.py           # 端到端测试脚本
├── .devcontainer/           # GitHub Codespaces 配置
└── models/                  # 离线 ONNX 模型目录（默认不入库）
```

## 接口说明

| 方法 | 路径           | 说明                       |
| ---- | -------------- | -------------------------- |
| GET  | `/`            | 服务信息                   |
| GET  | `/health`      | 健康检查                   |
| GET  | `/docs`        | Swagger 在线文档           |
| POST | `/ocr`         | multipart 文件上传识别     |
| POST | `/ocr/base64`  | 提交 base64 字符串识别     |

## 快速开始

### 方式 1：在 GitHub Codespaces 中运行

1. 在仓库页面点击 `Code -> Codespaces -> Create codespace on main`
2. 容器启动后依赖会自动安装，运行：
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
3. 在另一个终端执行：
   ```bash
   python test_client.py
   ```

### 方式 2：本地 Docker

```bash
docker build -t rapidocr-offline:v1.0 .
docker run -d --name rapidocr-service -p 8000:8000 --restart always rapidocr-offline:v1.0
```

### 方式 3：本地 Python

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 离线部署

将以下三个 ONNX 模型放入 `models/` 目录：

- `ch_PP-OCRv4_det_infer.onnx`
- `ch_ppocr_mobile_v2.0_cls_infer.onnx`
- `ch_PP-OCRv4_rec_infer.onnx`

构建镜像后即可在无网环境运行：

```bash
docker save -o rapidocr-offline-v1.0.tar rapidocr-offline:v1.0
# 内网环境
docker load -i rapidocr-offline-v1.0.tar
docker run -d --name rapidocr-service -p 8000:8000 rapidocr-offline:v1.0
```

## 调用示例

```bash
curl -X POST -F "file=@test.png" http://127.0.0.1:8000/ocr
```

返回：

```json
{
  "success": true,
  "elapsed_ms": 320.45,
  "count": 2,
  "items": [
    { "text": "Hello RapidOCR", "score": 0.987, "box": [[...]] }
  ]
}
```
