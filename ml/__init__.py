"""
ML Engine Package

LightGBM 기반 주가 예측 모델 및 Feature Engineering

Components:
    - models: LightGBM 분류 모델
    - features: 기술적 지표 기반 Feature Engineering
    - utils: 데이터 로딩 및 분할

Example:
    >>> from ml.models import LGBMStockClassifier
    >>> from ml.features import TechnicalFeatureEngine
    >>> from ml.utils import MLDataLoader, TimeSeriesDataSplitter
    >>>
    >>> # Feature 생성
    >>> engine = TechnicalFeatureEngine()
    >>> features = engine.create_features(ohlcv_df)
    >>> labels = engine.create_labels(ohlcv_df)
    >>>
    >>> # 데이터 분할
    >>> splitter = TimeSeriesDataSplitter()
    >>> X_train, X_test, y_train, y_test = splitter.train_test_split(features, labels)
    >>>
    >>> # 모델 학습
    >>> model = LGBMStockClassifier()
    >>> model.fit(X_train, y_train)
    >>>
    >>> # 예측
    >>> predictions = model.predict(X_test)
"""

from .models import LGBMStockClassifier, BaseMLModel
from .features import TechnicalFeatureEngine, FeatureSelector
from .utils import MLDataLoader, TimeSeriesDataSplitter

__all__ = [
    # Models
    'LGBMStockClassifier',
    'BaseMLModel',

    # Features
    'TechnicalFeatureEngine',
    'FeatureSelector',

    # Utils
    'MLDataLoader',
    'TimeSeriesDataSplitter',
]

__version__ = '1.0.0'
