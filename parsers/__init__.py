"""
Parsers package - Parse and validate scraped data

Provides Vietnamese-specific parsing for:
- Prices (tỷ, triệu, ngàn)
- Areas (m², m2)
- Locations (cities, districts)
- Contact info (phone, zalo, facebook, email)
"""

# Import lightweight parsers (no external dependencies)
from parsers.price_parser import parse_vietnamese_price, format_price_vnd, parse_price_range
from parsers.area_parser import parse_area, format_area, parse_area_range
from parsers.location_parser import parse_location, detect_city, detect_district
from parsers.contact_parser import (
    parse_phone_numbers,
    parse_contact,
    parse_zalo,
    parse_facebook,
    parse_email,
)

# Lazy import for ListingParser (requires langchain_groq)
def get_listing_parser():
    """Get ListingParser instance (lazy load to avoid import errors in tests)."""
    from parsers.listing_parser import ListingParser
    return ListingParser

__all__ = [
    # Price parsing
    'parse_vietnamese_price',
    'format_price_vnd',
    'parse_price_range',
    # Area parsing
    'parse_area',
    'format_area',
    'parse_area_range',
    # Location parsing
    'parse_location',
    'detect_city',
    'detect_district',
    # Contact parsing
    'parse_phone_numbers',
    'parse_contact',
    'parse_zalo',
    'parse_facebook',
    'parse_email',
    # Listing parser (lazy)
    'get_listing_parser',
]
