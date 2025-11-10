# Phase 4: Rich CLI + Monorepo Refactoring (TDD)

## 📋 개요

### Phase 4 목표
- **Rich CLI**: 사용자 친화적인 CLI 인터페이스 구축
  - 진행 바, 컬러풀한 출력, 테이블 뷰
  - 대화형 메뉴 시스템
  - 상태 모니터링 및 로깅
- **모노레포 리팩토링**: 프로젝트 구조 개선
  - 명확한 패키지 분리 (data, ml, backtest, api, cli)
  - 의존성 관리 개선
  - 설정 파일 중앙화
- **TDD 적용**: 모든 CLI 코드는 테스트 먼저 작성

---

## 🎯 Phase 4 목표 및 완료 기준

### 1. Rich CLI 기능

**필수 기능:**
1. **진행 바 (Progress Bar)**
   - 데이터 수집 진행 상황 표시
   - 백테스팅 진행 상황 표시
   - ETA (예상 완료 시간) 표시

2. **컬러풀한 출력**
   - 성공/실패/경고 메시지 색상 구분
   - 테이블 형식의 데이터 출력
   - Syntax highlighting for 코드/로그

3. **대화형 메뉴**
   - 메인 메뉴 (데이터 수집, 백테스팅, ML 학습, 분석)
   - 서브 메뉴 (옵션 선택, 파라미터 입력)
   - 키보드 네비게이션

4. **상태 모니터링**
   - 실시간 데이터 수집 상태
   - 시스템 리소스 모니터링 (CPU, 메모리)
   - API 호출 제한 상태

**완료 기준:**
- [ ] Rich Progress bar 동작 (10개 테스트)
- [ ] 컬러 출력 테스트 (5개 테스트)
- [ ] 대화형 메뉴 테스트 (15개 테스트)
- [ ] 상태 모니터링 테스트 (10개 테스트)
- [ ] 최소 40개 테스트, 100% 통과

---

### 2. 모노레포 구조

**목표 구조:**
```
kiwoom-auto/
├── packages/
│   ├── data/           # 데이터 수집 및 저장
│   │   ├── collectors/
│   │   ├── db/
│   │   └── tests/
│   ├── ml/             # 머신러닝 엔진
│   │   ├── models/
│   │   ├── features/
│   │   ├── explainer/
│   │   └── tests/
│   ├── backtest/       # 백테스팅 엔진
│   │   ├── strategies/
│   │   ├── evaluation/
│   │   └── tests/
│   ├── api/            # API 클라이언트
│   │   ├── kis/
│   │   ├── dart/
│   │   └── tests/
│   └── cli/            # CLI 인터페이스
│       ├── commands/
│       ├── ui/
│       └── tests/
├── shared/             # 공통 유틸리티
│   ├── config/
│   ├── logging/
│   └── tests/
├── pyproject.toml      # 중앙 설정
└── README.md
```

**완료 기준:**
- [ ] 패키지 구조 리팩토링 완료
- [ ] 각 패키지의 `__init__.py` 및 `pyproject.toml` 설정
- [ ] Import 경로 업데이트
- [ ] 모든 기존 테스트 통과 (311개)

---

### 3. Rich CLI 구현 계획

#### 3.1 핵심 라이브러리
- **Rich**: Terminal formatting, progress bars, tables, syntax highlighting
- **Typer**: CLI 프레임워크 (type hints, auto-completion)
- **Prompt Toolkit**: 대화형 입력 (autocomplete, validation)

#### 3.2 주요 컴포넌트

**A. CLI Commands (cli/commands/)**
- `collect.py`: 데이터 수집 명령어
- `backtest.py`: 백테스팅 명령어
- `ml.py`: ML 학습/예측 명령어
- `analyze.py`: 분석 및 시각화 명령어

**B. UI Components (cli/ui/)**
- `progress.py`: 진행 바 및 스피너
- `table.py`: 테이블 렌더링
- `menu.py`: 대화형 메뉴
- `status.py`: 상태 모니터링 패널

**C. Utilities (cli/utils/)**
- `formatter.py`: 출력 포맷팅 (숫자, 날짜, 퍼센트)
- `logger.py`: Rich 통합 로거
- `config.py`: CLI 설정 관리

---

## 🛠️ 구현 전략

### Phase 4.1: Rich CLI 기본 구조 (Agent 1)

**작업 범위:**
1. Rich + Typer 통합
2. 기본 명령어 구조 (`collect`, `backtest`, `ml`, `analyze`)
3. 진행 바 및 컬러 출력
4. 로깅 시스템

**테스트 계획:**
- Rich 출력 캡처 및 검증
- CLI 명령어 실행 테스트
- 진행 바 업데이트 테스트
- 로그 출력 테스트

**예상 산출물:**
- `cli/main.py`: 메인 CLI 엔트리포인트
- `cli/commands/*.py`: 4개 명령어 모듈
- `cli/ui/progress.py`: 진행 바 컴포넌트
- `cli/ui/console.py`: Rich Console 래퍼
- `tests/cli/`: 15개 테스트

---

### Phase 4.2: 대화형 메뉴 + 상태 모니터링 (Agent 2)

**작업 범위:**
1. 대화형 메뉴 시스템 (Prompt Toolkit)
2. 실시간 상태 모니터링 패널
3. 테이블 렌더링 (데이터 요약)
4. API 제한 상태 표시

