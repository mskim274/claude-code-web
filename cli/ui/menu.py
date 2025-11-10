"""Interactive menu module for CLI"""
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass, field


@dataclass
class MenuOption:
    """Menu option with key, label, and optional action"""
    key: str
    label: str
    action: Optional[Callable] = None


@dataclass
class MenuResult:
    """Result of menu selection"""
    selected_key: str
    data: Dict[str, Any] = field(default_factory=dict)

    def is_exit(self) -> bool:
        """Check if exit option was selected"""
        return self.selected_key == "0"


class InteractiveMenu:
    """Interactive menu with keyboard navigation"""

    def __init__(self, title: str, options: List[MenuOption]):
        """
        Initialize interactive menu.

        Args:
            title: Menu title
            options: List of menu options
        """
        self.title = title
        self.options = options

    def add_option(self, option: MenuOption) -> None:
        """
        Add option to menu.

        Args:
            option: MenuOption to add
        """
        self.options.append(option)

    def _get_user_input(self, completer: WordCompleter) -> Optional[str]:
        """
        Get user input (extracted for testing).

        Args:
            completer: WordCompleter for auto-completion

        Returns:
            User input or None if cancelled
        """
        try:
            return prompt("\n선택: ", completer=completer)
        except (EOFError, KeyboardInterrupt):
            return None

    def show(self) -> Optional[str]:
        """
        Display menu and return selected option key.

        Returns:
            Selected option key or None if invalid
        """
        print(f"\n{self.title}")
        print("=" * 50)

        for opt in self.options:
            print(f"  {opt.key}. {opt.label}")

        completer = WordCompleter([opt.key for opt in self.options])
        choice = self._get_user_input(completer)

        if choice is None:
            return None

        # Validate choice
        if choice in [opt.key for opt in self.options]:
            return choice

        return None

    def create_submenu(self, title: str, options: List[MenuOption]) -> "InteractiveMenu":
        """
        Create submenu from current menu.

        Args:
            title: Submenu title
            options: List of submenu options

        Returns:
            New InteractiveMenu instance
        """
        return InteractiveMenu(title=title, options=options)

    def run(self) -> Optional[MenuResult]:
        """
        Run menu and execute selected action.

        Returns:
            MenuResult or None if cancelled
        """
        selected_key = self.show()

        if selected_key is None:
            return None

        # Find selected option
        selected_option = None
        for opt in self.options:
            if opt.key == selected_key:
                selected_option = opt
                break

        if selected_option is None:
            return None

        # Execute action if provided
        result_data = {}
        if selected_option.action:
            result_data = selected_option.action() or {}

        return MenuResult(selected_key=selected_key, data=result_data)
