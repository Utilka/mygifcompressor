# mygifcompressor

A small production-ready Python CLI for compressing GIF files to under **1MB** while preserving original dimensions.

## Features

- Preserves original GIF width and height.
- Iteratively reduces color palette depth to decrease file size.
- Uses `input/` and `output/` directories by default.
- Managed with Poetry.

## Requirements

- Python 3.11+
- Poetry

## Installation

```bash
poetry install
```

## Usage

Put source GIFs in `./input`, then run:

```bash
poetry run mygifcompressor
```

Optional arguments:

```bash
poetry run mygifcompressor --input-dir input --output-dir output --target-kb 1024
```

## Notes

- Target size is per-file.
- Compression is best effort: if a GIF cannot be compressed below target without changing dimensions, the tool keeps the best attempt and reports a warning.
