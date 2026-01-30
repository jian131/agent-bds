"""
Unit tests for area parser.
"""

import pytest
from parsers.area_parser import parse_area, format_area, parse_area_range


class TestParseArea:
    """Test area parsing."""

    def test_parse_m2(self):
        """Test standard m2 format."""
        assert parse_area("85.5 m2") == 85.5
        assert parse_area("85m2") == 85.0
        assert parse_area("100 m2") == 100.0

    def test_parse_m2_squared(self):
        """Test m² format."""
        assert parse_area("85,5m²") == 85.5
        assert parse_area("100m²") == 100.0

    def test_parse_with_label(self):
        """Test with label prefix."""
        assert parse_area("Diện tích: 100m2") == 100.0
        assert parse_area("DT: 85.5 m2") == 85.5

    def test_parse_comma_decimal(self):
        """Test comma as decimal separator."""
        assert parse_area("85,5 m2") == 85.5

    def test_empty_invalid(self):
        """Test empty and invalid inputs."""
        assert parse_area("") is None
        assert parse_area(None) is None


class TestFormatArea:
    """Test area formatting."""

    def test_format_integer(self):
        assert format_area(100.0) == "100m²"

    def test_format_decimal(self):
        assert format_area(85.5) == "85.5m²"


class TestParseAreaRange:
    """Test area range parsing."""

    def test_range(self):
        min_a, max_a = parse_area_range("50 - 100 m2")
        assert min_a == 50.0
        assert max_a == 100.0

    def test_from_area(self):
        min_a, max_a = parse_area_range("từ 50m2")
        assert min_a == 50.0
        assert max_a is None

    def test_to_area(self):
        min_a, max_a = parse_area_range("dưới 100m2")
        assert min_a is None
        assert max_a == 100.0
