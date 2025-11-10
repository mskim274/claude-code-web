---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Task, TodoWrite
description: Apply Cluefin features to Kiwoom backtest system with TDD approach
argument-hint: [phase_number (1-4) or 'all']
model: sonnet
---

# Cluefin 기능을 키움 백테스팅 시스템에 TDD 방식으로 적용

## 개요

이 프롬프트는 Cluefin 프로젝트의 우수 사례를 현재 키움증권 백테스팅 시스템에 단계별로 적용합니다.
모든 코드는 **Test-Driven Development (TDD)** 방식으로 작성하며, 각 Phase마다 전문 에이전트를 활용하여 품질을 보장합니다.

## 변수

### 동적 변수
- `$PHASE`: 적용할 Phase 번호 (1-4) 또는 'all' (기본값: '1')

### 정적 변수
- `PROJECT_ROOT`: c:\Users\andms\Desktop\kiwoom-auto\claude-code-web
- `TEST_DIR`: tests/
- `DOCS_DIR`: docs/
- `PYTHON_64`: venv\Scripts\python.exe
- `PYTHON_32`: C:\Python312-32\python.exe

## 지침

### 필수 원칙

1. **TDD 강제**: 모든 새 코드는 테스트 먼저 작성 (Red → Green → Refactor)
2. **전문 에이전트 활용**: 각 Phase마다 Task 도구로 전문 에이전트 생성
3. **병렬 처리 최적화**: 독립적인 작업은 병렬로 실행
4. **타입 안전성**: 모든 함수에 타입 힌트 필수
5. **문서화**: 모든 public API에 docstring 필수
6. **하이브리드 아키텍처 유지**: 64비트(메인) + 32비트(키움 API 서버) 구조 유지
7. **기존 기능 보존**: 현재 동작하는 기능은 절대 손상시키지 않음
8. **점진적 마이그레이션**: 기존 코드와 새 코드가 공존하도록 설계

### 테스트 요구사항

- **단위 테스트**: pytest로 모든 함수/클래스 테스트
- **통합 테스트**: 컴포넌트 간 상호작용 테스트
- **커버리지**: 최소 80% 이상
- **Mock 활용**: 외부 API(키움, KIS, DART)는 Mock 처리
- **CI/CD 준비**: GitHub Actions 워크플로우 생성

### 에러 처리

- 모든 Phase에서 에러 발생 시 즉시 중단하고 보고
- 롤백 전략 수립 (Git 브랜치 활용)
- 실패한 Phase는 재시도 가능하도록 멱등성 보장

## 프로젝트 구조

현재 프로젝트 구조:

```
claude-code-web/
├── collectors/              # 데이터 수집 (키움 API)
│   ├── kiwoom_api.py        # 키움 API 클라이언트 (64비트)
│   ├── kiwoom_api_server.py # 키움 API 서버 (32비트)
│   └── stock_collector.py   # 데이터 수집기
├── db/                      # 데이터베이스
│   ├── models.py            # SQLAlchemy 모델
│   └── database.py          # DB 연결
├── backtest/                # 백테스팅
│   ├── engine.py            # 백테스팅 엔진
│   └── strategy.py          # 전략
├── gui/                     # PyQt5 GUI
│   └── main_window.py
├── config/                  # 설정
├── scripts/                 # 실행 스크립트
├── requirements.txt         # 의존성 (64비트)
└── README.md
```

Phase 적용 후 목표 구조:

```
claude-code-web/
├── collectors/              # [유지] 데이터 수집
│   ├── apis/                # [신규] 통합 API 클라이언트
│   │   ├── kiwoom/          # 키움 API (기존 코드 이동)
│   │   ├── kis/             # [Phase 2] KIS API
│   │   ├── dart/            # [Phase 2] DART API
│   │   └── unified.py       # [Phase 2] 통합 인터페이스
│   └── stock_collector.py   # [유지] 데이터 수집기
├── db/                      # [확장] 데이터베이스
│   ├── models/              # [Phase 1] 모델 재구성
│   │   ├── stock.py         # SQLAlchemy + Pydantic
│   │   ├── price.py
│   │   └── schemas.py       # [Phase 1] Pydantic 스키마
│   └── database.py          # [유지]
├── backtest/                # [확장] 백테스팅
│   ├── indicators/          # [Phase 1] 기술적 지표
│   │   ├── talib_wrapper.py # TA-Lib 래퍼
│   │   └── custom.py        # 커스텀 지표
│   ├── strategies/          # [확장] 전략
│   │   ├── base.py          # 기본 전략
│   │   ├── ta_strategy.py   # [Phase 1] TA 기반 전략
│   │   └── ml_strategy.py   # [Phase 3] ML 기반 전략
│   ├── ml/                  # [Phase 3] 머신러닝
│   │   ├── models/          # LightGBM 모델
│   │   ├── features.py      # 피처 엔지니어링
│   │   └── explainer.py     # SHAP 설명
│   └── engine.py            # [유지] 백테스팅 엔진
├── gui/                     # [유지] PyQt5 GUI
├── cli/                     # [Phase 4] Rich CLI
│   ├── main.py              # CLI 진입점
│   ├── commands/            # CLI 명령어
│   └── display.py           # Rich 테이블/차트
├── tests/                   # [신규] 테스트 스위트
│   ├── unit/                # 단위 테스트
│   ├── integration/         # 통합 테스트
│   ├── e2e/                 # E2E 테스트
│   ├── conftest.py          # pytest 설정
│   └── fixtures/            # 테스트 픽스처
├── docs/                    # [신규] 문서
│   ├── api/                 # API 문서
│   ├── guides/              # 가이드
│   └── architecture.md      # 아키텍처 문서
├── .github/                 # [Phase 4] CI/CD
│   └── workflows/
│       └── test.yml
├── pyproject.toml           # [Phase 4] 통합 설정
├── pytest.ini               # [신규] pytest 설정
├── requirements.txt         # [확장] 의존성
└── requirements-dev.txt     # [신규] 개발 의존성
```

## 워크플로우

### Phase 1: 타입 안전성 + 기술적 지표 (2주)

**목표**: Pydantic 모델 도입 + TA-Lib 통합으로 코드 품질과 백테스팅 능력 향상

**종속성**: 없음 (첫 번째 Phase)
**실행 모드**: 혼합 (설계는 순차, 구현은 병렬)
**서브 에이전트 전략**:
- Agent 1: Pydantic 스키마 설계 및 구현 (TDD)
- Agent 2: TA-Lib 통합 및 지표 래퍼 구현 (TDD)
- Agent 3: 테스트 스위트 생성 (병렬)

#### 1.1 Phase 1 계획 수립 (순차적)

**작업**:
1. 현재 `db/models.py`의 SQLAlchemy 모델 분석
2. Pydantic 스키마 설계 (API 응답, 검증 규칙)
3. TA-Lib 통합 포인트 식별 (백테스팅 전략, 차트 뷰어)
4. 테스트 전략 수립 (Mock 데이터, 픽스처)
5. 작업 분해 및 우선순위 설정

**산출물**:
- `docs/phase1_plan.md`: Phase 1 상세 계획
- `tests/fixtures/sample_data.py`: 테스트용 샘플 데이터

**병렬 실행**: 불가 (계획 수립은 순차적)

