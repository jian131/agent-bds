"""
Vietnamese location parser.
Extract city, district, ward from address.
"""

import re
from typing import Optional, Dict, Tuple

# Vietnam cities and their aliases
CITIES = {
    "Hà Nội": ["hà nội", "ha noi", "hanoi", "hn"],
    "Hồ Chí Minh": ["hồ chí minh", "ho chi minh", "hcm", "sài gòn", "saigon", "sg", "tp hcm", "tphcm"],
    "Đà Nẵng": ["đà nẵng", "da nang", "dn"],
    "Hải Phòng": ["hải phòng", "hai phong", "hp"],
    "Cần Thơ": ["cần thơ", "can tho", "ct"],
    "Bình Dương": ["bình dương", "binh duong", "bd"],
    "Đồng Nai": ["đồng nai", "dong nai"],
    "Bắc Ninh": ["bắc ninh", "bac ninh"],
    "Hưng Yên": ["hưng yên", "hung yen"],
    "Long An": ["long an"],
    "Bà Rịa - Vũng Tàu": ["bà rịa", "vũng tàu", "vung tau", "br-vt"],
}

# Hanoi districts
HANOI_DISTRICTS = [
    "Ba Đình", "Hoàn Kiếm", "Tây Hồ", "Long Biên", "Cầu Giấy",
    "Đống Đa", "Hai Bà Trưng", "Hoàng Mai", "Thanh Xuân",
    "Nam Từ Liêm", "Bắc Từ Liêm", "Hà Đông", "Thanh Trì",
    "Gia Lâm", "Đông Anh", "Hoài Đức", "Thanh Oai", "Thường Tín",
    "Sóc Sơn", "Mê Linh", "Đan Phượng", "Quốc Oai", "Chương Mỹ",
    "Phúc Thọ", "Thạch Thất", "Ba Vì", "Phú Xuyên", "Mỹ Đức", "Ứng Hòa",
]

# HCM districts
HCM_DISTRICTS = [
    "Quận 1", "Quận 2", "Quận 3", "Quận 4", "Quận 5",
    "Quận 6", "Quận 7", "Quận 8", "Quận 9", "Quận 10",
    "Quận 11", "Quận 12", "Bình Thạnh", "Gò Vấp", "Phú Nhuận",
    "Tân Bình", "Tân Phú", "Bình Tân", "Thủ Đức",
    "Nhà Bè", "Hóc Môn", "Củ Chi", "Bình Chánh", "Cần Giờ",
]


def normalize_text(text: str) -> str:
    """Normalize Vietnamese text for matching."""
    return text.lower().strip()


def detect_city(text: str) -> Optional[str]:
    """Detect city from text."""
    text_lower = normalize_text(text)

    for city, aliases in CITIES.items():
        for alias in aliases:
            if alias in text_lower:
                return city

    # Try to detect from district
    for district in HANOI_DISTRICTS:
        if normalize_text(district) in text_lower:
            return "Hà Nội"

    for district in HCM_DISTRICTS:
        if normalize_text(district) in text_lower:
            return "Hồ Chí Minh"

    return None


def detect_district(text: str, city: Optional[str] = None) -> Optional[str]:
    """Detect district from text."""
    text_lower = normalize_text(text)

    # Check Hanoi districts
    if city is None or city == "Hà Nội":
        for district in HANOI_DISTRICTS:
            if normalize_text(district) in text_lower:
                return district

    # Check HCM districts
    if city is None or city == "Hồ Chí Minh":
        for district in HCM_DISTRICTS:
            # Handle "Q.1", "Q1", "Quận 1"
            district_lower = normalize_text(district)
            if district_lower in text_lower:
                return district

            # Match Q.X or QX patterns
            if district.startswith("Quận "):
                num = district.replace("Quận ", "")
                patterns = [f"q.{num}", f"q{num}", f"quận {num}"]
                for pattern in patterns:
                    if pattern in text_lower:
                        return district

    return None


def parse_location(address: str) -> Dict[str, Optional[str]]:
    """
    Parse Vietnamese address into components.

    Args:
        address: Full address string

    Returns:
        Dict with keys: address, ward, district, city
    """
    result = {
        "address": address,
        "ward": None,
        "district": None,
        "city": None,
    }

    if not address:
        return result

    # Detect city first
    result["city"] = detect_city(address)

    # Detect district
    result["district"] = detect_district(address, result["city"])

    # Try to extract ward (phường/xã)
    ward_pattern = re.search(
        r"(?:phường|xã|p\.)\s*([^,]+)",
        address,
        re.IGNORECASE
    )
    if ward_pattern:
        result["ward"] = ward_pattern.group(1).strip()

    return result


def format_location(district: Optional[str], city: Optional[str]) -> str:
    """Format location for display."""
    parts = []
    if district:
        parts.append(district)
    if city:
        parts.append(city)
    return ", ".join(parts) if parts else ""
