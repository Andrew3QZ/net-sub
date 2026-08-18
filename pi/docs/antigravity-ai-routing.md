# Antigravity / AnnBot AI 路由固化说明

## 目标

把 Pi 上已经实测有效的 AI 网络优化固化为可版本化、可审计、可回滚的 Git 资产。

## 规则来源

- AI 域名事实源：`rules/ai.txt`
- mihomo 规则产物：`dist/mihomo/rules/ai.yaml`
- 节点池产物：`dist/mihomo/proxies.yaml`
- Pi 接入脚本：`scripts/patch_mihomo.py`、`scripts/patch_mihomo_nodes.py`、`scripts/patch_mihomo_groups.py`、`scripts/patch_mihomo_git.py`

## 分组原则

1. AI 专线和 Antigravity/AnnBot 工作流优先走稳定主力节点。
2. 免费池 `net-sub` 每 6 小时自动筛选，但只作为 `🆓 免费应急`。
3. 红杏等私人订阅只保留在 Pi 本地配置，不进入 public Git。
4. 修改 Pi 分组时要先备份，再校验 mihomo 配置，再热重载/重启。
5. 切换主力池时要扫描所有 AI 组，不能只改 `🚀 Proxy` 或 `🛡️ Sentinel`。

## 验证项

- `sub.1919444.xyz/mihomo/proxies.yaml` 可拉取。
- `sub.1919444.xyz/mihomo/rules/ai.yaml` 可拉取。
- Pi mihomo rule-provider 中 `ai`、`docker`、`discord`、`meetings` 均有更新时间。
- `api.openai.com`、`claude.ai`、`openrouter.ai`、`generativelanguage.googleapis.com` 命中 AI 规则组。
- `githubusercontent.com` 不直连，走代理。
- Telegram 能收到 bot 的定时扫描统计。
