"""
Price extraction module for extracting product prices from images.
"""

import base64
import mimetypes
from typing import List

from loguru import logger
from openai import OpenAI
from pydantic import BaseModel, ValidationError


# 🔹 Schema for single item
class PriceItem(BaseModel):
    item: str
    price: float
    currency: str


# 🔹 Schema for multiple items
class PriceResponse(BaseModel):
    items: List[PriceItem]


class PriceExtractor:
    """Handles image processing and price extraction."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://127.0.0.1:8080/v1",
    ):
        self.model = model
        self.client = OpenAI(base_url=base_url, api_key="not-needed")

    def extract(self, image_path: str) -> List[PriceItem] | None:
        """Extract price data from an image."""
        try:
            # 🔹 Read image
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            b64 = base64.b64encode(image_bytes).decode("utf-8")
            mime_type = mimetypes.guess_type(image_path)[0] or "image/png"

            # 🔥 Improved prompt
            prompt = (
                "Extract all visible product or service prices from this image.\n\n"
                "Return ONLY a JSON object in this format:\n"
                "{\n"
                '  "items": [\n'
                "    {\n"
                '      "item": "product name",\n'
                '      "price": 123.45,\n'
                '      "currency": "INR"\n'
                "    }\n"
                "  ]\n"
                "}\n\n"
                "Rules:\n"
                "- price must be numeric (no ₹, $, commas)\n"
                "- currency must be ISO code (INR, USD, EUR)\n"
                "- if multiple items exist, include all\n"
                "- if unclear, make best guess\n"
            )

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{b64}",
                                },
                            },
                        ],
                    }
                ],
                temperature=0.0,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "PriceResponse",
                        "schema": PriceResponse.model_json_schema(),
                    },
                },
            )

            content = response.choices[0].message.content

            if content is None:
                logger.warning("Empty response from model")
                return None

            # 🔹 Safe parsing
            try:
                parsed = PriceResponse.model_validate_json(content)
                return parsed.items
            except ValidationError as ve:
                logger.error(f"Validation error: {ve}")
                return None

        except Exception as e:
            logger.error(f"Error extracting price from {image_path}: {e}")
            return None