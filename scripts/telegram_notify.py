#!/usr/bin/env python3
"""
net-sub Telegram 通知

读取 dist/nodes.json + dist/probe-stats.json + dist/nodes-alive.txt，推送订阅刷新、节点筛选、Pi 接入状态提示到 Telegram。
环境变量:
  TELEGRAM_BOT_TOKEN - bot token（未设置则跳过）
  TELEGRAM_CHAT_ID   - 接收通知的 chat id
  GITHUB_*           - GitHub Actions 自动注入，用于生成 run/commit 链接
用法:
  python3 scripts/telegram_notify.py            # 正常通知
  python3 scripts/telegram_notify.py --failed   # 失败通知
"""
import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
DIST = BASE / "dist"


def send_telegram(text, bot_token, chat_id):
    # Markdown 容易被域名/emoji/括号破坏，使用纯文本更稳。
    payload = json.dumps({"chat_id": chat_id, "text": text, "disable_web_page_preview": True}).encode()
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            ok = 200 <= resp.status < 300
            print("✅ Telegram 推送成功" if ok else f"❌ Telegram HTTP {resp.status}")
            return ok
    except Exception as e:
        print(f"❌ Telegram 请求失败: {e}")
        return False


def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {} if default is None else default


def count_alive():
    p = DIST / "nodes-alive.txt"
    if not p.exists():
        return 0
    with open(p, "r", encoding="utf-8") as f:
        return sum(1 for l in f if l.strip())


def run_url():
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "Andrew3QZ/net-sub")
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    if run_id:
        return f"{server}/{repo}/actions/runs/{run_id}"
    return f"{server}/{repo}/actions"


def protected_base_url():
    secret = os.environ.get("NET_SUB_PATH_SECRET", "<SUB_PATH_SECRET>")
    return f"https://sub.1919444.xyz/sub/{secret}"


def short_sha():
    sha = os.environ.get("GITHUB_SHA", "")
    return sha[:8] if sha else "-"


def fmt_dict(d):
    if not d:
        return "-"
    return ", ".join(f"{k}:{v}" for k, v in sorted(d.items()))


def build_success_message():
    stats = load_json(DIST / "nodes.json")
    probe = load_json(DIST / "probe-stats.json")
    alive = int(probe.get("alive", count_alive()) or 0)
    tested = int(probe.get("tested", stats.get("deduped", 0)) or 0)
    rate = (alive / tested * 100) if tested else 0

    source_total = stats.get("sources_total", "-")
    source_ok = stats.get("sources_ok", "-")
    fetched_uris = stats.get("fetched_uris", 0)
    deduped = stats.get("deduped", 0)
    proto_all = stats.get("protocols", {})
    proto_alive = probe.get("alive_protocols", {})
    duration = probe.get("duration_seconds", "-")

    return "\n".join([
        "🛰️ net-sub bot 每日/定时扫描完成",
        "",
        f"时间(UTC): {stats.get('timestamp', '-')}",
        f"Commit: {short_sha()}",
        f"Actions: {run_url()}",
        "",
        "节点收集与筛选:",
        f"- 源: {source_ok}/{source_total} 可拉取",
        f"- 原始 URI: {fetched_uris}",
        f"- 去重后: {deduped}",
        f"- TCP 存活: {alive}/{tested} ({rate:.1f}%)，耗时 {duration}s",
        f"- 去重协议: {fmt_dict(proto_all)}",
        f"- 存活协议: {fmt_dict(proto_alive)}",
        "",
        "Pi / mihomo 接入:",
        f"- proxy-provider: {protected_base_url()}/mihomo/proxies.yaml",
        f"- rule-provider: {protected_base_url()}/mihomo/rules/*.yaml",
        "- 建议策略: 主力 UserNodeB/C；net-sub 免费池仅进 🆓 免费应急；Antigravity/AnnBot AI 组走稳定主力，免费池兜底。",
        "",
        "安全边界: 私人订阅和 token 不进 Git；Pi 本地配置只用模板/patch 固化。",
    ])


def build_failed_message():
    stats = load_json(DIST / "nodes.json")
    return "\n".join([
        "⚠️ net-sub bot 扫描/刷新失败",
        "",
        f"时间(UTC): {stats.get('timestamp', '-')}",
        f"Commit: {short_sha()}",
        f"Actions: {run_url()}",
        "",
        "请查看 Actions 日志。常见原因: 上游源不可达、节点格式异常、生成器语法错误、GitHub Pages/提交权限异常。",
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--failed", action="store_true", help="失败通知模式")
    args = ap.parse_args()

    bot = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not bot or not chat:
        print("⚠️ 未配置 TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID，跳过推送")
        return 0

    text = build_failed_message() if args.failed else build_success_message()
    return 0 if send_telegram(text, bot, chat) else 1


if __name__ == "__main__":
    sys.exit(main())
