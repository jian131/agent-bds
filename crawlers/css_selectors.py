"""
Expanded CSS Selectors - 10+ platforms
Full contact extraction support
"""

from typing import Dict, Optional
from urllib.parse import urlparse

PLATFORM_SELECTORS = {
    # ===== MAJOR PLATFORMS =====

    'batdongsan.com.vn': {
        'list_page': {
            'items': '.js__product-link-for-product-id',
            'schema': {
                'title': '.re__card-title::text',
                'price': '.re__card-config-price::text',
                'area': '.re__card-config-area::text',
                'location': '.re__card-location::text',
                'url': '::attr(href)',
                'bedrooms': '.re__card-config-bedroom::text',
                'bathrooms': '.re__card-config-bathroom::text',
                'images': '.re__card-image img::attr(src)'
            }
        },
        'detail_page': {
            'schema': {
                'title': 'h1.re__pr-title::text',
                'price': '.re__pr-short-info-item--price .re__pr-short-info-item-value::text',
                'area': '.re__pr-short-info-item--acreage .re__pr-short-info-item-value::text',
                'location': '.re__pr-short-info-item--location .re__pr-short-info-item-value::text',
                'description': '.re__detail-content::text',
                'phone': '.re__contact-button::attr(data-phone)',
                'contact_name': '.re__contact-name::text',
                'bedrooms': '.re__pr-short-info-item--bedroom .re__pr-short-info-item-value::text',
                'bathrooms': '.re__pr-short-info-item--bathroom .re__pr-short-info-item-value::text',
                'legal_status': '.re__pr-specs-content-item--legal .re__pr-specs-content-item-value::text',
                'direction': '.re__pr-specs-content-item--direction .re__pr-specs-content-item-value::text',
                'images': '.re__pr-photos-image img::attr(src)'
            }
        }
    },

    'chotot.com': {
        'list_page': {
            'items': '[class*="AdItem"]',
            'schema': {
                'title': '[class*="AdTitle"], [class*="title"]::text',
                'price': '[class*="AdPrice"], [class*="price"]::text',
                'location': '[class*="LocationText"], [class*="location"]::text',
                'area': '[class*="Area"]::text',
                'url': 'a::attr(href)',
                'images': 'img::attr(src)'
            }
        },
        'detail_page': {
            'schema': {
                'title': 'h1[class*="AdTitle"]::text',
                'price': '[class*="PriceValue"]::text',
                'location': '[class*="AddressPath"]::text',
                'description': '[class*="Description"]::text',
                'area': '[class*="ParameterValue"]:contains("Diện tích")::text',
                'phone': 'button[class*="PhoneButton"]::attr(data-phone)',
                'contact_name': '[class*="SellerName"]::text',
                'images': '[class*="Gallery"] img::attr(src)'
            }
        }
    },

    'mogi.vn': {
        'list_page': {
            'items': '.props .prop-item, .property-item',
            'schema': {
                'title': '.prop-title a::text',
                'price': '.price::text',
                'area': '.area::text',
                'location': '.location::text',
                'url': '.prop-title a::attr(href)',
                'images': '.image img::attr(src)'
            }
        },
        'detail_page': {
            'schema': {
                'title': 'h1.title::text',
                'price': '.price-value::text',
                'area': '.info-row:contains("Diện tích") .info-value::text',
                'location': '.info-address::text',
                'description': '.description::text',
                'phone': '.contact-phone::text',
                'contact_name': '.contact-name::text',
                'bedrooms': '.info-row:contains("Phòng ngủ") .info-value::text',
                'images': '.gallery-item img::attr(src)'
            }
        }
    },

    'alonhadat.com.vn': {
        'list_page': {
            'items': '.content-item',
            'schema': {
                'title': '.ct_title a::text',
                'price': '.ct_price::text',
                'area': '.ct_dt::text',
                'location': '.ct_dis::text',
                'url': '.ct_title a::attr(href)',
                'images': '.thumbnail img::attr(src)'
            }
        },
        'detail_page': {
            'schema': {
                'title': 'h1.title::text',
                'price': '.price::text',
                'area': '.table-detail tr:contains("Diện tích") td::text',
                'location': '.address::text',
                'description': '.comment::text',
                'phone': '.fone::text',
                'contact_name': '.name::text',
                'images': '.slider img::attr(src)'
            }
        }
    },

    # ===== ADDITIONAL PLATFORMS =====

    'nhadat247.com.vn': {
        'list_page': {
            'items': '.product-item, .item-list',
            'schema': {
                'title': '.p-title a::text, .title a::text',
                'price': '.p-price::text, .price::text',
                'area': '.p-area::text, .area::text',
                'location': '.p-address::text, .address::text',
                'url': '.p-title a::attr(href), .title a::attr(href)',
                'images': 'img::attr(src)'
            }
        },
        'detail_page': {
            'schema': {
                'title': 'h1::text',
                'price': '.product-price::text',
                'area': '.product-area::text',
                'location': '.product-address::text',
                'description': '.product-description::text',
                'phone': '.contact-phone::text',
                'contact_name': '.contact-name::text'
            }
        }
    },

    'muaban.net': {
        'list_page': {
            'items': '.item-listing, .listing-item',
            'schema': {
                'title': '.item-title::text, .title::text',
                'price': '.item-price::text, .price::text',
                'location': '.item-location::text, .location::text',
                'url': '.item-title a::attr(href), a::attr(href)',
                'images': 'img::attr(src)'
            }
        },
        'detail_page': {
            'schema': {
                'title': 'h1::text',
                'price': '.detail-price::text',
                'location': '.detail-location::text',
                'description': '.detail-content::text',
                'phone': '.seller-phone::text',
                'contact_name': '.seller-name::text'
            }
        }
    },

    'dothi.net': {
        'list_page': {
            'items': '.list-item, .property-item',
            'schema': {
                'title': '.title a::text',
                'price': '.price::text',
                'area': '.area::text',
                'location': '.location::text',
                'url': '.title a::attr(href)',
                'images': 'img::attr(src)'
            }
        }
    },

    'homedy.com': {
        'list_page': {
            'items': '.product-item, .listing-card',
            'schema': {
                'title': '.title::text',
                'price': '.price::text',
                'area': '.acreage::text',
                'location': '.address::text',
                'url': 'a::attr(href)',
                'images': 'img::attr(src)'
            }
        }
    },

    'nhatot.com': {
        'list_page': {
            'items': '[data-ad-id], .AdItem',
            'schema': {
                'title': '.AdTitle::text, [class*="title"]::text',
                'price': '.AdPrice::text, [class*="price"]::text',
                'location': '.LocationText::text, [class*="location"]::text',
                'url': 'a::attr(href)',
                'images': 'img::attr(src)'
            }
        }
    },

    'propzy.vn': {
        'list_page': {
            'items': '.property-card, .listing-item',
            'schema': {
                'title': '.card-title::text',
                'price': '.card-price::text',
                'area': '.card-area::text',
                'location': '.card-location::text',
                'url': 'a::attr(href)',
                'images': 'img::attr(src)'
            }
        }
    },

    'bds123.vn': {
        'list_page': {
            'items': '.vip-item, .normal-item',
            'schema': {
                'title': '.title a::text',
                'price': '.price::text',
                'area': '.area::text',
                'location': '.location::text',
                'url': '.title a::attr(href)'
            }
        }
    },

    'tinbatdongsan.com': {
        'list_page': {
            'items': '.item, .listing',
            'schema': {
                'title': '.title::text',
                'price': '.price::text',
                'area': '.area::text',
                'location': '.address::text',
                'url': 'a::attr(href)'
            }
        }
    },

    # ===== FACEBOOK =====

    'facebook.com': {
        'group_page': {
            'items': '[role="article"]',
            'schema': {
                'content': '[data-ad-preview="message"]::text',
                'author': 'strong a::text',
                'url': '[href*="/posts/"], [href*="/permalink/"]::attr(href)',
                'images': 'img[src*="fbcdn"]::attr(src)',
                'timestamp': '[href*="/posts/"] abbr::attr(title)'
            }
        },
        'marketplace': {
            'items': '[data-testid="marketplace-card"], [class*="marketplace"]',
            'schema': {
                'title': 'span[dir="auto"]::text',
                'price': '[aria-label*="₫"]::text, [class*="price"]::text',
                'location': 'span:contains("Vị trí")::text',
                'url': 'a::attr(href)',
                'images': 'img::attr(src)'
            }
        }
    }
}

