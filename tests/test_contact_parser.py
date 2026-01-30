"""
Unit tests for contact parser.
"""

import pytest
from parsers.contact_parser import (
    parse_phone_numbers,
    parse_zalo,
    parse_facebook,
    parse_email,
    parse_contact,
)


class TestParsePhoneNumbers:
    """Test phone number parsing."""

    def test_parse_standard_format(self):
        phones = parse_phone_numbers("Liên hệ: 0912345678")
        assert "0912345678" in phones

    def test_parse_with_spaces(self):
        phones = parse_phone_numbers("SĐT: 091 234 5678")
        assert len(phones) == 1
        # Should be normalized

    def test_parse_with_dots(self):
        phones = parse_phone_numbers("Phone: 091.234.5678")
        assert len(phones) == 1

    def test_parse_84_format(self):
        phones = parse_phone_numbers("+84912345678")
        assert "0912345678" in phones

    def test_parse_multiple(self):
        phones = parse_phone_numbers("LH: 0912345678 hoặc 0987654321")
        assert len(phones) == 2

    def test_empty_invalid(self):
        assert parse_phone_numbers("") == []
        assert parse_phone_numbers(None) == []


class TestParseZalo:
    """Test Zalo parsing."""

    def test_parse_zalo_number(self):
        assert parse_zalo("Zalo: 0912345678") == "0912345678"
        assert parse_zalo("zalo 0912345678") == "0912345678"

    def test_parse_zalo_link(self):
        assert parse_zalo("zalo.me/0912345678") == "0912345678"

    def test_no_zalo(self):
        assert parse_zalo("No zalo here") is None


class TestParseFacebook:
    """Test Facebook parsing."""

    def test_parse_facebook_link(self):
        assert parse_facebook("facebook.com/username") == "https://facebook.com/username"
        assert parse_facebook("fb.com/user123") == "https://facebook.com/user123"

    def test_ignore_share_links(self):
        assert parse_facebook("facebook.com/share") is None
        assert parse_facebook("facebook.com/sharer") is None

    def test_no_facebook(self):
        assert parse_facebook("No facebook here") is None


class TestParseEmail:
    """Test email parsing."""

    def test_parse_email(self):
        assert parse_email("Contact: test@example.com") == "test@example.com"
        assert parse_email("Email: user.name@domain.vn") == "user.name@domain.vn"

    def test_no_email(self):
        assert parse_email("No email here") is None


class TestParseContact:
    """Test full contact parsing."""

    def test_parse_full_contact(self):
        text = """
        Liên hệ: Mr. Hùng
        SĐT: 0912345678
        Zalo: 0912345678
        FB: facebook.com/hungnguyen
        Email: hung@email.com
        """
        contact = parse_contact(text, "Mr. Hùng")

        assert contact["name"] == "Mr. Hùng"
        assert len(contact["phones"]) >= 1
        assert contact["zalo"] == "0912345678"
        assert contact["facebook"] == "https://facebook.com/hungnguyen"
        assert contact["email"] == "hung@email.com"
