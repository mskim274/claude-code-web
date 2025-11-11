"""
백테스팅 엔진
"""

import logging
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import and_

from db.database import session_scope
from db.models import Stock, DailyPrice
from backtest.strategy import BaseStrategy

logger = logging.getLogger(__name__)


class BacktestEngine:
    """백테스팅 엔진"""

    def __init__(self, strategy: BaseStrategy, start_date, end_date, initial_capital=10000000):
        """
        백테스팅 엔진 초기화

        Args:
            strategy: 백테스팅 전략
            start_date: 시작일 (datetime.date)
            end_date: 종료일 (datetime.date)
            initial_capital: 초기 자본금
        """
        self.strategy = strategy
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital

        self.strategy.cash = initial_capital
        self.strategy.initial_cash = initial_capital

        self.results = None
        self.equity_curve = []

        logger.info(f"BacktestEngine initialized: {strategy.name}, {start_date} ~ {end_date}")

    def load_data(self, stock_code):
        """
        종목 데이터 로드

        Args:
            stock_code: 종목 코드

        Returns:
            pd.DataFrame: 주가 데이터
        """
        with session_scope() as session:
            query = session.query(DailyPrice).filter(
                and_(
                    DailyPrice.stock_code == stock_code,
                    DailyPrice.date >= self.start_date,
                    DailyPrice.date <= self.end_date
                )
            ).order_by(DailyPrice.date)

            prices = query.all()

            if not prices:
                logger.warning(f"No data for {stock_code}")
                return None

            # DataFrame 생성
            data = pd.DataFrame([
                {
                    'date': p.date,
                    'open': p.open,
                    'high': p.high,
                    'low': p.low,
                    'close': p.close,
                    'volume': p.volume,
                }
                for p in prices
            ])

            data.set_index('date', inplace=True)
            logger.info(f"Loaded {len(data)} records for {stock_code}")

            return data

    def run(self, stock_code):
        """
        백테스트 실행

        Args:
            stock_code: 종목 코드

        Returns:
            dict: 백테스트 결과
        """
        logger.info(f"Running backtest for {stock_code}")

        # 데이터 로드
        data = self.load_data(stock_code)
        if data is None or len(data) == 0:
            logger.error(f"No data available for {stock_code}")
            return None

        # 신호 생성
        signals = self.strategy.generate_signals(data)

        if signals is None:
            logger.error("Failed to generate signals")
            return None

        # 백테스트 실행
        position = 0  # 현재 포지션 (0: 없음, >0: 보유)

        for date, row in signals.iterrows():
            if pd.isna(row.get('positions', 0)):
                continue

            # 매수 신호
            if row['positions'] == 1 and position == 0:
                # 가용 현금으로 매수 가능한 수량 계산
                price = row['price']
                max_quantity = int(self.strategy.cash / price)

                if max_quantity > 0:
                    success = self.strategy.buy(stock_code, price, max_quantity, date)
                    if success:
                        position = max_quantity
                        logger.debug(f"BUY: {date}, Price: {price}, Qty: {max_quantity}")

            # 매도 신호
            elif row['positions'] == -1 and position > 0:
                price = row['price']
                success = self.strategy.sell(stock_code, price, position, date)
                if success:
                    logger.debug(f"SELL: {date}, Price: {price}, Qty: {position}")
                    position = 0

            # 일별 자산 기록
            current_prices = {stock_code: row['price']}
            portfolio_value = self.strategy.get_portfolio_value(current_prices)
            self.equity_curve.append({
                'date': date,
                'portfolio_value': portfolio_value,
                'cash': self.strategy.cash,
                'position': position
            })

        # 성과 계산
        performance = self.strategy.get_performance()

        # 최종 청산 (포지션이 남아있으면)
        if position > 0:
            final_price = data.iloc[-1]['close']
            self.strategy.sell(stock_code, final_price, position, data.index[-1])

        # 결과 저장
        equity_df = pd.DataFrame(self.equity_curve)

        # Validate and normalize equity curve DataFrame
        if not equity_df.empty and 'date' in equity_df.columns:
            # Convert date column to datetime if not already
            equity_df['date'] = pd.to_datetime(equity_df['date'])
            # Sort by date and remove duplicates
            equity_df = equity_df.drop_duplicates(subset='date').sort_values('date')
            # Set date as index
            equity_df.set_index('date', inplace=True)
        else:
            # Empty or invalid equity curve
            equity_df = None
            logger.warning(f"Invalid equity curve for {stock_code}: empty or missing 'date' column")

        # Calculate total return with division by zero guard
        if self.initial_capital > 0:
            total_return = ((self.strategy.cash - self.initial_capital) / self.initial_capital) * 100
        else:
            total_return = 0.0
            logger.warning(f"Initial capital is zero for {stock_code}, total_return set to 0")

        results = {
            'stock_code': stock_code,
            'strategy': self.strategy.name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_capital': self.initial_capital,
            'final_capital': self.strategy.cash,
            'total_return': total_return,
            'trades': self.strategy.trades,
            'performance': performance,
            'equity_curve': equity_df  # 자산 곡선 데이터 추가
        }

        # Clear equity_curve list to free memory
        self.equity_curve.clear()

        # Don't retain self.results to allow GC
        self.results = None

        logger.info(f"Backtest completed: Return={results['total_return']:.2f}%")

        return results

    def get_equity_curve(self):
        """
        자산 곡선 반환

        Returns:
            pd.DataFrame: 일별 자산 데이터
        """
        if not self.equity_curve:
            return None

        df = pd.DataFrame(self.equity_curve)
        df.set_index('date', inplace=True)
        return df

    def get_trades_df(self):
        """
        거래 내역 DataFrame 반환

        Returns:
            pd.DataFrame: 거래 내역
        """
        if not self.strategy.trades:
            return None

        return pd.DataFrame(self.strategy.trades)

    def calculate_metrics(self):
        """
        상세 성과 지표 계산

        Returns:
            dict: 성과 지표
        """
        if not self.results:
            return None

        equity_df = self.get_equity_curve()
        if equity_df is None:
            return None

        # 일별 수익률
        equity_df['returns'] = equity_df['portfolio_value'].pct_change()

        # Sharpe Ratio (연율화, 무위험 수익률 0 가정)
        sharpe_ratio = (equity_df['returns'].mean() / equity_df['returns'].std()) * (252 ** 0.5) \
            if equity_df['returns'].std() != 0 else 0

        # Maximum Drawdown
        cumulative = (1 + equity_df['returns']).cumprod()
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100

        # 승률 계산
        trades_df = self.get_trades_df()
        if trades_df is not None and len(trades_df) > 0:
            # 매수/매도 쌍 찾기
            buy_trades = trades_df[trades_df['action'] == 'BUY']
            sell_trades = trades_df[trades_df['action'] == 'SELL']

            wins = 0
            losses = 0
            for i in range(min(len(buy_trades), len(sell_trades))):
                buy_price = buy_trades.iloc[i]['price']
                sell_price = sell_trades.iloc[i]['price']
                if sell_price > buy_price:
                    wins += 1
                else:
                    losses += 1

            win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0
        else:
            win_rate = 0

        return {
            'total_return': self.results['total_return'],
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': len(self.strategy.trades),
            'final_capital': self.results['final_capital']
        }

    def print_summary(self):
        """백테스트 결과 요약 출력"""
        if not self.results:
            print("No results available. Run backtest first.")
            return

        metrics = self.calculate_metrics()

        print("\n" + "=" * 60)
        print(f"Backtest Summary: {self.strategy.name}")
        print("=" * 60)
        print(f"Stock Code      : {self.results['stock_code']}")
        print(f"Period          : {self.start_date} ~ {self.end_date}")
        print(f"Initial Capital : {self.initial_capital:,} KRW")
        print(f"Final Capital   : {self.results['final_capital']:,.0f} KRW")
        print(f"Total Return    : {metrics['total_return']:.2f}%")
        print(f"Sharpe Ratio    : {metrics['sharpe_ratio']:.2f}")
        print(f"Max Drawdown    : {metrics['max_drawdown']:.2f}%")
        print(f"Win Rate        : {metrics['win_rate']:.2f}%")
        print(f"Total Trades    : {metrics['total_trades']}")
        print("=" * 60 + "\n")
