"""
ML Data Loader

데이터베이스에서 ML 학습용 데이터를 로드하는 유틸리티
"""

import pandas as pd
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
import logging
import sys
import os

# db.models 모듈 임포트
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from db.models import DailyPrice

logger = logging.getLogger(__name__)


class MLDataLoader:
    """
    ML 학습용 데이터 로더

    데이터베이스에서 주가 데이터를 불러와 ML 학습에 적합한 형태로 변환합니다.

    Example:
        >>> from db.database import SessionLocal
        >>> loader = MLDataLoader()
        >>> with SessionLocal() as session:
        ...     df = loader.load_stock_data(
        ...         session=session,
        ...         stock_code="005930",
        ...         start_date=date(2020, 1, 1),
        ...         end_date=date(2024, 1, 1)
        ...     )
    """

    def load_stock_data(
        self,
        session: Session,
        stock_code: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        데이터베이스에서 주가 데이터 로드

        Args:
            session: SQLAlchemy 세션
            stock_code: 종목코드 (예: "005930")
            start_date: 시작일
            end_date: 종료일

        Returns:
            DataFrame with columns: date, open, high, low, close, volume

        Example:
            >>> df = loader.load_stock_data(
            ...     session=session,
            ...     stock_code="005930",
            ...     start_date=date(2020, 1, 1),
            ...     end_date=date(2024, 1, 1)
            ... )
            >>> print(df.head())
                  date    open    high     low   close    volume
            0  2020-01-02  56000  56500  55500  56000  10000000
            ...
        """
        logger.info(
            f"Loading stock data: code={stock_code}, "
            f"period={start_date} to {end_date}"
        )

        # 데이터베이스 쿼리
        prices = session.query(DailyPrice).filter(
            DailyPrice.stock_code == stock_code,
            DailyPrice.date >= start_date,
            DailyPrice.date <= end_date
        ).order_by(DailyPrice.date).all()

        if not prices:
            logger.warning(f"No data found for {stock_code}")
            return pd.DataFrame(columns=['date', 'open', 'high', 'low', 'close', 'volume'])

        # DataFrame 변환
        df = pd.DataFrame([{
            'date': p.date,
            'open': p.open,
            'high': p.high,
            'low': p.low,
            'close': p.close,
            'volume': p.volume
        } for p in prices])

        logger.info(f"Loaded {len(df)} rows")

        return df

    def load_multiple_stocks(
        self,
        session: Session,
        stock_codes: list[str],
        start_date: date,
        end_date: date
    ) -> dict[str, pd.DataFrame]:
        """
        여러 종목의 주가 데이터 로드

        Args:
            session: SQLAlchemy 세션
            stock_codes: 종목코드 리스트
            start_date: 시작일
            end_date: 종료일

        Returns:
            종목코드를 키로 하는 DataFrame 딕셔너리

        Example:
            >>> data_dict = loader.load_multiple_stocks(
            ...     session=session,
            ...     stock_codes=["005930", "000660"],
            ...     start_date=date(2020, 1, 1),
            ...     end_date=date(2024, 1, 1)
            ... )
            >>> print(data_dict["005930"].head())
        """
        logger.info(f"Loading {len(stock_codes)} stocks")

        result = {}
        for code in stock_codes:
            df = self.load_stock_data(session, code, start_date, end_date)
            result[code] = df

        logger.info(f"Loaded data for {len(result)} stocks")

        return result

    def __repr__(self) -> str:
        """문자열 표현"""
        return "MLDataLoader()"