**테스트 계획:**
- 메뉴 네비게이션 테스트
- 상태 업데이트 테스트
- 테이블 렌더링 테스트
- Mock input 처리 테스트

**예상 산출물:**
- `cli/ui/menu.py`: 대화형 메뉴
- `cli/ui/status.py`: 상태 모니터링
- `cli/ui/table.py`: 테이블 렌더링
- `tests/cli/`: 15개 테스트

---

### Phase 4.3: 모노레포 리팩토링 (Agent 3)

**작업 범위:**
1. 패키지 구조 재구성
2. Import 경로 업데이트
3. `pyproject.toml` 설정
4. 설정 파일 중앙화

**테스트 계획:**
- 모든 기존 테스트 통과 확인
- Import 경로 검증
- 패키지 설치 테스트
- CLI 명령어 실행 테스트

**예상 산출물:**
- 새로운 `packages/` 디렉토리 구조
- `pyproject.toml` (Poetry or setuptools)
- 업데이트된 `README.md`
- `tests/integration/`: 10개 통합 테스트

---

## 📊 에이전트 역할 분담

### Agent 1: Rich CLI 기본 (commands + progress)
- **목표**: 기본 CLI 구조 + 진행 바
- **테스트**: 15개
- **예상 시간**: 2-3시간

### Agent 2: 대화형 UI (menu + status)
- **목표**: 대화형 메뉴 + 상태 모니터링
- **테스트**: 15개
- **예상 시간**: 2-3시간

### Agent 3: 모노레포 리팩토링
- **목표**: 패키지 구조 재구성
- **테스트**: 기존 311개 + 신규 10개
- **예상 시간**: 3-4시간

---

## 🧪 TDD 적용 전략

### Red-Green-Refactor 사이클

**Red (실패하는 테스트 작성):**
1. 각 CLI 명령어에 대한 테스트 먼저 작성
2. 진행 바, 메뉴, 테이블 출력 검증 테스트
3. Mock을 사용한 사용자 입력 테스트

**Green (최소 구현):**
1. Rich + Typer를 사용한 기본 구현
2. 테스트를 통과하는 최소한의 코드
3. 출력 캡처 및 검증

**Refactor (리팩토링):**
1. 코드 중복 제거
2. UI 컴포넌트 분리
3. 설정 외부화

---

## 📦 주요 의존성

```toml
[tool.poetry.dependencies]
python = "^3.11"
# Existing dependencies...
rich = "^13.7.0"
typer = "^0.9.0"
prompt-toolkit = "^3.0.43"
psutil = "^5.9.6"  # 시스템 모니터링

[tool.poetry.dev-dependencies]
pytest-console-scripts = "^1.4.1"  # CLI 테스트
```

---

## ✅ 완료 기준

### Phase 4 완료 조건:
1. **Rich CLI 기능**:
   - [ ] 4개 메인 명령어 (`collect`, `backtest`, `ml`, `analyze`)
   - [ ] 진행 바 및 스피너
   - [ ] 컬러풀한 출력 (성공/실패/경고)
   - [ ] 대화형 메뉴
   - [ ] 상태 모니터링 패널
   - [ ] 테이블 렌더링

2. **모노레포 구조**:
   - [ ] `packages/` 디렉토리 구조
   - [ ] 각 패키지의 `__init__.py` 및 테스트
   - [ ] `pyproject.toml` 설정
   - [ ] 모든 기존 테스트 통과 (311개)

3. **테스트**:
   - [ ] CLI 테스트: 40개 이상
   - [ ] 통합 테스트: 10개 이상
   - [ ] 전체 테스트: 361개 이상
   - [ ] 커버리지: 80% 이상

4. **문서**:
   - [ ] CLI 사용법 (README.md)
   - [ ] 개발자 가이드 (CONTRIBUTING.md)
   - [ ] API 문서 (docs/)

---

## 🎯 성공 지표

- ✅ Rich CLI 동작 확인 (스크린샷)
- ✅ 모든 테스트 통과 (361개+)
- ✅ CLI 명령어 실행 가능
- ✅ 대화형 메뉴 동작
- ✅ 상태 모니터링 정상 작동
- ✅ 패키지 구조 정리 완료

---

## 📝 다음 단계

**Phase 4 완료 후:**
- Phase 5: 실전 배포 (Docker, CI/CD)
- Phase 6: 웹 대시보드 (FastAPI + React)
- Phase 7: 실시간 트레이딩 (키움 API 통합)

---

## 🚀 시작하기

### 1. 의존성 설치
```bash
pip install rich==13.7.0 typer==0.9.0 prompt-toolkit==3.0.43 psutil==5.9.6
```

### 2. Agent 실행 순서
1. Agent 1: Rich CLI 기본 구조
2. Agent 2: 대화형 UI
3. Agent 3: 모노레포 리팩토링

### 3. 검증
```bash
# CLI 명령어 테스트
python -m cli.main collect --help
python -m cli.main backtest --help

# 테스트 실행
pytest tests/cli/ -v
pytest tests/integration/ -v
```

---

**시작 시간**: 2025-11-10
**예상 완료**: 2025-11-11
**총 작업 시간**: 7-10시간
