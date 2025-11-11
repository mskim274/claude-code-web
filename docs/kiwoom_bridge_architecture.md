# Kiwoom Bridge Architecture Design

## 개요

64-bit GUI와 32-bit Kiwoom API 간의 효율적인 통신을 위한 영구 Bridge 프로세스 아키텍처.

## 문제점 분석

### 현재 아키텍처의 한계
1. **프로세스 반복 생성**: 각 API 호출마다 32-bit Python 프로세스 생성
2. **콘솔 창 깜빡임**: subprocess 호출 시 CMD 창 표시 (Quick Fix로 해결됨)
3. **비효율적 리소스 사용**: 로그인 세션 반복 생성/파괴
4. **제한된 성능 최적화**: 순차 처리만 가능, 우선순위 큐 불가능

### Quick Fix 적용 (완료)
```python
# collectors/kiwoom_api_client.py
subprocess.Popen(
    [python32_path, str(script_path)],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NO_WINDOW,
    shell=False
)
```
✅ **효과**: CMD 창 숨김, 즉각적인 사용자 경험 개선

## Bridge 아키텍처 설계

### 전체 구조

```
┌─────────────────────────────────────┐
│   64-bit GUI (PyQt5)                │
│   - Main Application                │
│   - UI Components                   │
│   - Data Visualization              │
└───────────────┬─────────────────────┘
                │ IPC (Named Pipe/TCP)
                │ JSON-RPC Protocol
┌───────────────▼─────────────────────┐
│   32-bit Kiwoom Bridge (pythonw.exe)│
│   - Request Queue                   │
│   - Rate Limiter (1 req/sec)        │
│   - Kiwoom COM Object (QAxWidget)   │
│   - Qt Event Loop                   │
│   - Session Management              │
└─────────────────────────────────────┘
```

### 핵심 컴포넌트

#### 1. Kiwoom Bridge Process (32-bit)
**파일**: `collectors/kiwoom_bridge.py`

**책임**:
- 단일 영구 프로세스로 실행
- Kiwoom COM 객체 호스팅 (STA 스레드)
- Qt 메시지 루프 유지
- 로그인 세션 관리
- 요청 큐 처리
- Rate Limiting (1 req/sec)

**구조**:
```python
class KiwoomBridge:
    def __init__(self):
        self.app = QCoreApplication([])
        self.kiwoom = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.request_queue = Queue()
        self.rate_limiter = RateLimiter(rate=1.0)  # 1 req/sec
        self.ipc_server = IPCServer()

    def run(self):
        # Qt 이벤트 루프 시작
        # IPC 서버 리스닝
        # 요청 큐 처리
        pass
```

#### 2. IPC Communication Layer
**프로토콜**: JSON-RPC 2.0 over Named Pipe (Windows) or TCP localhost

**Named Pipe 선택 이유**:
- Windows 네이티브 지원
- TCP보다 빠름 (로컬 통신)
- 포트 충돌 없음
- 보안 우수 (프로세스 격리)

**메시지 포맷**:
```json
// Request
{
  "jsonrpc": "2.0",
  "method": "fetch_daily_price",
  "params": {
    "stock_code": "005930",
    "start_date": "20240101",
    "end_date": "20241231"
  },
  "id": "req-001"
}

// Response
{
  "jsonrpc": "2.0",
  "result": {
    "data": [...],
    "count": 250
  },
  "id": "req-001"
}

// Error
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": "Login failed"
  },
  "id": "req-001"
}
```

#### 3. Request Queue & Priority System
**우선순위 레벨**:
1. **URGENT**: 실시간 데이터 (체결, 호가)
2. **HIGH**: 사용자가 선택한 종목
3. **NORMAL**: 일반 업데이트
4. **LOW**: 배치 전체 수집

**구현**:
```python
from queue import PriorityQueue
import enum

class Priority(enum.IntEnum):
    URGENT = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

class RequestQueue:
    def __init__(self):
        self.queue = PriorityQueue()

    def enqueue(self, priority, request):
        self.queue.put((priority, timestamp(), request))

    def dequeue(self):
        return self.queue.get()
```

#### 4. Rate Limiter
**알고리즘**: Token Bucket

```python
import time
from collections import deque

class RateLimiter:
    def __init__(self, rate=1.0):
        self.rate = rate  # requests per second
        self.tokens = 1.0
        self.last_update = time.monotonic()

    def acquire(self):
        now = time.monotonic()
        elapsed = now - self.last_update

        # Refill tokens
        self.tokens = min(1.0, self.tokens + elapsed * self.rate)
        self.last_update = now

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        else:
            # Wait time
            wait_time = (1.0 - self.tokens) / self.rate
            time.sleep(wait_time)
            self.tokens = 0.0
            return True
```

#### 5. Session Management
**로그인 상태 관리**:
- 자동 로그인 (계정 정보 안전 저장)
- 세션 타임아웃 감지 및 재로그인
- 건강 체크 (주기적 ping)
- 점검 시간 대응

```python
class SessionManager:
    def __init__(self, kiwoom):
        self.kiwoom = kiwoom
        self.logged_in = False
        self.last_activity = time.monotonic()

    def ensure_logged_in(self):
        if not self.logged_in:
            self.login()

    def health_check(self):
        # 주기적 상태 확인
        pass

    def handle_disconnect(self):
        # 재연결 로직
        pass
```

