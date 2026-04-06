#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Agent 联动 - 飞书 Bot 命令处理器
用途: 处理飞书群中的 @Bot 命令，触发对应的 Agent 执行
"""

import os
import json
import logging
import asyncio
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import requests
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 常量定义
GATEWAY_URL = os.getenv('OPENCLAW_GATEWAY_URL', 'http://127.0.0.1:18789')
GATEWAY_TOKEN = os.getenv('GATEWAY_TOKEN', '')
PROJECT_ROOT = Path('/Users/mac/Documents/龙虾相关/my_openclaw')
LOG_DIR = Path('/Users/mac/.openclaw/logs')

class AgentType(Enum):
    """Agent 类型枚举"""
    SCOUT = "scout"
    CENSOR = "censor"
    WRITER = "writer"
    AUDITOR = "auditor"

class FeishuBotHandler:
    """飞书 Bot 命令处理器"""
    
    def __init__(self):
        self.gateway_url = GATEWAY_URL
        self.gateway_token = GATEWAY_TOKEN
        self.project_root = PROJECT_ROOT
        self.log_dir = LOG_DIR
        
        # 命令映射
        self.command_map = {
            'scan': (AgentType.SCOUT, self.handle_scout_scan),
            'analyze': (AgentType.SCOUT, self.handle_scout_analyze),
            'report': (AgentType.SCOUT, self.handle_scout_report),
            'verify': (AgentType.CENSOR, self.handle_censor_verify),
            'check': (AgentType.CENSOR, self.handle_censor_check),
            'validate': (AgentType.CENSOR, self.handle_censor_validate),
            'modify': (AgentType.WRITER, self.handle_writer_modify),
            'optimize': (AgentType.WRITER, self.handle_writer_optimize),
            'refactor': (AgentType.WRITER, self.handle_writer_refactor),
            'audit': (AgentType.AUDITOR, self.handle_auditor_audit),
            'test': (AgentType.AUDITOR, self.handle_auditor_test),
        }
    
    def parse_command(self, message: str) -> Optional[Dict[str, Any]]:
        """解析飞书消息中的命令"""
        try:
            parts = message.strip().split()
            if len(parts) < 2:
                return None
            
            command = parts[1].lower()
            args = parts[2:] if len(parts) > 2 else []
            
            if command not in self.command_map:
                return None
            
            agent_type, handler = self.command_map[command]
            
            return {
                'command': command,
                'agent': agent_type,
                'handler': handler,
                'args': args,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"命令解析失败: {e}")
            return None
    
    # Scout 处理器
    async def handle_scout_scan(self, args: list) -> Dict[str, Any]:
        """处理 Scout 扫描命令"""
        logger.info(f"Scout 扫描: {args}")
        if not args:
            return {'status': 'error', 'message': '缺少扫描路径参数'}
        
        try:
            result = await self._call_agent(AgentType.SCOUT, 'scan', {'path': args[0]})
            return {'status': 'success', 'message': f'扫描完成: {args[0]}', 'data': result}
        except Exception as e:
            logger.error(f"Scout 扫描失败: {e}")
            return {'status': 'error', 'message': f'扫描失败: {str(e)}'}
    
    async def handle_scout_analyze(self, args: list) -> Dict[str, Any]:
        """处理 Scout 分析命令"""
        logger.info(f"Scout 分析: {args}")
        if not args:
            return {'status': 'error', 'message': '缺少分析文件参数'}
        
        try:
            result = await self._call_agent(AgentType.SCOUT, 'analyze', {'file': args[0]})
            return {'status': 'success', 'message': f'分析完成: {args[0]}', 'data': result}
        except Exception as e:
            logger.error(f"Scout 分析失败: {e}")
            return {'status': 'error', 'message': f'分析失败: {str(e)}'}
    
    async def handle_scout_report(self, args: list) -> Dict[str, Any]:
        """处理 Scout 报告命令"""
        logger.info("Scout 生成报告")
        try:
            result = await self._call_agent(AgentType.SCOUT, 'report', {})
            return {'status': 'success', 'message': '报告已生成', 'data': result}
        except Exception as e:
            logger.error(f"Scout 报告生成失败: {e}")
            return {'status': 'error', 'message': f'报告生成失败: {str(e)}'}
    
    # Censor 处理器
    async def handle_censor_verify(self, args: list) -> Dict[str, Any]:
        """处理 Censor 验证命令"""
        logger.info("Censor 验证")
        try:
            result = await self._call_agent(AgentType.CENSOR, 'verify', {})
            return {'status': 'success', 'message': '验证完成', 'data': result}
        except Exception as e:
            logger.error(f"Censor 验证失败: {e}")
            return {'status': 'error', 'message': f'验证失败: {str(e)}'}
    
    async def handle_censor_check(self, args: list) -> Dict[str, Any]:
        """处理 Censor 检查命令"""
        logger.info("Censor 检查")
        try:
            result = await self._call_agent(AgentType.CENSOR, 'check', {})
            return {'status': 'success', 'message': '检查完成', 'data': result}
        except Exception as e:
            logger.error(f"Censor 检查失败: {e}")
            return {'status': 'error', 'message': f'检查失败: {str(e)}'}
    
    async def handle_censor_validate(self, args: list) -> Dict[str, Any]:
        """处理 Censor 验证配置命令"""
        logger.info("Censor 验证配置")
        try:
            result = await self._call_agent(AgentType.CENSOR, 'validate', {})
            return {'status': 'success', 'message': '配置验证完成', 'data': result}
        except Exception as e:
            logger.error(f"Censor 配置验证失败: {e}")
            return {'status': 'error', 'message': f'配置验证失败: {str(e)}'}
    
    # Writer 处理器
    async def handle_writer_modify(self, args: list) -> Dict[str, Any]:
        """处理 Writer 修改命令"""
        logger.info(f"Writer 修改: {args}")
        if not args:
            return {'status': 'error', 'message': '缺少修改文件参数'}
        
        try:
            result = await self._call_agent(AgentType.WRITER, 'modify', {'file': args[0]})
            return {'status': 'success', 'message': f'修改完成: {args[0]}', 'data': result}
        except Exception as e:
            logger.error(f"Writer 修改失败: {e}")
            return {'status': 'error', 'message': f'修改失败: {str(e)}'}
    
    async def handle_writer_optimize(self, args: list) -> Dict[str, Any]:
        """处理 Writer 优化命令"""
        logger.info(f"Writer 优化: {args}")
        if not args:
            return {'status': 'error', 'message': '缺少优化文件参数'}
        
        try:
            result = await self._call_agent(AgentType.WRITER, 'optimize', {'file': args[0]})
            return {'status': 'success', 'message': f'优化完成: {args[0]}', 'data': result}
        except Exception as e:
            logger.error(f"Writer 优化失败: {e}")
            return {'status': 'error', 'message': f'优化失败: {str(e)}'}
    
    async def handle_writer_refactor(self, args: list) -> Dict[str, Any]:
        """处理 Writer 重构命令"""
        logger.info(f"Writer 重构: {args}")
        if not args:
            return {'status': 'error', 'message': '缺少重构文件参数'}
        
        try:
            result = await self._call_agent(AgentType.WRITER, 'refactor', {'file': args[0]})
            return {'status': 'success', 'message': f'重构完成: {args[0]}', 'data': result}
        except Exception as e:
            logger.error(f"Writer 重构失败: {e}")
            return {'status': 'error', 'message': f'重构失败: {str(e)}'}
    
    # Auditor 处理器
    async def handle_auditor_audit(self, args: list) -> Dict[str, Any]:
        """处理 Auditor 审计命令"""
        logger.info("Auditor 审计")
        try:
            result = await self._call_agent(AgentType.AUDITOR, 'audit', {})
            return {'status': 'success', 'message': '审计完成', 'data': result}
        except Exception as e:
            logger.error(f"Auditor 审计失败: {e}")
            return {'status': 'error', 'message': f'审计失败: {str(e)}'}
    
    async def handle_auditor_test(self, args: list) -> Dict[str, Any]:
        """处理 Auditor 测试命令"""
        logger.info("Auditor 运行测试")
        try:
            result = await self._call_agent(AgentType.AUDITOR, 'test', {})
            return {'status': 'success', 'message': '测试完成', 'data': result}
        except Exception as e:
            logger.error(f"Auditor 测试失败: {e}")
            return {'status': 'error', 'message': f'测试失败: {str(e)}'}
    
    async def _call_agent(self, agent: AgentType, action: str, params: Dict) -> Dict[str, Any]:
        """调用 Agent"""
        try:
            url = f"{self.gateway_url}/agents/{agent.value}/{action}"
            headers = {
                'Authorization': f'Bearer {self.gateway_token}',
                'Content-Type': 'application/json'
            }
            response = requests.post(url, json=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"调用 Agent 失败: {e}")
            raise
    
    async def process_command(self, message: str) -> Dict[str, Any]:
        """处理命令"""
        try:
            cmd_info = self.parse_command(message)
            if not cmd_info:
                return {'status': 'error', 'message': '无法识别的命令'}
            
            handler = cmd_info['handler']
            result = await handler(cmd_info['args'])
            return result
        except Exception as e:
            logger.error(f"处理命令失败: {e}")
            return {'status': 'error', 'message': f'处理失败: {str(e)}'}

async def test_handler():
    """测试处理器"""
    handler = FeishuBotHandler()
    test_commands = [
        "@Scout 扫描 /app/workspace",
        "@Censor 检查",
        "@Writer 优化 /path/to/file",
        "@Auditor 审计"
    ]
    
    for cmd in test_commands:
        logger.info(f"测试命令: {cmd}")
        result = await handler.process_command(cmd)
        logger.info(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        print()

if __name__ == '__main__':
    asyncio.run(test_handler())
