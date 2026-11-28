# QJAI Agent Template

潜界 AI 定时业务 Agent 开发模板。

- OpenAI Agents SDK / Python 3.12
- OCI 镜像交付，业务代码不依赖计算平台
- 自建 n8n 统一调度；Modal Functions 按需执行（Smoke 端到端验收通过）
- 默认 smoke 模式，不调用模型，不执行外部业务副作用

## 本地验证

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python -m qjai_agent
```

## 容器验证

```bash
docker build --platform linux/amd64 -t qjai-agent-template:dev .
docker run --rm qjai-agent-template:dev
```

## 实际 Agent 调用（会产生模型费用）

将 .env.example 复制为 .env，填入自己的 API key 和明确的模型名称，然后：

```bash
docker run --rm --env-file .env -e AGENT_MODE=live qjai-agent-template:dev
```

不要将 .env 或其他凭据提交到 Git。模型默认走 OpenAI API；兼容模型网关、运行记录持久化及业务幂等性由后续阶段实现。

## 任务协议

环境变量：AGENT_MODE（smoke/live）、AGENT_NAME、RUN_ID（可选）、BUSINESS_DATE（UTC 日期默认值；生产由 n8n 明确传入）、AGENT_INPUT、OPENAI_MODEL。

stdout 输出单行 JSON 结果，包含 run_id、agent_name、business_date、status、mode、duration_ms、output、usage；失败退出码非零，stderr 仅记录错误类型，不输出 API 密钥。业务代码位于 qjai_agent/job.py。RUN_ID 用于追踪，不代表已实现持久化去重。

## 实施阶段

1. 最小业务模板与容器 smoke test
2. CI / GHCR 镜像发布及依赖锁定
3. Modal Functions 适配及实际账单验证
4. n8n 调度、状态跟踪与幂等性
5. 真实业务 Agent 迁移

## 性能基准测试

[Agent performance benchmark](https://github.com/gamehack/qjai-agent-template/actions/workflows/benchmark.yml) 为手动测试工作流；默认无网络 smoke，不发布镜像、不部署 Modal。正式业务测试必须使用无副作用的 fixture，显式授权 live 模型调用。CI 对构建镜像自动进行三次离线 benchmark。报告含运行时间、CPU、内存、Token 及样本统计，不包含正文或密钥。详细定义与上线流程：[性能测试规范](docs/benchmark.md)。

## 工程命名规范

新增业务 Agent 必须使用 `qjai-agent-<business>` 小写 kebab-case 仓库名。CI 自动校验名称并推导 GHCR 镜像、OCI title 标签及默认 Agent 标识。完整规则见 [命名规范](docs/naming.md)。
