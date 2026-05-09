from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


DEFAULT_LVGL_DIR = Path("lvgl")
DEFAULT_OUTPUT_DIR = Path("littlefs/anim")
DEFAULT_COLOR_FORMAT = "RGB565"
DEFAULT_COMPRESS = "RLE"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract frames from a GIF and convert them to LVGL BIN images."
    )
    parser.add_argument("gif", type=Path, help="Input GIF file.")
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
        choices=("RLE", "LZ4", "NONE"),
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


def main() -> int:
    args = parse_args()
    prefix = args.prefix or args.gif.stem
    converter = require_valid_input(args.gif, args.lvgl_dir)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.keep_frames:
        frame_dir = args.keep_frames
        frame_paths = extract_gif_frames(args.gif, frame_dir, prefix)

        for frame_path in frame_paths:
            convert_frame(
                frame_path,
                converter,
                args.output_dir,
                args.color_format,
                args.compress,
                args.python,
            )
    else:
        with tempfile.TemporaryDirectory(prefix="embedded_anim_") as temp_dir:
            frame_paths = extract_gif_frames(args.gif, Path(temp_dir), prefix)

            for frame_path in frame_paths:
                convert_frame(
                    frame_path,
                    converter,
                    args.output_dir,
                    args.color_format,
                    args.compress,
                    args.python,
                )

    print(f"Done. Converted {len(frame_paths)} frame(s) to {args.output_dir}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
