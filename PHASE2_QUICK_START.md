# Phase 2 Quick Start Guide

## Running Tests

### Option 1: Custom Test Runner (Recommended)
```bash
cd c:\Users\andms\Desktop\kiwoom-auto\claude-code-web
python run_phase2_tests.py
```

### Option 2: Individual Component Testing
```bash
# Test Mock APIs
python -c "from tests.fixtures.mock_apis import MockKISAPI; api = MockKISAPI(); print(api.get_stock_price('005930'))"

# Test Cache
python -c "from collectors.apis.cache import APICache; cache = APICache(); cache.set('test', 'value'); print(cache.get('test'))"

# Test UnifiedAPIClient
python -c "from collectors.apis.unified import UnifiedAPIClient, DataSource; from tests.fixtures.mock_apis import MockKISAPI; client = UnifiedAPIClient(kis_api=MockKISAPI()); print(client.get_stock_price('005930', DataSource.KIS))"
```

## Quick Usage Examples

### 1. Basic Stock Price Query
```python
from collectors.apis.unified import UnifiedAPIClient, DataSource
from tests.fixtures.mock_apis import MockKISAPI, MockKiwoomAPI

# Create client
client = UnifiedAPIClient(
    kis_api=MockKISAPI(),
    kiwoom_api=MockKiwoomAPI()
)

# Get stock price (auto fallback)
price = client.get_stock_price("005930", source=DataSource.AUTO)
print(f"Price: {price['current_price']:,}원")
```

### 2. Overseas Stock
```python
# Get US stock
apple = client.get_overseas_stock("AAPL", "NASDAQ")
print(f"AAPL: ${apple['current_price']}")
```

### 3. Financial Analysis
```python
from tests.fixtures.mock_apis import MockDARTAPI

client = UnifiedAPIClient(
    kis_api=MockKISAPI(),
    dart_api=MockDARTAPI()
)

# Get comprehensive data
data = client.get_comprehensive_data("005930", year=2023, quarter=4)
print(f"PER: {data['metrics']['per']}")
print(f"ROE: {data['metrics']['roe']}%")
```

### 4. Multi-Stock Screening
```python
import pandas as pd

stocks = ["005930", "000660", "035720"]
results = []

for code in stocks:
    data = client.get_comprehensive_data(code, year=2023, quarter=4)
    results.append({
        'code': code,
        'price': data['price']['current_price'],
        'roe': data['metrics']['roe'],
    })

df = pd.DataFrame(results)
print(df[df['roe'] > 15])  # High ROE stocks
```

## File Locations

### Core Implementation
- `collectors/apis/unified.py` - UnifiedAPIClient
- `collectors/apis/cache.py` - APICache

### Mock APIs
- `tests/fixtures/mock_apis.py` - Mock implementations

### Tests
- `tests/integration/test_unified_api.py` - Integration tests
- `tests/integration/test_phase2_pipeline.py` - Pipeline tests
- `tests/e2e/test_overseas_backtest.py` - Overseas backtesting
- `tests/e2e/test_fundamental_analysis.py` - Fundamental analysis

## Key Classes

### UnifiedAPIClient
```python
UnifiedAPIClient(
    kiwoom_api=None,    # Kiwoom API instance
    kis_api=None,       # KIS API instance
    dart_api=None,      # DART API instance
    cache_ttl=60,       # Cache TTL in seconds
    enable_cache=True   # Enable/disable caching
)
```

**Methods**:
- `get_stock_price(code, source=DataSource.AUTO)` - Get stock price
- `get_overseas_stock(symbol, exchange)` - Get overseas stock
- `get_financial_data(code, year, quarter)` - Get financial data
- `get_comprehensive_data(code, year, quarter)` - Get all data + metrics
- `get_cache_stats()` - Get cache statistics
- `clear_cache()` - Clear cache

### DataSource Enum
```python
DataSource.KIWOOM  # Use Kiwoom only
DataSource.KIS     # Use KIS only
DataSource.AUTO    # Auto fallback (KIS → Kiwoom)
```

### APICache
```python
APICache(
    ttl_seconds=60,    # Time to live
    max_size=1000      # Max cache entries
)
```

**Methods**:
- `get(key)` - Get cached value
- `set(key, value, ttl_seconds=None)` - Set cache value
- `delete(key)` - Delete cache entry
- `clear()` - Clear all cache
- `get_stats()` - Get cache statistics

## Integration with Real APIs

### Step 1: Import Real APIs (When Agent 1 & 2 Complete)
```python
# Instead of mocks, use real implementations
from collectors.apis.kis import KISAPIClient  # From Agent 1
from collectors.apis.dart import DARTAPIClient  # From Agent 2

# Create real client
client = UnifiedAPIClient(
    kis_api=KISAPIClient(app_key="...", app_secret="..."),
    dart_api=DARTAPIClient(api_key="...")
)
```

### Step 2: Test with Real Data
```python
# Same API, real data!
price = client.get_stock_price("005930", DataSource.AUTO)
```

## Troubleshooting

### Issue: Tests fail with import errors
**Solution**: Ensure you're in the project root directory
```bash
cd c:\Users\andms\Desktop\kiwoom-auto\claude-code-web
```

### Issue: Cache not working
**Solution**: Check if cache is enabled
```python
client = UnifiedAPIClient(kis_api=api, enable_cache=True)
stats = client.get_cache_stats()
print(stats)
```

### Issue: All sources fail
**Solution**: Check mock API initialization
```python
# Ensure APIs are not in fail mode
kis = MockKISAPI(fail=False)
client = UnifiedAPIClient(kis_api=kis)
```

## Performance Tips

1. **Enable caching** for frequently accessed data
2. **Use batch requests** when querying multiple stocks
3. **Monitor cache hit rate** via `get_cache_stats()`
4. **Adjust TTL** based on data update frequency
5. **Use AUTO mode** for automatic fallback

## Next Steps

1. ✅ Run tests: `python run_phase2_tests.py`
2. ⏳ Wait for Agent 1 (KIS API) completion
3. ⏳ Wait for Agent 2 (DART API) completion
4. 🔄 Replace mocks with real APIs
5. 🔄 Test with production data
6. 🔄 Deploy to production

## Support

- **Full Documentation**: `PHASE2_INTEGRATION_REPORT.md`
- **Test Results**: Run `python run_phase2_tests.py`
- **Code Examples**: See test files in `tests/` directory

---

**Status**: ✅ Ready for Integration
**Last Updated**: 2025-11-10
