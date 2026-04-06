#!/bin/bash
# ComfyUI macOS 原生安装脚本 (Apple Silicon M1/M2/M3)
# 用途：本地运行 Stable Diffusion，完全离线/内网，不对外暴露

set -e

echo "=========================================="
echo "ComfyUI macOS 安装脚本 (MPS 加速)"
echo "=========================================="

COMFYUI_DIR="$HOME/comfyui"
PYTHON_VERSION="3.10"  # 建议用 3.10+

# 检测系统
if [[ "$(uname)" != "Darwin" ]]; then
    echo "[!] 仅支持 macOS"
    exit 1
fi

if [[ "$(uname -m)" == "arm64" ]]; then
    echo "[+] Apple Silicon 检测到"
else
    echo "[!] 仅验证 Apple Silicon Mac"
fi

# 检查内存
TOTAL_MEM=$(sysctl -n hw.memsize 2>/dev/null)
TOTAL_MEM_GB=$((TOTAL_MEM / 1024 / 1024 / 1024))
echo "[*] 内存: ${TOTAL_MEM_GB} GB"
if [[ $TOTAL_MEM_GB -lt 8 ]]; then
    echo "[!] 建议 8GB+ 内存，低于此可能不稳定"
fi

# 检查磁盘空间
DATA_VOL=$(df -h /System/Volumes/Data 2>/dev/null | tail -1 | awk '{print $4}')
echo "[*] 可用磁盘: $DATA_VOL"
echo "[*] 建议预留 20GB+"

echo ""
echo "[1/6] 安装 Python 3.10 (如果需要)..."
if ! command -v python3.10 &> /dev/null; then
    brew install python@3.10
else
    echo "    Python 3.10 已安装"
fi

PYTHON_BIN=$(which python3.10 2>/dev/null || which python3 2>/dev/null)
echo "    使用: $PYTHON_BIN"

echo ""
echo "[2/6] 创建虚拟环境..."
cd "$HOME"
if [[ -d "comfyui_env" ]]; then
    echo "    虚拟环境已存在，跳过"
else
    $PYTHON_BIN -m venv comfyui_env
fi
source "$HOME/comfyui_env/bin/activate"

echo ""
echo "[3/6] 安装 PyTorch (MPS 支持)..."
pip install --upgrade pip
pip install torch torchvision torchaudio

# 验证 MPS
python3 -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'MPS 可用: {torch.backends.mps.is_available()}')
print(f'MPS 构建: {torch.backends.mps.is_built()}')
"

echo ""
echo "[4/6] 克隆 ComfyUI..."
if [[ -d "$COMFYUI_DIR" ]]; then
    echo "    ComfyUI 已克隆，更新中..."
    cd "$COMFYUI_DIR"
    git pull
else
    cd "$HOME"
    git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFYUI_DIR"
fi

echo ""
echo "[5/6] 安装 ComfyUI 依赖..."
cd "$COMFYUI_DIR"
pip install -r requirements.txt

echo ""
echo "[6/6] 下载 Stable Diffusion 模型..."
MODELS_DIR="$HOME/ComfyUI/models/checkpoints"
mkdir -p "$MODELS_DIR"

SD_MODEL_URL="https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors"
SD_MODEL_NAME="v1-5-pruned-emaonly.safetensors"

if [[ -f "$MODELS_DIR/$SD_MODEL_NAME" ]]; then
    echo "    模型已存在: $SD_MODEL_NAME"
else
    echo "    下载中 (约 4GB, 首次需几分钟)..."
    echo "    如果下载过慢，可以手动从 HuggingFace 下载:"
    echo "    https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors"
    echo "    保存到: $MODELS_DIR/"
    echo ""
    echo "    或者使用国内镜像（如果有）"
    
    # 尝试用 curl 下载（可中断续传）
    curl -L -C - -o "$MODELS_DIR/$SD_MODEL_NAME" "$SD_MODEL_URL" || {
        echo "[!] 下载失败，请手动下载后放到上述目录"
    }
fi

echo ""
echo "=========================================="
echo "安装完成！"
echo "=========================================="
echo ""
echo "启动 ComfyUI:"
echo "  cd $COMFYUI_DIR"
echo "  source $HOME/comfyui_env/bin/activate"
echo "  python main.py --listen 127.0.0.1 --port 8188"
echo ""
echo "启动后访问: http://127.0.0.1:8188"
echo "（仅本地访问，不对外暴露）"
echo ""
echo "API 地址: http://127.0.0.1:8188"
echo ""
