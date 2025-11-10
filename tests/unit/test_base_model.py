"""
Unit tests for BaseMLModel abstract class

TDD Phase: Red - Write tests first
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os


class TestBaseMLModel:
    """BaseMLModel 추상 클래스 테스트"""

    def test_base_model_cannot_be_instantiated(self):
        """추상 클래스는 직접 인스턴스화 불가"""
        from ml.models.base_model import BaseMLModel

        with pytest.raises(TypeError):
            BaseMLModel()

    def test_concrete_model_must_implement_fit(self):
        """구체 클래스는 fit 메서드 구현 필수"""
        from ml.models.base_model import BaseMLModel

        class IncompleteModel(BaseMLModel):
            def predict(self, X):
                pass

        with pytest.raises(TypeError):
            IncompleteModel()

    def test_concrete_model_must_implement_predict(self):
        """구체 클래스는 predict 메서드 구현 필수"""
        from ml.models.base_model import BaseMLModel

        class IncompleteModel(BaseMLModel):
            def fit(self, X, y):
                pass

        with pytest.raises(TypeError):
            IncompleteModel()

    def test_concrete_model_can_be_instantiated(self):
        """모든 추상 메서드를 구현하면 인스턴스화 가능"""
        from ml.models.base_model import BaseMLModel

        class ConcreteModel(BaseMLModel):
            def __init__(self):
                self.model = None

            def fit(self, X, y):
                self.model = "trained"
                return self

            def predict(self, X):
                return np.array([1, 2, 3])

        model = ConcreteModel()
        assert model is not None

    def test_save_method_saves_model(self):
        """save 메서드가 모델을 저장하는지 확인"""
        from ml.models.base_model import BaseMLModel

        class ConcreteModel(BaseMLModel):
            def __init__(self):
                self.model = "test_model"

            def fit(self, X, y):
                return self

            def predict(self, X):
                return np.array([1, 2, 3])

        model = ConcreteModel()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_model.pkl")
            model.save(path)

            assert os.path.exists(path)

    def test_load_method_loads_model(self):
        """load 메서드가 모델을 로드하는지 확인"""
        from ml.models.base_model import BaseMLModel

        class ConcreteModel(BaseMLModel):
            def __init__(self):
                self.model = None

            def fit(self, X, y):
                return self

            def predict(self, X):
                return np.array([1, 2, 3])

        # 저장
        model1 = ConcreteModel()
        model1.model = "original_model"

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_model.pkl")
            model1.save(path)

            # 로드
            model2 = ConcreteModel()
            model2.load(path)

            assert model2.model == "original_model"
