#!/usr/bin/env python3
"""
net-sub probe_nodes.py — 节点存活探测（TCP 连接测试）

从 dist/nodes.txt 读取节点，并发 TCP 探测 host:port，
输出存活节点到 dist/nodes-alive.txt。

用法:
  python3 scripts/probe_nodes.py [--max-workers 64] [--timeout 4]

注意: 探测结果随时间变化，免费源节点时好时坏；
      探测只做 TCP 连通性检查，不代表代理可用。
"""
import argparse
import concurrent.futures
import json
import os
import socket
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(BASE, "dist")


def host_port_of(uri):
    """从 URI 提取 (host, port)。"""
    try:
        proto = uri.split("://")[0]
        body = uri.split("://")[1]
        if proto == "vmess":
            import base64
            try:
                j = json.loads(base64.b64decode(body.split("#")[0] + "==").decode())
                return j.get("add"), int(j.get("port", 0))
            except Exception:
                return None
        # vless/trojan/ss/ssr: [user@]host:port[?query][#name]
        hp = body.split("@")[-1]
        hp = hp.split("?")[0].split("#")[0]
        host, port = hp.rsplit(":", 1)
        return host, int(port)
    except Exception:
        return None


def probe(uri, timeout=4):
    hp = host_port_of(uri)
    if not hp or not hp[0] or not hp[1]:
        return uri, False
    host, port = hp
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return uri, True
    except Exception:
        return uri, False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-workers", type=int, default=64)
    ap.add_argument("--timeout", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0, help="最多探测 N 个（0=全部）")
    args = ap.parse_args()

    nodes_path = os.path.join(DIST, "nodes.txt")
    with open(nodes_path, "r", encoding="utf-8") as f:
        nodes = [l.strip() for l in f if l.strip()]

    if args.limit:
        nodes = nodes[: args.limit]
    print(f"🔍 探测 {len(nodes)} 个节点 (timeout={args.timeout}s, workers={args.max_workers})...")

    alive = []
    t0 = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as ex:
        for i, (uri, ok) in enumerate(ex.map(lambda u: probe(u, args.timeout), nodes)):
            if ok:
                alive.append(uri)
            if (i + 1) % 500 == 0:
                print(f"  进度 {i+1}/{len(nodes)}，存活 {len(alive)}")

    # 统计
    from collections import Counter
    proto_alive = Counter(u.split("://")[0] for u in alive)
    proto_all = Counter(u.split("://")[0] for u in nodes)

    with open(os.path.join(DIST, "nodes-alive.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(alive) + "\n")

    print(f"\n✅ 存活 {len(alive)}/{len(nodes)} ({(len(alive)/max(len(nodes),1)*100):.1f}%) 耗时 {time.time()-t0:.0f}s")
    print(f"   存活协议: {dict(proto_alive)}")
    print(f"   全部协议: {dict(proto_all)}")


if __name__ == "__main__":
    main()
