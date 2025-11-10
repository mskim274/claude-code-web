"""
End-to-End tests for overseas stock backtesting.

Tests complete workflow from data collection to backtesting for:
- US stocks (NASDAQ, NYSE)
- Chinese stocks
- Japanese stocks
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any

from collectors.apis.unified import UnifiedAPIClient
from tests.fixtures.mock_apis import MockKISAPI


class SimpleBacktester:
    """Simple backtester for testing purposes"""

    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions: Dict[str, float] = {}
        self.trades: List[Dict] = []

    def buy(self, symbol: str, price: float, shares: float, timestamp: datetime):
        """Buy shares"""
        cost = price * shares
        if cost <= self.capital:
            self.capital -= cost
            self.positions[symbol] = self.positions.get(symbol, 0) + shares
            self.trades.append({
                "type": "buy",
                "symbol": symbol,
                "price": price,
                "shares": shares,
                "timestamp": timestamp,
            })
            return True
        return False

    def sell(self, symbol: str, price: float, shares: float, timestamp: datetime):
        """Sell shares"""
        if symbol in self.positions and self.positions[symbol] >= shares:
            self.capital += price * shares
            self.positions[symbol] -= shares
            self.trades.append({
                "type": "sell",
                "symbol": symbol,
                "price": price,
                "shares": shares,
                "timestamp": timestamp,
            })
            return True
        return False

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        position_value = sum(
            shares * current_prices.get(symbol, 0)
            for symbol, shares in self.positions.items()
        )
        return self.capital + position_value

    def get_returns(self, current_prices: Dict[str, float]) -> float:
        """Calculate returns as percentage"""
        current_value = self.get_portfolio_value(current_prices)
        return (current_value - self.initial_capital) / self.initial_capital * 100


class TestOverseasDataCollection:
    """Test overseas stock data collection"""

    def test_collect_us_stock_data(self):
        """Test collecting US stock data from NASDAQ"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())

        us_stocks = ["AAPL", "MSFT", "GOOGL", "AMZN"]
        data = []

        for symbol in us_stocks:
            stock_data = client.get_overseas_stock(symbol, "NASDAQ")
            data.append(stock_data)

        assert len(data) == 4
        assert all(d["exchange"] == "NASDAQ" for d in data)
        assert all(d["current_price"] > 0 for d in data)

    def test_collect_multiple_exchange_data(self):
        """Test collecting data from multiple exchanges"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())

        stocks = [
            ("AAPL", "NASDAQ"),
            ("JPM", "NYSE"),
            ("TSM", "NYSE"),
        ]

        data = []
        for symbol, exchange in stocks:
            stock_data = client.get_overseas_stock(symbol, exchange)
            data.append(stock_data)

        df = pd.DataFrame(data)

        assert len(df) == 3
        assert set(df["exchange"].unique()) == {"NASDAQ", "NYSE"}

    def test_collect_asian_stocks(self):
        """Test collecting Chinese and Japanese stock data"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())

        # Chinese stocks (Hong Kong)
        chinese_stocks = [("BABA", "HKEX"), ("TCEHY", "HKEX")]

        # Japanese stocks (Tokyo)
        japanese_stocks = [("7203", "TSE"), ("6758", "TSE")]

        all_data = []

        for symbol, exchange in chinese_stocks + japanese_stocks:
            stock_data = client.get_overseas_stock(symbol, exchange)
            all_data.append(stock_data)

        df = pd.DataFrame(all_data)

        assert len(df) == 4
        assert "HKEX" in df["exchange"].values
        assert "TSE" in df["exchange"].values

    def test_data_quality_validation(self):
        """Test validating collected overseas data quality"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())

        stock_data = client.get_overseas_stock("AAPL", "NASDAQ")

        # Check required fields
        required_fields = [
            "symbol", "exchange", "current_price", "open_price",
            "high_price", "low_price", "volume", "change_rate"
        ]
        for field in required_fields:
            assert field in stock_data, f"Missing field: {field}"

        # Check price relationships
        assert stock_data["low_price"] <= stock_data["current_price"]
        assert stock_data["current_price"] <= stock_data["high_price"]
        assert stock_data["volume"] > 0

    def test_batch_data_collection_with_cache(self):
        """Test batch collection with caching"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())

        symbols = ["AAPL", "MSFT", "GOOGL"]

        # First batch - cache miss
        batch1 = []
        for symbol in symbols:
            batch1.append(client.get_overseas_stock(symbol, "NASDAQ"))

        # Second batch - cache hit
        batch2 = []
        for symbol in symbols:
            batch2.append(client.get_overseas_stock(symbol, "NASDAQ"))

        # Cache should reduce API calls
        stats = client.get_cache_stats()
        assert stats["hits"] > 0

        # Data should be identical
        assert batch1[0]["current_price"] == batch2[0]["current_price"]


