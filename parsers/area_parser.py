"""
Vietnamese area parser.
Handles various area formats.
"""

import re
from typing import Optional


def parse_area(area_text: str) -> Optional[float]:
    """
    Parse Vietnamese area text to square meters.

    Examples:
        "85.5 m2" -> 85.5
        "85,5m²" -> 85.5
        "85m2" -> 85.0
        "1000m²" -> 1000.0
        "Diện tích: 100m2" -> 100.0

    Returns:
        Area in square meters or None if parsing fails
    """
    if not area_text:
        return None

    # Normalize text
    text = area_text.lower().strip()
    text = text.replace(",", ".")
    text = text.replace("²", "2")
    text = text.replace("m2", " m2 ")

    # Pattern: X.Y m2 or Xm2
    pattern = re.search(r"(\d+(?:\.\d+)?)\s*m2", text)
    if pattern:
        return float(pattern.group(1))

    # Pattern: Just number (assume m2)
    pattern_num = re.search(r"(\d+(?:\.\d+)?)", text)
    if pattern_num:
        value = float(pattern_num.group(1))
        # Sanity check - area should be reasonable
        if 10 <= value <= 10000:
            return value

    return None


def format_area(area_m2: float) -> str:
    """Format area to Vietnamese text."""
    if area_m2 == int(area_m2):
        return f"{int(area_m2)}m²"
    return f"{area_m2:.1f}m²"


def parse_area_range(text: str) -> tuple[Optional[float], Optional[float]]:
    """
    Parse area range from text.

    Examples:
        "50 - 100 m2" -> (50.0, 100.0)
        "từ 50m2" -> (50.0, None)
        "dưới 100m2" -> (None, 100.0)
    """
    if not text:
        return None, None

    text = text.lower().strip()
    text = text.replace(",", ".")
    text = text.replace("²", "2")

    # Pattern: X - Y m2
    range_pattern = re.search(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*m2", text)
    if range_pattern:
        return float(range_pattern.group(1)), float(range_pattern.group(2))

    # Pattern: từ X m2
    from_pattern = re.search(r"từ\s*(\d+(?:\.\d+)?)\s*m2", text)
    if from_pattern:
        return float(from_pattern.group(1)), None

    # Pattern: dưới/đến X m2
    to_pattern = re.search(r"(?:dưới|đến)\s*(\d+(?:\.\d+)?)\s*m2", text)
    if to_pattern:
        return None, float(to_pattern.group(1))

    return None, None
