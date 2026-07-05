# 🍑 Peach Counter 桃数统计

> Storm-damage fallen fruit counter for orchard insurance claims.  
> 暴雨/风灾后桃树落果计数，用于农业保险理赔估损。

A lightweight image processing tool that counts fallen peaches from orchard photos. **No machine learning required** — pure Computer Vision (OpenCV) approach using HSV color segmentation and morphology.

纯计算机视觉方案，无需 AI 训练，OpenCV 一把梭。**不依赖任何模型，离线运行。**

---

## 截图 Preview

```
┌─────────────────────────────────────┐
│           桃数统计                    │
│                                       │
│  ○熟桃  ○青桃  ●自动                  │
│                                       │
│  [单张选图]   [批量选文件夹]           │
│  ██████████████░░ 进度条              │
│                                       │
│ ┌─────────┬──────┬──────┐             │
│ │ 文件名  │ 个数 │ 状态 │             │
│ ├─────────┼──────┼──────┤             │
│ │ 桃园1   │  12  │ OK   │             │
│ │ 桃园2   │   8  │ OK   │             │
│ └─────────┴──────┴──────┘             │
│                                       │
│ 总落果数：20     图片：2              │
└─────────────────────────────────────┘
```

---

## Features 功能

- **Single image mode** — Pick one photo, get count instantly  
  单张模式：选图即出数

- **Batch folder mode** — Process entire folder, summary table  
  批量模式：扫一整个文件夹，表格汇总

- **Three detection modes** — Ripe / Green / Auto  
  三种检测模式：熟桃 / 青桃 / 自动

- **Bounding box overlay** — Every detected fruit numbered on result image  
  结果图上框出每个桃子并编号

- **Windows-ready** — Double-click `run.bat` to launch  
  Windows 双击启动，无需手动装依赖

---

## How it works 原理

| Step 步骤 | Method 方法 |
|-----------|------------|
| Color segmentation | Multi-band HSV thresholding (ripe + green + muddy) — 多路 HSV 阈值 |
| Noise removal | Morphological open/close — 形态学去噪 |
| Shape filter | Circularity ≥ 0.3 + aspect ratio ≥ 0.5 — 圆形度+长宽比 |
| Texture filter | Laplacian variance (paper bag rejection) — 纹理过滤（防纸袋） |

---

## Quick Start 快速开始

### Windows

1. Install Python 3.8+ from [python.org](https://www.python.org/downloads/) — **check "Add Python to PATH"**
2. Double-click `run.bat`

### macOS / Linux

```bash
pip install opencv-python numpy
python peach_counter.py
```

### Command Line (headless)

```bash
# Single image
python peach_counter.py photo.jpg

# Or use the core function directly
python3 -c "
from peach_counter import count_peaches
import cv2
img = cv2.imread('orchard.jpg')
n, result = count_peaches(img, mode='auto')
print(f'{n} peaches')
cv2.imwrite('output.jpg', result)
"
```

---

## Dependencies 依赖

- Python 3.8+
- opencv-python
- numpy

All auto-installed by `run.bat` on first launch.

---

## Accuracy 精度说明

| Scene 场景 | Performance 效果 |
|-----------|-----------------|
| Muddy ground + ripe peach | ✅ ~90% |
| Grass + green peach | ✅ ~80-85% |
| Heavy shadow / backlight | ⚠️ Drops to ~60% |
| Dense overlapping fruit | ⚠️ Under-counts |
| Yellow paper bags present | ⚠️ Kick them aside before shooting |

**Tip**: Take photos from directly above (俯拍), ideally with consistent height and good lighting.

---

## License 许可

MIT — do whatever you want.