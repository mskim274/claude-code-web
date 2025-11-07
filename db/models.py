"""
Database models for stock data
"""

from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey, Index, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Stock(Base):
    """종목 기본 정보"""
    __tablename__ = 'stocks'

    code = Column(String(10), primary_key=True, comment='종목코드')
    name = Column(String(100), nullable=False, comment='종목명')
    market = Column(String(10), nullable=False, comment='시장구분 (KOSPI/KOSDAQ)')
    sector = Column(String(50), comment='업종')
    listing_date = Column(Date, comment='상장일')

    created_at = Column(DateTime, default=lambda: datetime.now(), comment='생성일시')
    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now(), comment='수정일시')

    # Relationships
    daily_prices = relationship("DailyPrice", back_populates="stock", cascade="all, delete-orphan")
    minute_prices = relationship("MinutePrice", back_populates="stock", cascade="all, delete-orphan")
    stock_info = relationship("StockInfo", back_populates="stock", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Stock(code={self.code}, name={self.name}, market={self.market})>"


class DailyPrice(Base):
    """일별 주가 데이터 (OHLCV)"""
    __tablename__ = 'daily_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), ForeignKey('stocks.code'), nullable=False, comment='종목코드')
    date = Column(Date, nullable=False, comment='날짜')

    open = Column(Integer, nullable=False, comment='시가')
    high = Column(Integer, nullable=False, comment='고가')
    low = Column(Integer, nullable=False, comment='저가')
    close = Column(Integer, nullable=False, comment='종가')
    volume = Column(BigInteger, nullable=False, comment='거래량')
    trading_value = Column(BigInteger, comment='거래대금')

    # 추가 지표
    change = Column(Integer, comment='전일대비')
    change_rate = Column(Float, comment='등락률 (%)')

    # 수정주가 관련
    adj_close = Column(Float, comment='수정종가')
    adj_factor = Column(Float, default=1.0, comment='수정비율')

    created_at = Column(DateTime, default=lambda: datetime.now(), comment='생성일시')

    # Relationship
    stock = relationship("Stock", back_populates="daily_prices")

    # Indexes
    __table_args__ = (
        Index('idx_daily_stock_date', 'stock_code', 'date', unique=True),
        Index('idx_daily_date', 'date'),
    )

    def __repr__(self):
        return f"<DailyPrice(stock={self.stock_code}, date={self.date}, close={self.close})>"


class MinutePrice(Base):
    """분봉 데이터"""
    __tablename__ = 'minute_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), ForeignKey('stocks.code'), nullable=False, comment='종목코드')
    datetime = Column(DateTime, nullable=False, comment='일시')
    interval = Column(Integer, nullable=False, comment='분봉 간격 (1, 5, 60 등)')

    open = Column(Integer, nullable=False, comment='시가')
    high = Column(Integer, nullable=False, comment='고가')
    low = Column(Integer, nullable=False, comment='저가')
    close = Column(Integer, nullable=False, comment='종가')
    volume = Column(BigInteger, nullable=False, comment='거래량')

    created_at = Column(DateTime, default=lambda: datetime.now(), comment='생성일시')

    # Relationship
    stock = relationship("Stock", back_populates="minute_prices")

    # Indexes
    __table_args__ = (
        Index('idx_minute_stock_datetime', 'stock_code', 'datetime', 'interval', unique=True),
        Index('idx_minute_datetime', 'datetime'),
    )

    def __repr__(self):
        return f"<MinutePrice(stock={self.stock_code}, datetime={self.datetime}, close={self.close})>"


class TickPrice(Base):
    """틱 데이터 (체결 데이터)"""
    __tablename__ = 'tick_prices'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), ForeignKey('stocks.code'), nullable=False, comment='종목코드')
    datetime = Column(DateTime, nullable=False, comment='체결시간')

    price = Column(Integer, nullable=False, comment='체결가')
    volume = Column(BigInteger, nullable=False, comment='체결량')

    # 추가 정보
    change = Column(Integer, comment='전일대비')
    ask_volume = Column(BigInteger, comment='매도잔량')
    bid_volume = Column(BigInteger, comment='매수잔량')
    market_type = Column(String(10), comment='장구분 (장전, 장중, 장후)')

    created_at = Column(DateTime, default=lambda: datetime.now(), comment='생성일시')

    # Relationship
    stock = relationship("Stock", backref="tick_prices")

    # Indexes
    __table_args__ = (
        Index('idx_tick_stock_datetime', 'stock_code', 'datetime', unique=True),
        Index('idx_tick_datetime', 'datetime'),
    )

    def __repr__(self):
        return f"<TickPrice(stock={self.stock_code}, datetime={self.datetime}, price={self.price})>"


