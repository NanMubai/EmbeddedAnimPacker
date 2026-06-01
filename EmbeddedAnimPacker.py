from __future__ import annotations

import argparse
import contextlib
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


__version__ = "0.2.0"

DEFAULT_LVGL_DIR = Path("lvgl")
DEFAULT_OUTPUT_DIR = Path("littlefs/anim")
DEFAULT_COLOR_FORMAT = "RGB565"
DEFAULT_COMPRESS = "RLE"
COMPRESS_CHOICES = ("RLE", "LZ4", "NONE")
COMMON_COLOR_FORMATS = ("RGB565", "RGB565A8", "RGB888", "ARGB8888", "XRGB8888")


@dataclass
class ConversionConfig:
    """All inputs needed for one GIF -> LVGL BIN conversion run."""

    gif: Path
    lvgl_dir: Path = DEFAULT_LVGL_DIR
    output_dir: Path = DEFAULT_OUTPUT_DIR
    color_format: str = DEFAULT_COLOR_FORMAT
    compress: str = DEFAULT_COMPRESS
    prefix: str | None = None
    keep_frames: Path | None = None
    python: str = sys.executable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract frames from a GIF and convert them to LVGL BIN images."
    )
    parser.add_argument(
        "gif",
        type=Path,
        nargs="?",
        default=None,
        help="Input GIF file. Omit to launch the interactive menu.",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Launch the interactive configuration menu (used automatically when no GIF is given).",
    )
    parser.add_argument(
        "--lvgl-dir",
        type=Path,
        default=DEFAULT_LVGL_DIR,
        help=f"LVGL directory. Default: {DEFAULT_LVGL_DIR}",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for generated .bin files. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--cf",
        "--color-format",
        dest="color_format",
        default=DEFAULT_COLOR_FORMAT,
        help=f"LVGL color format. Default: {DEFAULT_COLOR_FORMAT}",
    )
    parser.add_argument(
        "--compress",
        default=DEFAULT_COMPRESS,
        choices=COMPRESS_CHOICES,
        help=f"LVGL compression mode. Default: {DEFAULT_COMPRESS}",
    )
    parser.add_argument(
        "--prefix",
        default=None,
        help="Frame filename prefix. Default: input GIF stem.",
    )
    parser.add_argument(
        "--keep-frames",
        type=Path,
        default=None,
        help="Keep extracted PNG frames in this directory instead of using a temp directory.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable used to run LVGLImage.py. Default: current interpreter.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser.parse_args()


def require_valid_input(gif_path: Path, lvgl_dir: Path) -> Path:
    if not gif_path.is_file():
        raise FileNotFoundError(f"GIF file not found: {gif_path}")

    if gif_path.suffix.lower() != ".gif":
        raise ValueError(f"Input must be a .gif file: {gif_path}")

    converter = lvgl_dir / "scripts" / "LVGLImage.py"
    if not converter.is_file():
        raise FileNotFoundError(f"LVGL image converter not found: {converter}")

    return converter


def extract_gif_frames(gif_path: Path, output_dir: Path, prefix: str) -> list[Path]:
    try:
        from PIL import Image, ImageSequence
    except ImportError as exc:
        raise RuntimeError(
            "Pillow is required to read GIF files. Install it with: "
            "python3 -m pip install Pillow"
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    frame_paths: list[Path] = []

    with Image.open(gif_path) as gif:
        for index, frame in enumerate(ImageSequence.Iterator(gif)):
            frame_path = output_dir / f"{prefix}_{index:04d}.png"
            frame.convert("RGBA").save(frame_path)
            frame_paths.append(frame_path)

    if not frame_paths:
        raise RuntimeError(f"No frames found in GIF: {gif_path}")

    return frame_paths


def convert_frame(
    frame_path: Path,
    converter: Path,
    output_dir: Path,
    color_format: str,
    compress: str,
    python_executable: str,
) -> None:
    print("Converting:", frame_path)
    subprocess.run(
        [
            python_executable,
            str(converter),
            "--ofmt",
            "BIN",
            "--cf",
            color_format,
            "--compress",
            compress,
            "-o",
            str(output_dir),
            str(frame_path),
        ],
        check=True,
    )


def run_conversion(cfg: ConversionConfig) -> int:
    """Validate inputs, extract frames and convert each one to an LVGL BIN."""
    prefix = cfg.prefix or cfg.gif.stem
    converter = require_valid_input(cfg.gif, cfg.lvgl_dir)

    cfg.output_dir.mkdir(parents=True, exist_ok=True)

    with contextlib.ExitStack() as stack:
        if cfg.keep_frames is not None:
            frame_dir = cfg.keep_frames
        else:
            frame_dir = Path(
                stack.enter_context(
                    tempfile.TemporaryDirectory(prefix="embedded_anim_")
                )
            )

        frame_paths = extract_gif_frames(cfg.gif, frame_dir, prefix)
        for frame_path in frame_paths:
            convert_frame(
                frame_path,
                converter,
                cfg.output_dir,
                cfg.color_format,
                cfg.compress,
                cfg.python,
            )

    print(f"Done. Converted {len(frame_paths)} frame(s) to {cfg.output_dir}.")
    return 0


# --------------------------------------------------------------------------- #
# Interactive menu
# --------------------------------------------------------------------------- #


class _MenuCancelled(Exception):
    """Raised when the user aborts the interactive menu (Ctrl-C / quit)."""


def _ask(question):
    """Run a questionary prompt; treat a None answer (Ctrl-C) as cancellation."""
    answer = question.ask()
    if answer is None:
        raise _MenuCancelled
    return answer


def discover_gifs() -> list[Path]:
    """List *.gif files in the current working directory."""
    return sorted(Path.cwd().glob("*.gif"))


def _select_gif(questionary) -> Path:
    manual = "✏️  手动输入路径…"
    quit_choice = "退出"
    while True:
        by_name = {gif.name: gif for gif in discover_gifs()}
        if not by_name:
            questionary.print(
                "当前目录没有找到 .gif 文件，请手动输入路径。", style="fg:yellow"
            )
        answer = _ask(
            questionary.select(
                "选择源 GIF（当前目录）：",
                choices=[*by_name, manual, quit_choice],
            )
        )
        if answer == quit_choice:
            raise _MenuCancelled
        if answer == manual:
            candidate = Path(_ask(questionary.path("GIF 路径："))).expanduser()
        else:
            candidate = by_name[answer]

        if candidate.is_file() and candidate.suffix.lower() == ".gif":
            return candidate
        questionary.print(f"无效的 GIF 文件：{candidate}", style="bold fg:red")


def run_interactive_menu() -> int:
    try:
        import questionary
    except ImportError:
        print(
            "交互式菜单需要 questionary。请安装：\n"
            "    python3 -m pip install questionary\n"
            "或：python3 -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    print("=== EmbeddedAnimPacker 交互式菜单 ===")

    try:
        gif = _select_gif(questionary)

        lvgl_dir = _ask(
            questionary.path("LVGL 目录：", default=str(DEFAULT_LVGL_DIR))
        )
        output_dir = _ask(
            questionary.path("输出目录：", default=str(DEFAULT_OUTPUT_DIR))
        )

        color_format = _ask(
            questionary.select(
                "颜色格式 (color format)：",
                choices=[*COMMON_COLOR_FORMATS, "自定义…"],
                default=DEFAULT_COLOR_FORMAT,
            )
        )
        if color_format == "自定义…":
            color_format = _ask(
                questionary.text("自定义颜色格式：", default=DEFAULT_COLOR_FORMAT)
            ).strip()

        compress = _ask(
            questionary.select(
                "压缩方式 (compress)：",
                choices=list(COMPRESS_CHOICES),
                default=DEFAULT_COMPRESS,
            )
        )

        prefix = _ask(
            questionary.text("帧文件名前缀（留空使用 GIF 文件名）：", default="")
        ).strip() or None

        keep_frames: Path | None = None
        if _ask(questionary.confirm("保留中间 PNG 帧？", default=False)):
            keep_frames = Path(
                _ask(questionary.path("帧输出目录：", default="frames"))
            ).expanduser()

        cfg = ConversionConfig(
            gif=gif,
            lvgl_dir=Path(lvgl_dir).expanduser(),
            output_dir=Path(output_dir).expanduser(),
            color_format=color_format,
            compress=compress,
            prefix=prefix,
            keep_frames=keep_frames,
        )

        print("\n--- 配置汇总 ---")
        print(f"  源 GIF    : {cfg.gif}")
        print(f"  LVGL 目录 : {cfg.lvgl_dir}")
        print(f"  输出目录  : {cfg.output_dir}")
        print(f"  颜色格式  : {cfg.color_format}")
        print(f"  压缩方式  : {cfg.compress}")
        print(f"  帧前缀    : {cfg.prefix or cfg.gif.stem}")
        print(f"  保留帧    : {cfg.keep_frames or '否（使用临时目录）'}")
        print("----------------")

        if not _ask(questionary.confirm("确认开始转换？", default=True)):
            raise _MenuCancelled
    except _MenuCancelled:
        print("已取消。")
        return 0

    return run_conversion(cfg)


def main() -> int:
    args = parse_args()

    if args.interactive or args.gif is None:
        return run_interactive_menu()

    cfg = ConversionConfig(
        gif=args.gif,
        lvgl_dir=args.lvgl_dir,
        output_dir=args.output_dir,
        color_format=args.color_format,
        compress=args.compress,
        prefix=args.prefix,
        keep_frames=args.keep_frames,
        python=args.python,
    )
    return run_conversion(cfg)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n已取消。", file=sys.stderr)
        raise SystemExit(130)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
