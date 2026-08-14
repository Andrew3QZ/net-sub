#!/usr/bin/env python3
"""
在 Pi mihomo config.yaml 中接入 net-sub 节点池（proxy-provider）。

改动（最小、可回退）：
1. proxy-providers 追加 net-sub（url 指向 sub.1919444.xyz/mihomo/proxies.yaml）
2. 所有 url-test 组的 use 列表追加 net-sub（红杏+UserNode+net-sub 统一选优）
   - 若组已有 net-sub 则跳过
用法: python3 patch_mihomo_nodes.py /path/to/config.yaml
"""
import sys
import yaml

NETSUB_PROVIDER = {
    "type": "http",
    "url": "https://sub.1919444.xyz/mihomo/proxies.yaml",
    "path": "./providers/net-sub.yaml",
    "interval": 21600,
    "health-check": {
        "enable": True,
        "interval": 1800,
        "lazy": True,
        "url": "http://www.gstatic.com/generate_204",
    },
}


def main():
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # --- 1. proxy-providers 追加 ---
    pps = cfg.setdefault("proxy-providers", {})
    if "net-sub" in pps:
        print("⏭️  net-sub provider 已存在")
    else:
        pps["net-sub"] = NETSUB_PROVIDER
        print("✅ proxy-providers 新增: net-sub")

    # --- 2. url-test 组 use 追加 ---
    changed = []
    for g in cfg.get("proxy-groups", []):
        if g.get("type") != "url-test":
            continue
        use = g.setdefault("use", [])
        if "net-sub" not in use:
            use.append("net-sub")
            changed.append(g.get("name"))
    print(f"✅ url-test 组 use 追加 net-sub: {changed}")

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print(f"✅ 已写入 {path}")


if __name__ == "__main__":
    main()
