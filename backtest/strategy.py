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
        signals.loc[self.short_window:, 'signal'] = \
            (signals['short_ma'][self.short_window:] > signals['long_ma'][self.short_window:]).astype(int)

        # 포지션 변화 (1: 매수, -1: 매도)
        signals['positions'] = signals['signal'].diff()

        return signals


class RSIStrategy(BaseStrategy):
    """RSI 전략"""

    def __init__(self, rsi_period=14, oversold=30, overbought=70):
        """
        Args:
            rsi_period: RSI 계산 기간
            oversold: 과매도 기준선
            overbought: 과매수 기준선
        """
        super().__init__(name=f"RSI_{rsi_period}_{oversold}_{overbought}")
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought

    def calculate_rsi(self, prices, period=14):
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signals(self, data):
        """RSI 기반 신호 생성"""
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['close']
        signals['rsi'] = self.calculate_rsi(data['close'], self.rsi_period)

        # 신호 생성
        signals['signal'] = 0
        signals.loc[signals['rsi'] < self.oversold, 'signal'] = 1  # 매수
        signals.loc[signals['rsi'] > self.overbought, 'signal'] = -1  # 매도

        signals['positions'] = signals['signal'].diff()
        return signals


class BollingerBandsStrategy(BaseStrategy):
    """볼린저 밴드 전략"""

    def __init__(self, period=20, std_dev=2):
        """
        Args:
            period: 이동평균 기간
            std_dev: 표준편차 배수
        """
        super().__init__(name=f"BB_{period}_{std_dev}")
        self.period = period
        self.std_dev = std_dev

    def generate_signals(self, data):
        """볼린저 밴드 기반 신호 생성"""
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['close']

        # 볼린저 밴드 계산
        signals['middle_band'] = data['close'].rolling(window=self.period).mean()
        rolling_std = data['close'].rolling(window=self.period).std()
        signals['upper_band'] = signals['middle_band'] + (rolling_std * self.std_dev)
        signals['lower_band'] = signals['middle_band'] - (rolling_std * self.std_dev)

        # 신호 생성
        signals['signal'] = 0
        signals.loc[data['close'] < signals['lower_band'], 'signal'] = 1  # 하단 돌파 시 매수
        signals.loc[data['close'] > signals['upper_band'], 'signal'] = -1  # 상단 돌파 시 매도

        signals['positions'] = signals['signal'].diff()
        return signals
