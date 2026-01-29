"""
Parse and validate listings
Convert raw scraped data → clean structured format
"""

from typing import List, Dict, Optional
import re
from datetime import datetime
import hashlib
from langchain_groq import ChatGroq
from config import settings

class ListingParser:
    """Parse and validate property listings"""

    def __init__(self):
        self.llm = ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0
        )

    async def parse_and_validate_batch(self, raw_listings: List[Dict]) -> List[Dict]:
        """Parse and validate batch of listings"""

        validated = []

        for raw in raw_listings:
            try:
                parsed = await self.parse_single(raw)

                if self.validate(parsed):
                    validated.append(parsed)

            except Exception as e:
                print(f"  ⚠️ Parse error: {e}")
                continue

        return validated

    async def parse_single(self, raw: Dict) -> Dict:
        """Parse single listing to standard format"""

        listing = {
            'id': self._generate_id(raw),
            'title': raw.get('title', '').strip(),
            'price_text': raw.get('price', '').strip(),
            'price_number': self._parse_price(raw.get('price', '')),
            'area_text': raw.get('area', '').strip(),
            'area_m2': self._parse_area(raw.get('area', '')),
            'location': self._parse_location(raw),
            'contact': self._parse_contact(raw),
            'images': raw.get('images', []) if isinstance(raw.get('images'), list) else [],
            'source_url': raw.get('source_url', ''),
            'source_platform': raw.get('source_platform', 'unknown'),
            'property_type': raw.get('property_type', ''),
            'bedrooms': self._parse_number(raw.get('bedrooms')),
            'bathrooms': self._parse_number(raw.get('bathrooms')),
            'description': raw.get('description', '')[:1000],  # Limit length
            'scraped_at': datetime.now(),
            'posted_at': raw.get('posted_at'),
            'raw_data': raw
        }

        return listing

    def _parse_price(self, price_text: str) -> int:
        """Parse Vietnamese price text to number"""

        if not price_text:
            return 0

        try:
            # Remove common words
            clean = price_text.lower()
            clean = re.sub(r'[,.](?=\d{3})', '', clean)  # Remove thousand separators

            # Extract numbers
            numbers = re.findall(r'\d+(?:[.,]\d+)?', clean)

            if not numbers:
                return 0

            value = float(numbers[0].replace(',', '.'))

            # Determine multiplier
            if 'tỷ' in clean or 'ty' in clean:
                value *= 1_000_000_000
            elif 'triệu' in clean or 'trieu' in clean:
                value *= 1_000_000
            elif 'nghìn' in clean or 'nghin' in clean:
                value *= 1_000

            return int(value)

        except:
            return 0

    def _parse_area(self, area_text: str) -> float:
        """Parse area text to m2"""

        if not area_text:
            return 0.0

        try:
            # Extract number
            numbers = re.findall(r'\d+(?:[.,]\d+)?', area_text)
            if numbers:
                return float(numbers[0].replace(',', '.'))
            return 0.0
        except:
            return 0.0

    def _parse_location(self, raw: Dict) -> Dict:
        """Parse location to structured format"""

        location_text = raw.get('location', '')

        # Simple parsing - can enhance with LLM if needed
        location = {
            'address': location_text,
            'ward': '',
            'district': '',
            'city': ''  # Will be detected below
        }

        location_lower = location_text.lower()

        # Detect city first
        city_mappings = {
            'hà nội': 'Hà Nội',
            'ha noi': 'Hà Nội',
            'hanoi': 'Hà Nội',
            'hồ chí minh': 'Hồ Chí Minh',
            'hcm': 'Hồ Chí Minh',
            'sài gòn': 'Hồ Chí Minh',
            'saigon': 'Hồ Chí Minh',
            'đà nẵng': 'Đà Nẵng',
            'da nang': 'Đà Nẵng',
            'bình dương': 'Bình Dương',
            'binh duong': 'Bình Dương',
            'đồng nai': 'Đồng Nai',
            'hưng yên': 'Hưng Yên',
            'hung yen': 'Hưng Yên',
            'bắc ninh': 'Bắc Ninh',
            'hải phòng': 'Hải Phòng',
            'cần thơ': 'Cần Thơ',
        }

        for key, city in city_mappings.items():
            if key in location_lower:
                location['city'] = city
                break

        # If no city found, try to detect from district
        if not location['city']:
            # Check for HN districts
            hn_districts = ['ba đình', 'hoàn kiếm', 'tây hồ', 'long biên',
                           'cầu giấy', 'đống đa', 'hai bà trưng', 'hoàng mai',
                           'thanh xuân', 'nam từ liêm', 'bắc từ liêm', 'hà đông',
                           'gia lâm', 'đông anh', 'hoài đức']
            # Check for HCM districts
            hcm_districts = ['quận 1', 'quận 2', 'quận 3', 'quận 7', 'quận 9',
                            'bình thạnh', 'tân bình', 'phú nhuận', 'gò vấp',
                            'thủ đức', 'bình tân', 'tân phú']

            for d in hn_districts:
                if d in location_lower:
                    location['city'] = 'Hà Nội'
                    break

            if not location['city']:
                for d in hcm_districts:
                    if d in location_lower:
                        location['city'] = 'Hồ Chí Minh'
                        break

        # Extract district
        districts = [
            'ba đình', 'hoàn kiếm', 'tây hồ', 'long biên',
            'cầu giấy', 'đống đa', 'hai bà trưng', 'hoàng mai',
            'thanh xuân', 'nam từ liêm', 'bắc từ liêm', 'hà đông'
        ]

        location_lower = location_text.lower()
        for district in districts:
            if district in location_lower:
                location['district'] = district.title()
                break

        return location

    def _parse_contact(self, raw: Dict) -> Dict:
        """Enhanced contact parsing - extract phone, Zalo, Facebook, email"""

        # Get all contact text
        phone_raw = raw.get('phone', '') or raw.get('contact', '')
        description = raw.get('description', '') or ''
        content = raw.get('content', '') or ''

        combined_text = f"{phone_raw} {description} {content}"

        contact = {
            'phones': [],
            'zalo': [],
            'facebook': [],
            'email': [],
            'name': raw.get('contact_name', '') or raw.get('author', '')
        }

        # Extract phones (VN format)
        phone_patterns = [
            r'0\d{9,10}',  # 0912345678
            r'\+84\d{9,10}',  # +84912345678
            r'84\d{9,10}',  # 84912345678
        ]

        for pattern in phone_patterns:
            matches = re.findall(pattern, combined_text)
            for match in matches:
                # Normalize
                clean = re.sub(r'[^\d]', '', match)
                if clean.startswith('84') and len(clean) > 10:
                    clean = '0' + clean[2:]

                if len(clean) in [10, 11] and clean not in contact['phones']:
                    contact['phones'].append(clean)

        # Extract Zalo
        zalo_patterns = [
            r'zalo[:\s]*0\d{9,10}',
            r'z\.?a\.?l\.?o[:\s]*0\d{9,10}',
            r'số zalo[:\s]*0\d{9,10}',
        ]

        for pattern in zalo_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                # Extract number
                nums = re.findall(r'0\d{9,10}', match)
                if nums and nums[0] not in contact['zalo']:
                    contact['zalo'].append(nums[0])

        # Extract Facebook
        fb_patterns = [
            r'facebook\.com/[\w.]+',
            r'fb\.com/[\w.]+',
            r'fb\.me/[\w.]+',
            r'fb[:\s]+([\w.]+)',
            r'facebook[:\s]+([\w.]+)'
        ]

        for pattern in fb_patterns:
            matches = re.findall(pattern, combined_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                if match and match not in contact['facebook'] and len(match) > 3:
                    contact['facebook'].append(match)

        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, combined_text)
        contact['email'] = list(set(emails))

        # Primary contact (for backward compat)
        contact['phone'] = contact['phones'][0] if contact['phones'] else ''
        contact['phone_clean'] = contact['phone']

        return contact

    def _parse_number(self, value) -> int:
        """Parse number field"""

        if not value:
            return 0

        try:
            # Extract first number
            numbers = re.findall(r'\d+', str(value))
            return int(numbers[0]) if numbers else 0
        except:
            return 0

    def _generate_id(self, raw: Dict) -> str:
        """Generate unique ID"""

        url = raw.get('source_url', '')
        phone = raw.get('phone', '')
        title = raw.get('title', '')

        unique_str = f"{url}{phone}{title}"
        return hashlib.md5(unique_str.encode()).hexdigest()

    def validate(self, listing: Dict) -> bool:
        """Validate listing data"""

        # Required fields
        if not listing.get('title'):
            return False

        if not listing.get('source_url'):
            return False

        # Validate phone
        phone_clean = listing.get('contact', {}).get('phone_clean', '')
        if phone_clean and len(phone_clean) not in [10, 11]:
            listing['contact']['phone_clean'] = ''  # Clear invalid phone

        # Validate price range (Hà Nội: 500tr - 100 tỷ)
        price = listing.get('price_number', 0)
        if price > 0 and (price < 500_000_000 or price > 100_000_000_000):
            # Don't reject, just warn
            pass

        # Validate area
        area = listing.get('area_m2', 0)
        if area > 0 and (area < 10 or area > 10000):
            # Don't reject, just warn
            pass

        return True
