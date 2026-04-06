import os
import subprocess
import sys
import shutil

def run_openclaw():
    # 获取当前脚本所在目录作为基础路径，适配 Mac 本机与 Docker 环境
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    js_path = os.path.join(base_dir, "openclaw_core/dist/index.js")
    source_config = os.path.join(base_dir, "openclaw.json")
    
    if not os.path.exists(source_config):
        print(f"严重物理断点: 找不到 {source_config}")
        sys.exit(1)
        
    # 使用相对路径下的 .openclaw 目录，避免在根路径下操作权限报错
    state_dir = os.path.join(base_dir, ".openclaw")
    os.makedirs(state_dir, exist_ok=True)

    env = os.environ.copy()
    env["OPENCLAW_CONFIG_PATH"] = source_config
    env["OPENCLAW_STATE_DIR"] = state_dir

    try:
        # 显式指定工作目录为 base_dir
        subprocess.run(["node", js_path, "gateway", "run"], env=env, check=True, cwd=base_dir)
    except Exception as e:
        print(f"主进程异常中断: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_openclaw()
