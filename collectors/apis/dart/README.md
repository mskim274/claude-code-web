# DART API Client

전자공시시스템 OpenAPI 클라이언트 (TDD 방식으로 개발)

## 개요

이 패키지는 금융감독원의 전자공시시스템(DART) OpenAPI를 Python으로 쉽게 사용할 수 있도록 구현한 클라이언트입니다.

## 주요 기능

### 1. DART API 클라이언트 (`client.py`)
- 기업 기본정보 조회
- 재무제표 조회 (연간/분기)
- 공시 목록 조회
- 재무 지표 자동 계산

### 2. CORPCODE 파서 (`corpcode_parser.py`)
- 종목코드 → 고유번호 변환
- CORPCODE.xml 자동 다운로드 및 파싱

### 3. 재무 지표 계산기 (`financial_metrics.py`)
- PER (주가수익비율)
- PBR (주가순자산비율)
- ROE (자기자본이익률)
- 부채비율
- 영업이익률
- 순이익률

### 4. Pydantic 스키마 (`schemas.py`)
- `DARTFinancialStatement`: 재무제표
- `DARTDisclosure`: 공시 정보
- `DARTCompanyInfo`: 기업 정보
- `DARTFinancialStatementItem`: 재무제표 항목
- `DARTCorpCode`: 고유번호 매핑

### 5. Mock 클라이언트 (`mock_client.py`)
- 테스트용 Mock 구현
- 실제 API 호출 없이 테스트 가능

## 사용 예시

### 기본 사용법

```python
from collectors.apis.dart import DARTAPIClient

# 클라이언트 생성
client = DARTAPIClient(api_key="your_api_key")

# 기업 정보 조회
company = client.get_company_info("005930")  # 삼성전자
print(f"회사명: {company['corp_name']}")

# 재무제표 조회
corp_code = "00126380"
financial_data = client.get_financial_statement(
    corp_code=corp_code,
    year=2023,
    quarter=2
)

# 재무 지표 계산
market_cap = 400_000_000_000_000  # 400조
metrics = client.calculate_financial_metrics(
    financial_data,
    market_cap
)
print(f"PER: {metrics['per']}")
print(f"PBR: {metrics['pbr']}")
print(f"ROE: {metrics['roe']}%")
```

### Context Manager 사용

```python
from collectors.apis.dart import DARTAPIClient

with DARTAPIClient(api_key="your_api_key") as client:
    result = client.get_financial_statement_with_metrics(
        stock_code="005930",
        year=2023,
        quarter=2,
        market_cap=400_000_000_000_000
    )
    print(result)
```

### Mock 클라이언트로 테스트

```python
from collectors.apis.dart import MockDARTAPIClient

# 실제 API 호출 없이 테스트
mock_client = MockDARTAPIClient("test_api_key")
company = mock_client.get_company_info("005930")
assert company["corp_name"] == "삼성전자"
```

## API 엔드포인트

### Base URL
```
https://opendart.fss.or.kr/api
```

### 주요 API
- `/corpCode.xml`: 고유번호 다운로드
- `/company.json`: 기업 개황
- `/fnlttSinglAcntAll.json`: 재무제표
- `/list.json`: 공시 목록

## 재무 지표 계산 공식

```python
# PER (주가수익비율)
PER = 시가총액 / 당기순이익

# PBR (주가순자산비율)
PBR = 시가총액 / 자본총계

# ROE (자기자본이익률)
ROE = (당기순이익 / 자본총계) × 100

# 부채비율
부채비율 = (부채총계 / 자본총계) × 100

# 영업이익률
영업이익률 = (영업이익 / 매출액) × 100

# 순이익률
순이익률 = (당기순이익 / 매출액) × 100
```

## 파일 구조

```
collectors/apis/dart/
├── __init__.py              # 패키지 진입점
├── client.py                # DART API 클라이언트 (318줄)
├── schemas.py               # Pydantic 스키마 (197줄)
├── corpcode_parser.py       # CORPCODE 파서 (163줄)
├── financial_metrics.py     # 재무 지표 계산기 (239줄)
├── mock_client.py           # Mock 클라이언트 (299줄)
└── README.md                # 이 파일
```

## 테스트

### 단위 테스트 (42개)
```bash
# 모든 DART 관련 단위 테스트 실행
pytest tests/unit/test_dart_*.py tests/unit/test_financial_metrics.py -v
```

- `test_dart_client.py`: 18개 테스트
- `test_dart_schemas.py`: 11개 테스트
- `test_financial_metrics.py`: 13개 테스트

### 통합 테스트 (5개)
```bash
# 통합 테스트 실행
pytest tests/integration/test_dart_integration.py -v
```

### 전체 테스트 (47개)
```bash
# 모든 DART 테스트 실행
pytest tests/unit/test_dart_*.py tests/unit/test_financial_metrics.py tests/integration/test_dart_integration.py -v
```

**결과**: 47 passed ✅

## 데이터베이스 모델 (Phase 2)

### 6개 새 테이블

1. **FinancialStatement**: 재무제표 데이터
2. **Disclosure**: 공시 정보
3. **CompanyInfo**: 기업 상세정보
4. **OverseasStock**: 해외주식 기본정보
5. **OverseasPrice**: 해외주식 일봉
6. **APIToken**: API 토큰 관리

```python
from db.models_phase2 import FinancialStatement, Disclosure, CompanyInfo

# 재무제표 저장
fs = FinancialStatement(
    corp_code="00126380",
    corp_name="삼성전자",
    stock_code="005930",
    year=2023,
    quarter=2,
    revenue=302231154000000,
    net_income=35539395000000,
    per=11.25,
    pbr=1.20,
    roe=10.67
)
session.add(fs)
session.commit()
```

## 주의사항

### 1. XML 파싱
DART API는 일부 엔드포인트에서 XML 응답을 사용합니다 (JSON 아님).

### 2. CP949 인코딩
한글 처리 시 인코딩에 주의해야 합니다.

### 3. 종목코드 매핑
DART API는 종목코드가 아닌 고유번호(corp_code)를 사용합니다.
- 종목코드 (6자리): `005930`
- 고유번호 (8자리): `00126380`

반드시 `CorpCodeParser`를 사용하여 변환해야 합니다.

### 4. Rate Limiting
API 호출 제한에 유의하세요.

## 개발 방식

이 패키지는 **TDD (Test-Driven Development)** 방식으로 개발되었습니다.

### Red → Green → Refactor

1. **Red**: 테스트 먼저 작성 (실패)
2. **Green**: 최소한의 코드로 테스트 통과
3. **Refactor**: 코드 개선

### 테스트 커버리지

- 단위 테스트: 42개
- 통합 테스트: 5개
- **총 47개 테스트 통과** ✅

## API Key 발급

1. [DART OpenAPI](https://opendart.fss.or.kr/) 접속
2. 회원가입 및 로그인
3. 인증키 발급 신청
4. 승인 후 API Key 사용

## 라이선스

이 프로젝트는 내부 사용을 위한 것입니다.

## 문의

기술 지원이 필요하면 개발팀에 문의하세요.
