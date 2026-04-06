"""
OpenClaw 智能分流系统集成脚本

这个脚本展示如何在 OpenClaw 的 Hook 或 Skill 中集成任务分流逻辑。
"""

import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

# 假设 router.py 已在 Python path 中
try:
    from openclaw_core.skills.task_router.router import (
        TaskRouter, 
        TaskProcessor, 
        SmartDispatcher
    )
except ImportError:
    print("⚠ 警告：无法导入 router 模块，请确保路径正确")


class OpenClawTaskDispatcher:
    """OpenClaw 任务分流集成器"""
    
    def __init__(self, config_path: str = "./openclaw.json"):
        """
        初始化分流器
        
        Args:
            config_path: openclaw.json 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.dispatcher = SmartDispatcher(
            router_agent_id="router",
            processor_agent_id="processor"
        )
    
    def _load_config(self) -> Dict[str, Any]:
        """加载 OpenClaw 配置"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    async def process_user_input(self, user_input: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        处理用户输入，自动分流到合适的 agent
        
        Args:
            user_input: 用户输入文本
            context: 上下文信息（如 Discord 消息 ID、用户 ID 等）
            
        Returns:
            {
                "status": "success|error",
                "classification": {...},
                "target_agent": str,
                "action": "route_to_processor|process_directly",
                "decompose_prompt": str (可选),
                "metadata": {...}
            }
        """
        try:
            # 1. 分流
            dispatch_result = await self.dispatcher.dispatch(user_input, context)
            
            # 2. 构建响应
            response = {
                "status": "success",
                "classification": dispatch_result["classification"],
                "target_agent": dispatch_result["target_agent"],
                "action": "route_to_processor" if dispatch_result["target_agent_id"] else "process_directly",
                "metadata": dispatch_result["metadata"]
            }
            
            # 3. 若为高复杂度，添加拆解提示词
            if "decompose_prompt" in dispatch_result:
                response["decompose_prompt"] = dispatch_result["decompose_prompt"]
            
            return response
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "metadata": {"char_count": len(user_input)}
            }
    
    def get_agent_config(self, agent_id: str) -> Optional[Dict]:
        """获取指定 agent 的配置"""
        for agent in self.config.get("agents", {}).get("list", []):
            if agent.get("id") == agent_id:
                return agent
        return None
    
    def get_model_config(self, model_id: str) -> Optional[Dict]:
        """获取指定模型的配置"""
        providers = self.config.get("models", {}).get("providers", {})
        for provider_id, provider_config in providers.items():
            for model in provider_config.get("models", []):
                if model.get("id") == model_id:
                    return {
                        "provider": provider_id,
                        "model": model,
                        "baseUrl": provider_config.get("baseUrl"),
                        "apiKey": provider_config.get("apiKey")
                    }
        return None


class DiscordHookIntegration:
    """Discord Hook 集成示例"""
    
    def __init__(self, dispatcher: OpenClawTaskDispatcher):
        """
        初始化 Discord Hook 集成
        
        Args:
            dispatcher: OpenClawTaskDispatcher 实例
        """
        self.dispatcher = dispatcher
    
    async def handle_discord_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 Discord 消息
        
        Args:
            message_data: Discord 消息数据
                {
                    "content": "用户消息内容",
                    "author_id": "用户 ID",
                    "channel_id": "频道 ID",
                    "message_id": "消息 ID"
                }
            
        Returns:
            {
                "status": "success|error",
                "action": "reply|forward_to_agent",
                "target_agent": str (可选),
                "response": str (可选),
                "metadata": {...}
            }
        """
        user_input = message_data.get("content", "")
        context = {
            "author_id": message_data.get("author_id"),
            "channel_id": message_data.get("channel_id"),
            "message_id": message_data.get("message_id"),
            "source": "discord"
        }
        
        # 分流
        dispatch_result = await self.dispatcher.process_user_input(user_input, context)
        
        if dispatch_result["status"] != "success":
            return {
                "status": "error",
                "action": "reply",
                "response": f"处理失败: {dispatch_result.get('error', '未知错误')}",
                "metadata": dispatch_result.get("metadata", {})
            }
        
        # 根据分流结果决定行动
        if dispatch_result["action"] == "route_to_processor":
            return {
                "status": "success",
                "action": "forward_to_agent",
                "target_agent": "processor",
                "decompose_prompt": dispatch_result.get("decompose_prompt"),
                "metadata": {
                    **dispatch_result["metadata"],
                    "complexity": dispatch_result["classification"]["complexity"],
                    "confidence": dispatch_result["classification"]["confidence"]
                }
            }
        else:
            return {
                "status": "success",
                "action": "process_directly",
                "target_agent": "router",
                "metadata": {
                    **dispatch_result["metadata"],
                    "complexity": dispatch_result["classification"]["complexity"]
                }
            }


# ============================================================================
# 使用示例
# ============================================================================

async def main():
    """主函数 - 演示如何使用"""
    
    # 1. 初始化分流器
    dispatcher = OpenClawTaskDispatcher(
        config_path="/Users/mac/Documents/龙虾相关/my_openclaw/openclaw.json"
    )
    
    # 2. 测试用例
    test_cases = [
        {
            "name": "简单任务",
            "input": "修改一下这个函数的参数"
        },
        {
            "name": "复杂任务",
            "input": "我需要重构整个 Discord 消息处理系统，涉及 5 个文件，需要支持异步队列、优先级调度、错误重试机制。当前系统在高峰期消息延迟 > 5s，需要优化到 < 500ms。" * 2
        },
        {
            "name": "包含代码的任务",
            "input": "帮我检查这段代码有没有 bug\n```python\ndef process_message(msg):\n    # TODO: 添加错误处理\n    # TODO: 支持异步处理\n    return msg.upper()\n```"
        }
    ]
    
    print("=" * 70)
    print("OpenClaw 智能分流系统演示")
    print("=" * 70)
    
    for test_case in test_cases:
        print(f"\n【{test_case['name']}】")
        print(f"输入: {test_case['input'][:80]}...")
        
        result = await dispatcher.process_user_input(test_case['input'])
        
        print(f"状态: {result['status']}")
        if result['status'] == 'success':
            print(f"复杂度: {result['classification']['complexity']}")
            print(f"原因: {result['classification']['reason']}")
            print(f"置信度: {result['classification']['confidence']:.1%}")
            print(f"行动: {result['action']}")
            if result['action'] == 'route_to_processor':
                print(f"目标 Agent: {result['target_agent']}")
        else:
            print(f"错误: {result.get('error', '未知错误')}")
    
    # 3. Discord Hook 集成示例
    print("\n" + "=" * 70)
    print("Discord Hook 集成示例")
    print("=" * 70)
    
    hook_integration = DiscordHookIntegration(dispatcher)
    
    discord_message = {
        "content": "我需要重构整个系统架构，支持多模块并发处理",
        "author_id": "123456789",
        "channel_id": "987654321",
        "message_id": "111111111"
    }
    
    print(f"\nDiscord 消息: {discord_message['content']}")
    hook_result = await hook_integration.handle_discord_message(discord_message)
    
    print(f"处理结果:")
    print(f"  状态: {hook_result['status']}")
    print(f"  行动: {hook_result['action']}")
    if hook_result['action'] == 'forward_to_agent':
        print(f"  目标 Agent: {hook_result['target_agent']}")
    print(f"  复杂度: {hook_result['metadata'].get('complexity')}")


if __name__ == "__main__":
    asyncio.run(main())
