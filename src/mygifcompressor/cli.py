"""CLI entrypoint for GIF compression."""

from __future__ import annotations

import argparse
from pathlib import Path

from .compressor import BYTES_IN_MEGABYTE, CompressionError, compress_gif


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compress GIFs below a target size while preserving dimensions."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("input"),
        help="Directory containing source GIFs (default: ./input)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for compressed GIFs (default: ./output)",
    )
    parser.add_argument(
        "--target-kb",
        type=int,
        default=1024,
        help="Maximum output size in KB per GIF (default: 1024)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    input_dir: Path = args.input_dir
    output_dir: Path = args.output_dir
    target_size = args.target_kb * 1024

    if target_size <= 0:
        parser.error("--target-kb must be greater than 0")

    if not input_dir.exists() or not input_dir.is_dir():
        parser.error(f"Input directory does not exist: {input_dir}")

    gifs = sorted(input_dir.glob("*.gif"))
    if not gifs:
        print(f"No GIF files found in {input_dir}")
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)

    print(
        f"Found {len(gifs)} GIF(s). Target size: {target_size / BYTES_IN_MEGABYTE:.2f} MB"
    )

    failures = 0

    for gif_path in gifs:
        destination = output_dir / gif_path.name
        try:
            result = compress_gif(gif_path, destination, target_size=target_size)
            status = "OK" if result.success else "WARN"
            print(
                f"[{status}] {gif_path.name}: "
                f"{result.original_size / 1024:.1f}KB -> {result.compressed_size / 1024:.1f}KB "
                f"(colors={result.colors_used})"
            )
            if not result.success:
                failures += 1
        except CompressionError as error:
            failures += 1
            print(f"[ERROR] {gif_path.name}: {error}")

    if failures:
        print(f"Completed with {failures} file(s) above target or errored.")
        return 1

    print("All GIFs were compressed successfully under the target size.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
