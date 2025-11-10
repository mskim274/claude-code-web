"""
Pydantic Schemas Phase 2
API request/response schemas for Phase 2 models
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from datetime import date as DateType
from typing import Optional


# ===== Financial Statement Schemas =====

class FinancialStatementBase(BaseModel):
    """재무제표 기본 스키마"""
    corp_code: str = Field(..., min_length=8, max_length=8, description="고유번호")
    corp_name: str = Field(..., max_length=100, description="회사명")
    stock_code: str = Field(..., min_length=6, max_length=6, description="종목코드")
    year: int = Field(..., ge=1900, le=2100, description="사업연도")
    quarter: int = Field(..., ge=1, le=4, description="분기")
    report_type: Optional[str] = Field(None, max_length=10, description="보고서 코드")


class FinancialStatementCreate(FinancialStatementBase):
    """재무제표 생성 스키마"""
    revenue: Optional[int] = Field(None, description="매출액")
    operating_profit: Optional[int] = Field(None, description="영업이익")
    net_income: Optional[int] = Field(None, description="당기순이익")
    total_assets: Optional[int] = Field(None, description="자산총계")
    total_liabilities: Optional[int] = Field(None, description="부채총계")
    total_equity: Optional[int] = Field(None, description="자본총계")
    per: Optional[float] = Field(None, description="PER")
    pbr: Optional[float] = Field(None, description="PBR")
    roe: Optional[float] = Field(None, description="ROE (%)")
    debt_ratio: Optional[float] = Field(None, description="부채비율 (%)")
    operating_margin: Optional[float] = Field(None, description="영업이익률 (%)")
    net_margin: Optional[float] = Field(None, description="순이익률 (%)")
    market_cap: Optional[int] = Field(None, description="시가총액")


class FinancialStatementResponse(FinancialStatementCreate):
    """재무제표 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FinancialStatementUpdate(BaseModel):
    """재무제표 수정 스키마"""
    revenue: Optional[int] = None
    operating_profit: Optional[int] = None
    net_income: Optional[int] = None
    total_assets: Optional[int] = None
    total_liabilities: Optional[int] = None
    total_equity: Optional[int] = None
    per: Optional[float] = None
    pbr: Optional[float] = None
    roe: Optional[float] = None
    debt_ratio: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    market_cap: Optional[int] = None


# ===== Disclosure Schemas =====

class DisclosureBase(BaseModel):
    """공시 정보 기본 스키마"""
    rcept_no: str = Field(..., min_length=14, max_length=14, description="접수번호")
    corp_code: str = Field(..., min_length=8, max_length=8, description="고유번호")
    corp_name: str = Field(..., max_length=100, description="회사명")
    stock_code: Optional[str] = Field(None, min_length=6, max_length=6, description="종목코드")
    report_nm: str = Field(..., max_length=200, description="보고서명")
    rcept_dt: DateType = Field(..., description="접수일자")
    flr_nm: str = Field(..., max_length=100, description="공시제출인명")


class DisclosureCreate(DisclosureBase):
    """공시 정보 생성 스키마"""
    corp_cls: Optional[str] = Field(None, max_length=1, description="법인구분")
    rm: Optional[str] = Field(None, description="비고")


class DisclosureResponse(DisclosureCreate):
    """공시 정보 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DisclosureUpdate(BaseModel):
    """공시 정보 수정 스키마"""
    report_nm: Optional[str] = None
    flr_nm: Optional[str] = None
    corp_cls: Optional[str] = None
    rm: Optional[str] = None


# ===== Company Info Schemas =====

class CompanyInfoBase(BaseModel):
    """기업 정보 기본 스키마"""
    corp_code: str = Field(..., min_length=8, max_length=8, description="고유번호")
    corp_name: str = Field(..., max_length=100, description="정식회사명칭")
    stock_code: str = Field(..., min_length=6, max_length=6, description="종목코드")


class CompanyInfoCreate(CompanyInfoBase):
    """기업 정보 생성 스키마"""
    corp_name_eng: Optional[str] = Field(None, max_length=200, description="영문명칭")
    ceo_nm: Optional[str] = Field(None, max_length=100, description="대표자명")
    est_dt: Optional[str] = Field(None, min_length=8, max_length=8, description="설립일")
    jurir_no: Optional[str] = Field(None, max_length=13, description="법인등록번호")
    bizr_no: Optional[str] = Field(None, max_length=10, description="사업자등록번호")
    addr: Optional[str] = Field(None, max_length=500, description="주소")
    hm_url: Optional[str] = Field(None, max_length=200, description="홈페이지")
    ir_url: Optional[str] = Field(None, max_length=200, description="IR 홈페이지")
    phn_no: Optional[str] = Field(None, max_length=20, description="전화번호")
    fax_no: Optional[str] = Field(None, max_length=20, description="팩스번호")
    induty_code: Optional[str] = Field(None, max_length=10, description="업종코드")


class CompanyInfoResponse(CompanyInfoCreate):
    """기업 정보 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyInfoUpdate(BaseModel):
    """기업 정보 수정 스키마"""
    corp_name: Optional[str] = None
    corp_name_eng: Optional[str] = None
    ceo_nm: Optional[str] = None
    addr: Optional[str] = None
    hm_url: Optional[str] = None
    ir_url: Optional[str] = None
    phn_no: Optional[str] = None
    fax_no: Optional[str] = None


