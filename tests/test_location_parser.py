"""
Unit tests for location parser.
"""

import pytest
from parsers.location_parser import detect_city, detect_district, parse_location


class TestDetectCity:
    """Test city detection."""

    def test_detect_hanoi(self):
        assert detect_city("Cầu Giấy, Hà Nội") == "Hà Nội"
        assert detect_city("123 Đường ABC, HN") == "Hà Nội"
        assert detect_city("Hanoi Vietnam") == "Hà Nội"

    def test_detect_hcm(self):
        assert detect_city("Quận 1, Hồ Chí Minh") == "Hồ Chí Minh"
        assert detect_city("HCM City") == "Hồ Chí Minh"
        assert detect_city("Sài Gòn") == "Hồ Chí Minh"
        assert detect_city("TP HCM") == "Hồ Chí Minh"

    def test_detect_from_district(self):
        """Test detecting city from district name."""
        assert detect_city("Cầu Giấy") == "Hà Nội"
        assert detect_city("Bình Thạnh") == "Hồ Chí Minh"

    def test_no_city(self):
        assert detect_city("Unknown location") is None
        assert detect_city("") is None


class TestDetectDistrict:
    """Test district detection."""

    def test_detect_hanoi_districts(self):
        assert detect_district("Cầu Giấy, Hà Nội") == "Cầu Giấy"
        assert detect_district("Đống Đa") == "Đống Đa"
        assert detect_district("Hai Bà Trưng") == "Hai Bà Trưng"

    def test_detect_hcm_districts(self):
        assert detect_district("Quận 1, HCM") == "Quận 1"
        assert detect_district("Q.7") == "Quận 7"
        assert detect_district("Q7, Sài Gòn") == "Quận 7"
        assert detect_district("Bình Thạnh") == "Bình Thạnh"

    def test_no_district(self):
        assert detect_district("Unknown") is None


class TestParseLocation:
    """Test full location parsing."""

    def test_parse_full_address(self):
        result = parse_location("123 Đường ABC, Phường XYZ, Cầu Giấy, Hà Nội")
        assert result["city"] == "Hà Nội"
        assert result["district"] == "Cầu Giấy"
        assert result["address"] == "123 Đường ABC, Phường XYZ, Cầu Giấy, Hà Nội"

    def test_parse_hcm_address(self):
        result = parse_location("Quận 7, Hồ Chí Minh")
        assert result["city"] == "Hồ Chí Minh"
        assert result["district"] == "Quận 7"

    def test_parse_empty(self):
        result = parse_location("")
        assert result["city"] is None
        assert result["district"] is None
