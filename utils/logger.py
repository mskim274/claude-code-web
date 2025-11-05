"""
로깅 유틸리티
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime

from config.kiwoom_config import KiwoomConfig


def setup_logger(name='kiwoom_collector', level=None):
    """
    로거 설정

    Args:
        name: 로거 이름
        level: 로그 레벨 (None이면 config에서 가져옴)

    Returns:
        logging.Logger: 설정된 로거
    """
    # 디렉토리 생성
    KiwoomConfig.ensure_directories()

    # 로그 레벨 설정
    log_level = level or KiwoomConfig.LOG_LEVEL
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)

    # 이미 핸들러가 있으면 제거 (중복 방지)
    if logger.handlers:
        logger.handlers.clear()

    # 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (일별 로그)
    log_file = KiwoomConfig.LOG_DIR / f'{name}_{datetime.now():%Y%m%d}.log'
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(name='kiwoom_collector'):
    """
    로거 반환 (없으면 생성)

    Args:
        name: 로거 이름

    Returns:
        logging.Logger: 로거
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
