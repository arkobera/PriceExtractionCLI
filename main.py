#!/usr/bin/env python3
"""
Quantity extraction tool that processes images using a Vision Language Model.
"""

from pathlib import Path
import time

import click
from loguru import logger
from watchdog.observers import Observer

from price_extractor.file_handler import (
    IMAGE_EXTENSIONS,
    QuantityFileHandler,
    append_to_csv,
    process_image,
)
from price_extractor.extractor import QuantityExtractor
from price_extractor.llama_server import (
    DEFAULT_PORT,
    start_llama_server,
    stop_server,
    wait_for_server,
)
from price_extractor.table_printer import print_results_table


# -------------------------
# Helper Functions
# -------------------------
def collect_image_paths(paths: tuple[str, ...]) -> list[Path]:
    image_paths: list[Path] = []

    for p in paths:
        path = Path(p)

        if path.is_dir():
            for file_path in path.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in IMAGE_EXTENSIONS:
                    image_paths.append(file_path)

        elif path.is_file():
            if path.suffix.lower() in IMAGE_EXTENSIONS:
                image_paths.append(path)
            else:
                logger.warning(f"Skipping non-image file: {path}")

        else:
            logger.warning(f"Path does not exist: {path}")

    return image_paths


@click.group()
def cli():
    """Quantity extraction tool using local LLM."""


# -------------------------
# WATCH MODE
# -------------------------
@cli.command()
@click.option("--dir", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--model", required=True)
@click.option("--port", default=DEFAULT_PORT, type=int)
def watch(dir: Path, model: str, port: int):
    """Watch a directory and process new images for quantities."""

    logger.info(f"Watching directory: {dir}")

    base_url = f"http://127.0.0.1:{port}/v1"
    extractor = QuantityExtractor(model, base_url=base_url)

    handler = QuantityFileHandler(extractor, str(dir / "quantities.csv"))

    observer = Observer()
    observer.schedule(handler, str(dir), recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


# -------------------------
# PROCESS MODE
# -------------------------
@cli.command()
@click.option("--model", required=True)
@click.option("--output", type=click.Path(path_type=Path), default=None)
@click.option("--port", default=DEFAULT_PORT, type=int)
@click.argument("paths", nargs=-1, required=True)
def process(model: str, output: Path | None, port: int, paths: tuple[str, ...]):
    """Process images and extract quantities."""

    image_paths = collect_image_paths(paths)

    if not image_paths:
        logger.warning("No image files found.")
        return

    logger.info(f"Found {len(image_paths)} images")

    base_url = f"http://127.0.0.1:{port}/v1"
    extractor = QuantityExtractor(model, base_url=base_url)

    results = []

    for image_path in image_paths:
        print("Processing:", image_path)

        items = process_image(extractor, str(image_path))

        if not items:
            logger.warning(f"No items extracted from {image_path}")
            continue

        results.extend(items)

        if output:
            append_to_csv(str(output), items)

    if results:
        print_results_table(results)
    else:
        logger.warning("No results extracted.")

    logger.info("Processing complete.")


# -------------------------
# ENTRY POINT
# -------------------------
if __name__ == "__main__":
    cli()
