"""
Performance tests for data processing, validation, and indicator calculation

Measures performance of:
1. Pydantic schema validation
2. TA-Lib indicator calculation
3. Large dataset processing
4. Database operations
"""

import pytest
import time
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from typing import List
import os

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Import modules (with fallback for Phase 1)
try:
    from schemas.stock import DailyPriceSchema, MinutePriceSchema
except ImportError:
    DailyPriceSchema = None
    MinutePriceSchema = None

try:
    from indicators.talib_wrapper import TechnicalIndicators
except ImportError:
    TechnicalIndicators = None


# Performance thresholds
VALIDATION_THRESHOLD_10K = 5.0  # seconds for 10,000 records
TALIB_THRESHOLD_1K = 1.0         # seconds for 1,000 days
TALIB_THRESHOLD_10K = 8.0        # seconds for 10,000 days
PIPELINE_THRESHOLD_1K = 2.0      # seconds for full pipeline (1,000 records)


def generate_large_ohlcv(days: int, base_price: int = 70000) -> pd.DataFrame:
    """Generate large OHLCV dataset for performance testing"""
    dates = pd.date_range(start='2020-01-01', periods=days, freq='D')

    np.random.seed(42)

    data = {
        'date': dates,
        'open': base_price + np.random.randint(-1000, 1000, days),
        'high': base_price + np.random.randint(500, 2000, days),
        'low': base_price + np.random.randint(-2000, -500, days),
        'close': base_price + np.random.randint(-1000, 1000, days),
        'volume': np.random.randint(1000000, 5000000, days)
    }

    df = pd.DataFrame(data)

    # Ensure OHLC integrity
    df['high'] = df[['open', 'high', 'close']].max(axis=1) + 100
    df['low'] = df[['open', 'low', 'close']].min(axis=1) - 100

    return df


def generate_price_dict_list(count: int) -> List[dict]:
    """Generate list of price dictionaries for schema validation"""
    base_date = date(2020, 1, 1)
    return [
        {
            'stock_code': '005930',
            'date': base_date + timedelta(days=i),
            'open': 70000 + i * 10,
            'high': 71000 + i * 10,
            'low': 69000 + i * 10,
            'close': 70500 + i * 10,
            'volume': 10000000 + i * 1000
        }
        for i in range(count)
    ]


def measure_memory_usage():
    """Get current memory usage in MB"""
    if not PSUTIL_AVAILABLE:
        return 0.0
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # Convert to MB


@pytest.mark.performance
class TestPydanticPerformance:
    """Pydantic 스키마 검증 성능 테스트"""

    def test_validation_performance_1k(self):
        """1,000개 레코드 검증 성능"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        large_data = generate_price_dict_list(1000)

        start_time = time.time()
        validated = [DailyPriceSchema(**item) for item in large_data]
        elapsed_time = time.time() - start_time

        assert len(validated) == 1000
        assert elapsed_time < 1.0, f"Too slow: {elapsed_time:.3f}s for 1,000 records"
        print(f"\n✓ Pydantic 1K validation: {elapsed_time:.3f}s ({1000/elapsed_time:.0f} records/sec)")

    def test_validation_performance_10k(self):
        """10,000개 레코드 검증 성능"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        large_data = generate_price_dict_list(10000)

        start_time = time.time()
        validated = [DailyPriceSchema(**item) for item in large_data]
        elapsed_time = time.time() - start_time

        assert len(validated) == 10000
        assert elapsed_time < VALIDATION_THRESHOLD_10K, \
            f"Too slow: {elapsed_time:.3f}s for 10,000 records (threshold: {VALIDATION_THRESHOLD_10K}s)"
        print(f"\n✓ Pydantic 10K validation: {elapsed_time:.3f}s ({10000/elapsed_time:.0f} records/sec)")

    def test_validation_memory_usage(self):
        """스키마 검증 메모리 사용량 테스트"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        large_data = generate_price_dict_list(10000)

        mem_before = measure_memory_usage()
        validated = [DailyPriceSchema(**item) for item in large_data]
        mem_after = measure_memory_usage()

        memory_increase = mem_after - mem_before
        print(f"\n✓ Memory increase for 10K records: {memory_increase:.2f} MB")

        # Should not exceed 100MB for 10K records
        assert memory_increase < 100, f"Excessive memory usage: {memory_increase:.2f} MB"

    def test_schema_to_dataframe_performance(self):
        """스키마 → DataFrame 변환 성능"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        large_data = generate_price_dict_list(10000)
        schemas = [DailyPriceSchema(**item) for item in large_data]

        start_time = time.time()
        df = pd.DataFrame([s.model_dump() for s in schemas])
        elapsed_time = time.time() - start_time

        assert len(df) == 10000
        assert elapsed_time < 1.0, f"Too slow: {elapsed_time:.3f}s for DataFrame conversion"
        print(f"\n✓ Schema to DataFrame (10K): {elapsed_time:.3f}s")