#### 1.2 의존성 추가 (순차적)

**작업**:
1. requirements.txt에 새 패키지 추가
   - `pydantic==2.5.3`
   - `TA-Lib==0.4.28` (바이너리 설치 필요)
   - `pytest==7.4.3`
   - `pytest-cov==4.1.0`
   - `pytest-mock==3.12.0`
2. 가상환경에 설치
3. TA-Lib 바이너리 설치 (Windows용)

**명령**:
```bash
venv\Scripts\activate
pip install pydantic==2.5.3 pytest==7.4.3 pytest-cov==4.1.0 pytest-mock==3.12.0

# TA-Lib 바이너리 설치 (Windows)
pip install https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp312-cp312-win_amd64.whl
```

**병렬 실행**: 불가 (의존성 설치는 순차적)

#### 1.3 Pydantic 스키마 구현 (TDD, 병렬 가능)

**서브 에이전트**: Agent 1 (Pydantic 전문가)

**TDD 사이클**:

**Red (테스트 먼저)**:
```python
# tests/unit/test_schemas.py
import pytest
from datetime import date
from db.schemas import StockSchema, DailyPriceSchema

def test_stock_schema_validation():
    """종목 스키마 검증 테스트"""
    # 유효한 데이터
    valid_data = {
        "code": "005930",
        "name": "삼성전자",
        "market": "KOSPI"
    }
    stock = StockSchema(**valid_data)
    assert stock.code == "005930"
    assert stock.name == "삼성전자"

    # 잘못된 데이터 (종목코드 길이)
    with pytest.raises(ValueError):
        StockSchema(code="12345678901", name="테스트", market="KOSPI")

def test_daily_price_schema_validation():
    """일봉 데이터 스키마 검증 테스트"""
    valid_data = {
        "stock_code": "005930",
        "date": date(2024, 1, 1),
        "open": 70000,
        "high": 71000,
        "low": 69000,
        "close": 70500,
        "volume": 10000000
    }
    price = DailyPriceSchema(**valid_data)
    assert price.close > price.low
    assert price.high >= price.close

    # 잘못된 데이터 (음수 가격)
    with pytest.raises(ValueError):
        DailyPriceSchema(**{**valid_data, "close": -1000})
```

**Green (최소 구현)**:
```python
# db/schemas.py
from pydantic import BaseModel, Field, validator
from datetime import date
from typing import Optional

class StockSchema(BaseModel):
    """종목 정보 스키마 (Pydantic)"""
    code: str = Field(..., min_length=6, max_length=10, description="종목코드")
    name: str = Field(..., min_length=1, max_length=100, description="종목명")
    market: str = Field(..., pattern="^(KOSPI|KOSDAQ)$", description="시장구분")
    sector: Optional[str] = Field(None, max_length=50, description="업종")
    listing_date: Optional[date] = Field(None, description="상장일")

    class Config:
        orm_mode = True  # SQLAlchemy 모델과 호환

    @validator('code')
    def validate_code(cls, v):
        if not v.isdigit():
            raise ValueError('종목코드는 숫자만 가능합니다')
        return v

class DailyPriceSchema(BaseModel):
    """일봉 데이터 스키마 (Pydantic)"""
    stock_code: str = Field(..., min_length=6, max_length=10)
    date: date = Field(..., description="날짜")
    open: int = Field(..., ge=0, description="시가")
    high: int = Field(..., ge=0, description="고가")
    low: int = Field(..., ge=0, description="저가")
    close: int = Field(..., ge=0, description="종가")
    volume: int = Field(..., ge=0, description="거래량")
    trading_value: Optional[int] = Field(None, ge=0, description="거래대금")

    class Config:
        orm_mode = True

    @validator('high')
    def validate_high(cls, v, values):
        if 'low' in values and v < values['low']:
            raise ValueError('고가는 저가보다 높아야 합니다')
        return v

    @validator('close')
    def validate_close(cls, v, values):
        if 'low' in values and v < values['low']:
            raise ValueError('종가는 저가 이상이어야 합니다')
        if 'high' in values and v > values['high']:
            raise ValueError('종가는 고가 이하여야 합니다')
        return v
```

**Refactor (리팩토링)**:
- 중복 검증 로직을 유틸리티 함수로 추출
- 한국어 에러 메시지 국제화(i18n) 준비

**작업**:
1. `db/schemas.py` 파일 생성
2. 모든 SQLAlchemy 모델에 대응하는 Pydantic 스키마 작성:
   - StockSchema
   - DailyPriceSchema
   - MinutePriceSchema
   - TickPriceSchema
   - StockInfoSchema
3. 커스텀 validator 추가 (가격 범위, 날짜 검증 등)
4. SQLAlchemy 모델과 호환 (orm_mode=True)

**병렬 실행**: Agent 2(TA-Lib)와 병렬로 실행 가능

#### 1.4 TA-Lib 통합 (TDD, 병렬 가능)

**서브 에이전트**: Agent 2 (TA-Lib 전문가)

**TDD 사이클**:

**Red (테스트 먼저)**:
```python
# tests/unit/test_indicators.py
import pytest
import pandas as pd
import numpy as np
from backtest.indicators import TechnicalIndicators

@pytest.fixture
def sample_ohlcv():
    """테스트용 OHLCV 데이터"""
    return pd.DataFrame({
        'open': [100, 102, 101, 103, 105],
        'high': [105, 106, 104, 107, 108],
        'low': [99, 101, 100, 102, 104],
        'close': [102, 103, 102, 105, 107],
        'volume': [1000, 1100, 1050, 1200, 1300]
    })

def test_rsi_calculation(sample_ohlcv):
    """RSI 지표 계산 테스트"""
    indicators = TechnicalIndicators()
    rsi = indicators.calculate_rsi(sample_ohlcv['close'], period=14)

    assert isinstance(rsi, pd.Series)
    assert len(rsi) == len(sample_ohlcv)
    assert rsi.notna().any()  # 일부 값은 계산되어야 함
    assert (rsi >= 0).all() and (rsi <= 100).all()  # RSI는 0-100 범위

def test_macd_calculation(sample_ohlcv):
    """MACD 지표 계산 테스트"""
    indicators = TechnicalIndicators()
    macd, signal, hist = indicators.calculate_macd(sample_ohlcv['close'])

    assert isinstance(macd, pd.Series)
    assert isinstance(signal, pd.Series)
    assert isinstance(hist, pd.Series)
    assert len(macd) == len(sample_ohlcv)

def test_bollinger_bands(sample_ohlcv):
    """볼린저 밴드 계산 테스트"""
    indicators = TechnicalIndicators()
    upper, middle, lower = indicators.calculate_bollinger_bands(
        sample_ohlcv['close'], period=20, std=2
    )

    assert (upper >= middle).all()
    assert (middle >= lower).all()
```

