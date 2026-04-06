#!/usr/bin/env python3
"""
飞书卡片发送器 - 带防卡死机制
支持卡片验证、超时控制、并发限制、速率限制
"""
import asyncio
import httpx
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import logging
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CardType(Enum):
    """卡片类型"""
    TEXT = "text"
    INTERACTIVE = "interactive"
    SHARE = "share"


@dataclass
class CardConfig:
    """卡片配置"""
    render_timeout: int = 5000  # 毫秒
    max_size: int = 65536  # 字节
    max_elements: int = 100
    max_depth: int = 10
    send_timeout: int = 10  # 秒
    concurrent_sends: int = 5
    rate_limit: int = 20  # 消息/秒


@dataclass
class CardMetrics:
    """卡片指标"""
    total_sent: int = 0
    total_failed: int = 0
    total_timeout: int = 0
    avg_send_time: float = 0.0
    send_times: List[float] = field(default_factory=list)


class FeishuCardSender:
    """飞书卡片发送器"""
    
    def __init__(self, app_id: str, app_secret: str, config: Optional[CardConfig] = None):
        self.app_id = app_id
        self.app_secret = app_secret
        self.config = config or CardConfig()
        self.base_url = "https://open.feishu.cn/open-apis"
        self.access_token = None
        self.token_expire_time = 0
        self.send_semaphore = asyncio.Semaphore(self.config.concurrent_sends)
        self.metrics = CardMetrics()
        self.last_send_time = 0
        self.send_interval = 1.0 / self.config.rate_limit
    
    async def get_access_token(self) -> str:
        """获取访问令牌（带缓存）"""
        current_time = time.time()
        if self.access_token and current_time < self.token_expire_time:
            return self.access_token
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/auth/v3/tenant_access_token/internal",
                    json={
                        "app_id": self.app_id,
                        "app_secret": self.app_secret
                    }
                )
                data = response.json()
                
                if data.get("code") != 0:
                    raise Exception(f"Failed to get token: {data.get('msg')}")
                
                self.access_token = data["tenant_access_token"]
                self.token_expire_time = current_time + data.get("expire", 7200) - 300
                logger.info("Access token refreshed")
                return self.access_token
        except asyncio.TimeoutError:
            logger.error("Token request timeout")
            raise
        except Exception as e:
            logger.error(f"Failed to get token: {e}")
            raise
    
    def validate_card(self, card: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证卡片有效性，返回(是否有效, 错误信息)"""
        try:
            # 检查大小
            card_json = json.dumps(card, ensure_ascii=False)
            card_size = len(card_json.encode('utf-8'))
            
            if card_size > self.config.max_size:
                msg = f"Card size {card_size} exceeds limit {self.config.max_size}"
                logger.warning(msg)
                return False, msg
            
            # 检查元素数量
            element_count = self._count_elements(card)
            if element_count > self.config.max_elements:
                msg = f"Card elements {element_count} exceeds limit {self.config.max_elements}"
                logger.warning(msg)
                return False, msg
            
            # 检查嵌套深度
            depth = self._check_depth(card)
            if depth > self.config.max_depth:
                msg = f"Card depth {depth} exceeds limit {self.config.max_depth}"
                logger.warning(msg)
                return False, msg
            
            logger.debug(f"Card validated: size={card_size}, elements={element_count}, depth={depth}")
            return True, None
        
        except Exception as e:
            msg = f"Card validation error: {e}"
            logger.error(msg)
            return False, msg
    
    def _count_elements(self, obj: Any) -> int:
        """计算对象中的元素数量"""
        if isinstance(obj, dict):
            return sum(self._count_elements(v) for v in obj.values()) + len(obj)
        elif isinstance(obj, list):
            return sum(self._count_elements(item) for item in obj) + len(obj)
        else:
            return 1
    
    def _check_depth(self, obj: Any, current_depth: int = 0) -> int:
        """检查对象嵌套深度"""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._check_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._check_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth
    
    async def _rate_limit(self) -> None:
        """速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_send_time
        
        if time_since_last < self.send_interval:
            await asyncio.sleep(self.send_interval - time_since_last)
        
        self.last_send_time = time.time()
    
    async def send_card(self, chat_id: str, card: Dict[str, Any], 
                       timeout: Optional[int] = None) -> Dict[str, Any]:
        """发送卡片（带防卡死）"""
        timeout = timeout or self.config.send_timeout
        start_time = time.time()
        
        try:
            # 验证卡片
            is_valid, error_msg = self.validate_card(card)
            if not is_valid:
                self.metrics.total_failed += 1
                return {
                    "status": "error",
                    "message": error_msg,
                    "code": "INVALID_CARD"
                }
            
            # 速率限制
            await self._rate_limit()
            
            # 并发控制
            async with self.send_semaphore:
                try:
                    token = await asyncio.wait_for(
                        self.get_access_token(),
                        timeout=timeout
                    )
                    
                    payload = {
                        "receive_id": chat_id,
                        "msg_type": "interactive",
                        "content": json.dumps(card, ensure_ascii=False)
                    }
                    
                    headers = {
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }
                    
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        response = await asyncio.wait_for(
                            client.post(
                                f"{self.base_url}/im/v1/messages?receive_id_type=chat_id",
                                json=payload,
                                headers=headers
                            ),
                            timeout=timeout
                        )
                        
                        result = response.json()
                        elapsed = time.time() - start_time
                        
                        if result.get("code") != 0:
                            self.metrics.total_failed += 1
                            logger.error(f"Failed to send card: {result.get('msg')}")
                            return {
                                "status": "error",
                                "message": result.get('msg'),
                                "code": result.get('code'),
                                "elapsed": elapsed
                            }
                        
                        self.metrics.total_sent += 1
                        self.metrics.send_times.append(elapsed)
                        self.metrics.avg_send_time = sum(self.metrics.send_times) / len(self.metrics.send_times)
                        
                        logger.info(f"Card sent successfully in {elapsed:.2f}s: {result.get('data', {}).get('message_id')}")
                        return {
                            "status": "success",
                            "message_id": result.get("data", {}).get("message_id"),
                            "elapsed": elapsed
                        }
                
                except asyncio.TimeoutError:
                    self.metrics.total_timeout += 1
                    elapsed = time.time() - start_time
                    logger.error(f"Card send timeout after {timeout}s")
                    return {
                        "status": "timeout",
                        "message": f"Send timeout after {timeout}s",
                        "code": "SEND_TIMEOUT",
                        "elapsed": elapsed
                    }
        
        except Exception as e:
            self.metrics.total_failed += 1
            elapsed = time.time() - start_time
            logger.error(f"Error sending card: {e}")
            return {
                "status": "error",
                "message": str(e),
                "code": "SEND_ERROR",
                "elapsed": elapsed
            }
    
    async def send_text_card(self, chat_id: str, title: str, content: str,
                            timeout: Optional[int] = None) -> Dict[str, Any]:
        """发送简单文本卡片"""
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": content,
                        "tag": "lark_md"
                    }
                }
            ],
            "header": {
                "title": {
                    "content": title,
                    "tag": "plain_text"
                }
            }
        }
        
        return await self.send_card(chat_id, card, timeout=timeout)
    
    async def send_batch_cards(self, chat_id: str, cards: List[Dict[str, Any]],
                              timeout: Optional[int] = None) -> List[Dict[str, Any]]:
        """批量发送卡片"""
        tasks = [self.send_card(chat_id, card, timeout=timeout) for card in cards]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        return {
            "total_sent": self.metrics.total_sent,
            "total_failed": self.metrics.total_failed,
            "total_timeout": self.metrics.total_timeout,
            "avg_send_time": self.metrics.avg_send_time,
            "success_rate": self.metrics.total_sent / (self.metrics.total_sent + self.metrics.total_failed) if (self.metrics.total_sent + self.metrics.total_failed) > 0 else 0
        }


