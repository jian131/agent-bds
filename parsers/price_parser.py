"""
Vietnamese price parser.
Handles various Vietnamese price formats.
"""

import re
from typing import Optional, Tuple
from decimal import Decimal


def parse_vietnamese_price(price_text: str) -> Tuple[Optional[int], Optional[str]]:
    """
    Parse Vietnamese price text to number in VND.

    Examples:
        "3.5 tỷ" -> (3_500_000_000, "tỷ")
        "3 tỷ 200 triệu" -> (3_200_000_000, "tỷ")
        "850 triệu" -> (850_000_000, "triệu")
        "12 triệu/tháng" -> (12_000_000, "triệu/tháng")
        "25.000.000 đ" -> (25_000_000, "đ")
        "Thỏa thuận" -> (None, None)

    Returns:
        Tuple of (price_number, price_unit)
    """
    if not price_text:
        return None, None

    # Normalize text
    text = price_text.lower().strip()
    text = text.replace(",", ".")

    # Check for negotiable/contact prices
    if any(kw in text for kw in ["thỏa thuận", "thoả thuận", "liên hệ", "thương lượng"]):
        return None, None

    # Pattern: X tỷ Y triệu (e.g., "3 tỷ 200 triệu")
    pattern_ty_trieu = re.search(r"(\d+(?:\.\d+)?)\s*tỷ\s*(\d+(?:\.\d+)?)\s*triệu", text)
    if pattern_ty_trieu:
        ty = float(pattern_ty_trieu.group(1))
        trieu = float(pattern_ty_trieu.group(2))
        return int((ty * 1_000_000_000) + (trieu * 1_000_000)), "tỷ"

    # Pattern: X.Y tỷ or X tỷ (e.g., "3.5 tỷ", "3 tỷ")
    pattern_ty = re.search(r"(\d+(?:\.\d+)?)\s*tỷ", text)
    if pattern_ty:
        ty = float(pattern_ty.group(1))
        return int(ty * 1_000_000_000), "tỷ"

    # Pattern: X triệu/tháng (e.g., "12 triệu/tháng")
    pattern_trieu_thang = re.search(r"(\d+(?:\.\d+)?)\s*triệu\s*/\s*tháng", text)
    if pattern_trieu_thang:
        trieu = float(pattern_trieu_thang.group(1))
        return int(trieu * 1_000_000), "triệu/tháng"

    # Pattern: X triệu (e.g., "850 triệu")
    pattern_trieu = re.search(r"(\d+(?:\.\d+)?)\s*triệu", text)
    if pattern_trieu:
        trieu = float(pattern_trieu.group(1))
        return int(trieu * 1_000_000), "triệu"

    # Pattern: X.XXX.XXX đ or X.XXX.XXX VNĐ (e.g., "25.000.000 đ")
    pattern_vnd = re.search(r"(\d{1,3}(?:\.\d{3})+)\s*(?:đ|vnđ|vnd|₫)", text)
    if pattern_vnd:
        num_str = pattern_vnd.group(1).replace(".", "")
        return int(num_str), "đ"

    # Pattern: Plain number with thousand separators (e.g., "3,500,000,000")
    pattern_plain = re.search(r"(\d{1,3}(?:[,\.]\d{3})+)", text)
    if pattern_plain:
        num_str = pattern_plain.group(1).replace(",", "").replace(".", "")
        return int(num_str), None

    # Pattern: Simple number (e.g., "3500000000")
    pattern_simple = re.search(r"(\d{7,})", text)
    if pattern_simple:
        return int(pattern_simple.group(1)), None

    return None, None


def format_price_vnd(price: int) -> str:
    """Format price number to Vietnamese text."""
    if price >= 1_000_000_000:
        ty = price / 1_000_000_000
        if ty == int(ty):
            return f"{int(ty)} tỷ"
        return f"{ty:.1f} tỷ"
    elif price >= 1_000_000:
        trieu = price / 1_000_000
        if trieu == int(trieu):
            return f"{int(trieu)} triệu"
        return f"{trieu:.1f} triệu"
    else:
        return f"{price:,} đ".replace(",", ".")


def parse_price_range(text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Parse price range from text.

    Examples:
        "3 - 5 tỷ" -> (3_000_000_000, 5_000_000_000)
        "từ 2 tỷ" -> (2_000_000_000, None)
        "dưới 3 tỷ" -> (None, 3_000_000_000)
    """
    if not text:
        return None, None

    text = text.lower().strip()

    # Pattern: X - Y tỷ/triệu
    range_pattern = re.search(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\s*(tỷ|triệu)", text)
    if range_pattern:
        low = float(range_pattern.group(1))
        high = float(range_pattern.group(2))
        unit = range_pattern.group(3)
        multiplier = 1_000_000_000 if unit == "tỷ" else 1_000_000
        return int(low * multiplier), int(high * multiplier)

    # Pattern: từ X tỷ/triệu
    from_pattern = re.search(r"từ\s*(\d+(?:\.\d+)?)\s*(tỷ|triệu)", text)
    if from_pattern:
        value = float(from_pattern.group(1))
        unit = from_pattern.group(2)
        multiplier = 1_000_000_000 if unit == "tỷ" else 1_000_000
        return int(value * multiplier), None

    # Pattern: dưới/đến X tỷ/triệu
    to_pattern = re.search(r"(?:dưới|đến)\s*(\d+(?:\.\d+)?)\s*(tỷ|triệu)", text)
    if to_pattern:
        value = float(to_pattern.group(1))
        unit = to_pattern.group(2)
        multiplier = 1_000_000_000 if unit == "tỷ" else 1_000_000
        return None, int(value * multiplier)

    return None, None
