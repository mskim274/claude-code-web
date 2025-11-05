"""
백테스팅 전략 베이스 클래스
"""

from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd


class BaseStrategy(ABC):
    """백테스팅 전략 베이스 클래스"""

    def __init__(self, name="BaseStrategy"):
        """
        전략 초기화

        Args:
            name: 전략 이름
        """
        self.name = name
        self.portfolio = {}  # {종목코드: 보유수량}
        self.cash = 10000000  # 초기 현금 (1천만원)
        self.initial_cash = self.cash
        self.trades = []  # 거래 내역

    @abstractmethod
    def generate_signals(self, data):
        """
        매매 신호 생성

        Args:
            data: pd.DataFrame - 주가 데이터

        Returns:
            pd.DataFrame: 신호 데이터 (컬럼: signal, 1=매수, -1=매도, 0=관망)
        """
        pass

    def buy(self, stock_code, price, quantity, date):
        """
        매수 실행

        Args:
            stock_code: 종목 코드
            price: 매수 가격
            quantity: 수량
            date: 날짜
        """
        cost = price * quantity
        if cost > self.cash:
            # 현금 부족
            return False

        self.cash -= cost
        self.portfolio[stock_code] = self.portfolio.get(stock_code, 0) + quantity

        self.trades.append({
            'date': date,
            'stock_code': stock_code,
            'action': 'BUY',
            'price': price,
            'quantity': quantity,
            'amount': cost
        })

        return True

    def sell(self, stock_code, price, quantity, date):
        """
        매도 실행

        Args:
            stock_code: 종목 코드
            price: 매도 가격
            quantity: 수량
            date: 날짜
        """
        if stock_code not in self.portfolio or self.portfolio[stock_code] < quantity:
            # 보유 수량 부족
            return False

        proceeds = price * quantity
        self.cash += proceeds
        self.portfolio[stock_code] -= quantity

        if self.portfolio[stock_code] == 0:
            del self.portfolio[stock_code]

        self.trades.append({
            'date': date,
            'stock_code': stock_code,
            'action': 'SELL',
            'price': price,
            'quantity': quantity,
            'amount': proceeds
        })

        return True

    def get_portfolio_value(self, current_prices):
        """
        현재 포트폴리오 가치 계산

        Args:
            current_prices: dict - {종목코드: 현재가}

        Returns:
            float: 총 자산 가치
        """
        stock_value = sum(
            current_prices.get(code, 0) * qty
            for code, qty in self.portfolio.items()
        )
        return self.cash + stock_value

    def get_performance(self):
        """
        성과 지표 계산

        Returns:
            dict: 성과 지표
        """
        total_return = (self.cash - self.initial_cash) / self.initial_cash * 100

        return {
            'initial_cash': self.initial_cash,
            'final_cash': self.cash,
            'total_return': total_return,
            'total_trades': len(self.trades),
            'buy_trades': len([t for t in self.trades if t['action'] == 'BUY']),
            'sell_trades': len([t for t in self.trades if t['action'] == 'SELL'])
        }


class MovingAverageCrossStrategy(BaseStrategy):
    """이동평균선 교차 전략 예시"""

    def __init__(self, short_window=20, long_window=60):
        """
        Args:
            short_window: 단기 이평선 기간
            long_window: 장기 이평선 기간
        """
        super().__init__(name=f"MA_Cross_{short_window}_{long_window}")
        self.short_window = short_window
        self.long_window = long_window

    def generate_signals(self, data):
        """
        골든크로스/데드크로스 신호 생성

        Args:
            data: pd.DataFrame with 'close' column

        Returns:
            pd.DataFrame: 신호 데이터
        """
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['close']

        # 이동평균선 계산
        signals['short_ma'] = data['close'].rolling(window=self.short_window).mean()
        signals['long_ma'] = data['close'].rolling(window=self.long_window).mean()

        # 신호 생성
        signals['signal'] = 0
        signals['signal'][self.short_window:] = \
            (signals['short_ma'][self.short_window:] > signals['long_ma'][self.short_window:]).astype(int)

        # 포지션 변화 (1: 매수, -1: 매도)
        signals['positions'] = signals['signal'].diff()

        return signals