class InvestorTrading(Base):
    """투자자별 매매 동향"""
    __tablename__ = 'investor_trading'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), ForeignKey('stocks.code'), nullable=False, comment='종목코드')
    date = Column(Date, nullable=False, comment='날짜')

    # 기관
    institution_buy = Column(BigInteger, default=0, comment='기관 매수량')
    institution_sell = Column(BigInteger, default=0, comment='기관 매도량')
    institution_net = Column(BigInteger, default=0, comment='기관 순매수')

    # 외국인
    foreign_buy = Column(BigInteger, default=0, comment='외국인 매수량')
    foreign_sell = Column(BigInteger, default=0, comment='외국인 매도량')
    foreign_net = Column(BigInteger, default=0, comment='외국인 순매수')

    # 개인
    individual_buy = Column(BigInteger, default=0, comment='개인 매수량')
    individual_sell = Column(BigInteger, default=0, comment='개인 매도량')
    individual_net = Column(BigInteger, default=0, comment='개인 순매수')

    created_at = Column(DateTime, default=lambda: datetime.now(), comment='생성일시')

    # Indexes
    __table_args__ = (
        Index('idx_investor_stock_date', 'stock_code', 'date', unique=True),
    )

    def __repr__(self):
        return f"<InvestorTrading(stock={self.stock_code}, date={self.date})>"


class StockInfo(Base):
    """종목 상세 정보 (재무 지표 등)"""
    __tablename__ = 'stock_info'

    stock_code = Column(String(10), ForeignKey('stocks.code'), primary_key=True, comment='종목코드')

    # 기본 정보
    market_cap = Column(BigInteger, comment='시가총액')
    shares_outstanding = Column(BigInteger, comment='상장주식수')
    par_value = Column(Integer, comment='액면가')

    # 재무 지표
    per = Column(Float, comment='PER')
    pbr = Column(Float, comment='PBR')
    roe = Column(Float, comment='ROE')
    eps = Column(Integer, comment='EPS')
    bps = Column(Integer, comment='BPS')

    # 배당 정보
    dividend_yield = Column(Float, comment='배당수익률')
    dividend_per_share = Column(Integer, comment='주당배당금')

    # 거래 정보
    credit_ratio = Column(Float, comment='신용잔고율')
    short_selling_ratio = Column(Float, comment='공매도비율')

    # 52주 고저
    high_52w = Column(Integer, comment='52주 최고가')
    low_52w = Column(Integer, comment='52주 최저가')
    high_52w_date = Column(Date, comment='52주 최고가 날짜')
    low_52w_date = Column(Date, comment='52주 최저가 날짜')

    updated_at = Column(DateTime, default=lambda: datetime.now(), onupdate=lambda: datetime.now(), comment='수정일시')

    # Relationship
    stock = relationship("Stock", back_populates="stock_info")

    def __repr__(self):
        return f"<StockInfo(stock={self.stock_code}, per={self.per}, pbr={self.pbr})>"


class CollectionLog(Base):
    """데이터 수집 로그"""
    __tablename__ = 'collection_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(10), comment='종목코드 (전체 수집시 NULL)')
    collection_type = Column(String(20), nullable=False, comment='수집 타입 (daily, minute, info 등)')
    start_date = Column(Date, comment='수집 시작일')
    end_date = Column(Date, comment='수집 종료일')

    status = Column(String(20), nullable=False, comment='상태 (success, failed, in_progress)')
    records_collected = Column(Integer, default=0, comment='수집된 레코드 수')
    error_message = Column(String(500), comment='에러 메시지')

    started_at = Column(DateTime, default=lambda: datetime.now(), comment='수집 시작 시간')
    completed_at = Column(DateTime, comment='수집 완료 시간')

    def __repr__(self):
        return f"<CollectionLog(type={self.collection_type}, status={self.status}, stock={self.stock_code})>"
