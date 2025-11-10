"""
LightGBM-based Stock Price Classifier

주가 방향 예측을 위한 LightGBM 분류 모델
3-class 분류: 0(하락), 1(보합), 2(상승)
"""

import lightgbm as lgb
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
import logging

from .base_model import BaseMLModel

logger = logging.getLogger(__name__)


class LGBMStockClassifier(BaseMLModel):
    """
    LightGBM 기반 주가 방향 예측 모델

    3-class 분류 모델:
        - 0: 하락 (return < -threshold)
        - 1: 보합 (-threshold <= return <= threshold)
        - 2: 상승 (return > threshold)

    Features:
        - 빠른 학습 속도
        - 낮은 메모리 사용량
        - Early stopping 지원
        - Feature importance 제공

    Example:
        >>> model = LGBMStockClassifier(threshold=0.01)  # 1% threshold
        >>> model.fit(X_train, y_train, eval_set=[(X_val, y_val)])
        >>> predictions = model.predict(X_test)
        >>> probabilities = model.predict_proba(X_test)
    """

    def __init__(
        self,
        params: Optional[Dict[str, Any]] = None,
        threshold: float = 0.01
    ):
        """
        모델 초기화

        Args:
            params: LightGBM 하이퍼파라미터
                - objective: 'multiclass' (고정)
                - num_class: 3 (고정)
                - boosting_type: 'gbdt', 'dart', 'goss' 등
                - num_leaves: 트리의 최대 리프 수 (기본 31)
                - learning_rate: 학습률 (기본 0.05)
                - feature_fraction: 피처 샘플링 비율 (기본 0.9)
                - bagging_fraction: 데이터 샘플링 비율 (기본 0.8)
                - bagging_freq: 배깅 빈도 (기본 5)
                - verbose: 로그 출력 수준 (기본 -1)
                - random_state: 랜덤 시드 (기본 42)
            threshold: 상승/하락 판단 임계값 (기본 1% = 0.01)

        Example:
            >>> # 기본 설정
            >>> model = LGBMStockClassifier()
            >>>
            >>> # 커스텀 설정
            >>> custom_params = {
            ...     'num_leaves': 50,
            ...     'learning_rate': 0.1,
            ... }
            >>> model = LGBMStockClassifier(params=custom_params, threshold=0.02)
        """
        default_params = {
            'objective': 'multiclass',
            'num_class': 3,
            'metric': 'multi_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': 42
        }

        # 커스텀 파라미터로 기본값 업데이트
        self.params = {**default_params, **(params or {})}

        # objective와 num_class는 고정
        self.params['objective'] = 'multiclass'
        self.params['num_class'] = 3

        self.threshold = threshold
        self.model = lgb.LGBMClassifier(**self.params)
        self.feature_names: Optional[List[str]] = None

        logger.info(f"LGBMStockClassifier initialized with threshold={threshold}")

    def fit(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        eval_set: Optional[List[Tuple[pd.DataFrame, pd.Series]]] = None,
        early_stopping_rounds: int = 50
    ) -> 'LGBMStockClassifier':
        """
        모델 학습

        Args:
            X: 특징 데이터프레임 (shape: [n_samples, n_features])
            y: 타겟 레이블 (0: 하락, 1: 보합, 2: 상승)
            eval_set: 검증 데이터셋 리스트 [(X_val, y_val), ...]
            early_stopping_rounds: Early stopping 라운드 수

        Returns:
            학습된 모델 (self)

        Example:
            >>> # 기본 학습
            >>> model.fit(X_train, y_train)
            >>>
            >>> # Early stopping 사용
            >>> model.fit(
            ...     X_train, y_train,
            ...     eval_set=[(X_val, y_val)],
            ...     early_stopping_rounds=50
            ... )
        """
        self.feature_names = X.columns.tolist()

        fit_params = {}
        if eval_set is not None:
            fit_params['eval_set'] = eval_set
            fit_params['callbacks'] = [
                lgb.early_stopping(early_stopping_rounds, verbose=False)
            ]

        logger.info(f"Training LGBM model with {len(X)} samples, {len(X.columns)} features")

        self.model.fit(X, y, **fit_params)

        logger.info("Training completed")

        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        클래스 예측

        Args:
            X: 특징 데이터프레임

        Returns:
            예측 클래스 배열 (0: 하락, 1: 보합, 2: 상승)

        Example:
            >>> predictions = model.predict(X_test)
            >>> print(predictions)  # array([2, 1, 0, 2, ...])
        """
        return self.model.predict(X)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        클래스별 확률 예측

        Args:
            X: 특징 데이터프레임

        Returns:
            확률 배열 (shape: [n_samples, 3])
            - [:, 0]: 하락 확률
            - [:, 1]: 보합 확률
            - [:, 2]: 상승 확률

        Example:
            >>> probas = model.predict_proba(X_test)
            >>> print(probas[0])  # array([0.1, 0.3, 0.6])  # 60% 상승 확률
        """
        return self.model.predict_proba(X)

    def get_feature_importance(self) -> pd.DataFrame:
        """
        Feature Importance 반환

        LightGBM의 gain 기반 feature importance를 반환합니다.

        Returns:
            DataFrame with columns:
                - feature: 피처 이름
                - importance: 중요도 (gain 기반)

        Example:
            >>> importance = model.get_feature_importance()
            >>> print(importance.head())
                        feature  importance
            0  RSI_14        250.5
            1  MACD          180.2
            2  BB_Upper      150.1
            ...
        """
        if self.feature_names is None:
            raise ValueError("Model must be trained before getting feature importance")

        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False).reset_index(drop=True)

        logger.info(f"Top 5 features: {importance_df.head()['feature'].tolist()}")

        return importance_df

    def __repr__(self) -> str:
        """문자열 표현"""
        return (
            f"LGBMStockClassifier("
            f"threshold={self.threshold}, "
            f"num_leaves={self.params['num_leaves']}, "
            f"learning_rate={self.params['learning_rate']}"
            f")"
        )