**Green (최소 구현)**:
```python
# backtest/indicators/talib_wrapper.py
import talib
import pandas as pd
from typing import Tuple, Optional

class TechnicalIndicators:
    """기술적 지표 계산 (TA-Lib 래퍼)"""

    @staticmethod
    def calculate_rsi(close: pd.Series, period: int = 14) -> pd.Series:
        """RSI (Relative Strength Index) 계산

        Args:
            close: 종가 시리즈
            period: RSI 기간 (기본값: 14)

        Returns:
            RSI 값 (0-100)
        """
        return pd.Series(talib.RSI(close.values, timeperiod=period), index=close.index)

    @staticmethod
    def calculate_macd(
        close: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD (Moving Average Convergence Divergence) 계산

        Args:
            close: 종가 시리즈
            fast: 빠른 EMA 기간
            slow: 느린 EMA 기간
            signal: 시그널 기간

        Returns:
            (MACD, Signal, Histogram)
        """
        macd, signal_line, hist = talib.MACD(
            close.values,
            fastperiod=fast,
            slowperiod=slow,
            signalperiod=signal
        )
        return (
            pd.Series(macd, index=close.index),
            pd.Series(signal_line, index=close.index),
            pd.Series(hist, index=close.index)
        )

    @staticmethod
    def calculate_bollinger_bands(
        close: pd.Series,
        period: int = 20,
        std: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """볼린저 밴드 계산

        Args:
            close: 종가 시리즈
            period: 이동평균 기간
            std: 표준편차 배수

        Returns:
            (Upper Band, Middle Band, Lower Band)
        """
        upper, middle, lower = talib.BBANDS(
            close.values,
            timeperiod=period,
            nbdevup=std,
            nbdevdn=std
        )
        return (
            pd.Series(upper, index=close.index),
            pd.Series(middle, index=close.index),
            pd.Series(lower, index=close.index)
        )

    @classmethod
    def calculate_all(cls, df: pd.DataFrame) -> pd.DataFrame:
        """모든 주요 지표를 한 번에 계산

        Args:
            df: OHLCV 데이터프레임

        Returns:
            지표가 추가된 데이터프레임
        """
        result = df.copy()

        # 추세 지표
        result['SMA_20'] = talib.SMA(df['close'].values, timeperiod=20)
        result['EMA_20'] = talib.EMA(df['close'].values, timeperiod=20)

        # 모멘텀 지표
        result['RSI_14'] = cls.calculate_rsi(df['close'], period=14)
        macd, signal, hist = cls.calculate_macd(df['close'])
        result['MACD'] = macd
        result['MACD_Signal'] = signal
        result['MACD_Hist'] = hist

        # 변동성 지표
        upper, middle, lower = cls.calculate_bollinger_bands(df['close'])
        result['BB_Upper'] = upper
        result['BB_Middle'] = middle
        result['BB_Lower'] = lower
        result['ATR_14'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)

        # 거래량 지표
        result['OBV'] = talib.OBV(df['close'].values, df['volume'].values)

        return result
```

**Refactor**:
- 150개 TA-Lib 지표를 카테고리별로 분류 (추세, 모멘텀, 변동성, 거래량)
- 지표별 설명 및 파라미터 문서화

**작업**:
1. `backtest/indicators/talib_wrapper.py` 생성
2. 주요 150개 지표 래퍼 함수 작성:
   - 추세: SMA, EMA, WMA, DEMA, TEMA
   - 모멘텀: RSI, MACD, Stochastic, CCI, ROC
   - 변동성: Bollinger Bands, ATR, Keltner Channel
   - 거래량: OBV, AD, ADOSC
3. 통합 계산 함수 `calculate_all()` 구현
4. 에러 처리 (데이터 부족, NaN 처리)

**병렬 실행**: Agent 1(Pydantic)과 병렬로 실행 가능

#### 1.5 백테스팅 전략에 지표 통합 (순차적)

**종속성**: 1.3, 1.4 완료 후

**TDD 사이클**:

**Red (테스트 먼저)**:
```python
# tests/integration/test_ta_strategy.py
import pytest
from backtest.strategies import RSIStrategy
from backtest.engine import BacktestEngine
from db.models import DailyPrice

def test_rsi_strategy_signals(sample_stock_data):
    """RSI 전략 시그널 생성 테스트"""
    strategy = RSIStrategy(rsi_period=14, oversold=30, overbought=70)
    signals = strategy.generate_signals(sample_stock_data)

    assert 'signal' in signals.columns
    assert signals['signal'].isin([1, 0, -1]).all()  # 매수(1), 중립(0), 매도(-1)

def test_rsi_strategy_backtest(sample_stock_data):
    """RSI 전략 백테스팅 테스트"""
    engine = BacktestEngine(initial_capital=10000000)
    strategy = RSIStrategy(rsi_period=14, oversold=30, overbought=70)

    result = engine.run(strategy, sample_stock_data)

    assert result['final_value'] > 0
    assert 'total_return' in result
    assert 'sharpe_ratio' in result
    assert 'max_drawdown' in result
```

**Green (최소 구현)**:
```python
# backtest/strategies/ta_strategy.py
from backtest.strategy import BaseStrategy
from backtest.indicators import TechnicalIndicators
import pandas as pd

class RSIStrategy(BaseStrategy):
    """RSI 기반 백테스팅 전략

    전략 로직:
    - RSI < oversold: 매수 시그널
    - RSI > overbought: 매도 시그널
    """

    def __init__(self, rsi_period: int = 14, oversold: int = 30, overbought: int = 70):
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.indicators = TechnicalIndicators()

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """매매 시그널 생성

        Args:
            data: OHLCV 데이터

        Returns:
            시그널이 추가된 데이터프레임 (1: 매수, 0: 중립, -1: 매도)
        """
        df = data.copy()

        # RSI 계산
        df['RSI'] = self.indicators.calculate_rsi(df['close'], period=self.rsi_period)

        # 시그널 생성
        df['signal'] = 0
        df.loc[df['RSI'] < self.oversold, 'signal'] = 1   # 과매도 → 매수
        df.loc[df['RSI'] > self.overbought, 'signal'] = -1 # 과매수 → 매도

        return df

    def calculate_position_size(self, capital: float, price: float) -> int:
        """포지션 크기 계산 (주문 수량)"""
        return int(capital * 0.1 / price)  # 자본의 10%

class MACDStrategy(BaseStrategy):
    """MACD 크로스오버 전략"""

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.indicators = TechnicalIndicators()

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()

        # MACD 계산
        df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = self.indicators.calculate_macd(
            df['close'], fast=self.fast, slow=self.slow, signal=self.signal
        )

        # 시그널 생성 (MACD가 시그널선을 상향/하향 돌파)
        df['signal'] = 0
        df['MACD_Diff'] = df['MACD'] - df['MACD_Signal']
        df['MACD_Diff_Prev'] = df['MACD_Diff'].shift(1)

        # 골든 크로스 (상향 돌파)
        df.loc[(df['MACD_Diff'] > 0) & (df['MACD_Diff_Prev'] <= 0), 'signal'] = 1

        # 데드 크로스 (하향 돌파)
        df.loc[(df['MACD_Diff'] < 0) & (df['MACD_Diff_Prev'] >= 0), 'signal'] = -1

        return df
```

**작업**:
1. `backtest/strategies/ta_strategy.py` 생성
2. 주요 전략 구현:
   - RSIStrategy
   - MACDStrategy
   - BollingerBandsStrategy
   - MultiIndicatorStrategy (복합 전략)
3. 기존 `backtest/strategy.py`의 BaseStrategy 확장
4. GUI에 새 전략 추가

**병렬 실행**: 불가 (통합은 순차적)

#### 1.6 테스트 실행 및 검증 (순차적)

**종속성**: 모든 Phase 1 작업 완료

