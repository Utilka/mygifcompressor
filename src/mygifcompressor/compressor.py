"""Core GIF compression logic."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageSequence

BYTES_IN_MEGABYTE = 1_048_576


@dataclass(frozen=True)
class CompressionResult:
    """Represents the output of a compression attempt."""

    input_path: Path
    output_path: Path
    original_size: int
    compressed_size: int
    target_size: int
    success: bool
    colors_used: int


class CompressionError(Exception):
    """Raised when GIF compression cannot be completed."""


def compress_gif(
    input_path: Path,
    output_path: Path,
    target_size: int = BYTES_IN_MEGABYTE,
    color_steps: tuple[int, ...] = (256, 192, 128, 96, 64, 48, 32, 24, 16),
    frame_step_options: tuple[int, ...] = (1, 2, 3, 4),
) -> CompressionResult:
    """Compress a GIF by reducing palette colors while preserving dimensions.

    The compressor keeps width and height intact and iteratively tries combinations of:
    - lower palette color counts
    - frame downsampling (while preserving overall animation duration)

    It returns as soon as the target size is achieved, otherwise it keeps the smallest
    candidate it could produce.
    """

    if target_size <= 0:
        raise ValueError("target_size must be a positive integer")

    if not input_path.exists():
        raise CompressionError(f"Input GIF does not exist: {input_path}")

    if input_path.suffix.lower() != ".gif":
        raise CompressionError(f"Input file is not a GIF: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    original_size = input_path.stat().st_size
    best_size = float("inf")
    best_colors = color_steps[-1]

    with Image.open(input_path) as source:
        if source.format != "GIF":
            raise CompressionError(f"Unsupported image format: {source.format}")

        size = source.size
        durations = [
            frame.info.get("duration", source.info.get("duration", 100))
            for frame in ImageSequence.Iterator(source)
        ]
        loop = source.info.get("loop", 0)
        disposal = source.info.get("disposal", 2)

        rgba_frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(source)]

        if not rgba_frames:
            raise CompressionError(f"GIF has no frames: {input_path}")

        for frame_step in frame_step_options:
            sampled_frames: list[Image.Image] = []
            sampled_durations: list[int] = []

            for index in range(0, len(rgba_frames), frame_step):
                sampled_frames.append(rgba_frames[index])
                end_index = min(index + frame_step, len(durations))
                sampled_durations.append(sum(durations[index:end_index]))

            if not sampled_frames:
                continue

            for colors in color_steps:
                processed_frames = [
                    frame.quantize(colors=colors, method=Image.Quantize.FASTOCTREE)
                    for frame in sampled_frames
                ]

                first, *rest = processed_frames
                first.save(
                    output_path,
                    save_all=True,
                    append_images=rest,
                    optimize=True,
                    loop=loop,
                    duration=sampled_durations,
                    disposal=disposal,
                )

                with Image.open(output_path) as candidate:
                    if candidate.size != size:
                        raise CompressionError(
                            "Compression changed GIF dimensions, which is not allowed."
                        )

                compressed_size = output_path.stat().st_size
                if compressed_size < best_size:
                    best_size = compressed_size
                    best_colors = colors

                if compressed_size <= target_size:
                    return CompressionResult(
                        input_path=input_path,
                        output_path=output_path,
                        original_size=original_size,
                        compressed_size=compressed_size,
                        target_size=target_size,
                        success=True,
                        colors_used=colors,
                    )

    final_size = output_path.stat().st_size if output_path.exists() else original_size
    return CompressionResult(
        input_path=input_path,
        output_path=output_path,
        original_size=original_size,
        compressed_size=final_size,
        target_size=target_size,
        success=final_size <= target_size,
        colors_used=best_colors,
    )
