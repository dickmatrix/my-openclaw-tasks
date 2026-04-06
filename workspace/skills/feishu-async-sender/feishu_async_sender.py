#!/usr/bin/env python3
"""
飞书异步发送 Skill - 带指数退避逻辑的高并发消息发送
支持流式反馈、消息聚合、速率限制处理
"""
import asyncio
import httpx
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""
    TEXT = "text"
    CARD = "interactive"
    POST = "post"


@dataclass
class Message:
    """飞书消息"""
    content: str
    msg_type: MessageType = MessageType.TEXT
    chat_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 5
    initial_delay: float = 0.5  # 初始延迟 500ms
    max_delay: float = 30.0  # 最大延迟 30s
    exponential_base: float = 2.0  # 指数基数


class FeishuAsyncSender:
    """飞书异步发送器"""
    
    def __init__(self, app_id: str, app_secret: str, retry_config: Optional[RetryConfig] = None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.retry_config = retry_config or RetryConfig()
        self.base_url = "https://open.feishu.cn/open-apis"
        self.access_token = None
        self.token_expire_time = 0
        self.message_buffer = []
        self.buffer_lock = asyncio.Lock()
        self.buffer_flush_interval = 0.5  # 500ms 聚合发送
        self.last_flush_time = time.time()
    
    async def get_access_token(self) -> str:
        """获取访问令牌（带缓存）"""
        current_time = time.time()
        if self.access_token and current_time < self.token_expire_time:
            return self.access_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": self.app_id,
                    "app_secret": self.app_secret
                },
                timeout=10.0
            )
            data = response.json()
            
            if data.get("code") != 0:
                raise Exception(f"Failed to get access token: {data.get('msg')}")
            
            self.access_token = data["tenant_access_token"]
            self.token_expire_time = current_time + data.get("expire", 7200) - 300
            return self.access_token
    
    async def send_message_with_retry(self, message: Message) -> Dict[str, Any]:
        """发送消息（带指数退避重试）"""
        retry_count = 0
        delay = self.retry_config.initial_delay
        
        while retry_count <= self.retry_config.max_retries:
            try:
                return await self._send_message_internal(message)
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # 速率限制
                    retry_count += 1
                    if retry_count > self.retry_config.max_retries:
                        logger.error(f"Max retries exceeded for message to {message.chat_id}")
                        raise
                    
                    # 指数退避
                    delay = min(
                        self.retry_config.initial_delay * (self.retry_config.exponential_base ** (retry_count - 1)),
                        self.retry_config.max_delay
                    )
                    # 添加随机抖动 (±20%)
                    jitter = delay * 0.2 * (2 * asyncio.get_event_loop().time() % 1 - 1)
                    actual_delay = delay + jitter
                    
                    logger.warning(f"Rate limited. Retry {retry_count}/{self.retry_config.max_retries} after {actual_delay:.2f}s")
                    await asyncio.sleep(actual_delay)
                else:
                    raise
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                raise
        
        raise Exception("Failed to send message after all retries")
    
    async def _send_message_internal(self, message: Message) -> Dict[str, Any]:
        """内部消息发送逻辑"""
        token = await self.get_access_token()
        
        # 构建请求体
        payload = {
            "msg_type": message.msg_type.value,
            "content": json.dumps({"text": message.content}) if message.msg_type == MessageType.TEXT else message.content
        }
        
        # 确定目标
        if message.chat_id:
            endpoint = f"{self.base_url}/im/v1/messages?receive_id_type=chat_id"
            payload["receive_id"] = message.chat_id
        elif message.user_id:
            endpoint = f"{self.base_url}/im/v1/messages?receive_id_type=user_id"
            payload["receive_id"] = message.user_id
        else:
            raise ValueError("Either chat_id or user_id must be provided")
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
    
    async def buffer_message(self, message: Message) -> None:
        """将消息加入缓冲区"""
        async with self.buffer_lock:
            self.message_buffer.append(message)
            
            # 检查是否需要立即刷新
            current_time = time.time()
            if current_time - self.last_flush_time >= self.buffer_flush_interval:
                await self._flush_buffer()
    
    async def _flush_buffer(self) -> None:
        """刷新缓冲区，批量发送消息"""
        if not self.message_buffer:
            return
        
        messages_to_send = self.message_buffer.copy()
        self.message_buffer.clear()
        self.last_flush_time = time.time()
        
        # 并发发送所有消息
        tasks = [self.send_message_with_retry(msg) for msg in messages_to_send]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to send message {i}: {result}")
            else:
                logger.info(f"Message {i} sent successfully: {result.get('data', {}).get('message_id')}")
    
    async def send_streaming_message(self, chat_id: str, initial_content: str, 
                                     content_generator) -> str:
        """发送流式消息（打字机效果）
        
        Args:
            chat_id: 聊天 ID
            initial_content: 初始内容
            content_generator: 异步生成器，逐步产生内容
            
        Returns:
            str: 最终消息 ID
        """
        token = await self.get_access_token()
        
        # 发送初始消息
        initial_msg = Message(content=initial_content, chat_id=chat_id)
        result = await self.send_message_with_retry(initial_msg)
        message_id = result.get("data", {}).get("message_id")
        
        if not message_id:
            raise Exception("Failed to create initial message")
        
        # 流式更新消息
        accumulated_content = initial_content
        async for chunk in content_generator:
            accumulated_content += chunk
            
            # 每 500ms 更新一次
            await asyncio.sleep(0.5)
            
            update_payload = {
                "content": json.dumps({"text": accumulated_content})
            }
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            try:
                async with httpx.AsyncClient() as client:
                    await client.patch(
                        f"{self.base_url}/im/v1/messages/{message_id}",
                        json=update_payload,
                        headers=headers,
                        timeout=10.0
                    )
            except Exception as e:
                logger.error(f"Failed to update message: {e}")
        
        return message_id