**작업**:
1. 전체 테스트 실행
   ```bash
   pytest tests/ -v --cov=. --cov-report=html
   ```
2. 커버리지 확인 (80% 이상)
3. 타입 체크
   ```bash
   mypy db/schemas.py backtest/indicators/
   ```
4. 코드 품질 검사
   ```bash
   flake8 db/schemas.py backtest/indicators/
   black db/schemas.py backtest/indicators/ --check
   ```

**완료 기준**:
- [ ] 모든 테스트 통과 (pytest)
- [ ] 코드 커버리지 80% 이상
- [ ] 타입 체크 통과 (mypy)
- [ ] 기존 기능 정상 동작 (GUI 실행 테스트)
- [ ] TA-Lib 지표 150개 사용 가능
- [ ] Pydantic 스키마로 데이터 검증 가능

**병렬 실행**: 불가 (최종 검증은 순차적)

---

### Phase 2: 다중 API 통합 (1개월)

**목표**: KIS API + DART API 추가하여 해외주식, 재무제표 데이터 수집 가능

**종속성**: Phase 1 완료
**실행 모드**: 혼합
**서브 에이전트 전략**:
- Agent 1: KIS API 클라이언트 구현 (TDD)
- Agent 2: DART API 클라이언트 구현 (TDD)
- Agent 3: 통합 인터페이스 설계 및 구현

#### 2.1 Phase 2 계획 수립

**작업**:
1. KIS OpenAPI 문서 조사 (WebSearch)
2. DART OpenAPI 문서 조사 (WebSearch)
3. 통합 인터페이스 설계 (Unified API)
4. 데이터베이스 스키마 확장 계획
5. 테스트 전략 (Mock API 응답)

**산출물**:
- `docs/phase2_plan.md`
- `docs/api_comparison.md`: 키움 vs KIS vs DART API 비교표

#### 2.2 KIS API 클라이언트 구현 (TDD, 병렬)

**서브 에이전트**: Agent 1 (KIS API 전문가)

**TDD 사이클**:

**Red (테스트 먼저)**:
```python
# tests/unit/test_kis_api.py
import pytest
from collectors.apis.kis import KISAPIClient

@pytest.fixture
def kis_client(mocker):
    """Mock KIS API 클라이언트"""
    client = KISAPIClient(app_key="test", app_secret="test")
    # OAuth 토큰 발급 Mock
    mocker.patch.object(client, '_get_access_token', return_value="mock_token")
    return client

def test_kis_get_stock_price(kis_client, mocker):
    """KIS API 주가 조회 테스트"""
    mock_response = {
        "output": {
            "stck_prpr": "70000",  # 현재가
            "stck_oprc": "69500",  # 시가
            "stck_hgpr": "70500",  # 고가
            "stck_lwpr": "69000",  # 저가
        }
    }
    mocker.patch.object(kis_client, '_request', return_value=mock_response)

    price = kis_client.get_stock_price("005930")

    assert price['close'] == 70000
    assert price['open'] == 69500

def test_kis_get_overseas_stock(kis_client, mocker):
    """KIS API 해외주식 조회 테스트"""
    mock_response = {
        "output": {
            "last": "150.25",  # 현재가 (USD)
            "open": "149.50",
        }
    }
    mocker.patch.object(kis_client, '_request', return_value=mock_response)

    price = kis_client.get_overseas_stock("AAPL", exchange="NASDAQ")

    assert price['symbol'] == "AAPL"
    assert price['close'] == 150.25
```

**Green (최소 구현)**:
```python
# collectors/apis/kis/client.py
import requests
from typing import Dict, Optional
from pydantic import BaseModel

class KISAPIClient:
    """한국투자증권 OpenAPI 클라이언트"""

    BASE_URL = "https://openapi.koreainvestment.com:9443"

    def __init__(self, app_key: str, app_secret: str, account: Optional[str] = None):
        self.app_key = app_key
        self.app_secret = app_secret
        self.account = account
        self.access_token = None

    def _get_access_token(self) -> str:
        """OAuth 토큰 발급"""
        url = f"{self.BASE_URL}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        data = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }

        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        self.access_token = response.json()['access_token']
        return self.access_token

    def _request(self, endpoint: str, tr_id: str, params: Dict) -> Dict:
        """KIS API 요청"""
        if not self.access_token:
            self._get_access_token()

        url = f"{self.BASE_URL}{endpoint}"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        return response.json()

    def get_stock_price(self, code: str) -> Dict:
        """국내주식 현재가 조회

        Args:
            code: 종목코드 (6자리)

        Returns:
            {"open": int, "high": int, "low": int, "close": int, "volume": int}
        """
        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"
        tr_id = "FHKST01010100"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": code
        }

        result = self._request(endpoint, tr_id, params)
        output = result['output']

        return {
            "code": code,
            "open": int(output['stck_oprc']),
            "high": int(output['stck_hgpr']),
            "low": int(output['stck_lwpr']),
            "close": int(output['stck_prpr']),
            "volume": int(output.get('acml_vol', 0))
        }

    def get_overseas_stock(self, symbol: str, exchange: str = "NASDAQ") -> Dict:
        """해외주식 현재가 조회

        Args:
            symbol: 티커 심볼 (예: AAPL, TSLA)
            exchange: 거래소 (NASDAQ, NYSE, AMEX 등)

        Returns:
            {"symbol": str, "close": float, "currency": str}
        """
        endpoint = "/uapi/overseas-price/v1/quotations/price"
        tr_id = "HHDFS00000300"

        exchange_codes = {
            "NASDAQ": "NAS",
            "NYSE": "NYS",
            "AMEX": "AMS"
        }

        params = {
            "AUTH": "",
            "EXCD": exchange_codes.get(exchange, "NAS"),
            "SYMB": symbol
        }

        result = self._request(endpoint, tr_id, params)
        output = result['output']

        return {
            "symbol": symbol,
            "exchange": exchange,
            "close": float(output['last']),
            "open": float(output.get('open', 0)),
            "currency": "USD"
        }
```

**작업**:
1. `collectors/apis/kis/` 디렉토리 생성
2. KIS API 주요 기능 구현:
   - OAuth 인증
   - 국내주식 시세 조회
   - 해외주식 시세 조회 (미국, 중국, 일본)
   - 계좌 조회
3. Pydantic 스키마로 응답 검증
4. Rate Limiting 구현

**병렬 실행**: Agent 2(DART)와 병렬 가능

#### 2.3 DART API 클라이언트 구현 (TDD, 병렬)

**서브 에이전트**: Agent 2 (DART API 전문가)

**TDD 사이클**:

