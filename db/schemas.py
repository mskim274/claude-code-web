"""
Pydantic v2 스키마 정의
SQLAlchemy 모델과 호환되는 데이터 검증 스키마
"""

from __future__ import annotations
import datetime as dt
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from enum import Enum


# ==================== Enums ====================

class MarketType(str, Enum):
    """시장 구분"""
    KOSPI = "KOSPI"
    KOSDAQ = "KOSDAQ"


class CollectionStatus(str, Enum):
    """데이터 수집 상태"""
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


# ==================== Stock 스키마 ====================

class StockSchema(BaseModel):
    """종목 기본 정보 스키마

    종목코드, 종목명, 시장구분 등 종목의 기본 정보를 관리합니다.
    """

    code: str = Field(
        ...,
        min_length=6,
        max_length=10,
        description="종목코드 (6-10자리 숫자)"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="종목명"
    )
    market: MarketType = Field(
        ...,
        description="시장구분 (KOSPI 또는 KOSDAQ)"
    )
    sector: Optional[str] = Field(
        None,
        max_length=50,
        description="업종"
    )
    listing_date: Optional[dt.date] = Field(
        None,
        description="상장일"
    )
    created_at: Optional[dt.datetime] = Field(
        None,
        description="생성일시"
    )
    updated_at: Optional[dt.datetime] = Field(
        None,
        description="수정일시"
    )

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        str_strip_whitespace=True
    )

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """종목코드는 숫자만 허용"""
        if not v.isdigit():
            raise ValueError("종목코드는 숫자만 포함해야 합니다")
        return v


# ==================== DailyPrice 스키마 ====================

class DailyPriceSchema(BaseModel):
    """일봉 데이터 스키마

    일별 OHLCV(시가, 고가, 저가, 종가, 거래량) 데이터를 관리합니다.
    """

    id: Optional[int] = Field(
        None,
        description="고유 ID"
    )
    stock_code: str = Field(
        ...,
        min_length=6,
        max_length=10,
        description="종목코드"
    )
    date: dt.date = Field(
        ...,
        description="날짜"
    )
    open: int = Field(
        ...,
        ge=0,
        description="시가 (0 이상)"
    )
    high: int = Field(
        ...,
        ge=0,
        description="고가 (0 이상)"
    )
    low: int = Field(
        ...,
        ge=0,
        description="저가 (0 이상)"
    )
    close: int = Field(
        ...,
        ge=0,
        description="종가 (0 이상)"
    )
    volume: int = Field(
        ...,
        ge=0,
        description="거래량 (0 이상)"
    )
    trading_value: Optional[int] = Field(
        None,
        ge=0,
        description="거래대금"
    )
    change: Optional[int] = Field(
        None,
        description="전일대비"
    )
    change_rate: Optional[float] = Field(
        None,
        description="등락률 (%)"
    )
    adj_close: Optional[float] = Field(
        None,
        ge=0,
        description="수정종가"
    )
    adj_factor: Optional[float] = Field(
        None,
        ge=0,
        description="수정비율"
    )
    created_at: Optional[dt.datetime] = Field(
        None,
        description="생성일시"
    )

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )

    @model_validator(mode='after')
    def validate_prices(self):
        """OHLC 가격 검증: high >= close >= low, high >= open >= low"""
        # 고가는 저가 이상
        if self.high < self.low:
            raise ValueError("고가는 저가 이상이어야 합니다")

        # 종가는 저가 이상, 고가 이하
        if self.close < self.low:
            raise ValueError("종가는 저가 이상이어야 합니다")
        if self.close > self.high:
            raise ValueError("종가는 고가 이하여야 합니다")

        # 시가는 저가 이상, 고가 이하
        if self.open < self.low:
            raise ValueError("시가는 저가 이상이어야 합니다")
        if self.open > self.high:
            raise ValueError("시가는 고가 이하여야 합니다")

        return self


# ==================== MinutePrice 스키마 ====================

