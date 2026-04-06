#!/usr/bin/env bash
# 修复全局 npm 安装的 openclaw：飞书插件依赖未正确提升到可解析路径时，
# 日志会出现: Cannot find module '@larksuiteoapi/node-sdk'，导致所有飞书 Bot 无响应。
#
# 用法（本机）:
#   bash scripts/repair-openclaw-feishu-deps.sh
#
# 需要写入全局 node_modules，请在本机信任环境下执行；执行后请重启 Gateway（LaunchAgent 或手动）。

set -euo pipefail

OW="${OPENCLAW_NPM_ROOT:-/Users/mac/.npm-global/lib/node_modules/openclaw}"
FEISHU_EXT="$OW/dist/extensions/feishu"

if [[ ! -d "$OW" ]]; then
  echo "未找到 openclaw 目录: $OW" >&2
  echo "可设置: OPENCLAW_NPM_ROOT=/path/to/lib/node_modules/openclaw" >&2
  exit 1
fi

if [[ ! -d "$FEISHU_EXT/node_modules" ]]; then
  echo "未找到 $FEISHU_EXT/node_modules，请先在该目录执行: npm install" >&2
  exit 1
fi

echo "合并飞书扩展依赖 -> $OW/node_modules ..."
rsync -a "$FEISHU_EXT/node_modules/" "$OW/node_modules/"

echo "校验飞书扩展可加载 ..."
cd "$OW"
node --input-type=module -e "import('./dist/extensions/feishu/index.js').then(() => console.log('OK: feishu extension loads')).catch((e) => { console.error(e); process.exit(1); })"

echo ""
echo "请重启 Gateway，例如:"
echo "  launchctl kickstart -k gui/\$(id -u)/ai.openclaw.gateway"
echo "  # 或你的 plist 标签"
