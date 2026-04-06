#!/usr/bin/env python3
"""
AI 游戏资产批量生成工具
用途：调用 Stable Diffusion API 批量生成游戏资产

依赖安装：pip install requests pillow python-dotenv

使用前配置：
1. 设置 SD_API_URL（你的 SD API 地址，如使用 OpenAI 兼容 API）
2. 设置 SD_API_KEY（如需要）
3. 或配置 COMFYUI_URL（ComfyUI 工作流API）
"""

import os
import json
import time
import random
import requests
from pathlib import Path
from datetime import datetime
from PIL import Image
from dotenv import load_dotenv

# ============== 配置区 ==============
load_dotenv()

SD_API_URL = os.getenv("SD_API_URL", "http://localhost:8188")  # 默认 ComfyUI 端口
SD_API_KEY = os.getenv("SD_API_KEY", "")
COMFYUI_MODE = os.getenv("COMFYUI_MODE", "true").lower() == "true"  # 默认 ComfyUI 模式
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output_assets")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "4"))

# ============== 预设风格 ==============
ASSET_PRESETS = {
    "pixel_art_icon": {
        "prompt_template": "pixel art game icon, {subject}, 16-bit style, transparent background, clean edges, {color} color scheme, RPG inventory item",
        "neg_prompt": "blurry, low quality, watermark, text, logo, photograph, realistic",
        "width": 512,
        "height": 512,
        "steps": 30,
        "cfg_scale": 8,
        "sampler": "DPM++ 2M Karras",
    },
    "pbr_texture": {
        "prompt_template": "seamless PBR texture, {subject}, 4k resolution, physically based rendering, clean tiling, game ready",
        "neg_prompt": "blurry, low quality, watermark, text, seams, JPEG artifacts",
        "width": 1024,
        "height": 1024,
        "steps": 40,
        "cfg_scale": 7,
        "sampler": "DPM++ 2M Karras",
    },
    "character_art": {
        "prompt_template": "game character portrait, {subject}, {style}, transparent background, full body, fantasy RPG style, detailed, high quality",
        "neg_prompt": "blurry, low quality, watermark, text, logo, deformed, bad anatomy",
        "width": 1024,
        "height": 1024,
        "steps": 35,
        "cfg_scale": 8,
        "sampler": "DPM++ 2M Karras",
    },
    "ui_element": {
        "prompt_template": "game UI element, {subject}, clean flat design, modern game UI, {color} accent, transparent background, crisp edges",
        "neg_prompt": "blurry, low quality, watermark, text, logo, realistic, photograph",
        "width": 512,
        "height": 512,
        "steps": 25,
        "cfg_scale": 7,
        "sampler": "Euler a",
    },
}

# ============== 资产主题词库 ==============
SUBJECTS = {
    "weapons": ["sword", "axe", "bow", "staff", "dagger", "shield", "mace", "spear", "wand", "hammer"],
    "potions": ["health potion", "mana potion", "speed potion", "strength potion", "poison flask", "elixir", "antidote", "stamina drink"],
    "armor": ["helmet", "chestplate", "gauntlets", "boots", "shield", "cloak", "ring", "amulet", "belt"],
    "items": ["chest", "key", "gem", "coin", "scroll", "book", "crown", "skull", "crystal", "orb"],
    "creatures": ["dragon", "goblin", "slime", "skeleton", "wolf", "spider", "snake", "bear", "eagle", "slime"],
    "environment": ["tree", "rock", "flower", "mushroom", "torch", "flag", "bridge", "door", "fountain", "altar"],
}

STYLES = ["watercolor", "oil painting", "anime", "realistic", "cartoon", "pixel art", "ink sketch", "low poly"]
COLORS = ["red", "blue", "green", "golden", "silver", "purple", "dark", "bright", "warm", "cool"]


