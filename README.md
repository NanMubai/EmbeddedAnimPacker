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

不带任何参数运行，会进入交互式菜单：从当前目录选择源 GIF（支持**多选或一键全选**，批量转换）、逐项配置参数，最后确认并执行转换：

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

## 抽帧 / 减帧

嵌入式场景下每一帧都是占 flash / RAM 的 `.bin`，可以用下面的选项**截取片段**或
**减少帧数**。抽帧只决定哪些帧被送去转 BIN，输出帧始终从 `0000` **连续重新编号**
（不会留空洞，方便 LVGL 顺序播放）。

| 选项 | 含义 |
| --- | --- |
| `--frame-start N` | 起始帧（含），默认 `0` |
| `--frame-end N` | 结束帧（含），默认末帧 |
| `--frame-step N` | 区间内每 N 帧取 1（隔帧减帧），默认 `1`（全保留） |
| `--frame-count N` | 区间内均匀抽 N 帧；与 `--frame-step` **互斥**，给定时优先 |

隔帧减半（12 帧 → 6 帧）：

```bash
python3 EmbeddedAnimPacker.py boot.gif --frame-step 2
```

只取前半段（第 0–11 帧）：

```bash
python3 EmbeddedAnimPacker.py boot.gif --frame-start 0 --frame-end 11
```

把任意帧数均匀抽成固定 8 帧：

```bash
python3 EmbeddedAnimPacker.py boot.gif --frame-count 8
```

组合使用，并保留抽完的 PNG 以便预览：

```bash
python3 EmbeddedAnimPacker.py boot.gif --frame-start 0 --frame-end 11 --frame-step 2 \
  --keep-frames ./frames
```

> 多选 / 全选批量转换时，同一套抽帧参数会套用到所有 GIF；固定的 `--frame-end`
> 在较短的 GIF 上会自动收敛到其末帧。交互式菜单里也有对应的「是否抽帧」步骤。
