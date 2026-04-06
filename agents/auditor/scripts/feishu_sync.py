#!/usr/bin/env python3
"""
Feishu Doc Sync - 本地文件夹 → 飞书云文档同步脚本
监控指定本地文件夹，有 .md 文件变化时自动同步到飞书云文档

使用方式:
    pip install watchdog requests
    python feishu_sync.py --folder "/path/to/knowledge/base"

首次运行会创建飞书文档，之后自动增量更新。
"""

import os
import time
import hashlib
import argparse
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
import json

# ============== 配置区 ==============
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "cli_a94d84f810f81ccd")  # Auditor app
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
FEISHU_API_BASE = "https://open.feishu.cn/open-apis"

# 文档标题映射 (本地文件名 → 飞书文档Token)
DOC_MAP_FILE = ".feishu_doc_map.json"
# ======================================


def get_app_token():
    """获取 tenant access token"""
    url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
    resp = requests.post(url, json={
        "app_id": FEISHU_APP_ID,
        "app_secret": FEISHU_APP_SECRET
    })
    resp.raise_for_status()
    return resp.json().get("tenant_access_token")


def create_doc(title: str, content: str, folder_token: str = None) -> str:
    """创建新文档并写入内容"""
    token = get_app_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. 创建文档
    url = f"{FEISHU_API_BASE}/docx/v1/documents"
    payload = {"title": title}
    if folder_token:
        payload["parent_token"] = folder_token
        payload["parent_type"] = "explorer"
    
    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    doc_token = resp.json().get("data", {}).get("document", {}).get("document_id")
    
    if not doc_token:
        raise Exception(f"Failed to create doc: {resp.text}")
    
    # 2. 写入内容
    write_url = f"{FEISHU_API_BASE}/docx/v1/documents/{doc_token}/blocks"
    blocks = markdown_to_blocks(content)
    
    # 插入内容块
    for i, block in enumerate(blocks):
        requests.post(write_url, headers=headers, json={
            "children": [block],
            "index": i
        })
    
    return doc_token


def update_doc_content(doc_token: str, content: str):
    """更新文档内容（完整覆盖）"""
    token = get_app_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # 获取现有块
    list_url = f"{FEISHU_API_BASE}/docx/v1/documents/{doc_token}/blocks"
    resp = requests.get(list_url, headers=headers)
    blocks = resp.json().get("data", {}).get("items", [])
    
    # 删除现有内容块（保留页面块）
    page_block_id = blocks[0]["block_id"] if blocks else None
    if not page_block_id:
        return
    
    content_block_ids = []
    for b in blocks[1:]:  # 跳过页面块
        content_block_ids.append(b["block_id"])
    
    if content_block_ids:
        del_url = f"{FEISHU_API_BASE}/docx/v1/documents/{doc_token}/blocks/{page_block_id}/children"
        requests.delete(del_url, headers=headers, json={
            "start_index": 0,
            "end_index": len(content_block_ids)
        })
    
    # 插入新内容
    new_blocks = markdown_to_blocks(content)
    insert_url = f"{FEISHU_API_BASE}/docx/v1/documents/{doc_token}/blocks/{page_block_id}/children"
    for i, block in enumerate(new_blocks):
        requests.post(insert_url, headers=headers, json={
            "children": [block],
            "index": i
        })


def markdown_to_blocks(content: str) -> list:
    """简单 Markdown → 飞书块转换"""
    blocks = []
    for line in content.split("\n"):
        line = line.rstrip()
        if not line:
            continue
        
        if line.startswith("# "):
            blocks.append({
                "block_type": 2,  # heading1
                "heading1": {
                    "elements": [{"text_run": {"content": line[2:]}}],
                    "style": {"align": 1}
                }
            })
        elif line.startswith("## "):
            blocks.append({
                "block_type": 3,  # heading2
                "heading2": {
                    "elements": [{"text_run": {"content": line[3:]}}],
                    "style": {"align": 1}
                }
            })
        elif line.startswith("### "):
            blocks.append({
                "block_type": 4,  # heading3
                "heading3": {
                    "elements": [{"text_run": {"content": line[4:]}}],
                    "style": {"align": 1}
                }
            })
        elif line.startswith("- ") or line.startswith("* "):
            blocks.append({
                "block_type": 12,  # bullet
                "bullet": {
                    "elements": [{"text_run": {"content": line[2:]}}],
                    "style": {"align": 1}
                }
            })
        else:
            blocks.append({
                "block_type": 2,  # text as paragraph
                "text": {
                    "elements": [{"text_run": {"content": line}}],
                    "style": {"align": 1}
                }
            })
    
    return blocks


def load_doc_map(folder: str) -> dict:
    """加载本地文档映射表"""
    map_path = os.path.join(folder, DOC_MAP_FILE)
    if os.path.exists(map_path):
        with open(map_path) as f:
            return json.load(f)
    return {}


def save_doc_map(folder: str, doc_map: dict):
    """保存映射表"""
    map_path = os.path.join(folder, DOC_MAP_FILE)
    with open(map_path, "w") as f:
        json.dump(doc_map, f, indent=2)


class SyncHandler(FileSystemEventHandler):
    """文件系统事件处理器"""
    
    def __init__(self, folder: str):
        self.folder = folder
        self.doc_map = load_doc_map(folder)
        self.pending = {}  # 简易防抖
    
    def _get_relative_path(self, path: str) -> str:
        return os.path.relpath(path, self.folder)
    
    def _should_sync(self, path: str) -> bool:
        ext = os.path.splitext(path)[1].lower()
        return ext in (".md", ".txt", ".markdown") and not path.endswith(DOC_MAP_FILE)
    
    def _sync_file(self, path: str):
        rel_path = self._get_relative_path(path)
        filename = os.path.basename(path)
        title = os.path.splitext(filename)[0]
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if rel_path in self.doc_map:
                # 更新已有文档
                doc_token = self.doc_map[rel_path]
                print(f"[更新] {filename} → {doc_token}")
                update_doc_content(doc_token, content)
            else:
                # 创建新文档
                print(f"[新建] {filename}")
                doc_token = create_doc(title, content)
                self.doc_map[rel_path] = doc_token
                save_doc_map(self.folder, self.doc_map)
                print(f"    → {doc_token}")
                
        except Exception as e:
            print(f"[错误] {filename}: {e}")
    
    def on_modified(self, event):
        if event.is_directory:
            return
        if self._should_sync(event.src_path):
            # 防抖：延迟 1 秒再处理
            self.pending[event.src_path] = time.time()
            time.sleep(1)
            if event.src_path in self.pending:
                del self.pending[event.src_path]
                self._sync_file(event.src_path)
    
    def on_created(self, event):
        if event.is_directory:
            return
        if self._should_sync(event.src_path):
            self._sync_file(event.src_path)


def main():
    parser = argparse.ArgumentParser(description="飞书云文档同步工具")
    parser.add_argument("--folder", "-f", required=True, help="监控的本地文件夹路径")
    args = parser.parse_args()
    
    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        print(f"[错误] 目录不存在: {folder}")
        return
    
    print(f"🔄 开始监控: {folder}")
    print(f"📋 映射表: {os.path.join(folder, DOC_MAP_FILE)}")
    print("-" * 40)
    
    event_handler = SyncHandler(folder)
    observer = Observer()
    observer.schedule(event_handler, folder, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
