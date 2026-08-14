#!/usr/bin/env python3
"""
net-sub generate.py — 从共享规则清单 + 节点清单生成双端产物

产物:
  dist/shadowrocket.conf              # iOS Shadowrocket 完整配置（含节点+规则）
  dist/mihomo/proxies.yaml            # mihomo proxy-provider（节点）
  dist/mihomo/rules/<name>.yaml       # mihomo rule-provider（共享规则）
  dist/mihomo/README.md               # Pi 接入说明
"""
import os
import sys
import time
from collections import Counter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = os.path.join(BASE, "rules")
DIST = os.path.join(BASE, "dist")
MIHOMO = os.path.join(DIST, "mihomo")

# 规则文件 → (shadow 分组名, mihomo 分组名, mihomo rule-provider 名)
RULE_SETS = [
    ("ai.txt",       "AI-Services", "🤖 国外 AI 专线", "ai"),
    ("meetings.txt", "Meetings",    "📹 Zoom 会议",    "meetings"),
    ("discord.txt",  "Discord",     "Discord",         "discord"),
    ("docker.txt",   "Docker",      "🐳 Docker",       "docker"),
    ("direct-domains.txt", "DIRECT", "DIRECT",          "direct-domains"),
    ("direct-ips.txt",     "DIRECT", "DIRECT",          "direct-ips"),
]


def load_rules(name):
    path = os.path.join(RULES, name)
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            items.append(line)
    return items


def parse_nodes(path):
    """读 dist/nodes.txt，解析节点为 (uri, 摘要) 列表。"""
    nodes = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            nodes.append(line)
    return nodes


def node_summary(uri):
    """从 URI 提取可读名称：协议 + host:port。"""
    try:
        proto = uri.split("://")[0]
        body = uri.split("://")[1]
        if proto == "vmess":
            return f"{proto}://{body[:40]}"
        hostport = body.split("@")[-1]
        host = hostport.split(":")[0]
        port = hostport.split(":")[1].split("?")[0]
        return f"{proto}://{host}:{port}"
    except Exception:
        return uri[:60]


def uri_to_mihomo(uri):
    """
    将 vless/trojan/ss URI 转为 mihomo proxy yaml 条目。
    返回 dict 或 None（无法解析）。
    """
    from urllib.parse import urlparse, parse_qs, unquote
    try:
        proto = uri.split("://")[0]
        body = uri.split("://")[1]

        if proto in ("vless", "trojan"):
            # user@host:port?query
            at = body.find("@")
            if at < 0:
                return None
            user = body[:at]
            rest = body[at + 1:]
            q = rest.find("?")
            if q < 0:
                host, port = rest.rsplit(":", 1)
                query = {}
            else:
                hostport, qs = rest[:q], rest[q + 1:]
                host, port = hostport.rsplit(":", 1)
                query = parse_qs(qs)
            entry = {
                "name": f"{proto}-{host}-{port}",
                "type": proto,
                "server": host,
                "port": int(port),
                "uuid": user,
            }
            if query.get("security", ["none"])[0] == "tls":
                entry["tls"] = True
                if query.get("sni"):
                    entry["servername"] = query["sni"][0]
            if query.get("type", ["none"])[0] == "ws":
                entry["network"] = "ws"
                if query.get("path"):
                    # 去掉 #fragment（节点名），只保留真实 path
                    p = query["path"][0].split("#")[0]
                    entry["ws-opts"] = {"path": p}
                if query.get("host"):
                    entry["ws-opts"] = {**entry.get("ws-opts", {}), "headers": {"Host": query["host"][0].split("#")[0]}}
            if query.get("fp"):
                entry["client-fingerprint"] = query["fp"][0]
            return entry

        elif proto == "ss":
            # ss://method:pass@host:port 或 ss://base64(method:pass)@host:port
            import base64
            if "@" in body:
                auth, hostport = body.rsplit("@", 1)
                if ":" not in auth:
                    try:
                        auth = base64.b64decode(auth + "==").decode()
                    except Exception:
                        return None
                method, password = auth.split(":", 1)
                host, port = hostport.rsplit(":", 1)
                return {
                    "name": f"ss-{host}-{port}",
                    "type": "ss",
                    "server": host,
                    "port": int(port),
                    "cipher": method,
                    "password": password,
                }
        return None
    except Exception:
        return None


