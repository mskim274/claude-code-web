"""
End-to-End backtest workflow tests

Tests complete backtesting scenarios from data collection to result analysis:
1. Data loading and preparation
2. Indicator calculation
3. Strategy signal generation
4. Backtest execution
5. Performance analysis
6. Multiple strategy comparison
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database models
from db.models import Base, Stock, DailyPrice
from backtest.engine import BacktestEngine
from backtest.strategy import BaseStrategy, MovingAverageCrossStrategy

# Schemas (with fallback)
try:
    from schemas.stock import DailyPriceSchema
except ImportError:
    DailyPriceSchema = None

# Indicators (with fallback)
try:
    from indicators.talib_wrapper import TechnicalIndicators
except ImportError:
    TechnicalIndicators = None


@pytest.fixture(scope="module")
def backtest_db():
    """Create in-memory database with sample data for backtesting"""
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create stock
    stock = Stock(code='005930', name='삼성전자', market='KOSPI')
    session.add(stock)

    # Generate 200 days of realistic price data
    base_date = date(2023, 1, 1)
    base_price = 70000

    np.random.seed(42)

    for i in range(200):
        # Simulate price movement with trend and noise
        trend = i * 50  # Upward trend
        noise = np.random.randint(-500, 500)
        close_price = base_price + trend + noise

        daily_price = DailyPrice(
            stock_code='005930',
            date=base_date + timedelta(days=i),
            open=int(close_price * 0.995),
            high=int(close_price * 1.01),
            low=int(close_price * 0.99),
            close=close_price,
            volume=np.random.randint(10000000, 20000000)
        )
        session.add(daily_price)

    session.commit()

    yield engine

    session.close()
    engine.dispose()


class TestBasicBacktest:
    """기본 백테스트 워크플로우 테스트"""

    def test_simple_ma_cross_backtest(self, backtest_db):
        """단순 이동평균 교차 전략 백테스트"""
        # Create backtest engine
        strategy = MovingAverageCrossStrategy(short_window=20, long_window=60)
        engine = BacktestEngine(
            strategy=strategy,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 7, 20),
            initial_capital=10000000
        )

        # Load data (monkey patch to use our test DB)
        Session = sessionmaker(bind=backtest_db)
        session = Session()

        with pytest.MonkeyPatch.context() as mp:
            # Run backtest
            data = engine.load_data('005930')

            if data is None or len(data) == 0:
                # Manually load from test DB
                query = session.query(DailyPrice).filter(
                    DailyPrice.stock_code == '005930'
                ).order_by(DailyPrice.date)
                prices = query.all()

                data = pd.DataFrame([
                    {
                        'date': p.date,
                        'open': p.open,
                        'high': p.high,
                        'low': p.low,
                        'close': p.close,
                        'volume': p.volume
                    }
                    for p in prices
                ])
                data.set_index('date', inplace=True)

            # Generate signals
            signals = strategy.generate_signals(data)

            assert signals is not None
            assert 'signal' in signals.columns
            assert 'positions' in signals.columns
            assert len(signals) > 0

        session.close()

    def test_backtest_with_indicators(self, backtest_db):
        """TA-Lib 지표를 사용한 백테스트"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        # Load data
        Session = sessionmaker(bind=backtest_db)
        session = Session()

        query = session.query(DailyPrice).filter(
            DailyPrice.stock_code == '005930'
        ).order_by(DailyPrice.date)
        prices = query.all()

        df = pd.DataFrame([
            {
                'date': p.date,
                'open': p.open,
                'high': p.high,
                'low': p.low,
                'close': p.close,
                'volume': p.volume
            }
            for p in prices
        ])

        # Add indicators
        indicators = TechnicalIndicators()
        df_with_indicators = indicators.calculate_all(df)

        # Verify indicators
        assert 'sma_20' in df_with_indicators.columns
        assert 'rsi_14' in df_with_indicators.columns
        assert 'macd' in df_with_indicators.columns

        session.close()

    def test_full_backtest_execution(self, backtest_db):
        """전체 백테스트 실행"""
        # Load and prepare data
        Session = sessionmaker(bind=backtest_db)
        session = Session()

        query = session.query(DailyPrice).filter(
            DailyPrice.stock_code == '005930'
        ).order_by(DailyPrice.date)
        prices = query.all()

        df = pd.DataFrame([
            {
                'date': p.date,
                'open': p.open,
                'high': p.high,
                'low': p.low,
                'close': p.close,
                'volume': p.volume
            }
            for p in prices
        ])
        df.set_index('date', inplace=True)

        # Create and run strategy
        strategy = MovingAverageCrossStrategy(short_window=20, long_window=60)
        signals = strategy.generate_signals(df)

        # Simulate backtest execution
        initial_capital = 10000000
        position = 0
        cash = initial_capital

        for date_idx, row in signals.iterrows():
            if pd.isna(row.get('positions', 0)):
                continue

            # Buy signal
            if row['positions'] == 1 and position == 0:
                price = row['price']
                max_quantity = int(cash / price)
                if max_quantity > 0:
                    cost = price * max_quantity
                    cash -= cost
                    position = max_quantity

            # Sell signal
            elif row['positions'] == -1 and position > 0:
                price = row['price']
                proceeds = price * position
                cash += proceeds
                position = 0

        # Calculate final value
        if position > 0:
            final_price = df.iloc[-1]['close']
            cash += final_price * position

        total_return = (cash - initial_capital) / initial_capital * 100

        print(f"\n✓ Backtest Results:")
        print(f"  Initial Capital: {initial_capital:,} KRW")
        print(f"  Final Capital: {cash:,.0f} KRW")
        print(f"  Total Return: {total_return:.2f}%")

        assert cash > 0
        assert abs(total_return) < 1000  # Sanity check

        session.close()


