# 🚀 快速启动指南

## 需要执行的文件

### 1️⃣ 聊天机器人（飞书对话）
```bash
python chatbot.py
```
**作用**: 接收飞书消息，通过 Agent 处理 K8s 运维请求

---

### 2️⃣ 定时巡检（后台监控）
```bash
python scheduler.py
# 或后台运行
nohup python scheduler.py > scheduler.log 2>&1 &
```
**作用**: 每 2 分钟自动巡检集群健康状态，异常时推送飞书告警

---

## 📋 部署前准备

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置 K8s 权限（可选但推荐）
```bash
kubectl apply -f rbac.yaml
```

### 3. 确保 kubeconfig 可用
```bash
kubectl cluster-info
```

---

## ⚡ 一键启动（推荐）

创建启动脚本 `start.sh`:
```bash
#!/bin/bash
# 启动聊天机器人
python chatbot.py &
echo "✓ 聊天机器人已启动"

# 启动定时巡检
python scheduler.py &
echo "✓ 定时巡检已启动"

echo "所有服务已启动！按 Ctrl+C 停止"
wait
```

运行：
```bash
chmod +x start.sh
./start.sh
```

---

## 🎯 简洁回复优化

已优化 Agent 提示词：
- ✅ 正常状态只回复"正常"
- ✅ 操作成功只简短确认
- ✅ 异常时才详细说明
- ✅ 不再重复工具输出
- ✅ 去除冗余描述

**对话示例**:
```
用户: 检查节点状态
Agent: 正常

用户: 创建 test 命名空间
Agent: 已创建

用户: nginx pod 一直重启
Agent: CrashLoopBackOff，日志显示端口冲突，建议修改端口配置
```

---

## 📁 文件说明

| 文件 | 用途 | 是否必需 |
|------|------|---------|
| `agent.py` | Agent 核心逻辑（被其他文件调用） | ✅ 必需 |
| `chatbot.py` | 飞书对话接口 | ✅ 必需 |
| `scheduler.py` | 定时巡检任务 | ✅ 必需 |
| `requirements.txt` | Python 依赖 | ✅ 必需 |
| `rbac.yaml` | K8s 权限配置 | 🟡 推荐 |
| `test_agent.py` | 功能测试脚本 | 🔵 可选 |
| `UPGRADE_GUIDE.md` | 升级说明文档 | 🔵 可选 |

---

## 🧪 快速测试

```bash
# 测试 Agent 功能
python test_agent.py

# 或手动测试单个功能
python -c "
from agent import app, HumanMessage
state = {'messages': [HumanMessage(content='检查节点状态')]}
for event in app.stream(state, stream_mode='values'): pass
print(event['messages'][-1].content)
"
```
