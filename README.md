# 키움증권 API 백테스팅 시스템 (하이브리드 아키텍처)

키움증권 OpenAPI를 활용하여 코스피/코스닥 전종목의 과거 데이터를 수집하고 백테스팅을 수행하는 시스템입니다.

## 핵심 특징

- **하이브리드 아키텍처**: 64비트 메인 프로그램 + 32비트 키움 API 서버 (IPC 통신)
- **일봉/분봉 데이터 수집**: 10년 이상 과거 데이터 조회 가능
- **모의투자 계좌 지원**: 실제 계좌 없이 테스트 가능
- **GUI 백테스팅**: 직관적인 그래픽 인터페이스
- **자동 Rate Limiting**: API 호출 제한 자동 관리 (초당 5회)

## 하이브리드 아키텍처란?

기존의 문제점:
- 키움 OpenAPI는 **32비트 전용**
- 최신 Python 라이브러리(pandas, numpy 등)는 **64비트 권장**
- 32비트 Python 3.11까지만 과학 패키지 지원

**해결책: 하이브리드 아키텍처**

```
┌─────────────────────────────────────┐
│   메인 프로그램 (64비트 Python)     │
│   - GUI (PyQt5)                     │
│   - 백테스팅 (Backtrader)           │
│   - 데이터 처리 (Pandas, Numpy)     │
│   - 데이터베이스 (SQLAlchemy)       │
└──────────────┬──────────────────────┘
               │ IPC 통신 (Socket)
               │ localhost:7777
┌──────────────┴──────────────────────┐
│   키움 API 서버 (32비트 Python)     │
│   - 키움 OpenAPI (QAxWidget)        │
│   - TR 데이터 조회                  │
│   - 일봉/분봉 데이터 수집           │
└─────────────────────────────────────┘
```

**장점:**
- 64비트 환경에서 최신 라이브러리 사용 가능
- 32비트 서버는 자동으로 시작/종료
- 사용자는 복잡성을 신경 쓸 필요 없음

## 시스템 요구사항

### 필수 소프트웨어

1. **Python 3.12 64비트** (메인 프로그램용)
   - Windows 64비트 OS
   - pandas, numpy, PyQt5 등 최신 라이브러리 사용

2. **Python 3.12 32비트** (키움 API 서버용)
   - 키움 OpenAPI와 통신
   - 설치 경로: `C:\Python312-32\`

3. **키움증권 OpenAPI+**
   - 키움증권 홈페이지에서 다운로드
   - 설치 후 버전처리 실행 필수
   - 모의투자 또는 실계좌 필요

### 계좌 요구사항

- **모의투자 계좌**: 무료로 사용 가능 (초기 자금 1억원)
- **실계좌**: 실제 거래 가능 (데이터 조회는 모의투자와 동일)

**중요**: 일봉/분봉 데이터 조회는 모의투자 계좌에서도 동일하게 동작합니다.

## 설치 방법

### 1단계: 저장소 클론

```bash
git clone <repository-url>
cd claude-code-web
```

### 2단계: Python 설치

#### Python 3.12 64비트 설치
- [Python 공식 사이트](https://www.python.org/downloads/)에서 다운로드
- "Add Python to PATH" 체크
- 설치 경로 예: `C:\Users\[USERNAME]\AppData\Local\Programs\Python\Python312\`

#### Python 3.12 32비트 설치
- [Python 공식 사이트](https://www.python.org/downloads/)에서 "Windows installer (32-bit)" 다운로드
- **중요**: "Customize installation" → 설치 경로를 `C:\Python312-32\`로 지정
- "Add Python to PATH" 체크 **해제** (충돌 방지)

#### 설치 확인

```bash
# 64비트 Python 확인
C:\Users\[USERNAME]\AppData\Local\Programs\Python\Python312\python.exe --version
C:\Users\[USERNAME]\AppData\Local\Programs\Python\Python312\python.exe -c "import platform; print(platform.architecture()[0])"

# 32비트 Python 확인
C:\Python312-32\python.exe --version
C:\Python312-32\python.exe -c "import platform; print(platform.architecture()[0])"
```

### 3단계: 64비트 환경 설정 (메인 프로그램)

```bash
# 64비트 Python으로 가상환경 생성
C:\Users\[USERNAME]\AppData\Local\Programs\Python\Python312\python.exe -m venv venv

