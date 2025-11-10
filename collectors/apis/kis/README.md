# KIS API Client

한국투자증권(Korean Investment & Securities) OpenAPI 클라이언트 라이브러리입니다.

## 특징

- **OAuth 2.0 인증**: 자동 토큰 관리 및 갱신
- **국내주식 시세**: 현재가, 일봉 데이터 조회
- **해외주식 시세**: 미국, 중국, 일본 등 주요 거래소 지원
- **Rate Limiting**: Token Bucket 알고리즘으로 API 제한 준수
- **Type Safety**: Pydantic 스키마로 타입 안정성 보장
- **Mock Client**: 실제 API 없이 테스트 가능
- **Retry 로직**: 네트워크 오류 자동 재시도
- **Error Handling**: 체계적인 예외 처리

## 설치

```bash
pip install pydantic requests
```

## 환경 설정

`.env` 파일에 KIS API 인증 정보를 설정하세요:

```env
KIS_APP_KEY=your_app_key_here
KIS_APP_SECRET=your_app_secret_here
KIS_USE_VIRTUAL=true  # true: 모의투자, false: 실전투자
```

## 빠른 시작

### 1. Mock Client로 시작하기 (추천)

실제 API 키 없이 바로 테스트할 수 있습니다:

```python
from collectors.apis.kis import MockKISClient, KISExchange

# Mock client 생성
with MockKISClient() as client:
    # 국내 주식 현재가
    price = client.get_stock_price("005930")
    print(f"{price.name}: {price.current_price:,}원")

    # 해외 주식 현재가
    apple = client.get_overseas_stock("AAPL", KISExchange.NASDAQ)
    print(f"{apple.name}: ${apple.current_price}")
```

### 2. 실제 API 사용하기

환경 변수 설정 후:

```python
from collectors.apis.kis import KISClient

# 실제 API client 생성
with KISClient() as client:
    price = client.get_stock_price("005930")
    print(f"{price.name}: {price.current_price:,}원")
```

## 주요 기능

### 국내 주식 현재가 조회

```python
from collectors.apis.kis import MockKISClient

with MockKISClient() as client:
    # 삼성전자 현재가
    price = client.get_stock_price("005930")

    print(f"종목: {price.name} ({price.code})")
    print(f"현재가: {price.current_price:,}원")
    print(f"시가: {price.open:,}원")
    print(f"고가: {price.high:,}원")
    print(f"저가: {price.low:,}원")
    print(f"거래량: {price.volume:,}주")
    print(f"등락: {price.change:+,}원 ({price.change_rate:+.2f}%)")
```

### 국내 주식 일봉 데이터

```python
from datetime import date, timedelta

with MockKISClient() as client:
    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    # 30일 일봉 데이터
    history = client.get_daily_price(
        "005930",
        start_date=start_date,
        end_date=end_date
    )

    for item in history[:5]:  # 최근 5일
        print(f"{item.date}: {item.close:,}원")
```

### 해외 주식 현재가

```python
from collectors.apis.kis import KISExchange

with MockKISClient() as client:
    # Apple (NASDAQ)
    apple = client.get_overseas_stock("AAPL", KISExchange.NASDAQ)
    print(f"{apple.name}: ${apple.current_price}")

    # Tencent (Hong Kong)
    tencent = client.get_overseas_stock("00700", KISExchange.HKEX)
    print(f"{tencent.name}: {tencent.currency} {tencent.current_price}")
```

### 해외 주식 일봉 데이터

```python
with MockKISClient() as client:
    # Apple 최근 30일 데이터
    history = client.get_overseas_daily(
        "AAPL",
        KISExchange.NASDAQ,
        period=30
    )

    for item in history[:5]:
        print(f"{item.date}: ${item.close:.2f}")
```

## 지원하는 거래소

- `KISExchange.NASDAQ`: 나스닥
- `KISExchange.NYSE`: 뉴욕증권거래소
- `KISExchange.AMEX`: 아메리칸증권거래소
- `KISExchange.HKEX`: 홍콩증권거래소
- `KISExchange.TSE`: 도쿄증권거래소
- `KISExchange.SSE`: 상하이증권거래소
- `KISExchange.SZSE`: 선전증권거래소

