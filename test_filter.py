# -*- coding: utf-8 -*-
"""Debug filter logic"""
import asyncio
import sys
sys.path.insert(0, '.')

from services.search_service import RealEstateSearchService

# Simulate listings from the search - WITH DICT LOCATION (like real data)
test_listings = [
    {
        'title': 'Quỹ 1N-2N-3N MIK giá rẻ nhất thị trường',
        'price': '2,59 tỷ',
        'price_text': '2,59 tỷ',
        'location': {'address': '·Văn Giang, Hưng Yên', 'district': '', 'city': ''}
    },
    {
        'title': 'PICITY SKYPARK ƯU ĐÃI GIÁ TỐT',
        'price': '3,67 tỷ',
        'price_text': '3,67 tỷ',
        'location': {'address': '·Dĩ An, Bình Dương', 'district': '', 'city': ''}
    },
    {
        'title': 'CIPUTRA TÂY HỒ',
        'price': '28 tỷ',
        'price_text': '28 tỷ',
        'location': {'address': '·Tây Hồ, Hà Nội', 'district': 'Tây Hồ', 'city': 'Hà Nội'}
    },
    {
        'title': 'Căn hộ Thanh Xuân 2PN',
        'price': '2,8 tỷ',
        'price_text': '2,8 tỷ',
        'location': {'address': '·Thanh Xuân, Hà Nội', 'district': 'Thanh Xuân', 'city': 'Hà Nội'}
    },
    {
        'title': 'Chung cư quận 9',
        'price': '2,9 tỷ',
        'price_text': '2,9 tỷ',
        'location': {'address': '·Quận 9, Hồ Chí Minh', 'district': 'Quận 9', 'city': 'Hồ Chí Minh'}
    },
    {
        'title': 'Chung cư Thanh Xuân giá rẻ',
        'price': '3,2 tỷ',
        'price_text': '3,2 tỷ',
        'location': {'address': '·Thanh Xuân, Hà Nội', 'district': 'Thanh Xuân', 'city': 'Hà Nội'}
    },
]

service = RealEstateSearchService()

# Test parsing
parsed = service._parse_query("chung cu 3 ty thanh xuan ha noi")
print(f"Parsed query: {parsed}")

# Test price parsing
for listing in test_listings:
    price_text = listing.get('price_text', '')
    price_val = service._parse_price_text(price_text)
    print(f"  '{price_text}' -> {price_val}")

# Test filter
print("\n--- Testing filter ---")
filtered = service._filter_by_criteria(test_listings, parsed)
print(f"\nFiltered results: {len(filtered)}")
for l in filtered:
    print(f"  - {l['title'][:40]} | {l['price_text']} | {l['location']}")
