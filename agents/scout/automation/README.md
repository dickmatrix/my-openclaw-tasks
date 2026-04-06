# 游戏资产变现自动化工具

## 快速开始

## 快速开始

### 1. 安装依赖

```bash
cd automation
pip install -r requirements.txt
```

### 2. 安装 ComfyUI（macOS 原生 + MPS 加速）

```bash
# 给脚本加执行权限
chmod +x install_comfyui_mac.sh
chmod +x start_comfyui.sh

# 运行安装（首次，5-30分钟）
./install_comfyui_mac.sh
```

> 安装内容：Python 3.10 虚拟环境 + ComfyUI + PyTorch (MPS) + SD 1.5 模型（约 4GB）
> 如果脚本中断，重新运行会从断点继续

### 3. 启动 ComfyUI

```bash
./start_comfyui.sh
```

正常启动后看到：
```
Server started on 127.0.0.1:8188
```
即可。

**安全说明：**
- `--listen 127.0.0.1` 仅监听本地，**不对外暴露**
- 无公网 IP，无端口映射，**完全内网运行**
- 模型下载仅首次需要联网，之后完全离线

---

## 工具说明

### 工具说明

| 脚本 | 功能 | 模式 |
|------|------|------|
| `install_comfyui_mac.sh` | 安装 ComfyUI（一次性） | Bash |
| `start_comfyui.sh` | 启动 ComfyUI 服务 | Bash |
| `asset_generator.py` | 批量生成游戏资产 | Python |
| `asset_packager.py` | 整理 + 打包 + 生成预览封面 | Python |
| `itchio_uploader.py` | Itch.io 上传辅助 | Python |
| `tasks_rpg_assets.json` | 预设生成任务配置 | JSON |

**ComfyUI 模式：** 支持自动检测，使用 ComfyUI 原生 API（MPS 加速）
**SD WebUI 模式：** 设置 `COMFYUI_MODE=false` 切换到 Automatic1111 兼容模式

#### 交互式使用（推荐新手）

```bash
python asset_generator.py
```

会引导你选择：
- 生成预设类型（像素图标 / PBR材质 / 角色立绘 / UI元素）
- 主题库（武器 / 药水 / 装备 / 怪物等）
- 每主题生成数量

#### 配置文件批量生成

```bash
python asset_generator.py --config tasks_rpg_assets.json
```

可编辑 `tasks_rpg_assets.json` 自定义生成任务。

#### 生成结果

生成完成后会保存在 `output_assets/YYYYMMDD_HHMMSS/` 目录下，包含：
- 原始生成图像（PNG）
- 生成报告 `generation_report.json`

---

### 工具2：整理打包 `asset_packager.py`

将生成好的图像整理、命名、打包，准备发布。

#### 完整打包流程

```bash
python asset_packager.py ./output_assets/20260403_143022
```

会自动完成：
- [x] 图像分类（icons / textures / characters / ui）
- [x] 标准化命名
- [x] 多尺寸缩略图生成
- [x] 预览网格图生成
- [x] Itch.io 封面图生成
- [x] zip 打包
- [x] 清单 JSON

#### 输出目录结构

```
packaged_assets/batch_20260403_143022/
├── icons/           # 分类图像
├── textures/
├── characters/
├── ui/
├── batch_20260403_143022.zip   # 打包好的资产包
├── manifest.json    # 资产清单
├── preview.png      # 3x3 预览网格
└── cover.png        # Itch.io 封面
```

---

## 完整变现流程

```
[Step 1] 生成资产
  python asset_generator.py --config tasks_rpg_assets.json

[Step 2] 整理打包
  python asset_packager.py ./output_assets/最新生成目录

[Step 3] 人工筛选 & 定价
  检查 packaged_assets/batch_XXX/ 下的资产
  人工修图（推荐外包，5-20元/张）

[Step 4] 发布上架
  Itch.io: https://itch.io/game-assets
  Unity Asset Store: https://assetstore.unity.com/publish
  
[Step 5] 收款
  Itch.io: 直连 Stripe/PayPal
  Unity: 月结转账
```

---

## 变现平台对比

| 平台 | 审核速度 | 流量 | 分成比例 | 适合资产 |
|------|:---:|:---:|:---:|------|
| **Itch.io** | 即时 | 中 | 0% / 10%* | 独立游戏资产 |
| **Unity Asset Store** | 3-7天 | 高 | 30% | 商业化资产 |
| **Unreal Marketplace** | 1-2周 | 高 | 12% | 3D资产为主 |
| **Sketchfab** | 1-3天 | 中 | 30-50% | 3D模型 |
| **Patreon** | 无审核 | 高 | 5-12% | 持续产出型 |

*平台默认抽10%，可降至0%使用"itch.io has no cut"选项

---

## 预期ROI参考

| 资产类型 | 成本估算 | 售价 | 月销目标 | 月收入目标 |
|---------|:---:|:---:|:---:|:---:|
| 像素图标包 80个 | ¥200-500 | $10-15 | 10-20单 | $100-300 |
| PBR材质包 20套 | ¥300-800 | $20-30 | 5-10单 | $100-300 |
| BGM 10首 | ¥100-300 | $5-10 | 10-30单 | $50-300 |
| 角色立绘 15张 | ¥500-1500 | $15-25 | 5-15单 | $75-375 |

---

## 常见问题

**Q: SD API 连接失败？**
```bash
# 检查 ComfyUI 是否启动
curl http://localhost:7860/system_stats

# 检查端口是否正确
lsof -i :7860
```

**Q: 生成图像质量差？**
- 调整 `ASSET_PRESETS` 中的 `steps` 和 `cfg_scale` 参数
- 细化 prompt 描述词
- 使用更精准的否定词

**Q: Unity Asset Store 审核被拒？**
- AI 生成内容需在描述中声明
- 确保资产为原创（非侵权训练数据）
- 避免使用品牌/版权相关词汇

---

*最后更新：2026-04-03*
