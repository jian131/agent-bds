"""
CSS Selectors cho từng platform
Fast extraction without LLM
"""

PLATFORM_SELECTORS = {
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
                'bathrooms': '.re__card-config-bathroom::text'
            }
        },
        'detail_page': {
            'schema': {
                'title': 'h1.re__pr-title::text',
                'price': '.re__pr-short-info-item-price::text',
                'area': '.re__pr-short-info-item-area::text',
                'location': '.re__pr-short-info-item-title:contains("Địa chỉ") + .re__pr-short-info-item-value::text',
                'description': '.re__pr-short-description::text',
                'phone': '.re__pr-contact-phone::text',
                'images': '.re__pr-media-item img::attr(src)'
            }
        }
    },

    'chotot.com': {
        'list_page': {
            'items': '.AdItem_adItem__gDDQT',
            'schema': {
                'title': '.AdItem_title__kgP6F::text',
                'price': '.AdPrice_adPrice__VQKPX::text',
                'location': '.AdItem_locationText__mskOK::text',
                'url': '::attr(href)',
                'images': 'img.AdItem_image__xF4aE::attr(src)'
            }
        }
    },

    'mogi.vn': {
        'list_page': {
            'items': '.property-item',
            'schema': {
                'title': '.prop-title a::text',
                'price': '.price::text',
                'area': '.area::text',
                'location': '.location::text',
                'url': '.prop-title a::attr(href)'
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
                'url': '.ct_title a::attr(href)'
            }
        }
    }
}

def get_selectors(url: str, page_type: str = 'list_page') -> Dict:
    """Get CSS selectors for URL"""
    for platform, selectors in PLATFORM_SELECTORS.items():
        if platform in url:
            return selectors.get(page_type, {})
    return {}

def detect_platform(url: str) -> str:
    """Detect platform from URL"""
    url_lower = url.lower()

    if 'batdongsan.com' in url_lower:
        return 'batdongsan.com.vn'
    elif 'chotot.com' in url_lower:
        return 'chotot.com'
    elif 'mogi.vn' in url_lower:
        return 'mogi.vn'
    elif 'alonhadat.com' in url_lower:
        return 'alonhadat.com.vn'
    elif 'facebook.com' in url_lower:
        return 'facebook.com'
    else:
        return 'unknown'
