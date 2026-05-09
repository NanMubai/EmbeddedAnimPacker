# EmbeddedAnimPacker

把 GIF 动画拆成 PNG 帧，并逐帧调用 LVGL 的 `LVGLImage.py` 生成 BIN 文件。

## 使用

建议先创建并启用 Python 虚拟环境：

```bash
python3 -m venv .venv
. .venv/bin/activate
```

然后安装 GIF 读取依赖：

```bash
python3 -m pip install -r requirements.txt
```

然后传入 GIF 文件：

```bash
python3 EmbeddedAnimPacker.py boot.gif
```

默认会调用 `lvgl/scripts/LVGLImage.py`，输出到 `littlefs/anim`。

常用参数：

```bash
python3 EmbeddedAnimPacker.py boot.gif \
  --lvgl-dir ./lvgl \
  --output-dir ./littlefs/anim \
  --cf RGB565 \
  --compress RLE
```

保留中间 PNG 帧：

```bash
python3 EmbeddedAnimPacker.py boot.gif --keep-frames ./frames
```
