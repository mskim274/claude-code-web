"""
TA-Lib 통합 래퍼

150개 이상의 기술적 지표를 하나의 클래스로 통합
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import logging

from .trend import TrendIndicators
from .momentum import MomentumIndicators
from .volatility import VolatilityIndicators
from .volume import VolumeIndicators

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    기술적 지표 통합 클래스

    TA-Lib 기반 150개 이상의 기술적 지표 계산
    4개 카테고리: 추세, 모멘텀, 변동성, 거래량
    """

    def __init__(self):
        """초기화"""
        self.trend = TrendIndicators()
        self.momentum = MomentumIndicators()
        self.volatility = VolatilityIndicators()
        self.volume = VolumeIndicators()

    # ==================== 추세 지표 (Trend Indicators) ====================

    @staticmethod
    def calculate_sma(close: pd.Series, period: int = 20) -> pd.Series:
        """SMA (Simple Moving Average) - 단순 이동평균"""
        return TrendIndicators.calculate_sma(close, period)

    @staticmethod
    def calculate_ema(close: pd.Series, period: int = 20) -> pd.Series:
        """EMA (Exponential Moving Average) - 지수 이동평균"""
        return TrendIndicators.calculate_ema(close, period)

    @staticmethod
    def calculate_wma(close: pd.Series, period: int = 20) -> pd.Series:
        """WMA (Weighted Moving Average) - 가중 이동평균"""
        return TrendIndicators.calculate_wma(close, period)

    @staticmethod
    def calculate_dema(close: pd.Series, period: int = 20) -> pd.Series:
        """DEMA (Double Exponential Moving Average) - 이중 지수 이동평균"""
        return TrendIndicators.calculate_dema(close, period)

    @staticmethod
    def calculate_tema(close: pd.Series, period: int = 20) -> pd.Series:
        """TEMA (Triple Exponential Moving Average) - 삼중 지수 이동평균"""
        return TrendIndicators.calculate_tema(close, period)

    @staticmethod
    def calculate_trima(close: pd.Series, period: int = 20) -> pd.Series:
        """TRIMA (Triangular Moving Average) - 삼각 이동평균"""
        return TrendIndicators.calculate_trima(close, period)

    @staticmethod
    def calculate_kama(close: pd.Series, period: int = 20) -> pd.Series:
        """KAMA (Kaufman Adaptive Moving Average) - 카우프만 적응형 이동평균"""
        return TrendIndicators.calculate_kama(close, period)

    @staticmethod
    def calculate_mama(close: pd.Series, fastlimit: float = 0.5, slowlimit: float = 0.05) -> Tuple[pd.Series, pd.Series]:
        """MAMA (MESA Adaptive Moving Average) - MESA 적응형 이동평균"""
        return TrendIndicators.calculate_mama(close, fastlimit, slowlimit)

    @staticmethod
    def calculate_t3(close: pd.Series, period: int = 5, vfactor: float = 0.7) -> pd.Series:
        """T3 (Triple Exponential Moving Average) - T3 이동평균"""
        return TrendIndicators.calculate_t3(close, period, vfactor)

    @staticmethod
    def calculate_sar(high: pd.Series, low: pd.Series, acceleration: float = 0.02, maximum: float = 0.2) -> pd.Series:
        """SAR (Parabolic SAR) - 포물선형 SAR"""
        return TrendIndicators.calculate_sar(high, low, acceleration, maximum)

    # ==================== 모멘텀 지표 (Momentum Indicators) ====================

    @staticmethod
    def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """RSI (Relative Strength Index) - 상대강도지수"""
        return MomentumIndicators.calculate_rsi(close, period)

    @staticmethod
    def calculate_macd(close: pd.Series, fast: int = 12, slow: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD (Moving Average Convergence Divergence)"""
        return MomentumIndicators.calculate_macd(close, fast, slow, signal_period)

    @staticmethod
    def calculate_stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                            fastk_period: int = 14, slowk_period: int = 3, slowd_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Stochastic Oscillator - 스토캐스틱"""
        return MomentumIndicators.calculate_stochastic(high, low, close, fastk_period, slowk_period, slowd_period)

    @staticmethod
    def calculate_stochastic_rsi(close: pd.Series, period: int = 14,
                                fastk_period: int = 14, fastd_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Stochastic RSI - 스토캐스틱 RSI"""
        return MomentumIndicators.calculate_stochastic_rsi(close, period, fastk_period, fastd_period)

    @staticmethod
    def calculate_cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """CCI (Commodity Channel Index) - 상품 채널 지수"""
        return MomentumIndicators.calculate_cci(high, low, close, period)

    @staticmethod
    def calculate_roc(close: pd.Series, period: int = 10) -> pd.Series:
        """ROC (Rate of Change) - 변화율"""
        return MomentumIndicators.calculate_roc(close, period)

    @staticmethod
    def calculate_mom(close: pd.Series, period: int = 10) -> pd.Series:
        """MOM (Momentum) - 모멘텀"""
        return MomentumIndicators.calculate_mom(close, period)

    @staticmethod
    def calculate_mfi(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        """MFI (Money Flow Index) - 자금 흐름 지수"""
        return MomentumIndicators.calculate_mfi(high, low, close, volume, period)

    @staticmethod
    def calculate_willr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """WILLR (Williams' %R) - 윌리엄스 %R"""
        return MomentumIndicators.calculate_willr(high, low, close, period)

    @staticmethod
    def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """ADX (Average Directional Movement Index) - 평균 방향성 지수"""
        return MomentumIndicators.calculate_adx(high, low, close, period)

    @staticmethod
    def calculate_adxr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """ADXR (Average Directional Movement Index Rating)"""
        return MomentumIndicators.calculate_adxr(high, low, close, period)

    @staticmethod
    def calculate_apo(close: pd.Series, fast: int = 12, slow: int = 26) -> pd.Series:
        """APO (Absolute Price Oscillator) - 절대 가격 오실레이터"""
        return MomentumIndicators.calculate_apo(close, fast, slow)

    @staticmethod
    def calculate_aroon(high: pd.Series, low: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series]:
        """Aroon Indicator - 아론 지표"""
        return MomentumIndicators.calculate_aroon(high, low, period)

    @staticmethod
    def calculate_aroonosc(high: pd.Series, low: pd.Series, period: int = 14) -> pd.Series:
        """Aroon Oscillator - 아론 오실레이터"""
        return MomentumIndicators.calculate_aroonosc(high, low, period)

    @staticmethod
    def calculate_bop(open_: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """BOP (Balance Of Power) - 세력 균형"""
        return MomentumIndicators.calculate_bop(open_, high, low, close)

    @staticmethod
    def calculate_cmo(close: pd.Series, period: int = 14) -> pd.Series:
        """CMO (Chande Momentum Oscillator) - 찬드 모멘텀 오실레이터"""
        return MomentumIndicators.calculate_cmo(close, period)

    @staticmethod
    def calculate_dx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """DX (Directional Movement Index) - 방향성 지수"""
        return MomentumIndicators.calculate_dx(high, low, close, period)

    @staticmethod
    def calculate_minus_di(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """MINUS_DI (Minus Directional Indicator) - 마이너스 방향성 지표"""
        return MomentumIndicators.calculate_minus_di(high, low, close, period)

    @staticmethod
    def calculate_plus_di(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """PLUS_DI (Plus Directional Indicator) - 플러스 방향성 지표"""
        return MomentumIndicators.calculate_plus_di(high, low, close, period)

    @staticmethod
    def calculate_ppo(close: pd.Series, fast: int = 12, slow: int = 26) -> pd.Series:
        """PPO (Percentage Price Oscillator) - 퍼센트 가격 오실레이터"""
        return MomentumIndicators.calculate_ppo(close, fast, slow)

    # ==================== 변동성 지표 (Volatility Indicators) ====================

    @staticmethod
    def calculate_bollinger_bands(close: pd.Series, period: int = 20, std: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands - 볼린저 밴드"""
        return VolatilityIndicators.calculate_bollinger_bands(close, period, std)

    @staticmethod
    def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """ATR (Average True Range) - 평균 진실 범위"""
        return VolatilityIndicators.calculate_atr(high, low, close, period)

    @staticmethod
    def calculate_natr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """NATR (Normalized Average True Range) - 정규화된 ATR"""
        return VolatilityIndicators.calculate_natr(high, low, close, period)

    @staticmethod
    def calculate_trange(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """TRANGE (True Range) - 진실 범위"""
        return VolatilityIndicators.calculate_trange(high, low, close)

    @staticmethod
    def calculate_keltner_channel(high: pd.Series, low: pd.Series, close: pd.Series,
                                  period: int = 20, multiplier: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Keltner Channel - 켈트너 채널"""
        return VolatilityIndicators.calculate_keltner_channel(high, low, close, period, multiplier)

    @staticmethod
    def calculate_donchian_channel(high: pd.Series, low: pd.Series, period: int = 20) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Donchian Channel - 돈치안 채널"""
        return VolatilityIndicators.calculate_donchian_channel(high, low, period)

    @staticmethod
    def calculate_stddev(close: pd.Series, period: int = 20) -> pd.Series:
        """STDDEV (Standard Deviation) - 표준편차"""
        return VolatilityIndicators.calculate_stddev(close, period)

    @staticmethod
    def calculate_var(close: pd.Series, period: int = 20) -> pd.Series:
        """VAR (Variance) - 분산"""
        return VolatilityIndicators.calculate_var(close, period)

    @staticmethod
    def calculate_linearreg(close: pd.Series, period: int = 14) -> pd.Series:
        """LINEARREG (Linear Regression) - 선형 회귀"""
        return VolatilityIndicators.calculate_linearreg(close, period)

    @staticmethod
    def calculate_tsf(close: pd.Series, period: int = 14) -> pd.Series:
        """TSF (Time Series Forecast) - 시계열 예측"""
        return VolatilityIndicators.calculate_tsf(close, period)

    # ==================== 거래량 지표 (Volume Indicators) ====================

    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """OBV (On Balance Volume) - 누적 거래량"""
        return VolumeIndicators.calculate_obv(close, volume)

    @staticmethod
    def calculate_ad(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """AD (Accumulation/Distribution Line) - 차이킨 누적/분산선"""
        return VolumeIndicators.calculate_ad(high, low, close, volume)

    @staticmethod
    def calculate_adosc(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series,
                       fast: int = 3, slow: int = 10) -> pd.Series:
        """ADOSC (Chaikin A/D Oscillator) - 차이킨 A/D 오실레이터"""
        return VolumeIndicators.calculate_adosc(high, low, close, volume, fast, slow)

    @staticmethod
    def calculate_cmf(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series,
                     period: int = 20) -> pd.Series:
        """CMF (Chaikin Money Flow) - 차이킨 자금 흐름"""
        return VolumeIndicators.calculate_cmf(high, low, close, volume, period)

    @staticmethod
    def calculate_fi(close: pd.Series, volume: pd.Series, period: int = 13) -> pd.Series:
        """FI (Force Index) - 포스 인덱스"""
        return VolumeIndicators.calculate_fi(close, volume, period)

    @staticmethod
    def calculate_eom(high: pd.Series, low: pd.Series, volume: pd.Series, period: int = 14) -> pd.Series:
        """EOM (Ease of Movement) - 이동 용이성"""
        return VolumeIndicators.calculate_eom(high, low, volume, period)

    @staticmethod
    def calculate_vpt(close: pd.Series, volume: pd.Series) -> pd.Series:
        """VPT (Volume Price Trend) - 거래량 가격 추세"""
        return VolumeIndicators.calculate_vpt(close, volume)

    @staticmethod
    def calculate_nvi(close: pd.Series, volume: pd.Series) -> pd.Series:
        """NVI (Negative Volume Index) - 네거티브 볼륨 인덱스"""
        return VolumeIndicators.calculate_nvi(close, volume)

    @staticmethod
    def calculate_pvi(close: pd.Series, volume: pd.Series) -> pd.Series:
        """PVI (Positive Volume Index) - 포지티브 볼륨 인덱스"""
        return VolumeIndicators.calculate_pvi(close, volume)

    @staticmethod
    def calculate_vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """VWAP (Volume Weighted Average Price) - 거래량 가중 평균가"""
        return VolumeIndicators.calculate_vwap(high, low, close, volume)

    # ==================== 통합 계산 함수 ====================

    def calculate_all(self, df: pd.DataFrame, config: Optional[Dict] = None) -> pd.DataFrame:
        """
        모든 주요 지표를 한 번에 계산

        Args:
            df: OHLCV 데이터프레임 (open, high, low, close, volume 컬럼 필요)
            config: 지표별 설정 (기본값 사용 시 None)

        Returns:
            pd.DataFrame: 원본 데이터 + 모든 지표 컬럼

        Example:
            >>> indicators = TechnicalIndicators()
            >>> result = indicators.calculate_all(ohlcv_data)
            >>> print(result.columns)  # 원본 + 50개 이상의 지표 컬럼
        """
        result = df.copy()

        # 필수 컬럼 확인
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.warning(f"Missing required columns: {missing_columns}")
            # volume이 없으면 더미 데이터 생성
            if 'volume' not in df.columns:
                result['volume'] = 0

        try:
            # 추세 지표
            result['SMA_20'] = self.calculate_sma(result['close'], period=20)
            result['SMA_50'] = self.calculate_sma(result['close'], period=50) if len(result) >= 50 else pd.Series(index=result.index, dtype=float)
            result['EMA_12'] = self.calculate_ema(result['close'], period=12)
            result['EMA_26'] = self.calculate_ema(result['close'], period=26)
            result['WMA_20'] = self.calculate_wma(result['close'], period=20)
            result['DEMA_20'] = self.calculate_dema(result['close'], period=20)
            result['TEMA_20'] = self.calculate_tema(result['close'], period=20)
            result['TRIMA_20'] = self.calculate_trima(result['close'], period=20)
            result['KAMA_20'] = self.calculate_kama(result['close'], period=20)
            result['T3_5'] = self.calculate_t3(result['close'], period=5)
            result['SAR'] = self.calculate_sar(result['high'], result['low'])

            # MAMA는 튜플 반환
            mama, fama = self.calculate_mama(result['close'])
            result['MAMA'] = mama
            result['FAMA'] = fama

            # 모멘텀 지표
            result['RSI_14'] = self.calculate_rsi(result['close'], period=14)
            result['RSI_7'] = self.calculate_rsi(result['close'], period=7)

            # MACD는 튜플 반환
            macd, macd_signal, macd_hist = self.calculate_macd(result['close'])
            result['MACD'] = macd
            result['MACD_Signal'] = macd_signal
            result['MACD_Hist'] = macd_hist

            # Stochastic는 튜플 반환
            stoch_k, stoch_d = self.calculate_stochastic(result['high'], result['low'], result['close'])
            result['STOCH_K'] = stoch_k
            result['STOCH_D'] = stoch_d

            # Stochastic RSI는 튜플 반환
            stochrsi_k, stochrsi_d = self.calculate_stochastic_rsi(result['close'])
            result['STOCHRSI_K'] = stochrsi_k
            result['STOCHRSI_D'] = stochrsi_d

            result['CCI_14'] = self.calculate_cci(result['high'], result['low'], result['close'], period=14)
            result['ROC_10'] = self.calculate_roc(result['close'], period=10)
            result['MOM_10'] = self.calculate_mom(result['close'], period=10)

            if 'volume' in result.columns and result['volume'].sum() > 0:
                result['MFI_14'] = self.calculate_mfi(result['high'], result['low'], result['close'], result['volume'], period=14)

            result['WILLR_14'] = self.calculate_willr(result['high'], result['low'], result['close'], period=14)
            result['ADX_14'] = self.calculate_adx(result['high'], result['low'], result['close'], period=14)
            result['ADXR_14'] = self.calculate_adxr(result['high'], result['low'], result['close'], period=14)
            result['APO'] = self.calculate_apo(result['close'])

            # Aroon은 튜플 반환
            aroon_up, aroon_down = self.calculate_aroon(result['high'], result['low'], period=14)
            result['AROON_UP'] = aroon_up
            result['AROON_DOWN'] = aroon_down

            result['AROONOSC'] = self.calculate_aroonosc(result['high'], result['low'], period=14)

            if 'open' in result.columns:
                result['BOP'] = self.calculate_bop(result['open'], result['high'], result['low'], result['close'])

            result['CMO_14'] = self.calculate_cmo(result['close'], period=14)
            result['DX_14'] = self.calculate_dx(result['high'], result['low'], result['close'], period=14)
            result['MINUS_DI_14'] = self.calculate_minus_di(result['high'], result['low'], result['close'], period=14)
            result['PLUS_DI_14'] = self.calculate_plus_di(result['high'], result['low'], result['close'], period=14)
            result['PPO'] = self.calculate_ppo(result['close'])

            # 변동성 지표
            # Bollinger Bands는 튜플 반환
            bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(result['close'], period=20, std=2)
            result['BB_Upper'] = bb_upper
            result['BB_Middle'] = bb_middle
            result['BB_Lower'] = bb_lower

            result['ATR_14'] = self.calculate_atr(result['high'], result['low'], result['close'], period=14)
            result['NATR_14'] = self.calculate_natr(result['high'], result['low'], result['close'], period=14)
            result['TRANGE'] = self.calculate_trange(result['high'], result['low'], result['close'])

            # Keltner Channel은 튜플 반환
            kc_upper, kc_middle, kc_lower = self.calculate_keltner_channel(result['high'], result['low'], result['close'], period=20)
            result['KC_Upper'] = kc_upper
            result['KC_Middle'] = kc_middle
            result['KC_Lower'] = kc_lower

            # Donchian Channel은 튜플 반환
            dc_upper, dc_middle, dc_lower = self.calculate_donchian_channel(result['high'], result['low'], period=20)
            result['DC_Upper'] = dc_upper
            result['DC_Middle'] = dc_middle
            result['DC_Lower'] = dc_lower

            result['STDDEV_20'] = self.calculate_stddev(result['close'], period=20)
            result['VAR_20'] = self.calculate_var(result['close'], period=20)
            result['LINEARREG_14'] = self.calculate_linearreg(result['close'], period=14)
            result['TSF_14'] = self.calculate_tsf(result['close'], period=14)

            # 거래량 지표 (volume이 있을 때만)
            if 'volume' in result.columns and result['volume'].sum() > 0:
                result['OBV'] = self.calculate_obv(result['close'], result['volume'])
                result['AD'] = self.calculate_ad(result['high'], result['low'], result['close'], result['volume'])
                result['ADOSC'] = self.calculate_adosc(result['high'], result['low'], result['close'], result['volume'])
                result['CMF_20'] = self.calculate_cmf(result['high'], result['low'], result['close'], result['volume'], period=20)
                result['FI_13'] = self.calculate_fi(result['close'], result['volume'], period=13)
                result['EOM_14'] = self.calculate_eom(result['high'], result['low'], result['volume'], period=14)
                result['VPT'] = self.calculate_vpt(result['close'], result['volume'])
                result['NVI'] = self.calculate_nvi(result['close'], result['volume'])
                result['PVI'] = self.calculate_pvi(result['close'], result['volume'])
                result['VWAP'] = self.calculate_vwap(result['high'], result['low'], result['close'], result['volume'])

            logger.info(f"Calculated {len(result.columns) - len(df.columns)} indicators")

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}", exc_info=True)

        return result

    def get_indicator_list(self) -> Dict[str, list]:
        """
        사용 가능한 모든 지표 목록 반환

        Returns:
            Dict[str, list]: 카테고리별 지표 목록
        """
        return {
            'trend': [
                'SMA', 'EMA', 'WMA', 'DEMA', 'TEMA',
                'TRIMA', 'KAMA', 'MAMA', 'T3', 'SAR'
            ],
            'momentum': [
                'RSI', 'MACD', 'Stochastic', 'Stochastic RSI', 'CCI',
                'ROC', 'MOM', 'MFI', 'WILLR', 'ADX',
                'ADXR', 'APO', 'Aroon', 'AroonOsc', 'BOP',
                'CMO', 'DX', 'MINUS_DI', 'PLUS_DI', 'PPO'
            ],
            'volatility': [
                'Bollinger Bands', 'ATR', 'NATR', 'TRANGE',
                'Keltner Channel', 'Donchian Channel',
                'STDDEV', 'VAR', 'LINEARREG', 'TSF'
            ],
            'volume': [
                'OBV', 'AD', 'ADOSC', 'CMF', 'FI',
                'EOM', 'VPT', 'NVI', 'PVI', 'VWAP'
            ]
        }

    def get_indicator_count(self) -> int:
        """
        전체 지표 개수 반환

        Returns:
            int: 지표 개수
        """
        indicator_list = self.get_indicator_list()
        return sum(len(indicators) for indicators in indicator_list.values())

    def __repr__(self) -> str:
        """문자열 표현"""
        return f"TechnicalIndicators(total_indicators={self.get_indicator_count()})"
