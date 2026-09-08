"""
Portfolio Risk & Diversification Score Agent
Built for the Binance Agent OS Mini Hackathon (Track A - Data Analysis).
Read-only: never places trades, never touches withdrawals.
Automatically analyzes your ENTIRE Binance portfolio -- no manual asset list needed.
"""

import os

from dotenv import load_dotenv

from binance_client import BinanceReadOnlyClient
from portfolio_risk import (
    annualized_volatility,
    build_correlation_matrix,
    concentration_risk,
    daily_returns,
    diversification_score,
)

load_dotenv()

LOOKBACK_DAYS = 30
MIN_VALUE_USDT = 1.0  # Ignore dust balances worth less than $1.
DEMO_MODE = os.environ.get("DEMO_MODE", "").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

MOCK_BALANCES = [
    {"asset": "BTC", "total": 0.05},
    {"asset": "ETH", "total": 1.2},
    {"asset": "BNB", "total": 10},
    {"asset": "USDT", "total": 500},
]

MOCK_PRICE_HISTORY = {
    "BTC": [
        60000,
        61000,
        60500,
        62000,
        61500,
        63000,
        62500,
        64000,
        63500,
        65000,
        64500,
        66000,
        65500,
        67000,
        66500,
        68000,
        67500,
        69000,
        68500,
        70000,
        69500,
        71000,
        70500,
        72000,
        71500,
        73000,
        72500,
        74000,
        73500,
        75000,
    ],
    "ETH": [
        3000,
        3050,
        3020,
        3100,
        3080,
        3150,
        3120,
        3200,
        3180,
        3250,
        3220,
        3300,
        3280,
        3350,
        3320,
        3400,
        3380,
        3450,
        3420,
        3500,
        3480,
        3550,
        3520,
        3600,
        3580,
        3650,
        3620,
        3700,
        3680,
        3750,
    ],
    "BNB": [
        550,
        555,
        552,
        560,
        558,
        565,
        562,
        570,
        568,
        575,
        572,
        580,
        578,
        585,
        582,
        590,
        588,
        595,
        592,
        600,
        598,
        605,
        602,
        610,
        608,
        615,
        612,
        620,
        618,
        625,
    ],
}


def main():
    client = None
    if DEMO_MODE:
        print("DEMO_MODE is enabled. Using local sample portfolio data.")
        balances = MOCK_BALANCES
    else:
        api_key = os.environ["BINANCE_API_KEY"]
        api_secret = os.environ["BINANCE_API_SECRET"]
        client = BinanceReadOnlyClient(api_key, api_secret)

        print("Fetching your full portfolio...")
        balances = client.get_balances(min_balance=0.0)

    portfolio_values = {}
    returns_by_asset = {}
    skipped = []

    for balance in balances:
        asset = balance["asset"]
        amount = balance["total"]

        if DEMO_MODE and asset in MOCK_PRICE_HISTORY:
            closes = MOCK_PRICE_HISTORY[asset]
            price = closes[-1]
        elif asset in ("USDT", "USDC", "BUSD", "FDUSD"):
            price = 1.0
            closes = None
        else:
            symbol = f"{asset}USDT"
            try:
                if client is None:
                    raise RuntimeError(f"No demo price data configured for {asset}")
                closes = client.get_daily_closes(symbol, days=LOOKBACK_DAYS)
                price = closes[-1] if closes else 0
            except Exception:
                skipped.append(asset)
                continue

        value = amount * price
        if value < MIN_VALUE_USDT:
            continue

        portfolio_values[asset] = value
        if closes and len(closes) > 1:
            returns_by_asset[asset] = daily_returns(closes)
        else:
            returns_by_asset[asset] = []

    if skipped:
        print(f"Skipped (no USDT trading pair found): {', '.join(skipped)}\n")

    if not portfolio_values:
        print("No holdings above the dust threshold were found.")
        return

    total_value = sum(portfolio_values.values())
    concentration = concentration_risk(portfolio_values)

    # Only include assets with enough price history for correlation.
    correlatable_assets = {
        asset: returns
        for asset, returns in returns_by_asset.items()
        if len(returns) > 1
    }
    corr_matrix = (
        build_correlation_matrix(correlatable_assets)
        if len(correlatable_assets) > 1
        else {}
    )
    diversification = (
        diversification_score(corr_matrix, concentration)
        if corr_matrix
        else {
            "score": 0,
            "avg_correlation": 0,
            "max_concentration_pct": (
                max(concentration.values()) if concentration else 100
            ),
            "verdict": (
                "Not enough assets with price history to assess correlation."
            ),
        }
    )

    print("--- Full Portfolio Overview ---")
    for asset, value in sorted(
        portfolio_values.items(), key=lambda item: -item[1]
    ):
        vol = (
            annualized_volatility(returns_by_asset[asset])
            if returns_by_asset[asset]
            else 0
        )
        print(
            f"{asset}: ${value:.2f} ({concentration[asset]}% of portfolio) | "
            f"Annualized volatility: {vol:.1f}%"
        )
    print(f"Total portfolio value: ${total_value:.2f}\n")

    if corr_matrix:
        print("--- Correlation Matrix ---")
        assets = list(corr_matrix.keys())
        header = "        " + "  ".join(f"{asset:>6}" for asset in assets)
        print(header)
        for asset in assets:
            row = "  ".join(
                f"{corr_matrix[asset][other]:>6.2f}" for other in assets
            )
            print(f"{asset:>6}  {row}")
        print()

    print("--- Diversification Score ---")
    print(f"Score: {diversification['score']}/100")
    print(f"Average correlation between holdings: {diversification['avg_correlation']}")
    print(
        "Largest single-asset concentration: "
        f"{diversification['max_concentration_pct']}%"
    )
    print(f"Verdict: {diversification['verdict']}")


if __name__ == "__main__":
    main()