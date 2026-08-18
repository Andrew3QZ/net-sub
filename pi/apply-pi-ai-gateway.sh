#!/usr/bin/env bash
set -euo pipefail

CONFIG="${1:-/home/ubuntu/clash-config/config.yaml}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -f "$CONFIG" ]]; then
  echo "❌ config not found: $CONFIG" >&2
  exit 1
fi

backup="${CONFIG}.backup.net-sub-ai.$(date +%Y%m%d-%H%M%S)"
cp "$CONFIG" "$backup"
echo "✅ backup: $backup"

python3 "$ROOT/scripts/patch_mihomo.py" "$CONFIG"
python3 "$ROOT/scripts/patch_mihomo_nodes.py" "$CONFIG"
python3 "$ROOT/scripts/patch_mihomo_groups.py" "$CONFIG"
python3 "$ROOT/scripts/patch_mihomo_git.py" "$CONFIG"

echo "✅ patched: $CONFIG"
echo "下一步在 Pi 上执行 mihomo 配置校验，例如："
echo "  docker exec mihomo /mihomo -t -f /root/.config/mihomo/config.yaml"
echo "校验通过后再热重载或重启 mihomo。"
