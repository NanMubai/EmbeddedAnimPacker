# EmbeddedAnimPacker

把 GIF 动画拆成 PNG 帧，并逐帧调用 LVGL 的 `LVGLImage.py` 生成 BIN 文件。

## 使用

建议先创建并启用 Python 虚拟环境：

```bash
python3 -m venv .venv
. .venv/bin/activate
```

然后安装依赖（Pillow 用于读取 GIF，questionary 用于交互式菜单）：

```bash
python3 -m pip install -r requirements.txt
```

## 交互式菜单

不带任何参数运行，会进入交互式菜单：可以从当前目录选择源 GIF、逐项配置参数，最后确认并执行转换：

```bash
python3 EmbeddedAnimPacker.py
```

也可以用 `-i` / `--interactive` 显式进入菜单。菜单仅在进入时才需要 `questionary`；纯命令行用法不依赖它。

## 命令行

直接传入 GIF 文件即可（行为与以前一致）：

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
