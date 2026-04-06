#!/usr/bin/env python3
"""
K8s Agent 功能测试脚本
用于验证所有新增的工具是否正常工作
"""

from agent import app, HumanMessage

def test_agent(query: str, namespace: str = "default"):
    """测试 Agent 响应"""
    print(f"\n{'='*60}")
    print(f"测试查询: {query}")
    print(f"命名空间: {namespace}")
    print(f"{'='*60}")
    
    state = {
        "messages": [HumanMessage(content=query)],
        "current_namespace": namespace
    }
    
    try:
        for event in app.stream(state, stream_mode="values"):
            pass
        
        response = event["messages"][-1].content
        print(f"\nAgent 响应:\n{response}")
        return response
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        return None

def main():
    print("🚀 K8s Agent 功能测试")
    print("=" * 60)
    
    # 测试1: 查询节点状态
    print("\n📋 测试 1: 查询节点状态")
    test_agent("检查所有节点状态")
    
    # 测试2: 查询 Pod
    print("\n📋 测试 2: 查询 default 命名空间的 Pod")
    test_agent("列出 default 命名空间的所有 Pod")
    
    # 测试3: 查询 Deployment
    print("\n📋 测试 3: 查询 Deployment 状态")
    test_agent("查看 default 命名空间的所有 deployment")
    
    # 测试4: 创建命名空间（谨慎）
    print("\n📋 测试 4: 创建测试命名空间")
    response = test_agent("创建一个名为 test-agent 的命名空间")
    
    if response and "成功" in response:
        # 测试5: 在新命名空间创建 Pod
        print("\n📋 测试 5: 在 test-agent 命名空间创建 nginx Pod")
        test_agent("在 test-agent 命名空间创建一个 nginx pod，镜像用 nginx:latest", "test-agent")
        
        # 测试6: 查看新创建的 Pod
        print("\n📋 测试 6: 查看新创建的 Pod 状态")
        test_agent("查看 test-agent 命名空间的 pod 状态", "test-agent")
        
        # 清理测试资源
        print("\n🧹 清理测试资源")
        test_agent("删除 test-agent 命名空间中的 nginx pod", "test-agent")
        test_agent("删除 test-agent 命名空间")
    
    # 测试7: 创建 Deployment（谨慎）
    print("\n📋 测试 7: 创建测试 Deployment")
    response = test_agent("在 default 命名空间创建一个 nginx-test deployment，2个副本，镜像用 nginx:latest")
    
    if response and "成功" in response:
        # 测试8: 扩缩容
        print("\n📋 测试 8: 扩容 Deployment")
        test_agent("把 nginx-test 扩容到 3 个副本")
        
        # 测试9: 查看扩容结果
        print("\n📋 测试 9: 查看扩容后的状态")
        test_agent("查看 nginx-test deployment 的状态")
        
        # 测试10: 重启 Deployment
        print("\n📋 测试 10: 重启 Deployment")
        test_agent("重启 nginx-test deployment")
        
        # 清理
        print("\n🧹 清理测试资源")
        test_agent("删除 nginx-test deployment")
    
    print("\n" + "="*60)
    print("✅ 测试完成！")
    print("="*60)

if __name__ == "__main__":
    print("""
⚠️  警告：此测试脚本会在你的 K8s 集群中创建和删除资源
    
测试内容：
1. 查询节点、Pod、Deployment 状态
2. 创建测试命名空间 (test-agent)
3. 创建测试 Pod 和 Deployment
4. 测试扩缩容功能
5. 自动清理测试资源

请确保：
- 你有足够的 K8s 权限
- 这是测试环境，而非生产环境
- kubeconfig 已正确配置

是否继续？(yes/no): """)
    
    confirmation = input().strip().lower()
    if confirmation == "yes":
        main()
    else:
        print("❌ 测试已取消")