# ===== Overseas Stock Schemas =====

class OverseasStockBase(BaseModel):
    """해외주식 기본 스키마"""
    symbol: str = Field(..., max_length=20, description="심볼")
    name: str = Field(..., max_length=200, description="종목명")
    exchange: str = Field(..., max_length=20, description="거래소")


class OverseasStockCreate(OverseasStockBase):
    """해외주식 생성 스키마"""
    name_kr: Optional[str] = Field(None, max_length=200, description="한글명")
    exchange_code: Optional[str] = Field(None, max_length=10, description="거래소 코드")
    market: Optional[str] = Field(None, max_length=20, description="시장 구분")
    country: Optional[str] = Field(None, max_length=50, description="국가")
    country_code: Optional[str] = Field(None, max_length=3, description="국가 코드")
    currency: Optional[str] = Field(None, max_length=3, description="통화")
    sector: Optional[str] = Field(None, max_length=100, description="섹터")
    industry: Optional[str] = Field(None, max_length=100, description="산업")
    is_tradable: bool = Field(True, description="거래 가능 여부")


class OverseasStockResponse(OverseasStockCreate):
    """해외주식 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OverseasStockUpdate(BaseModel):
    """해외주식 수정 스키마"""
    name: Optional[str] = None
    name_kr: Optional[str] = None
    is_tradable: Optional[bool] = None
    sector: Optional[str] = None
    industry: Optional[str] = None


# ===== Overseas Price Schemas =====

class OverseasPriceBase(BaseModel):
    """해외주식 가격 기본 스키마"""
    symbol: str = Field(..., max_length=20, description="심볼")
    date: DateType = Field(..., description="거래일")
    close: float = Field(..., description="종가")


class OverseasPriceCreate(OverseasPriceBase):
    """해외주식 가격 생성 스키마"""
    open: Optional[float] = Field(None, description="시가")
    high: Optional[float] = Field(None, description="고가")
    low: Optional[float] = Field(None, description="저가")
    volume: Optional[int] = Field(None, description="거래량")
    value: Optional[int] = Field(None, description="거래대금")
    adj_close: Optional[float] = Field(None, description="조정종가")


class OverseasPriceResponse(OverseasPriceCreate):
    """해외주식 가격 응답 스키마"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class OverseasPriceUpdate(BaseModel):
    """해외주식 가격 수정 스키마"""
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[int] = None
    value: Optional[int] = None
    adj_close: Optional[float] = None


# ===== API Token Schemas =====

class APITokenBase(BaseModel):
    """API 토큰 기본 스키마"""
    api_name: str = Field(..., max_length=50, description="API 이름")
    token_type: str = Field(..., max_length=20, description="토큰 타입")
    token: str = Field(..., description="토큰 값")


class APITokenCreate(APITokenBase):
    """API 토큰 생성 스키마"""
    expires_at: Optional[datetime] = Field(None, description="만료일시")
    is_active: bool = Field(True, description="활성 여부")
    app_key: Optional[str] = Field(None, max_length=100, description="앱 키")
    app_secret: Optional[str] = Field(None, max_length=100, description="앱 시크릿")
    account_no: Optional[str] = Field(None, max_length=50, description="계좌번호")


class APITokenResponse(APITokenCreate):
    """API 토큰 응답 스키마"""
    id: int
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


class APITokenUpdate(BaseModel):
    """API 토큰 수정 스키마"""
    token: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    last_used_at: Optional[datetime] = None


# ===== List Response Schemas =====

class PaginatedResponse(BaseModel):
    """페이징 응답 기본 스키마"""
    total: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    pages: int = Field(..., description="전체 페이지 수")


class FinancialStatementListResponse(PaginatedResponse):
    """재무제표 목록 응답"""
    items: list[FinancialStatementResponse]


class DisclosureListResponse(PaginatedResponse):
    """공시 목록 응답"""
    items: list[DisclosureResponse]


class CompanyInfoListResponse(PaginatedResponse):
    """기업 정보 목록 응답"""
    items: list[CompanyInfoResponse]


class OverseasStockListResponse(PaginatedResponse):
    """해외주식 목록 응답"""
    items: list[OverseasStockResponse]


class OverseasPriceListResponse(PaginatedResponse):
    """해외주식 가격 목록 응답"""
    items: list[OverseasPriceResponse]
