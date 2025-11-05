"""
Database connection and session management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging

from config.kiwoom_config import KiwoomConfig
from .models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """데이터베이스 연결 관리자"""

    def __init__(self, db_url=None):
        """
        데이터베이스 매니저 초기화

        Args:
            db_url: 데이터베이스 연결 URL (None이면 config에서 가져옴)
        """
        self.db_url = db_url or KiwoomConfig.get_db_url()

        # SQLite 특별 처리
        if self.db_url.startswith('sqlite'):
            self.engine = create_engine(
                self.db_url,
                connect_args={'check_same_thread': False},
                poolclass=StaticPool,
                echo=False
            )
        else:
            self.engine = create_engine(
                self.db_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=False
            )

        # Session factory
        self.SessionFactory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.SessionFactory)

        logger.info(f"Database initialized: {self.db_url}")

    def create_all_tables(self):
        """모든 테이블 생성"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("All tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def drop_all_tables(self):
        """모든 테이블 삭제 (주의!)"""
        try:
            Base.metadata.drop_all(self.engine)
            logger.warning("All tables dropped")
        except Exception as e:
            logger.error(f"Error dropping tables: {e}")
            raise

    def get_session(self):
        """세션 반환"""
        return self.Session()

    @contextmanager
    def session_scope(self):
        """
        세션 컨텍스트 매니저

        Usage:
            with db_manager.session_scope() as session:
                session.add(obj)
                # 자동으로 commit/rollback
        """
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session rollback due to error: {e}")
            raise
        finally:
            session.close()

    def close(self):
        """데이터베이스 연결 종료"""
        self.Session.remove()
        self.engine.dispose()
        logger.info("Database connection closed")


# 전역 데이터베이스 매니저 인스턴스
_db_manager = None


def init_db(db_url=None):
    """
    데이터베이스 초기화

    Args:
        db_url: 데이터베이스 연결 URL

    Returns:
        DatabaseManager: 데이터베이스 매니저 인스턴스
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_url)
        _db_manager.create_all_tables()
    return _db_manager


def get_db_manager():
    """전역 데이터베이스 매니저 반환"""
    global _db_manager
    if _db_manager is None:
        _db_manager = init_db()
    return _db_manager


def get_session():
    """데이터베이스 세션 반환"""
    return get_db_manager().get_session()


@contextmanager
def session_scope():
    """세션 컨텍스트 매니저"""
    db_manager = get_db_manager()
    with db_manager.session_scope() as session:
        yield session
