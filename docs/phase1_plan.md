# Phase 1: Pydantic 스키마 도입 및 TA-Lib 통합 상세 계획

**프로젝트**: 키움 백테스팅 시스템
**문서 버전**: 1.0
**작성일**: 2025-11-10
**예상 기간**: 8-10 작업일 (65시간)

---

## 목차

1. [개요](#1-개요)
2. [현재 상태 분석](#2-현재-상태-분석)
3. [작업 분해 및 우선순위](#3-작업-분해-및-우선순위)
4. [병렬 처리 전략](#4-병렬-처리-전략)
5. [전문 에이전트 역할 분담](#5-전문-에이전트-역할-분담)
6. [테스트 전략](#6-테스트-전략)
7. [예상 산출물](#7-예상-산출물)
8. [완료 기준](#8-완료-기준)
9. [리스크 및 대응](#9-리스크-및-대응)
10. [마이그레이션 전략](#10-마이그레이션-전략)

---

## 1. 개요

### 1.1 Phase 1 목표

- **Pydantic v2 도입**: SQLAlchemy 모델에 대응하는 Pydantic 스키마 생성
- **TA-Lib 통합**: 150개 이상의 기술적 지표를 백테스팅 시스템에 통합
- **TDD 적용**: 모든 코드는 테스트 먼저 작성
- **무중단 마이그레이션**: 기존 기능 손상 없이 점진적 도입

### 1.2 성공 지표

- Pydantic 스키마 7개 모델 완성
- TA-Lib 지표 최소 50개 통합
- 테스트 커버리지 80% 이상
- 기존 GUI 및 데이터 수집 기능 정상 동작

---

## 2. 현재 상태 분석

### 2.1 데이터베이스 모델

**기존 SQLAlchemy 모델 7개:**

1. Stock - 종목 기본 정보
2. DailyPrice - 일별 주가 데이터
3. MinutePrice - 분봉 데이터
4. TickPrice - 틱 데이터
5. InvestorTrading - 투자자별 매매 동향
6. StockInfo - 종목 상세 정보
7. CollectionLog - 데이터 수집 로그

**문제점:**

- 타입 검증 부재
- API 응답 검증 없음
- 데이터 변환 로직 분산

### 2.2 의존성

**추가 필요:**



---

## 3. 작업 분해 및 우선순위

### 3.1 작업 그룹

**A: 환경 설정 (P0) - 2시간**

- A1: requirements.txt 업데이트 (30분)
- A2: TA-Lib 설치 가이드 (1시간)
- A3: 프로젝트 구조 재구성 (30분)

**B: Pydantic 스키마 (P0) - 10시간**

- B1: 기본 스키마 생성 (1시간)
- B2: 종목 관련 스키마 (2시간)
- B3: 가격 데이터 스키마 (3시간)
- B4: 투자자/메타 스키마 (2시간)
- B5: 검증 로직 구현 (2시간)

**C: TA-Lib 통합 (P1) - 21시간**

- C1: 기본 구조 (2시간)
- C2: Overlap Studies (4시간)
- C3: Momentum Indicators (5시간)
- C4: Volume Indicators (2시간)
- C5: Volatility Indicators (2시간)
- C6: Pattern Recognition (3시간)
- C7: 지표 관리 시스템 (3시간)

**D: 백테스팅 통합 (P1) - 10시간**

- D1: 전략 베이스 리팩토링 (3시간)
- D2: 샘플 전략 구현 (4시간)
- D3: 엔진 업데이트 (3시간)

**E: 테스트 (P0/P1) - 17시간**

- E1: 스키마 테스트 (5시간)
- E2: 지표 테스트 (6시간)
- E3: 통합 테스트 (4시간)
- E4: 성능 테스트 (2시간)

**F: 문서화 (P2) - 5시간**

- F1: API 문서 (3시간)
- F2: 마이그레이션 가이드 (2시간)

**총 예상 시간**: 65시간 (8-10 작업일)

---

## 4. 병렬 처리 전략

### Day 1: 환경 설정
- A1, A2, A3 (순차 처리)

### Day 2-3: 코어 개발 (병렬)
- Track 1 (Agent 1): B1-B5 (Pydantic)
- Track 2 (Agent 2): C1-C2 (TA-Lib 기본)
- Track 3 (Agent 3): E1 (테스트)

### Day 4-5: 지표 확장 (병렬)
- Track 1 (Agent 2): C3, C4, C5
- Track 2 (Agent 3): E2

### Day 6-7: 통합 (병렬)
- Track 1 (Agent 1): D1, D2
- Track 2 (Agent 2): C6, C7
- Track 3 (Agent 3): E3

### Day 8: 마무리
- All: E4, F1, F2

---

## 5. 전문 에이전트 역할 분담

### Agent 1: Pydantic Specialist
- Pydantic 스키마 설계
- 검증 로직 작성
- Task: B, E1, D1

### Agent 2: TA-Lib Specialist
- TA-Lib 래퍼 구현
- 150개 지표 통합
- Task: C, E2, D2

### Agent 3: Testing Specialist
- 통합 테스트
- 성능 테스트
- 문서화
- Task: E3, E4, F

---

## 6. 테스트 전략

### 6.1 TDD 사이클
Red (테스트 작성) → Green (최소 구현) → Refactor (리팩토링)

### 6.2 테스트 커버리지 목표

| 컴포넌트 | 목표 |
|---------|------|
| schemas/ | 100% |
| indicators/ | 90% |
| backtest/ | 80% |

---

## 7. 예상 산출물

```
claude-code-web/
├── schemas/          # NEW
│   ├── base.py
│   ├── stock.py
│   └── price.py
├── indicators/       # NEW
│   ├── base.py
│   ├── momentum.py
│   └── overlap.py
├── backtest/
│   └── strategy_v2.py # NEW
├── tests/            # NEW
│   ├── test_schemas/
│   ├── test_indicators/
│   └── test_integration/
└── docs/
    ├── phase1_plan.md
    └── migration_guide.md
```

---

## 8. 완료 기준

### 기능 완료
- [ ] 7개 Pydantic 스키마 완성
- [ ] 50개 TA-Lib 지표 통합
- [ ] 3개 샘플 전략 구현

### 테스트 완료
- [ ] 커버리지 80% 이상
- [ ] 통합 테스트 10개 이상
- [ ] 모든 테스트 Green

### 호환성
- [ ] 기존 데이터 수집 정상 동작
- [ ] 기존 GUI 정상 동작
- [ ] DB 스키마 변경 없음

---

## 9. 리스크 및 대응

### Risk 1: TA-Lib 설치 실패 (High)
**대응:**
- 사전 설치 가이드 작성
- 대체 방안 (pandas-ta)
- Docker 환경 제공

### Risk 2: Pydantic v2 호환성 (Medium)
**대응:**
- 의존성 철저히 확인
- 점진적 도입
- 마이그레이션 도구 사용

### Risk 3: 성능 저하 (Medium)
**대응:**
- 지표 캐싱 시스템
- Lazy Loading
- NumPy 벡터화

### Risk 4: 기존 기능 손상 (High)
**대응:**
- 점진적 마이그레이션
- 철저한 테스트
- 롤백 계획

---

## 10. 마이그레이션 전략

### 10.1 원칙
1. 하위 호환성 유지
2. 점진적 도입
3. 롤백 가능 (Feature Flag)

### 10.2 단계

**Stage 1: 새 시스템 구축**
- schemas/, indicators/ 생성
- 기존 코드 미수정

**Stage 2: 테스트**
- 독립적 테스트
- 병행 운영

**Stage 3: Adapter**
```python
def orm_to_schema(orm_obj):
    return StockSchema.model_validate(orm_obj)
```

**Stage 4: 점진적 전환**
- collectors/ 모듈 적용
- backtest/ 모듈 적용

### 10.3 Feature Flag
```python
FEATURE_FLAGS = {
    'USE_PYDANTIC_SCHEMAS': True,
    'USE_TALIB_INDICATORS': True,
}
```

### 10.4 DB 마이그레이션
**원칙: DB 스키마 수정 없음**
- SQLAlchemy 모델 유지
- Pydantic은 검증/직렬화만

---

## 부록: 설치 가이드

### TA-Lib 설치 (Windows 64비트)
```bash
pip install TA_Lib-0.4.28-cp312-cp312-win_amd64.whl
```

### Pydantic 설치
```bash
pip install pydantic==2.10.3
```

### 참고 자료
- Pydantic: https://docs.pydantic.dev/latest/
- TA-Lib: https://ta-lib.github.io/ta-lib-python/
- pytest: https://docs.pytest.org/

---

**문서 작성**: Claude Code
**최종 수정**: 2025-11-10