**Red (테스트 먼저)**:
```python
# tests/unit/test_dart_api.py
import pytest
from collectors.apis.dart import DARTAPIClient

@pytest.fixture
def dart_client(mocker):
    """Mock DART API 클라이언트"""
    client = DARTAPIClient(api_key="test_key")
    return client

def test_dart_get_company_info(dart_client, mocker):
    """DART API 기업 기본정보 조회 테스트"""
    mock_response = {
        "status": "000",
        "corp_name": "삼성전자",
        "corp_code": "00126380",
        "stock_code": "005930"
    }
    mocker.patch('requests.get', return_value=mocker.Mock(
        json=lambda: mock_response,
        raise_for_status=lambda: None
    ))

    info = dart_client.get_company_info("005930")

    assert info['corp_name'] == "삼성전자"
    assert info['stock_code'] == "005930"

def test_dart_get_financial_statement(dart_client, mocker):
    """DART API 재무제표 조회 테스트"""
    mock_response = {
        "status": "000",
        "list": [
            {
                "account_nm": "자산총계",
                "thstrm_amount": "1000000000000"  # 1조원
            },
            {
                "account_nm": "매출액",
                "thstrm_amount": "500000000000"  # 5000억원
            }
        ]
    }
    mocker.patch('requests.get', return_value=mocker.Mock(
        json=lambda: mock_response,
        raise_for_status=lambda: None
    ))

    fs = dart_client.get_financial_statement("00126380", year=2023, quarter=4)

    assert len(fs) > 0
    assert fs[0]['account_nm'] == "자산총계"
```

**Green (최소 구현)**:
```python
# collectors/apis/dart/client.py
import requests
from typing import Dict, List, Optional
from datetime import date

class DARTAPIClient:
    """DART(전자공시) OpenAPI 클라이언트"""

    BASE_URL = "https://opendart.fss.or.kr/api"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _request(self, endpoint: str, params: Dict) -> Dict:
        """DART API 요청"""
        url = f"{self.BASE_URL}/{endpoint}.json"
        params['crtfc_key'] = self.api_key

        response = requests.get(url, params=params)
        response.raise_for_status()

        result = response.json()

        if result['status'] != '000':
            raise Exception(f"DART API Error: {result.get('message', 'Unknown error')}")

        return result

    def get_company_info(self, stock_code: str) -> Dict:
        """기업 기본정보 조회

        Args:
            stock_code: 종목코드 (6자리)

        Returns:
            기업 정보 딕셔너리
        """
        # 먼저 종목코드로 고유번호(corp_code) 조회
        corp_code = self._get_corp_code(stock_code)

        endpoint = "company"
        params = {"corp_code": corp_code}

        result = self._request(endpoint, params)
        result['stock_code'] = stock_code

        return result

    def _get_corp_code(self, stock_code: str) -> str:
        """종목코드로 고유번호 조회"""
        # DART CORPCODE.xml 다운로드 및 파싱 (별도 구현 필요)
        # 여기서는 간소화
        pass

    def get_financial_statement(
        self,
        corp_code: str,
        year: int,
        quarter: int = 4,
        report_type: str = "11011"  # 사업보고서
    ) -> List[Dict]:
        """재무제표 조회

        Args:
            corp_code: 고유번호 (8자리)
            year: 사업연도
            quarter: 분기 (1~4)
            report_type: 보고서 종류

        Returns:
            재무제표 항목 리스트
        """
        endpoint = "fnlttSinglAcntAll"
        params = {
            "corp_code": corp_code,
            "bsns_year": str(year),
            "reprt_code": self._get_report_code(quarter)
        }

        result = self._request(endpoint, params)
        return result.get('list', [])

    def _get_report_code(self, quarter: int) -> str:
        """분기별 보고서 코드"""
        codes = {1: "11013", 2: "11012", 3: "11014", 4: "11011"}
        return codes.get(quarter, "11011")

    def get_disclosure_list(
        self,
        corp_code: str,
        start_date: date,
        end_date: date
    ) -> List[Dict]:
        """공시 목록 조회

        Args:
            corp_code: 고유번호
            start_date: 시작일
            end_date: 종료일

        Returns:
            공시 목록
        """
        endpoint = "list"
        params = {
            "corp_code": corp_code,
            "bgn_de": start_date.strftime("%Y%m%d"),
            "end_de": end_date.strftime("%Y%m%d")
        }

        result = self._request(endpoint, params)
        return result.get('list', [])
```

**작업**:
1. `collectors/apis/dart/` 디렉토리 생성
2. DART API 주요 기능 구현:
   - 기업 기본정보
   - 재무제표 (연간, 분기)
   - 공시 목록
   - CORPCODE.xml 파싱
3. 재무 지표 계산 (PER, PBR, ROE 등)
4. 데이터베이스 스키마 확장 (financial_statements 테이블)

**병렬 실행**: Agent 1(KIS)와 병렬 가능

#### 2.4 통합 API 인터페이스 구현 (순차적)

**종속성**: 2.2, 2.3 완료 후

**서브 에이전트**: Agent 3 (아키텍처 전문가)

**작업**:
1. `collectors/apis/unified.py` 생성
2. 통합 인터페이스 설계:
   ```python
   class UnifiedAPIClient:
       def __init__(self):
           self.kiwoom = KiwoomAPI()
           self.kis = KISAPIClient()
           self.dart = DARTAPIClient()

       def get_stock_price(self, code: str, source: str = "kiwoom") -> Dict:
           """통합 주가 조회"""
           if source == "kiwoom":
               return self.kiwoom.get_stock_price(code)
           elif source == "kis":
               return self.kis.get_stock_price(code)

       def get_financial_data(self, code: str) -> Dict:
           """재무 데이터 조회 (DART)"""
           return self.dart.get_financial_statement(code)
   ```
3. GUI에 데이터 소스 선택 옵션 추가
4. 백테스팅에 재무 지표 활용 전략 추가

**병렬 실행**: 불가 (통합은 순차적)

#### 2.5 테스트 및 검증

**완료 기준**:
- [ ] KIS API 국내/해외 주식 조회 가능
- [ ] DART API 재무제표 조회 가능
- [ ] 통합 인터페이스로 다중 소스 접근 가능
- [ ] 모든 테스트 통과
- [ ] 코드 커버리지 80% 이상

---

### Phase 3: 머신러닝 예측 엔진 (2개월)

**목표**: LightGBM + SHAP으로 AI 기반 백테스팅 전략 구현

**종속성**: Phase 1, 2 완료 (TA-Lib 지표 + 재무 데이터 필요)
**실행 모드**: 혼합
**서브 에이전트 전략**:
- Agent 1: 피처 엔지니어링 (기술적 지표 + 재무 지표)
- Agent 2: LightGBM 모델 학습 및 최적화
- Agent 3: SHAP 설명 기능 구현
- Agent 4: GUI에 ML 탭 추가

#### 3.1 Phase 3 계획 수립

**작업**:
1. ML 파이프라인 설계
2. 피처 선정 (기술적 지표, 재무 지표, 투자자 매매 동향 등)
3. 타겟 변수 정의 (다음 날 수익률, 상승/하락 분류 등)
4. 학습 데이터 수집 전략
5. 모델 평가 지표 (Accuracy, F1, Sharpe Ratio 등)

**산출물**:
- `docs/phase3_plan.md`
- `docs/ml_features.md`: 피처 목록 및 설명

#### 3.2 피처 엔지니어링 (TDD, 병렬)

**서브 에이전트**: Agent 1 (피처 엔지니어링 전문가)

**TDD 사이클**:

**Red (테스트)**:
```python
# tests/unit/test_features.py
def test_technical_features(sample_ohlcv):
    """기술적 지표 피처 생성 테스트"""
    features = FeatureEngineer()
    result = features.create_technical_features(sample_ohlcv)

    assert 'RSI_14' in result.columns
    assert 'MACD' in result.columns
    assert 'BB_width' in result.columns  # 볼린저 밴드 폭

def test_financial_features(sample_financial_data):
    """재무 지표 피처 생성 테스트"""
    features = FeatureEngineer()
    result = features.create_financial_features(sample_financial_data)

    assert 'PER' in result.columns
    assert 'ROE' in result.columns
    assert 'debt_ratio' in result.columns
```

