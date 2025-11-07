# 분봉/틱 데이터 수집 가이드

키움증권 OpenAPI를 통한 분봉 및 틱 데이터 수집 기능 사용 가이드입니다.

## 목차
1. [기능 개요](#기능-개요)
2. [설치 및 설정](#설치-및-설정)
3. [데이터 수집 방법](#데이터-수집-방법)
4. [API 제약사항](#api-제약사항)
5. [성능 최적화](#성능-최적화)

---

## 기능 개요

### 지원하는 데이터 타입

#### 1. 분봉 데이터 (MinutePrice)
- **지원 간격**: 1분, 5분, 10분, 30분, 60분
- **최대 조회**: 900개 (연속조회 가능)
- **데이터 항목**: 시가, 고가, 저가, 종가, 거래량
- **용도**: 단기/초단기 백테스팅, 전략 분석

#### 2. 틱 데이터 (TickPrice)
- **최대 조회**: 600틱 (연속조회 불가)
- **데이터 항목**: 체결가, 체결량, 전일대비, 매도/매수 호가
- **용도**: 초단타 매매 분석, 실시간 모니터링
- **제약사항**: 과거 데이터 제한적 (최근 600틱만)

---

## 설치 및 설정

### 1. 데이터베이스 마이그레이션

새로운 TickPrice 테이블을 추가합니다:

```bash
python migrate_db.py
```

### 2. 설정 확인

`config/kiwoom_config.py`에서 설정을 확인/수정할 수 있습니다:

```python
# 분봉 수집 설정
MINUTE_INTERVALS = [1, 5, 10, 30, 60]  # 수집할 분봉 간격
MINUTE_COUNT = 900  # 분봉 수집 개수

# 틱 데이터 설정
TICK_COUNT = 600  # 틱 데이터 수집 개수 (최대 600)
```

---

## 데이터 수집 방법

### 1. 단일 종목 분봉 수집

```python
from collectors.stock_collector import StockCollector

collector = StockCollector()
collector.login()

# 60분봉 100개 수집
collector.collect_minute_price("005930", interval=60, count=100)

# 10분봉 500개 수집
collector.collect_minute_price("005930", interval=10, count=500)

collector.logout()
```

### 2. 다중 종목 분봉 수집

```python
from collectors.stock_collector import StockCollector

collector = StockCollector()
collector.login()

# 특정 종목 리스트
stock_codes = ["005930", "000660", "035420"]

# 60분, 30분, 10분 분봉 수집 (각 500개)
result = collector.collect_all_minute_prices(
    intervals=[60, 30, 10],
    count=500,
    stock_codes=stock_codes
)

print(f"수집 결과: {result}")

collector.logout()
```

### 3. 단일 종목 틱 데이터 수집

```python
from collectors.stock_collector import StockCollector

collector = StockCollector()
collector.login()

# 틱 데이터 600개 수집
collector.collect_tick_data("005930", count=600)

collector.logout()
```

### 4. 다중 종목 틱 데이터 수집

```python
from collectors.stock_collector import StockCollector

collector = StockCollector()
collector.login()

# 특정 종목 리스트
stock_codes = ["005930", "000660", "035420"]

# 틱 데이터 수집
result = collector.collect_all_tick_data(
    count=600,
    stock_codes=stock_codes
)

print(f"수집 결과: {result}")

collector.logout()
```

### 5. 테스트 스크립트 사용

간편한 테스트를 위한 대화형 스크립트:

```bash
python test_minute_tick_collection.py
```

메뉴:
1. 단일 종목 분봉 데이터 수집 (삼성전자)
2. 단일 종목 틱 데이터 수집 (삼성전자)
3. 다중 종목 분봉 데이터 수집 (대표 5개 종목)
4. 다중 종목 틱 데이터 수집 (대표 5개 종목)
5. 전체 테스트 실행

---

## API 제약사항

### 키움 OpenAPI 제한

1. **Rate Limit**: 초당 5회 요청 제한
   - 현재 설정: 1초당 1회 (안전 마진)

2. **분봉 데이터**:
   - 최대 900개까지 조회 가능
   - 연속 조회 지원 (더 많은 데이터 수집 가능)

3. **틱 데이터**:
   - 최대 600틱만 조회 가능
   - 연속 조회 불가능 (과거 데이터 제한적)

### 데이터 용량 추정

#### 분봉 데이터 (코스피+코스닥 2,500종목 기준)

| 분봉 간격 | 1개월 데이터 용량 |
|----------|-----------------|
| 1분봉 | 약 3GB |
| 5분봉 | 약 600MB |
| 10분봉 | 약 300MB |
| 30분봉 | 약 100MB |
| 60분봉 | 약 50MB |

#### 틱 데이터

| 항목 | 값 |
|-----|-----|
| 최대 레코드 | 1,500,000개 (600틱 × 2,500종목) |
| 예상 용량 | 약 200MB |
| 비고 | 갱신식 (최근 600틱만 유지) |

### 수집 시간 추정

#### 전체 종목 (2,500개) 기준

| 작업 | 소요 시간 |
|-----|---------|
| 5종류 분봉 (1/5/10/30/60분) | 약 3.5시간 |
| 틱 데이터 | 약 40분 |
| 전체 (분봉 + 틱) | 약 4시간 10분 |

---

## 성능 최적화

### 1. 선택적 수집 전략

#### 추천 방법 1: 핵심 분봉만 수집
```python
# 60분, 10분, 1분만 수집 (3종류)
collector.collect_all_minute_prices(
    intervals=[60, 10, 1],
    count=500,
    stock_codes=target_stocks  # 필터링된 종목
)
```

#### 추천 방법 2: 주요 종목만 수집
```python
# 코스피200 + 거래량 상위 종목만
from db.database import session_scope
from db.models import Stock

with session_scope() as session:
    # 종목 필터링 로직
    top_stocks = session.query(Stock).filter(
        Stock.market == 'KOSPI'
    ).limit(200).all()

    stock_codes = [s.code for s in top_stocks]

# 필터링된 종목만 수집
collector.collect_all_minute_prices(
    intervals=[60, 10],
    count=500,
    stock_codes=stock_codes
)
```

### 2. 데이터 보관 전략

#### 단계적 보관
```python
# 최근 1개월: 1분봉
# 최근 3개월: 5분봉, 10분봉
# 최근 1년: 30분봉, 60분봉
```

### 3. 증분 업데이트

기존 데이터가 있는 종목은 자동으로 스킵됩니다:

```python
# 중복 체크: datetime + interval 기준
existing = session.query(MinutePrice).filter_by(
    stock_code=stock_code,
    datetime=dt,
    interval=interval
).first()

if existing:
    continue  # 이미 존재하면 스킵
```

### 4. 틱 데이터 활용 가이드

#### 권장 용도
- ✅ 실시간 트레이딩 모니터링
- ✅ 최근 체결 동향 분석
- ❌ 장기 백테스팅 (1분봉 권장)

#### 대안
```python
# 백테스팅용: 틱 대신 1분봉 사용
collector.collect_minute_price("005930", interval=1, count=900)
```

---

## 문제 해결

### 1. 타임아웃 발생

```python
# 재시도 로직 자동 적용됨
# max_retries = 2 (기본값)
# 3초 대기 후 재시도
```

### 2. 데이터 수집 실패

로그 확인:
```bash
# 로그 파일 확인
ls -lh logs/
```

수집 로그 조회:
```python
from db.database import session_scope
from db.models import CollectionLog

with session_scope() as session:
    failed_logs = session.query(CollectionLog).filter_by(
        status='failed'
    ).all()

    for log in failed_logs:
        print(f"{log.stock_code}: {log.error_message}")
```

### 3. 메모리 부족

배치 크기 조정:
```python
# 한 번에 처리할 종목 수 줄이기
batch_size = 100
for i in range(0, len(all_stocks), batch_size):
    batch = all_stocks[i:i+batch_size]
    collector.collect_all_minute_prices(stock_codes=batch)
```

---

## 참고 자료

### 키움 API 문서
- [키움증권 OpenAPI 개발가이드](https://www3.kiwoom.com/nkw.templateFrameSet.do?m=m1408000000)

### 관련 파일
- `collectors/kiwoom_api_server.py`: 32비트 API 서버
- `collectors/kiwoom_api_client.py`: 64비트 클라이언트
- `collectors/stock_collector.py`: 데이터 수집기
- `db/models.py`: 데이터 모델 정의
- `config/kiwoom_config.py`: 설정 파일

### DB 스키마

#### MinutePrice 테이블
```sql
CREATE TABLE minute_prices (
    id INTEGER PRIMARY KEY,
    stock_code VARCHAR(10),
    datetime DATETIME,
    interval INTEGER,
    open INTEGER,
    high INTEGER,
    low INTEGER,
    close INTEGER,
    volume BIGINT,
    UNIQUE(stock_code, datetime, interval)
);
```

#### TickPrice 테이블
```sql
CREATE TABLE tick_prices (
    id INTEGER PRIMARY KEY,
    stock_code VARCHAR(10),
    datetime DATETIME,
    price INTEGER,
    volume BIGINT,
    change INTEGER,
    ask_volume BIGINT,
    bid_volume BIGINT,
    market_type VARCHAR(10),
    UNIQUE(stock_code, datetime)
);
```

---

## 라이선스

이 프로젝트는 키움증권 OpenAPI를 사용하며, 개인 투자 목적으로만 사용할 수 있습니다.
