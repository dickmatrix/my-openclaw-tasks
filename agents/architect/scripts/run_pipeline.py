#!/usr/bin/env python3
"""
run_pipeline.py
一键执行完整流程（演示用）
顺序执行：阶段一建库 -> 阶段二增量 -> 阶段三报告
用法: python3 run_pipeline.py [stage]
  python3 run_pipeline.py all     # 全部阶段
  python3 run_pipeline.py 1      # 仅阶段一
  python3 run_pipeline.py 2      # 仅阶段二
  python3 run_pipeline.py 3      # 仅阶段三
  python3 run_pipeline.py compress [weekly|monthly|quarterly]  # 知识压缩
"""

import subprocess
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def run(script_name, *args):
    script_path = os.path.join(BASE_DIR, "scripts", script_name)
    cmd = ["python3", script_path] + list(args)
    print(f"\n▶ 运行: {' '.join(cmd[1:])}\n")
    result = subprocess.run(cmd, cwd=BASE_DIR)
    if result.returncode != 0:
        print(f"⚠ 脚本退出码: {result.returncode}")
    return result.returncode

def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else "all"
    
    print("=" * 60)
    print("Quant_Analyst 量化分析管道 | stage=", stage)
    print("=" * 60)
    
    if stage == "all":
        run("mock_data_generator.py")
        print("\n" + "="*60)
        run("incremental_pipeline.py", "3")
        print("\n" + "="*60)
        run("daily_strategy.py")
    
    elif stage == "1":
        run("mock_data_generator.py")
    
    elif stage == "2":
        run("incremental_pipeline.py", "3")
    
    elif stage == "3":
        run("daily_strategy.py")
    
    elif stage == "compress":
        freq = sys.argv[2] if len(sys.argv) > 2 else "weekly"
        run("compress_knowledge.py", freq)
    
    else:
        print(f"未知 stage: {stage}")
        print("用法: python3 run_pipeline.py [all|1|2|3|compress]")
        sys.exit(1)
    
    print("\n✅ 流程执行完毕！")

if __name__ == "__main__":
    main()
