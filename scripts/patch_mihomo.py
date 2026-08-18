#!/usr/bin/env python3
"""
在 Pi mihomo config.yaml 中接入 net-sub 共享规则集。

改动（最小、可回退）：
1. rule-providers 追加 6 个远程 provider（ai/meetings/discord/docker/direct-domains/direct-ips）
2. rules 尾部 cn-ip 之后、MATCH 之前插入 RULE-SET 引用
   - ai/meetings 引用现有专线组；discord/docker 引用 🚀 Proxy（Pi 无专门组，零新增）
   - direct-domains/direct-ips 引用 DIRECT
用法: python3 patch_mihomo.py /path/to/config.yaml
"""
import os
import sys
import yaml

SECRET = os.environ.get("NET_SUB_PATH_SECRET", "")
if not SECRET:
    raise SystemExit("NET_SUB_PATH_SECRET 未设置；请在 Pi 上通过环境变量注入，不要写入 Git")
SUBDOMAIN = f"https://sub.1919444.xyz/sub/{SECRET}"

PROVIDERS = {
    "ai":            {"behavior": "classical", "group": "🤖 国外 AI 专线"},
    "meetings":      {"behavior": "classical", "group": "📹 Zoom 会议"},
    "discord":       {"behavior": "classical", "group": "🚀 Proxy"},
    "docker":        {"behavior": "classical", "group": "🚀 Proxy"},
    "direct-domains": {"behavior": "classical", "group": "DIRECT"},
    "direct-ips":    {"behavior": "classical", "group": "DIRECT"},
}


def main():
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # --- 1. rule-providers 追加 ---
    rps = cfg.setdefault("rule-providers", {})
    existing = set(rps.keys())
    added = []
    for name, spec in PROVIDERS.items():
        if name in existing:
            print(f"  ⏭️  {name} 已存在，跳过")
            continue
        rps[name] = {
            "type": "http",
            "behavior": spec["behavior"],
            "format": "yaml",
            "url": f"{SUBDOMAIN}/rules/{name}.yaml",
            "path": f"./ruleset/net-sub-{name}.yaml",
            "interval": 21600,
            "proxy": "🚀 Proxy",
        }
        added.append(name)
    print(f"✅ rule-providers 新增: {added}")

    # --- 2. rules 插入 RULE-SET 引用 ---
    rules = cfg.setdefault("rules", [])
    # 找到 cn-ip RULE-SET 的位置（在其后插入），或 MATCH 前
    insert_at = None
    for i, r in enumerate(rules):
        if isinstance(r, str) and r.startswith("RULE-SET,cn-ip"):
            insert_at = i + 1
            break
    if insert_at is None:
        for i, r in enumerate(rules):
            if isinstance(r, str) and r.startswith("MATCH"):
                insert_at = i
                break
    if insert_at is None:
        insert_at = len(rules)

    new_rules = []
    for name, spec in PROVIDERS.items():
        line = f"RULE-SET,{name},{spec['group']}"
        if name == "direct-ips":
            line = f"RULE-SET,{name},DIRECT,no-resolve"
        # 已有 net-sub 引用则先移除（避免重复）——在原列表上过滤后挂回 cfg
        rules = [r for r in rules if not (isinstance(r, str) and r.startswith(f"RULE-SET,{name},"))]
        new_rules.append(line)
    cfg["rules"] = rules  # 关键：重新挂回，否则插入丢失

    # 重新定位（rules 可能已变）
    insert_at = None
    for i, r in enumerate(rules):
        if isinstance(r, str) and r.startswith("RULE-SET,cn-ip"):
            insert_at = i + 1
            break
    if insert_at is None:
        for i, r in enumerate(rules):
            if isinstance(r, str) and r.startswith("MATCH"):
                insert_at = i
                break
    if insert_at is None:
        insert_at = len(rules)
    rules[insert_at:insert_at] = new_rules

    print(f"✅ rules 插入 {len(new_rules)} 条 RULE-SET 于位置 {insert_at}:")
    for r in new_rules:
        print(f"   {r}")

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print(f"✅ 已写入 {path}")


if __name__ == "__main__":
    main()
