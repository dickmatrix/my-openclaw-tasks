"""
Bypass_Scraper_API — 反爬绕过采集工具

使用方法（作为 skill 调用）:
  from skills.bypass_scraper import bypass_scrape
  result = bypass_scrape("https://target-site.com/page")

配置（环境变量）:
  SCRAPER_API_KEY       — 商业 API Key（如 ScrapingNinja / ScrapingBee）
  SCRAPER_API_ENDPOINT  — API Endpoint（默认自动选择最优）
  SCRAPER_TIMEOUT       — 单次请求超时（秒），默认 60
  SCRAPER_MAX_RETRIES   — 最大重试次数，默认 3
  SCRAPER_FALLBACK_MODE — 当 API 不可用时是否启用内置备选（"browser" | "none"）
"""

from __future__ import annotations

import json
import os
import random
import re
import time
from typing import Optional

import requests

# ── 配置读取 ────────────────────────────────────────────────
_API_KEY: str = os.getenv("SCRAPER_API_KEY", "")
_API_ENDPOINT: str = os.getenv(
    "SCRAPER_API_ENDPOINT",
    "http://api.scraperapi.com?api_key={key}&url={url}&render=true"
)
_TIMEOUT: int = int(os.getenv("SCRAPER_TIMEOUT", "60"))
_MAX_RETRIES: int = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
_FALLBACK: str = os.getenv("SCRAPER_FALLBACK_MODE", "browser")

# ── User-Agent 轮换池 ───────────────────────────────────────
_UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15",
]

# ── 反爬特征识别 ─────────────────────────────────────────────
_CF_PATTERNS = [
    "cloudflare", "checking your browser", "cf-challenge",
    "attention required", "ddos protection", "incapsula",
]
_CAPTCHA_PATTERNS = [
    "captcha", "recaptcha", "g-recaptcha", "hcaptcha",
    "challenge", "verify you are human", "pixiv_dosm",
]
_BLOCK_CODES = {403, 429, 503}


def _detect_block(html: str, status_code: int) -> tuple[bool, str]:
    """检测是否被反爬拦截。返回 (is_blocked, block_type)"""
    html_lower = html.lower()
    if status_code in _BLOCK_CODES:
        return True, f"HTTP_{status_code}"
    for pat in _CF_PATTERNS:
        if pat in html_lower:
            return True, "Cloudflare"
    for pat in _CAPTCHA_PATTERNS:
        if pat in html_lower:
            return True, "CAPTCHA"
    return False, ""


def _fetch_with_api(url: str, retries: int = _MAX_RETRIES) -> dict:
    """
    通过商业 API 获取页面（绕过 Cloudflare / CAPTCHA）。
    返回 {"success": bool, "html": str, "error": str, "attempts": int}
    """
    if not _API_KEY:
        return {"success": False, "html": "", "error": "NO_API_KEY", "attempts": 0}

    endpoint = _API_ENDPOINT.format(key=_API_KEY, url=url)
    headers = {"User-Agent": random.choice(_UA_POOL)}

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                endpoint,
                headers=headers,
                timeout=_TIMEOUT,
                allow_redirects=True,
            )
            blocked, block_type = _detect_block(resp.text, resp.status_code)
            if not blocked:
                return {
                    "success": True,
                    "html": resp.text,
                    "error": "",
                    "attempts": attempt,
                    "block_type": None,
                }
            else:
                # 被识别为机器人，重试
                wait = 2 ** attempt + random.uniform(0, 1)
                print(f"  [Bypass_Scraper] attempt {attempt}/{retries} — "
                      f"被{block_type}拦截，{wait:.1f}s 后重试...")
                time.sleep(wait)
        except requests.exceptions.Timeout:
            wait = 2 ** attempt
            print(f"  [Bypass_Scraper] attempt {attempt}/{retries} — 超时，{wait:.1f}s 后重试...")
            time.sleep(wait)
        except Exception as e:
            return {"success": False, "html": "", "error": str(e), "attempts": attempt}

    return {"success": False, "html": "", "error": "MAX_RETRIES_EXCEEDED", "attempts": retries}


