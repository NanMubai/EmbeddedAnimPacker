# AGENTS.md

本文件给在本仓库中工作的编码代理使用。修改代码前先阅读 `README.md` 和当前脚本实现，保持改动小而直接。

## 项目概览

`EmbeddedAnimPacker` 是一个 Python 命令行工具，用于：

1. 读取输入 GIF。
2. 使用 Pillow 拆分为逐帧 PNG。
3. 调用本地 LVGL 仓库中的 `scripts/LVGLImage.py`。
4. 生成适合放入 LittleFS 的 LVGL BIN 图片文件。

主入口是 `EmbeddedAnimPacker.py`，提供两种用法：

- **命令行**：传入 GIF 与参数，行为与脚本最初版本一致。
- **交互式菜单**：不带 GIF 参数（或传 `-i`/`--interactive`）时进入，基于 `questionary` 选择素材并配置参数。`_select_gifs()` 采用两步式选择，返回 GIF 列表，支持多选 / 一键全选 / 手动输入路径。

两条路径都汇聚到同一个 `run_conversion(ConversionConfig)` 单 GIF 管线。命令行直接调用它；菜单经 `run_conversions(gifs, template)` 逐个调用（continue-on-error，末尾打印聚合结果），且多选时强制用各 GIF 自身 stem 作帧前缀以避免冲突。

## 重要文件

- `EmbeddedAnimPacker.py`: CLI 主程序。
- `requirements.txt`: Python 运行依赖：`Pillow`（读取 GIF）与 `questionary`（交互式菜单）。
- `README.md`: 面向用户的使用说明。
- `default.gif`: 示例输入素材。
- `frames/`: `--keep-frames` 生成的中间 PNG 帧，通常不要提交。
- `littlefs/anim/`: 默认 BIN 输出目录，通常不要提交。
- `lvgl/`: 本地 LVGL checkout，作为外部工具目录使用，通常不要提交。

## 本地环境

推荐使用虚拟环境：

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
```

运行完整转换需要本地存在 LVGL 仓库，并确保 `lvgl/scripts/LVGLImage.py` 可用。

## 常用命令

安装依赖：

```bash
python3 -m pip install -r requirements.txt
```

进入交互式菜单（不带 GIF 参数，或显式加 `-i`）：

```bash
python3 EmbeddedAnimPacker.py
python3 EmbeddedAnimPacker.py -i
```

运行转换（命令行）：

```bash
python3 EmbeddedAnimPacker.py default.gif
```

指定 LVGL 和输出目录：

```bash
python3 EmbeddedAnimPacker.py default.gif \
  --lvgl-dir ./lvgl \
  --output-dir ./littlefs/anim \
  --cf RGB565 \
  --compress RLE
```

保留中间帧：

```bash
python3 EmbeddedAnimPacker.py default.gif --keep-frames ./frames
```

只检查 CLI 参数和基础语法时，可运行：

```bash
python3 -m py_compile EmbeddedAnimPacker.py
python3 EmbeddedAnimPacker.py --help
```

## 代码约定

- 使用 Python 标准库和 `pathlib.Path` 处理路径。
- 保持 CLI 参数清晰，新增参数时同步更新 `README.md`。
- 对用户输入、文件路径和外部工具缺失给出明确错误信息。
- 调用外部命令时使用参数列表，不拼接 shell 字符串。
- 默认行为应避免留下临时文件；只有用户传入 `--keep-frames` 时才保留中间 PNG。
- 不要引入重量级依赖，除非能明显简化核心流程。
- `questionary` 只在 `run_interactive_menu()` 内部按需导入；纯命令行路径不得依赖它，缺失时给出清晰安装提示。
- 新增转换参数时，同步加到 `ConversionConfig`、命令行参数和交互式菜单三处，并更新 `README.md`。

## 版本控制注意事项

- 不要提交 `.venv/`、`frames/`、`littlefs/anim/`、`lvgl/`、缓存目录或本地编辑器文件。
- Commit messages must be written in English and follow Conventional Commits 1.0.0, for example `feat: add frame prefix option` or `fix: validate GIF input path`.
- Version numbers must follow Semantic Versioning 2.0.0.
- 如果需要新增示例输入素材，确认文件大小合理，并在 `README.md` 中说明用途。
- 如果修改默认输出位置、颜色格式或压缩格式，请同步检查 `.gitignore` 和文档。

## 验证建议

没有完整 LVGL 环境时，至少运行：

```bash
python3 -m py_compile EmbeddedAnimPacker.py
python3 EmbeddedAnimPacker.py --help
```

有完整 LVGL 环境时，使用小 GIF 做一次端到端转换，并检查输出目录中的 `.bin` 文件数量是否等于 GIF 帧数。

交互式菜单需要真实 TTY 才能运行（`questionary` 基于 `prompt_toolkit`），不便用管道自动化。无 TTY 时可单独调用 `discover_gifs()` 和 `run_conversion(ConversionConfig(...))` 验证非交互逻辑。
