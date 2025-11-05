# 키움증권 API 주식 백테스팅 시스템

키움증권 OpenAPI를 활용하여 코스피/코스닥 전종목의 과거 데이터를 수집하고 백테스팅을 수행하는 시스템입니다.

## 주요 기능

- **전종목 데이터 수집**: 코스피, 코스닥 전 종목의 과거 5년치 일봉 데이터 수집
- **데이터베이스 저장**: SQLite 또는 PostgreSQL에 체계적으로 저장
- **백테스팅 엔진**: 수집된 데이터로 다양한 전략 백테스트
- **Rate Limiting**: API 호출 제한 자동 관리 (초당 5회)
- **로깅 시스템**: 수집 과정 및 오류 추적

## 프로젝트 구조

```
claude-code-web/
├── config/                  # 설정 파일
│   ├── __init__.py
│   └── kiwoom_config.py     # 키움 API 및 프로젝트 설정
├── db/                      # 데이터베이스
│   ├── __init__.py
│   ├── models.py            # SQLAlchemy 모델
│   └── database.py          # DB 연결 관리
├── collectors/              # 데이터 수집
│   ├── __init__.py
│   ├── kiwoom_api.py        # 키움 API 래퍼
│   └── stock_collector.py   # 데이터 수집기
├── utils/                   # 유틸리티
│   ├── __init__.py
│   ├── logger.py            # 로깅 설정
│   └── rate_limiter.py      # API 호출 제한 관리
├── backtest/                # 백테스팅
│   ├── __init__.py
│   ├── engine.py            # 백테스트 엔진
│   └── strategy.py          # 전략 베이스 클래스
├── scripts/                 # 실행 스크립트
│   ├── init_db.py           # DB 초기화
│   ├── collect_stock_list.py      # 종목 리스트 수집
│   ├── collect_daily_prices.py    # 일봉 데이터 수집
│   ├── update_latest.py     # 최신 데이터 업데이트
│   └── run_backtest.py      # 백테스트 실행
├── data/                    # 데이터 저장 디렉토리 (자동 생성)
├── logs/                    # 로그 파일 (자동 생성)
├── requirements.txt         # Python 패키지 의존성
├── .env.example             # 환경 변수 예시
└── README.md                # 본 문서
```

## 필수 요구사항

### 소프트웨어
- Python 3.8 이상
- Windows OS (키움 OpenAPI는 Windows 전용)
- 키움증권 계좌 및 OpenAPI+ 설치

### 키움 OpenAPI+ 설치
1. 키움증권 홈페이지에서 OpenAPI+ 다운로드
2. 설치 후 버전처리 실행
3. 모의투자 또는 실계좌 로그인 테스트

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd claude-code-web
```

### 2. 가상 환경 생성 및 활성화

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정 (선택사항)

```bash
copy .env.example .env
# .env 파일을 편집하여 필요한 설정 변경
```

## 사용 방법

### 1단계: 데이터베이스 초기화

```bash
python scripts/init_db.py
```

데이터베이스 테이블이 생성됩니다.

### 2단계: 종목 리스트 수집

```bash
python scripts/collect_stock_list.py
```

코스피, 코스닥의 전체 종목 리스트를 수집합니다 (약 2,400개).
소요시간: 약 5-10분

### 3단계: 과거 데이터 수집

```bash
# 전체 종목 5년치 데이터 수집
python scripts/collect_daily_prices.py --years 5

# 특정 종목만 수집 (예: 삼성전자)
python scripts/collect_daily_prices.py --code 005930 --years 5
```

**주의**: 전체 종목 수집은 **2-3일** 소요됩니다!
- 약 2,400개 종목 × 5년 데이터
- API 호출 제한으로 인한 자동 지연
- 중간에 중단해도 수집된 데이터는 DB에 저장됨

### 4단계: 백테스트 실행

```bash
# 삼성전자 1년 백테스트 (이동평균 교차 전략)
python scripts/run_backtest.py --code 005930 --start 2023-01-01 --end 2024-01-01

# 다른 이동평균 기간으로 테스트
python scripts/run_backtest.py --code 005930 --short-ma 5 --long-ma 20 --capital 50000000
```

### 일일 업데이트

장 마감 후 최신 데이터 업데이트:

```bash
python scripts/update_latest.py
```

## 데이터베이스 스키마

### stocks (종목 정보)
- code: 종목코드 (PK)
- name: 종목명
- market: 시장구분 (KOSPI/KOSDAQ)
- sector: 업종
- listing_date: 상장일

### daily_prices (일봉 데이터)
- stock_code: 종목코드 (FK)
- date: 날짜
- open, high, low, close: OHLC
- volume: 거래량
- trading_value: 거래대금
- adj_close: 수정주가

### stock_info (종목 상세 정보)
- stock_code: 종목코드 (FK)
- market_cap: 시가총액
- per, pbr, roe: 재무 지표
- eps, bps: 주당 지표

### collection_logs (수집 로그)
- 데이터 수집 이력 및 오류 추적

## 백테스팅 전략 추가

새로운 전략을 추가하려면 `BaseStrategy`를 상속받아 구현:

```python
# backtest/strategy.py
from backtest.strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(name="MyStrategy")

    def generate_signals(self, data):
        # 매매 신호 생성 로직
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0
        # ... 전략 로직 ...
        return signals
```

## 백테스팅에 필요한 데이터

### 필수 데이터
1. **일별 OHLCV**: 시가, 고가, 저가, 종가, 거래량
2. **종목 정보**: 종목코드, 종목명, 시장구분
3. **수정주가**: 배당/액면분할 반영

### 선택적 데이터 (전략에 따라)
4. **재무 지표**: PER, PBR, ROE 등
5. **투자자별 매매**: 기관, 외국인, 개인
6. **분봉 데이터**: 단기 매매 전략용

## 성능 최적화

### 데이터 수집
- 배치 커밋: 100개 종목마다 DB 커밋
- Rate Limiter: 초당 5회 제한 자동 관리
- 재시도 로직: 실패 시 최대 3회 재시도

### 백테스팅
- 벡터화 연산: pandas 활용
- 인덱싱: 날짜별, 종목별 인덱스
- 메모리 효율: 필요한 기간만 로드

## 문제 해결

### 키움 API 로그인 실패
- 키움 OpenAPI+ 설치 확인
- 키움증권 HTS 로그인 상태 확인
- 방화벽 설정 확인

### 데이터 수집 중단
- 로그 파일 확인: `logs/collect_daily_prices_YYYYMMDD.log`
- 중단된 시점부터 재개 가능
- 이미 수집된 데이터는 유지됨

### 메모리 부족
- PostgreSQL 사용 권장 (대용량 데이터)
- 배치 크기 조정: `config/kiwoom_config.py`의 `BATCH_SIZE`

## 주의사항

1. **API 제한**: 키움 API는 초당 5회 제한이 있습니다
2. **거래 시간**: 장중(09:00-15:30)에는 실시간 데이터만 조회 가능
3. **데이터 정확성**: 수정주가 확인 필요
4. **법적 책임**: 실제 투자 시 발생하는 손실은 본인 책임입니다

## 라이센스

MIT License

## 기여

버그 리포트, 기능 제안, Pull Request 환영합니다!

## 연락처

문의사항은 Issues를 통해 남겨주세요.

---

**면책 조항**: 본 프로젝트는 교육 및 연구 목적입니다. 실제 투자에 사용 시 발생하는 손실에 대해 개발자는 책임지지 않습니다.