@pytest.mark.performance
class TestTALibPerformance:
    """TA-Lib 지표 계산 성능 테스트"""

    def test_talib_calculation_performance_1k(self):
        """1,000일치 데이터 지표 계산 성능"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        large_df = generate_large_ohlcv(days=1000)
        indicators = TechnicalIndicators()

        start_time = time.time()
        result = indicators.calculate_all(large_df)
        elapsed_time = time.time() - start_time

        assert len(result) == 1000
        assert elapsed_time < TALIB_THRESHOLD_1K, \
            f"Too slow: {elapsed_time:.3f}s for 1,000 days (threshold: {TALIB_THRESHOLD_1K}s)"
        print(f"\n✓ TA-Lib 1K calculation: {elapsed_time:.3f}s")

    def test_talib_calculation_performance_10k(self):
        """10,000일치 데이터 지표 계산 성능"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        large_df = generate_large_ohlcv(days=10000)
        indicators = TechnicalIndicators()

        start_time = time.time()
        result = indicators.calculate_all(large_df)
        elapsed_time = time.time() - start_time

        assert len(result) == 10000
        assert elapsed_time < TALIB_THRESHOLD_10K, \
            f"Too slow: {elapsed_time:.3f}s for 10,000 days (threshold: {TALIB_THRESHOLD_10K}s)"
        print(f"\n✓ TA-Lib 10K calculation: {elapsed_time:.3f}s")

    def test_individual_indicator_performance(self):
        """개별 지표 계산 성능 비교"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        df = generate_large_ohlcv(days=1000)
        indicators = TechnicalIndicators()

        # Test individual indicators
        timings = {}

        # SMA
        start = time.time()
        indicators.calculate_sma(df, period=20)
        timings['SMA'] = time.time() - start

        # RSI
        start = time.time()
        indicators.calculate_rsi(df, period=14)
        timings['RSI'] = time.time() - start

        # MACD
        start = time.time()
        indicators.calculate_macd(df)
        timings['MACD'] = time.time() - start

        # Bollinger Bands
        start = time.time()
        indicators.calculate_bbands(df)
        timings['BBands'] = time.time() - start

        print("\n✓ Individual indicator timings (1000 days):")
        for name, timing in timings.items():
            print(f"  {name}: {timing:.4f}s")
            assert timing < 0.1, f"{name} too slow: {timing:.4f}s"

    def test_talib_memory_usage(self):
        """TA-Lib 지표 계산 메모리 사용량"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        large_df = generate_large_ohlcv(days=10000)
        indicators = TechnicalIndicators()

        mem_before = measure_memory_usage()
        result = indicators.calculate_all(large_df)
        mem_after = measure_memory_usage()

        memory_increase = mem_after - mem_before
        print(f"\n✓ Memory increase for 10K TA-Lib calculation: {memory_increase:.2f} MB")

        # Should not exceed 200MB for 10K days with all indicators
        assert memory_increase < 200, f"Excessive memory usage: {memory_increase:.2f} MB"


