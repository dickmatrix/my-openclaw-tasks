#!/usr/bin/env python3
"""
飞书Bot诊断和测试脚本
用于检查Gateway、Bot连接和卡片发送
"""
import subprocess
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, Any, Tuple


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_gateway_listen_port() -> int:
    cfg = _repo_root() / "openclaw.json"
    try:
        with cfg.open(encoding="utf-8") as f:
            data = json.load(f)
        return int(data.get("gateway", {}).get("port") or 18889)
    except Exception:
        return 18889


def get_gateway_host_port() -> int:
    """与 scripts/openclaw-gateway.sh host-port 一致（本机 curl / lsof 用）。"""
    helper = Path(__file__).resolve().parent / "openclaw-gateway.sh"
    if helper.is_file():
        try:
            result = subprocess.run(
                [str(helper), "host-port"],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            out = result.stdout.strip()
            if result.returncode == 0 and out.isdigit():
                return int(out)
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
    return get_gateway_listen_port()

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg: str):
    print(f"{Colors.GREEN}✓ {msg}{Colors.END}")

def print_error(msg: str):
    print(f"{Colors.RED}✗ {msg}{Colors.END}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.END}")

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.END}")

def check_gateway_process() -> Tuple[bool, str]:
    """检查Gateway进程"""
    print_info("检查Gateway进程...")
    try:
        result = subprocess.run(
            ["pgrep", "-f", "openclaw-gateway"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            pid = result.stdout.strip()
            print_success(f"Gateway进程运行中 (PID: {pid})")
            return True, pid
        else:
            print_error("Gateway进程未运行")
            return False, ""
    except Exception as e:
        print_error(f"检查进程失败: {e}")
        return False, ""

def check_gateway_port() -> bool:
    """检查Gateway端口"""
    port = get_gateway_host_port()
    print_info(f"检查Gateway端口 ({port}, 与 scripts/openclaw-gateway.sh host-port 一致)...")
    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success(f"端口{port}已监听")
            return True
        else:
            print_error(f"端口{port}未监听")
            return False
    except Exception as e:
        print_error(f"检查端口失败: {e}")
        return False

def check_gateway_health() -> bool:
    """检查Gateway健康状态"""
    port = get_gateway_host_port()
    print_info("检查Gateway健康状态...")
    try:
        result = subprocess.run(
            ["curl", "-s", "-m", "5", f"http://127.0.0.1:{port}/health"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print_success("Gateway健康检查通过")
            return True
        else:
            print_warning("Gateway健康检查超时或失败")
            return False
    except Exception as e:
        print_warning(f"Gateway健康检查异常: {e}")
        return False

def check_environment_variables() -> bool:
    """检查环境变量"""
    print_info("检查环境变量...")
    
    required_vars = [
        "FEISHU_MAC_APP_ID",
        "FEISHU_MAC_APP_SECRET",
        "GATEWAY_TOKEN"
    ]
    
    all_ok = True
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # 隐藏敏感信息
            masked = value[:10] + "***" if len(value) > 10 else "***"
            print_success(f"{var} = {masked}")
        else:
            print_error(f"{var} 未设置")
            all_ok = False
    
    return all_ok

def check_gateway_logs() -> bool:
    """检查Gateway日志"""
    print_info("检查Gateway日志...")
    
    log_file = "/Users/mac/.openclaw/logs/gateway.log"
    if not os.path.exists(log_file):
        print_warning(f"日志文件不存在: {log_file}")
        return False
    
    try:
        # 读取最后50行
        result = subprocess.run(
            ["tail", "-50", log_file],
            capture_output=True,
            text=True
        )
        
        logs = result.stdout
        
        # 检查错误
        if "error" in logs.lower() or "exception" in logs.lower():
            print_warning("日志中发现错误信息")
            # 显示错误行
            for line in logs.split('\n'):
                if "error" in line.lower() or "exception" in line.lower():
                    print(f"  {line[:100]}")
            return False
        else:
            print_success("日志中未发现明显错误")
            return True
    except Exception as e:
        print_error(f"读取日志失败: {e}")
        return False

def check_bot_config() -> bool:
    """检查Bot配置"""
    print_info("检查Bot配置...")
    
    config_file = "/Users/mac/Documents/龙虾相关/my_openclaw/feishu_bot_config.json"
    if not os.path.exists(config_file):
        print_error(f"配置文件不存在: {config_file}")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        bots = config.get("feishu_bots", [])
        print_success(f"找到 {len(bots)} 个Bot配置")
        
        for bot in bots:
            name = bot.get("name", "Unknown")
            status = bot.get("status", "unknown")
            print(f"  - {name}: {status}")
        
        return True
    except Exception as e:
        print_error(f"读取配置失败: {e}")
        return False

def check_cpu_memory() -> bool:
    """检查CPU和内存占用"""
    print_info("检查Gateway资源占用...")
    
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        
        for line in result.stdout.split('\n'):
            if "openclaw-gateway" in line and "grep" not in line:
                parts = line.split()
                if len(parts) >= 4:
                    cpu = parts[2]
                    mem = parts[3]
                    print(f"  CPU: {cpu}%, Memory: {mem}%")
                    
                    # 检查是否超过阈值
                    try:
                        cpu_val = float(cpu)
                        mem_val = float(mem)
                        
                        if cpu_val > 80:
                            print_warning(f"CPU占用过高: {cpu}%")
                            return False
                        if mem_val > 80:
                            print_warning(f"内存占用过高: {mem}%")
                            return False
                        
                        print_success("资源占用正常")
                        return True
                    except ValueError:
                        pass
        
        print_warning("未找到Gateway进程")
        return False
    except Exception as e:
        print_error(f"检查资源失败: {e}")
        return False

def run_diagnostics() -> Dict[str, bool]:
    """运行完整诊断"""
    print("\n" + "="*50)
    print("飞书Bot诊断工具")
    print("="*50 + "\n")
    
    results = {}
    
    # 检查环境变量
    results["environment"] = check_environment_variables()
    print()
    
    # 检查Gateway进程
    process_ok, pid = check_gateway_process()
    results["process"] = process_ok
    print()
    
    # 检查端口
    results["port"] = check_gateway_port()
    print()
    
    # 检查健康状态
    results["health"] = check_gateway_health()
    print()
    
    # 检查资源占用
    results["resources"] = check_cpu_memory()
    print()
    
    # 检查日志
    results["logs"] = check_gateway_logs()
    print()
    
    # 检查Bot配置
    results["config"] = check_bot_config()
    print()
    
    return results

def print_summary(results: Dict[str, bool]):
    """打印诊断总结"""
    print("="*50)
    print("诊断总结")
    print("="*50)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n通过检查: {passed}/{total}\n")
    
    for check, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {check}: {status}")
    
    print()
    
    if passed == total:
        print_success("所有检查通过！Bot应该可以正常工作")
        return 0
    else:
        print_error("存在失败的检查，请查看上面的详细信息")
        print("\n建议的修复步骤:")
        print("1. 运行修复脚本: bash fix_feishu_bot.sh")
        print(
            "2. 重启Gateway: pkill -9 openclaw-gateway && sleep 2 && "
            f"openclaw gateway --port {get_gateway_listen_port()}"
        )
        print("3. 查看日志: tail -f /Users/mac/.openclaw/logs/gateway.log")
        return 1

def main():
    """主函数"""
    try:
        results = run_diagnostics()
        exit_code = print_summary(results)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n诊断被中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"诊断过程出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