class MinutePriceSchema(BaseModel):
    """분봉 데이터 스키마

    분 단위 OHLCV 데이터를 관리합니다.
    지원 간격: 1, 3, 5, 10, 15, 30, 45, 60분
    """

    id: Optional[int] = Field(
        None,
        description="고유 ID"
    )
    stock_code: str = Field(
        ...,
        min_length=6,
        max_length=10,
        description="종목코드"
    )
    datetime: dt.datetime = Field(
        ...,
        description="일시"
    )
    interval: int = Field(
        ...,
        description="분봉 간격 (1, 3, 5, 10, 15, 30, 45, 60)"
    )
    open: int = Field(
        ...,
        ge=0,
        description="시가 (0 이상)"
    )
    high: int = Field(
        ...,
        ge=0,
        description="고가 (0 이상)"
    )
    low: int = Field(
        ...,
        ge=0,
        description="저가 (0 이상)"
    )
    close: int = Field(
        ...,
        ge=0,
        description="종가 (0 이상)"
    )
    volume: int = Field(
        ...,
        ge=0,
        description="거래량 (0 이상)"
    )
    created_at: Optional[dt.datetime] = Field(
        None,
        description="생성일시"
    )

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, v: int) -> int:
        """분봉 간격은 1, 3, 5, 10, 15, 30, 45, 60만 허용"""
        valid_intervals = [1, 3, 5, 10, 15, 30, 45, 60]
        if v not in valid_intervals:
            raise ValueError(
                f"분봉 간격은 {valid_intervals} 중 하나여야 합니다"
            )
        return v

    @model_validator(mode='after')
    def validate_prices(self):
        """OHLC 가격 검증: high >= close >= low, high >= open >= low"""
        # 고가는 저가 이상
        if self.high < self.low:
            raise ValueError("고가는 저가 이상이어야 합니다")

        # 종가는 저가 이상, 고가 이하
        if self.close < self.low:
            raise ValueError("종가는 저가 이상이어야 합니다")
        if self.close > self.high:
            raise ValueError("종가는 고가 이하여야 합니다")

        # 시가는 저가 이상, 고가 이하
        if self.open < self.low:
            raise ValueError("시가는 저가 이상이어야 합니다")
        if self.open > self.high:
            raise ValueError("시가는 고가 이하여야 합니다")

        return self


# ==================== TickPrice 스키마 ====================

class TickPriceSchema(BaseModel):
    """틱 데이터 스키마

    체결 단위의 실시간 가격 및 거래량 데이터를 관리합니다.
    """

    id: Optional[int] = Field(
        None,
        description="고유 ID"
    )
    stock_code: str = Field(
        ...,
        min_length=6,
        max_length=10,
        description="종목코드"
    )
    datetime: dt.datetime = Field(
        ...,
        description="체결시간"
    )
    price: int = Field(
        ...,
        ge=0,
        description="체결가 (0 이상)"
    )
    volume: int = Field(
        ...,
        ge=0,
        description="체결량 (0 이상)"
    )
    change: Optional[int] = Field(
        None,
        description="전일대비"
    )
    ask_volume: Optional[int] = Field(
        None,
        ge=0,
        description="매도잔량"
    )
    bid_volume: Optional[int] = Field(
        None,
        ge=0,
        description="매수잔량"
    )
    market_type: Optional[str] = Field(
        None,
        max_length=10,
        description="장구분 (장전, 장중, 장후)"
    )
    created_at: Optional[dt.datetime] = Field(
        None,
        description="생성일시"
    )

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )


# ==================== InvestorTrading 스키마 ====================

class InvestorTradingSchema(BaseModel):
    """투자자 매매 동향 스키마

    기관, 외국인, 개인 투자자별 매수/매도/순매수 데이터를 관리합니다.
    """

    id: Optional[int] = Field(
        None,
        description="고유 ID"
    )
    stock_code: str = Field(
        ...,
        min_length=6,
        max_length=10,
        description="종목코드"
    )
    date: dt.date = Field(
        ...,
        description="날짜"
    )

    # 기관
    institution_buy: int = Field(
        default=0,
        ge=0,
        description="기관 매수량"
    )
    institution_sell: int = Field(
        default=0,
        ge=0,
        description="기관 매도량"
    )
    institution_net: int = Field(
        default=0,
        description="기관 순매수 (음수 가능)"
    )

    # 외국인
    foreign_buy: int = Field(
        default=0,
        ge=0,
        description="외국인 매수량"
    )
    foreign_sell: int = Field(
        default=0,
        ge=0,
        description="외국인 매도량"
    )
    foreign_net: int = Field(
        default=0,
        description="외국인 순매수 (음수 가능)"
    )

    # 개인
    individual_buy: int = Field(
        default=0,
        ge=0,
        description="개인 매수량"
    )
    individual_sell: int = Field(
        default=0,
        ge=0,
        description="개인 매도량"
    )
    individual_net: int = Field(
        default=0,
        description="개인 순매수 (음수 가능)"
    )

    created_at: Optional[dt.datetime] = Field(
        None,
        description="생성일시"
    )

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )


