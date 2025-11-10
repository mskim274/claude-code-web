"""
Base ML Model Abstract Class

모든 머신러닝 모델의 베이스 클래스
공통 인터페이스와 저장/로드 기능 제공
"""

from abc import ABC, abstractmethod
import joblib
from typing import Any
import pandas as pd
import numpy as np


class BaseMLModel(ABC):
    """
    머신러닝 모델 베이스 클래스

    모든 ML 모델은 이 클래스를 상속받아 fit, predict 메서드를 구현해야 합니다.
    저장/로드 기능은 joblib을 사용하여 제공됩니다.

    Example:
        >>> class MyModel(BaseMLModel):
        ...     def __init__(self):
        ...         self.model = SomeMLModel()
        ...
        ...     def fit(self, X, y):
        ...         self.model.fit(X, y)
        ...         return self
        ...
        ...     def predict(self, X):
        ...         return self.model.predict(X)
    """

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'BaseMLModel':
        """
        모델 학습

        Args:
            X: 특징 데이터프레임
            y: 타겟 데이터

        Returns:
            학습된 모델 (self)
        """
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        예측 수행

        Args:
            X: 특징 데이터프레임

        Returns:
            예측 결과 배열
        """
        pass

    def save(self, path: str) -> None:
        """
        모델 저장

        joblib을 사용하여 모델을 파일로 저장합니다.

        Args:
            path: 저장할 파일 경로 (예: 'model.pkl')

        Example:
            >>> model.save('trained_model.pkl')
        """
        joblib.dump(self.model, path)

    def load(self, path: str) -> None:
        """
        모델 로드

        joblib을 사용하여 저장된 모델을 불러옵니다.

        Args:
            path: 불러올 파일 경로

        Example:
            >>> model = MyModel()
            >>> model.load('trained_model.pkl')
        """
        self.model = joblib.load(path)