@pytest.mark.performance
class TestFullPipelinePerformance:
    """전체 파이프라인 성능 테스트"""

    def test_full_pipeline_1k(self):
        """전체 파이프라인 성능 (1,000 레코드)"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        # Generate data
        price_dicts = generate_price_dict_list(1000)

        start_time = time.time()

        # Step 1: Validate with Pydantic
        schemas = [DailyPriceSchema(**item) for item in price_dicts]

        # Step 2: Convert to DataFrame
        df = pd.DataFrame([s.model_dump() for s in schemas])

        # Step 3: Calculate indicators
        indicators = TechnicalIndicators()
        df_with_indicators = indicators.calculate_all(df)

        elapsed_time = time.time() - start_time

        assert len(df_with_indicators) == 1000
        assert elapsed_time < PIPELINE_THRESHOLD_1K, \
            f"Pipeline too slow: {elapsed_time:.3f}s (threshold: {PIPELINE_THRESHOLD_1K}s)"
        print(f"\n✓ Full pipeline (1K): {elapsed_time:.3f}s")

    def test_pipeline_scalability(self):
        """파이프라인 확장성 테스트 (100, 500, 1000, 5000)"""
        if DailyPriceSchema is None or TechnicalIndicators is None:
            pytest.skip("Waiting for Agent 1 and Agent 2")

        sizes = [100, 500, 1000, 5000]
        timings = []

        for size in sizes:
            price_dicts = generate_price_dict_list(size)

            start_time = time.time()
            schemas = [DailyPriceSchema(**item) for item in price_dicts]
            df = pd.DataFrame([s.model_dump() for s in schemas])
            indicators = TechnicalIndicators()
            df_with_indicators = indicators.calculate_all(df)
            elapsed_time = time.time() - start_time

            timings.append(elapsed_time)
            print(f"  {size} records: {elapsed_time:.3f}s")

        # Check linear scalability (within 2x tolerance)
        print("\n✓ Pipeline scalability test:")
        for i in range(len(sizes) - 1):
            ratio = timings[i + 1] / timings[i]
            size_ratio = sizes[i + 1] / sizes[i]
            print(f"  {sizes[i]} -> {sizes[i+1]}: {ratio:.2f}x time for {size_ratio:.1f}x data")
            # Scalability should be roughly linear (allow up to 2x overhead)
            assert ratio < size_ratio * 2, f"Poor scalability: {ratio:.2f}x"


@pytest.mark.performance
class TestConcurrentProcessing:
    """병렬 처리 성능 테스트"""

    def test_parallel_validation(self):
        """병렬 검증 성능 (멀티스레딩)"""
        if DailyPriceSchema is None:
            pytest.skip("DailyPriceSchema not yet implemented by Agent 1")

        from concurrent.futures import ThreadPoolExecutor

        large_data = generate_price_dict_list(10000)

        # Sequential
        start_time = time.time()
        validated_seq = [DailyPriceSchema(**item) for item in large_data]
        seq_time = time.time() - start_time

        # Parallel (4 threads)
        def validate_chunk(chunk):
            return [DailyPriceSchema(**item) for item in chunk]

        chunk_size = len(large_data) // 4
        chunks = [large_data[i:i + chunk_size] for i in range(0, len(large_data), chunk_size)]

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(validate_chunk, chunks))
        validated_par = [item for sublist in results for item in sublist]
        par_time = time.time() - start_time

        print(f"\n✓ Validation performance:")
        print(f"  Sequential: {seq_time:.3f}s")
        print(f"  Parallel (4 threads): {par_time:.3f}s")
        print(f"  Speedup: {seq_time/par_time:.2f}x")

        assert len(validated_par) == 10000

    @pytest.mark.slow
    def test_parallel_indicator_calculation(self):
        """병렬 지표 계산 (멀티스톡)"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        from concurrent.futures import ThreadPoolExecutor

        # Generate data for 10 different stocks
        stocks = [f"00593{i}" for i in range(10)]
        stock_data = {stock: generate_large_ohlcv(days=1000) for stock in stocks}

        indicators = TechnicalIndicators()

        # Sequential
        start_time = time.time()
        results_seq = {stock: indicators.calculate_all(df) for stock, df in stock_data.items()}
        seq_time = time.time() - start_time

        # Parallel
        def calc_indicators(stock_df_tuple):
            stock, df = stock_df_tuple
            return stock, indicators.calculate_all(df)

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            results_par = dict(executor.map(calc_indicators, stock_data.items()))
        par_time = time.time() - start_time

        print(f"\n✓ Multi-stock indicator calculation:")
        print(f"  Sequential: {seq_time:.3f}s")
        print(f"  Parallel (4 workers): {par_time:.3f}s")
        print(f"  Speedup: {seq_time/par_time:.2f}x")


@pytest.mark.performance
class TestBenchmarks:
    """벤치마크 및 성능 기준선"""

    def test_baseline_pandas_operations(self):
        """Pandas 기본 연산 벤치마크"""
        df = generate_large_ohlcv(days=10000)

        # Rolling mean
        start = time.time()
        df['ma20'] = df['close'].rolling(window=20).mean()
        rolling_time = time.time() - start

        # Pct change
        start = time.time()
        df['returns'] = df['close'].pct_change()
        pct_change_time = time.time() - start

        # Group by (simulated multi-stock)
        df['stock'] = '005930'
        start = time.time()
        grouped = df.groupby('stock')['close'].mean()
        groupby_time = time.time() - start

        print(f"\n✓ Pandas baseline benchmarks (10K rows):")
        print(f"  Rolling mean: {rolling_time:.4f}s")
        print(f"  Pct change: {pct_change_time:.4f}s")
        print(f"  Group by: {groupby_time:.4f}s")

    def test_compare_numpy_vs_talib(self):
        """NumPy vs TA-Lib 성능 비교"""
        if TechnicalIndicators is None:
            pytest.skip("TechnicalIndicators not yet implemented by Agent 2")

        df = generate_large_ohlcv(days=1000)

        # NumPy SMA
        start = time.time()
        numpy_sma = df['close'].rolling(window=20).mean()
        numpy_time = time.time() - start

        # TA-Lib SMA
        indicators = TechnicalIndicators()
        start = time.time()
        talib_result = indicators.calculate_sma(df, period=20)
        talib_time = time.time() - start

        print(f"\n✓ NumPy vs TA-Lib (SMA-20, 1000 days):")
        print(f"  NumPy: {numpy_time:.4f}s")
        print(f"  TA-Lib: {talib_time:.4f}s")
        print(f"  Ratio: {talib_time/numpy_time:.2f}x")


# Performance summary fixture
@pytest.fixture(scope="session", autouse=True)
def performance_summary(request):
    """Print performance test summary at the end"""
    yield

    print("\n" + "=" * 70)
    print("PERFORMANCE TEST SUMMARY")
    print("=" * 70)
    print(f"Thresholds:")
    print(f"  - Pydantic validation (10K): < {VALIDATION_THRESHOLD_10K}s")
    print(f"  - TA-Lib calculation (1K): < {TALIB_THRESHOLD_1K}s")
    print(f"  - TA-Lib calculation (10K): < {TALIB_THRESHOLD_10K}s")
    print(f"  - Full pipeline (1K): < {PIPELINE_THRESHOLD_1K}s")
    print("=" * 70 + "\n")