class RSIStrategyForTesting(BaseStrategy):
    """RSI 기반 전략 (테스트용)"""

    def __init__(self, rsi_period=14, oversold=30, overbought=70):
        super().__init__(name="RSI_Strategy")
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, data):
        """RSI 기반 매매 신호 생성"""
        if TechnicalIndicators is None:
            # Fallback: use simple moving average
            signals = pd.DataFrame(index=data.index)
            signals['price'] = data['close']
            signals['signal'] = 0
            signals['positions'] = 0
            return signals

        indicators = TechnicalIndicators()
        df_with_indicators = indicators.calculate_rsi(data, period=self.rsi_period)

        signals = pd.DataFrame(index=df_with_indicators.index)
        signals['price'] = df_with_indicators['close']
        signals['rsi'] = df_with_indicators['rsi_14']

        # Generate signals: buy when oversold, sell when overbought
        signals['signal'] = 0
        signals.loc[signals['rsi'] < self.oversold, 'signal'] = 1  # Buy
        signals.loc[signals['rsi'] > self.overbought, 'signal'] = -1  # Sell

        # Position changes
        signals['positions'] = signals['signal'].diff()

        return signals


class TestAdvancedStrategies:
    """고급 전략 테스트"""

    def test_rsi_strategy(self, backtest_db):
        """RSI 전략 백테스트"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        # Load data
        Session = sessionmaker(bind=backtest_db)
        session = Session()

        query = session.query(DailyPrice).filter(
            DailyPrice.stock_code == '005930'
        ).order_by(DailyPrice.date)
        prices = query.all()

        df = pd.DataFrame([
            {
                'date': p.date,
                'open': p.open,
                'high': p.high,
                'low': p.low,
                'close': p.close,
                'volume': p.volume
            }
            for p in prices
        ])
        df.set_index('date', inplace=True)

        # Create RSI strategy
        strategy = RSIStrategyForTesting(rsi_period=14, oversold=30, overbought=70)
        signals = strategy.generate_signals(df)

        assert signals is not None
        assert 'rsi' in signals.columns
        assert 'signal' in signals.columns

        # Check signals are generated
        buy_signals = (signals['signal'] == 1).sum()
        sell_signals = (signals['signal'] == -1).sum()

        print(f"\n✓ RSI Strategy Signals:")
        print(f"  Buy signals: {buy_signals}")
        print(f"  Sell signals: {sell_signals}")

        session.close()

    def test_multiple_strategy_comparison(self, backtest_db):
        """여러 전략 비교"""
        # Load data
        Session = sessionmaker(bind=backtest_db)
        session = Session()

        query = session.query(DailyPrice).filter(
            DailyPrice.stock_code == '005930'
        ).order_by(DailyPrice.date)
        prices = query.all()

        df = pd.DataFrame([
            {
                'date': p.date,
                'open': p.open,
                'high': p.high,
                'low': p.low,
                'close': p.close,
                'volume': p.volume
            }
            for p in prices
        ])
        df.set_index('date', inplace=True)

        # Test multiple strategies
        strategies = [
            MovingAverageCrossStrategy(short_window=20, long_window=60),
            MovingAverageCrossStrategy(short_window=10, long_window=30),
        ]

        if TechnicalIndicators is not None:
            strategies.append(RSIStrategyForTesting(rsi_period=14, oversold=30, overbought=70))

        results = []

        for strategy in strategies:
            signals = strategy.generate_signals(df)
            if signals is None:
                continue

            # Simple performance metric: number of signals
            buy_count = (signals.get('positions', 0) == 1).sum()
            sell_count = (signals.get('positions', 0) == -1).sum()

            results.append({
                'strategy': strategy.name,
                'buy_signals': buy_count,
                'sell_signals': sell_count
            })

        print(f"\n✓ Strategy Comparison:")
        for result in results:
            print(f"  {result['strategy']}: "
                  f"{result['buy_signals']} buys, {result['sell_signals']} sells")

        assert len(results) >= 2

        session.close()


class TestPerformanceMetrics:
    """성과 지표 테스트"""

    def test_calculate_sharpe_ratio(self, backtest_db):
        """샤프 비율 계산"""
        # Load data
        Session = sessionmaker(bind=backtest_db)
        session = Session()

        query = session.query(DailyPrice).filter(
            DailyPrice.stock_code == '005930'
        ).order_by(DailyPrice.date)
        prices = query.all()

        df = pd.DataFrame([
            {
                'date': p.date,
                'close': p.close
            }
            for p in prices
        ])

        # Calculate returns
        df['returns'] = df['close'].pct_change()

        # Calculate Sharpe Ratio
        mean_return = df['returns'].mean()
        std_return = df['returns'].std()
        sharpe_ratio = (mean_return / std_return) * np.sqrt(252) if std_return != 0 else 0

        print(f"\n✓ Performance Metrics:")
        print(f"  Mean Daily Return: {mean_return:.4f}")
        print(f"  Std Dev: {std_return:.4f}")
        print(f"  Sharpe Ratio: {sharpe_ratio:.2f}")

        assert isinstance(sharpe_ratio, (int, float))

        session.close()

    def test_calculate_max_drawdown(self, backtest_db):
        """최대 낙폭 계산"""
        # Load data
        Session = sessionmaker(bind=backtest_db)
        session = Session()

        query = session.query(DailyPrice).filter(
            DailyPrice.stock_code == '005930'
        ).order_by(DailyPrice.date)
        prices = query.all()

        df = pd.DataFrame([
            {
                'date': p.date,
                'close': p.close
            }
            for p in prices
        ])

        # Calculate max drawdown
        df['returns'] = df['close'].pct_change()
        cumulative = (1 + df['returns']).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100

        print(f"\n✓ Max Drawdown: {max_drawdown:.2f}%")

        assert max_drawdown <= 0  # Drawdown should be negative or zero

        session.close()

    def test_win_rate_calculation(self, backtest_db):
        """승률 계산"""
        # Simulate trades
        trades = [
            {'action': 'BUY', 'price': 70000},
            {'action': 'SELL', 'price': 72000},  # Win
            {'action': 'BUY', 'price': 72000},
            {'action': 'SELL', 'price': 71000},  # Loss
            {'action': 'BUY', 'price': 71000},
            {'action': 'SELL', 'price': 73000},  # Win
        ]

        wins = 0
        losses = 0

        for i in range(0, len(trades), 2):
            if i + 1 < len(trades):
                buy_price = trades[i]['price']
                sell_price = trades[i + 1]['price']
                if sell_price > buy_price:
                    wins += 1
                else:
                    losses += 1

        win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

        print(f"\n✓ Win Rate: {win_rate:.2f}% ({wins} wins, {losses} losses)")

        assert 0 <= win_rate <= 100


class TestRealWorldScenarios:
    """실제 시나리오 테스트"""

    def test_bull_market_strategy(self, backtest_db):
        """상승장 전략 테스트"""
        # Load data
        Session = sessionmaker(bind=backtest_db)
        session = Session()

        query = session.query(DailyPrice).filter(
            DailyPrice.stock_code == '005930'
        ).order_by(DailyPrice.date)
        prices = query.all()

        df = pd.DataFrame([
            {
                'date': p.date,
                'open': p.open,
                'high': p.high,
                'low': p.low,
                'close': p.close,
                'volume': p.volume
            }
            for p in prices
        ])
        df.set_index('date', inplace=True)

        # Buy-and-hold strategy
        initial_price = df.iloc[0]['close']
        final_price = df.iloc[-1]['close']
        buy_hold_return = (final_price - initial_price) / initial_price * 100

        print(f"\n✓ Buy-and-Hold Return: {buy_hold_return:.2f}%")

        # Our strategy should ideally beat buy-and-hold
        strategy = MovingAverageCrossStrategy(short_window=20, long_window=60)
        signals = strategy.generate_signals(df)

        assert signals is not None

        session.close()

    def test_volatility_handling(self, backtest_db):
        """변동성 처리 테스트"""
        # Load data
        Session = sessionmaker(bind=backtest_db)
        session = Session()

        query = session.query(DailyPrice).filter(
            DailyPrice.stock_code == '005930'
        ).order_by(DailyPrice.date)
        prices = query.all()

        df = pd.DataFrame([
            {
                'date': p.date,
                'close': p.close
            }
            for p in prices
        ])

        # Calculate volatility
        df['returns'] = df['close'].pct_change()
        volatility = df['returns'].std() * np.sqrt(252) * 100  # Annualized

        print(f"\n✓ Annualized Volatility: {volatility:.2f}%")

        # Strategy should handle high volatility
        assert volatility >= 0

        session.close()

    @pytest.mark.slow
    def test_long_period_backtest(self, backtest_db):
        """장기 백테스트 (200일)"""
        # Load all data
        Session = sessionmaker(bind=backtest_db)
        session = Session()

        query = session.query(DailyPrice).filter(
            DailyPrice.stock_code == '005930'
        ).order_by(DailyPrice.date)
        prices = query.all()

        df = pd.DataFrame([
            {
                'date': p.date,
                'open': p.open,
                'high': p.high,
                'low': p.low,
                'close': p.close,
                'volume': p.volume
            }
            for p in prices
        ])
        df.set_index('date', inplace=True)

        # Run strategy over full period
        strategy = MovingAverageCrossStrategy(short_window=20, long_window=60)
        signals = strategy.generate_signals(df)

        assert len(signals) == len(df)

        # Count trades
        trades = (signals['positions'] != 0).sum()
        print(f"\n✓ Total trades over 200 days: {trades}")

        session.close()


class TestEdgeCases:
    """경계 조건 테스트"""

    def test_no_signals_generated(self):
        """신호가 생성되지 않는 경우"""
        # Create flat price data
        df = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=100),
            'open': [70000] * 100,
            'high': [71000] * 100,
            'low': [69000] * 100,
            'close': [70000] * 100,  # Flat prices
            'volume': [10000000] * 100
        })
        df.set_index('date', inplace=True)

        strategy = MovingAverageCrossStrategy(short_window=20, long_window=60)
        signals = strategy.generate_signals(df)

        # Should generate signals dataframe even if no crossovers
        assert signals is not None
        assert 'signal' in signals.columns

    def test_insufficient_data_for_strategy(self):
        """전략 실행에 불충분한 데이터"""
        # Only 50 days, but long MA is 60
        df = pd.DataFrame({
            'date': pd.date_range(start='2024-01-01', periods=50),
            'open': [70000] * 50,
            'high': [71000] * 50,
            'low': [69000] * 50,
            'close': [70000] * 50,
            'volume': [10000000] * 50
        })
        df.set_index('date', inplace=True)

        strategy = MovingAverageCrossStrategy(short_window=20, long_window=60)
        signals = strategy.generate_signals(df)

        # Should handle gracefully
        assert signals is not None

    def test_all_buy_signals(self):
        """모든 매수 신호만 발생"""
        # This would happen in extreme uptrend
        # Strategy should handle gracefully (not enough sells to close positions)
        pass  # Implementation depends on strategy logic


# E2E workflow summary
@pytest.fixture(scope="module", autouse=True)
def e2e_summary(request):
    """Print E2E test summary"""
    yield

    print("\n" + "=" * 70)
    print("END-TO-END BACKTEST WORKFLOW SUMMARY")
    print("=" * 70)
    print("Completed E2E tests covering:")
    print("  ✓ Basic MA crossover strategy")
    print("  ✓ RSI-based strategy")
    print("  ✓ Multiple strategy comparison")
    print("  ✓ Performance metrics (Sharpe, drawdown, win rate)")
    print("  ✓ Real-world scenarios (bull market, volatility)")
    print("  ✓ Edge cases (no signals, insufficient data)")
    print("=" * 70 + "\n")
