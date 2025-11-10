"""Table rendering module for CLI"""
from rich.table import Table
from rich.console import Console
import pandas as pd
from typing import List, Optional, Dict, Any


class TableRenderer:
    """Rich Table wrapper for rendering data tables"""

    def __init__(self, console: Optional[Console] = None):
        """
        Initialize table renderer.

        Args:
            console: Rich Console instance (creates new if not provided)
        """
        self.console = console or Console()

    def render_dataframe(self, df: pd.DataFrame, title: str = "") -> Table:
        """
        Render pandas DataFrame as Rich Table.

        Args:
            df: DataFrame to render
            title: Table title

        Returns:
            Rich Table instance
        """
        table = Table(title=title, show_header=True, header_style="bold magenta")

        # Add columns
        for col in df.columns:
            table.add_column(str(col))

        # Add rows
        for _, row in df.iterrows():
            table.add_row(*[str(val) for val in row])

        return table

    def render_stock_prices(self, prices: List[Dict[str, Any]]) -> Table:
        """
        Render stock prices table.

        Args:
            prices: List of price dictionaries

        Returns:
            Rich Table instance
        """
        table = Table(title="주가 데이터", show_header=True)
        table.add_column("종목코드", style="cyan")
        table.add_column("종목명")
        table.add_column("현재가", justify="right", style="green")
        table.add_column("등락률", justify="right")

        for price in prices:
            change_rate = price.get('change_rate', 0)
            change_color = "red" if change_rate < 0 else "green"
            table.add_row(
                price['code'],
                price['name'],
                f"{price['price']:,}",
                f"[{change_color}]{change_rate:.2f}%[/{change_color}]"
            )

        return table

    def render_backtest_results(self, results: Dict[str, Any]) -> Table:
        """
        Render backtest results table.

        Args:
            results: Dictionary with backtest metrics

        Returns:
            Rich Table instance
        """
        table = Table(title="백테스팅 결과", show_header=True, header_style="bold cyan")
        table.add_column("지표", style="cyan")
        table.add_column("값", justify="right")

        # Map metric names to Korean
        metric_names = {
            "total_return": "총 수익률",
            "sharpe_ratio": "샤프 비율",
            "max_drawdown": "최대 낙폭",
            "win_rate": "승률",
            "total_trades": "총 거래 횟수"
        }

        for key, value in results.items():
            display_name = metric_names.get(key, key)

            # Format value based on type
            if isinstance(value, float):
                if key in ["total_return", "max_drawdown", "win_rate"]:
                    formatted_value = f"{value:.2f}%"
                else:
                    formatted_value = f"{value:.2f}"
            else:
                formatted_value = str(value)

            # Color based on value
            if key == "total_return":
                color = "green" if value > 0 else "red"
                formatted_value = f"[{color}]{formatted_value}[/{color}]"

            table.add_row(display_name, formatted_value)

        return table

    def render_feature_importance(self, features: List[Dict[str, Any]]) -> Table:
        """
        Render feature importance table.

        Args:
            features: List of feature dictionaries with name and importance

        Returns:
            Rich Table instance
        """
        table = Table(title="Feature Importance", show_header=True, header_style="bold magenta")
        table.add_column("Feature", style="cyan")
        table.add_column("Importance", justify="right")
        table.add_column("Bar", justify="left")

        # Sort by importance descending
        sorted_features = sorted(features, key=lambda x: x['importance'], reverse=True)

        for feature in sorted_features:
            importance = feature['importance']
            # Create simple bar chart
            bar_length = int(importance * 50)  # Scale to 50 chars max
            bar = "█" * bar_length

            table.add_row(
                feature['feature'],
                f"{importance:.4f}",
                f"[green]{bar}[/green]"
            )

        return table

    def render_ml_predictions(self, predictions: List[Dict[str, Any]]) -> Table:
        """
        Render ML prediction results table.

        Args:
            predictions: List of prediction dictionaries

        Returns:
            Rich Table instance
        """
        table = Table(title="ML 예측 결과", show_header=True, header_style="bold cyan")
        table.add_column("날짜", style="cyan")
        table.add_column("실제값", justify="right")
        table.add_column("예측값", justify="right")
        table.add_column("오차율(%)", justify="right")

        for pred in predictions:
            error = pred.get('error', 0)
            error_color = "red" if error > 2 else "yellow" if error > 1 else "green"

            table.add_row(
                pred['date'],
                f"{pred['actual']:,}",
                f"{pred['predicted']:,}",
                f"[{error_color}]{error:.2f}%[/{error_color}]"
            )

        return table

    def print_table(self, table: Table) -> None:
        """
        Print table to console.

        Args:
            table: Rich Table instance
        """
        self.console.print(table)
