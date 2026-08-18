#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${NET_SUB_BASE_URL:-https://sub.1919444.xyz}"
API="${MIHOMO_API:-http://127.0.0.1:9090}"

echo "== net-sub remote artifacts =="
for path in \
  /mihomo/proxies.yaml \
  /mihomo/rules/ai.yaml \
  /mihomo/rules/docker.yaml \
  /mihomo/rules/discord.yaml \
  /mihomo/rules/meetings.yaml; do
  code=$(curl -L -sS -o /tmp/net-sub-check.out -w '%{http_code}' "$BASE_URL$path" || true)
  bytes=$(wc -c < /tmp/net-sub-check.out | tr -d ' ')
  echo "$code $bytes bytes $BASE_URL$path"
done

echo
if curl -sS "$API/version" >/tmp/mihomo-version.json 2>/dev/null; then
  echo "== mihomo API =="
  cat /tmp/mihomo-version.json
  echo
  echo "== providers summary =="
  curl -sS "$API/providers/proxies" | python3 - <<'PY' || true
import json,sys
try:
    data=json.load(sys.stdin).get('providers',{})
    for name in ['UserNodeB','UserNodeC','net-sub','HongXingVIP']:
        p=data.get(name)
        if p:
            print(f"{name}: proxies={len(p.get('proxies',[]))} updatedAt={p.get('updatedAt','-')}")
except Exception as e:
    print(f"provider summary unavailable: {e}")
PY
else
  echo "⚠️ mihomo API unavailable at $API (remote artifact checks above still valid)"
fi
