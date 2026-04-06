"""
Task Router & Processor - 智能分流与任务拆解系统

核心逻辑：
1. Router 快速判别任务复杂度
2. Processor 执行高复杂度任务拆解
3. 支持直接处理低复杂度任务
"""

import re
import asyncio
from typing import Literal, Dict, Any
from dataclasses import dataclass


@dataclass
class TaskClassification:
    """任务分类结果"""
    complexity: Literal["LOW", "HIGH"]
    reason: str
    target_model: str
    confidence: float


class TaskRouter:
    """任务路由器 - 判别任务复杂度"""
    
    # 高复杂度关键词
    HIGH_COMPLEXITY_KEYWORDS = {
        "重构", "底层", "全局", "安全", "多模块", 
        "架构", "跨文件", "性能优化", "重设计",
        "refactor", "architecture", "redesign", "security",
        "performance", "optimization", "cross-module"
    }
    
    # 字符数阈值
    CHAR_THRESHOLD = 300
    
    # 代码块比例阈值
    CODE_BLOCK_RATIO_THRESHOLD = 0.5
    
    @classmethod
    def classify(cls, text: str) -> TaskClassification:
        """
        分类任务复杂度
        
        Args:
            text: 用户输入文本
            
        Returns:
            TaskClassification 对象
        """
        reasons = []
        score = 0
        
        # 1. 字符数检查
        char_count = len(text)
        if char_count > cls.CHAR_THRESHOLD:
            reasons.append(f"字符数 {char_count} > {cls.CHAR_THRESHOLD}")
            score += 40
        
        # 2. 关键词检查
        text_lower = text.lower()
        matched_keywords = [
            kw for kw in cls.HIGH_COMPLEXITY_KEYWORDS 
            if kw in text_lower
        ]
        if matched_keywords:
            reasons.append(f"包含关键词: {', '.join(matched_keywords[:3])}")
            score += 30
        
        # 3. 代码块比例检查
        code_blocks = re.findall(r'```[\s\S]*?```', text)
        if code_blocks:
            code_chars = sum(len(block) for block in code_blocks)
            ratio = code_chars / char_count if char_count > 0 else 0
            if ratio > cls.CODE_BLOCK_RATIO_THRESHOLD:
                reasons.append(f"代码块比例 {ratio:.1%} > {cls.CODE_BLOCK_RATIO_THRESHOLD:.0%}")
                score += 20
        
        # 4. TODO/FIXME 检查
        todo_count = len(re.findall(r'(TODO|FIXME)', text, re.IGNORECASE))
        if todo_count > 1:
            reasons.append(f"包含 {todo_count} 个 TODO/FIXME")
            score += 10
        
        # 判定复杂度
        is_high_complexity = score >= 40
        complexity = "HIGH" if is_high_complexity else "LOW"
        target_model = "nscc-minimax-1/MiniMax-M2.5" if is_high_complexity else "nscc-deepseek-7b/DeepSeek-R1-Distill-Qwen-7B"
        confidence = min(score / 100, 1.0)
        
        return TaskClassification(
            complexity=complexity,
            reason=" | ".join(reasons) if reasons else "简单任务",
            target_model=target_model,
            confidence=confidence
        )


class TaskProcessor:
    """任务处理器 - 执行任务拆解"""
    
    DECOMPOSE_PROMPT_TEMPLATE = """
用户需求：
{user_input}

请按照以下格式输出任务拆解方案：

### 1. 需求解析

**原始意图：** [简述]

**核心冲突/痛点：** [逻辑漏洞或技术难点]

### 2. 子任务拆解

| 序号 | 模块 | 修改描述 | 优先级 |
|------|------|--------|------|
| 01 | [路径/组件名] | [具体修改] | 高 |

### 3. 具体的修改描述

#### [文件 A]
- **删除：** [具体内容]
- **新增/修改：** [逻辑说明]

约束：
- 禁止使用"可能"、"大概"、"优化"等模糊词汇
- 精确到函数级别
- 若信息缺失，标记 [信息缺失: 需补充 X]
"""
    
    @classmethod
    def prepare_decompose_prompt(cls, user_input: str) -> str:
        """准备任务拆解提示词"""
        return cls.DECOMPOSE_PROMPT_TEMPLATE.format(user_input=user_input)


class SmartDispatcher:
    """智能分流器 - 协调 Router 和 Processor"""
    
    def __init__(self, router_agent_id: str = "router", processor_agent_id: str = "processor"):
        """
        初始化分流器
        
        Args:
            router_agent_id: Router Agent ID
            processor_agent_id: Processor Agent ID
        """
        self.router_agent_id = router_agent_id
        self.processor_agent_id = processor_agent_id
    
    async def dispatch(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        分流用户输入到合适的处理器
        
        Args:
            user_input: 用户输入
            context: 上下文信息（可选）
            
        Returns:
            {
                "classification": TaskClassification,
                "target_agent": str,
                "decompose_prompt": str (仅当 HIGH_COMPLEXITY 时),
                "metadata": {...}
            }
        """
        # 1. 分类任务
        classification = TaskRouter.classify(user_input)
        
        # 2. 准备响应
        response = {
            "classification": {
                "complexity": classification.complexity,
                "reason": classification.reason,
                "confidence": classification.confidence,
            },
            "target_agent": classification.target_model,
            "target_agent_id": self.processor_agent_id if classification.complexity == "HIGH" else None,
            "metadata": {
                "char_count": len(user_input),
                "timestamp": None,
            }
        }
        
        # 3. 若为高复杂度，准备拆解提示词
        if classification.complexity == "HIGH":
            response["decompose_prompt"] = TaskProcessor.prepare_decompose_prompt(user_input)
        
        return response


if __name__ == "__main__":
    test_cases = [
        "修改一下这个函数的参数",
        "我需要重构整个 Discord 消息处理系统，涉及 5 个文件，需要支持异步队列、优先级调度、错误重试机制。当前系统在高峰期消息延迟 > 5s，需要优化到 < 500ms。" * 2,
        "帮我检查这段代码有没有 bug\n```python\ndef foo():\n    pass\n```",
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"测试用例 {i}")
        print(f"{'='*60}")
        print(f"输入长度: {len(test)} 字符")
        print(f"输入预览: {test[:100]}...")
        
        classification = TaskRouter.classify(test)
        print(f"\n分类结果:")
        print(f"  复杂度: {classification.complexity}")
        print(f"  原因: {classification.reason}")
        print(f"  目标模型: {classification.target_model}")
        print(f"  置信度: {classification.confidence:.1%}")
