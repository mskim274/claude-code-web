"""
Performance Metrics

Comprehensive evaluation metrics for both classification models and trading strategies.
Includes accuracy, precision, recall, F1-score, Sharpe ratio, Sortino ratio, drawdown, etc.
"""

import pandas as pd
import numpy as np
from typing import Dict
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)


class PerformanceEvaluator:
    """
    모델 및 트레이딩 성능 평가

    분류 모델의 정확도와 트레이딩 전략의 수익성을 평가하는 도구입니다.
    scikit-learn 메트릭과 금융 성과 지표를 모두 제공합니다.

    Example:
        >>> evaluator = PerformanceEvaluator()
        >>> # Classification metrics
        >>> clf_metrics = evaluator.evaluate_classification(y_true, y_pred)
        >>> print(f"Accuracy: {clf_metrics['accuracy']:.4f}")
        >>>
        >>> # Trading metrics
        >>> trading_metrics = evaluator.evaluate_trading(returns)
        >>> print(f"Sharpe Ratio: {trading_metrics['sharpe_ratio']:.4f}")
        >>>
        >>> # Print full report
        >>> evaluator.print_report(clf_metrics, trading_metrics)
    """

    def evaluate_classification(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray
    ) -> Dict[str, float]:
        """
        분류 모델 성능 평가

        다중 클래스 분류 문제의 성능을 평가합니다.
        macro averaging을 사용하여 클래스 불균형에 강건합니다.

        Args:
            y_true: 실제 레이블 (0, 1, 2)
            y_pred: 예측 레이블 (0, 1, 2)

        Returns:
            Dict with:
                - accuracy: 정확도 (0-1)
                - precision: 정밀도 (macro avg)
                - recall: 재현율 (macro avg)
                - f1_score: F1 점수 (macro avg)
                - confusion_matrix: 혼동 행렬 (list of lists)

        Example:
            >>> y_true = np.array([0, 1, 2, 0, 1])
            >>> y_pred = np.array([0, 1, 1, 0, 1])
            >>> metrics = evaluator.evaluate_classification(y_true, y_pred)
            >>> metrics['accuracy']  # 0.8
        """
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(
                y_true, y_pred,
                average='macro',
                zero_division=0
            ),
            'recall': recall_score(
                y_true, y_pred,
                average='macro',
                zero_division=0
            ),
            'f1_score': f1_score(
                y_true, y_pred,
                average='macro',
                zero_division=0
            ),
            'confusion_matrix': confusion_matrix(y_true, y_pred).tolist()
        }

    def evaluate_trading(
        self,
        returns: pd.Series,
        risk_free_rate: float = 0.02
    ) -> Dict[str, float]:
        """
        트레이딩 성능 평가

        수익률 시계열을 분석하여 위험 조정 수익률과 성과 지표를 계산합니다.

        Args:
            returns: 일별 수익률 시계열 (예: 0.01 = 1%)
            risk_free_rate: 무위험 수익률 (연율, 예: 0.02 = 2%)

        Returns:
            Dict with:
                - total_return: 총 수익률
                - annualized_return: 연환산 수익률 (CAGR)
                - sharpe_ratio: 샤프 비율 (위험 대비 수익)
                - sortino_ratio: 소르티노 비율 (하방 위험 대비 수익)
                - max_drawdown: 최대 낙폭 (음수)
                - win_rate: 승률 (0-1)
                - profit_factor: 손익비 (총 이익 / 총 손실)
                - num_trades: 거래 횟수 (non-zero returns)
                - avg_return_per_trade: 거래당 평균 수익률

        Example:
            >>> returns = pd.Series([0.01, -0.005, 0.02, 0.01])
            >>> metrics = evaluator.evaluate_trading(returns)
            >>> print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
            >>> print(f"Win Rate: {metrics['win_rate']:.1%}")
        """
        # 누적 수익률 계산
        cumulative_returns = (1 + returns).cumprod()
        total_return = cumulative_returns.iloc[-1] - 1

        # 연환산 수익률 (CAGR)
        years = len(returns) / 252  # 연간 약 252 거래일
        if years > 0:
            annualized_return = (1 + total_return) ** (1 / years) - 1
        else:
            annualized_return = 0.0

        # Sharpe Ratio
        # 일별 초과 수익률
        daily_rf = risk_free_rate / 252
        excess_returns = returns - daily_rf

        if returns.std() != 0:
            sharpe_ratio = np.sqrt(252) * excess_returns.mean() / returns.std()
        else:
            sharpe_ratio = 0.0

        # Sortino Ratio (하방 위험만 고려)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() != 0:
            sortino_ratio = np.sqrt(252) * excess_returns.mean() / downside_returns.std()
        else:
            sortino_ratio = 0.0

        # Max Drawdown
        cummax = cumulative_returns.cummax()
        drawdown = (cumulative_returns - cummax) / cummax
        max_drawdown = drawdown.min()

        # Win Rate
        winning_trades = returns[returns > 0]
        losing_trades = returns[returns < 0]
        total_trades = len(winning_trades) + len(losing_trades)

        if total_trades > 0:
            win_rate = len(winning_trades) / total_trades
        else:
            win_rate = 0.0

        # Profit Factor
        total_profit = winning_trades.sum() if len(winning_trades) > 0 else 0.0
        total_loss = abs(losing_trades.sum()) if len(losing_trades) > 0 else 0.0

        if total_loss > 0:
            profit_factor = total_profit / total_loss
        else:
            profit_factor = np.inf if total_profit > 0 else 0.0

        # Number of trades (non-zero returns)
        num_trades = (returns != 0).sum()

        # Average return per trade
        if num_trades > 0:
            avg_return_per_trade = returns[returns != 0].mean()
        else:
            avg_return_per_trade = 0.0

        return {
            'total_return': float(total_return),
            'annualized_return': float(annualized_return),
            'sharpe_ratio': float(sharpe_ratio),
            'sortino_ratio': float(sortino_ratio),
            'max_drawdown': float(max_drawdown),
            'win_rate': float(win_rate),
            'profit_factor': float(profit_factor),
            'num_trades': int(num_trades),
            'avg_return_per_trade': float(avg_return_per_trade)
        }

    def print_report(
        self,
        classification_metrics: Dict,
        trading_metrics: Dict
    ):
        """
        성능 리포트 출력

        분류 및 트레이딩 메트릭을 보기 좋게 출력합니다.

        Args:
            classification_metrics: evaluate_classification 결과
            trading_metrics: evaluate_trading 결과

        Example:
            >>> evaluator.print_report(clf_metrics, trading_metrics)
            ======================================================================
            CLASSIFICATION METRICS
            ======================================================================
            Accuracy:  0.6500
            Precision: 0.6234
            ...
        """
        print("=" * 70)
        print("CLASSIFICATION METRICS")
        print("=" * 70)
        print(f"Accuracy:  {classification_metrics['accuracy']:.4f}")
        print(f"Precision: {classification_metrics['precision']:.4f}")
        print(f"Recall:    {classification_metrics['recall']:.4f}")
        print(f"F1-Score:  {classification_metrics['f1_score']:.4f}")
        print()

        print("=" * 70)
        print("TRADING METRICS")
        print("=" * 70)
        print(f"Total Return:      {trading_metrics['total_return']:.2%}")
        print(f"Annualized Return: {trading_metrics['annualized_return']:.2%}")
        print(f"Sharpe Ratio:      {trading_metrics['sharpe_ratio']:.4f}")
        print(f"Sortino Ratio:     {trading_metrics['sortino_ratio']:.4f}")
        print(f"Max Drawdown:      {trading_metrics['max_drawdown']:.2%}")
        print(f"Win Rate:          {trading_metrics['win_rate']:.2%}")

        # Handle infinite profit factor
        if np.isinf(trading_metrics['profit_factor']):
            print(f"Profit Factor:     inf")
        else:
            print(f"Profit Factor:     {trading_metrics['profit_factor']:.4f}")

        print(f"Num Trades:        {trading_metrics['num_trades']}")
        print(f"Avg Return/Trade:  {trading_metrics['avg_return_per_trade']:.4f}")
        print("=" * 70)

    def __repr__(self) -> str:
        """String representation"""
        return "PerformanceEvaluator()"
