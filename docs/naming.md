# QJAI 工程命名规范 v1.0

自 2026-11-29 生效。适用于新增公司项目；历史项目兼容保留，独立品牌、第三方 fork、个人历史项目不强制加 qjai 前缀。

## 标准项目名

`qjai-<type>-<name>`，小写英文字母、数字、单连字符分隔，禁止空格、下划线、驼峰、连续或尾部连字符。类型：agent、service、gateway、bridge、monitor、web、lib、infra、lab。业务 Agent 名为 qjai-agent-<business>，确需拆分时增加职责后缀。业务名称不绑定 Modal、Docker、n8n 等平台。建议保持简短。

| 对象 | Product Hunt 示例 |
| --- | --- |
| Repository | gamehack/qjai-agent-producthunt |
| OCI Image | ghcr.io/gamehack/qjai-agent-producthunt |
| Modal App | qjai-agent-producthunt |
| Gateway Agent ID | producthunt |
| n8n Workflow | QJAI \\| Agent \\| Product Hunt |

Gateway Agent ID 为稳定业务标识，在网关白名单唯一注册；现有 smoke 保留。Modal App 名与仓库一致，测试/生产通过环境隔离。平台自动分配实例 ID，不强行覆盖。

## 容器

- 镜像路径继承仓库名；仓库名称校验原始大小写，不靠自动转小写掩盖错误。Registry owner 转小写。
- main 构建发布 latest、sha-<完整 Git SHA>；正式版本 vMAJOR.MINOR.PATCH；生产部署必须固定 @sha256:<digest>，latest 仅用于开发。
- 单实例常驻容器使用标准项目名。Compose project name 使用标准项目名，多实例服务由 Compose 自动分配名称，不固定 container_name。
- 临时测试容器：<project>-test-<unique-id>；一次性任务容器：<project>-<run-id>。运行标识须合法且唯一；原始业务 run_id 独立保留，必要时采用安全编码作为实例后缀。
- Modal 自动命名容器实例。
- OCI 标签：org.opencontainers.image.title、source、revision；构建时项目名也传入 AGENT_NAME，作为任务输出默认 agent_name。
- 公共镜像不得包含密钥、私有配置或敏感业务数据。

## CI

```bash
python scripts/check_naming.py --repository gamehack/qjai-agent-producthunt --type agent
python -m unittest discover -s tests_host -v
```

Agent 模板构建/手动性能测试在构建前校验命名、推导 GHCR 路径。Dockerfile 本地默认 qjai-agent-template；下游本地构建需传 `--build-arg QJAI_PROJECT_NAME=<project>`，性能测试同时指定 `--project-name <project>`（CI 自动推导）。现有 Modal 部署仍固定原镜像 digest，不因模板 CI 自动升级。

历史项目 qjai-modal-gateway、kilo-bridge、codex-bridge、claude-bridge 等不批量重命名；业务迁移时单独评估镜像、部署、凭据、Webhook、DNS、调度及回滚。FreeQuota 等独立产品保留名称。公司级权威规范见 Notion「GitHub 项目与容器命名规范」。
