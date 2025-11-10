"""
Feature Selection

Feature 선택 및 필터링을 위한 유틸리티
"""

from sklearn.feature_selection import SelectKBest, f_classif
import pandas as pd
import numpy as np
from typing import List
import logging

logger = logging.getLogger(__name__)


class FeatureSelector:
    """
    Feature 선택 및 필터링

    ANOVA F-value 기반으로 상위 K개 feature를 선택합니다.

    Example:
        >>> selector = FeatureSelector()
        >>> top_features = selector.select_by_importance(X, y, k=30)
    """

    def select_by_importance(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        k: int = 30
    ) -> List[str]:
        """
        ANOVA F-value 기반 상위 K개 feature 선택

        Args:
            X: 특징 데이터프레임
            y: 타겟 레이블
            k: 선택할 feature 개수

        Returns:
            선택된 feature 이름 리스트

        Example:
            >>> selector = FeatureSelector()
            >>> top_30 = selector.select_by_importance(X_train, y_train, k=30)
            >>> X_selected = X_train[top_30]
        """
        logger.info(f"Selecting top {k} features from {len(X.columns)} features")

        selector = SelectKBest(f_classif, k=min(k, len(X.columns)))
        selector.fit(X, y)

        mask = selector.get_support()
        selected_features = X.columns[mask].tolist()

        logger.info(f"Selected {len(selected_features)} features")

        return selected_features

    def __repr__(self) -> str:
        """문자열 표현"""
        return "FeatureSelector(method='ANOVA F-value')"
