"""Test CLI formatter utilities"""
import pytest
from datetime import date, datetime
from rich.text import Text
from cli.ui.formatter import (
    format_number,
    format_percent,
    format_date,
    format_datetime,
    colorize_status,
    format_currency,
)


class TestNumberFormatting:
    """Test number formatting"""

    def test_format_integer(self):
        """Test format integer with thousands separator"""
        assert format_number(1000) == "1,000"
        assert format_number(1000000) == "1,000,000"
        assert format_number(123456789) == "123,456,789"

    def test_format_float(self):
        """Test format float with decimals"""
        assert format_number(1234.5678, decimals=2) == "1,234.57"
        assert format_number(1000.0, decimals=2) == "1,000.00"
        assert format_number(999.999, decimals=1) == "1,000.0"

    def test_format_negative_number(self):
        """Test format negative numbers"""
        assert format_number(-1000) == "-1,000"
        assert format_number(-1234.56, decimals=2) == "-1,234.56"


class TestPercentFormatting:
    """Test percentage formatting"""

    def test_format_percent_basic(self):
        """Test format decimal as percentage"""
        assert format_percent(0.125) == "12.50%"
        assert format_percent(0.5) == "50.00%"
        assert format_percent(1.0) == "100.00%"

    def test_format_percent_decimals(self):
        """Test format percent with different decimal places"""
        assert format_percent(0.12345, decimals=1) == "12.3%"
        assert format_percent(0.12345, decimals=3) == "12.345%"

    def test_format_negative_percent(self):
        """Test format negative percentage"""
        assert format_percent(-0.05) == "-5.00%"
        assert format_percent(-0.125, decimals=1) == "-12.5%"


class TestDateFormatting:
    """Test date formatting"""

    def test_format_date_default(self):
        """Test format date with default format"""
        d = date(2024, 1, 15)
        assert format_date(d) == "2024-01-15"

    def test_format_date_custom(self):
        """Test format date with custom format"""
        d = date(2024, 1, 15)
        assert format_date(d, fmt="%Y/%m/%d") == "2024/01/15"
        assert format_date(d, fmt="%d-%m-%Y") == "15-01-2024"

    def test_format_datetime_default(self):
        """Test format datetime with default format"""
        dt = datetime(2024, 1, 15, 10, 30, 45)
        result = format_datetime(dt)
        assert "2024-01-15" in result
        assert "10:30" in result


class TestColorizeStatus:
    """Test status colorization"""

    def test_colorize_success(self):
        """Test colorize success message"""
        result = colorize_status("success", "Operation completed")
        assert isinstance(result, Text)
        assert "Operation completed" in str(result)

    def test_colorize_error(self):
        """Test colorize error message"""
        result = colorize_status("error", "Operation failed")
        assert isinstance(result, Text)
        assert "Operation failed" in str(result)

    def test_colorize_warning(self):
        """Test colorize warning message"""
        result = colorize_status("warning", "Be careful")
        assert isinstance(result, Text)
        assert "Be careful" in str(result)

    def test_colorize_info(self):
        """Test colorize info message"""
        result = colorize_status("info", "Just FYI")
        assert isinstance(result, Text)
        assert "Just FYI" in str(result)


class TestCurrencyFormatting:
    """Test currency formatting"""

    def test_format_currency_krw(self):
        """Test format Korean Won"""
        assert format_currency(1000000, currency="KRW") == "₩1,000,000"
        assert format_currency(50000, currency="KRW") == "₩50,000"

    def test_format_currency_usd(self):
        """Test format US Dollar"""
        assert format_currency(1234.56, currency="USD") == "$1,234.56"
        assert format_currency(1000, currency="USD") == "$1,000.00"
