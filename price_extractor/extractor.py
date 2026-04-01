"""
Price extraction module for extracting product prices from images.
"""

import base64
import mimetypes
from typing import List, Optional

from loguru import logger
from openai import OpenAI
from pydantic import BaseModel, ValidationError
import json 
import re

def clean_price(price_str: str) -> float:
    # Remove symbols like $, ₹, commas
    cleaned = re.sub(r"[^\d.]", "", price_str)
    return float(cleaned) if cleaned else 0.0

# 🔹 Schema for single item
class PriceItem(BaseModel):
    item: str
    price: float
    currency: Optional[str] = 'INR'


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
        # print("🔥 EXTRACT FUNCTION CALLED")
        """Extract price data from an image."""
        try:
            # 🔹 Read image
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            b64 = base64.b64encode(image_bytes).decode("utf-8")
            mime_type = mimetypes.guess_type(image_path)[0] or "image/png"

            # 🔥 Improved prompt
            prompt = (
    "You are an AI that extracts structured data.\n\n"
    "From this image, extract ALL visible product prices.\n\n"
    "Return ONLY valid JSON in this EXACT format:\n\n"
    "{\n"
    '  "items": [\n'
    "    {\n"
    '      "item": "string",\n'
    '      "price": number,\n'
    '      "currency": "INR"\n'
    "    }\n"
    "  ]\n"
    "}\n\n"
    "Rules:\n"
    "- Output MUST be valid JSON\n"
    "- Do NOT include text outside JSON\n"
    "- price must be numeric only (no ₹, commas)\n"
    "- If no price found, return: {\"items\": []}"
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
            # print("\n===== RAW MODEL OUTPUT =====")
            # print(content)
            # print("================================\n")

            if content is None:
                logger.warning("Empty response from model")
                return None

            # 🔹 Safe parsing
            try:
                # parsed = PriceResponse.model_validate_json(content)
                # return parsed.items
                data = json.loads(content)
                for item in data.get("items", []):
                    if isinstance(item.get("price"), str):
                        item["price"] = clean_price(item["price"])
                parsed = PriceResponse(**data)
                return parsed.items

            except ValidationError as ve:
                logger.error(f"Validation error: {ve}")
                return None

        except Exception as e:
            logger.error(f"Error extracting price from {image_path}: {e}")
            return None