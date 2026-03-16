# 🌉 OpenClaw A2A Bridge

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![A2A Protocol](https://img.shields.io/badge/A2A-Protocol-orange.svg)](https://github.com/a2aproject/A2A)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-compatible-purple.svg)](https://github.com/nicepkg/openclaw)

**基于 [Google A2A 协议](https://github.com/a2aproject/A2A) 的 [OpenClaw](https://github.com/nicepkg/openclaw) 跨设备 Agent 通信桥接方案。**

> 你的 AI Agent 不应该是孤岛。这个项目让它们能跨设备对话、协作，说的还是标准协议。

---

## 为什么需要这个项目？

单个 AI Agent 很强，但**多个 Agent 协作**才是真正的杀手级能力。问题在于，大部分 Agent 框架把 Agent 困在单机里。

**OpenClaw A2A Bridge** 用 Google 的 A2A 协议（Agent 互操作的新标准）解决了这个问题。它把 OpenClaw 强大的 Agent 运行时包装成 A2A 兼容服务，让你的 Agent 能够：

- 🔍 **自动发现**彼此的能力
- 💬 通过标准 JSON-RPC 协议**通信**
- 🌐 在 Tailscale 网络（或任何网络）上**跨设备协作**
- 🔄 通过 SSE **实时流式**响应

## 核心特性

| 特性 | 说明 |
|------|------|
| **A2A 协议兼容** | 完整实现 Agent Card 发现、JSON-RPC 2.0 通信、SSE 流式 |
| **OpenClaw 深度集成** | 通过 OpenResponses API 把任意 OpenClaw Agent 暴露为 A2A 服务 |
| **跨设备通信** | 为 Tailscale 多机环境设计，也支持任何可达网络 |
| **零配置发现** | Agent 通过 `/.well-known/agent.json` 自描述，不需要注册中心 |
| **流量日志** | 所有 A2A 流量自动记录到轮转日志，方便调试和监控 |
| **健康检查** | 内置组件级健康检查（服务器、Agent Card、API） |
| **开机自启** | 支持 macOS LaunchAgent 和 Linux systemd |
| **交互式客户端** | CLI 客户端支持发现、单条消息、流式、交互模式 |

## 架构

```
┌──────────────────────┐          A2A 协议               ┌──────────────────────┐
│    设备 A              │       (JSON-RPC / HTTP)        │    设备 B              │
│                       │                                │                       │
│  ┌─────────────────┐  │  ◄── Tailscale / 局域网 ───►  │  ┌─────────────────┐  │
│  │  A2A Server      │  │       或任意网络               │  │  A2A Server      │  │
│  │  (端口 9100)     │  │                                │  │  (端口 9100)     │  │
│  └────────┬────────┘  │                                │  └────────┬────────┘  │
│           │            │                                │           │            │
│           ▼            │                                │           ▼            │
│  ┌─────────────────┐  │                                │  ┌─────────────────┐  │
│  │  OpenResponses   │  │                                │  │  OpenResponses   │  │
│  │  适配器          │  │                                │  │  适配器          │  │
│  └────────┬────────┘  │                                │  └────────┬────────┘  │
│           │            │                                │           │            │
│           ▼            │                                │           ▼            │
│  ┌─────────────────┐  │                                │  ┌─────────────────┐  │
│  │  OpenClaw Agent  │  │                                │  │  OpenClaw Agent  │  │
│  └─────────────────┘  │                                │  └─────────────────┘  │
└──────────────────────┘                                └──────────────────────┘
```

## 🤖 直接告诉你的 Agent（推荐方式）

最简单的安装方法？**直接给你的 OpenClaw Agent 发这段话：**

### 单个 Agent 安装

> 帮我安装 A2A Bridge。克隆 https://github.com/Shy-Plus/openclaw-a2a-bridge.git 到 workspace/projects/，安装 Python 依赖，从 .env.example 创建 .env，把 A2A_PUBLIC_URL 设成我这台机器的 IP，然后在 9100 端口启动 A2A Server。同时在 gateway 配置里启用 OpenResponses API（gateway.http.endpoints.responses.enabled = true）并重启 gateway。

### 连接两个 Agent

Agent A 已经装好了？给 Agent B 发：

> 安装 A2A Bridge 并连接另一个 Agent。克隆 https://github.com/Shy-Plus/openclaw-a2a-bridge.git，安装依赖，在 .env 里设置 A2A_PUBLIC_URL 为我的 IP，A2A_REMOTE_HOST 设为 {Agent A 的 IP}。启动 A2A Server，然后测试连接：`python -m src.client --target http://{Agent A 的 IP}:9100 --message "你好，我是 Agent B"`。同时启用 OpenResponses API。

### 多 Agent 组网

3个以上 Agent？给每个新 Agent 发：

> 加入 A2A Agent 网络。克隆 https://github.com/Shy-Plus/openclaw-a2a-bridge.git，装依赖，把 A2A_PUBLIC_URL 设成我的 IP。在 9100 端口启动 Server。然后发现并测试所有已知 Agent：{列出它们的 IP}。给每个 Agent 发一条 hello 完成注册。

### OpenClaw 配置命令

你的 Agent 需要启用 OpenResponses API。它可以自动完成，或者手动执行：

```bash
openclaw config set gateway.http.endpoints.responses.enabled true
openclaw gateway restart
```

---

## 快速开始（手动方式）

### 1. 安装

```bash
git clone https://github.com/Shy-Plus/openclaw-a2a-bridge.git
cd openclaw-a2a-bridge
pip install -r requirements.txt
```

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env，至少设置 A2A_PUBLIC_URL 为你的机器 IP
```

### 3. 启动

```bash
./scripts/run_server.sh
```

搞定。你的 Agent 现在可以通过 `http://你的IP:9100/.well-known/agent.json` 被发现了。

## 使用方式

### 发现远程 Agent

```bash
python -m src.client --target http://远程地址:9100 --discover-only
```

### 发消息

```bash
python -m src.client --target http://远程地址:9100 -m "你好！"
```

### 交互聊天

```bash
python -m src.client --target http://远程地址:9100
```

### 流式模式

```bash
python -m src.client --target http://远程地址:9100 -m "讲个故事" --stream
```

### 健康检查

```bash
python -m src.health_check --url http://localhost:9100
```

### 跑协作 Demo

```bash
# 先在两台机器上各启动 A2A Server
python examples/demo.py --local http://设备A:9100 --remote http://设备B:9100
```

## 配置参考

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `A2A_GATEWAY_TOKEN` | 自动从 `openclaw.json` 读取 | Gateway 认证 Token |
| `A2A_LOCAL_HOST` | `0.0.0.0` | 绑定地址 |
| `A2A_LOCAL_PORT` | `9100` | 监听端口 |
| `A2A_LOCAL_API` | `http://localhost:18789/v1/responses` | OpenResponses API 地址 |
| `A2A_PUBLIC_URL` | `http://{host}:{port}` | Agent Card 广播的公网 URL |
| `A2A_REMOTE_HOST` | — | 远程 Agent IP（多 Agent 场景） |
| `A2A_MODEL` | `openclaw:main` | OpenResponses 模型名 |
| `A2A_AGENT_CARD` | `cards/agent_card.json` | Agent Card 文件路径 |
| `A2A_TRAFFIC_LOG` | `~/.openclaw/logs/a2a-traffic.log` | 流量日志路径 |

## A2A 协议对标

| A2A 特性 | 状态 | 说明 |
|----------|------|------|
| Agent Card（能力发现）| ✅ | `GET /.well-known/agent.json` |
| JSON-RPC 2.0 通信 | ✅ | 标准请求/响应 |
| 同步消息 | ✅ | 发送→等待→返回 |
| SSE 流式 | ✅ | 实时 token 流 |
| 多技能声明 | ✅ | Agent Card skills 数组 |
| Bearer Token 认证 | ✅ | OpenResponses API 层 |
| 任务管理 | ✅ | 内存任务存储 |

## 项目结构

```
openclaw-a2a-bridge/
├── src/                       # 核心源码
│   ├── server.py              # A2A 服务端
│   ├── client.py              # A2A 客户端
│   ├── adapter.py             # OpenResponses ↔ A2A 适配器
│   ├── config.py              # 集中配置
│   └── health_check.py        # 健康检查
├── cards/                     # Agent Card 定义
│   ├── agent_card.json        # 主 Agent Card（自定义这个）
│   └── remote_agent_card.json # 远程 Agent 示例
├── scripts/                   # 运维脚本
│   ├── run_server.sh          # 启动/停止/重启
│   └── install_service.sh     # macOS 自启安装
├── examples/                  # 使用示例
│   ├── demo.py                # 多 Agent 协作演示
│   └── collaborative_workflow.py  # 流水线工作流示例
├── docs/                      # 文档
│   ├── architecture.md        # 架构详解
│   ├── setup-guide.md         # 部署指南
│   └── troubleshooting.md     # 故障排除
├── .env.example               # 环境变量模板
├── requirements.txt           # Python 依赖
└── LICENSE                    # MIT 开源协议
```

## 开机自启

### macOS

```bash
./scripts/install_service.sh              # 安装
./scripts/install_service.sh --uninstall  # 卸载
```

### Linux

参见 [docs/setup-guide.md](docs/setup-guide.md#auto-start-on-boot-linux)。

## 技术栈

- **协议**: Google A2A Protocol
- **SDK**: a2a-sdk (Python)
- **传输**: JSON-RPC 2.0 over HTTP
- **后端**: OpenClaw OpenResponses API
- **网络**: Tailscale（推荐）/ 任意 IP 网络
- **Agent 框架**: OpenClaw

## 安全

- 通信走 Tailscale 内网（端到端加密）
- 每个 Gateway 有独立的 auth token
- Agent Card 不包含敏感信息
- 敏感配置通过环境变量注入，不进代码

## 贡献

欢迎 PR！流程：

1. Fork 仓库
2. 创建分支：`git checkout -b feat/你的功能`
3. 提交：`git commit -m "feat: 新功能描述"`
4. 推送：`git push origin feat/你的功能`
5. 提 Pull Request

提交信息请遵循 [Conventional Commits](https://www.conventionalcommits.org/)。

## License

[MIT License](LICENSE)

## 致谢

- **[Google A2A Protocol](https://github.com/a2aproject/A2A)** — Agent 间通信协议标准
- **[a2a-sdk](https://pypi.org/project/a2a-sdk/)** — 官方 Python SDK
- **[OpenClaw](https://github.com/nicepkg/openclaw)** — 本项目依赖的 Agent 运行时
- **[Tailscale](https://tailscale.com/)** — 安全的网状 VPN

---

<p align="center">
  Built by <a href="https://github.com/Shy-Plus">Shy's Lab</a> 🪐
  <br>
  <sub>让 Agent 开口说话，一座桥的事。</sub>
</p>