def gen_shadowrocket(nodes, rules_map):
    """生成 Shadowrocket 完整配置。"""
    header_date = time.strftime("%Y-%m-%d %H:%M")
    lines = []
    lines.append("# net-sub Shadowrocket 配置（自动生成，勿手改）")
    lines.append(f"# 生成时间: {header_date} UTC")
    lines.append(f"# 节点数: {len(nodes)}")
    lines.append("")
    lines.append("[General]")
    lines.append("bypass-system = true")
    lines.append("skip-proxy = 192.168.0.0/16,10.0.0.0/8,172.16.0.0/12,localhost,*.local,captive.apple.com,9985678.xyz")
    lines.append("bypass-tun = 10.0.0.0/8,100.64.0.0/10,127.0.0.0/8,169.254.0.0/16,172.16.0.0/12,192.0.0.0/24,192.0.2.0/24,192.88.99.0/24,192.168.0.0/16,198.18.0.0/15,198.51.100.0/24,203.0.113.0/24,224.0.0.0/4,255.255.255.255/32")
    lines.append("dns-server = system, 223.5.5.5, 119.29.29.29")
    lines.append("ipv6 = false")
    lines.append("prefer-ipv6 = false")
    lines.append("dns-fallback-system = true")
    lines.append("dns-direct-system = true")
    lines.append("icmp-auto-reply = true")
    lines.append("private-ip-answer = true")
    lines.append("udp-policy-not-supported-behaviour = REJECT")
    lines.append("skip-cert-verify = true")
    lines.append("")
    lines.append("[Proxy]")
    for uri in nodes:
        lines.append(uri)
    lines.append("")
    lines.append("[Proxy Group]")
    lines.append("AI-Services = select, PROXY")
    lines.append("Meetings = select, PROXY")
    lines.append("Discord = select, Meetings, PROXY")
    lines.append("Docker = select, DIRECT, PROXY")
    lines.append("Proxy = select, PROXY, AI-Services, Meetings, DIRECT")
    lines.append("")
    lines.append("[Rule]")
    # 直连 IP 优先
    for cidr in rules_map.get("direct-ips", []):
        lines.append(f"IP-CIDR,{cidr},DIRECT")
    # 局域网
    lines.append("IP-CIDR,192.168.31.0/24,DIRECT")
    lines.append("IP-CIDR,192.168.0.0/16,DIRECT")
    lines.append("IP-CIDR,10.0.0.0/8,DIRECT")
    lines.append("IP-CIDR,172.16.0.0/12,DIRECT")
    lines.append("DOMAIN-SUFFIX,1919444.xyz,DIRECT")
    lines.append("DOMAIN-SUFFIX,9985678.xyz,DIRECT")
    # 分组规则
    group_map = {
        "ai": "AI-Services",
        "meetings": "Meetings",
        "discord": "Discord",
        "docker": "Docker",
    }
    for name, domains in rules_map.items():
        g = group_map.get(name)
        if not g:
            continue
        for d in domains:
            lines.append(f"DOMAIN-SUFFIX,{d},{g}")
    # Discord keyword 兜底
    lines.append("DOMAIN-KEYWORD,discord,Discord")
    # 直连域名（direct-domains 已在上面以 DOMAIN-SUFFIX 输出? 单独处理）
    for d in rules_map.get("direct-domains", []):
        lines.append(f"DOMAIN-SUFFIX,{d},DIRECT")
    lines.append("GEOIP,CN,DIRECT")
    lines.append("FINAL,Proxy")
    lines.append("")
    lines.append("[Host]")
    lines.append("localhost = 127.0.0.1")
    lines.append("")
    return "\n".join(lines)


def gen_mihomo(nodes):
    """生成 mihomo proxy-provider yaml。"""
    proxies = []
    failed = 0
    for uri in nodes:
        e = uri_to_mihomo(uri)
        if e:
            proxies.append(e)
        else:
            failed += 1
    # 重名处理
    seen = set()
    for p in proxies:
        n = p["name"]
        i = 2
        while n in seen:
            n = f"{p['name']}-{i}"
            i += 1
        p["name"] = n
        seen.add(n)
    return proxies, failed


def gen_rule_provider(name, domains, is_ip=False):
    """生成 mihomo rule-provider yaml。"""
    behavior = "ipcidr" if is_ip else "domain"
    lines = [
        "payload:",
    ]
    for d in domains:
        if is_ip:
            lines.append(f"  - '{d}'")
        else:
            lines.append(f"  - '{d}'")
    return "\n".join(lines), behavior


