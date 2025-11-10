"""Tests for input validators module"""
import pytest
from unittest.mock import Mock
from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError
from cli.ui.validators import StockCodeValidator, DateValidator, NumberValidator


class TestStockCodeValidator:
    """Test StockCodeValidator class"""

    def test_valid_stock_code(self):
        """Test validation of valid 6-digit stock code"""
        validator = StockCodeValidator()
        doc = Document("005930")

        # Should not raise ValidationError
        try:
            validator.validate(doc)
        except ValidationError:
            pytest.fail("Valid stock code raised ValidationError")

    def test_invalid_stock_code_not_numeric(self):
        """Test validation of non-numeric stock code"""
        validator = StockCodeValidator()
        doc = Document("ABC123")

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(doc)
        assert "6자리 숫자" in str(exc_info.value.message)

    def test_invalid_stock_code_wrong_length(self):
        """Test validation of stock code with wrong length"""
        validator = StockCodeValidator()
        doc = Document("12345")  # 5 digits

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(doc)
        assert "6자리 숫자" in str(exc_info.value.message)

    def test_empty_stock_code(self):
        """Test validation of empty stock code"""
        validator = StockCodeValidator()
        doc = Document("")

        with pytest.raises(ValidationError):
            validator.validate(doc)


class TestDateValidator:
    """Test DateValidator class"""

    def test_valid_date(self):
        """Test validation of valid date in YYYY-MM-DD format"""
        validator = DateValidator()
        doc = Document("2025-11-10")

        try:
            validator.validate(doc)
        except ValidationError:
            pytest.fail("Valid date raised ValidationError")

    def test_invalid_date_format(self):
        """Test validation of invalid date format"""
        validator = DateValidator()
        doc = Document("11/10/2025")

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(doc)
        assert "YYYY-MM-DD" in str(exc_info.value.message)

    def test_invalid_date_value(self):
        """Test validation of invalid date value"""
        validator = DateValidator()
        doc = Document("2025-13-45")  # Invalid month and day

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(doc)
        assert "YYYY-MM-DD" in str(exc_info.value.message)

    def test_empty_date(self):
        """Test validation of empty date"""
        validator = DateValidator()
        doc = Document("")

        with pytest.raises(ValidationError):
            validator.validate(doc)


class TestNumberValidator:
    """Test NumberValidator class"""

    def test_valid_number(self):
        """Test validation of valid number"""
        validator = NumberValidator(min_value=0, max_value=100)
        doc = Document("50")

        try:
            validator.validate(doc)
        except ValidationError:
            pytest.fail("Valid number raised ValidationError")

    def test_valid_float_number(self):
        """Test validation of valid float number"""
        validator = NumberValidator(min_value=0, max_value=100)
        doc = Document("50.5")

        try:
            validator.validate(doc)
        except ValidationError:
            pytest.fail("Valid float number raised ValidationError")

    def test_number_below_minimum(self):
        """Test validation of number below minimum"""
        validator = NumberValidator(min_value=10, max_value=100)
        doc = Document("5")

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(doc)
        assert "10에서 100 사이" in str(exc_info.value.message)

    def test_number_above_maximum(self):
        """Test validation of number above maximum"""
        validator = NumberValidator(min_value=0, max_value=100)
        doc = Document("150")

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(doc)
        assert "0에서 100 사이" in str(exc_info.value.message)

    def test_invalid_number_format(self):
        """Test validation of non-numeric input"""
        validator = NumberValidator(min_value=0, max_value=100)
        doc = Document("abc")

        with pytest.raises(ValidationError):
            validator.validate(doc)

    def test_default_range(self):
        """Test NumberValidator with default range (0 to infinity)"""
        validator = NumberValidator()
        doc = Document("1000000")

        try:
            validator.validate(doc)
        except ValidationError:
            pytest.fail("Valid number with default range raised ValidationError")

    def test_negative_number_when_allowed(self):
        """Test validation of negative number when allowed"""
        validator = NumberValidator(min_value=-100, max_value=100)
        doc = Document("-50")

        try:
            validator.validate(doc)
        except ValidationError:
            pytest.fail("Valid negative number raised ValidationError")
