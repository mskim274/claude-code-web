"""Tests for interactive menu module"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from cli.ui.menu import InteractiveMenu, MenuOption, MenuResult


class TestMenuOption:
    """Test MenuOption class"""

    def test_menu_option_creation(self):
        """Test MenuOption can be created with key and label"""
        option = MenuOption(key="1", label="Data Collection")
        assert option.key == "1"
        assert option.label == "Data Collection"
        assert option.action is None

    def test_menu_option_with_action(self):
        """Test MenuOption can be created with action callable"""
        action = Mock()
        option = MenuOption(key="1", label="Test", action=action)
        assert option.action is action


class TestInteractiveMenu:
    """Test InteractiveMenu class"""

    def test_menu_initialization(self):
        """Test menu can be initialized with title and options"""
        options = [
            MenuOption(key="1", label="Option 1"),
            MenuOption(key="2", label="Option 2"),
        ]
        menu = InteractiveMenu(title="Test Menu", options=options)
        assert menu.title == "Test Menu"
        assert len(menu.options) == 2
        assert menu.options[0].key == "1"

    def test_menu_add_option(self):
        """Test adding option to menu"""
        menu = InteractiveMenu(title="Test Menu", options=[])
        menu.add_option(MenuOption(key="1", label="New Option"))
        assert len(menu.options) == 1
        assert menu.options[0].key == "1"

    def test_menu_show_returns_selected_option(self):
        """Test menu show returns selected option key"""
        options = [
            MenuOption(key="1", label="Option 1"),
            MenuOption(key="2", label="Option 2"),
        ]
        menu = InteractiveMenu(title="Test Menu", options=options)

        with patch.object(menu, '_get_user_input', return_value='1'):
            result = menu.show()
            assert result == "1"

    def test_menu_show_returns_none_for_invalid_option(self):
        """Test menu show returns None for invalid option"""
        options = [
            MenuOption(key="1", label="Option 1"),
            MenuOption(key="2", label="Option 2"),
        ]
        menu = InteractiveMenu(title="Test Menu", options=options)

        with patch.object(menu, '_get_user_input', return_value='99'):
            result = menu.show()
            assert result is None

    def test_menu_handles_escape_key(self):
        """Test menu handles ESC key (empty input)"""
        options = [MenuOption(key="1", label="Option 1")]
        menu = InteractiveMenu(title="Test Menu", options=options)

        with patch.object(menu, '_get_user_input', return_value=None):
            result = menu.show()
            assert result is None

    def test_menu_create_submenu(self):
        """Test creating submenu from main menu"""
        main_menu = InteractiveMenu(title="Main Menu", options=[])
        sub_options = [MenuOption(key="1", label="Sub Option 1")]
        submenu = main_menu.create_submenu(title="Sub Menu", options=sub_options)

        assert submenu.title == "Sub Menu"
        assert len(submenu.options) == 1
        assert isinstance(submenu, InteractiveMenu)


class TestMenuResult:
    """Test MenuResult class"""

    def test_menu_result_creation(self):
        """Test MenuResult can be created with selection and data"""
        result = MenuResult(selected_key="1", data={"test": "value"})
        assert result.selected_key == "1"
        assert result.data == {"test": "value"}

    def test_menu_result_is_exit(self):
        """Test MenuResult can check if exit was selected"""
        exit_result = MenuResult(selected_key="0", data={})
        normal_result = MenuResult(selected_key="1", data={})

        assert exit_result.is_exit() is True
        assert normal_result.is_exit() is False
