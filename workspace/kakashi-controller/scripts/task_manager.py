#!/usr/bin/env python3
"""
卡卡西 - 任务调度脚本
负责任务分配、状态管理和异常处理
"""

import json
import uuid
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "global_tasks_state.json")


class TaskStateManager:
    """任务状态管理器 - 性能优化版"""
    
    def __init__(self, state_file: str = STATE_FILE):
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        """加载状态文件"""
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return self._init_state()
    
    def _init_state(self) -> dict:
        """初始化状态文件"""
        return {
            "schema": "global_task_state.v1",
            "last_updated": datetime.now().isoformat(),
            "tasks": [],
            "agents": {
                "naruto": {"status": "idle", "last_heartbeat": "", "model": "gpt-4o"},
                "sasuke": {"status": "idle", "last_heartbeat": "", "model": "gpt-4o"},
                "sakura": {"status": "idle", "last_heartbeat": "", "model": "gpt-4o-mini"}
            },
            "system": {
                "kakashi_status": "active",
                "critical_errors": [],
                "parallel_execution": True
            }
        }
    
    def save_state(self):
        """保存状态文件"""
        self.state["last_updated"] = datetime.now().isoformat()
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
    
    def create_task(self, user_request: str, agent_type: str, priority: str = "normal") -> str:
        """创建新任务"""
        task_id = str(uuid.uuid4())[:8]
        task = {
            "task_id": task_id,
            "user_request": user_request,
            "status": "pending",
            "assigned_agent": agent_type,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "retry_count": 0,
            "priority": priority,
            "result": None,
            "error_log": [],
            "dependencies": [] # 用于依赖图
        }
        self.state["tasks"].append(task)
        self.save_state()
        return task_id
    
    def update_task_status(self, task_id: str, status: str, result: Optional[str] = None):
        """更新任务状态"""
        for task in self.state["tasks"]:
            if task["task_id"] == task_id:
                task["status"] = status
                task["updated_at"] = datetime.now().isoformat()
                if result:
                    task["result"] = result
                break
        self.save_state()
    
    async def execute_task_async(self, task: dict):
        """异步执行单个任务"""
        task_id = task["task_id"]
        print(f"[*] Executing task {task_id} on agent {task['assigned_agent']}...")
        self.update_task_status(task_id, "running")
        
        # 模拟任务处理开销
        await asyncio.sleep(1) 
        
        print(f"[+] Task {task_id} completed.")
        self.update_task_status(task_id, "completed", result="Execution successful (simulated)")

    async def run_parallel_tasks(self):
        """Action Item A: 并发分发无依赖子任务"""
        pending_tasks = self.get_pending_tasks()
        if not pending_tasks:
            return

        # 简单依赖图过滤：仅处理无前置依赖的任务
        executable_tasks = [t for t in pending_tasks if not t.get("dependencies")]
        
        if executable_tasks:
            print(f"[*] Launching {len(executable_tasks)} tasks in parallel...")
            await asyncio.gather(*(self.execute_task_async(t) for t in executable_tasks))

    def get_agent_for_task(self, user_request: str) -> str:
        """Action Item D: 智能路由 (Model Routing)"""
        request_lower = user_request.lower()
        
        # 简单任务路由至 gpt-4o-mini (Sakura)
        # 非推理类任务：提取、格式化、简单总结
        simple_keywords = ["提取", "格式化", "总结", "翻译", "转换", "列出"]
        if any(kw in request_lower for kw in simple_keywords) and len(user_request) < 1000:
            return "sakura"
        
        # 复杂推理路由至 gpt-4o (Naruto)
        complex_keywords = ["重构", "架构", "优化", "设计", "性能", "调试", "复杂"]
        if any(kw in request_lower for kw in complex_keywords):
            return "naruto"
            
        # 默认路由至 Sasuke
        return "sasuke"
    
    def apply_context_window(self, messages: List[dict], window_size: int = 5) -> List[dict]:
        """Action Item C: Summary Buffer Window"""
        # 仅保留最近 window_size 轮对话 (每轮通常包括 user 和 assistant)
        limit = window_size * 2
        if len(messages) <= limit:
            return messages
        return messages[-limit:]

    def rag_pre_filter(self, query: str, documents: List[str], top_k: int = 3) -> List[str]:
        """Action Item C: RAG 预过滤 (Top-K)"""
        # 简化版实现：基于关键词重合度的向量相似度模拟
        scored_docs = []
        query_words = set(query.lower().split())
        
        for doc in documents:
            doc_words = set(doc.lower().split())
            score = len(query_words.intersection(doc_words)) / max(len(query_words), 1)
            scored_docs.append((score, doc))
            
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:top_k]]
    
    def check_idle_timeout(self, timeout_minutes: int = 5) -> bool:
        """检查是否超过静止时间"""
        last_updated = datetime.fromisoformat(self.state["last_updated"])
        return datetime.now() - last_updated > timedelta(minutes=timeout_minutes)
    
    def get_pending_tasks(self) -> List[dict]:
        """获取待处理任务"""
        return [t for t in self.state["tasks"] if t["status"] == "pending"]
    
    def get_running_tasks(self) -> List[dict]:
        """获取进行中任务"""
        return [t for t in self.state["tasks"] if t["status"] == "running"]
    
    def check_stuck_tasks(self, timeout_minutes: int = 30) -> List[dict]:
        """检查阻塞任务（L3检测）"""
        stuck = []
        for task in self.state["tasks"]:
            if task["status"] == "running":
                updated = datetime.fromisoformat(task["updated_at"])
                if datetime.now() - updated > timedelta(minutes=timeout_minutes):
                    stuck.append(task)
        return stuck


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="卡卡西任务调度")
    parser.add_argument("--create-task", help="创建新任务")
    parser.add_argument("--agent", help="指定Agent类型")
    parser.add_argument("--update-status", help="更新任务状态")
    parser.add_argument("--task-id", help="任务ID")
    parser.add_argument("--check-idle", action="store_true", help="检查静止状态")
    parser.add_argument("--check-stuck", action="store_true", help="检查阻塞任务")
    
    args = parser.parse_args()
    
    manager = TaskStateManager()
    
    if args.create_task:
        agent = args.agent or manager.get_agent_for_task(args.create_task)
        task_id = manager.create_task(args.create_task, agent)
        print(f"Task created: {task_id} -> {agent}")
    
    elif args.update_status and args.task_id:
        manager.update_task_status(args.task_id, args.update_status)
        print(f"Task {args.task_id} status updated to {args.update_status}")
    
    elif args.check_idle:
        is_idle = manager.check_idle_timeout()
        print(f"Idle timeout: {is_idle}")
    
    elif args.check_stuck:
        stuck = manager.check_stuck_tasks()
        print(f"Stuck tasks: {len(stuck)}")
        for t in stuck:
            print(f"  - {t['task_id']}: {t['user_request'][:50]}...")
    
    else:
        # 打印当前状态
        print(json.dumps(manager.state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
