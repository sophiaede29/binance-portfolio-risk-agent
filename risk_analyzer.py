"""
Computes a portfolio diversification and risk score using:
- Volatility (annualized std dev of daily returns)
- Correlation matrix between held assets
- Concentration risk (% of portfolio in one asset)
"""

import math


def daily_returns(closes: list[float]) -> list[float]:
    return [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(1, len(closes))]


def std_dev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def annualized_volatility(returns: list[float]) -> float:
    daily_std = std_dev(returns)
    return daily_std * math.sqrt(365) * 100


def correlation(returns_a: list[float], returns_b: list[float]) -> float:
    n = min(len(returns_a), len(returns_b))
    a, b = returns_a[-n:], returns_b[-n:]
    if n < 2:
        return 0.0
    mean_a, mean_b = sum(a) / n, sum(b) / n
    cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n)) / (n - 1)
    std_a, std_b = std_dev(a), std_dev(b)
    if std_a == 0 or std_b == 0:
        return 0.0
    return cov / (std_a * std_b)


def build_correlation_matrix(returns_by_asset: dict) -> dict:
    assets = list(returns_by_asset.key
