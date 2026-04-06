#!/usr/bin/env python3
"""Copilot Token Orchestrator v2.0

Sidecar 调度器：
- watchdog 热监控 ./tokens/ 目录，自动补给新 GHU_ token
- Round-Robin + 随机选取，并发安全（threading.Lock）
- 自动审计：拦截 401/403 响应，毫秒级剔除死号
- 递归重试：换号后对 OpenClaw 完全透明
- 429 冷却：触发限速后将 token 放入 15 分钟休眠池
- 暴露 /status 接口供运维查看池状态

端口: 8090
目标: http://copilot_pool:8080 (docker 内网) 或 http://127.0.0.1:8088 (宿主机)
"""

import os
import time
import random
import threading
import logging
from datetime import datetime
from collections import deque

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import httpx
import uvicorn

# ---------------------------------------------------------------------------
# 配置区
# ---------------------------------------------------------------------------
TOKEN_DIR   = os.environ.get("TOKEN_DIR",   "/tokens")
POOL_FILE   = os.environ.get("POOL_FILE",   "/tokens/token_pool.txt")
TARGET_URL  = os.environ.get("TARGET_URL",  "http://copilot_pool:8080")
SUPER_TOKEN = os.environ.get("COPILOT_SUPER_TOKEN", "copilot-pool-secret-2026")
LISTEN_PORT = int(os.environ.get("ORCHESTRATOR_PORT", "8090"))

# 触发剔除的状态码
PRUNE_CODES   = {401, 403}
# 触发冷却的状态码
COOLDOWN_CODES = {429}
# 冷却时间（秒）
COOLDOWN_SECS  = 15 * 60  # 15 分钟
# 最大递归重试次数（防止无限循环）
MAX_RETRIES = 5

# ---------------------------------------------------------------------------
# 全局状态
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("orchestrator")

token_pool: set[str] = set()       # 活跃池
cooldown_queue: deque = deque()    # (token, 解禁时间戳)
pool_lock = threading.Lock()
pruned_log: list[dict] = []        # 审计日志
stats = {"total_requests": 0, "pruned": 0, "cooled": 0, "retries": 0}


# ---------------------------------------------------------------------------
# Token 管理
# ---------------------------------------------------------------------------
def load_tokens():
    """冷启动：从 POOL_FILE 加载历史 token"""
    with pool_lock:
        if os.path.exists(POOL_FILE):
            with open(POOL_FILE, "r") as f:
                for line in f:
                    t = line.strip()
                    if t.startswith("ghu_"):
                        token_pool.add(t)
    log.info(f"[INIT] Pool loaded: {len(token_pool)} tokens from {POOL_FILE}")


def add_token(token: str):
    """向池中添加新 token，并持久化"""
    with pool_lock:
        if token not in token_pool:
            token_pool.add(token)
            with open(POOL_FILE, "a") as pf:
                pf.write(token + "\n")
            log.info(f"[+] SYNCED: {token[:15]}... | pool_size={len(token_pool)}")


def prune_token(token: str, reason: str = "auth_failure"):
    """剔除失效 token，记录审计日志"""
    with pool_lock:
        token_pool.discard(token)
        stats["pruned"] += 1
        pruned_log.append({
            "token_prefix": token[:15],
            "reason": reason,
            "at": datetime.utcnow().isoformat(),
        })
    log.warning(f"[!] PRUNED: {token[:15]}... reason={reason} | remaining={len(token_pool)}")


def cooldown_token(token: str):
    """将 token 移出活跃池，放入冷却队列"""
    with pool_lock:
        token_pool.discard(token)
        cooldown_queue.append((token, time.time() + COOLDOWN_SECS))
        stats["cooled"] += 1
    log.warning(f"[~] COOLDOWN: {token[:15]}... for {COOLDOWN_SECS//60}min | remaining={len(token_pool)}")


def restore_cooled_tokens():
    """后台线程：定期将冷却到期的 token 还回活跃池"""
    while True:
        now = time.time()
        with pool_lock:
            while cooldown_queue and cooldown_queue[0][1] <= now:
                token, _ = cooldown_queue.popleft()
                token_pool.add(token)
                log.info(f"[~] RESTORED from cooldown: {token[:15]}... | pool_size={len(token_pool)}")
        time.sleep(30)


def pick_token() -> str | None:
    """从活跃池中随机选取一个 token"""
    with pool_lock:
        if not token_pool:
            return None
        return random.choice(list(token_pool))


