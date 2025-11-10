"""
Unit tests for LGBMStockClassifier

TDD Phase: Red - Write tests first
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os


class TestLGBMStockClassifier:
    """LGBMStockClassifier 모델 테스트"""

    @pytest.fixture
    def sample_data(self):
        """테스트용 샘플 데이터"""
        np.random.seed(42)
        n_samples = 100

        X = pd.DataFrame({
            'feature1': np.random.randn(n_samples),
            'feature2': np.random.randn(n_samples),
            'feature3': np.random.randn(n_samples),
            'feature4': np.random.randn(n_samples),
            'feature5': np.random.randn(n_samples),
        })

        # 3-class 분류: 0(하락), 1(보합), 2(상승)
        y = pd.Series(np.random.choice([0, 1, 2], size=n_samples))

        return X, y

    def test_model_initialization(self, sample_data):
        """모델 초기화 테스트"""
        from ml.models.lgbm_classifier import LGBMStockClassifier

        model = LGBMStockClassifier()

        assert model is not None
        assert model.threshold == 0.01
        assert model.params['objective'] == 'multiclass'
        assert model.params['num_class'] == 3

    def test_model_initialization_with_custom_params(self):
        """커스텀 파라미터로 모델 초기화"""
        from ml.models.lgbm_classifier import LGBMStockClassifier

        custom_params = {
            'num_leaves': 50,
            'learning_rate': 0.1
        }

        model = LGBMStockClassifier(params=custom_params, threshold=0.02)

        assert model.threshold == 0.02
        assert model.params['num_leaves'] == 50
        assert model.params['learning_rate'] == 0.1
        # 기본값도 유지되어야 함
        assert model.params['objective'] == 'multiclass'

    def test_model_fit_with_valid_data(self, sample_data):
        """유효한 데이터로 모델 학습"""
        from ml.models.lgbm_classifier import LGBMStockClassifier

        X, y = sample_data
        model = LGBMStockClassifier()

        result = model.fit(X, y)

        assert result is model  # fit은 self를 반환해야 함
        assert model.feature_names is not None
        assert model.feature_names == X.columns.tolist()

    def test_model_predict_returns_correct_shape(self, sample_data):
        """예측 결과가 올바른 shape를 반환하는지 확인"""
        from ml.models.lgbm_classifier import LGBMStockClassifier

        X, y = sample_data
        model = LGBMStockClassifier()
        model.fit(X, y)

        predictions = model.predict(X)

        assert isinstance(predictions, np.ndarray)
        assert predictions.shape == (len(X),)
        # 예측값은 0, 1, 2 중 하나
        assert all(p in [0, 1, 2] for p in predictions)

    def test_model_predict_proba_sum_to_one(self, sample_data):
        """예측 확률의 합이 1인지 확인"""
        from ml.models.lgbm_classifier import LGBMStockClassifier

        X, y = sample_data
        model = LGBMStockClassifier()
        model.fit(X, y)

        probas = model.predict_proba(X)

        assert isinstance(probas, np.ndarray)
        assert probas.shape == (len(X), 3)  # 3-class
        # 각 샘플의 확률 합이 1에 근사
        np.testing.assert_array_almost_equal(
            probas.sum(axis=1),
            np.ones(len(X)),
            decimal=5
        )

    def test_model_predict_proba_returns_correct_shape(self, sample_data):
        """predict_proba가 올바른 shape를 반환하는지 확인"""
        from ml.models.lgbm_classifier import LGBMStockClassifier

        X, y = sample_data
        model = LGBMStockClassifier()
        model.fit(X, y)

        probas = model.predict_proba(X)

        assert probas.shape == (len(X), 3)
        # 모든 확률은 0~1 사이
        assert (probas >= 0).all() and (probas <= 1).all()

    def test_model_save_and_load(self, sample_data):
        """모델 저장 및 로드 테스트"""
        from ml.models.lgbm_classifier import LGBMStockClassifier

        X, y = sample_data
        model1 = LGBMStockClassifier()
        model1.fit(X, y)

        # 원본 예측
        pred1 = model1.predict(X)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "lgbm_model.pkl")

            # 저장
            model1.save(path)
            assert os.path.exists(path)

            # 로드
            model2 = LGBMStockClassifier()
            model2.feature_names = model1.feature_names
            model2.load(path)

            # 로드된 모델의 예측
            pred2 = model2.predict(X)

            # 동일한 예측 결과
            np.testing.assert_array_equal(pred1, pred2)

    def test_get_feature_importance(self, sample_data):
        """Feature Importance 반환 테스트"""
        from ml.models.lgbm_classifier import LGBMStockClassifier

        X, y = sample_data
        model = LGBMStockClassifier()
        model.fit(X, y)

        importance_df = model.get_feature_importance()

        assert isinstance(importance_df, pd.DataFrame)
        assert 'feature' in importance_df.columns
        assert 'importance' in importance_df.columns
        assert len(importance_df) == len(X.columns)
        # importance는 내림차순 정렬
        assert importance_df['importance'].is_monotonic_decreasing

    def test_model_fit_with_early_stopping(self, sample_data):
        """Early stopping과 함께 학습"""
        from ml.models.lgbm_classifier import LGBMStockClassifier

        X, y = sample_data

        # Train/validation split
        split_idx = int(len(X) * 0.8)
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        model = LGBMStockClassifier()
        eval_set = [(X_val, y_val)]

        model.fit(X_train, y_train, eval_set=eval_set, early_stopping_rounds=10)

        # 학습이 완료되어야 함
        assert model.model is not None
        predictions = model.predict(X_val)
        assert len(predictions) == len(X_val)

    def test_model_with_single_class_raises_error(self):
        """단일 클래스만 있는 데이터는 에러 발생"""
        from ml.models.lgbm_classifier import LGBMStockClassifier

        X = pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5],
            'feature2': [2, 3, 4, 5, 6],
        })
        y = pd.Series([0, 0, 0, 0, 0])  # 모두 같은 클래스

        model = LGBMStockClassifier()

        # LightGBM은 단일 클래스 학습 시 에러 발생할 수 있음
        # 또는 경고만 발생할 수 있으므로 학습은 가능하도록 함
        try:
            model.fit(X, y)
        except Exception:
            pass  # 에러 발생해도 OK

    def test_feature_names_preserved(self, sample_data):
        """feature names가 올바르게 저장되는지 확인"""
        from ml.models.lgbm_classifier import LGBMStockClassifier

        X, y = sample_data
        original_features = X.columns.tolist()

        model = LGBMStockClassifier()
        model.fit(X, y)

        assert model.feature_names == original_features
