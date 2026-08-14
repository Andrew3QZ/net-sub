#!/usr/bin/env python3
"""
net-sub Telegram 通知

读取 dist/nodes.json + dist/nodes-alive.txt 统计，推送订阅刷新结果到 Telegram。
环境变量:
  TELEGRAM_BOT_TOKEN - bot token（未设置则跳过）
  TELEGRAM_CHAT_ID   - 接收通知的 chat id
用法:
  python3 scripts/telegram_notify.py            # 正常通知
  python3 scripts/telegram_notify.py --failed   # 失败通知（更短）
"""
import argparse
import json
import os
import sys
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(BASE, "dist")


def send_telegram(text, bot_token, chat_id):
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode()
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            ok = 200 <= resp.status < 300
            if ok:
                print("✅ Telegram 推送成功")
            else:
                print(f"❌ Telegram HTTP {resp.status}")
            return ok
    except Exception as e:
        print(f"❌ Telegram 请求失败: {e}")
        return False


def load_stats():
    with open(os.path.join(DIST, "nodes.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def count_alive():
    p = os.path.join(DIST, "nodes-alive.txt")
    if not os.path.exists(p):
        return 0
    with open(p, "r", encoding="utf-8") as f:
        return sum(1 for l in f if l.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--failed", action="store_true", help="失败通知模式")
    args = ap.parse_args()

    bot = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not bot or not chat:
        print("⚠️ 未配置 TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID，跳过推送")
        return 0

    stats = load_stats()
    alive = count_alive()
    proto = stats.get("protocols", {})

    if args.failed:
        text = (
            f"⚠️ *net-sub 订阅刷新失败*\n\n"
            f"时间: {stats.get('timestamp', '-')}\n"
            f"请查看 Actions 日志定位问题。"
        )
    else:
        text = (
            f"🛰️ *net-sub 订阅刷新*\n\n"
            f"🕐 {stats.get('timestamp', '-')} (UTC)\n"
            f"📥 原始: {stats.get('fetched_uris', 0)} → 去重: {stats.get('deduped', 0)}\n"
            f"🩺 存活: {alive} (TCP 探测)\n"
            f"📦 协议: {json.dumps(proto, ensure_ascii=False)}\n"
            f"🌐 订阅: sub.1919444.xyz/shadowrocket.conf"
        )

    return 0 if send_telegram(text, bot, chat) else 1


if __name__ == "__main__":
    sys.exit(main())
