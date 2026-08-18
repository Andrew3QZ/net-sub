#!/usr/bin/env bash
set -euo pipefail
CONFIG="${1:-/home/ubuntu/clash-config/config.yaml}"
BACKUP="${2:-}"
if [[ -z "$BACKUP" || ! -f "$BACKUP" ]]; then
  echo "用法: bash pi/rollback.sh /path/to/config.yaml /path/to/config.yaml.backup..." >&2
  exit 1
fi
cp "$BACKUP" "$CONFIG"
echo "✅ restored $CONFIG from $BACKUP"
echo "请重新校验并 reload/restart mihomo。"
