#!/usr/bin/env python3
"""
Pi mihomo 代理组结构修复：稳定节点为主力，免费池/红杏降级为应急备用。

背景（2026-08-14 实测）：
- net-sub 免费节点池（1247 节点）测速快但大流量传输不稳（git 全量 clone 断流 early EOF）
- UserNode 节点（HKG 等）延迟略高但稳定
- 用户要求：红杏只做备用

改动：
1. 🚀 Proxy: use 移除 net-sub（只留 UserNodeB/UserNodeC）
2. AI 组（🇸🇬/🇯🇵/🇺🇸/🤖通用备用）: use 移除 net-sub 和 HongXingVIP（只留 UserNodeB/C）
3. 📹 Zoom 会议: use 移除 net-sub（只留 UserNodeB/C）
4. 🛡️ Sentinel: use 移除 net-sub
5. 新增「🆓 免费应急」组（url-test, use: [net-sub]），并挂入 ☁️ Cloudflare 优选和 🐟 Final 的 proxies 选项
用法: python3 patch_mihomo_groups.py /path/to/config.yaml
"""
import sys
import yaml

MAIN_GROUPS = ["🚀 Proxy", "🇸🇬 AI 新加坡", "🇯🇵 AI 日本", "🇺🇸 AI 美国原生", "🤖 AI 通用备用", "📹 Zoom 会议", "🛡️ Sentinel"]
# 这些组移除 net-sub
REMOVE_NETSUB = MAIN_GROUPS
# 这些组额外移除红杏（AI 组只做备用）
REMOVE_HONGXING = ["🇸🇬 AI 新加坡", "🇯🇵 AI 日本", "🇺🇸 AI 美国原生", "🤖 AI 通用备用"]


def main():
    path = sys.argv[1]
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    groups = cfg.get("proxy-groups", [])
    by_name = {g.get("name"): g for g in groups}

    # 1-4. 主力组移除 net-sub / 红杏
    for name in REMOVE_NETSUB:
        g = by_name.get(name)
        if not g:
            continue
        use = g.get("use", [])
        if "net-sub" in use:
            use.remove("net-sub")
            print(f"🔧 {name}: use 移除 net-sub -> {use}")
        if name in REMOVE_HONGXING and "HongXingVIP" in use:
            use.remove("HongXingVIP")
            print(f"🔧 {name}: use 移除 HongXingVIP -> {use}")

    # 5. 新增「🆓 免费应急」组
    if "🆓 免费应急" not in by_name:
        new_group = {
            "name": "🆓 免费应急",
            "type": "url-test",
            "use": ["net-sub"],
            "url": "http://www.gstatic.com/generate_204",
            "interval": 300,
        }
        groups.append(new_group)
        by_name["🆓 免费应急"] = new_group
        print("➕ 新增组: 🆓 免费应急 (use: [net-sub])")

    # 把 🆓 免费应急 挂入 ☁️ Cloudflare 优选 和 🐟 Final 的选项（紧急切换入口）
    for target in ["☁️ Cloudflare 优选", "🐟 Final"]:
        g = by_name.get(target)
        if g and "🆓 免费应急" not in g.get("proxies", []):
            g.setdefault("proxies", []).append("🆓 免费应急")
            print(f"🔗 {target}: proxies 追加 🆓 免费应急")

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print(f"✅ 已写入 {path}")


if __name__ == "__main__":
    main()
