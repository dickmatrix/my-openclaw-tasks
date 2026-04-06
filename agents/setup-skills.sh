#!/usr/bin/env bash
# =============================================================================
# setup-skills.sh
# 为 researcher / validator / coder / auditor 四个 Agent 安装技能，
# 并检查 .env 中所有必需的 API Key 是否已配置。
# 用法：bash agents/setup-skills.sh [--dry-run]
# =============================================================================

set -euo pipefail

# ── 颜色 ─────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ── 路径解析 ──────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
  echo -e "${YELLOW}[DRY-RUN] 仅预演，不执行实际安装${RESET}"
fi

# ── 工具检查 ──────────────────────────────────────────────────────────────────
check_deps() {
  local missing=()
  for cmd in clawhub node; do
    if ! command -v "$cmd" &>/dev/null; then
      missing+=("$cmd")
    fi
  done
  if [[ ${#missing[@]} -gt 0 ]]; then
    echo -e "${RED}[ERROR] 缺少必要命令：${missing[*]}${RESET}"
    echo -e "        请先安装：${BOLD}npm i -g clawhub${RESET}"
    exit 1
  fi
}

# ── .env 加载 ─────────────────────────────────────────────────────────────────
load_env() {
  if [[ -f "${ENV_FILE}" ]]; then
    # 仅导出非注释、非空行的 KEY=VALUE
    set -o allexport
    # shellcheck disable=SC1090
    source <(grep -E '^[A-Z_][A-Z0-9_]*=' "${ENV_FILE}" | grep -v '^#')
    set +o allexport
  else
    echo -e "${YELLOW}[WARN] 未找到 .env 文件：${ENV_FILE}${RESET}"
  fi
}

# ── API Key 检查 ──────────────────────────────────────────────────────────────
#
# 每条记录格式：  "SKILL名称|ENV变量名|描述/用途"
#
# jina-reader   → JINA_API_KEY      (Jina Reader / web-fetch 的 API key)
# pii-guardian  → OPENAI_API_KEY 或 GLM_API_KEY（PII 扫描模型，可二选一）
# git-patch     → GITHUB_TOKEN      (GitHub API，用于推送 patch / PR)
# docker-executor → DOCKER_HOST 可选，但不是密钥；无硬性 key 要求
#
REQUIRED_KEYS=(
  "jina-reader|JINA_API_KEY|Jina Reader 需要此 Key 才能抓取网页内容（https://jina.ai/api-key）"
  "pii-guardian|OPENAI_API_KEY|PII Guardian 默认使用 OpenAI 进行隐私扫描（可改用 GLM_API_KEY）"
  "git-patch|GITHUB_TOKEN|Git Patch 推送到 GitHub / 创建 PR 时需要个人访问令牌"
)

check_api_keys() {
  echo ""
  echo -e "${BOLD}${CYAN}━━━ API Key 检查 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
  local missing_count=0

  for entry in "${REQUIRED_KEYS[@]}"; do
    IFS='|' read -r skill_name env_var description <<< "$entry"
    local value="${!env_var:-}"

    if [[ -z "$value" ]]; then
      echo -e "  ${RED}✗ [MISSING]${RESET}  ${BOLD}${env_var}${RESET}"
      echo -e "            技能：${skill_name}"
      echo -e "            说明：${description}"
      echo -e "            → 请在 ${ENV_FILE} 中补充：${BOLD}${env_var}=your_key_here${RESET}"
      echo ""
      ((missing_count++))
    else
      # 仅打印 key 的前 8 位，其余用 * 遮盖
      local masked="${value:0:8}$(printf '%0.s*' {1..12})"
      echo -e "  ${GREEN}✓ [OK]${RESET}      ${BOLD}${env_var}${RESET} = ${masked}"
      echo -e "            技能：${skill_name}"
    fi
  done

  # docker-executor 不需要 API key，但提示 DOCKER_HOST 可选配置
  echo ""
  echo -e "  ${CYAN}ℹ [INFO]${RESET}   ${BOLD}docker-executor${RESET} 无需 API Key"
  local docker_host="${DOCKER_HOST:-}"
  if [[ -n "$docker_host" ]]; then
    echo -e "            DOCKER_HOST = ${docker_host}  ${GREEN}(已配置)${RESET}"
  else
    echo -e "            DOCKER_HOST 未设置，将使用系统默认 Docker socket"
    echo -e "            如需远程 Docker，请在 .env 中设置：${BOLD}DOCKER_HOST=tcp://host:2376${RESET}"
  fi

  echo ""
  echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

  if [[ $missing_count -gt 0 ]]; then
    echo -e "${YELLOW}[WARN] 共有 ${missing_count} 个 API Key 缺失，请补全后重新运行本脚本。${RESET}"
    echo -e "       缺失的 Key 不会阻止安装，但对应技能在运行时将会报错。"
    echo ""
  else
    echo -e "${GREEN}[OK] 所有必需的 API Key 均已配置。${RESET}"
    echo ""
  fi
}

# ── 技能安装 ──────────────────────────────────────────────────────────────────
#
# 格式：  "skill-slug|目标 Agent 列表（逗号分隔）|安装目标目录（相对 PROJECT_ROOT）"
#
# 安装策略：
#   - researcher  → jina-reader（网页抓取）
#   - validator   → pii-guardian（隐私数据扫描）
#   - coder       → git-patch + docker-executor（代码执行 & 发布）
#   - auditor     → pii-guardian + git-patch（合规审计）
#
SKILLS=(
  "jina-reader|researcher|agents/researcher"
  "pii-guardian|validator,auditor|agents/validator agents/auditor"
  "git-patch|coder,auditor|agents/worker-code agents/auditor"
  "docker-executor|coder|agents/worker-code"
)

install_skill_to_dir() {
  local slug="$1"
  local target_dir="$2"
  local skills_dir="${PROJECT_ROOT}/${target_dir}/skills"

  mkdir -p "${skills_dir}"

  echo -e "    ${CYAN}→${RESET} 目标：${BOLD}${target_dir}/skills/${RESET}"

  if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "    ${YELLOW}[DRY-RUN]${RESET} clawhub install ${slug} --workdir ${skills_dir} --force"
    return 0
  fi

  if clawhub install "${slug}" --workdir "${PROJECT_ROOT}/${target_dir}" --force 2>&1; then
    echo -e "    ${GREEN}✓ 安装成功${RESET}"
  else
    echo -e "    ${RED}✗ 安装失败（slug: ${slug}）—— 请检查网络或 slug 是否正确${RESET}"
    # 不 exit，继续安装其他技能
  fi
}

install_all_skills() {
  echo ""
  echo -e "${BOLD}${CYAN}━━━ 技能安装 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"

  for entry in "${SKILLS[@]}"; do
    IFS='|' read -r slug agents_label target_dirs_str <<< "$entry"

    echo ""
    echo -e "  ${BOLD}▶ ${slug}${RESET}  （供 Agent：${agents_label}）"

    # target_dirs_str 可能包含多个目录（空格分隔）
    IFS=' ' read -ra target_dirs <<< "$target_dirs_str"
    for target_dir in "${target_dirs[@]}"; do
      install_skill_to_dir "${slug}" "${target_dir}"
    done
  done

  echo ""
  echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}"
}

# ── 汇总提示 ──────────────────────────────────────────────────────────────────
print_summary() {
  echo -e "${BOLD}${GREEN}✔ 完成！${RESET}"
  echo ""
  echo -e "下一步："
  echo -e "  1. 如有 API Key 缺失，请编辑 ${BOLD}.env${RESET} 补全后重新运行本脚本"
  echo -e "  2. 在 openclaw.json 的 skills.entries 中为各技能配置 apiKey"
  echo -e "  3. 重启 Gateway 使新技能生效：${BOLD}openclaw gateway restart${RESET}"
  echo -e "  4. 验证：${BOLD}openclaw skills list --eligible${RESET}"
  echo ""
}

# ── 入口 ──────────────────────────────────────────────────────────────────────
main() {
  echo ""
  echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════════════╗${RESET}"
  echo -e "${BOLD}${CYAN}║   OpenClaw · Agent 技能安装脚本                                 ║${RESET}"
  echo -e "${BOLD}${CYAN}║   目标 Agent：researcher / validator / coder / auditor          ║${RESET}"
  echo -e "${BOLD}${CYAN}║   技    能：jina-reader · pii-guardian · git-patch · docker-executor ║${RESET}"
  echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════════════════════════╝${RESET}"
  echo ""

  check_deps
  load_env
  check_api_keys
  install_all_skills
  print_summary
}

main "$@"