"""Tests for table rendering module"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch
from cli.ui.table import TableRenderer


class TestTableRenderer:
    """Test TableRenderer class"""

    def test_table_renderer_initialization(self):
        """Test TableRenderer can be initialized"""
        renderer = TableRenderer()
        assert renderer.console is not None

    def test_table_renderer_with_custom_console(self):
        """Test TableRenderer with custom console"""
        custom_console = Mock()
        renderer = TableRenderer(console=custom_console)
        assert renderer.console is custom_console

    def test_render_dataframe(self):
        """Test rendering pandas DataFrame as table"""
        renderer = TableRenderer()
        df = pd.DataFrame({
            "종목코드": ["005930", "000660"],
            "종목명": ["삼성전자", "SK하이닉스"],
            "현재가": [70000, 120000]
        })

        table = renderer.render_dataframe(df, title="테스트 테이블")
        assert table is not None
        assert table.title == "테스트 테이블"

    def test_render_empty_dataframe(self):
        """Test rendering empty DataFrame"""
        renderer = TableRenderer()
        df = pd.DataFrame()

        table = renderer.render_dataframe(df, title="빈 테이블")
        assert table is not None
        assert table.title == "빈 테이블"

    def test_render_stock_prices(self):
        """Test rendering stock prices table"""
        renderer = TableRenderer()
        prices = [
            {
                "code": "005930",
                "name": "삼성전자",
                "price": 70000,
                "change_rate": 1.5
            },
            {
                "code": "000660",
                "name": "SK하이닉스",
                "price": 120000,
                "change_rate": -2.3
            }
        ]

        table = renderer.render_stock_prices(prices)
        assert table is not None
        assert table.title == "주가 데이터"

    def test_render_backtest_results(self):
        """Test rendering backtest results table"""
        renderer = TableRenderer()
        results = {
            "total_return": 15.5,
            "sharpe_ratio": 1.8,
            "max_drawdown": -12.3,
            "win_rate": 65.5,
            "total_trades": 150
        }

        table = renderer.render_backtest_results(results)
        assert table is not None
        assert table.title == "백테스팅 결과"

    def test_render_feature_importance(self):
        """Test rendering feature importance table"""
        renderer = TableRenderer()
        features = [
            {"feature": "RSI", "importance": 0.35},
            {"feature": "MACD", "importance": 0.28},
            {"feature": "BB", "importance": 0.22},
            {"feature": "Volume", "importance": 0.15}
        ]

        table = renderer.render_feature_importance(features)
        assert table is not None
        assert table.title == "Feature Importance"

    def test_render_ml_predictions(self):
        """Test rendering ML prediction results table"""
        renderer = TableRenderer()
        predictions = [
            {
                "date": "2025-11-10",
                "actual": 70000,
                "predicted": 71000,
                "error": 1.43
            },
            {
                "date": "2025-11-11",
                "actual": 71500,
                "predicted": 72000,
                "error": 0.70
            }
        ]

        table = renderer.render_ml_predictions(predictions)
        assert table is not None
        assert table.title == "ML 예측 결과"

    def test_print_table(self):
        """Test printing table to console"""
        mock_console = Mock()
        renderer = TableRenderer(console=mock_console)
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})

        table = renderer.render_dataframe(df)
        renderer.print_table(table)

        mock_console.print.assert_called_once_with(table)
