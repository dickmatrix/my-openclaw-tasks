import asyncio
import time
from task_manager import TaskStateManager

async def test_parallelism():
    manager = TaskStateManager()
    
    # 清空之前的任务 (模拟环境)
    manager.state["tasks"] = []
    
    # 创建 3 个独立子任务
    tasks = [
        manager.create_task("Task 1: Simple extraction", "sakura"),
        manager.create_task("Task 2: Code refactoring", "naruto"),
        manager.create_task("Task 3: Documentation", "sakura")
    ]
    
    print(f"[*] Starting parallel execution of {len(tasks)} tasks...")
    start_time = time.time()
    
    # 运行并行任务
    await manager.run_parallel_tasks()
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    print(f"\n[!] Total execution time: {total_duration:.2f}s")
    print(f"[!] Max single task time (simulated): 1.00s")
    
    if total_duration <= 1.2:
        print("\n✅ Parallelism verification PASSED!")
    else:
        print("\n❌ Parallelism verification FAILED!")

def test_routing_and_context():
    manager = TaskStateManager()
    
    print("\n[*] Testing Smart Routing...")
    # 简单任务
    agent_simple = manager.get_agent_for_task("提取这段话的关键词")
    print(f"Simple task routed to: {agent_simple}")
    assert agent_simple == "sakura"
    
    # 复杂任务
    agent_complex = manager.get_agent_for_task("重构现有的性能架构并优化")
    print(f"Complex task routed to: {agent_complex}")
    assert agent_complex == "naruto"
    
    print("✅ Smart Routing verification PASSED!")
    
    print("\n[*] Testing Context Window Control...")
    messages = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
    limited = manager.apply_context_window(messages, window_size=3)
    print(f"Original messages: {len(messages)}, Limited: {len(limited)}")
    assert len(limited) == 6 # 3 * 2
    print("✅ Context Window verification PASSED!")

if __name__ == "__main__":
    asyncio.run(test_parallelism())
    test_routing_and_context()
