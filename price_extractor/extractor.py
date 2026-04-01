"""
Quantity extraction module for extracting item quantities from images.
"""

import base64
import mimetypes
from typing import List, Optional

from loguru import logger
from openai import OpenAI
from pydantic import BaseModel, ValidationError
import json


# 🔹 Schema for single item
class QuantityItem(BaseModel):
    item_name: str
    quantity: float
    unit: str


# 🔹 Schema for multiple items
class QuantityResponse(BaseModel):
    items: List[QuantityItem]


class QuantityExtractor:
    """Handles image processing and quantity extraction."""

    def __init__(
        self,
        model: str,
        base_url: str = "http://127.0.0.1:8080/v1",
    ):
        self.model = model
        self.client = OpenAI(base_url=base_url, api_key="not-needed")

    def extract(self, image_path: str) -> List[QuantityItem] | None:
        """Extract quantity data from an image."""
        try:
            # 🔹 Read image
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            b64 = base64.b64encode(image_bytes).decode("utf-8")
            mime_type = mimetypes.guess_type(image_path)[0] or "image/png"

            prompt = (
                "You are an AI that extracts structured data.\n\n"
                "From this image, extract ALL visible products/items with their quantities.\n\n"
                "Return ONLY valid JSON in this EXACT format:\n\n"
                "{\n"
                '  "items": [\n'
                "    {\n"
                '      "item_name": "string",\n'
                '      "quantity": number,\n'
                '      "unit": "string"\n'
                "    }\n"
                "  ]\n"
                "}\n\n"
                "Rules:\n"
                "- Output MUST be valid JSON\n"
                "- Do NOT include text outside JSON\n"
                "- quantity must be numeric only (e.g. 2, 3.5)\n"
                "- unit should be the measurement unit (e.g. bottles, packs, pieces, kg)\n"
                '- If nothing found, return: {"items": []}'
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
                        "name": "QuantityResponse",
                        "schema": QuantityResponse.model_json_schema(),
                    },
                },
            )

            content = response.choices[0].message.content

            if content is None:
                logger.warning("Empty response from model")
                return None

            # 🔹 Safe parsing
            try:
                data = json.loads(content)
                parsed = QuantityResponse(**data)
                return parsed.items

            except ValidationError as ve:
                logger.error(f"Validation error: {ve}")
                return None

        except Exception as e:
            logger.error(f"Error extracting quantity from {image_path}: {e}")
            return None
