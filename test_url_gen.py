"""Test URL generation"""
import sys
sys.path.insert(0, '.')

from services.search_service import RealEstateSearchService

service = RealEstateSearchService()

queries = [
    "chung cu 2 ty cau giay",
    "chung cu 2 ty cau giay ha noi",
    "nha rieng 3 ty quan 7 hcm",
    "can ho 1.5 ty da nang",
    "dat nen duoi 1 ty binh duong"
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print('='*60)

    parsed = service._parse_query(query)
    print(f"Parsed: {parsed}")

    urls = service._generate_fallback_urls(query)
    print(f"\nURLs:")
    for u in urls:
        print(f"  {u['url']}")
