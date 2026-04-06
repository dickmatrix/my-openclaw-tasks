#!/usr/bin/env python3
"""
Agent招聘专员 - 配置生成脚本
生成Agent配置文件和部署命令
"""

import json
import argparse
from datetime import datetime


def generate_agent_config(
    name: str,
    purpose: str,
    personality: str,
    tools: list,
    trigger_mode: str,
    chat_id: str = None
) -> dict:
    """生成Agent配置"""
    
    config = {
        "agent_name": name,
        "created_at": datetime.now().isoformat(),
        "purpose": purpose,
        "system_prompt": generate_system_prompt(name, purpose, personality),
        "tools": tools,
        "trigger_mode": trigger_mode,
        "chat_id": chat_id,
        "runtime_config": {
            "mode": "session",
            "runtime": "subagent",
            "thread": True
        }
    }
    
    return config


def generate_system_prompt(name: str, purpose: str, personality: str) -> str:
    """根据性格生成system prompt"""
    
    personalities = {
        "专业": f"你是「{name}」，一个专业的AI助手。\n\n**定位**：{purpose}\n**风格**：专业、准确、简洁\n**原则**：\n- 回答基于事实，不确定时明确说明\n- 复杂问题分步骤解释\n- 保持礼貌但不过度寒暄",
        
        "活泼": f"你是「{name}」，一个活力满满的AI助手！🎉\n\n**定位**：{purpose}\n**风格**：热情、有趣、爱用emoji\n**原则**：\n- 用轻松的方式回答问题\n- 适当开玩笑，但不失礼貌\n- 让用户感到愉快",
        
        "严肃": f"你是「{name}」，一个严谨认真的AI助手。\n\n**定位**：{purpose}\n**风格**：正式、严谨、直接\n**原则**：\n- 只说确定的事实\n- 不添加多余修饰\n- 高效解决问题",
        
        "幽默": f"你是「{name}」，一个爱吐槽的AI助手。😏\n\n**定位**：{purpose}\n**风格**：机智、幽默、略带 sarcasm\n**原则**：\n- 用有趣的方式回答问题\n- 适当吐槽，但不冒犯\n- 让用户会心一笑",
        
        "大姐头": f"你是「{name}」，一个雷厉风行的AI助手。\n\n**定位**：{purpose}\n**风格**：直接、高效、不拖泥带水\n**原则**：\n- 少说废话，多办实事\n- 问题说清楚，答案给直接\n- 不绕弯子，不寒暄",
    }
    
    return personalities.get(personality, personalities["专业"])


def generate_spawn_command(config: dict) -> str:
    """生成sessions_spawn命令"""
    
    cmd = f'''sessions_spawn(
    task="{config['purpose']}",
    mode="session",
    runtime="subagent",
    thread=True,
    # 这里可以指定agentId或自定义system prompt
)'''
    
    return cmd


def main():
    parser = argparse.ArgumentParser(description="生成Agent配置")
    parser.add_argument("--name", required=True, help="Agent名称")
    parser.add_argument("--purpose", required=True, help="Agent用途")
    parser.add_argument("--personality", default="专业", help="性格风格")
    parser.add_argument("--tools", default="read,web_search,message", help="工具权限，逗号分隔")
    parser.add_argument("--trigger", default="@触发", help="触发模式")
    parser.add_argument("--chat-id", help="飞书群聊ID")
    parser.add_argument("--output", help="输出文件路径")
    
    args = parser.parse_args()
    
    tools = [t.strip() for t in args.tools.split(",")]
    
    config = generate_agent_config(
        name=args.name,
        purpose=args.purpose,
        personality=args.personality,
        tools=tools,
        trigger_mode=args.trigger,
        chat_id=args.chat_id
    )
    
    output = {
        "config": config,
        "spawn_command": generate_spawn_command(config),
        "notes": [
            "1. 测试通过后再部署到正式群",
            "2. 建议先使用@触发模式",
            "3. 定期检查Agent回复质量"
        ]
    }
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"配置已保存到: {args.output}")
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