class TestOverseasBacktestStrategies:
    """Test various backtesting strategies for overseas stocks"""

    def test_simple_buy_and_hold_strategy(self):
        """Test buy and hold strategy"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())
        backtester = SimpleBacktester(initial_capital=10000)

        # Buy stocks at start
        symbols = ["AAPL", "MSFT", "GOOGL"]
        start_prices = {}

        for symbol in symbols:
            data = client.get_overseas_stock(symbol, "NASDAQ")
            price = data["current_price"]
            start_prices[symbol] = price

            # Buy equal amounts
            shares = (backtester.initial_capital / len(symbols)) / price
            backtester.buy(symbol, price, shares, datetime.now())

        # Simulate price increase
        client.clear_cache()

        end_prices = {}
        for symbol in symbols:
            data = client.get_overseas_stock(symbol, "NASDAQ")
            end_prices[symbol] = data["current_price"] * 1.1  # 10% increase

        # Calculate returns
        returns = backtester.get_returns(end_prices)

        assert len(backtester.trades) == 3
        assert all(t["type"] == "buy" for t in backtester.trades)

    def test_momentum_strategy(self):
        """Test momentum-based trading strategy"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())
        backtester = SimpleBacktester(initial_capital=10000)

        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN"]

        # Collect initial data
        initial_data = {}
        for symbol in symbols:
            data = client.get_overseas_stock(symbol, "NASDAQ")
            initial_data[symbol] = {
                "price": data["current_price"],
                "change_rate": data["change_rate"]
            }

        # Buy top performers (positive momentum)
        top_performers = sorted(
            initial_data.items(),
            key=lambda x: x[1]["change_rate"],
            reverse=True
        )[:2]

        for symbol, data in top_performers:
            if data["change_rate"] > 0:
                shares = (backtester.initial_capital / 2) / data["price"]
                backtester.buy(symbol, data["price"], shares, datetime.now())

        assert len(backtester.trades) >= 1
        assert all(
            initial_data[t["symbol"]]["change_rate"] > 0
            for t in backtester.trades
        )

    def test_diversified_portfolio_strategy(self):
        """Test diversified portfolio across regions"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())
        backtester = SimpleBacktester(initial_capital=10000)

        # Diversify across regions
        portfolio = [
            ("AAPL", "NASDAQ"),   # US Tech
            ("JPM", "NYSE"),      # US Finance
            ("BABA", "HKEX"),     # China Tech
            ("7203", "TSE"),      # Japan Auto
        ]

        allocation_per_stock = backtester.initial_capital / len(portfolio)

        for symbol, exchange in portfolio:
            data = client.get_overseas_stock(symbol, exchange)
            shares = allocation_per_stock / data["current_price"]
            backtester.buy(
                symbol,
                data["current_price"],
                shares,
                datetime.now()
            )

        assert len(backtester.trades) == 4
        assert len(set(t["symbol"] for t in backtester.trades)) == 4

        # Portfolio should be diversified
        unique_exchanges = set(exch for _, exch in portfolio)
        assert len(unique_exchanges) >= 3

    def test_stop_loss_strategy(self):
        """Test strategy with stop-loss mechanism"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())
        backtester = SimpleBacktester(initial_capital=10000)

        symbol = "AAPL"
        stop_loss_pct = 0.05  # 5% stop loss

        # Buy initial position
        data = client.get_overseas_stock(symbol, "NASDAQ")
        buy_price = data["current_price"]
        shares = backtester.initial_capital / buy_price
        backtester.buy(symbol, buy_price, shares, datetime.now())

        # Simulate price drop
        current_price = buy_price * 0.93  # 7% drop
        stop_loss_price = buy_price * (1 - stop_loss_pct)

        # Trigger stop loss
        if current_price <= stop_loss_price:
            backtester.sell(symbol, current_price, shares, datetime.now())

        # Should have both buy and sell trades
        assert len(backtester.trades) == 2
        assert backtester.trades[0]["type"] == "buy"
        assert backtester.trades[1]["type"] == "sell"

    def test_sector_rotation_strategy(self):
        """Test sector rotation strategy"""
        client = UnifiedAPIClient(kis_api=MockKISAPI())
        backtester = SimpleBacktester(initial_capital=10000)

        # Define sectors
        sectors = {
            "tech": ["AAPL", "MSFT", "GOOGL"],
            "finance": ["JPM", "BAC", "GS"],
            "healthcare": ["JNJ", "PFE", "UNH"],
        }

        # Calculate sector momentum
        sector_performance = {}

        for sector, symbols in sectors.items():
            total_change = 0
            for symbol in symbols:
                data = client.get_overseas_stock(symbol, "NASDAQ")
                total_change += data["change_rate"]

            sector_performance[sector] = total_change / len(symbols)

        # Invest in best performing sector
        best_sector = max(sector_performance.items(), key=lambda x: x[1])[0]
        best_symbols = sectors[best_sector]

        allocation_per_stock = backtester.initial_capital / len(best_symbols)

        for symbol in best_symbols:
            data = client.get_overseas_stock(symbol, "NASDAQ")
            shares = allocation_per_stock / data["current_price"]
            backtester.buy(symbol, data["current_price"], shares, datetime.now())

        # All trades should be in same sector
        traded_symbols = set(t["symbol"] for t in backtester.trades)
        assert traded_symbols.issubset(set(best_symbols))


