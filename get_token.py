#!/usr/bin/env python3
"""获取 GitHub Copilot GHU_ Token

使用 GitHub Device Flow 授权，无需密码，扫码/输入验证码即可。
获取的 token 自动写入 ./tokens/ 目录，触发 orchestrator 热补给。
"""

import requests
import time
import os
import sys
from datetime import datetime

# GitHub Copilot 官方编辑器插件 Client ID
# CLIENT_ID = "01ab8ac9411c470473ee"  # 旧版，部分代理环境不可用
CLIENT_ID = "Iv1.b507a08c87ecfe98"  # GitHub CLI client_id，兼容性更好
TOKENS_DIR = "./tokens"
POOL_FILE = "./token_pool.txt"

# 代理配置（使用本机专线）
PROXIES = {
    "http": os.environ.get("HTTP_PROXY", "http://127.0.0.1:7897"),
    "https": os.environ.get("HTTPS_PROXY", "http://127.0.0.1:7897"),
}


def get_ghu_token(save_to_pool: bool = True) -> str | None:
    """通过 Device Flow 获取 GHU_ token，成功后写入 tokens/ 目录"""
    print("[*] 正在向 GitHub 请求设备码...")

    try:
        resp = requests.post(
            "https://github.com/login/device/code",
            data={"client_id": CLIENT_ID, "scope": "read:user"},
            headers={"Accept": "application/json"},
            proxies=PROXIES,
            timeout=15,
        ).json()
    except Exception as e:
        print(f"[-] 请求失败: {e}")
        return None

    user_code = resp.get("user_code")
    device_code = resp.get("device_code")
    interval = resp.get("interval", 5)
    expires_in = resp.get("expires_in", 900)

    if not user_code or not device_code:
        print(f"[-] 获取设备码失败: {resp}")
        return None

    print("\n" + "=" * 50)
    print(f"  请打开浏览器访问: https://github.com/login/device")
    print(f"  输入验证码:        {user_code}")
    print(f"  验证码有效期:      {expires_in // 60} 分钟")
    print("=" * 50)
    print("[*] 等待授权中（每隔{}秒检查一次）...".format(interval))

    deadline = time.time() + expires_in
    while time.time() < deadline:
        time.sleep(interval)
        try:
            token_resp = requests.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
                proxies=PROXIES,
                timeout=15,
            ).json()
        except Exception as e:
            print(f"  [!] 轮询异常: {e}")
            continue

        error = token_resp.get("error")
        if "access_token" in token_resp:
            token = token_resp["access_token"]
            print(f"\n[+] 授权成功！")
            print(f"    Token: {token[:15]}...{token[-4:]}")

            if save_to_pool:
                _save_token(token)

            return token

        elif error == "authorization_pending":
            print("  ... 等待用户授权", end="\r")
            continue
        elif error == "slow_down":
            interval += 5
            continue
        elif error == "expired_token":
            print("\n[-] 验证码已过期，请重新运行脚本")
            return None
        else:
            print(f"\n[-] 错误: {token_resp.get('error_description', error)}")
            return None

    print("\n[-] 超时，请重新运行")
    return None


def _save_token(token: str):
    """将 token 写入 tokens/ 目录（触发 orchestrator watchdog）和 token_pool.txt"""
    os.makedirs(TOKENS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    token_file = os.path.join(TOKENS_DIR, f"token_{timestamp}.txt")

    with open(token_file, "w") as f:
        f.write(token)
    print(f"[+] Token 已写入: {token_file}")
    print("[+] orchestrator watchdog 将自动检测并加入轮询池")

    # 同时追加到 pool 文件（以防 orchestrator 未运行时的冷启动）
    with open(POOL_FILE, "a") as pf:
        pf.write(token + "\n")
    print(f"[+] Token 已追加到: {POOL_FILE}")


if __name__ == "__main__":
    token = get_ghu_token(save_to_pool=True)
    if token:
        print("\n[✓] 完成！orchestrator 将在几秒内热加载此 token。")
        sys.exit(0)
    else:
        sys.exit(1)