async def send_card_safe(app_id: str, app_secret: str, chat_id: str, 
                        card: Dict[str, Any], timeout: int = 10,
                        config: Optional[CardConfig] = None) -> Dict[str, Any]:
    """安全发送卡片"""
    sender = FeishuCardSender(app_id, app_secret, config=config)
    return await sender.send_card(chat_id, card, timeout=timeout)


async def send_text_card_safe(app_id: str, app_secret: str, chat_id: str,
                             title: str, content: str, timeout: int = 10) -> Dict[str, Any]:
    """安全发送文本卡片"""
    sender = FeishuCardSender(app_id, app_secret)
    return await sender.send_text_card(chat_id, title, content, timeout=timeout)


def main(action: str, **kwargs) -> Dict[str, Any]:
    """同步包装器"""
    if action == "send":
        return asyncio.run(send_card_safe(
            app_id=kwargs.get("app_id"),
            app_secret=kwargs.get("app_secret"),
            chat_id=kwargs.get("chat_id"),
            card=kwargs.get("card", {}),
            timeout=kwargs.get("timeout", 10)
        ))
    elif action == "send_text":
        return asyncio.run(send_text_card_safe(
            app_id=kwargs.get("app_id"),
            app_secret=kwargs.get("app_secret"),
            chat_id=kwargs.get("chat_id"),
            title=kwargs.get("title", ""),
            content=kwargs.get("content", ""),
            timeout=kwargs.get("timeout", 10)
        ))
    else:
        return {"status": "error", "message": f"Unknown action: {action}"}


if __name__ == "__main__":
    # 测试
    async def test():
        result = await send_text_card_safe(
            app_id="test_app_id",
            app_secret="test_app_secret",
            chat_id="test_chat_id",
            title="测试卡片",
            content="这是一条测试消息",
            timeout=5
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    asyncio.run(test())
