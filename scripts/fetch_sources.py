#!/usr/bin/env python3
"""
net-sub fetch_sources.py — 拉取上游节点源，解析、去重，输出节点清单

用法:
  python3 scripts/fetch_sources.py                 # 正常模式（拉取 sources/nodes.txt）
  python3 scripts/fetch_sources.py --input FILE    # 离线模式（用本地文件，跳过网络）

输出:
  dist/nodes.txt     # 去重后的原始 URI 列表
  dist/nodes.json    # 统计信息
"""
import argparse
import concurrent.futures
import json
import os
import sys
import time
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES_FILE = os.path.join(BASE, "sources", "nodes.txt")
DIST = os.path.join(BASE, "dist")


def load_sources(path):
    urls = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    return urls


def fetch(url, timeout=30):
    """拉取单个源，返回文本；失败返回 None。"""
    req = urllib.request.Request(url, headers={"User-Agent": "net-sub/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            # 优先 utf-8，失败回退
            for enc in ("utf-8", "latin-1"):
                try:
                    return data.decode(enc)
                except UnicodeDecodeError:
                    continue
            return data.decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ⚠️  {url} 失败: {e}")
        return None


def parse_uris(text):
    """从文本中提取合法代理 URI（vless/vmess/trojan/ss/ssr）。"""
    import re
    uris = []
    # 可能是 base64 整体编码（部分订阅）
    stripped = text.strip().replace("\n", "")
    if stripped and len(stripped) > 40 and not stripped.startswith(("vless://", "vmess://", "trojan://", "ss://", "ssr://")):
        try:
            import base64
            decoded = base64.b64decode(stripped + "=" * (-len(stripped) % 4)).decode("utf-8", errors="replace")
            if any(p in decoded for p in ("://", "\n")):
                text = decoded
        except Exception:
            pass
    for line in text.splitlines():
        line = line.strip()
        if any(line.startswith(p) for p in ("vless://", "vmess://", "trojan://", "ss://", "ssr://")):
            uris.append(line)
        else:
            # 一行可能包含多个 URI（空格分隔）
            for tok in line.split():
                if any(tok.startswith(p) for p in ("vless://", "vmess://", "trojan://", "ss://", "ssr://")):
                    uris.append(tok)
    return uris


def normalize(uri):
    """去重 key：vless/trojan 用 proto://host:port（协议不同不算重复），其他用完整 URI。"""
    if uri.startswith(("vless://", "trojan://")):
        try:
            proto = uri.split("://")[0]
            host = uri.split("@")[1].split(":")[0]
            port = uri.split("@")[1].split(":")[1].split("?")[0]
            return f"{proto}://{host}:{port}"
        except Exception:
            return uri
    return uri


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", help="离线模式：用本地文件代替网络拉取")
    ap.add_argument("--max-sources", type=int, default=20, help="最多拉取源数")
    args = ap.parse_args()

    os.makedirs(DIST, exist_ok=True)

    if args.input:
        print(f"📂 离线模式：读取 {args.input}")
        with open(args.input, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        uris = parse_uris(text)
        fetched = 0
        stats = {"mode": "offline", "input": args.input}
    else:
        sources = load_sources(SOURCES_FILE)[: args.max_sources]
        print(f"🌐 拉取 {len(sources)} 个源...")
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(fetch, u): u for u in sources}
            for fut in concurrent.futures.as_completed(futs):
                url = futs[fut]
                txt = fut.result()
                if txt is not None:
                    results[url] = txt
        uris = []
        for url, txt in results.items():
            u = parse_uris(txt)
            print(f"  ✅ {url} → {len(u)} 节点")
            uris.extend(u)
        fetched = len(results)
        stats = {"mode": "online", "sources_total": len(sources), "sources_ok": fetched}

    # 去重
    seen = set()
    deduped = []
    for u in uris:
        k = normalize(u)
        if k not in seen:
            seen.add(k)
            deduped.append(u)

    # 协议分布
    from collections import Counter
    proto = Counter(u.split("://")[0] for u in deduped)

    stats.update({
        "fetched_uris": len(uris),
        "deduped": len(deduped),
        "protocols": dict(proto),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })

    with open(os.path.join(DIST, "nodes.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(deduped) + "\n")
    with open(os.path.join(DIST, "nodes.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成: 原始 {len(uris)} → 去重后 {len(deduped)} 节点")
    print(f"   协议分布: {dict(proto)}")
    print(f"   产物: dist/nodes.txt, dist/nodes.json")


if __name__ == "__main__":
    main()