def _fetch_with_browser_fallback(url: str, retries: int = 2) -> dict:
    """
    内置 Playwright 备选（当 API 不可用时）。
    仅在 _FALLBACK == "browser" 时启用。
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"success": False, "html": "", "error": "PLAYWRIGHT_NOT_INSTALLED", "attempts": 0}

    for attempt in range(1, retries + 1):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=_TIMEOUT * 1000, wait_until="networkidle")
                html = page.content()
                browser.close()
                return {"success": True, "html": html, "error": "", "attempts": attempt}
        except Exception as e:
            wait = 2 ** attempt
            print(f"  [Bypass_Scraper/browser] attempt {attempt}/{retries} — {e}，"
                  f"{wait:.1f}s 后重试...")
            time.sleep(wait)
    return {"success": False, "html": "", "error": "BROWSER_FALLBACK_FAILED", "attempts": retries}


def bypass_scrape(
    target_url: str,
    use_api: bool = True,
    use_browser_fallback: bool = True,
) -> dict:
    """
    主入口函数。采集目标 URL，绕过反爬。

    参数:
        target_url: 目标网址（String）
        use_api: 是否优先使用商业 API（默认 True）
        use_browser_fallback: API 失败后是否启用浏览器备选（默认 True）

    返回:
        {
            "success": bool,
            "html": str,          # 渲染后的纯净 HTML
            "error": str,         # 错误类型（成功时为空）
            "attempts": int,      # 实际尝试次数
            "block_type": str,    # 拦截类型（CF / CAPTCHA / HTTP_403 等）
            "method": str,        # 使用的方法（api / browser / requests）
        }
    """
    print(f"[Bypass_Scraper] 开始采集: {target_url}")

    # 分支1C：当检测到 403/429/CF/CAPTCHA 时触发
    # 先尝试直接请求（快速诊断）
    try:
        direct_resp = requests.get(
            target_url,
            headers={"User-Agent": random.choice(_UA_POOL)},
            timeout=10,
            allow_redirects=True,
        )
        blocked, block_type = _detect_block(direct_resp.text, direct_resp.status_code)
        if not blocked and direct_resp.status_code == 200:
            print(f"  [Bypass_Scraper] 直接访问成功（无需绕过），method=requests")
            return {
                "success": True,
                "html": direct_resp.text,
                "error": "",
                "attempts": 1,
                "block_type": None,
                "method": "requests",
            }
        elif direct_resp.status_code in _BLOCK_CODES or blocked:
            print(f"  [Bypass_Scraper] 检测到 {block_type or f'HTTP_{direct_resp.status_code}'}，"
                  f"触发反爬绕过...")
    except Exception:
        pass  # 直接请求失败，继续走绕过逻辑

    # 优先商业 API
    if use_api and _API_KEY:
        result = _fetch_with_api(target_url)
        if result["success"]:
            print(f"  [Bypass_Scraper] API 成功，尝试次数={result['attempts']}")
            result["method"] = "api"
            return result
        print(f"  [Bypass_Scraper] API 失败: {result['error']}，尝试备选...")

    # 浏览器备选
    if use_browser_fallback and _FALLBACK == "browser":
        result = _fetch_with_browser_fallback(target_url)
        if result["success"]:
            print(f"  [Bypass_Scraper] 浏览器备选成功，尝试次数={result['attempts']}")
            result["method"] = "browser"
            return result
        print(f"  [Bypass_Scraper] 浏览器备选失败: {result['error']}")

    # 全部失败
    print(f"  [Bypass_Scraper] ❌ 全部方法失败（重试 {_MAX_RETRIES} 次均未成功）")
    return {
        "success": False,
        "html": "",
        "error": "ALL_METHODS_FAILED",
        "attempts": _MAX_RETRIES,
        "method": "none",
    }


# ── CLI 入口（调试用）─────────────────────────────────────────
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python bypass_scraper.py <target_url>")
        sys.exit(1)
    result = bypass_scrape(sys.argv[1])
    print(json.dumps(
        {k: v if k != "html" else f"<html:{len(v)} bytes>" for k, v in result.items()},
        ensure_ascii=False, indent=2,
    ))