# 가상환경 활성화
venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 4단계: 32비트 환경 설정 (키움 API 서버)

```bash
# 32비트 Python에 PyQt5 설치 (전역)
C:\Python312-32\python.exe -m pip install PyQt5==5.15.10
```

**중요**: 32비트는 가상환경 없이 전역 설치합니다. 키움 API 서버가 자동으로 찾을 수 있도록 하기 위함입니다.

### 5단계: 키움 OpenAPI+ 설치

1. [키움증권 OpenAPI+ 다운로드](https://www.kiwoom.com/h/customer/download/VOpenApiInfoView)
2. 설치 후 **버전처리** 실행 (필수!)
3. 키움증권 HTS에서 모의투자 로그인 테스트

### 6단계: 데이터베이스 초기화

```bash
python scripts/init_db.py
```

## 실행 방법

### GUI 모드 (권장)

#### 방법 1: 배치 파일 실행 (가장 간단)

```bash
run_gui.bat
```

더블클릭으로 실행하면 자동으로:
1. 64비트 Python으로 GUI 시작
2. 32비트 서버 자동 시작 (백그라운드)
3. IPC 통신 자동 연결

#### 방법 2: 직접 실행

```bash
# 가상환경 활성화
venv\Scripts\activate

# GUI 실행
python gui_main.py
```

### 하이브리드 아키텍처 테스트

```bash
# 가상환경 활성화
venv\Scripts\activate

# 하이브리드 테스트
python test_hybrid.py
```

테스트 내용:
- 32비트 서버 자동 시작
- 로그인 테스트
- 종목 리스트 조회
- 일봉 데이터 조회
- 분봉 데이터 조회

## 주요 기능

### 1. 데이터 수집

#### 종목 리스트 수집
- 코스피, 코스닥 전체 종목 (약 2,500개)
- 종목코드, 종목명, 시장구분 자동 저장

#### 일봉 데이터 수집
```python
from collectors.kiwoom_api import KiwoomAPI

api = KiwoomAPI()
api.login()

# 10년치 데이터 조회
daily_data = api.get_daily_price(
    code='005930',           # 삼성전자
    start_date='20140101',   # 2014년 1월 1일
    end_date='20241231'      # 2024년 12월 31일
)
```

**특징:**
- 연속 조회 자동 처리 (600일씩 분할)
- 최대 10년치 데이터 (약 2,500일)
- Rate Limiting 자동 적용 (초당 5회)

#### 분봉 데이터 수집
```python
# 5분봉 900개 조회 (약 3일치)
minute_data = api.get_minute_price(
    code='005930',   # 삼성전자
    tick=5,         # 5분봉
    count=900       # 900개
)
```

**지원 분봉:**
- 1분봉, 3분봉, 5분봉, 10분봉
- 15분봉, 30분봉, 45분봉, 60분봉

### 2. GUI 주요 화면

#### Dashboard (대시보드)
- 전체 종목 수 통계
- 데이터 수집 현황
- 빠른 액션 버튼

#### Data Collector (데이터 수집)
1. **종목 리스트 수집**: 코스피+코스닥 전체 종목
2. **일봉 데이터 수집**: 모든 종목의 과거 데이터
3. **개별 종목 수집**: 특정 종목만 수집
4. **최신 데이터 업데이트**: 오늘 데이터만 업데이트

**진행률 표시:**
- 실시간 진행률 (%)
- 현재 처리 중인 종목
- 수집 로그 출력

#### Backtest (백테스팅)
- 종목 선택
- 기간 설정
- 전략 선택 (이동평균 교차 등)
- 파라미터 조정
- 결과 차트 및 통계

#### Chart Viewer (차트 뷰어)
- 캔들스틱 차트
- 거래량 차트
- 이동평균선

### 3. 모의투자 vs 실제 계좌

| 기능 | 모의투자 | 실제 계좌 |
|------|---------|----------|
| 로그인 | ✅ 동일 | ✅ 동일 |
| 일봉 데이터 조회 | ✅ 동일 | ✅ 동일 |
| 분봉 데이터 조회 | ✅ 동일 | ✅ 동일 |
| 종목 리스트 조회 | ✅ 동일 | ✅ 동일 |
| 주문 체결 | 가상 체결 | 실제 체결 |
| 잔고 조회 | 가상 잔고 | 실제 잔고 |
| 초기 자금 | 1억원 | 실제 자금 |

**결론**: 백테스팅 시스템은 모의투자 계좌로 충분합니다.

## 프로젝트 구조

```
claude-code-web/
├── collectors/               # 데이터 수집
│   ├── kiwoom_api.py        # 키움 API 래퍼 (64비트)
│   ├── kiwoom_api_client.py # IPC 클라이언트 (64비트)
│   ├── kiwoom_api_server.py # 키움 API 서버 (32비트)
│   ├── kiwoom_api_old.py    # 기존 32비트 구현 (백업)
│   └── stock_collector.py   # 데이터 수집기
├── db/                      # 데이터베이스
│   ├── models.py            # SQLAlchemy 모델
│   └── database.py          # DB 연결 관리
├── backtest/                # 백테스팅
│   ├── engine.py            # 백테스트 엔진
│   └── strategy.py          # 전략 베이스 클래스
├── gui/                     # GUI 애플리케이션
│   ├── main_window.py       # 메인 윈도우
│   └── widgets/             # GUI 위젯
├── config/                  # 설정 파일
│   └── kiwoom_config.py     # 키움 API 설정
├── scripts/                 # 실행 스크립트
│   ├── init_db.py           # DB 초기화
│   └── collect_stock_list.py
├── claudedocs/              # 문서
│   └── kiwoom_mock_account_conditions.md
├── test_hybrid.py           # 하이브리드 아키텍처 테스트
├── gui_main.py              # GUI 실행 파일
├── run_gui.bat              # GUI 실행 배치 파일
├── requirements.txt         # Python 패키지 (64비트)
└── README.md                # 본 문서
```

## 문제 해결

### 32비트 서버 시작 실패

**증상**: "32비트 Python을 찾을 수 없습니다"

**해결**:
```bash
# 32비트 Python 경로 확인
dir C:\Python312-32\python.exe

# 없으면 32비트 Python 재설치
# 설치 경로를 정확히 C:\Python312-32\ 로 지정
```

### 서버 연결 실패

**증상**: "Connection refused", "키움 API 서버에 연결할 수 없습니다"

**해결**:
1. 32비트 서버 프로세스 확인
   - 작업 관리자에서 `python.exe (32비트)` 프로세스 확인
2. 포트 충돌 확인
   ```bash
   netstat -ano | findstr 7777
   ```
3. 방화벽 설정 확인

### 키움 API 로그인 실패

**증상**: `OnEventConnect` 에러, 로그인 창이 뜨지 않음

**해결**:
1. 키움증권 HTS에서 먼저 로그인
2. OpenAPI+ 버전처리 실행
3. 32비트 Python에 PyQt5 설치 확인
   ```bash
   C:\Python312-32\python.exe -m pip list | findstr PyQt5
   ```
4. Windows 재부팅

### GUI 실행 오류

**증상**: `ModuleNotFoundError: No module named 'collectors'`

**해결**:
```bash
# 가상환경 활성화 확인
venv\Scripts\activate

# 프로젝트 루트 디렉토리에서 실행
cd c:\Users\AND\OneDrive\바탕 화면\trading\claude-code-web
python gui_main.py
```

### 종목 리스트 수집이 느림

**이유**: Rate Limiting (초당 5회) + 2,500개 종목 × 종목명 조회

**개선**:
- 최근 업데이트에서 불필요한 API 호출 제거
- 종목명만 조회 (상장일은 나중에)
- 실제 소요 시간: 약 8-10분

### 데이터베이스 오류

**증상**: `OperationalError`, `IntegrityError`

**해결**:
```bash
# 데이터베이스 초기화
python scripts/init_db.py

# SQLite 파일 삭제 후 재생성
del data\trading.db
python scripts/init_db.py
```

## 성능 최적화

### 데이터 수집
- 배치 커밋: 100개 종목마다 커밋
- Rate Limiter: 초당 5회 자동 제어
- 연속 조회: 600일씩 자동 분할

### IPC 통신
- 버퍼 크기: 1MB (대용량 데이터 전송)
- Keep-alive: 연결 유지
- 자동 재연결: 서버 재시작 지원

### 백테스팅
- 벡터화 연산: pandas 활용
- 인덱싱: 날짜별 최적화
- 메모리 효율: 필요한 기간만 로드

## 데이터베이스 스키마

### stocks (종목 정보)
```sql
CREATE TABLE stocks (
    code VARCHAR(10) PRIMARY KEY,  -- 종목코드
    name VARCHAR(100),              -- 종목명
    market VARCHAR(10),             -- KOSPI/KOSDAQ
    listing_date DATE                -- 상장일
);
```

### daily_prices (일봉 데이터)
```sql
CREATE TABLE daily_prices (
    stock_code VARCHAR(10),         -- 종목코드 (FK)
    date DATE,                      -- 날짜
    open INTEGER,                   -- 시가
    high INTEGER,                   -- 고가
    low INTEGER,                    -- 저가
    close INTEGER,                  -- 종가
    volume BIGINT,                  -- 거래량
    trading_value BIGINT,           -- 거래대금
    adj_close FLOAT,                -- 수정주가
    PRIMARY KEY (stock_code, date)
);
```

### minute_prices (분봉 데이터)
```sql
CREATE TABLE minute_prices (
    stock_code VARCHAR(10),         -- 종목코드 (FK)
    datetime TIMESTAMP,             -- 체결시간
    open INTEGER,                   -- 시가
    high INTEGER,                   -- 고가
    low INTEGER,                    -- 저가
    close INTEGER,                  -- 종가
    volume BIGINT,                  -- 거래량
    PRIMARY KEY (stock_code, datetime)
);
```

## API 명세

### KiwoomAPI 주요 메서드

```python
class KiwoomAPI:
    def login(self) -> bool:
        """키움 로그인"""

    def logout(self):
        """로그아웃"""

    def get_code_list_by_market(self, market_code: str) -> list:
        """시장별 종목 코드 리스트 조회

        Args:
            market_code: '0' (코스피), '10' (코스닥)
        """

    def get_master_code_name(self, code: str) -> str:
        """종목명 조회"""

    def get_login_info(self, tag: str) -> str:
        """로그인 정보 조회

        Args:
            tag: "USER_ID", "USER_NAME", "ACCOUNT_CNT", "ACCNO"
        """

    def get_daily_price(
        self,
        code: str,
        start_date: str = None,
        end_date: str = None
    ) -> list:
        """일봉 데이터 조회

        Args:
            code: 종목코드
            start_date: 시작일자 (YYYYMMDD)
            end_date: 종료일자 (YYYYMMDD)

        Returns:
            [{'일자', '현재가', '시가', '고가', '저가', '거래량'}, ...]
        """

    def get_minute_price(
        self,
        code: str,
        tick: int = 1,
        count: int = 900
    ) -> list:
        """분봉 데이터 조회

        Args:
            code: 종목코드
            tick: 분봉 단위 (1, 3, 5, 10, 15, 30, 45, 60)
            count: 조회 개수

        Returns:
            [{'체결시간', '현재가', '시가', '고가', '저가', '거래량'}, ...]
        """
```

## 향후 계획

- [ ] 실시간 시세 조회
- [ ] 자동 매매 기능
- [ ] 다양한 백테스팅 전략 추가
- [ ] 웹 대시보드
- [ ] 알림 기능 (텔레그램, 이메일)

## 주의사항

1. **하이브리드 아키텍처**: 64비트 Python + 32비트 Python 모두 필요
2. **API 제한**: 키움 API는 초당 5회 제한
3. **거래 시간**: 장중(09:00-15:30)에는 일부 기능 제한
4. **데이터 정확성**: 수정주가 확인 필요
5. **법적 책임**: 실제 투자 손실은 본인 책임

## 문서

- [모의투자 계좌 조건](claudedocs/kiwoom_mock_account_conditions.md)
- [하이브리드 아키텍처 설명](test_hybrid.py)

## 라이센스

MIT License

## 기여

버그 리포트, 기능 제안, Pull Request 환영합니다!

## 면책 조항

본 프로젝트는 교육 및 연구 목적입니다. 실제 투자에 사용 시 발생하는 손실에 대해 개발자는 책임지지 않습니다.

---

**최종 업데이트**: 2025-01-06
**버전**: 2.0 (하이브리드 아키텍처)