# Platform detection
def detect_platform(url: str) -> str:
    """Enhanced platform detection"""
    url_lower = url.lower()

    platforms = {
        'batdongsan.com': 'batdongsan.com.vn',
        'chotot.com': 'chotot.com',
        'mogi.vn': 'mogi.vn',
        'alonhadat.com': 'alonhadat.com.vn',
        'nhadat247.com': 'nhadat247.com.vn',
        'muaban.net': 'muaban.net',
        'dothi.net': 'dothi.net',
        'homedy.com': 'homedy.com',
        'nhatot.com': 'nhatot.com',
        'propzy.vn': 'propzy.vn',
        'bds123.vn': 'bds123.vn',
        'tinbatdongsan.com': 'tinbatdongsan.com',
        'facebook.com': 'facebook.com',
    }

    for key, value in platforms.items():
        if key in url_lower:
            return value

    return 'unknown'

def get_selectors(url: str, page_type: str = 'list_page') -> Dict:
    """Get selectors for URL"""
    platform = detect_platform(url)
    return PLATFORM_SELECTORS.get(platform, {}).get(page_type, {})

def get_all_platforms() -> list:
    """Get list of all supported platforms"""
    return list(PLATFORM_SELECTORS.keys())

def get_platform_info(platform: str) -> Dict:
    """Get detailed info about a platform"""
    selectors = PLATFORM_SELECTORS.get(platform, {})
    return {
        'name': platform,
        'has_list_page': 'list_page' in selectors,
        'has_detail_page': 'detail_page' in selectors,
        'has_group_page': 'group_page' in selectors,
        'has_marketplace': 'marketplace' in selectors,
    }