def main():
    os.makedirs(MIHOMO, exist_ok=True)
    os.makedirs(os.path.join(MIHOMO, "rules"), exist_ok=True)

    # 1. 规则清单
    rules_map = {}
    for fname, shadow_group, mihomo_group, provider_name in RULE_SETS:
        rules_map[fname.replace(".txt", "")] = load_rules(fname)

    # 2. 节点
    nodes_path = os.path.join(DIST, "nodes.txt")
    if not os.path.exists(nodes_path):
        print("❌ dist/nodes.txt 不存在，先跑 fetch_sources.py")
        sys.exit(1)
    nodes = parse_nodes(nodes_path)
    print(f"📦 节点: {len(nodes)}")

    # 3. Shadowrocket
    sr_conf = gen_shadowrocket(nodes, rules_map)
    sr_path = os.path.join(DIST, "shadowrocket.conf")
    with open(sr_path, "w", encoding="utf-8") as f:
        f.write(sr_conf)
    print(f"✅ dist/shadowrocket.conf ({len(sr_conf)} bytes)")

    # 4. mihomo proxies
    proxies, failed = gen_mihomo(nodes)
    px_path = os.path.join(MIHOMO, "proxies.yaml")
    with open(px_path, "w", encoding="utf-8") as f:
        f.write("proxies:\n")
        for p in proxies:
            f.write(f"  - name: \"{p['name']}\"\n")
            f.write(f"    type: {p['type']}\n")
            f.write(f"    server: \"{p['server']}\"\n")
            f.write(f"    port: {p['port']}\n")
            if p["type"] in ("vless", "trojan"):
                f.write(f"    uuid: \"{p['uuid']}\"\n")
                if "tls" in p and p["tls"]:
                    f.write("    tls: true\n")
                    if p.get("servername"):
                        f.write(f"    servername: \"{p['servername']}\"\n")
                if p.get("network") == "ws":
                    f.write("    network: ws\n")
                    if p.get("ws-opts"):
                        f.write("    ws-opts:\n")
                        for k, v in p["ws-opts"].items():
                            if isinstance(v, dict):
                                f.write(f"      {k}:\n")
                                for kk, vv in v.items():
                                    f.write(f"        \"{kk}\": \"{vv}\"\n")
                            else:
                                f.write(f"      \"{k}\": \"{v}\"\n")
                if p.get("client-fingerprint"):
                    f.write(f"    client-fingerprint: \"{p['client-fingerprint']}\"\n")
            elif p["type"] == "ss":
                f.write(f"    cipher: \"{p['cipher']}\"\n")
                f.write(f"    password: \"{p['password']}\"\n")
    print(f"✅ dist/mihomo/proxies.yaml ({len(proxies)} 转换成功, {failed} 跳过)")

    # 5. mihomo rule providers
    for fname, shadow_group, mihomo_group, provider_name in RULE_SETS:
        key = fname.replace(".txt", "")
        items = rules_map.get(key, [])
        is_ip = key == "direct-ips"
        content, behavior = gen_rule_provider(provider_name, items, is_ip)
        rp_path = os.path.join(MIHOMO, "rules", f"{provider_name}.yaml")
        with open(rp_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ dist/mihomo/rules/{provider_name}.yaml ({behavior}, {len(items)} 条)")

    # 6. mihomo README
    readme = f"""# net-sub mihomo 接入说明（自动生成）

## 节点订阅（proxy-provider）
```yaml
proxy-providers:
  net-sub:
    type: http
    url: https://<域名>/mihomo/proxies.yaml
    interval: 21600
    health-check:
      enable: true
      interval: 1800
      url: http://www.gstatic.com/generate_204
```

## 规则集（rule-provider）
```yaml
rule-providers:
  ai:
    type: http
    behavior: domain
    format: yaml
    url: https://<域名>/mihomo/rules/ai.yaml
    interval: 21600
  meetings:
    type: http
    behavior: domain
    format: yaml
    url: https://<域名>/mihomo/rules/meetings.yaml
    interval: 21600
  discord:
    type: http
    behavior: domain
    format: yaml
    url: https://<域名>/mihomo/rules/discord.yaml
    interval: 21600
  docker:
    type: http
    behavior: domain
    format: yaml
    url: https://<域名>/mihomo/rules/docker.yaml
    interval: 21600
  direct-domains:
    type: http
    behavior: domain
    format: yaml
    url: https://<域名>/mihomo/rules/direct-domains.yaml
    interval: 21600
  direct-ips:
    type: http
    behavior: ipcidr
    format: yaml
    url: https://<域名>/mihomo/rules/direct-ips.yaml
    interval: 21600
```

## 规则引用顺序（放在 cn-domain/cn-ip 之后、MATCH 之前）
```yaml
rules:
  - RULE-SET,ai,🤖 国外 AI 专线
  - RULE-SET,meetings,📹 Zoom 会议
  - RULE-SET,discord,Discord
  - RULE-SET,docker,🐳 Docker
  - RULE-SET,direct-domains,DIRECT
  - RULE-SET,direct-ips,DIRECT,no-resolve
```
生成时间: {time.strftime("%Y-%m-%d %H:%M")} UTC
"""
    with open(os.path.join(MIHOMO, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme)
    print("✅ dist/mihomo/README.md")


if __name__ == "__main__":
    main()
