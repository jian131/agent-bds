"""
Unit tests for price parser.
"""

import pytest
from parsers.price_parser import parse_vietnamese_price, format_price_vnd, parse_price_range


class TestParseVietnamesePrice:
    """Test Vietnamese price parsing."""

    def test_parse_ty(self):
        """Test parsing tỷ format."""
        assert parse_vietnamese_price("3.5 tỷ") == (3_500_000_000, "tỷ")
        assert parse_vietnamese_price("3 tỷ") == (3_000_000_000, "tỷ")
        assert parse_vietnamese_price("10 tỷ") == (10_000_000_000, "tỷ")
        assert parse_vietnamese_price("0.5 tỷ") == (500_000_000, "tỷ")

    def test_parse_ty_trieu(self):
        """Test parsing tỷ + triệu format."""
        assert parse_vietnamese_price("3 tỷ 200 triệu") == (3_200_000_000, "tỷ")
        assert parse_vietnamese_price("1 tỷ 500 triệu") == (1_500_000_000, "tỷ")
        assert parse_vietnamese_price("2 tỷ 50 triệu") == (2_050_000_000, "tỷ")

    def test_parse_trieu(self):
        """Test parsing triệu format."""
        assert parse_vietnamese_price("850 triệu") == (850_000_000, "triệu")
        assert parse_vietnamese_price("500 triệu") == (500_000_000, "triệu")
        assert parse_vietnamese_price("1.5 triệu") == (1_500_000, "triệu")

    def test_parse_trieu_per_month(self):
        """Test parsing triệu/tháng format."""
        assert parse_vietnamese_price("12 triệu/tháng") == (12_000_000, "triệu/tháng")
        assert parse_vietnamese_price("15 triệu / tháng") == (15_000_000, "triệu/tháng")

    def test_parse_vnd_format(self):
        """Test parsing VND format with dots."""
        assert parse_vietnamese_price("25.000.000 đ") == (25_000_000, "đ")
        assert parse_vietnamese_price("3.500.000.000 VNĐ") == (3_500_000_000, "đ")

    def test_negotiable(self):
        """Test negotiable/contact prices."""
        assert parse_vietnamese_price("Thỏa thuận") == (None, None)
        assert parse_vietnamese_price("Liên hệ") == (None, None)
        assert parse_vietnamese_price("Giá thương lượng") == (None, None)

    def test_empty_invalid(self):
        """Test empty and invalid inputs."""
        assert parse_vietnamese_price("") == (None, None)
        assert parse_vietnamese_price(None) == (None, None)

    def test_comma_decimal(self):
        """Test comma as decimal separator."""
        assert parse_vietnamese_price("3,5 tỷ") == (3_500_000_000, "tỷ")


class TestFormatPriceVnd:
    """Test price formatting."""

    def test_format_ty(self):
        assert format_price_vnd(3_000_000_000) == "3 tỷ"
        assert format_price_vnd(3_500_000_000) == "3.5 tỷ"

    def test_format_trieu(self):
        assert format_price_vnd(500_000_000) == "500 triệu"
        assert format_price_vnd(850_000_000) == "850 triệu"

    def test_format_small(self):
        assert format_price_vnd(500_000) == "500.000 đ"


class TestParsePriceRange:
    """Test price range parsing."""

    def test_range_ty(self):
        min_p, max_p = parse_price_range("3 - 5 tỷ")
        assert min_p == 3_000_000_000
        assert max_p == 5_000_000_000

    def test_from_price(self):
        min_p, max_p = parse_price_range("từ 2 tỷ")
        assert min_p == 2_000_000_000
        assert max_p is None

    def test_to_price(self):
        min_p, max_p = parse_price_range("dưới 3 tỷ")
        assert min_p is None
        assert max_p == 3_000_000_000
