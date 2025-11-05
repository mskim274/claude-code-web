"""
Chart widget for displaying stock price charts
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import pandas as pd


class ChartWidget(QWidget):
    """Widget for displaying candlestick charts"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        self.init_ui()

    def init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def plot_candlestick(self, df: pd.DataFrame, title: str = ""):
        """Plot candlestick chart with volume"""
        if df is None or len(df) == 0:
            return

        self.figure.clear()

        # Create subplots
        ax1 = self.figure.add_subplot(2, 1, 1)
        ax2 = self.figure.add_subplot(2, 1, 2, sharex=ax1)

        # Candlestick chart
        for idx, row in df.iterrows():
            date_num = idx

            color = 'red' if row['close'] >= row['open'] else 'blue'

            # Draw high-low line
            ax1.plot([date_num, date_num],
                    [row['low'], row['high']],
                    color=color, linewidth=1)

            # Draw open-close rectangle
            height = abs(row['close'] - row['open'])
            bottom = min(row['open'], row['close'])

            rect = Rectangle((date_num - 0.3, bottom), 0.6, height,
                           facecolor=color, edgecolor=color)
            ax1.add_patch(rect)

        ax1.set_ylabel('Price')
        ax1.set_title(title)
        ax1.grid(True, alpha=0.3)

        # Volume chart
        colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'blue'
                 for i in range(len(df))]

        ax2.bar(range(len(df)), df['volume'], color=colors, alpha=0.5)
        ax2.set_ylabel('Volume')
        ax2.set_xlabel('Date')
        ax2.grid(True, alpha=0.3)

        # Format x-axis
        if hasattr(df.index, 'strftime'):
            date_labels = df.index.strftime('%Y-%m-%d')
            tick_positions = range(0, len(df), max(1, len(df) // 10))
            ax2.set_xticks(tick_positions)
            ax2.set_xticklabels([date_labels[i] for i in tick_positions], rotation=45)

        self.figure.tight_layout()
        self.canvas.draw()

    def plot_line(self, df: pd.DataFrame, columns: list, title: str = ""):
        """Plot simple line chart"""
        if df is None or len(df) == 0:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(1, 1, 1)

        for col in columns:
            if col in df.columns:
                ax.plot(df.index, df[col], label=col)

        ax.set_xlabel('Date')
        ax.set_ylabel('Value')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()

    def plot_backtest_results(self, results: dict):
        """Plot backtest results"""
        if not results or 'equity_curve' not in results:
            return

        self.figure.clear()

        # Equity curve
        ax1 = self.figure.add_subplot(2, 1, 1)
        equity = results['equity_curve']

        ax1.plot(equity.index, equity['portfolio_value'], label='Portfolio Value', linewidth=2)
        ax1.axhline(y=results['initial_capital'], color='gray', linestyle='--', label='Initial Capital')

        ax1.set_ylabel('Portfolio Value')
        ax1.set_title(f"Backtest Results - Total Return: {results.get('total_return', 0):.2f}%")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Drawdown
        ax2 = self.figure.add_subplot(2, 1, 2, sharex=ax1)

        if 'drawdown' in equity.columns:
            ax2.fill_between(equity.index, equity['drawdown'], 0, color='red', alpha=0.3)
            ax2.set_ylabel('Drawdown (%)')
            ax2.set_xlabel('Date')
            ax2.grid(True, alpha=0.3)

        self.figure.tight_layout()
        self.canvas.draw()

    def clear(self):
        """Clear the chart"""
        self.figure.clear()
        self.canvas.draw()
