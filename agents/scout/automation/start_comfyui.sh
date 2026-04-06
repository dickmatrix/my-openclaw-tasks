#!/bin/bash
# ComfyUI 快速启动脚本（安装后使用）
# 用途：一键启动 ComfyUI 并验证 API 可用

set -e

COMFYUI_DIR="$HOME/comfyui"
VENV_DIR="$HOME/comfyui_env"

if [[ ! -d "$COMFYUI_DIR" ]]; then
    echo "[!] ComfyUI 未安装，请先运行 install_comfyui_mac.sh"
    exit 1
fi

if [[ ! -d "$VENV_DIR" ]]; then
    echo "[!] 虚拟环境未创建，请先运行 install_comfyui_mac.sh"
    exit 1
fi

echo "=========================================="
echo "启动 ComfyUI (MPS 加速)"
echo "=========================================="

cd "$COMFYUI_DIR"
source "$VENV_DIR/bin/activate"

echo "[*] 检查 PyTorch MPS 状态..."
python3 -c "
import torch
print(f'  PyTorch: {torch.__version__}')
print(f'  MPS 可用: {torch.backends.mps.is_available()}')
"

echo ""
echo "[*] 检查模型文件..."
MODELS_DIR="$HOME/ComfyUI/models/checkpoints"
if [[ -f "$MODELS_DIR/v1-5-pruned-emaonly.safetensors" ]]; then
    echo "  [✓] SD 1.5 模型已就绪"
else
    echo "  [!] 模型文件未找到，请先运行 install_comfyui_mac.sh 下载模型"
    echo "  模型路径: $MODELS_DIR"
fi

echo ""
echo "[*] 启动 ComfyUI..."
echo "  访问地址: http://127.0.0.1:8188"
echo "  API 地址: http://127.0.0.1:8188"
echo "  仅本地访问，不对外暴露"
echo "  按 Ctrl+C 停止"
echo ""

# 启动参数：
# --listen 127.0.0.1  仅监听本地（不对外暴露）
# --port 8188         指定端口
# MPS 会自动启用（如 PyTorch 检测到 Apple Silicon GPU）
python3 main.py \
    --listen 127.0.0.1 \
    --port 8188 \
    2>&1
