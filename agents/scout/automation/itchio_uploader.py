#!/usr/bin/env python3
"""
Itch.io 自动化上传工具
用途：自动将打包好的资产上传到 Itch.io

依赖：pip install requests selenium

注意事项：
- Itch.io 官方 API 需要申请 BUTLER_API_KEY
- 申请地址：https://itch.io/user/settings/api-keys
- 此脚本使用 Itch.io 官方工具 butler 或 Selenium 模拟上传
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import requests

# ============== 配置 ==============
ITCH_API_KEY = os.getenv("BUTLER_API_KEY", "")
ITCH_USERNAME = os.getenv("ITCH_USERNAME", "")
ITCH_GAME_ID = os.getenv("ITCH_GAME_ID", "")

ITCH_UPLOAD_URL = "https://itch.io/api/latest/upload"


class ItchUploader:
    """Itch.io 上传工具"""
    
    def __init__(self, api_key="", username="", game_id=""):
        self.api_key = api_key or BUTLER_API_KEY
        self.username = username or ITCH_USERNAME
        self.game_id = game_id or ITCH_GAME_ID
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
    
    def create_listing(self, title, description, tags, price=0):
        """创建商品 listing"""
        data = {
            "game": {"title": title},
            "listing": {
                "description": description,
                "tags": tags,
                "price": price,
            }
        }
        
        response = self.session.post(
            f"https://itch.io/api/latest/game/{self.game_id}",
            json=data
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def upload_file(self, file_path, game_id=None, channel="default"):
        """
        使用 Itch.io JSON API 上传文件
        注意：需要先在网页端创建商品获取 game_id
        """
        if not self.api_key:
            print("[!] 需要设置 BUTLER_API_KEY")
            print("[*] 申请地址: https://itch.io/user/settings/api-keys")
            return None
        
        game_id = game_id or self.game_id
        if not game_id:
            print("[!] 需要设置 ITCH_GAME_ID（游戏ID）")
            return None
        
        file_path = Path(file_path)
        if not file_path.exists():
            print(f"[!] 文件不存在: {file_path}")
            return None
        
        # 获取上传地址
        upload_info = self.session.get(
            f"https://itch.io/api/latest/game/{game_id}/upload-requests"
        )
        
        if upload_info.status_code != 200:
            print(f"[!] 获取上传地址失败: {upload_info.status_code}")
            return None
        
        # 上传文件
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f, "application/zip")}
            upload_response = self.session.post(
                upload_info.json()["upload_url"],
                files=files
            )
        
        return upload_response.json() if upload_response.status_code == 200 else None


def manual_upload_instructions():
    """输出手动上传指引（推荐首次）"""
    print("""
========================================
Itch.io 上传指引（首次建议手动）
========================================

首次上架建议手动操作，熟悉后再切自动化。

Step 1: 注册 Itch.io
  https://itch.io

Step 2: 创建商品
  1. 登录后点击 "Sell on Itch.io"
  2. 选择 "Game" 或 "Digital Asset"
  3. 填写标题、描述、标签
  4. 设置价格（建议 $5-$15）

Step 3: 上传文件
  1. 进入商品页面
  2. 点击 "Upload files"
  3. 拖入打包好的 .zip 文件
  4. 提交审核（通常即时发布）

Step 4: 获取 API Key（后续自动化用）
  1. 进入 https://itch.io/user/settings/api-keys
  2. 创建 API Key
  3. 设置环境变量:
     export BUTLER_API_KEY="your_key_here"
     export ITCH_USERNAME="your_username"
     export ITCH_GAME_ID="your_game_id"

========================================
快速验证市场方法
========================================

上架后快速获得反馈：
1. 先上 1-2 个低价包（$3-$5）测转化率
2. 看自然流量（Itch.io 有站内搜索流量）
3. 有 5+ 下载后考虑提价

========================================
""".strip())


def generate_itchio_page_content(asset_pack_path, manifest):
    """生成 Itch.io 页面内容（用于粘贴到描述）"""
    
    total_files = manifest.get("total_files", 0)
    
    content = f"""
=== AI Generated Game Asset Pack ===

📦 内容包含：
- 总计 {total_files} 个游戏资产
{_format_categories(manifest.get("categories", {}))}

🎯 适用场景：
- 独立游戏开发
- 游戏原型制作
- 教学演示
- 个人项目

📋 格式说明：
- PNG 透明背景
- 512x512 像素（可按需缩放）
- 像素风格 / RPG 风格

⚡ 使用说明：
1. 下载解压
2. 导入 Unity / Godot / RPG Maker 等引擎
3. 自由使用（详见授权协议）

💰 授权：
- 个人和商业项目均可使用
- 禁止二次销售或分发源文件
- 禁止用于 AI 训练

© All rights reserved by the creator
Generated with AI (Stable Diffusion / ComfyUI)
    """.strip()
    
    return content


def _format_categories(categories):
    lines = []
    for cat, info in categories.items():
        lines.append(f"- {cat.upper()}: {info['count']} 个")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Itch.io 辅助工具")
    parser.add_argument("--manifest", help="资产包 manifest.json 路径")
    parser.add_argument("--pack-zip", help="打包好的 zip 文件路径")
    parser.add_argument("--generate-desc", action="store_true", help="生成页面描述文案")
    parser.add_argument("--instructions", action="store_true", help="显示手动上传指引")
    
    args = parser.parse_args()
    
    if args.instructions:
        manual_upload_instructions()
    elif args.generate_desc and args.manifest:
        with open(args.manifest, 'r') as f:
            manifest = json.load(f)
        content = generate_itchio_page_content("", manifest)
        print(content)
    else:
        manual_upload_instructions()
