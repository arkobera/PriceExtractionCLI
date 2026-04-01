"""
File handler for processing product quantity images in a watched directory.
"""

import csv
import os
from pathlib import Path
import time
from typing import Any, List

from loguru import logger
from watchdog.events import FileSystemEventHandler

from price_extractor.extractor import QuantityItem, QuantityExtractor

# Supported image extensions
IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".webp",
}

CSV_COLUMNS = ["processed_at", "file_path", "item_name", "quantity", "unit"]


def process_image(
    extractor: QuantityExtractor, image_path: str
) -> List[dict[str, Any]] | None:
    """Process a single image and return extracted quantity data as list of dicts."""
    try:
        logger.info(f"Processing image: {image_path}")

        items: List[QuantityItem] | None = extractor.extract(image_path)

        if not items:
            logger.warning(f"No quantity data extracted from {image_path}")
            return None

        results = []
        for item in items:
            data = item.model_dump()
            data.update(
                {
                    "file_path": image_path,
                    "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            results.append(data)

        logger.info(f"Extracted {len(results)} items from {image_path}")
        return results

    except Exception as e:
        logger.error(f"Error processing image {image_path}: {e}")
        return None


def append_to_csv(output_file: str, data_list: List[dict[str, Any]]):
    """Append multiple extracted quantity items to a CSV file."""
    try:
        logger.info(f"Appending data to CSV: {output_file}")

        file_exists = os.path.exists(output_file)
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

        with open(output_file, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_COLUMNS)

            if not file_exists:
                writer.writeheader()

            for data in data_list:
                writer.writerow({col: data.get(col, "") for col in CSV_COLUMNS})

        logger.info("Data appended to CSV successfully.")

    except Exception as e:
        logger.error(f"Error writing to CSV {output_file}: {e}")


class QuantityFileHandler(FileSystemEventHandler):
    """Handles file system events for new images containing quantity data."""

    def __init__(self, extractor: QuantityExtractor, output_file: str):
        self.extractor = extractor
        self.output_file = output_file
        self.processed_files: set[str] = set()

        logger.info(f"Output will be saved to: {self.output_file}")

        self.image_extensions = IMAGE_EXTENSIONS

    def on_created(self, event):
        """Handle new file creation events."""
        if event.is_directory:
            return

        file_path = str(event.src_path)
        file_ext = Path(file_path).suffix.lower()

        if file_ext in IMAGE_EXTENSIONS and file_path not in self.processed_files:
            logger.info(f"New image detected: {file_path}")
            self._process_and_save(file_path)

    def _process_and_save(self, image_path: str):
        """Process image and append extracted data to CSV."""
        self.processed_files.add(image_path)

        results = process_image(self.extractor, image_path)
        if not results:
            return

        append_to_csv(self.output_file, results)

        for item in results:
            logger.info(
                f"{image_path}: {item['item_name']} - {item['quantity']} {item['unit']}"
            )

    def process_image(self, image_path: str):
        """Process a single image (used manually or for existing files)."""
        self._process_and_save(image_path)
