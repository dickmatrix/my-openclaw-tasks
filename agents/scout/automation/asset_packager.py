#!/usr/bin/env python3
"""
游戏资产整理 & 打包工具
用途：批量整理、命名、裁剪、打包生成的资产，准备发布

依赖：pip install pillow python-dotenv requests

功能：
1. 批量重命名（标准化命名）
2. 批量裁剪/缩放
3. 生成预览图（缩略图网格）
4. 打包成 zip
5. 生成上架清单（可选）
"""

import os
import sys
import json
import zipfile
import argparse
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import shutil

# ============== 配置 ==============
DEFAULT_OUTPUT = "./packaged_assets"
THUMBNAIL_SIZE = (256, 256)
PREVIEW_GRID = (3, 3)  # 3x3 网格预览
LOGO_TEXT = "AI Generated Asset"


class AssetPackager:
    def __init__(self, input_dir, output_dir=DEFAULT_OUTPUT):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.batch_name = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.batch_dir = self.output_dir / f"batch_{self.batch_name}"
        self.batch_dir.mkdir(parents=True, exist_ok=True)
        
        # 分类子目录
        self.categories = {
            "icons": self.batch_dir / "icons",
            "textures": self.batch_dir / "textures",
            "characters": self.batch_dir / "characters",
            "ui": self.batch_dir / "ui",
            "audio": self.batch_dir / "audio",
            "other": self.batch_dir / "other",
        }
        for d in self.categories.values():
            d.mkdir(exist_ok=True)
        
        print(f"[+] 输入目录: {self.input_dir}")
        print(f"[+] 输出目录: {self.batch_dir}")

    def auto_categorize(self, filename):
        """根据文件名自动分类"""
        filename_lower = filename.lower()
        
        if any(k in filename_lower for k in ["icon", "item", "prop"]):
            return "icons"
        elif any(k in filename_lower for k in ["texture", "material", "pbr", "tile"]):
            return "textures"
        elif any(k in filename_lower for k in ["character", "char", "portrait", "avatar"]):
            return "characters"
        elif any(k in filename_lower for k in ["ui", "button", "menu", "interface"]):
            return "ui"
        elif any(k in filename_lower for k in ["audio", "bgm", "sfx", "sound"]):
            return "audio"
        return "other"

    def rename_standard(self, filename, category):
        """标准化命名"""
        # 移除空格和特殊字符
        name = filename.stem
        name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        # 添加分类前缀
        prefix = category[:3].upper()
        return f"{prefix}_{name}_{self.batch_name[:8]}{filename.suffix}"

    def process_images(self, sizes=None):
        """
        批量处理图像：
        1. 统一格式（PNG）
        2. 缩放到指定尺寸
        3. 生成缩略图
        """
        if sizes is None:
            sizes = [64, 128, 256, 512]
        
        image_files = list(self.input_dir.glob("*.png")) + \
                      list(self.input_dir.glob("*.jpg")) + \
                      list(self.input_dir.glob("*.jpeg")) + \
                      list(self.input_dir.glob("*.webp"))
        
        if not image_files:
            print("[!] 未找到图像文件")
            return
        
        print(f"[>] 找到 {len(image_files)} 个图像文件")
        
        processed = []
        
        for img_path in image_files:
            try:
                # 读取图像
                img = Image.open(img_path)
                if img.mode != "RGBA":
                    img = img.convert("RGBA")
                
                category = self.auto_categorize(img_path.name)
                
                # 保存到对应分类
                new_name = self.rename_standard(img_path, category)
                dest_path = self.categories[category] / new_name
                
                # 保存主图（保留原始尺寸）
                img.save(dest_path, "PNG")
                processed.append({"original": str(img_path), "dest": str(dest_path), "category": category})
                
                # 生成多尺寸缩略图
                for size in sizes:
                    thumb_name = new_name.replace(".png", f"_{size}.png")
                    thumb_path = self.categories[category] / thumb_name
                    img_resized = img.resize((size, size), Image.Resampling.LANCZOS)
                    img_resized.save(thumb_path, "PNG")
                
                print(f"    [✓] {img_path.name} -> {new_name}")
                
            except Exception as e:
                print(f"    [✗] 处理失败 {img_path.name}: {e}")
        
        return processed

    def generate_preview_grid(self, category="icons", output_name="preview.png"):
        """
        生成 3x3 预览网格图
        用于 Itch.io / Unity Asset Store 展示
        """
        category_dir = self.categories.get(category)
        if not category_dir or not category_dir.exists():
            print(f"[!] 分类目录不存在: {category}")
            return
        
        image_files = list(category_dir.glob("*.png"))[:9]
        if len(image_files) < 1:
            print(f"[!] {category} 目录下没有图像")
            return
        
        # 计算网格尺寸
        cols, rows = PREVIEW_GRID
        thumb_w, thumb_h = THUMBNAIL_SIZE
        grid_w = cols * thumb_w
        grid_h = rows * thumb_h
        
        # 创建网格画布
        grid = Image.new("RGB", (grid_w, grid_h), (40, 40, 40))
        
        for i, img_path in enumerate(image_files):
            if i >= cols * rows:
                break
            try:
                img = Image.open(img_path)
                img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
                
                x = (i % cols) * thumb_w + (thumb_w - img.width) // 2
                y = (i // cols) * thumb_h + (thumb_h - img.height) // 2
                
                grid.paste(img, (x, y))
            except Exception as e:
                print(f"    [!] 缩略图处理失败: {img_path.name}: {e}")
        
        # 保存预览图
        preview_path = self.batch_dir / output_name
        grid.save(preview_path, "PNG")
        print(f"[+] 预览图已生成: {preview_path}")
        return preview_path

    def generate_cover(self, output_name="cover.png", width=1280, height=720):
        """
        生成封面图
        用于 Itch.io 封面展示
        """
        category_dirs = [d for d in self.categories.values() if d.exists() and any(d.glob("*.png"))]
        
        if not category_dirs:
            print("[!] 没有可用的图像生成封面")
            return
        
        # 收集前9张图
        sample_images = []
        for cat_dir in category_dirs:
            sample_images.extend(list(cat_dir.glob("*.png"))[:3])
            if len(sample_images) >= 9:
                break
        sample_images = sample_images[:9]
        
        if not sample_images:
            return
        
        cols = min(3, len(sample_images))
        rows = (len(sample_images) + cols - 1) // cols
        thumb_w, thumb_h = THUMBNAIL_SIZE
        grid_w = cols * thumb_w
        grid_h = rows * thumb_h
        
        # 创建封面背景
        cover = Image.new("RGB", (width, height), (20, 20, 30))
        
        # 中心区域放网格预览
        for i, img_path in enumerate(sample_images):
            img = Image.open(img_path)
            img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            
            x_offset = (width - grid_w) // 2 + (i % cols) * thumb_w + (thumb_w - img.width) // 2
            y_offset = (height - grid_h) // 2 + (i // cols) * thumb_h + (thumb_h - img.height) // 2
            
            cover.paste(img, (x_offset, y_offset))
        
        # 添加标题文字（简单用 PIL 画上去）
        draw = ImageDraw.Draw(cover)
        try:
            # 尝试使用系统字体
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        except:
            font = ImageFont.load_default()
        
        title = f"Game Assets Pack #{self.batch_name[:8]}"
        bbox = draw.textbbox((0, 0), title, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(((width - text_w) // 2, height - text_h - 30), title, fill=(255, 255, 255), font=font)
        
        cover_path = self.batch_dir / output_name
        cover.save(cover_path, "PNG")
        print(f"[+] 封面图已生成: {cover_path}")
        return cover_path

    def create_zip_package(self, include_subdirs=True):
        """打包所有资产为 zip"""
        zip_name = f"assets_pack_{self.batch_name}.zip"
        zip_path = self.batch_dir / zip_name
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if include_subdirs:
                for category, cat_dir in self.categories.items():
                    if cat_dir.exists():
                        for file in cat_dir.glob("**/*"):
                            if file.is_file():
                                arcname = f"{category}/{file.name}"
                                zipf.write(file, arcname)
            else:
                for cat_dir in self.categories.values():
                    if cat_dir.exists():
                        for file in cat_dir.glob("*.png"):
                            zipf.write(file, file.name)
        
        print(f"[+] 资产包已打包: {zip_path}")
        print(f"    大小: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
        return zip_path

    def generate_manifest(self):
        """生成上架清单 JSON"""
        manifest = {
            "batch_id": self.batch_name,
            "created": datetime.now().isoformat(),
            "categories": {},
            "total_files": 0,
        }
        
        for category, cat_dir in self.categories.items():
            if cat_dir.exists():
                files = list(cat_dir.glob("*.png"))
                if files:
                    manifest["categories"][category] = {
                        "count": len(files),
                        "files": [f.name for f in files],
                    }
                    manifest["total_files"] += len(files)
        
        manifest_path = self.batch_dir / "manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"[+] 清单已生成: {manifest_path}")
        return manifest

    def run_full_pipeline(self):
        """运行完整打包流程"""
        print("\n" + "=" * 50)
        print("开始处理资产包")
        print("=" * 50)
        
        # 1. 处理图像
        processed = self.process_images()
        
        # 2. 生成预览图（每个分类）
        for cat in self.categories:
            if (self.categories[cat] / "*.png").exists():
                self.generate_preview_grid(cat, f"preview_{cat}.png")
        
        # 3. 生成封面
        self.generate_cover()
        
        # 4. 打包
        self.create_zip_package()
        
        # 5. 生成清单
        self.generate_manifest()
        
        print("\n" + "=" * 50)
        print(f"打包完成！输出目录: {self.batch_dir}")
        print("=" * 50)
        
        return self.batch_dir


def main():
    parser = argparse.ArgumentParser(description="游戏资产整理打包工具")
    parser.add_argument("input_dir", help="资产输入目录")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help="输出目录")
    parser.add_argument("--skip-preview", action="store_true", help="跳过预览图生成")
    parser.add_argument("--skip-cover", action="store_true", help="跳过封面生成")
    
    args = parser.parse_args()
    
    packager = AssetPackager(args.input_dir, args.output)
    
    # 如果只需要处理和打包（不需要生成预览/封面）
    if args.skip_preview and args.skip_cover:
        processed = packager.process_images()
        packager.create_zip_package()
        packager.generate_manifest()
    else:
        packager.run_full_pipeline()


if __name__ == "__main__":
    main()
