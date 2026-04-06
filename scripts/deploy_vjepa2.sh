#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="vjepa2-docker"
CONTAINER_NAME="vjepa2-container"
INPUT_DIR="${PROJECT_ROOT}/input"
OUTPUT_DIR="${PROJECT_ROOT}/output"
WEIGHTS_DIR="${PROJECT_ROOT}/weights"
LOG_FILE="${OUTPUT_DIR}/deploy_vjepa2.log"
RUN_TEST_FILE="${OUTPUT_DIR}/run_test.py"
WEIGHT_FILE="${WEIGHTS_DIR}/vjepa2-1.2B.pth"

mkdir -p "${INPUT_DIR}" "${OUTPUT_DIR}" "${WEIGHTS_DIR}"
: > "${LOG_FILE}"

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$1" | tee -a "${LOG_FILE}"
}

run_and_log() {
  log "$*"
  "$@" 2>&1 | tee -a "${LOG_FILE}"
}

ensure_docker() {
  command -v docker >/dev/null || { log "Docker 未安装。请先安装 Docker Desktop。"; exit 1; }
  docker info >/dev/null 2>&1 || { log "Docker 未启动。请先启动 Docker Desktop。"; exit 1; }
}

build_image() {
  run_and_log docker pull pytorch/pytorch:2.4.1-cuda12.1-cudnn9-runtime
  run_and_log docker build \
    -f "${PROJECT_ROOT}/Dockerfile.vjepa2" \
    -t "${IMAGE_NAME}" \
    "${PROJECT_ROOT}"
}

download_weights() {
  if [[ -f "${WEIGHT_FILE}" ]]; then
    log "权重已存在，跳过下载: ${WEIGHT_FILE}"
    return
  fi

  local candidates=(
    "https://dl.fbaipublicfiles.com/vjepa2/vjepa2-1.2B.pth"
    "https://huggingface.co/facebook/vjepa2-1.2B/resolve/main/vjepa2-1.2B.pth"
    "https://dl.fbaipublicfiles.com/vjepa2/vitl.pt"
  )

  for url in "${candidates[@]}"; do
    log "尝试下载权重: ${url}"
    if curl -fL --retry 5 --retry-delay 5 --connect-timeout 30 --max-time 0 "${url}" -o "${WEIGHT_FILE}.part" 2>>"${LOG_FILE}"; then
      mv "${WEIGHT_FILE}.part" "${WEIGHT_FILE}"
      log "权重下载成功: ${WEIGHT_FILE}"
      return
    fi
    rm -f "${WEIGHT_FILE}.part"
  done

  log "无法下载 vjepa2-1.2B.pth。请手动下载后放到 ${WEIGHT_FILE}"
  exit 1
}

create_container() {
  if docker ps -a --format '{{.Names}}' | grep -Fxq "${CONTAINER_NAME}"; then
    run_and_log docker rm -f "${CONTAINER_NAME}"
  fi

  run_and_log docker run -d \
    --name "${CONTAINER_NAME}" \
    --gpus all \
    --user 1000:1000 \
    --cap-drop ALL \
    --security-opt no-new-privileges:true \
    --pids-limit 1024 \
    --read-only \
    --tmpfs /tmp:rw,nosuid,noexec,size=8g \
    --mount type=bind,src="${INPUT_DIR}",dst=/workspace/input,readonly \
    --mount type=bind,src="${OUTPUT_DIR}",dst=/workspace/output \
    --mount type=bind,src="${WEIGHTS_DIR}",dst=/workspace/weights \
    "${IMAGE_NAME}" \
    sleep infinity
}

