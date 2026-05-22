"""RapidOCR 服务端到端测试脚本

用法：
    python test_client.py [base_url]
默认 base_url = http://127.0.0.1:8000
"""

import io
import sys
import time

import requests
from PIL import Image, ImageDraw, ImageFont


def make_sample_image() -> bytes:
    """生成一张包含中英文文字的测试图片。"""
    image = Image.new("RGB", (480, 200), color="white")
    draw = ImageDraw.Draw(image)
    try:
        # Codespaces / Linux 上常见字体路径
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32
        )
    except OSError:
        font = ImageFont.load_default()

    draw.text((20, 30), "Hello RapidOCR", fill="black", font=font)
    draw.text((20, 90), "12345  ABCDE", fill="black", font=font)
    draw.text((20, 140), "GitHub Codespaces", fill="black", font=font)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def wait_for_service(base_url: str, timeout: int = 60) -> None:
    """轮询等待服务启动。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = requests.get(f"{base_url}/health", timeout=2)
            if resp.ok:
                print(f"[OK] 服务已就绪: {resp.json()}")
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError(f"服务在 {timeout}s 内未就绪: {base_url}")


def main(base_url: str) -> int:
    wait_for_service(base_url)

    image_bytes = make_sample_image()

    print("\n[1] 测试 /ocr 文件上传接口")
    files = {"file": ("test.png", image_bytes, "image/png")}
    resp = requests.post(f"{base_url}/ocr", files=files, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    print(f"  耗时: {data['elapsed_ms']} ms, 识别条数: {data['count']}")
    for item in data["items"]:
        print(f"    - {item['text']} (score={item['score']:.3f})")

    if data["count"] == 0:
        print("[WARN] 未识别到任何文本")
        return 2

    print("\n[2] 测试 /health 健康检查")
    resp = requests.get(f"{base_url}/health", timeout=5)
    resp.raise_for_status()
    print(f"  -> {resp.json()}")

    print("\n[PASS] 全部测试通过")
    return 0


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    sys.exit(main(url))
