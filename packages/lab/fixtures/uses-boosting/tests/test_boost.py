import numpy as np
import pytest
from boost import fit_lightgbm, fit_xgboost

X = np.arange(20.0).reshape(-1, 1)
y = (X[:, 0] >= 10).astype(int)


@pytest.mark.id("tst_xgbt01")
def test_xgboost():
    """XGBoost separates two groups"""
    assert fit_xgboost(X, y).predict(X).tolist() == y.tolist()


@pytest.mark.id("tst_lgbm01")
def test_lightgbm():
    """LightGBM separates two groups"""
    assert fit_lightgbm(X, y).predict(X).tolist() == y.tolist()