**Green (구현)**:
```python
# backtest/ml/features.py
class FeatureEngineer:
    """머신러닝 피처 생성"""

    def create_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 피처 생성"""
        result = df.copy()

        # TA-Lib 지표 추가
        indicators = TechnicalIndicators()
        result = indicators.calculate_all(result)

        # 커스텀 피처
        result['price_change_1d'] = result['close'].pct_change(1)
        result['price_change_5d'] = result['close'].pct_change(5)
        result['volume_change'] = result['volume'].pct_change(1)

        # 볼린저 밴드 폭
        result['BB_width'] = (result['BB_Upper'] - result['BB_Lower']) / result['BB_Middle']

        return result

    def create_target(self, df: pd.DataFrame, horizon: int = 1) -> pd.Series:
        """타겟 변수 생성 (다음 날 수익률)"""
        return df['close'].pct_change(horizon).shift(-horizon)
```

**작업**:
1. `backtest/ml/features.py` 생성
2. 피처 생성 함수 작성 (50개 이상 피처)
3. 피처 선택 (Correlation, Feature Importance)
4. 데이터 정규화/스케일링

**병렬 실행**: Agent 2(모델 학습)와 병렬 가능

#### 3.3 LightGBM 모델 구현 (TDD, 병렬)

**서브 에이전트**: Agent 2 (ML 모델 전문가)

**TDD 사이클**:

**Red**:
```python
# tests/unit/test_ml_model.py
def test_lightgbm_training(sample_features, sample_target):
    """LightGBM 모델 학습 테스트"""
    model = LightGBMPredictor()
    model.train(sample_features, sample_target)

    assert model.is_trained
    assert model.model is not None

def test_lightgbm_prediction(trained_model, sample_features):
    """LightGBM 예측 테스트"""
    predictions = trained_model.predict(sample_features)

    assert len(predictions) == len(sample_features)
    assert predictions.dtype == float
```

**Green**:
```python
# backtest/ml/models/lightgbm_model.py
import lightgbm as lgb
import numpy as np

class LightGBMPredictor:
    """LightGBM 기반 주가 예측 모델"""

    def __init__(self, params: Optional[Dict] = None):
        self.params = params or {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9
        }
        self.model = None
        self.feature_names = None

    def train(self, X: pd.DataFrame, y: pd.Series,
              validation_split: float = 0.2):
        """모델 학습"""
        # Train/Validation 분할
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # LightGBM Dataset 생성
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

        # 학습
        self.model = lgb.train(
            self.params,
            train_data,
            num_boost_round=1000,
            valid_sets=[val_data],
            early_stopping_rounds=50,
            verbose_eval=100
        )

        self.feature_names = X.columns.tolist()
        self.is_trained = True

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """예측"""
        if not self.is_trained:
            raise ValueError("모델이 학습되지 않았습니다")

        return self.model.predict(X)

    def get_feature_importance(self) -> pd.DataFrame:
        """피처 중요도 조회"""
        importance = self.model.feature_importance()
        return pd.DataFrame({
            'feature': self.feature_names,
            'importance': importance
        }).sort_values('importance', ascending=False)
```

**작업**:
1. `backtest/ml/models/` 디렉토리 생성
2. LightGBM 모델 구현
3. 하이퍼파라미터 튜닝 (Optuna)
4. 모델 저장/로드 기능

**병렬 실행**: Agent 1(피처)과 병렬 가능

#### 3.4 SHAP 설명 기능 (TDD, 순차)

**종속성**: 3.3 완료 후

**서브 에이전트**: Agent 3 (XAI 전문가)

**TDD 사이클**:

**Red**:
```python
# tests/unit/test_explainer.py
def test_shap_explanation(trained_model, sample_features):
    """SHAP 설명 생성 테스트"""
    explainer = SHAPExplainer(trained_model)
    shap_values = explainer.explain(sample_features)

    assert shap_values.shape == sample_features.shape
```

**Green**:
```python
# backtest/ml/explainer.py
import shap
import matplotlib.pyplot as plt

class SHAPExplainer:
    """SHAP 기반 모델 설명"""

    def __init__(self, model: LightGBMPredictor):
        self.model = model
        self.explainer = shap.TreeExplainer(model.model)

    def explain(self, X: pd.DataFrame) -> np.ndarray:
        """SHAP 값 계산"""
        return self.explainer.shap_values(X)

    def plot_summary(self, X: pd.DataFrame, save_path: Optional[str] = None):
        """SHAP 요약 플롯"""
        shap_values = self.explain(X)
        shap.summary_plot(shap_values, X, show=False)

        if save_path:
            plt.savefig(save_path)
        else:
            plt.show()

    def plot_waterfall(self, X: pd.DataFrame, index: int):
        """특정 예측에 대한 SHAP Waterfall 플롯"""
        shap_values = self.explain(X.iloc[[index]])
        shap.waterfall_plot(
            shap.Explanation(
                values=shap_values[0],
                base_values=self.explainer.expected_value,
                data=X.iloc[index],
                feature_names=X.columns.tolist()
            )
        )
```

**작업**:
1. `backtest/ml/explainer.py` 생성
2. SHAP 시각화 함수 작성
3. GUI에 SHAP 플롯 통합

**병렬 실행**: 불가 (모델 학습 후 실행)

#### 3.5 ML 백테스팅 전략 구현

**TDD 사이클**:

**Red**:
```python
# tests/integration/test_ml_strategy.py
def test_ml_strategy_backtest(sample_stock_data):
    """ML 전략 백테스팅 테스트"""
    strategy = MLStrategy(
        model_path="models/lightgbm_model.txt",
        threshold=0.02  # 2% 이상 상승 예측 시 매수
    )

    engine = BacktestEngine(initial_capital=10000000)
    result = engine.run(strategy, sample_stock_data)

    assert result['final_value'] > 0
    assert 'ml_accuracy' in result
```

**Green**:
```python
# backtest/strategies/ml_strategy.py
class MLStrategy(BaseStrategy):
    """머신러닝 기반 백테스팅 전략"""

    def __init__(self, model_path: str, threshold: float = 0.02):
        self.model = LightGBMPredictor()
        self.model.load(model_path)
        self.threshold = threshold
        self.feature_engineer = FeatureEngineer()
        self.explainer = SHAPExplainer(self.model)

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """ML 예측 기반 시그널 생성"""
        df = data.copy()

        # 피처 생성
        features = self.feature_engineer.create_technical_features(df)
        features = features.dropna()

        # 예측
        predictions = self.model.predict(features)
        df.loc[features.index, 'predicted_return'] = predictions

        # 시그널 생성
        df['signal'] = 0
        df.loc[df['predicted_return'] > self.threshold, 'signal'] = 1   # 매수
        df.loc[df['predicted_return'] < -self.threshold, 'signal'] = -1  # 매도

        # SHAP 값 저장 (설명용)
        shap_values = self.explainer.explain(features)
        df.loc[features.index, 'shap_top_feature'] = self._get_top_shap_feature(
            shap_values, features.columns
        )

        return df

    def _get_top_shap_feature(self, shap_values, feature_names):
        """가장 영향이 큰 피처 추출"""
        abs_shap = np.abs(shap_values)
        top_indices = np.argmax(abs_shap, axis=1)
        return [feature_names[i] for i in top_indices]
```

