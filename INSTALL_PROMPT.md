# OpenClaw A2A Bridge 安装 Prompt

默认语言：**中文** | [English](INSTALL_PROMPT.en.md)

把下面整段原样交给你自己的 OpenClaw agent，让它帮你完成 A2A Bridge 的安装、配置和连接。

```text
你现在要帮我安装 OpenClaw A2A Bridge，让我的 agent 能通过 Google A2A 协议和其他设备上的 agent 通信。

你的目标不是解释原理，而是直接完成安装和接线，让 A2A Server 跑起来。

严格约束：
1. 不要修改 OpenClaw 自己的 openclaw.json，除了启用 OpenResponses API（gateway.http.endpoints.responses.enabled = true）。
2. 不要伪造、生成任何 API key 或 token。Gateway token 从 openclaw.json 自动读取。
3. 不要假设固定 IP 地址。必须探测本机真实 IP。
4. 所有敏感信息走环境变量，不要硬编码到代码里。
5. 如果某个依赖安装失败，停下来告诉我原因，不要跳过。

请按这个顺序执行：

第一阶段：确认环境
1. 确认 Python 3.11+ 可用：
   - `python3.11 --version` 或 `python3 --version`
   - 如果没有，告诉我安装命令（brew install python@3.11 / apt install python3.11）
2. 确认 OpenClaw Gateway 可达：
   - `openclaw status` 或 `curl -sS http://localhost:18789/health`
   - 记录 Gateway 端口（默认 18789）
3. 确认 OpenResponses API 状态：
   - 检查 openclaw.json 中 gateway.http.endpoints.responses.enabled 是否为 true
   - 如果不是，用 gateway config.patch 工具启用它并重启 gateway
4. 探测本机 IP 地址（按优先级）：
   - Tailscale IP：`tailscale status` 或 `tailscale ip -4`（如果有 tailscale）
   - 局域网 IP：`ipconfig getifaddr en0`（macOS）或 `hostname -I`（Linux）
   - 记录为 MY_IP，后续用于 A2A_PUBLIC_URL
5. 确认 pip 可用：`python3.11 -m pip --version`

第二阶段：安装项目
6. 选择安装目录（按优先级）：
   - 如果有 OpenClaw workspace：`~/.openclaw/workspace/projects/a2a-bridge/`
   - 否则：`~/projects/a2a-bridge/`
7. 克隆仓库：
   ```bash
   git clone https://github.com/Shy-Plus/openclaw-a2a-bridge.git <安装目录>
   cd <安装目录>
   ```
8. 如果目录已存在，先 `git pull` 更新而不是重新克隆。
9. 安装 Python 依赖：
   ```bash
   pip install -r requirements.txt
   ```
   如果 pip install 失败（网络问题），尝试：
   ```bash
   pip install 'a2a-sdk[http-server]' httpx uvicorn
   ```

第三阶段：配置
10. 从模板创建配置：
    ```bash
    cp .env.example .env
    ```
11. 修改 .env 中以下值（其他保持默认）：
    - `A2A_PUBLIC_URL=http://{MY_IP}:9100`（用第一阶段探测到的 IP）
    - `A2A_LOCAL_API=http://localhost:{GATEWAY_PORT}/v1/responses`（用第一阶段确认的端口）
    - `A2A_GATEWAY_TOKEN` 留空（会自动从 openclaw.json 读取）
12. 自定义 Agent Card（重要！这是你的 agent 的"名片"）：
    - 编辑 `cards/agent_card.json`
    - 修改 `name` 为你的 agent 名字
    - 修改 `description` 为你的 agent 描述
    - 修改 `skills` 列表，描述你的 agent 擅长什么
    - 修改 `provider.organization` 为你的组织/名字
13. 创建日志目录：
    ```bash
    mkdir -p ~/.openclaw/workspace/logs/
    mkdir -p ~/.openclaw/logs/
    ```

第四阶段：启动和验证
14. 启动 A2A Server：
    ```bash
    ./scripts/run_server.sh
    ```
    或手动：
    ```bash
    python -m src.server --port 9100 --public-url http://{MY_IP}:9100
    ```
15. 验证 Agent Card 可达：
    ```bash
    curl -sS http://localhost:9100/.well-known/agent-card.json
    ```
    应该返回你的 agent 名片 JSON。
16. 验证从外部可达（如果有另一台机器）：
    ```bash
    curl -sS http://{MY_IP}:9100/.well-known/agent-card.json
    ```
17. 运行健康检查：
    ```bash
    python -m src.health_check --url http://localhost:9100
    ```
    应该看到 3 项全绿（A2A Server / Agent Card / OpenResponses API）。

第五阶段：连接远程 Agent（可选）
18. 如果已知远程 agent 的 A2A 地址，测试连接：
    ```bash
    python -m src.client --target http://{REMOTE_IP}:9100 --discover-only
    ```
    应该看到远程 agent 的名片和技能列表。
19. 发送测试消息：
    ```bash
    python -m src.client --target http://{REMOTE_IP}:9100 --message "你好，我的 A2A Bridge 安装成功了"
    ```
20. 如果远程 agent 回复了，双向 A2A 通信已建立。

第六阶段：设置开机自启（可选但推荐）
21. macOS：
    ```bash
    ./scripts/install_service.sh
    ```
    这会创建 LaunchAgent，开机自动启动 A2A Server，崩溃自动重启。
22. Linux（systemd）：
    参见 docs/setup-guide.md 中的 systemd 配置。
23. 验证自启服务：
    ```bash
    ./scripts/run_server.sh status
    ```

第七阶段：交付结果
24. 安装完成后，输出以下信息：
    - ✅ 或 ❌：各阶段的执行结果
    - 本机 A2A 地址：http://{MY_IP}:9100
    - Agent Card 地址：http://{MY_IP}:9100/.well-known/agent-card.json
    - Agent 名称和技能数量
    - 是否已连接远程 agent（如果有的话）
    - 是否已设置开机自启
    - 日志文件位置
    - 如果有任何步骤失败：原因和修复建议

常见问题处理：
- 如果端口 9100 被占用，换 9200 或其他空闲端口，并更新 .env
- 如果 Tailscale 没装，用局域网 IP；如果两台机器不在同一局域网，需要先配网络互通
- 如果 pip install 超时，尝试换镜像源：pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
- 如果 OpenResponses API 返回 401，检查 gateway auth token 是否正确
- 如果 Agent Card URL 里是 127.0.0.1，确认 A2A_PUBLIC_URL 设成了外部可达 IP
```