async def send_message(app_id: str, app_secret: str, chat_id: str, 
                      content: str, msg_type: str = "text", **kwargs) -> Dict[str, Any]:
    """主入口函数 - 发送单条消息"""
    sender = FeishuAsyncSender(app_id, app_secret)
    
    message = Message(
        content=content,
        msg_type=MessageType(msg_type),
        chat_id=chat_id
    )
    
    return await sender.send_message_with_retry(message)


async def send_batch_messages(app_id: str, app_secret: str, 
                             messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """批量发送消息"""
    sender = FeishuAsyncSender(app_id, app_secret)
    
    tasks = []
    for msg_data in messages:
        message = Message(
            content=msg_data["content"],
            msg_type=MessageType(msg_data.get("msg_type", "text")),
            chat_id=msg_data.get("chat_id"),
            user_id=msg_data.get("user_id")
        )
        tasks.append(sender.send_message_with_retry(message))
    
    return await asyncio.gather(*tasks, return_exceptions=True)


def main(action: str, **kwargs) -> Dict[str, Any]:
    """同步包装器"""
    if action == "send":
        return asyncio.run(send_message(
            app_id=kwargs.get("app_id"),
            app_secret=kwargs.get("app_secret"),
            chat_id=kwargs.get("chat_id"),
            content=kwargs.get("content"),
            msg_type=kwargs.get("msg_type", "text")
        ))
    elif action == "send_batch":
        return asyncio.run(send_batch_messages(
            app_id=kwargs.get("app_id"),
            app_secret=kwargs.get("app_secret"),
            messages=kwargs.get("messages", [])
        ))
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


if __name__ == "__main__":
    # 测试代码
    test_result = asyncio.run(send_message(
        app_id="test_app_id",
        app_secret="test_app_secret",
        chat_id="test_chat_id",
        content="测试消息"
    ))
    print(json.dumps(test_result, ensure_ascii=False, indent=2))