**작업**:
1. `backtest/strategies/ml_strategy.py` 생성
2. ML 기반 전략 구현
3. 백테스팅 결과에 설명 추가

#### 3.6 GUI에 ML 탭 추가

**서브 에이전트**: Agent 4 (GUI 전문가)

**작업**:
1. `gui/widgets/ml_tab.py` 생성
2. ML 모델 학습 UI
   - 피처 선택
   - 하이퍼파라미터 설정
   - 학습 진행률
3. ML 백테스팅 UI
   - 모델 선택
   - 예측 차트
   - SHAP 플롯 표시
4. 모델 관리 UI (저장/로드)

#### 3.7 테스트 및 검증

**완료 기준**:
- [ ] LightGBM 모델 학습 가능
- [ ] SHAP으로 예측 근거 설명 가능
- [ ] ML 백테스팅 전략 동작
- [ ] GUI에서 ML 기능 사용 가능
- [ ] 모든 테스트 통과

---

### Phase 4: Rich CLI + 모노레포 리팩토링 (1개월)

**목표**: Rich 기반 CLI 추가 + 프로젝트 구조 모노레포로 리팩토링

**종속성**: Phase 1, 2, 3 완료
**실행 모드**: 혼합
**서브 에이전트 전략**:
- Agent 1: Rich CLI 구현
- Agent 2: 모노레포 구조 설계 및 마이그레이션
- Agent 3: CI/CD 파이프라인 구축

#### 4.1 Phase 4 계획 수립

**작업**:
1. CLI 명령어 설계
2. 모노레포 구조 설계 (uv workspace)
3. 마이그레이션 계획 (기존 코드 이동)
4. CI/CD 파이프라인 설계

**산출물**:
- `docs/phase4_plan.md`
- `docs/cli_commands.md`: CLI 명령어 목록

#### 4.2 Rich CLI 구현 (TDD, 병렬)

**서브 에이전트**: Agent 1 (CLI 전문가)

**TDD 사이클**:

**Red**:
```python
# tests/unit/test_cli.py
from click.testing import CliRunner
from cli.main import cli

def test_cli_backtest_command():
    """CLI 백테스팅 명령 테스트"""
    runner = CliRunner()
    result = runner.invoke(cli, ['backtest', '--code', '005930', '--strategy', 'rsi'])

    assert result.exit_code == 0
    assert '백테스팅 완료' in result.output
```

**Green**:
```python
# cli/main.py
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress

console = Console()

@click.group()
def cli():
    """키움 백테스팅 시스템 CLI"""
    pass

@cli.command()
@click.option('--code', required=True, help='종목코드')
@click.option('--strategy', default='rsi', help='전략 (rsi, macd, ml)')
@click.option('--start', help='시작일 (YYYYMMDD)')
@click.option('--end', help='종료일 (YYYYMMDD)')
def backtest(code, strategy, start, end):
    """백테스팅 실행"""
    console.print(f"[bold green]백테스팅 시작: {code}[/bold green]")

    # 백테스팅 엔진 실행
    with Progress() as progress:
        task = progress.add_task("[cyan]백테스팅 중...", total=100)

        # ... 백테스팅 로직 ...

        progress.update(task, advance=100)

    # 결과 테이블 표시
    table = Table(title="백테스팅 결과")
    table.add_column("지표", style="cyan")
    table.add_column("값", style="green")

    table.add_row("최종 수익률", "+15.3%")
    table.add_row("Sharpe Ratio", "1.25")
    table.add_row("MDD", "-8.5%")

    console.print(table)

@cli.command()
@click.option('--market', default='all', help='시장 (kospi, kosdaq, all)')
def collect(market):
    """데이터 수집"""
    console.print(f"[bold blue]데이터 수집 시작: {market}[/bold blue]")

    with Progress() as progress:
        task = progress.add_task("[cyan]수집 중...", total=2500)

        # ... 데이터 수집 로직 ...

        progress.update(task, advance=2500)

    console.print("[bold green]✓ 데이터 수집 완료[/bold green]")

if __name__ == '__main__':
    cli()
```

**작업**:
1. `cli/` 디렉토리 생성
2. Click + Rich로 CLI 구현
3. 주요 명령어:
   - `backtest`: 백테스팅 실행
   - `collect`: 데이터 수집
   - `analyze`: 종목 분석
   - `train`: ML 모델 학습
   - `predict`: ML 예측
4. Rich 테이블, 차트, 진행률 바 활용

**병렬 실행**: Agent 2(모노레포)와 병렬 가능

#### 4.3 모노레포 구조 마이그레이션 (순차)

**서브 에이전트**: Agent 2 (아키텍처 전문가)

**작업**:
1. `pyproject.toml` 생성 (uv workspace 설정)
2. 디렉토리 재구성:
   ```
   kiwoom-auto/
   ├── packages/
   │   ├── kiwoom-api/
   │   ├── kis-api/
   │   ├── dart-api/
   │   └── technical-indicators/
   ├── apps/
   │   ├── gui/
   │   └── cli/
   └── pyproject.toml
   ```
3. 기존 코드 이동
4. 의존성 통합 관리
5. 공통 라이브러리 추출

**병렬 실행**: Agent 1(CLI)과 병렬 가능 (충돌 없음)

#### 4.4 CI/CD 파이프라인 구축 (순차)

**종속성**: 4.2, 4.3 완료 후

**서브 에이전트**: Agent 3 (DevOps 전문가)

**작업**:
1. `.github/workflows/test.yml` 생성
2. GitHub Actions 워크플로우:
   - Python 3.12 64비트 + 32비트 설치
   - 의존성 설치
   - pytest 실행
   - 코드 커버리지 리포트
3. Pre-commit hooks 설정:
   - black (포매팅)
   - flake8 (린팅)
   - mypy (타입 체크)

**병렬 실행**: 불가 (통합 후 실행)

#### 4.5 테스트 및 검증

**완료 기준**:
- [ ] Rich CLI 모든 명령어 동작
- [ ] 모노레포 구조로 마이그레이션 완료
- [ ] CI/CD 파이프라인 동작
- [ ] 모든 테스트 통과
- [ ] GUI와 CLI 모두 정상 동작

---

## 테스트 스위트 생성

### 단위 테스트 (병렬 실행 가능)

#### Phase 1 테스트
- `tests/unit/test_schemas.py`: Pydantic 스키마 검증
- `tests/unit/test_indicators.py`: TA-Lib 지표 계산
- `tests/unit/test_ta_strategy.py`: TA 전략 로직

#### Phase 2 테스트
- `tests/unit/test_kis_api.py`: KIS API 클라이언트
- `tests/unit/test_dart_api.py`: DART API 클라이언트
- `tests/unit/test_unified_api.py`: 통합 API

#### Phase 3 테스트
- `tests/unit/test_features.py`: 피처 엔지니어링
- `tests/unit/test_ml_model.py`: LightGBM 모델
- `tests/unit/test_explainer.py`: SHAP 설명

