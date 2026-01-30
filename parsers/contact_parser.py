"""
Contact information parser.
Extract phone numbers, Zalo, Facebook, email.
"""

import re
from typing import List, Optional, Dict
import phonenumbers
from phonenumbers import NumberParseException


def parse_phone_numbers(text: str) -> List[str]:
    """
    Extract and normalize Vietnamese phone numbers from text.

    Args:
        text: Text containing phone numbers

    Returns:
        List of normalized phone numbers (10-11 digits starting with 0)
    """
    if not text:
        return []

    phones = set()

    # Pattern 1: Vietnamese format 0XXX XXX XXX or 0XXXXXXXXX
    pattern1 = re.findall(r"0\d{2,3}[\s.-]?\d{3}[\s.-]?\d{3,4}", text)
    for match in pattern1:
        clean = re.sub(r"[\s.-]", "", match)
        if len(clean) in [10, 11] and clean.startswith("0"):
            phones.add(clean)

    # Pattern 2: +84 or 84 format
    pattern2 = re.findall(r"(?:\+84|84)\d{9,10}", text)
    for match in pattern2:
        clean = re.sub(r"[^\d]", "", match)
        if clean.startswith("84"):
            clean = "0" + clean[2:]
        if len(clean) in [10, 11]:
            phones.add(clean)

    # Pattern 3: Just 10-11 consecutive digits
    pattern3 = re.findall(r"\d{10,11}", text)
    for match in pattern3:
        if match.startswith("0") and len(match) in [10, 11]:
            phones.add(match)

    # Validate using phonenumbers library
    validated = []
    for phone in phones:
        try:
            parsed = phonenumbers.parse(phone, "VN")
            if phonenumbers.is_valid_number(parsed):
                # Format to national format without spaces
                formatted = phonenumbers.format_number(
                    parsed,
                    phonenumbers.PhoneNumberFormat.NATIONAL
                ).replace(" ", "")
                validated.append(formatted)
        except NumberParseException:
            # Still add if looks like valid VN number
            if len(phone) in [10, 11] and phone.startswith("0"):
                validated.append(phone)

    return list(set(validated))


def parse_zalo(text: str) -> Optional[str]:
    """Extract Zalo number or link from text."""
    if not text:
        return None

    text_lower = text.lower()

    # Pattern: zalo: 0XXXXXXXXX or zalo 0XXXXXXXXX
    zalo_pattern = re.search(
        r"zalo[:\s]+0\d{9,10}",
        text_lower
    )
    if zalo_pattern:
        phones = parse_phone_numbers(zalo_pattern.group())
        if phones:
            return phones[0]

    # Pattern: zalo.me/XXXXXXXXXX
    zalo_link = re.search(r"zalo\.me/(\d+)", text_lower)
    if zalo_link:
        return zalo_link.group(1)

    return None


def parse_facebook(text: str) -> Optional[str]:
    """Extract Facebook link from text."""
    if not text:
        return None

    # Patterns for Facebook links
    patterns = [
        r"facebook\.com/([\w.]+)",
        r"fb\.com/([\w.]+)",
        r"fb\.me/([\w.]+)",
        r"m\.facebook\.com/([\w.]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            username = match.group(1)
            if username not in ["share", "sharer", "dialog", "plugins"]:
                return f"https://facebook.com/{username}"

    return None


def parse_email(text: str) -> Optional[str]:
    """Extract email address from text."""
    if not text:
        return None

    pattern = re.search(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        text
    )
    if pattern:
        return pattern.group().lower()

    return None


def parse_contact(text: str, contact_name: str = None) -> Dict:
    """
    Parse all contact information from text.

    Returns:
        Dict with keys: name, phones, zalo, facebook, email
    """
    return {
        "name": contact_name,
        "phones": parse_phone_numbers(text),
        "zalo": parse_zalo(text),
        "facebook": parse_facebook(text),
        "email": parse_email(text),
    }