### 클라이언트 (64-bit GUI)

#### 6. Bridge Client
**파일**: `collectors/bridge_client.py`

```python
import json
from multiprocessing.connection import Client

class KiwoomBridgeClient:
    def __init__(self, address=r'\\.\pipe\kiwoom_bridge'):
        self.address = address
        self.conn = None

    def connect(self):
        self.conn = Client(self.address)

    def call(self, method, params, priority='NORMAL'):
        request = {
            'jsonrpc': '2.0',
            'method': method,
            'params': params,
            'priority': priority,
            'id': self._generate_id()
        }

        self.conn.send(json.dumps(request))
        response = json.loads(self.conn.recv())

        if 'error' in response:
            raise Exception(response['error'])

        return response['result']

    def fetch_daily_price(self, stock_code, years=5, priority='NORMAL'):
        return self.call('fetch_daily_price', {
            'stock_code': stock_code,
            'years': years
        }, priority=priority)
```

## 성능 최적화 전략

### 1. Smart Skipping (이미 부분 구현됨)
```python
# DB에서 마지막 데이터 날짜 확인
last_date = db.get_last_date(stock_code)

if last_date == today:
    skip_stock()
else:
    fetch_from(last_date + 1 day)
```

### 2. Batch Processing
```python
# 100개 종목씩 그룹화
for batch in chunks(stock_codes, 100):
    for code in batch:
        bridge.enqueue('fetch_daily_price', code, priority='NORMAL')

    # DB에 배치 삽입
    db.bulk_insert(results)
```

### 3. Checkpoint & Resume
```python
class CheckpointManager:
    def __init__(self):
        self.checkpoint_file = 'data_collection_checkpoint.json'

    def save(self, processed_codes, failed_codes):
        with open(self.checkpoint_file, 'w') as f:
            json.dump({
                'processed': processed_codes,
                'failed': failed_codes,
                'timestamp': datetime.now().isoformat()
            }, f)

    def load(self):
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file) as f:
                return json.load(f)
        return None

    def resume(self, all_codes):
        checkpoint = self.load()
        if checkpoint:
            remaining = set(all_codes) - set(checkpoint['processed'])
            return list(remaining), checkpoint['failed']
        return all_codes, []
```

## 구현 로드맵

### Phase 1: Quick Fix ✅ (완료)
- subprocess CREATE_NO_WINDOW 적용
- DEVNULL 리다이렉트
- **소요 시간**: 10분
- **효과**: CMD 창 즉시 숨김

### Phase 2: Bridge Core (2-3일)
1. **Day 1**:
   - Kiwoom Bridge 프로세스 구조
   - Named Pipe IPC 구현
   - JSON-RPC 프로토콜

2. **Day 2**:
   - Request Queue & Priority
   - Rate Limiter
   - Session Management

3. **Day 3**:
   - Bridge Client 구현
   - 기존 코드 통합
   - 테스트

### Phase 3: 성능 최적화 (1-2일)
- Smart Skipping 강화
- Checkpoint & Resume
- Batch Processing

### Phase 4: UI 개선 (1일)
- 우선순위 선택 UI
- 진행률 표시 개선
- 일시정지/재개 버튼

## 예상 성능 개선

### 현재 (Quick Fix 후)
- 4,200개 종목 × 1초 = **70분**
- ✅ CMD 창 숨김

### Bridge 구현 후
- Smart Skipping: 70분 → **10-20분** (첫 실행 후)
- Priority Mode (상위 100개): **2분**
- Checkpoint Resume: 중단 후 **즉시 재개**

## 보안 고려사항

1. **Named Pipe 보안**:
   - 프로세스별 ACL 설정
   - 같은 사용자만 접근 가능

2. **계정 정보 저장**:
   - Windows DPAPI 사용
   - 암호화된 credential 저장

3. **에러 정보 노출 방지**:
   - 로그에만 상세 정보
   - 사용자에게는 간결한 메시지

## 테스트 계획

### Unit Tests
- Rate Limiter 정확성
- Request Queue 우선순위
- Session Manager 재연결

### Integration Tests
- Bridge ↔ Client IPC
- Kiwoom API 호출
- DB 연동

### E2E Tests
- 전체 데이터 수집 플로우
- 중단 후 재개
- 오류 복구

## 마이그레이션 전략

### 하위 호환성 유지
```python
# 기존 StockCollector 인터페이스 유지
class StockCollector:
    def __init__(self, use_bridge=True):
        if use_bridge:
            self.client = KiwoomBridgeClient()
        else:
            self.client = KiwoomAPIClient()  # 기존 방식
```

### 점진적 전환
1. Bridge 구현 완료
2. 테스트 환경에서 검증
3. 기본값을 Bridge로 변경
4. 안정화 후 legacy 코드 제거

## 결론

**Quick Fix (완료)**:
- ✅ 즉각적인 사용자 경험 개선
- ✅ 10분 작업으로 CMD 창 문제 해결

**Bridge 아키텍처 (향후)**:
- 장기적으로 최고의 솔루션
- 성능, 안정성, 확장성 모두 향상
- 2-3일 투자로 70분 → 2-20분 단축
- 우선순위 기반 수집, 재개 기능 등 추가

**권장 순서**:
1. ✅ Quick Fix 사용 (완료)
2. 사용자 피드백 수집
3. 필요시 Bridge 구현
4. 점진적 마이그레이션