#### Phase 4 테스트
- `tests/unit/test_cli.py`: CLI 명령어
- `tests/unit/test_display.py`: Rich 디스플레이

**병렬 실행 전략**:
```python
# pytest.ini
[pytest]
addopts = -n auto  # pytest-xdist로 병렬 실행
```

### 통합 테스트 (일부 순차)

#### Phase 1 통합 테스트
- `tests/integration/test_ta_backtest.py`: TA 전략 백테스팅 (순차)
- `tests/integration/test_indicator_strategy.py`: 지표와 전략 통합

#### Phase 2 통합 테스트
- `tests/integration/test_multi_api_collection.py`: 다중 API 데이터 수집
- `tests/integration/test_financial_backtest.py`: 재무 지표 백테스팅

#### Phase 3 통합 테스트
- `tests/integration/test_ml_pipeline.py`: ML 파이프라인 전체
- `tests/integration/test_ml_backtest.py`: ML 백테스팅

#### Phase 4 통합 테스트
- `tests/integration/test_cli_workflow.py`: CLI 워크플로우
- `tests/integration/test_gui_cli_compatibility.py`: GUI-CLI 호환성

### E2E 테스트 (순차 실행 필수)

- `tests/e2e/test_full_backtest_workflow.py`: 데이터 수집 → 백테스팅 → 결과 출력
- `tests/e2e/test_ml_training_workflow.py`: 피처 생성 → 모델 학습 → 백테스팅
- `tests/e2e/test_multi_strategy_comparison.py`: 여러 전략 비교

**순차 실행 이유**: 데이터베이스 상태 공유, 파일 I/O 충돌 방지

### 엣지 케이스 테스트

- 종목코드 없음
- 데이터 기간 부족
- API 타임아웃
- 잘못된 파라미터
- 메모리 부족 (대량 데이터)
- 32비트 서버 연결 실패

### 검증 명령

#### Phase 1 검증
```bash
# 테스트 실행
pytest tests/unit/test_schemas.py -v
pytest tests/unit/test_indicators.py -v
pytest tests/integration/test_ta_backtest.py -v

# 커버리지
pytest tests/ --cov=db.schemas --cov=backtest.indicators --cov-report=html

# 타입 체크
mypy db/schemas.py backtest/indicators/

# 코드 품질
flake8 db/schemas.py backtest/indicators/
black db/schemas.py backtest/indicators/ --check
```

#### Phase 2 검증
```bash
pytest tests/unit/test_kis_api.py tests/unit/test_dart_api.py -v
pytest tests/integration/test_multi_api_collection.py -v
mypy collectors/apis/
```

#### Phase 3 검증
```bash
pytest tests/unit/test_ml_model.py tests/unit/test_explainer.py -v
pytest tests/integration/test_ml_pipeline.py -v
mypy backtest/ml/
```

#### Phase 4 검증
```bash
pytest tests/unit/test_cli.py -v
pytest tests/e2e/ -v
mypy cli/
```

#### 전체 검증 (CI/CD)
```bash
# 전체 테스트 (병렬)
pytest tests/ -n auto --cov=. --cov-report=html --cov-report=term

# 커버리지 확인 (80% 이상)
coverage report --fail-under=80

# 타입 체크 (전체)
mypy .

# 코드 품질
flake8 .
black . --check
```

### 최종 품질 보증

#### 완료 기준 (모든 Phase 완료 후)

**기능 완료**:
- [ ] Phase 1: Pydantic + TA-Lib 완료
- [ ] Phase 2: KIS + DART API 완료
- [ ] Phase 3: LightGBM + SHAP 완료
- [ ] Phase 4: Rich CLI + 모노레포 완료

**테스트 통과**:
- [ ] 모든 단위 테스트 통과
- [ ] 모든 통합 테스트 통과
- [ ] 모든 E2E 테스트 통과
- [ ] 코드 커버리지 80% 이상

**코드 품질**:
- [ ] mypy 타입 체크 통과
- [ ] flake8 린팅 통과
- [ ] black 포매팅 완료

**기존 기능 보존**:
- [ ] GUI 정상 동작 (로그인, 데이터 수집, 백테스팅)
- [ ] 하이브리드 아키텍처 유지 (64비트 + 32비트)
- [ ] 기존 데이터베이스 호환성

**문서화**:
- [ ] API 문서 생성 (Sphinx)
- [ ] README 업데이트
- [ ] 아키텍처 문서 작성
- [ ] 각 Phase 문서화

**CI/CD**:
- [ ] GitHub Actions 워크플로우 동작
- [ ] Pre-commit hooks 설정 완료

---

## 최종 결과물

### 코드
- 모든 Phase의 구현 코드 (TDD 방식)
- 포괄적인 테스트 스위트 (단위, 통합, E2E)
- Rich CLI 애플리케이션
- 확장된 GUI (ML 탭 포함)

### 문서
- `docs/phase1_plan.md` ~ `docs/phase4_plan.md`: 각 Phase 계획
- `docs/architecture.md`: 전체 아키텍처 문서
- `docs/api/`: API 문서 (Sphinx)
- `docs/guides/`: 사용 가이드

### 인프라
- `.github/workflows/test.yml`: CI/CD 파이프라인
- `pyproject.toml`: 통합 프로젝트 설정
- `pytest.ini`: pytest 설정
- `.pre-commit-config.yaml`: Pre-commit hooks

### 데이터
- 확장된 데이터베이스 스키마 (재무제표, ML 예측 등)
- 학습된 ML 모델 (`models/lightgbm_*.txt`)

---

## 보고서

각 Phase 완료 시 다음 정보를 사용자에게 보고:

1. **완료된 작업**:
   - 생성된 파일 목록 (파일 경로 포함)
   - 추가된 기능 요약
   - 작성된 테스트 수

2. **테스트 결과**:
   - 통과한 테스트 수 / 전체 테스트 수
   - 코드 커버리지 (%)
   - 실패한 테스트 (있을 경우)

3. **다음 단계**:
   - 다음 Phase 소개
   - 필요한 사전 작업
   - 예상 소요 시간

4. **사용 방법**:
   - 새로운 기능 사용 예시
   - CLI 명령어 (해당 시)
   - GUI 조작 방법 (해당 시)

### 최종 보고서 (모든 Phase 완료)

**프로젝트 개요**:
- 시작일/종료일
- 총 소요 시간
- 커밋 수

**구현 통계**:
- 추가된 파일: XX개
- 추가된 코드 라인: XXXX줄
- 작성된 테스트: XXX개
- 코드 커버리지: XX%

**주요 성과**:
- Pydantic으로 타입 안전성 확보
- TA-Lib 150개 지표 활용 가능
- KIS + DART API로 다중 데이터 소스 확보
- LightGBM + SHAP으로 AI 백테스팅 구현
- Rich CLI로 사용자 경험 개선
- 모노레포 구조로 코드 관리 개선

**벤치마크**:
- 백테스팅 속도: X배 향상
- ML 예측 정확도: XX%
- 테스트 커버리지: XX% → XX%

**향후 개선 사항**:
- 실시간 트레이딩 기능
- 웹 대시보드 (FastAPI + React)
- 더 많은 ML 모델 (XGBoost, LSTM)
- 포트폴리오 최적화 (Markowitz, Black-Litterman)
