import os
from typing import TypedDict, Annotated, Sequence
from kubernetes import client, config
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langgraph.graph.message import add_messages
import subprocess

try:
    config.load_kube_config()
    print("成功加载 K8s 配置文件")
except Exception as e:
    print(f"警告: 未找到 K8s 配置文件，Agent 将在无集群连接模式下启动。错误: {e}")

core_v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

@tool
def get_pod_status(namespace: str, pod_name: str = None) -> str:
    """获取Pod状态信息"""
    try:
        if pod_name:
            pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
            return f"{pod.metadata.name}, {pod.status.phase}, {pod.status.pod_ip}"
        pods = core_v1.list_namespaced_pod(namespace=namespace)
        return "\n".join([f"{p.metadata.name}: {p.status.phase}" for p in pods.items])
    except Exception as e:
        return str(e)

@tool
def get_pod_logs(namespace: str, pod_name: str, tail_lines: int = 50, previous: bool = False) -> str:
    """获取Pod日志片段"""
    try:
        return core_v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=tail_lines, previous=previous)
    except Exception as e:
        return str(e)

@tool
def get_node_status(node_name: str = None) -> str:
    """获取K8s节点状态"""
    try:
        if node_name:
            n = core_v1.read_node(name=node_name)
            c = ", ".join([f"{x.type}={x.status}" for x in n.status.conditions if x.status == "True"])
            return f"{n.metadata.name}: {c}"
        nodes = core_v1.list_node()
        res = []
        for n in nodes.items:
            c = [x.type for x in n.status.conditions if x.status == "True"]
            s = "Ready" if "Ready" in c else "NotReady"
            res.append(f"{n.metadata.name}: {s} ({c})")
        return "\n".join(res)
    except Exception as e:
        return str(e)

@tool
def create_namespace(namespace: str) -> str:
    """创建新的命名空间"""
    try:
        body = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace))
        core_v1.create_namespace(body=body)
        return f"命名空间 {namespace} 创建成功"
    except Exception as e:
        return f"创建失败: {str(e)}"

@tool
def delete_namespace(namespace: str) -> str:
    """删除命名空间"""
    try:
        core_v1.delete_namespace(name=namespace)
        return f"命名空间 {namespace} 已标记删除"
    except Exception as e:
        return f"删除失败: {str(e)}"

@tool
def create_pod(namespace: str, pod_name: str, image: str, container_name: str = None) -> str:
    """创建Pod，需要指定命名空间、Pod名称和镜像"""
    try:
        if not container_name:
            container_name = pod_name
        
        container = client.V1Container(
            name=container_name,
            image=image,
            image_pull_policy="IfNotPresent"
        )
        
        spec = client.V1PodSpec(containers=[container])
        pod = client.V1Pod(
            metadata=client.V1ObjectMeta(name=pod_name),
            spec=spec
        )
        
        core_v1.create_namespaced_pod(namespace=namespace, body=pod)
        return f"Pod {pod_name} 在命名空间 {namespace} 中创建成功"
    except Exception as e:
        return f"创建Pod失败: {str(e)}"

@tool
def delete_pod(namespace: str, pod_name: str) -> str:
    """删除指定的Pod"""
    try:
        core_v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
        return f"Pod {pod_name} 已删除"
    except Exception as e:
        return f"删除Pod失败: {str(e)}"

@tool
def create_deployment(namespace: str, name: str, image: str, replicas: int = 1) -> str:
    """创建Deployment，指定副本数量"""
    try:
        container = client.V1Container(
            name=name,
            image=image,
            image_pull_policy="IfNotPresent"
        )
        
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": name}),
            spec=client.V1PodSpec(containers=[container])
        )
        
        spec = client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(match_labels={"app": name}),
            template=template
        )
        
        deployment = client.V1Deployment(
            metadata=client.V1ObjectMeta(name=name),
            spec=spec
        )
        
        apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)
        return f"Deployment {name} 在命名空间 {namespace} 中创建成功，副本数: {replicas}"
    except Exception as e:
        return f"创建Deployment失败: {str(e)}"

@tool
def scale_deployment(namespace: str, name: str, replicas: int) -> str:
    """扩缩容Deployment的副本数"""
    try:
        deployment = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
        deployment.spec.replicas = replicas
        apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=deployment)
        return f"Deployment {name} 已扩缩容至 {replicas} 个副本"
    except Exception as e:
        return f"扩缩容失败: {str(e)}"

@tool
def delete_deployment(namespace: str, name: str) -> str:
    """删除Deployment"""
    try:
        apps_v1.delete_namespaced_deployment(name=name, namespace=namespace)
        return f"Deployment {name} 已删除"
    except Exception as e:
        return f"删除Deployment失败: {str(e)}"

@tool
def get_deployment_status(namespace: str, name: str = None) -> str:
    """获取Deployment状态"""
    try:
        if name:
            dep = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            return f"{dep.metadata.name}: 期望副本={dep.spec.replicas}, 当前副本={dep.status.replicas}, 可用副本={dep.status.available_replicas}"
        
        deps = apps_v1.list_namespaced_deployment(namespace=namespace)
        return "\n".join([
            f"{d.metadata.name}: {d.status.available_replicas}/{d.spec.replicas} 可用"
            for d in deps.items
        ])
    except Exception as e:
        return f"获取Deployment状态失败: {str(e)}"

@tool
def restart_deployment(namespace: str, name: str) -> str:
    """重启Deployment（通过更新annotation触发滚动更新）"""
    try:
        from datetime import datetime
        deployment = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
        
        if deployment.spec.template.metadata.annotations is None:
            deployment.spec.template.metadata.annotations = {}
        
        deployment.spec.template.metadata.annotations["kubectl.kubernetes.io/restartedAt"] = datetime.now().isoformat()
        apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=deployment)
        return f"Deployment {name} 已触发重启"
    except Exception as e:
        return f"重启Deployment失败: {str(e)}"

@tool
def execute_kubectl_command(command: str) -> str:
    """执行底层kubectl命令行（兜底工具，用于其他工具无法覆盖的场景）"""
    try:
        if not command.startswith("kubectl "):
            command = "kubectl " + command
        res = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return res.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr
    except Exception as e:
        return str(e)

tools = [
    get_pod_status, 
    get_pod_logs, 
    get_node_status, 
    create_namespace,
    delete_namespace,
    create_pod,
    delete_pod,
    create_deployment,
    scale_deployment,
    delete_deployment,
    get_deployment_status,
    restart_deployment,
    execute_kubectl_command
]

import os
from dotenv import load_dotenv

load_dotenv()

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    current_namespace: str

llm = ChatOpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
    base_url="https://api.deepseek.com",
    model="deepseek-chat",
    temperature=0
)
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: AgentState):
    from langchain_core.messages import SystemMessage
    current_ns = state.get("current_namespace", "default")
    system_prompt = (
        f"K8s运维Agent，当前命名空间: {current_ns}\n"
        "原则：\n"
        "1. 必须调用工具完成操作\n"
        "2. 回复极简，只说结果和关键信息\n"
        "3. 正常状态只回复\"正常\"或简短确认\n"
        "4. 异常才详细说明问题和建议\n"
        "5. 不要重复工具返回的内容，不要啰嗦"
    )
    msg = llm_with_tools.invoke([SystemMessage(content=system_prompt)] + state["messages"])
    return {"messages": [msg]}

def should_continue(state: AgentState) -> str:
    return "tools" if state["messages"][-1].tool_calls else END

workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, ["tools", END])
workflow.add_edge("tools", "agent")
app = workflow.compile()

