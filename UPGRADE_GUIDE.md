# K8s 智能运维 Agent 升级说明

## 🎯 升级内容概览

本次升级大幅增强了智能体的 K8s 管理能力，从原来只能查询状态，升级为具备完整的资源创建、删除、扩缩容等生产级运维能力。

---

## ✨ 新增功能

### 1. 命名空间管理
- ✅ **create_namespace**: 创建新的命名空间
- ✅ **delete_namespace**: 删除命名空间

**示例对话**:
```
用户: 帮我创建一个叫 test-env 的命名空间
Agent: [调用 create_namespace] 命名空间 test-env 创建成功
```

### 2. Pod 管理
- ✅ **create_pod**: 创建 Pod（指定镜像、命名空间）
- ✅ **delete_pod**: 删除指定 Pod
- ✅ **get_pod_status**: 查询 Pod 状态（已有）
- ✅ **get_pod_logs**: 查看 Pod 日志（已有）

**示例对话**:
```
用户: 在 default 命名空间创建一个 nginx pod
Agent: [调用 create_pod] Pod nginx 在命名空间 default 中创建成功

用户: 删除这个 nginx pod
Agent: [调用 delete_pod] Pod nginx 已删除
```

### 3. Deployment 管理
- ✅ **create_deployment**: 创建 Deployment（支持指定副本数）
- ✅ **delete_deployment**: 删除 Deployment
- ✅ **scale_deployment**: 扩缩容 Deployment
- ✅ **restart_deployment**: 滚动重启 Deployment
- ✅ **get_deployment_status**: 查询 Deployment 状态

**示例对话**:
```
用户: 创建一个 nginx deployment，3个副本
Agent: [调用 create_deployment] Deployment nginx 在命名空间 default 中创建成功，副本数: 3

用户: 把 nginx 扩容到 5 个副本
Agent: [调用 scale_deployment] Deployment nginx 已扩缩容至 5 个副本

用户: 重启 nginx deployment
Agent: [调用 restart_deployment] Deployment nginx 已触发重启
```

### 4. 节点监控（已有，保留）
- ✅ **get_node_status**: 查看节点健康状态

### 5. 兜底工具（增强）
- ✅ **execute_kubectl_command**: 执行任意 kubectl 命令（用于其他工具未覆盖的场景）

---

## 🔧 改进内容

### 1. Agent 系统提示词优化
**之前**: 简单的功能说明
```python
"你是Kubernetes运维Agent。务必调用工具完成资源修改、创建、删除、查询等指令。"
```

**现在**: 详细的能力清单 + 工作原则
```python
"你是Kubernetes运维Agent，具备完整的K8s集群管理能力。
可用能力：
1. 命名空间管理: 创建、删除命名空间
2. Pod管理: 创建、删除、查询状态、查看日志
3. Deployment管理: 创建、删除、扩缩容、重启、查询状态
4. 节点监控: 查看节点健康状态
5. 故障排查: 查看日志、诊断异常Pod
6. 高级操作: 使用kubectl命令执行复杂操作

工作原则：
- 必须调用相应工具完成操作，不要凭空回答
- 创建资源前先检查是否已存在
- 删除操作要谨慎，确认用户意图
- 基于工具返回结果提供专业的运维建议"
```

### 2. 定时巡检任务增强
**新增检查项**:
- ✅ Deployment 副本数健康检查
- ✅ 更精准的异常识别（CrashLoopBackOff、Error、Pending）
- ✅ 更好的异常处理和错误上报

---

## 📊 工具列表对比

| 功能类别 | 原版工具数 | 升级后工具数 | 新增工具 |
|---------|-----------|------------|---------|
| Pod 管理 | 2 | 4 | +2 |
| Deployment 管理 | 0 | 5 | +5 |
| 命名空间管理 | 0 | 2 | +2 |
| 节点监控 | 1 | 1 | 0 |
| 兜底工具 | 1 | 1 | 0 |
| **总计** | **4** | **13** | **+9** |

---

## 🚀 使用示例

### 场景 1: 快速部署应用
```
用户: 帮我在 production 命名空间部署一个 redis，需要3个副本

Agent 执行流程:
1. [create_namespace] 检查/创建 production 命名空间
2. [create_deployment] 创建 redis deployment，副本数=3
3. [get_deployment_status] 验证部署状态
4. 返回: "已成功部署 redis，当前 3/3 副本运行正常"
```

### 场景 2: 故障排查与修复
```
用户: 我的应用一直重启，帮我看看

Agent 执行流程:
1. [get_pod_status] 查询 Pod 状态，发现 CrashLoopBackOff
2. [get_pod_logs] 查看最近日志，分析错误原因
3. 建议修复措施（例如：配置错误、资源不足等）
4. 如果需要，执行 [restart_deployment] 重启应用
```

### 场景 3: 弹性伸缩
```
用户: 现在流量高峰，把 web 服务扩容到 10 个实例

Agent 执行流程:
1. [get_deployment_status] 查看当前副本数
2. [scale_deployment] 扩容到 10 个副本
3. [get_deployment_status] 验证扩容结果
4. 返回: "已扩容至 10 个副本，当前 10/10 可用"
```

---

## 🔐 安全建议

1. **权限控制**: 确保 K8s ServiceAccount 具备必要的 RBAC 权限
2. **审计日志**: 所有工具调用都会通过 LangGraph 记录
3. **删除保护**: Agent 会在删除操作前进行二次确认提示
4. **命名空间隔离**: 默认在 `current_namespace` 中操作，避免误操作

---

## 📦 部署步骤

### 1. 安装依赖（无变化）
```bash
pip install -r requirements.txt
```

### 2. 配置 K8s 访问权限
```bash
# 确保 kubeconfig 可用
kubectl cluster-info

# 或在 Pod 内运行时使用 in-cluster config
```

### 3. 启动服务
```bash
# 启动聊天机器人（飞书）
python chatbot.py

# 启动定时巡检（后台运行）
nohup python scheduler.py &
```

---

## 🎯 常见问题 FAQ

### Q1: 为什么创建资源失败？
**A**: 检查以下几点：
1. K8s 集群连接是否正常
2. ServiceAccount 是否有足够权限（RBAC）
3. 命名空间是否存在
4. 资源名称是否符合 K8s 命名规范

### Q2: 如何限制 Agent 的操作范围？
**A**: 通过 K8s RBAC 配置，限制 ServiceAccount 的权限范围。例如：
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: agent-role
rules:
- apiGroups: ["", "apps"]
  resources: ["pods", "deployments"]
  verbs: ["get", "list", "create", "delete", "patch"]
```

### Q3: 定时巡检频率如何调整？
**A**: 修改 `scheduler.py` 中的：
```python
schedule.every(2).minutes.do(k8s_inspection_job)  # 改为需要的间隔
```

---

## 📈 未来规划

- [ ] Service 和 Ingress 管理
- [ ] ConfigMap 和 Secret 管理
- [ ] 资源配额和限制管理
- [ ] HPA（自动扩缩容）集成
- [ ] 更智能的故障诊断（基于历史数据）
- [ ] 多集群管理支持

---

## 📝 版本信息

- **当前版本**: v2.0
- **更新日期**: 2024
- **主要贡献**: 新增 9 个管理工具，全面支持生产级 K8s 运维