class AssetGenerator:
    def __init__(self, output_dir=OUTPUT_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir = self.output_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir.mkdir(parents=True, exist_ok=True)
        print(f"[+] 输出目录: {self.session_dir}")

    def build_prompt(self, preset_name, subject, style=None, color=None):
        preset = ASSET_PRESETS[preset_name]
        prompt = preset["prompt_template"].format(
            subject=subject,
            style=style or random.choice(STYLES),
            color=color or random.choice(COLORS)
        )
        return prompt, preset["neg_prompt"]

    def generate_batch_comfyui(self, preset_name, subjects, count_per_subject=3, save=True):
        """通过 ComfyUI API 批量生成"""
        from PIL import Image
        import base64
        import time

        preset = ASSET_PRESETS.get(preset_name, ASSET_PRESETS["pixel_art_icon"])
        results = []

        for subject in subjects:
            for i in range(count_per_subject):
                prompt, neg_prompt = self.build_prompt(preset_name, subject)

                # 构建 ComfyUI 简单 Text-to-Image 工作流
                workflow = {
                    "3": {
                        "inputs": {
                            "width": preset["width"],
                            "height": preset["height"],
                            "batch_size": 1
                        },
                        "class_type": "KSampler"
                    },
                    "4": {
                        "inputs": {
                            "seed": random.randint(0, 0xffffffffffffffff),
                            "steps": preset["steps"],
                            "cfg": preset["cfg_scale"],
                            "sampler_name": "euler",
                            "scheduler": "normal",
                            "positive": prompt,
                            "negative": neg_prompt,
                            "model": ["5", 0],
                            "latent_image": ["6", 0]
                        },
                        "class_type": "KSampler"
                    },
                    "5": {
                        "inputs": {"ckpt_name": "v1-5-pruned-emaonly.safetensors"},
                        "class_type": "CheckpointLoaderSimple"
                    },
                    "6": {
                        "inputs": {
                            "width": preset["width"],
                            "height": preset["height"],
                            "batch_size": 1
                        },
                        "class_type": "EmptyLatentImage"
                    },
                    "7": {
                        "inputs": {
                            "samples": ["4", 0],
                            "vae": ["5", 2]
                        },
                        "class_type": "VAEDecode"
                    },
                    "8": {
                        "inputs": {
                            "filename_prefix": f"asset_{subject.replace(' ', '_')}",
                            "images": ["7", 0]
                        },
                        "class_type": "SaveImage"
                    }
                }

                print(f"[>] 生成中 (ComfyUI): {subject} ({i+1}/{count_per_subject})")

                try:
                    response = requests.post(
                        f"{SD_API_URL}/prompt",
                        json={"prompt": workflow},
                        timeout=120
                    )

                    if response.status_code == 200:
                        result = response.json()
                        prompt_id = result.get("prompt_id")

                        if prompt_id:
                            # 轮询等待结果（最多 60 秒）
                            for _ in range(60):
                                time.sleep(1)
                                history_resp = requests.get(
                                    f"{SD_API_URL}/history/{prompt_id}",
                                    timeout=10
                                )
                                if history_resp.status_code == 200:
                                    history = history_resp.json()
                                    if prompt_id in history:
                                        outputs = history[prompt_id].get("outputs", {})
                                        for node_id, node_data in outputs.items():
                                            if "images" in node_data:
                                                for img_info in node_data["images"]:
                                                    img_data = img_info.get("image")
                                                    if img_data and save:
                                                        filename = f"{subject.replace(' ', '_')}_{preset_name}_{i+1}_{int(time.time())}.png"
                                                        filepath = self.session_dir / filename
                                                        img_bytes = base64.b64decode(img_data)
                                                        with open(filepath, "wb") as f:
                                                            f.write(img_bytes)
                                                        results.append({
                                                            "subject": subject,
                                                            "preset": preset_name,
                                                            "path": str(filepath),
                                                            "status": "success"
                                                        })
                                                        print(f"    [✓] 已保存: {filename}")
                                                        break
                                        break
                            else:
                                results.append({"subject": subject, "preset": preset_name, "status": "timeout"})
                        else:
                            results.append({"subject": subject, "preset": preset_name, "status": "no_prompt_id"})
                    else:
                        print(f"    [✗] API 错误: {response.status_code}")
                        results.append({"subject": subject, "preset": preset_name, "status": "error", "code": response.status_code})

                except Exception as e:
                    print(f"    [✗] 异常: {e}")
                    results.append({"subject": subject, "preset": preset_name, "status": "error", "error": str(e)})

                time.sleep(0.5)

        return results

    def generate_batch_sd_webui(self, preset_name, subjects, count_per_subject=3, save=True):
        """通过 SD WebUI API 批量生成"""
        preset = ASSET_PRESETS[preset_name]
        results = []
        
        for subject in subjects:
            for i in range(count_per_subject):
                prompt, neg_prompt = self.build_prompt(preset_name, subject)
                
                payload = {
                    "prompt": prompt,
                    "negative_prompt": neg_prompt,
                    "width": preset["width"],
                    "height": preset["height"],
                    "steps": preset["steps"],
                    "cfg_scale": preset["cfg_scale"],
                    "sampler_name": preset["sampler"],
                    "seed": -1,  # 随机种子
                }
                
                print(f"[>] 生成中: {subject} ({i+1}/{count_per_subject})")
                
                try:
                    response = requests.post(
                        f"{SD_API_URL}/sdapi/v1/txt2img",
                        json=payload,
                        headers={"Authorization": f"Bearer {SD_API_KEY}"} if SD_API_KEY else {},
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        images = result.get("images", [])
                        
                        if images and save:
                            img_data = images[0]
                            # 保存为 PNG
                            filename = f"{subject.replace(' ', '_')}_{preset_name}_{i+1}_{int(time.time())}.png"
                            filepath = self.session_dir / filename
                            
                            # 处理 base64 图像
                            import base64
                            img_bytes = base64.b64decode(img_data)
                            with open(filepath, "wb") as f:
                                f.write(img_bytes)
                            
                            results.append({"subject": subject, "preset": preset_name, "path": str(filepath), "status": "success"})
                            print(f"    [✓] 已保存: {filename}")
                        else:
                            results.append({"subject": subject, "preset": preset_name, "status": "no_image"})
                    else:
                        print(f"    [✗] API 错误: {response.status_code}")
                        results.append({"subject": subject, "preset": preset_name, "status": "error", "code": response.status_code})
                        
                except Exception as e:
                    print(f"    [✗] 异常: {e}")
                    results.append({"subject": subject, "preset": preset_name, "status": "error", "error": str(e)})
                
                time.sleep(0.5)  # 避免请求过快
        
        return results

    def generate_batch(self, preset_name, subjects, count_per_subject=3, save=True):
        """批量生成资产（自动选择 ComfyUI 或 SD WebUI 模式）"""
        if COMFYUI_MODE:
            return self.generate_batch_comfyui(preset_name, subjects, count_per_subject, save)
        else:
            return self.generate_batch_sd_webui(preset_name, subjects, count_per_subject, save)

    def generate_from_config(self, config_path):
        """从配置文件批量生成"""
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        all_results = []
        for item in config.get("tasks", []):
            preset = item["preset"]
            subjects = item.get("subjects", [])
            count = item.get("count_per_subject", 3)
            
            print(f"\n{'='*50}")
            print(f"开始任务: {preset} ({len(subjects)} 个主题)")
            results = self.generate_batch(preset, subjects, count)
            all_results.extend(results)
        
        # 保存生成报告
        report_path = self.session_dir / "generation_report.json"
        with open(report_path, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        success_count = sum(1 for r in all_results if r["status"] == "success")
        print(f"\n{'='*50}")
        print(f"生成完成！成功: {success_count}/{len(all_results)}")
        print(f"报告已保存: {report_path}")
        
        return all_results


def interactive_mode():
    """交互式模式"""
    print("=" * 50)
    print("AI 游戏资产批量生成器")
    print("=" * 50)
    
    gen = AssetGenerator()
    
    print("\n可用预设类型:")
    for i, name in enumerate(ASSET_PRESETS.keys(), 1):
        print(f"  {i}. {name}")
    
    print("\n可用主题库:")
    for i, name in enumerate(SUBJECTS.keys(), 1):
        print(f"  {i}. {name} ({len(SUBJECTS[name])} 个)")
    
    preset_choice = input("\n选择预设类型 [1-4] (默认1): ").strip()
    preset_idx = int(preset_choice) - 1 if preset_choice else 0
    preset_name = list(ASSET_PRESETS.keys())[preset_idx]
    
    category_choice = input("选择主题库 [1-6] (默认随机): ").strip()
    if category_choice:
        category_idx = int(category_choice) - 1
        category_name = list(SUBJECTS.keys())[category_idx]
        subjects = SUBJECTS[category_name]
    else:
        # 随机组合多个类别
        subjects = []
        for cat_subjects in SUBJECTS.values():
            subjects.extend(random.sample(cat_subjects, min(3, len(cat_subjects))))
    
    count = input("每个主题生成数量 [1-10] (默认3): ").strip()
    count = int(count) if count else 3
    
    print(f"\n开始生成: {preset_name}")
    print(f"主题数量: {len(subjects)}")
    print(f"每主题生成: {count} 张")
    
    results = gen.generate_batch(preset_name, subjects, count)
    
    success = [r for r in results if r["status"] == "success"]
    print(f"\n完成！成功生成 {len(success)} 张资产")
    print(f"保存位置: {gen.session_dir}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "--config" and len(sys.argv) > 2:
            gen = AssetGenerator()
            gen.generate_from_config(sys.argv[2])
        else:
            print("用法: python asset_generator.py --config config.json")
    else:
        interactive_mode()
