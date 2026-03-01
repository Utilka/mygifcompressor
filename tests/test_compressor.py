from pathlib import Path

from PIL import Image

from mygifcompressor.compressor import compress_gif


def _create_sample_gif(path: Path, frames: int = 6, size: tuple[int, int] = (120, 80)) -> None:
    images = []
    for index in range(frames):
        frame = Image.new("RGB", size, color=(index * 40 % 255, index * 30 % 255, index * 20 % 255))
        images.append(frame)

    first, *rest = images
    first.save(path, save_all=True, append_images=rest, duration=80, loop=0)


def test_compress_gif_preserves_dimensions(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.gif"
    output_path = tmp_path / "compressed.gif"

    _create_sample_gif(input_path, size=(200, 90))

    result = compress_gif(input_path, output_path, target_size=300_000)

    with Image.open(input_path) as original, Image.open(output_path) as compressed:
        assert original.size == compressed.size

    assert result.output_path.exists()
    assert result.original_size >= result.compressed_size or result.compressed_size > 0


def test_compress_gif_reports_when_target_unreachable(tmp_path: Path) -> None:
    input_path = tmp_path / "sample.gif"
    output_path = tmp_path / "compressed.gif"

    _create_sample_gif(input_path)

    result = compress_gif(input_path, output_path, target_size=1)

    assert result.success is False
    assert output_path.exists()


def test_compress_gif_can_reduce_frame_count_for_stronger_compression(tmp_path: Path) -> None:
    input_path = tmp_path / "animated.gif"
    output_path = tmp_path / "compressed.gif"

    _create_sample_gif(input_path, frames=18, size=(220, 140))

    result = compress_gif(input_path, output_path, target_size=2_000)

    with Image.open(input_path) as original, Image.open(output_path) as compressed:
        assert compressed.size == original.size
        assert compressed.n_frames <= original.n_frames

    assert result.compressed_size <= result.original_size


def test_compress_gif_merges_near_duplicate_frames(tmp_path: Path) -> None:
    input_path = tmp_path / "nearly-static.gif"
    output_path = tmp_path / "compressed.gif"

    frames = []
    for index in range(12):
        color = (20, 40, 60) if index % 3 else (21, 41, 61)
        frames.append(Image.new("RGB", (180, 120), color=color))

    first, *rest = frames
    first.save(input_path, save_all=True, append_images=rest, duration=60, loop=0)

    result = compress_gif(input_path, output_path, target_size=1)

    with Image.open(input_path) as original, Image.open(output_path) as compressed:
        assert compressed.size == original.size
        assert compressed.n_frames < original.n_frames

    assert result.compressed_size <= result.original_size
