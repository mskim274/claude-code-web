"""
Time Series Data Splitter

시계열 데이터 분할 (미래 데이터 유출 방지)
"""

from sklearn.model_selection import TimeSeriesSplit
import pandas as pd
import numpy as np
from typing import Tuple, Generator
import logging

logger = logging.getLogger(__name__)


class TimeSeriesDataSplitter:
    """
    시계열 데이터 분할 (미래 데이터 유출 방지)

    일반적인 random split이 아닌 시계열 순서를 유지하며 분할합니다.
    과거 데이터로 학습하고 미래 데이터로 테스트하여 현실적인 백테스팅을 수행합니다.

    Example:
        >>> splitter = TimeSeriesDataSplitter()
        >>> X_train, X_test, y_train, y_test = splitter.train_test_split(X, y, test_size=0.2)
    """

    def train_test_split(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        시계열 순서 유지하며 학습/테스트 분할

        Args:
            X: 특징 데이터프레임
            y: 타겟 레이블
            test_size: 테스트 데이터 비율 (기본 0.2 = 20%)

        Returns:
            X_train, X_test, y_train, y_test

        Example:
            >>> splitter = TimeSeriesDataSplitter()
            >>> X_train, X_test, y_train, y_test = splitter.train_test_split(X, y, test_size=0.2)
            >>> print(f"Train: {len(X_train)}, Test: {len(X_test)}")
            Train: 800, Test: 200
        """
        if not (0 < test_size < 1):
            raise ValueError("test_size must be between 0 and 1")

        split_idx = int(len(X) * (1 - test_size))

        logger.info(
            f"Splitting data: train={split_idx} ({1-test_size:.1%}), "
            f"test={len(X)-split_idx} ({test_size:.1%})"
        )

        X_train = X.iloc[:split_idx]
        X_test = X.iloc[split_idx:]
        y_train = y.iloc[:split_idx]
        y_test = y.iloc[split_idx:]

        return X_train, X_test, y_train, y_test

    def walk_forward_splits(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_splits: int = 5
    ) -> Generator[Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series], None, None]:
        """
        Walk-Forward 분할

        시계열 Cross-Validation을 수행합니다.
        과거 데이터로 학습하고 미래 데이터로 검증하는 과정을 반복합니다.

        Args:
            X: 특징 데이터프레임
            y: 타겟 레이블
            n_splits: 분할 횟수 (기본 5)

        Yields:
            X_train, X_test, y_train, y_test

        Example:
            >>> splitter = TimeSeriesDataSplitter()
            >>> for X_train, X_test, y_train, y_test in splitter.walk_forward_splits(X, y, n_splits=5):
            ...     model.fit(X_train, y_train)
            ...     score = model.score(X_test, y_test)
            ...     print(f"Fold score: {score}")
        """
        logger.info(f"Performing walk-forward validation with {n_splits} splits")

        tscv = TimeSeriesSplit(n_splits=n_splits)

        for fold, (train_idx, test_idx) in enumerate(tscv.split(X), 1):
            logger.debug(
                f"Fold {fold}/{n_splits}: "
                f"train={len(train_idx)}, test={len(test_idx)}"
            )

            yield (
                X.iloc[train_idx],
                X.iloc[test_idx],
                y.iloc[train_idx],
                y.iloc[test_idx]
            )

    def split_by_date(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        split_date: pd.Timestamp
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        특정 날짜를 기준으로 분할

        Args:
            X: 특징 데이터프레임 (date 컬럼 또는 DatetimeIndex 필요)
            y: 타겟 레이블
            split_date: 분할 기준 날짜

        Returns:
            X_train, X_test, y_train, y_test

        Example:
            >>> splitter = TimeSeriesDataSplitter()
            >>> split_date = pd.Timestamp('2023-01-01')
            >>> X_train, X_test, y_train, y_test = splitter.split_by_date(X, y, split_date)
        """
        logger.info(f"Splitting by date: {split_date}")

        if 'date' in X.columns:
            mask = X['date'] < split_date
        elif isinstance(X.index, pd.DatetimeIndex):
            mask = X.index < split_date
        else:
            raise ValueError("X must have 'date' column or DatetimeIndex")

        X_train = X[mask]
        X_test = X[~mask]
        y_train = y[mask]
        y_test = y[~mask]

        logger.info(
            f"Split result: train={len(X_train)}, test={len(X_test)}"
        )

        return X_train, X_test, y_train, y_test

    def __repr__(self) -> str:
        """문자열 표현"""
        return "TimeSeriesDataSplitter()"