# ==================== StockInfo 스키마 ====================

class StockInfoSchema(BaseModel):
    """종목 상세 정보 스키마

    시가총액, 재무지표(PER, PBR, ROE 등), 배당정보 등을 관리합니다.
    """

    stock_code: str = Field(
        ...,
        min_length=6,
        max_length=10,
        description="종목코드"
    )

    # 기본 정보
    market_cap: Optional[int] = Field(
        None,
        ge=0,
        description="시가총액"
    )
    shares_outstanding: Optional[int] = Field(
        None,
        ge=0,
        description="상장주식수"
    )
    par_value: Optional[int] = Field(
        None,
        ge=0,
        description="액면가"
    )

    # 재무 지표 (음수 허용 - 적자 기업의 경우)
    per: Optional[float] = Field(
        None,
        description="PER (주가수익비율)"
    )
    pbr: Optional[float] = Field(
        None,
        ge=0,
        description="PBR (주가순자산비율)"
    )
    roe: Optional[float] = Field(
        None,
        description="ROE (자기자본이익률)"
    )
    eps: Optional[int] = Field(
        None,
        description="EPS (주당순이익)"
    )
    bps: Optional[int] = Field(
        None,
        ge=0,
        description="BPS (주당순자산)"
    )

    # 배당 정보
    dividend_yield: Optional[float] = Field(
        None,
        ge=0,
        description="배당수익률 (%)"
    )
    dividend_per_share: Optional[int] = Field(
        None,
        ge=0,
        description="주당배당금"
    )

    # 거래 정보
    credit_ratio: Optional[float] = Field(
        None,
        ge=0,
        description="신용잔고율 (%)"
    )
    short_selling_ratio: Optional[float] = Field(
        None,
        ge=0,
        description="공매도비율 (%)"
    )

    # 52주 고저
    high_52w: Optional[int] = Field(
        None,
        ge=0,
        description="52주 최고가"
    )
    low_52w: Optional[int] = Field(
        None,
        ge=0,
        description="52주 최저가"
    )
    high_52w_date: Optional[dt.date] = Field(
        None,
        description="52주 최고가 날짜"
    )
    low_52w_date: Optional[dt.date] = Field(
        None,
        description="52주 최저가 날짜"
    )

    updated_at: Optional[dt.datetime] = Field(
        None,
        description="수정일시"
    )

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )


# ==================== CollectionLog 스키마 ====================

class CollectionLogSchema(BaseModel):
    """데이터 수집 로그 스키마

    데이터 수집 작업의 상태, 결과, 에러 메시지 등을 관리합니다.
    """

    id: Optional[int] = Field(
        None,
        description="고유 ID"
    )
    stock_code: Optional[str] = Field(
        None,
        min_length=6,
        max_length=10,
        description="종목코드 (전체 수집시 NULL)"
    )
    collection_type: str = Field(
        ...,
        max_length=20,
        description="수집 타입 (daily, minute, info 등)"
    )
    start_date: Optional[dt.date] = Field(
        None,
        description="수집 시작일"
    )
    end_date: Optional[dt.date] = Field(
        None,
        description="수집 종료일"
    )
    status: CollectionStatus = Field(
        ...,
        description="상태 (success, failed, in_progress)"
    )
    records_collected: int = Field(
        default=0,
        ge=0,
        description="수집된 레코드 수"
    )
    error_message: Optional[str] = Field(
        None,
        max_length=500,
        description="에러 메시지"
    )
    started_at: Optional[dt.datetime] = Field(
        None,
        description="수집 시작 시간"
    )
    completed_at: Optional[dt.datetime] = Field(
        None,
        description="수집 완료 시간"
    )

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
        str_strip_whitespace=True
    )
