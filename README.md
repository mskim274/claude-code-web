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
├── gui/                     # GUI 애플리케이션
│   ├── __init__.py
│   ├── main_window.py       # 메인 윈도우
│   ├── widgets/             # GUI 위젯
│   │   ├── dashboard.py
│   │   ├── stock_manager.py
│   │   ├── data_collector.py
│   │   ├── backtest_panel.py
│   │   ├── chart_viewer.py
│   │   └── settings.py
│   ├── components/          # 재사용 컴포넌트
│   │   ├── stock_table.py
│   │   ├── progress_dialog.py
│   │   └── chart_widget.py
│   └── utils/               # GUI 유틸리티
│       ├── theme.py
│       └── worker.py
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
├── main.py                  # CLI 실행 파일
├── gui_main.py              # GUI 실행 파일
└── README.md                # 본 문서
```

## 필수 요구사항

### 소프트웨어
- **Python 3.11 32비트** (필수!) - 키움 OpenAPI는 32비트 전용
- Windows OS (키움 OpenAPI는 Windows 전용)
- 키움증권 계좌 및 OpenAPI+ 설치

**중요**: Python은 반드시 **32비트 버전**을 설치해야 합니다. 64비트는 키움 API와 호환되지 않습니다.

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

**중요**: 반드시 32비트 Python 3.11을 사용해야 합니다!

#### Python 3.11 32비트 설치 확인
```bash
# Python 설치 경로 확인 (예시)
C:\Users\[USERNAME]\AppData\Local\Programs\Python\Python311-32\python.exe --version

# 32비트 확인
python -c "import struct; print('32bit' if struct.calcsize('P') * 8 == 32 else '64bit')"
```

#### 가상 환경 생성
```bash
# Python 3.11 32비트로 가상환경 생성
C:\Users\[USERNAME]\AppData\Local\Programs\Python\Python311-32\python.exe -m venv venv

# 가상환경 활성화
venv\Scripts\activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

**설치되는 주요 패키지** (32비트 호환 버전):
- PyQt5 5.15.10 - GUI 프레임워크
- SQLAlchemy 2.0.23 - 데이터베이스 ORM
- pandas 2.0.3 - 데이터 처리 (32비트 최종 지원 버전)
- numpy 1.26.2 - 수치 연산
- matplotlib 3.7.5 - 차트 시각화 (32비트 최종 지원 버전)
- backtrader 1.9.78.123 - 백테스팅 엔진

### 4. 환경 변수 설정 (선택사항)

```bash
copy .env.example .env
# .env 파일을 편집하여 필요한 설정 변경
```

## 사용 방법

### GUI 모드 (권장)

가장 쉬운 사용 방법은 GUI 애플리케이션을 실행하는 것입니다:

```bash
python gui_main.py
```

#### GUI 주요 기능

**1. Dashboard (대시보드)**
- 전체 종목 수 통계 (KOSPI/KOSDAQ 분리)
- 데이터 수집 현황 및 최근 업데이트 시간
- 최근 활동 로그 (최근 5개)
- 빠른 액션 버튼 (데이터 수집, 백테스트)

**2. Stock Manager (종목 관리)**
- 종목 검색 (코드/이름)
- 시장별 필터링 (KOSPI/KOSDAQ/전체)
- 종목 상세 정보 조회
- 데이터 레코드 수 확인
- 직접 데이터 수집/백테스트 실행

**3. Data Collector (데이터 수집)**
- 종목 리스트 수집 (키움 API)
- 전체 종목 일봉 데이터 수집 (1~20년)
- 개별 종목 데이터 수집
- 최신 데이터 업데이트
- 실시간 진행률 표시
- 수집 로그 출력

**4. Backtest (백테스팅)**
- 종목 선택 및 기간 설정
- 전략 선택 (이동평균 교차 등)
- 전략 파라미터 조정 (단기/장기 이동평균)
- 초기 자본금 설정
- 결과 요약 테이블
- 수익률 곡선 차트
- 거래 내역 조회