generate_run_test() {
  cat > "${RUN_TEST_FILE}" <<'PY'
import os
import re
import traceback
from pathlib import Path

import torch

LOG_PATH = Path('/workspace/output/run_test.log')
WEIGHT_PATH = Path('/workspace/weights/vjepa2-1.2B.pth')


def log(msg: str) -> None:
    print(msg, flush=True)
    with LOG_PATH.open('a', encoding='utf-8') as f:
        f.write(msg + '\n')


def clean_state_dict(sd: dict) -> dict:
    out = {}
    for k, v in sd.items():
        nk = k.replace('module.', '').replace('backbone.', '')
        out[nk] = v
    return out


def pick_tensor(obj):
    if torch.is_tensor(obj):
        return obj
    if isinstance(obj, (list, tuple)):
        for item in obj:
            t = pick_tensor(item)
            if t is not None:
                return t
    if isinstance(obj, dict):
        for _, item in obj.items():
            t = pick_tensor(item)
            if t is not None:
                return t
    return None


def load_local_weight(encoder):
    if not WEIGHT_PATH.exists():
        raise FileNotFoundError(f'权重不存在: {WEIGHT_PATH}')

    ckpt = torch.load(str(WEIGHT_PATH), map_location='cpu')
    if not isinstance(ckpt, dict):
        raise RuntimeError('权重文件不是 dict 结构，无法解析')

    state = None
    for k in ('target_encoder', 'encoder', 'state_dict', 'model'):
        if k in ckpt and isinstance(ckpt[k], dict):
            state = ckpt[k]
            break

    if state is None:
        tensor_keys = [k for k, v in ckpt.items() if torch.is_tensor(v)]
        if tensor_keys:
            state = {k: ckpt[k] for k in tensor_keys}

    if state is None:
        raise RuntimeError(f'未找到可加载参数键，现有键: {list(ckpt.keys())[:20]}')

    msg = encoder.load_state_dict(clean_state_dict(state), strict=False)
    log(f'load_state_dict done. missing={len(msg.missing_keys)} unexpected={len(msg.unexpected_keys)}')


def main() -> int:
    LOG_PATH.write_text('', encoding='utf-8')
    log(f'python={os.sys.version}')
    log(f'torch={torch.__version__}')
    log(f'cuda_available={torch.cuda.is_available()} device_count={torch.cuda.device_count()}')

    if not torch.cuda.is_available():
        raise RuntimeError('GPU_NOT_AVAILABLE')

    torch.cuda.init()
    device = torch.device('cuda:0')
    log(f'gpu_name={torch.cuda.get_device_name(0)}')

    encoder, predictor = torch.hub.load('/opt/vjepa2', 'vjepa2_vit_large', source='local', pretrained=False, num_frames=8)
    load_local_weight(encoder)

    encoder = encoder.to(device).eval()
    predictor = predictor.to(device).eval()

    x = torch.randn(1, 3, 8, 256, 256, device=device)
    with torch.no_grad():
        out = encoder(x)

    t = pick_tensor(out)
    if t is None:
        raise RuntimeError('推理输出为空')

    log(f'output_shape={tuple(t.shape)} dtype={t.dtype} mean={float(t.float().mean()):.6f} std={float(t.float().std()):.6f}')
    log('RUN_TEST_OK')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception:
        traceback.print_exc()
        raise
PY
  log "已生成测试脚本: ${RUN_TEST_FILE}"
}

apply_fix_and_retry() {
  local retry="$1"
  local run_log="${OUTPUT_DIR}/run_test_attempt_${retry}.log"

  set +e
  docker exec "${CONTAINER_NAME}" python /workspace/output/run_test.py > "${run_log}" 2>&1
  local code=$?
  set -e

  cat "${run_log}" >> "${LOG_FILE}"

  if [[ ${code} -eq 0 ]] && grep -q 'RUN_TEST_OK' "${run_log}"; then
    log "推理测试通过（第 ${retry} 次）"
    return 0
  fi

  log "第 ${retry} 次测试失败，开始自动诊断"

  if grep -Eq "No module named '([^']+)'" "${run_log}"; then
    local pkg
    pkg=$(grep -Eo "No module named '([^']+)'" "${run_log}" | sed -E "s/No module named '([^']+)'/\1/" | tail -n1)
    log "检测到缺失依赖: ${pkg}"
    run_and_log docker exec "${CONTAINER_NAME}" python -m pip install "${pkg}"
    return 1
  fi

  if grep -q 'GPU_NOT_AVAILABLE' "${run_log}"; then
    log "检测到 GPU 不可用，执行诊断命令"
    run_and_log docker exec "${CONTAINER_NAME}" nvidia-smi || true
    log "修复建议: 1) 安装 nvidia-container-toolkit 2) 重启 Docker 3) 用 'docker run --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi' 验证"
    return 1
  fi

  if grep -Eq 'out of memory|CUDA error: out of memory' "${run_log}"; then
    log "检测到 CUDA OOM，调整测试规模后重试"
    run_and_log docker exec "${CONTAINER_NAME}" python - <<'PY'
from pathlib import Path
p = Path('/workspace/output/run_test.py')
s = p.read_text(encoding='utf-8')
s = s.replace('x = torch.randn(1, 3, 8, 256, 256, device=device)', 'x = torch.randn(1, 3, 4, 256, 256, device=device)')
p.write_text(s, encoding='utf-8')
print('patched frames to 4')
PY
    return 1
  fi

  if grep -Eq '权重不存在|未找到可加载参数键|size mismatch|Error\(s\) in loading state_dict' "${run_log}"; then
    log "检测到权重加载异常，尝试使用官方 URL 重新拉取"
    run_and_log curl -fL --retry 5 --retry-delay 5 "https://dl.fbaipublicfiles.com/vjepa2/vitl.pt" -o "${WEIGHT_FILE}"
    return 1
  fi

  log "未识别错误类型。请查看日志: ${run_log}"
  return 1
}

main() {
  ensure_docker
  build_image
  download_weights
  create_container
  generate_run_test

  local max_retry=4
  local i=1
  while [[ ${i} -le ${max_retry} ]]; do
    if apply_fix_and_retry "${i}"; then
      log "部署成功：镜像=${IMAGE_NAME} 容器=${CONTAINER_NAME}"
      log "测试日志: ${OUTPUT_DIR}/run_test_attempt_${i}.log"
      return 0
    fi
    i=$((i + 1))
  done

  log "部署未通过自动调试。请查看日志: ${LOG_FILE}"
  return 1
}

main "$@"
