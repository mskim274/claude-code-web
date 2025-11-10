"""
KIS API Client Usage Examples.

Demonstrates how to use the KIS API client for various operations.
"""

from datetime import date, timedelta
from collectors.apis.kis import (
    KISClient,
    MockKISClient,
    KISExchange
)


def example_1_basic_stock_price():
    """Example 1: Get current stock price."""
    print("=" * 60)
    print("Example 1: Get Current Stock Price")
    print("=" * 60)

    # Use mock client for testing (replace with KISClient for real API)
    with MockKISClient() as client:
        # Get Samsung Electronics price
        price = client.get_stock_price("005930")

        print(f"\nStock: {price.name} ({price.code})")
        print(f"Current Price: {price.current_price:,}원")
        print(f"Open: {price.open:,}원")
        print(f"High: {price.high:,}원")
        print(f"Low: {price.low:,}원")
        print(f"Volume: {price.volume:,}주")
        print(f"Change: {price.change:+,}원 ({price.change_rate:+.2f}%)")


def example_2_historical_data():
    """Example 2: Get historical daily price data."""
    print("\n" + "=" * 60)
    print("Example 2: Get Historical Daily Price Data")
    print("=" * 60)

    with MockKISClient() as client:
        # Get 30 days of historical data
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        history = client.get_daily_price(
            "005930",
            start_date=start_date,
            end_date=end_date
        )

        print(f"\nRetrieved {len(history)} days of data")
        print(f"\nMost Recent 5 Days:")
        print("-" * 80)
        print(f"{'Date':<12} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Volume':>15}")
        print("-" * 80)

        for item in history[:5]:
            print(
                f"{item.date} "
                f"{item.open:>10,} "
                f"{item.high:>10,} "
                f"{item.low:>10,} "
                f"{item.close:>10,} "
                f"{item.volume:>15,}"
            )


def example_3_overseas_stocks():
    """Example 3: Get overseas stock prices."""
    print("\n" + "=" * 60)
    print("Example 3: Get Overseas Stock Prices")
    print("=" * 60)

    with MockKISClient() as client:
        # Get US tech stocks
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]

        print("\nUS Tech Stocks (NASDAQ):")
        print("-" * 80)
        print(f"{'Symbol':<10} {'Name':<25} {'Price':>12} {'Change':>10}")
        print("-" * 80)

        for symbol in symbols:
            price = client.get_overseas_stock(symbol, KISExchange.NASDAQ)
            print(
                f"{price.symbol:<10} "
                f"{price.name:<25} "
                f"${price.current_price:>11.2f} "
                f"{price.change_rate:>+9.2f}%"
            )


def example_4_multiple_exchanges():
    """Example 4: Get stocks from multiple exchanges."""
    print("\n" + "=" * 60)
    print("Example 4: Get Stocks from Multiple Exchanges")
    print("=" * 60)

    with MockKISClient() as client:
        stocks = [
            ("AAPL", KISExchange.NASDAQ, "US"),
            ("00700", KISExchange.HKEX, "HK"),
            ("9984", KISExchange.TSE, "JP"),
        ]

        print("\nGlobal Tech Stocks:")
        print("-" * 80)
        print(f"{'Symbol':<10} {'Exchange':<10} {'Name':<25} {'Price':>15}")
        print("-" * 80)

        for symbol, exchange, region in stocks:
            price = client.get_overseas_stock(symbol, exchange)
            print(
                f"{price.symbol:<10} "
                f"{exchange.value:<10} "
                f"{price.name:<25} "
                f"{price.currency} {price.current_price:>10.2f}"
            )


def example_5_overseas_historical():
    """Example 5: Get overseas historical data."""
    print("\n" + "=" * 60)
    print("Example 5: Get Overseas Historical Data")
    print("=" * 60)

    with MockKISClient() as client:
        # Get 10 days of Apple stock data
        history = client.get_overseas_daily("AAPL", KISExchange.NASDAQ, period=10)

        print(f"\nApple Inc. (AAPL) - Last 10 Days:")
        print("-" * 80)
        print(f"{'Date':<12} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Volume':>15}")
        print("-" * 80)

        for item in history:
            print(
                f"{item.date} "
                f"${item.open:>9.2f} "
                f"${item.high:>9.2f} "
                f"${item.low:>9.2f} "
                f"${item.close:>9.2f} "
                f"{item.volume:>15,}"
            )


def example_6_real_api_usage():
    """Example 6: Using real KIS API (requires credentials)."""
    print("\n" + "=" * 60)
    print("Example 6: Using Real KIS API")
    print("=" * 60)

    print("\nTo use the real KIS API, set environment variables:")
    print("  export KIS_APP_KEY='your_app_key'")
    print("  export KIS_APP_SECRET='your_app_secret'")
    print("\nThen use KISClient instead of MockKISClient:")
    print("\n# Example code:")
    print("from collectors.apis.kis import KISClient")
    print("\nwith KISClient() as client:")
    print("    price = client.get_stock_price('005930')")
    print("    print(f'Samsung: {price.current_price:,}원')")


def example_7_error_handling():
    """Example 7: Error handling."""
    print("\n" + "=" * 60)
    print("Example 7: Error Handling")
    print("=" * 60)

    from collectors.apis.kis import KISAPIError, KISNetworkError

    with MockKISClient() as client:
        try:
            # This will work with mock client
            price = client.get_stock_price("005930")
            print(f"\nSuccess: Got price for {price.name}")

        except KISAPIError as e:
            print(f"\nAPI Error: {e}")

        except KISNetworkError as e:
            print(f"\nNetwork Error: {e}")

        except Exception as e:
            print(f"\nUnexpected Error: {e}")


def example_8_batch_processing():
    """Example 8: Batch process multiple stocks."""
    print("\n" + "=" * 60)
    print("Example 8: Batch Process Multiple Stocks")
    print("=" * 60)

    with MockKISClient() as client:
        # Korean tech stocks
        stocks = {
            "005930": "삼성전자",
            "000660": "SK하이닉스",
            "035420": "NAVER",
            "035720": "카카오"
        }

        print("\nKorean Tech Stocks:")
        print("-" * 80)
        print(f"{'Code':<10} {'Name':<15} {'Price':>12} {'Change':>10} {'Volume':>15}")
        print("-" * 80)

        results = []
        for code, name in stocks.items():
            try:
                price = client.get_stock_price(code)
                results.append(price)

                print(
                    f"{price.code:<10} "
                    f"{price.name:<15} "
                    f"{price.current_price:>12,} "
                    f"{price.change_rate:>+9.2f}% "
                    f"{price.volume:>15,}"
                )

            except Exception as e:
                print(f"{code:<10} Error: {e}")

        print(f"\nSuccessfully retrieved data for {len(results)}/{len(stocks)} stocks")


def main():
    """Run all examples."""
    print("\n" + "=" * 60)
    print("KIS API Client Usage Examples")
    print("=" * 60)

    examples = [
        example_1_basic_stock_price,
        example_2_historical_data,
        example_3_overseas_stocks,
        example_4_multiple_exchanges,
        example_5_overseas_historical,
        example_6_real_api_usage,
        example_7_error_handling,
        example_8_batch_processing,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nError running example: {e}")

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
