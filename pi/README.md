# Pi AI Gateway 固化层

本目录用于把 GitHub 上每天/每 6 小时筛选出的 net-sub 节点池，稳定接入 Pi mihomo，并固化 AnnBot/Antigravity 的 AI 网络访问策略。

## 分层职责

```text
GitHub Actions refresh.yml
  fetch_sources.py → probe_nodes.py → generate.py → telegram_notify.py
        ↓
Cloudflare Pages: sub.1919444.xyz
        ↓
Pi mihomo proxy-provider / rule-provider
        ↓
AI / Antigravity / GitHub / Zoom / Docker 分组
```

- GitHub 端负责：公开免费节点源拉取、TCP 存活筛选、产物生成、Telegram 通知。
- Pi 端负责：稳定拉取 provider、保持主力/应急分组、验证 AI/GitHub 路由。
- 私人订阅、机场 token、mihomo secret、API key 不进 Git。

## 关键约定

- `annbot` 是规范 agent id；`antigravity` 是 alias，不是第二个独立作者。
- `net-sub` 免费池只进入 `🆓 免费应急`，不进入主力 AI 组。
- 主力 AI 组优先使用稳定 provider（当前原则：UserNodeB/C 或手动确认的付费池）。
- `🤖 Antigravity AI` / `🤖 国外 AI 专线` 应使用稳定主力，必要时通过 fallback 才进入免费池。
- GitHub 访问需覆盖 `github.com`、`githubusercontent.com`、`github.io`、`gist.github.com` 等系列域名。

## 使用方式

在 Pi 上先备份现有配置，再应用已有 patch 脚本：

```bash
bash pi/apply-pi-ai-gateway.sh /home/ubuntu/clash-config/config.yaml
bash pi/health-check.sh
```

> 默认脚本会调用仓库现有 `scripts/patch_mihomo*.py`，不会写入任何私人凭据。

## Telegram 通知

`refresh.yml` 每 6 小时运行一次，成功通知包含：

- 源数量与可拉取源数量
- 原始 URI 数、去重节点数
- TCP 存活节点数、存活率、耗时
- 去重/存活协议分布
- Actions run 链接
- Pi provider 地址和分组提示

需要 GitHub Secrets：

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