**5. Chart Viewer (차트 뷰어)**
- 캔들스틱 차트
- 거래량 차트
- 이동평균선 (20일/60일)
- 기간 선택
- 차트 타입 변경 (캔들/라인)

**6. Settings (설정)**
- 데이터베이스 설정 (SQLite/PostgreSQL)
- 로그 레벨 조정
- 기본 수집 연도 설정
- 다크모드 지원 (Ctrl+T)

### CLI 모드

명령줄 인터페이스를 선호하는 경우:

```bash
python main.py
```

대화형 메뉴가 나타납니다.

### 1단계: 데이터베이스 초기화

GUI에서: Dashboard → Quick Actions → 데이터베이스 초기화

또는 CLI:

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

### Python 32비트 / 64비트 오류
**증상**: `ModuleNotFoundError`, `DLL load failed`, 패키지 설치 실패

**해결**:
1. Python 버전 확인:
   ```bash
   python -c "import struct; print('32bit' if struct.calcsize('P') * 8 == 32 else '64bit')"
   ```
2. 32비트가 아니면 Python 3.11 32비트 재설치
3. venv 삭제 후 32비트 Python으로 재생성:
   ```bash
   rmdir /s /q venv
   C:\Users\[USERNAME]\AppData\Local\Programs\Python\Python311-32\python.exe -m venv venv
   ```

### 키움 API 로그인 실패
**증상**: `QAxBase::setControl: requested control KHOPENAPI.KHOpenAPICtrl.1 could not be instantiated`

**해결**:
- 키움 OpenAPI+ 설치 확인
- 32비트 Python 사용 확인 (필수!)
- 키움증권 HTS 로그인 상태 확인
- 방화벽 설정 확인
- Windows 재부팅 후 재시도

### pandas/matplotlib 설치 오류
**증상**: `Building wheel failed`, `Visual Studio installation not found`

**해결**:
- `requirements.txt`의 버전 사용 (32비트 호환 버전):
  - pandas==2.0.3
  - matplotlib==3.7.5
  - kiwisolver==1.4.7
- pip 옵션 사용: `pip install --only-binary=:all: [package]`

### GUI 실행 오류
**증상**: `ModuleNotFoundError: No module named 'PyQt5.sip'`

**해결**:
```bash
pip uninstall -y PyQt5 PyQt5-sip PyQt5-Qt5
pip install PyQt5==5.15.10
```

### 데이터 수집 중단
- 로그 파일 확인: `logs/collect_daily_prices_YYYYMMDD.log`
- 중단된 시점부터 재개 가능
- 이미 수집된 데이터는 유지됨

### 메모리 부족
- PostgreSQL 사용 권장 (대용량 데이터)
- 배치 크기 조정: `config/kiwoom_config.py`의 `BATCH_SIZE`

## 주의사항

1. **32비트 필수**: 키움 OpenAPI는 32비트 Python에서만 작동합니다
2. **Python 3.11 권장**: 과학 패키지의 32비트 지원이 Python 3.11까지입니다
3. **API 제한**: 키움 API는 초당 5회 제한이 있습니다
4. **거래 시간**: 장중(09:00-15:30)에는 실시간 데이터만 조회 가능
5. **데이터 정확성**: 수정주가 확인 필요
6. **법적 책임**: 실제 투자 시 발생하는 손실은 본인 책임입니다

## 알려진 제약사항

- pandas 2.1.x 이상: 32비트 Windows 미지원 (2.0.3 사용)
- matplotlib 3.8.x 이상: 32비트 Windows 미지원 (3.7.5 사용)
- Python 3.12+: 일부 32비트 패키지 미지원 (3.11 권장)

## 라이센스

MIT License

## 기여

버그 리포트, 기능 제안, Pull Request 환영합니다!

## 연락처

문의사항은 Issues를 통해 남겨주세요.

---

**면책 조항**: 본 프로젝트는 교육 및 연구 목적입니다. 실제 투자에 사용 시 발생하는 손실에 대해 개발자는 책임지지 않습니다.
