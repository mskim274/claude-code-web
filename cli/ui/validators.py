"""Input validators for CLI prompts"""
from prompt_toolkit.validation import Validator, ValidationError
from datetime import datetime


class StockCodeValidator(Validator):
    """Validator for 6-digit stock codes"""

    def validate(self, document):
        """
        Validate stock code format.

        Args:
            document: Document from prompt_toolkit

        Raises:
            ValidationError: If stock code is invalid
        """
        text = document.text

        if not text:
            raise ValidationError(
                message="종목코드를 입력해주세요",
                cursor_position=len(text)
            )

        if not text.isdigit() or len(text) != 6:
            raise ValidationError(
                message="종목코드는 6자리 숫자여야 합니다",
                cursor_position=len(text)
            )


class DateValidator(Validator):
    """Validator for date in YYYY-MM-DD format"""

    def validate(self, document):
        """
        Validate date format.

        Args:
            document: Document from prompt_toolkit

        Raises:
            ValidationError: If date format is invalid
        """
        text = document.text

        if not text:
            raise ValidationError(
                message="날짜를 입력해주세요",
                cursor_position=len(text)
            )

        try:
            datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            raise ValidationError(
                message="날짜 형식은 YYYY-MM-DD 여야 합니다",
                cursor_position=len(text)
            )


class NumberValidator(Validator):
    """Validator for numeric input with range constraints"""

    def __init__(self, min_value: float = 0, max_value: float = float('inf')):
        """
        Initialize number validator.

        Args:
            min_value: Minimum allowed value
            max_value: Maximum allowed value
        """
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, document):
        """
        Validate numeric input.

        Args:
            document: Document from prompt_toolkit

        Raises:
            ValidationError: If number is invalid or out of range
        """
        text = document.text

        if not text:
            raise ValidationError(
                message="숫자를 입력해주세요",
                cursor_position=len(text)
            )

        try:
            value = float(text)
            if not (self.min_value <= value <= self.max_value):
                raise ValueError()
        except ValueError:
            if self.max_value == float('inf'):
                message = f"숫자는 {self.min_value} 이상이어야 합니다"
            else:
                message = f"숫자는 {self.min_value}에서 {self.max_value} 사이여야 합니다"

            raise ValidationError(
                message=message,
                cursor_position=len(text)
            )
