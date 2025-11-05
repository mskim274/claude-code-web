"""
API 호출 속도 제한 관리
"""

import time
from collections import deque
from threading import Lock
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    API 호출 속도 제한기

    키움증권 API는 초당 5회 제한이 있음
    """

    def __init__(self, max_calls=5, time_window=1.0, min_interval=0.2):
        """
        Rate Limiter 초기화

        Args:
            max_calls: 시간 윈도우당 최대 호출 횟수
            time_window: 시간 윈도우 (초)
            min_interval: 최소 호출 간격 (초)
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.min_interval = min_interval

        self.call_times = deque()
        self.lock = Lock()
        self.last_call_time = 0

    def wait_if_needed(self):
        """
        필요시 대기

        호출 제한을 초과하지 않도록 대기
        """
        with self.lock:
            current_time = time.time()

            # 최소 간격 체크
            time_since_last_call = current_time - self.last_call_time
            if time_since_last_call < self.min_interval:
                sleep_time = self.min_interval - time_since_last_call
                logger.debug(f"Minimum interval wait: {sleep_time:.3f}s")
                time.sleep(sleep_time)
                current_time = time.time()

            # 시간 윈도우 밖의 오래된 호출 기록 제거
            while self.call_times and current_time - self.call_times[0] > self.time_window:
                self.call_times.popleft()

            # 호출 횟수 체크
            if len(self.call_times) >= self.max_calls:
                # 가장 오래된 호출로부터 time_window 경과 대기
                sleep_time = self.time_window - (current_time - self.call_times[0])
                if sleep_time > 0:
                    logger.debug(f"Rate limit wait: {sleep_time:.3f}s")
                    time.sleep(sleep_time)
                    current_time = time.time()
                    # 다시 오래된 기록 제거
                    while self.call_times and current_time - self.call_times[0] > self.time_window:
                        self.call_times.popleft()

            # 현재 호출 기록
            self.call_times.append(current_time)
            self.last_call_time = current_time

    def reset(self):
        """호출 기록 초기화"""
        with self.lock:
            self.call_times.clear()
            self.last_call_time = 0
            logger.debug("Rate limiter reset")

    def get_stats(self):
        """
        현재 상태 통계 반환

        Returns:
            dict: 통계 정보
        """
        with self.lock:
            current_time = time.time()
            # 현재 윈도우 내의 호출 수
            active_calls = sum(1 for t in self.call_times if current_time - t <= self.time_window)
            return {
                'active_calls': active_calls,
                'max_calls': self.max_calls,
                'time_window': self.time_window,
                'min_interval': self.min_interval,
                'time_since_last_call': current_time - self.last_call_time if self.last_call_time else None
            }
