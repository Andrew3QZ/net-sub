# net-sub — Shadowrocket / mihomo 统一订阅生产线

从一份共享规则清单 + 上游节点源，自动生成 Shadowrocket 和 mihomo 双端订阅产物，由 CF Pages 托管分发。

## 目录结构

```
sources/nodes.txt        # 上游节点源清单（免费公开源）
rules/*.txt              # ★ 共享规则清单（唯一事实源，双端生成）
scripts/fetch_sources.py # 拉取 → 解析 → 去重
scripts/generate.py      # 生成 shadowrocket.conf + mihomo/ 产物
.github/workflows/       # 定时刷新（每 6h）
dist/                    # 生成产物（自动提交，勿手改）
```

## 产物

| 文件 | 用途 |
|---|---|
| `dist/shadowrocket.conf` | iOS Shadowrocket 完整配置（节点 + 规则） |
| `dist/mihomo/proxies.yaml` | mihomo proxy-provider（节点） |
| `dist/mihomo/rules/*.yaml` | mihomo rule-provider（共享规则） |
| `dist/mihomo/README.md` | Pi 接入说明 |

## 规则维护

只改 `rules/` 下的 txt 文件，跑 `python3 scripts/generate.py` 重新生成。
规则分组对应：

| 文件 | Shadowrocket 组 | mihomo 组 |
|---|---|---|
| ai.txt | AI-Services | 🤖 国外 AI 专线 |
| meetings.txt | Meetings | 📹 Zoom 会议 |
| discord.txt | Discord | Discord |
| docker.txt | Docker | 🐳 Docker |
| direct-domains.txt | DIRECT | DIRECT |
| direct-ips.txt | DIRECT | DIRECT |


## Pi AI Gateway 固化

`pi/` 目录固化 Pi mihomo 接入方式：GitHub Actions 每 6 小时扫描/筛选公开节点并生成 `dist/mihomo/*`，Pi 只拉取稳定产物。AnnBot/Antigravity AI 访问遵循“稳定主力节点优先，`net-sub` 免费池仅作 `🆓 免费应急`”原则。

Telegram 通知由 `scripts/telegram_notify.py` 发送，成功消息包含源拉取、去重、TCP 存活率、协议分布、Actions 链接和 Pi 接入提示；需要仓库 Secrets `TELEGRAM_BOT_TOKEN` 与 `TELEGRAM_CHAT_ID`。

## 本地开发

```bash
# 离线模式（用现有节点文件）
python3 scripts/fetch_sources.py --input /tmp/nodes.txt
python3 scripts/generate.py
```

## 安全边界

- `sources/nodes.txt` 只放免费公开源；私人订阅（含 token）走 GitHub Actions Secrets 注入
- `dist/mihomo/proxies.yaml` 可能包含免费节点凭据，仓库保持 public 时注意免费源本身的公开性