## 에러 처리

```python
from collectors.apis.kis import (
    KISClient,
    KISAPIError,
    KISNetworkError,
    KISRateLimitError
)

try:
    with KISClient() as client:
        price = client.get_stock_price("005930")

except KISRateLimitError as e:
    print(f"Rate limit exceeded. Retry after {e.retry_after}s")

except KISNetworkError as e:
    print(f"Network error: {e}")

except KISAPIError as e:
    print(f"API error: {e}")
```

## Rate Limiting

초당 5회 API 호출 제한이 자동으로 적용됩니다:

```python
from collectors.apis.kis import TokenBucketRateLimiter

# 커스텀 rate limiter
limiter = TokenBucketRateLimiter(rate=10, per_seconds=1)

# 토큰 획득
limiter.acquire()  # 블로킹
result = limiter.try_acquire()  # 논블로킹

# 사용 가능한 토큰 수
available = limiter.get_available_tokens()
```

## 배치 처리 예제

```python
from collectors.apis.kis import MockKISClient

# 여러 종목 동시 조회
stocks = ["005930", "000660", "035420", "035720"]

with MockKISClient() as client:
    for code in stocks:
        try:
            price = client.get_stock_price(code)
            print(f"{price.name}: {price.current_price:,}원")
        except Exception as e:
            print(f"{code} 조회 실패: {e}")
```

## 스키마 (Pydantic Models)

### KISStockPrice
국내 주식 현재가 정보

```python
@dataclass
class KISStockPrice:
    code: str           # 종목코드
    name: str           # 종목명
    current_price: int  # 현재가
    open: int           # 시가
    high: int           # 고가
    low: int            # 저가
    volume: int         # 거래량
    change: int         # 전일대비
    change_rate: float  # 등락률
```

### KISDailyPrice
국내 주식 일봉 데이터

```python
@dataclass
class KISDailyPrice:
    code: str
    date: date
    open: int
    high: int
    low: int
    close: int
    volume: int
```

### KISOverseasStock
해외 주식 현재가 정보

```python
@dataclass
class KISOverseasStock:
    symbol: str          # 티커
    exchange: KISExchange
    name: str
    current_price: float
    open: float
    high: float
    low: float
    volume: int
    currency: str        # USD, HKD, JPY 등
```

## 테스트

```bash
# 단위 테스트
pytest tests/unit/test_kis_*.py -v

# 통합 테스트
pytest tests/integration/test_kis_integration.py -v

# 빠른 테스트
python test_kis_quick.py

# 예제 실행
python -m collectors.apis.kis.examples
```

## 아키텍처

```
collectors/apis/kis/
├── __init__.py           # 패키지 exports
├── auth.py               # OAuth 2.0 인증
├── client.py             # KIS API 클라이언트
├── mock_client.py        # Mock 클라이언트
├── schemas.py            # Pydantic 스키마
├── rate_limiter.py       # Rate limiter
├── examples.py           # 사용 예제
└── README.md             # 문서 (이 파일)
```

## API 제한사항

- **Rate Limit**: 초당 5회 (기본값)
- **일봉 데이터**: 최대 100일치
- **인증 토큰**: 24시간 유효
- **거래 시간**: KST 09:00-15:30 (국내), 현지 시간 (해외)

## 참고 문서

- [한국투자증권 OpenAPI 공식 문서](https://apiportal.koreainvestment.com)
- [KIS API 가이드](https://wikidocs.net/profile/info/book/16885)

## 라이선스

MIT License

## 개발

TDD(Test-Driven Development) 방식으로 개발되었습니다:
- 30개 이상의 단위 테스트
- 5개 이상의 통합 테스트
- Mock 클라이언트로 실제 API 없이 개발 가능

## 버전

**v1.0.0** (2024-11-10)
- OAuth 2.0 인증 구현
- 국내/해외 주식 시세 조회
- Rate limiting 구현
- Mock client 구현
- Pydantic 스키마 검증

## 기여

버그 리포트와 기능 제안을 환영합니다!
