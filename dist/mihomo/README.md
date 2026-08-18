# net-sub mihomo 接入说明（自动生成）

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

## 规则集（rule-provider，classical 格式）
```yaml
rule-providers:
  ai:
    type: http
    behavior: classical
    format: yaml
    url: https://<域名>/mihomo/rules/ai.yaml
    interval: 21600
  meetings:
    type: http
    behavior: classical
    format: yaml
    url: https://<域名>/mihomo/rules/meetings.yaml
    interval: 21600
  discord:
    type: http
    behavior: classical
    format: yaml
    url: https://<域名>/mihomo/rules/discord.yaml
    interval: 21600
  docker:
    type: http
    behavior: classical
    format: yaml
    url: https://<域名>/mihomo/rules/docker.yaml
    interval: 21600
  direct-domains:
    type: http
    behavior: classical
    format: yaml
    url: https://<域名>/mihomo/rules/direct-domains.yaml
    interval: 21600
  direct-ips:
    type: http
    behavior: classical
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
生成时间: 2026-08-18 03:57 UTC
