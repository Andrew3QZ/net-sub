#!/usr/bin/env python3
"""
在 Pi mihomo config.yaml 中修复 GitHub 流量走向。

改动：
1. 删除过时的 `DOMAIN,raw.githubusercontent.com,DIRECT`（家宽直连 GitHub 已不通）
2. rules 增加 github 系列域名走 🚀 Proxy：
   - DOMAIN-SUFFIX,githubusercontent.com,🚀 Proxy   (raw/objects/codeload/githubassets 全家)
   - DOMAIN-SUFFIX,gist.github.com,🚀 Proxy         (gist)
   - DOMAIN-SUFFIX,github.io,🚀 Proxy               (pages)
   注：github.com 已有 DOMAIN-SUFFIX 规则，无需重复
3. proxy-providers 全部加 `proxy: 🚀 Proxy`（订阅拉取走代理，raw 源不再直连超时）
用法: python3 patch_mihomo_git.py /path/to/config.yaml
"""
import sys
import yaml

GIT_RULES = [
    "DOMAIN-SUFFIX,githubusercontent.com,🚀 Proxy",
    "DOMAIN-SUFFIX,gist.github.com,🚀 Proxy",
    "DOMAIN-SUFFIX,github.io,🚀 Proxy",
]

# 要加 proxy 字段的 provider（raw.githubusercontent 源必须走代理）
PROVIDERS_TO_PROXY = ["HongXingVIP", "UserNodeA", "UserNodeB", "UserNodeC", "net-sub"]


def main():
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    rules = cfg.get("rules", [])

    # 1. 删除过时 DIRECT 规则
    removed = [r for r in rules if isinstance(r, str) and "raw.githubusercontent.com" in r and "DIRECT" in r]
    rules = [r for r in rules if not (isinstance(r, str) and "raw.githubusercontent.com" in r and "DIRECT" in r)]
    for r in removed:
        print(f"🗑️  删除: {r}")

    # 2. 插入 github 系列规则（放在 DOMAIN-SUFFIX,github.com 之前）
    insert_at = None
    for i, r in enumerate(rules):
        if isinstance(r, str) and r.startswith("DOMAIN-SUFFIX,github.com,"):
            insert_at = i
            break
    if insert_at is None:
        insert_at = 0
    # 去重
    existing = {r for r in rules if isinstance(r, str)}
    added = [r for r in GIT_RULES if r not in existing]
    rules[insert_at:insert_at] = added
    for r in added:
        print(f"➕ 新增: {r}")
    cfg["rules"] = rules

    # 3. provider 加 proxy
    pps = cfg.get("proxy-providers", {})
    for name in PROVIDERS_TO_PROXY:
        if name in pps and "proxy" not in pps[name]:
            pps[name]["proxy"] = "🚀 Proxy"
            print(f"🔄 {name}: 加 proxy: 🚀 Proxy")

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print(f"✅ 已写入 {path}")


if __name__ == "__main__":
    main()
