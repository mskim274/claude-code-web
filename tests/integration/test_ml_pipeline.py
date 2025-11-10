"""
Integration tests for ML Pipeline

전체 ML 파이프라인 통합 테스트 (Feature Engineering → Model Training → Prediction)
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class TestMLPipeline:
    """ML 파이프라인 통합 테스트"""

    @pytest.fixture
    def realistic_stock_data(self):
        """현실적인 주가 데이터 생성"""
        np.random.seed(42)
        n_days = 300  # 충분한 데이터

        dates = pd.date_range(start='2022-01-01', periods=n_days, freq='D')

        # 현실적인 주가 시뮬레이션 (Geometric Brownian Motion)
        S0 = 50000  # 초기 가격
        mu = 0.0002  # 일일 평균 수익률
        sigma = 0.02  # 일일 변동성

        returns = np.random.normal(mu, sigma, n_days)
        price_path = S0 * np.exp(np.cumsum(returns))

        df = pd.DataFrame({
            'date': dates,
            'close': price_path,
        })

        # OHLCV 생성
        df['open'] = df['close'] * (1 + np.random.uniform(-0.01, 0.01, n_days))
        df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.uniform(0, 0.02, n_days))
        df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.uniform(0, 0.02, n_days))
        df['volume'] = np.random.randint(100000, 1000000, n_days)

        # 컬럼 순서 정리
        df = df[['date', 'open', 'high', 'low', 'close', 'volume']]

        return df

    def test_feature_engineering_with_real_data(self, realistic_stock_data):
        """실제 데이터로 Feature Engineering 테스트"""
        from ml.features import TechnicalFeatureEngine

        engine = TechnicalFeatureEngine()
        features = engine.create_features(realistic_stock_data)

        # 검증
        assert isinstance(features, pd.DataFrame)
        assert len(features) > 100  # NaN 제거 후에도 충분한 데이터
        assert len(features.columns) >= 50  # 50+ 지표

        # NaN이 없어야 함
        assert not features.isnull().any().any()

    def test_model_training_with_features(self, realistic_stock_data):
        """Feature로 모델 학습 테스트"""
        from ml.features import TechnicalFeatureEngine
        from ml.models import LGBMStockClassifier
        from ml.utils import TimeSeriesDataSplitter

        # Feature 생성
        engine = TechnicalFeatureEngine()
        features = engine.create_features(realistic_stock_data)
        labels = engine.create_labels(realistic_stock_data, forward_days=1, threshold=0.01)

        # 인덱스 정렬 (dropna로 인한 불일치 방지)
        features, labels = features.align(labels, join='inner', axis=0)
        labels = labels.dropna()
        features = features.loc[labels.index]

        # date 컬럼 제거 (모델 학습용)
        if 'date' in features.columns:
            features = features.drop('date', axis=1)

        # 데이터 분할
        splitter = TimeSeriesDataSplitter()
        X_train, X_test, y_train, y_test = splitter.train_test_split(
            features, labels, test_size=0.2
        )

        # 모델 학습
        model = LGBMStockClassifier()
        model.fit(X_train, y_train)

        # 예측
        predictions = model.predict(X_test)

        # 검증
        assert len(predictions) == len(X_test)
        assert set(predictions).issubset({0, 1, 2})

        # 확률 예측
        probas = model.predict_proba(X_test)
        assert probas.shape == (len(X_test), 3)

        # Feature Importance
        importance = model.get_feature_importance()
        assert isinstance(importance, pd.DataFrame)
        assert len(importance) == len(X_train.columns)

    def test_full_pipeline_end_to_end(self, realistic_stock_data):
        """전체 파이프라인 E2E 테스트"""
        from ml.features import TechnicalFeatureEngine, FeatureSelector
        from ml.models import LGBMStockClassifier
        from ml.utils import TimeSeriesDataSplitter

        # 1. Feature Engineering
        engine = TechnicalFeatureEngine()
        features = engine.create_features(realistic_stock_data)
        labels = engine.create_labels(realistic_stock_data, forward_days=1, threshold=0.01)

        # 인덱스 정렬
        features, labels = features.align(labels, join='inner', axis=0)
        labels = labels.dropna()
        features = features.loc[labels.index]

        # date 컬럼 제거
        if 'date' in features.columns:
            features = features.drop('date', axis=1)

        # 2. 데이터 분할
        splitter = TimeSeriesDataSplitter()
        X_train, X_test, y_train, y_test = splitter.train_test_split(
            features, labels, test_size=0.2
        )

        # 3. Feature Selection (선택사항)
        selector = FeatureSelector()
        top_features = selector.select_by_importance(X_train, y_train, k=30)
        X_train_selected = X_train[top_features]
        X_test_selected = X_test[top_features]

        # 4. 모델 학습
        model = LGBMStockClassifier(threshold=0.01)
        model.fit(
            X_train_selected,
            y_train,
            eval_set=[(X_test_selected, y_test)],
            early_stopping_rounds=50
        )

        # 5. 예측
        y_pred = model.predict(X_test_selected)
        y_pred_proba = model.predict_proba(X_test_selected)

        # 6. 검증
        assert len(y_pred) == len(y_test)
        assert y_pred_proba.shape == (len(y_test), 3)

        # 정확도 계산
        accuracy = (y_pred == y_test).mean()
        print(f"\nTest Accuracy: {accuracy:.2%}")

        # Feature Importance
        importance = model.get_feature_importance()
        print(f"\nTop 5 Features:")
        print(importance.head())

        # 최소 정확도 확인 (랜덤보다는 나아야 함)
        assert accuracy > 0.25  # 3-class 랜덤 = 33%, 최소 25% 이상

    def test_walk_forward_validation(self, realistic_stock_data):
        """Walk-Forward Validation 테스트"""
        from ml.features import TechnicalFeatureEngine
        from ml.models import LGBMStockClassifier
        from ml.utils import TimeSeriesDataSplitter

        # Feature 생성
        engine = TechnicalFeatureEngine()
        features = engine.create_features(realistic_stock_data)
        labels = engine.create_labels(realistic_stock_data, forward_days=1, threshold=0.01)

        # 인덱스 정렬
        features, labels = features.align(labels, join='inner', axis=0)
        labels = labels.dropna()
        features = features.loc[labels.index]

        # date 컬럼 제거
        if 'date' in features.columns:
            features = features.drop('date', axis=1)

        # Walk-Forward 분할
        splitter = TimeSeriesDataSplitter()
        scores = []

        for X_train, X_test, y_train, y_test in splitter.walk_forward_splits(
            features, labels, n_splits=3
        ):
            # 모델 학습
            model = LGBMStockClassifier()
            model.fit(X_train, y_train)

            # 예측 및 평가
            y_pred = model.predict(X_test)
            accuracy = (y_pred == y_test).mean()
            scores.append(accuracy)

        # 검증
        assert len(scores) == 3
        print(f"\nWalk-Forward Scores: {scores}")
        print(f"Mean Accuracy: {np.mean(scores):.2%}")

    def test_model_save_and_load_pipeline(self, realistic_stock_data, tmp_path):
        """모델 저장/로드 파이프라인 테스트"""
        from ml.features import TechnicalFeatureEngine
        from ml.models import LGBMStockClassifier
        from ml.utils import TimeSeriesDataSplitter

        # Feature 생성
        engine = TechnicalFeatureEngine()
        features = engine.create_features(realistic_stock_data)
        labels = engine.create_labels(realistic_stock_data)

        # 인덱스 정렬
        features, labels = features.align(labels, join='inner', axis=0)
        labels = labels.dropna()
        features = features.loc[labels.index]

        # date 컬럼 제거
        if 'date' in features.columns:
            features = features.drop('date', axis=1)

        # 데이터 분할
        splitter = TimeSeriesDataSplitter()
        X_train, X_test, y_train, y_test = splitter.train_test_split(
            features, labels, test_size=0.2
        )

        # 모델 학습
        model1 = LGBMStockClassifier()
        model1.fit(X_train, y_train)
        pred1 = model1.predict(X_test)

        # 모델 저장
        model_path = tmp_path / "lgbm_model.pkl"
        model1.save(str(model_path))

        # 모델 로드
        model2 = LGBMStockClassifier()
        model2.feature_names = model1.feature_names
        model2.load(str(model_path))
        pred2 = model2.predict(X_test)

        # 검증: 동일한 예측
        np.testing.assert_array_equal(pred1, pred2)