class TestBacktestPerformanceMetrics:
    """Test calculating backtest performance metrics"""

    def test_calculate_total_returns(self):
        """Test calculating total returns"""
        backtester = SimpleBacktester(initial_capital=10000)

        # Execute some trades
        backtester.buy("AAPL", 150.0, 20, datetime.now())
        backtester.buy("MSFT", 300.0, 10, datetime.now())

        # Current prices with gains
        current_prices = {"AAPL": 165.0, "MSFT": 330.0}

        returns = backtester.get_returns(current_prices)

        assert returns > 0  # Should have positive returns
        assert isinstance(returns, float)

    def test_calculate_sharpe_ratio(self):
        """Test calculating Sharpe ratio (simplified)"""
        # Simulate returns over time
        returns = [0.02, -0.01, 0.03, 0.01, -0.005, 0.02]

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        # Simplified Sharpe ratio (assuming risk-free rate = 0)
        sharpe_ratio = mean_return / std_return if std_return > 0 else 0

        assert isinstance(sharpe_ratio, float)
        assert sharpe_ratio != 0

    def test_max_drawdown_calculation(self):
        """Test calculating maximum drawdown"""
        # Simulate portfolio values over time
        portfolio_values = [10000, 10500, 10200, 11000, 10800, 11500]

        peak = portfolio_values[0]
        max_dd = 0

        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_dd = max(max_dd, drawdown)

        assert max_dd >= 0
        assert max_dd <= 1

    def test_win_rate_calculation(self):
        """Test calculating win rate"""
        backtester = SimpleBacktester(initial_capital=10000)

        # Simulate trades
        trades = [
            {"type": "sell", "symbol": "AAPL", "profit": 100},
            {"type": "sell", "symbol": "MSFT", "profit": -50},
            {"type": "sell", "symbol": "GOOGL", "profit": 200},
            {"type": "sell", "symbol": "AMZN", "profit": -30},
        ]

        winning_trades = sum(1 for t in trades if t["profit"] > 0)
        win_rate = winning_trades / len(trades)

        assert win_rate == 0.5  # 2 out of 4 trades were profitable

    def test_portfolio_metrics_summary(self):
        """Test generating comprehensive portfolio metrics"""
        backtester = SimpleBacktester(initial_capital=10000)

        # Execute trades
        backtester.buy("AAPL", 150.0, 20, datetime.now())
        backtester.buy("MSFT", 300.0, 10, datetime.now())

        current_prices = {"AAPL": 165.0, "MSFT": 330.0}

        metrics = {
            "initial_capital": backtester.initial_capital,
            "current_value": backtester.get_portfolio_value(current_prices),
            "total_returns": backtester.get_returns(current_prices),
            "number_of_trades": len(backtester.trades),
            "positions": len(backtester.positions),
        }

        assert metrics["current_value"] > metrics["initial_capital"]
        assert metrics["total_returns"] > 0
        assert metrics["number_of_trades"] == 2
        assert metrics["positions"] == 2
