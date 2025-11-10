"""
Database Models Phase 2
Additional models for DART API and overseas stocks
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Text, ForeignKey, Boolean, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime

from db.database import Base


class FinancialStatement(Base):
    """
    재무제표 테이블
    DART API로부터 수집한 재무제표 데이터
    """
    __tablename__ = "financial_statements"

    id = Column(Integer, primary_key=True, index=True)

    # 기업 정보
    corp_code = Column(String(8), nullable=False, index=True, comment="고유번호")
    corp_name = Column(String(100), nullable=False, comment="회사명")
    stock_code = Column(String(6), nullable=False, index=True, comment="종목코드")

    # 기준 정보
    year = Column(Integer, nullable=False, index=True, comment="사업연도")
    quarter = Column(Integer, nullable=False, comment="분기 (1~4)")
    report_type = Column(String(10), comment="보고서 코드")

    # 손익계산서 (Income Statement)
    revenue = Column(BigInteger, comment="매출액 (원)")
    operating_profit = Column(BigInteger, comment="영업이익 (원)")
    net_income = Column(BigInteger, comment="당기순이익 (원)")

    # 재무상태표 (Balance Sheet)
    total_assets = Column(BigInteger, comment="자산총계 (원)")
    total_liabilities = Column(BigInteger, comment="부채총계 (원)")
    total_equity = Column(BigInteger, comment="자본총계 (원)")

    # 계산된 재무 지표
    per = Column(Float, comment="PER (주가수익비율)")
    pbr = Column(Float, comment="PBR (주가순자산비율)")
    roe = Column(Float, comment="ROE (자기자본이익률, %)")
    debt_ratio = Column(Float, comment="부채비율 (%)")
    operating_margin = Column(Float, comment="영업이익률 (%)")
    net_margin = Column(Float, comment="순이익률 (%)")

    # 메타 정보
    market_cap = Column(BigInteger, comment="시가총액 (원)")
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정일시")

    def __repr__(self):
        return f"<FinancialStatement {self.corp_name} {self.year}Q{self.quarter}>"


class Disclosure(Base):
    """
    공시 정보 테이블
    DART API로부터 수집한 공시 데이터
    """
    __tablename__ = "disclosures"

    id = Column(Integer, primary_key=True, index=True)

    # 공시 기본 정보
    rcept_no = Column(String(14), unique=True, nullable=False, index=True, comment="접수번호")
    corp_code = Column(String(8), nullable=False, index=True, comment="고유번호")
    corp_name = Column(String(100), nullable=False, comment="회사명")
    stock_code = Column(String(6), index=True, comment="종목코드")

    # 공시 내용
    report_nm = Column(String(200), nullable=False, comment="보고서명")
    rcept_dt = Column(Date, nullable=False, index=True, comment="접수일자")
    flr_nm = Column(String(100), comment="공시제출인명")

    # 추가 정보
    corp_cls = Column(String(1), comment="법인구분 (Y: 유가증권, K: 코스닥, N: 코넥스, E: 기타)")
    rm = Column(Text, comment="비고")

    # 메타 정보
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정일시")

    def __repr__(self):
        return f"<Disclosure {self.corp_name} - {self.report_nm}>"


class CompanyInfo(Base):
    """
    기업 상세정보 테이블
    DART API로부터 수집한 기업 개황
    """
    __tablename__ = "company_info"

    id = Column(Integer, primary_key=True, index=True)

    # 기본 식별 정보
    corp_code = Column(String(8), unique=True, nullable=False, index=True, comment="고유번호")
    corp_name = Column(String(100), nullable=False, index=True, comment="정식회사명칭")
    corp_name_eng = Column(String(200), comment="영문명칭")
    stock_code = Column(String(6), unique=True, index=True, comment="종목코드")

    # 대표자 및 설립 정보
    ceo_nm = Column(String(100), comment="대표자명")
    est_dt = Column(String(8), comment="설립일 (YYYYMMDD)")

    # 법인 정보
    jurir_no = Column(String(13), comment="법인등록번호")
    bizr_no = Column(String(10), comment="사업자등록번호")

    # 연락처
    addr = Column(String(500), comment="주소")
    hm_url = Column(String(200), comment="홈페이지")
    ir_url = Column(String(200), comment="IR 홈페이지")
    phn_no = Column(String(20), comment="전화번호")
    fax_no = Column(String(20), comment="팩스번호")

    # 업종 정보
    induty_code = Column(String(10), comment="업종코드")

    # 메타 정보
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정일시")

    def __repr__(self):
        return f"<CompanyInfo {self.corp_name} ({self.stock_code})>"


class OverseasStock(Base):
    """
    해외주식 기본정보 테이블
    한국투자증권 API로부터 수집한 해외 주식 정보
    """
    __tablename__ = "overseas_stocks"

    id = Column(Integer, primary_key=True, index=True)

    # 종목 정보
    symbol = Column(String(20), unique=True, nullable=False, index=True, comment="심볼 (e.g., AAPL)")
    name = Column(String(200), nullable=False, comment="종목명")
    name_kr = Column(String(200), comment="한글명")

    # 거래소 정보
    exchange = Column(String(20), nullable=False, index=True, comment="거래소 (NYSE, NASDAQ, etc.)")
    exchange_code = Column(String(10), comment="거래소 코드")
    market = Column(String(20), comment="시장 구분")

    # 국가 정보
    country = Column(String(50), comment="국가")
    country_code = Column(String(3), comment="국가 코드")
    currency = Column(String(3), comment="통화 (USD, EUR, etc.)")

    # 업종 정보
    sector = Column(String(100), comment="섹터")
    industry = Column(String(100), comment="산업")

    # 거래 가능 여부
    is_tradable = Column(Boolean, default=True, comment="거래 가능 여부")

    # 메타 정보
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정일시")

    # 관계
    prices = relationship("OverseasPrice", back_populates="stock", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<OverseasStock {self.symbol} - {self.name}>"


class OverseasPrice(Base):
    """
    해외주식 일봉 데이터 테이블
    한국투자증권 API로부터 수집한 해외 주식 가격 정보
    """
    __tablename__ = "overseas_prices"

    id = Column(Integer, primary_key=True, index=True)

    # 종목 참조
    symbol = Column(String(20), ForeignKey("overseas_stocks.symbol"), nullable=False, index=True, comment="심볼")

    # 날짜
    date = Column(Date, nullable=False, index=True, comment="거래일")

    # OHLCV 데이터
    open = Column(Float, comment="시가")
    high = Column(Float, comment="고가")
    low = Column(Float, comment="저가")
    close = Column(Float, nullable=False, comment="종가")
    volume = Column(BigInteger, comment="거래량")

    # 거래대금
    value = Column(BigInteger, comment="거래대금")

    # 조정 가격 (배당, 액면분할 등 반영)
    adj_close = Column(Float, comment="조정종가")

    # 메타 정보
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일시")

    # 관계
    stock = relationship("OverseasStock", back_populates="prices")

    def __repr__(self):
        return f"<OverseasPrice {self.symbol} {self.date}>"


class APIToken(Base):
    """
    API 토큰 관리 테이블
    각종 API의 인증 토큰 및 만료 정보 관리
    """
    __tablename__ = "api_tokens"

    id = Column(Integer, primary_key=True, index=True)

    # API 식별 정보
    api_name = Column(String(50), nullable=False, index=True, comment="API 이름 (KIS, DART, etc.)")
    token_type = Column(String(20), nullable=False, comment="토큰 타입 (access, refresh, api_key)")

    # 토큰 정보
    token = Column(Text, nullable=False, comment="토큰 값")

    # 만료 정보
    expires_at = Column(DateTime, comment="만료일시")
    is_active = Column(Boolean, default=True, index=True, comment="활성 여부")

    # 추가 정보
    app_key = Column(String(100), comment="앱 키")
    app_secret = Column(String(100), comment="앱 시크릿")
    account_no = Column(String(50), comment="계좌번호")

    # 메타 정보
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정일시")
    last_used_at = Column(DateTime, comment="마지막 사용일시")

    def __repr__(self):
        return f"<APIToken {self.api_name} - {self.token_type}>"
