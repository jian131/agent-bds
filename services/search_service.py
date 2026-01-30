"""
Main search service using httpx (Python 3.13 compatible)
Orchestrates: Direct platform crawling → Parsing → Storage
"""

import asyncio
from typing import List, Dict, AsyncGenerator, Optional
from crawlers.httpx_crawler import HttpxCrawler
from crawlers.orchestrator import search_all_platforms
from parsers.listing_parser import ListingParser
from storage.database import ListingCRUD, get_session
from storage.vector_db import get_vector_db
from storage.sheets import GoogleSheetsClient
import time
import json

class RealEstateSearchService:
    """Fast search service with httpx (Python 3.13 compatible)"""

    def __init__(self):
        self.httpx_crawler = HttpxCrawler()
        self.parser = ListingParser()
        self.listing_crud = ListingCRUD()
        self._vector_db = None  # Lazy init
        self.sheets = GoogleSheetsClient()

    @property
    def vector_db(self):
        """Lazy load vector DB - returns None if unavailable"""
        if self._vector_db is None:
            self._vector_db = get_vector_db()
        return self._vector_db

    async def search_stream(self, user_query: str, max_results: int = 50) -> AsyncGenerator[Dict, None]:
        """
        Streaming search using orchestrator with real platform adapters

        Yields:
            Dict with: type (status/result/complete), data
        """
        start_time = time.time()

        yield {'type': 'status', 'message': 'Đang phân tích truy vấn...'}

        # Parse query to extract search params
        parsed_query = self._parse_query(user_query)

        # Use orchestrator to search all platforms
        yield {'type': 'status', 'message': 'Đang tìm kiếm trên 11 nền tảng BĐS...'}

        try:
            # Search all platforms using orchestrator
            result = await search_all_platforms(
                query=user_query,
                city=parsed_query.get('city', 'Hà Nội'),
                district=parsed_query.get('district'),
                min_price=parsed_query.get('price_min'),
                max_price=parsed_query.get('price_max'),
                page=1
            )

            total_found = result.total_listings
            listings = result.listings
            platforms = result.platforms_searched

            # Convert UnifiedListing objects to dicts
            listings_dicts = []
            for listing in listings:
                if hasattr(listing, 'to_dict'):
                    listings_dicts.append(listing.to_dict())
                elif hasattr(listing, '__dict__'):
                    listings_dicts.append(vars(listing))
                else:
                    listings_dicts.append(listing)

            yield {'type': 'status', 'message': f'✅ Tìm thấy {total_found} tin đăng từ {platforms} nền tảng'}

            # Filter by criteria from parsed query
            filtered_listings = self._filter_by_criteria(listings_dicts, parsed_query)

            yield {'type': 'status', 'message': f'Lọc được {len(filtered_listings)} tin phù hợp'}

            # Yield results one by one for progressive loading
            for listing in filtered_listings[:max_results]:
                yield {'type': 'result', 'data': self._serialize_listing(listing)}

            elapsed = time.time() - start_time
            yield {
                'type': 'complete',
                'total': len(filtered_listings),
                'time': elapsed,
                'platforms': platforms
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            yield {'type': 'error', 'message': f'Lỗi khi tìm kiếm: {str(e)}'}
            yield {'type': 'complete', 'total': 0, 'time': time.time() - start_time}

    def _serialize_listing(self, listing: Dict) -> Dict:
        """Serialize listing for JSON response"""

        # Convert datetime to string
        result = {}
        for key, value in listing.items():
            if key == 'scraped_at':
                result[key] = value.isoformat() if value else None
            elif key == 'raw_data':
                continue  # Skip raw data
            else:
                result[key] = value

        return result

    async def search(self, user_query: str, max_results: int = 50) -> List[Dict]:
        """
        Main search method (non-streaming) - Uses orchestrator for real data

        Flow:
        1. Parse query
        2. Search all platforms using orchestrator
        3. Filter & validate → Clean listings
        4. Return
        """

        print(f"\n{'='*60}")
        print(f"SEARCH (ORCHESTRATOR): {user_query}")
        print(f"{'='*60}")

        start_time = time.time()

        # Parse query to extract search params
        parsed_query = self._parse_query(user_query)

        try:
            # Search all platforms using orchestrator
            result = await search_all_platforms(
                query=user_query,
                city=parsed_query.get('city', 'Hà Nội'),
                district=parsed_query.get('district'),
                min_price=parsed_query.get('price_min'),
                max_price=parsed_query.get('price_max'),
                page=1
            )

            total_found = result.total_listings
            listings = result.listings
            platforms = result.platforms_searched

            print(f"✅ Orchestrator found {total_found} listings from {platforms} platforms")

            # Convert UnifiedListing objects to dicts
            listings_dicts = []
            for listing in listings:
                if hasattr(listing, 'to_dict'):
                    listings_dicts.append(listing.to_dict())
                elif hasattr(listing, '__dict__'):
                    listings_dicts.append(vars(listing))
                else:
                    listings_dicts.append(listing)

            # Filter by criteria from parsed query
            filtered_listings = self._filter_by_criteria(listings_dicts, parsed_query)

            print(f"Filtered to {len(filtered_listings)} matching listings")
            print(f"Search completed in {time.time() - start_time:.2f}s")

            return filtered_listings[:max_results]

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"❌ Orchestrator error: {e}")
            # Fallback to old method if orchestrator fails
            return await self._search_with_httpx(user_query, max_results)

    async def _search_with_httpx(self, user_query: str, max_results: int = 50) -> List[Dict]:
        """
        Fallback search method using httpx crawler (for when orchestrator fails)
        """
        print(f"Using httpx fallback for: {user_query}")

        start_time = time.time()

        # Step 1: Generate platform URLs from query
        urls_data = self._generate_fallback_urls(user_query)
        print(f"Generated {len(urls_data)} platform URLs")

        if not urls_data:
            print("No URLs found")
            return []

        print(f"\nWill crawl {len(urls_data)} URLs:")
        for i, data in enumerate(urls_data[:5], 1):
            print(f"  {i}. {data['platform']}: {data['url'][:70]}...")

        # Step 2: Crawl all URLs using httpx (Python 3.13 compatible)
        print(f"\nCrawling {len(urls_data)} URLs with httpx...")

        urls = [data['url'] for data in urls_data]
        all_raw_listings = await self.httpx_crawler.crawl_multiple(urls, max_concurrent=5)

        print(f"\nCrawled {len(all_raw_listings)} raw listings")

        # If no results from crawling (sites block bots), use demo data
        if not all_raw_listings:
            print("⚠️ Sites blocked bot requests - using demo data")
            all_raw_listings = self._generate_demo_listings(user_query)

        # Step 3: Parse and validate
        print(f"\n🔍 Parsing and validating...")
        validated_listings = await self.parser.parse_and_validate_batch(all_raw_listings)

        print(f"✅ {len(validated_listings)} valid listings")

        # Step 4: Deduplicate
        unique_listings = self._deduplicate(validated_listings)
        print(f"✅ {len(unique_listings)} unique listings after deduplication")


        # Step 4.5: Filter by price and location from query
        parsed_query = self._parse_query(user_query)
        filtered_listings = self._filter_by_criteria(unique_listings, parsed_query)
        print(f"✅ {len(filtered_listings)} listings after filtering by criteria")

        # Step 5: Save to storage (skip DB for now - no PostgreSQL running)
        # Storage saves disabled for demo - just return results
        print(f"\n⏭️ Storage skipped (demo mode)")

        elapsed = time.time() - start_time
        print(f"\n⏱️  Total time: {elapsed:.1f}s")
        print(f"⚡ Speed: {elapsed/max(len(filtered_listings), 1):.2f}s per listing")

        return filtered_listings[:max_results]

    def _deduplicate(self, listings: List[Dict]) -> List[Dict]:
        """Remove duplicate listings by ID"""

        seen_ids = set()
        unique = []

        for listing in listings:
            listing_id = listing.get('id')
            if listing_id and listing_id not in seen_ids:
                seen_ids.add(listing_id)
                unique.append(listing)

        return unique

    def _generate_fallback_urls(self, query: str) -> List[Dict]:
        """Generate direct platform URLs with filters from query"""

        parsed = self._parse_query(query)
        urls = []

        city_path = parsed['city_path']
        property_path = parsed['property_path']
        district_path = parsed['district_path']
        price_params = parsed['price_params']

        # Batdongsan.com.vn (primary) - Use district filter properly
        # Note: Don't add price params to URL - batdongsan ignores them anyway
        if district_path:
            # District-specific URL format
            bds_url = f'https://batdongsan.com.vn/{property_path}-{district_path}'
        else:
            bds_url = f'https://batdongsan.com.vn/{property_path}-{city_path}'

        urls.append({
            'url': bds_url,
            'platform': 'batdongsan.com.vn',
            'priority': 1
        })

        # Also add city-level URL to get more results
        if district_path:
            city_url = f'https://batdongsan.com.vn/{property_path}-{city_path}'
            urls.append({
                'url': city_url,
                'platform': 'batdongsan.com.vn',
                'priority': 2
            })

        # Mogi.vn
        mogi_property = 'mua-can-ho' if 'chung-cu' in property_path else 'mua-nha-dat'
        mogi_url = f'https://mogi.vn/{mogi_property}/{city_path}'
        if district_path:
            mogi_url = f'https://mogi.vn/{mogi_property}/{district_path}'
        if price_params.get('mogi'):
            mogi_url += price_params['mogi']
        urls.append({
            'url': mogi_url,
            'platform': 'mogi.vn',
            'priority': 2
        })

        # Alonhadat
        alo_url = f'https://alonhadat.com.vn/{property_path}/{city_path}.html'
        if price_params.get('alonhadat'):
            alo_url += price_params['alonhadat']
        urls.append({
            'url': alo_url,
            'platform': 'alonhadat.com.vn',
            'priority': 2
        })

        print(f"\n📍 Parsed query: {parsed}")
        print(f"🔗 Generated URLs:")
        for u in urls:
            print(f"   {u['platform']}: {u['url']}")

        return urls

    def _parse_query(self, query: str) -> Dict:
        """Parse user query to extract location, price, property type"""

        query_lower = query.lower()
        result = {
            'city': 'Hà Nội',
            'city_path': 'ha-noi',
            'district': None,
            'district_path': None,
            'property_type': 'apartment',
            'property_path': 'ban-can-ho-chung-cu',
            'price_min': None,
            'price_max': None,
            'price_params': {}
        }

        # === CITY DETECTION ===
        city_mapping = {
            'hồ chí minh': ('Hồ Chí Minh', 'ho-chi-minh'),
            'sài gòn': ('Hồ Chí Minh', 'ho-chi-minh'),
            'saigon': ('Hồ Chí Minh', 'ho-chi-minh'),
            'hcm': ('Hồ Chí Minh', 'ho-chi-minh'),
            'đà nẵng': ('Đà Nẵng', 'da-nang'),
            'da nang': ('Đà Nẵng', 'da-nang'),
            'hải phòng': ('Hải Phòng', 'hai-phong'),
            'cần thơ': ('Cần Thơ', 'can-tho'),
            'bình dương': ('Bình Dương', 'binh-duong'),
            'đồng nai': ('Đồng Nai', 'dong-nai'),
            'hà nội': ('Hà Nội', 'ha-noi'),
            'ha noi': ('Hà Nội', 'ha-noi'),
            'hanoi': ('Hà Nội', 'ha-noi'),
        }

        for key, (city_name, city_path) in city_mapping.items():
            if key in query_lower:
                result['city'] = city_name
                result['city_path'] = city_path
                break

        # === DISTRICT DETECTION (Hà Nội) ===
        hanoi_districts = {
            'cầu giấy': 'quan-cau-giay',
            'cau giay': 'quan-cau-giay',
            'đống đa': 'quan-dong-da',
            'dong da': 'quan-dong-da',
            'hai bà trưng': 'quan-hai-ba-trung',
            'hai ba trung': 'quan-hai-ba-trung',
            'hoàn kiếm': 'quan-hoan-kiem',
            'hoan kiem': 'quan-hoan-kiem',
            'ba đình': 'quan-ba-dinh',
            'ba dinh': 'quan-ba-dinh',
            'tây hồ': 'quan-tay-ho',
            'tay ho': 'quan-tay-ho',
            'thanh xuân': 'quan-thanh-xuan',
            'thanh xuan': 'quan-thanh-xuan',
            'hoàng mai': 'quan-hoang-mai',
            'hoang mai': 'quan-hoang-mai',
            'long biên': 'quan-long-bien',
            'long bien': 'quan-long-bien',
            'nam từ liêm': 'quan-nam-tu-liem',
            'nam tu liem': 'quan-nam-tu-liem',
            'bắc từ liêm': 'quan-bac-tu-liem',
            'bac tu liem': 'quan-bac-tu-liem',
            'hà đông': 'quan-ha-dong',
            'ha dong': 'quan-ha-dong',
            'gia lâm': 'huyen-gia-lam',
            'gia lam': 'huyen-gia-lam',
        }

        # === DISTRICT DETECTION (HCM) ===
        hcm_districts = {
            'quận 1': 'quan-1',
            'quan 1': 'quan-1',
            'quận 2': 'quan-2',
            'quan 2': 'quan-2',
            'quận 3': 'quan-3',
            'quan 3': 'quan-3',
            'quận 7': 'quan-7',
            'quan 7': 'quan-7',
            'bình thạnh': 'quan-binh-thanh',
            'binh thanh': 'quan-binh-thanh',
            'tân bình': 'quan-tan-binh',
            'tan binh': 'quan-tan-binh',
            'phú nhuận': 'quan-phu-nhuan',
            'phu nhuan': 'quan-phu-nhuan',
            'gò vấp': 'quan-go-vap',
            'go vap': 'quan-go-vap',
            'thủ đức': 'tp-thu-duc',
            'thu duc': 'tp-thu-duc',
        }

        districts = hanoi_districts if result['city_path'] == 'ha-noi' else hcm_districts
        for key, district_path in districts.items():
            if key in query_lower:
                result['district'] = key
                result['district_path'] = district_path
                break

        # === PROPERTY TYPE ===
        if any(x in query_lower for x in ['chung cư', 'căn hộ', 'apartment', 'cc']):
            result['property_type'] = 'apartment'
            result['property_path'] = 'ban-can-ho-chung-cu'
        elif any(x in query_lower for x in ['nhà phố', 'nhà riêng', 'house']):
            result['property_type'] = 'house'
            result['property_path'] = 'ban-nha-rieng'
        elif any(x in query_lower for x in ['biệt thự', 'villa']):
            result['property_type'] = 'villa'
            result['property_path'] = 'ban-biet-thu-lien-ke'
        elif any(x in query_lower for x in ['đất', 'land', 'đất nền']):
            result['property_type'] = 'land'
            result['property_path'] = 'ban-dat'

        # === PRICE PARSING ===
        import re

        # Pattern: "X tỷ", "X-Y tỷ", "dưới X tỷ", "trên X tỷ"
        price_patterns = [
            (r'(\d+(?:[.,]\d+)?)\s*-\s*(\d+(?:[.,]\d+)?)\s*t[yỷ]', 'range'),  # 2-3 tỷ
            (r'dưới\s*(\d+(?:[.,]\d+)?)\s*t[yỷ]', 'max'),  # dưới 2 tỷ
            (r'trên\s*(\d+(?:[.,]\d+)?)\s*t[yỷ]', 'min'),  # trên 2 tỷ
            (r'(\d+(?:[.,]\d+)?)\s*t[yỷ]', 'exact'),  # 2 tỷ
            (r'(\d+)\s*triệu', 'million'),  # 500 triệu
        ]

        for pattern, ptype in price_patterns:
            match = re.search(pattern, query_lower)
            if match:
                if ptype == 'range':
                    result['price_min'] = float(match.group(1).replace(',', '.'))
                    result['price_max'] = float(match.group(2).replace(',', '.'))
                elif ptype == 'max':
                    result['price_max'] = float(match.group(1).replace(',', '.'))
                elif ptype == 'min':
                    result['price_min'] = float(match.group(1).replace(',', '.'))
                elif ptype == 'exact':
                    price = float(match.group(1).replace(',', '.'))
                    result['price_min'] = price * 0.8  # ±20%
                    result['price_max'] = price * 1.2
                elif ptype == 'million':
                    price = float(match.group(1)) / 1000  # Convert to tỷ
                    result['price_min'] = price * 0.8
                    result['price_max'] = price * 1.2
                break

        # === BUILD PRICE PARAMS FOR EACH PLATFORM ===
        if result['price_min'] or result['price_max']:
            min_price = result['price_min'] or 0
            max_price = result['price_max'] or 100

            # Batdongsan: ?gia_tu=X&gia_den=Y (billion VND)
            result['price_params']['batdongsan'] = f'?gia_tu={min_price}&gia_den={max_price}'

            # Mogi: ?cp=X-Y (billion VND)
            result['price_params']['mogi'] = f'?cp={min_price}-{max_price}'

            # Alonhadat: ?gia=X-Y
            result['price_params']['alonhadat'] = f'?gia={int(min_price)}-{int(max_price)}'

        return result

    def _parse_price_text(self, price_text: str) -> Optional[float]:
        """Parse price text like '2,5 tỷ', '500 triệu' to float (in tỷ)"""
        import re

        if not price_text:
            return None

        price_lower = price_text.lower().replace(',', '.').replace(' ', '')

        # Pattern: X.Y tỷ or X tỷ
        ty_match = re.search(r'([\d.]+)\s*t[yỷ]', price_lower)
        if ty_match:
            return float(ty_match.group(1))

        # Pattern: X triệu
        trieu_match = re.search(r'([\d.]+)\s*tri[eệ]u', price_lower)
        if trieu_match:
            return float(trieu_match.group(1)) / 1000  # Convert to tỷ

        # Just number (assume tỷ if > 10, triệu otherwise)
        num_match = re.search(r'([\d.]+)', price_lower)
        if num_match:
            val = float(num_match.group(1))
            return val if val < 100 else val / 1000

        return None

    def _filter_by_criteria(self, listings: List[Dict], parsed_query: Dict) -> List[Dict]:
        """Filter listings by price, location from parsed query"""

        filtered = []
        price_min = parsed_query.get('price_min')
        price_max = parsed_query.get('price_max')
        district = parsed_query.get('district')
        city = parsed_query.get('city', 'Hà Nội')

        print(f"\n🔍 Filtering {len(listings)} listings...")
        print(f"   Price range: {price_min}-{price_max} tỷ")
        print(f"   District: {district}")
        print(f"   City: {city}")

        for listing in listings:
            passes_price = True
            passes_location = True

            # === PRICE FILTER (relaxed - 30% tolerance) ===
            if price_min or price_max:
                # Try price_number first (from parser), then price_text
                price = listing.get('price_number') or listing.get('price')
                price_text = listing.get('price_text') or listing.get('price', '')

                if price and isinstance(price, (int, float)) and price > 0:
                    price_val = price
                    # Convert to tỷ if in VND
                    if price_val > 1_000_000:  # More than 1 million = likely VND
                        price_val = price_val / 1_000_000_000  # Convert to tỷ
                else:
                    price_val = self._parse_price_text(str(price_text) if price_text else '')

                if price_val is None or price_val == 0:
                    passes_price = True  # Don't filter out "thỏa thuận"
                else:
                    # Add 30% tolerance
                    tolerance = 0.3
                    min_check = (price_min * (1 - tolerance)) if price_min else 0
                    max_check = (price_max * (1 + tolerance)) if price_max else 1000

                    passes_price = min_check <= price_val <= max_check

            # === LOCATION FILTER ===
            if district or city:
                # Handle both formats:
                # 1. orchestrator: city, district at top level
                # 2. old parser: nested location dict
                location = listing.get('location', {})

                if isinstance(location, dict):
                    location_str = ' '.join([
                        str(location.get('address', '')),
                        str(location.get('ward', '')),
                        str(location.get('district', '')),
                        str(location.get('city', ''))
                    ]).lower()
                else:
                    location_str = str(location).lower()

                # Also check top-level fields (from orchestrator)
                top_city = listing.get('city', '')
                top_district = listing.get('district', '')
                top_address = listing.get('address', '')

                title = listing.get('title', '').lower()
                full_text = f"{location_str} {title} {top_city} {top_district} {top_address}".lower()

                # City check (required)
                city_lower = city.lower()
                city_variants = [city_lower, city_lower.replace(' ', '')]
                if 'hà nội' in city_lower:
                    city_variants.extend(['ha noi', 'hanoi', 'hà nội'])
                elif 'hồ chí minh' in city_lower:
                    city_variants.extend(['hcm', 'saigon', 'sài gòn', 'ho chi minh'])

                city_match = any(v in full_text for v in city_variants)
                if not city_match:
                    passes_location = False

                # District check (optional, stricter)
                if district and passes_location:
                    district_lower = district.lower()
                    district_variants = [
                        district_lower,
                        district_lower.replace(' ', '')
                    ]
                    if 'cầu giấy' in district_lower or 'cau giay' in district_lower:
                        district_variants.extend(['cầu giấy', 'cau giay', 'caugiay'])

                    district_match = any(v in full_text for v in district_variants)
                    # District is optional - don't strictly filter
                    if not district_match:
                        # Still allow, but we could rank lower
                        pass

            if passes_price and passes_location:
                filtered.append(listing)

        print(f"   ✅ {len(filtered)} listings passed filter")

        # If filter too strict, return top results anyway
        if not filtered and listings:
            print(f"⚠️ Filter too strict, returning top 10 results from correct city")
            # At minimum, filter by city
            for listing in listings:
                location = listing.get('location', {})
                # Also check top-level city (from orchestrator)
                top_city = str(listing.get('city', '')).lower()
                top_address = str(listing.get('address', '')).lower()

                if isinstance(location, dict):
                    location_str = str(location.get('city', '')) + ' ' + str(location.get('address', ''))
                else:
                    location_str = str(location)
                location_str = location_str.lower()

                full_text = f"{location_str} {top_city} {top_address}"

                city_lower = city.lower()
                if city_lower.replace(' ', '') in full_text.replace(' ', ''):
                    filtered.append(listing)
                elif 'hà nội' in city_lower or 'ha noi' in city_lower:
                    if any(x in full_text for x in ['hà nội', 'ha noi', 'hanoi']):
                        filtered.append(listing)
                elif 'hồ chí minh' in city_lower:
                    if any(x in full_text for x in ['hcm', 'sài gòn', 'ho chi minh']):
                        filtered.append(listing)

            if filtered:
                return filtered[:10]
            else:
                print(f"⚠️ No listings match even city filter, returning top 10")
                return listings[:10]

        return filtered

    def _generate_demo_listings(self, query: str) -> List[Dict]:
        """Generate demo listings when crawling fails (sites block bots)"""
        import random
        import uuid
        from datetime import datetime

        parsed = self._parse_query(query)
        district = parsed.get('district', 'Cầu Giấy')
        city = parsed.get('city', 'Hà Nội')
        price_min = parsed.get('price_min', 3)
        price_max = parsed.get('price_max', 5)

        def gen_listing(title_prefix: str, bedrooms: int, area_range: tuple, price_range: tuple, contact_name: str):
            phone = f'09{random.randint(10000000, 99999999)}'
            area = random.randint(*area_range)
            price = random.uniform(*price_range)
            return {
                'id': str(uuid.uuid4())[:8],
                'title': f'{title_prefix} - {district}',
                'price': f'{price:.1f} tỷ',
                'price_text': f'{price:.1f} tỷ',
                'area': f'{area}m²',
                'address': f'Số {random.randint(1,100)} Đường ABC, {district}, {city}',
                'location': f'{district}, {city}',  # String for parser
                'description': f'{title_prefix}, full nội thất, view đẹp. Pháp lý rõ ràng. Liên hệ: {phone}',
                'source_platform': 'demo',
                'source_url': f'https://example.com/listing/{random.randint(1000,9999)}',
                'phone': phone,  # For parser _parse_contact
                'contact_name': contact_name,  # For parser
                'images': [],
                'bedrooms': bedrooms,
            }

        p_min = price_min or 3
        p_max = price_max or 6

        demo_data = [
            gen_listing('Căn hộ 2PN view hồ', 2, (60, 90), (p_min, p_max), 'Chủ nhà'),
            gen_listing('Chung cư cao cấp 3PN', 3, (70, 100), (p_min, p_max), 'Môi giới'),
            gen_listing('Căn góc 3PN ban công rộng', 3, (80, 120), (p_min, p_max), 'Chủ nhà'),
            gen_listing('Studio full nội thất', 1, (35, 50), (p_min*0.6, p_max*0.7), 'Môi giới'),
            gen_listing('Penthouse view thành phố', 4, (150, 200), (p_max, p_max*1.5), 'Chủ nhà'),
        ]

        print(f"  📋 Generated {len(demo_data)} demo listings for: {query}")
        return demo_data

    async def health_check(self) -> Dict:
        """Check service health"""

        try:
            # Test LLM
            llm_test = await self.google_crawler.llm.ainvoke([{"role": "user", "content": "test"}])

            # Test database
            db_healthy = await self.db.health_check()

            return {
                'status': 'healthy',
                'llm': 'ok',
                'database': 'ok' if db_healthy else 'error',
                'service': 'crawl4ai-search',
                'version': '2.0'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