# ---------------------------------------------------------------------------
# Watchdog：监控 TOKEN_DIR 目录热补给
# ---------------------------------------------------------------------------
class TokenWatcher(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        time.sleep(0.5)  # 等待写入完成
        try:
            with open(event.src_path, "r") as f:
                new_token = f.read().strip()
            if new_token.startswith("ghu_"):
                add_token(new_token)
            else:
                log.debug(f"[?] Ignored non-GHU file: {event.src_path}")
        except Exception as e:
            log.error(f"[!] Failed to read token file {event.src_path}: {e}")


# ---------------------------------------------------------------------------
# FastAPI 应用
# ---------------------------------------------------------------------------
app = FastAPI(title="Copilot Orchestrator", version="2.0")


@app.get("/status")
async def status():
    """运维状态接口"""
    with pool_lock:
        pool_size = len(token_pool)
        cooling = len(cooldown_queue)
    return JSONResponse({
        "pool_size": pool_size,
        "cooling": cooling,
        "stats": stats,
        "pruned_log": pruned_log[-20:],  # 最近 20 条
    })


@app.get("/health")
async def health():
    return {"status": "ok", "pool_size": len(token_pool)}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy(request: Request, path: str, _retry: int = 0):
    """反向代理：选取 token → 注入 Header → 转发至 copilot_pool → 审计响应"""
    if _retry >= MAX_RETRIES:
        log.error(f"[!] Max retries ({MAX_RETRIES}) reached for /{path}")
        return Response(content="Error: all tokens exhausted after retries", status_code=503)

    # 先检查池，避免 body 读取挂起
    token = pick_token()
    if token is None:
        return Response(
            content="Error: token pool is empty",
            status_code=503,
            media_type="text/plain",
        )

    with pool_lock:
        stats["total_requests"] += 1

    # 只在非 GET/HEAD/OPTIONS 请求时读 body，避免 GET 请求挂起
    if request.method.upper() in ("GET", "HEAD", "OPTIONS"):
        body = b""
    else:
        body = await request.body()

    # 构造转发 headers
    forward_headers = {}
    skip_headers = {"host", "content-length", "transfer-encoding"}
    for k, v in request.headers.items():
        if k.lower() not in skip_headers:
            forward_headers[k] = v
    forward_headers["Authorization"] = f"Bearer {SUPER_TOKEN}"
    forward_headers["copilot_token"] = token  # 注入真实 GHU_ token

    target = f"{TARGET_URL}/{path}"
    params = dict(request.query_params)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.request(
                method=request.method,
                url=target,
                headers=forward_headers,
                content=body,
                params=params,
            )
    except httpx.TimeoutException:
        log.error(f"[!] Timeout forwarding to {target}")
        return Response(content="Error: upstream timeout", status_code=504)
    except Exception as e:
        log.error(f"[!] Upstream error: {e}")
        return Response(content=f"Error: {e}", status_code=502)

    # --- 审计响应 ---
    if resp.status_code in PRUNE_CODES:
        prune_token(token, reason=f"http_{resp.status_code}")
        stats["retries"] += 1
        log.info(f"[~] Retrying (attempt {_retry+1}) with new token...")
        # 换 token 重试，body 已缓存无需重读
        new_token = pick_token()
        if new_token is None:
            return Response(content="Error: all tokens pruned, pool empty", status_code=503)
        # 直接用新 token 再发一次请求，不递归调用 proxy
        forward_headers["copilot_token"] = new_token
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.request(
                    method=request.method,
                    url=target,
                    headers=forward_headers,
                    content=body,
                    params=params,
                )
        except Exception as e:
            return Response(content=f"Error: {e}", status_code=502)

    if resp.status_code in COOLDOWN_CODES:
        cooldown_token(token)
        stats["retries"] += 1
        log.info(f"[~] Token cooled, retrying with new token (attempt {_retry+1})...")
        new_token = pick_token()
        if new_token is None:
            return Response(content="Error: all tokens in cooldown, pool empty", status_code=503)
        forward_headers["copilot_token"] = new_token
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.request(
                    method=request.method,
                    url=target,
                    headers=forward_headers,
                    content=body,
                    params=params,
                )
        except Exception as e:
            return Response(content=f"Error: {e}", status_code=502)

    # 正常响应，透传给调用方
    response_headers = {}
    skip_resp_headers = {"content-encoding", "transfer-encoding", "content-length"}
    for k, v in resp.headers.items():
        if k.lower() not in skip_resp_headers:
            response_headers[k] = v

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        headers=response_headers,
    )


# ---------------------------------------------------------------------------
# 启动入口
# ---------------------------------------------------------------------------
def main():
    os.makedirs(TOKEN_DIR, exist_ok=True)

    # 1. 冷启动加载历史 token
    load_tokens()

    # 2. 启动 watchdog 热监控
    observer = Observer()
    observer.schedule(TokenWatcher(), TOKEN_DIR, recursive=False)
    observer.start()
    log.info(f"[INIT] Watching token directory: {TOKEN_DIR}")

    # 3. 启动冷却恢复后台线程
    t = threading.Thread(target=restore_cooled_tokens, daemon=True)
    t.start()
    log.info(f"[INIT] Cooldown restore thread started (interval=30s)")

    log.info(f"[INIT] Orchestrator listening on 0.0.0.0:{LISTEN_PORT}")
    log.info(f"[INIT] Forwarding to: {TARGET_URL}")

    # 4. 启动 FastAPI
    uvicorn.run(app, host="0.0.0.0", port=LISTEN_PORT, log_level="warning")


if __name__ == "__main__":
    main()
