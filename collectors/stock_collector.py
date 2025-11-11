"""
주식 데이터 수집기
"""

import logging
import time
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from collectors.kiwoom_api_client import KiwoomAPIClient
from db.database import session_scope
from db.models import Stock, DailyPrice, MinutePrice, TickPrice, StockInfo, CollectionLog
from config.kiwoom_config import KiwoomConfig

logger = logging.getLogger(__name__)


class StockCollector:
    """주식 데이터 수집기"""

    def __init__(self, use_kiwoom_api=True):
        """수집기 초기화"""
        self.use_kiwoom_api = use_kiwoom_api
        self.api = None
        self.is_logged_in = False

        if use_kiwoom_api:
            try:
                self.api = KiwoomAPIClient()
                logger.info("StockCollector initialized with Kiwoom API")
            except FileNotFoundError as e:
                logger.warning(f"Kiwoom API not available: {e}")
                logger.info("StockCollector initialized WITHOUT Kiwoom API")
        else:
            logger.info("StockCollector initialized WITHOUT Kiwoom API")

    def login(self):
        """키움 API 로그인"""
        if not self.is_logged_in:
            success = self.api.login()
            if success:
                self.is_logged_in = True
                user_id = self.api.get_login_info("USER_ID")
                user_name = self.api.get_login_info("USER_NAME")
                logger.info(f"Logged in as {user_name} ({user_id})")
            return success
        return True

    def logout(self):
        """로그아웃"""
        if self.is_logged_in:
            self.api.logout()
            self.is_logged_in = False

    def collect_all_stock_list(self):
        """
        전체 종목 리스트 수집 (코스피, 코스닥)

        Returns:
            int: 수집된 종목 수
        """
        if not self.is_logged_in:
            logger.error("Not logged in")
            return 0

        total_count = 0

        for market_code in KiwoomConfig.TARGET_MARKETS:
            market_name = KiwoomConfig.MARKETS[market_code]
            logger.info(f"Collecting stock list from {market_name}...")

            code_list = self.api.get_code_list_by_market(market_code)

            with session_scope() as session:
                for code in code_list:
                    try:
                        # 종목명 조회
                        name = self.api.get_master_code_name(code)
                        if not name:
                            continue

                        # 상장일 조회 (일단 None으로 처리 - 나중에 별도로 수집)
                        listing_date = None

                        # DB에 저장
                        stock = session.query(Stock).filter_by(code=code).first()
                        if stock:
                            # 업데이트
                            stock.name = name
                            stock.market = market_name
                            if listing_date:
                                stock.listing_date = listing_date
                        else:
                            # 신규 생성
                            stock = Stock(
                                code=code,
                                name=name,
                                market=market_name,
                                listing_date=listing_date
                            )
                            session.add(stock)

                        total_count += 1

                        if total_count % 100 == 0:
                            session.commit()
                            logger.info(f"Saved {total_count} stocks...")

                    except Exception as e:
                        logger.error(f"Error processing stock {code}: {e}")
                        continue

            logger.info(f"Completed {market_name}: {len(code_list)} stocks")

        logger.info(f"Total stocks collected: {total_count}")
        return total_count

    def collect_daily_price(self, stock_code, years=5):
        """
        특정 종목의 일봉 데이터 수집

        Args:
            stock_code: 종목 코드
            years: 수집할 과거 연수

        Returns:
            int: 수집된 레코드 수
        """
        if not self.is_logged_in:
            logger.error("Not logged in")
            return 0

        try:
            # 최근 상장 종목은 짧은 기간만 요청 (타임아웃 방지)
            # ETF, ETN 등은 대부분 최근 상장
            if stock_code.endswith(('0', 'C0', 'D0', 'H0', 'J0', 'P0', 'S0', 'Y0', 'Z0')):
                # ETF로 추정되는 종목은 3년치만 요청
                actual_years = min(years, 3)
                logger.info(f"ETF detected ({stock_code}), limiting to {actual_years} years")
            else:
                actual_years = years

            # 시작일/종료일 계산
            end_date = datetime.now()
            start_date = end_date - timedelta(days=actual_years * 365)

            logger.info(f"Collecting daily price for {stock_code} from {start_date.date()} to {end_date.date()}")

            # 수집 로그 생성
            with session_scope() as session:
                log = CollectionLog(
                    stock_code=stock_code,
                    collection_type='daily',
                    start_date=start_date.date(),
                    end_date=end_date.date(),
                    status='in_progress'
                )
                session.add(log)
                session.flush()
                log_id = log.id

            # API로 데이터 조회
            data_list = self.api.get_daily_price(
                stock_code,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d')
            )

            if not data_list:
                logger.warning(f"No data for {stock_code}")
                with session_scope() as session:
                    log = session.query(CollectionLog).get(log_id)
                    log.status = 'failed'
                    log.error_message = 'No data returned'
                    log.completed_at = datetime.now()
                return 0

            # DB에 저장
            saved_count = 0
            with session_scope() as session:
                for data in data_list:
                    try:
                        # 날짜 파싱
                        date_str = data['일자'].strip()
                        date = datetime.strptime(date_str, '%Y%m%d').date()

                        # 이미 존재하는지 확인
                        existing = session.query(DailyPrice).filter_by(
                            stock_code=stock_code,
                            date=date
                        ).first()

                        if existing:
                            continue

                        # 가격 데이터 파싱 (부호 제거)
                        close = abs(int(data['현재가'].strip()))
                        open_price = abs(int(data['시가'].strip()))
                        high = abs(int(data['고가'].strip()))
                        low = abs(int(data['저가'].strip()))
                        volume = int(data['거래량'].strip())

                        # 거래대금 (optional)
                        trading_value = None
                        if data.get('거래대금'):
                            trading_value = int(data['거래대금'].strip())

                        # DailyPrice 객체 생성
                        daily_price = DailyPrice(
                            stock_code=stock_code,
                            date=date,
                            open=open_price,
                            high=high,
                            low=low,
                            close=close,
                            volume=volume,
                            trading_value=trading_value,
                            adj_close=float(close)  # 기본값
                        )
                        session.add(daily_price)
                        saved_count += 1

                    except Exception as e:
                        logger.error(f"Error parsing data for {stock_code} on {data.get('일자')}: {e}")
                        continue

                # 수집 로그 업데이트
                log = session.query(CollectionLog).get(log_id)
                log.status = 'success'
                log.records_collected = saved_count
                log.completed_at = datetime.now()

            logger.info(f"Saved {saved_count} daily price records for {stock_code}")
            return saved_count

        except Exception as e:
            logger.error(f"Error collecting daily price for {stock_code}: {e}")
            with session_scope() as session:
                if 'log_id' in locals():
                    log = session.query(CollectionLog).get(log_id)
                    log.status = 'failed'
                    log.error_message = str(e)
                    log.completed_at = datetime.now()
            return 0

    def collect_all_daily_prices(self, years=5):
        """
        전체 종목의 일봉 데이터 수집

        Args:
            years: 수집할 과거 연수

        Returns:
            dict: 수집 통계
        """
        if not self.is_logged_in:
            logger.error("Not logged in")
            return {'success': 0, 'skipped': 0, 'failed': 0, 'total': 0}

        # 종목 리스트 조회
        with session_scope() as session:
            stocks = session.query(Stock).all()
            stock_codes = [(s.code, s.name) for s in stocks]

        total = len(stock_codes)
        success_count = 0
        skipped_count = 0
        failed_count = 0

        logger.info(f"Starting collection for {total} stocks ({years} years)")

        for idx, (code, name) in enumerate(stock_codes, 1):
            retry_count = 0
            max_retries = 2  # 재시도 횟수 증가

            while retry_count <= max_retries:
                try:
                    if retry_count == 0:
                        logger.info(f"[{idx}/{total}] Processing {name} ({code})")
                    else:
                        logger.info(f"[{idx}/{total}] Retrying {name} ({code}) - attempt {retry_count + 1}")

                    records = self.collect_daily_price(code, years)

                    if records > 0:
                        success_count += 1
                    elif records == 0:
                        skipped_count += 1  # 이미 데이터가 있음
                    else:
                        failed_count += 1

                    # 진행률 로그
                    if idx % 10 == 0:
                        progress = (idx / total) * 100
                        logger.info(f"Progress: {progress:.1f}% ({idx}/{total}), Success: {success_count}, Skipped: {skipped_count}, Failed: {failed_count}")

                    break  # 성공하면 루프 탈출

                except (ConnectionError, TimeoutError) as e:
                    error_type = type(e).__name__
                    logger.warning(f"{error_type} processing {code}: {e}")

                    if retry_count < max_retries:
                        logger.info(f"Waiting 3 seconds before retry...")
                        time.sleep(3)  # 재시도 전 대기
                        logger.info(f"Retrying {code}...")
                        retry_count += 1
                    else:
                        logger.error(f"Failed after {max_retries + 1} attempts for {code}")
                        failed_count += 1
                        break

                except Exception as e:
                    logger.error(f"Error processing {code}: {e}")
                    failed_count += 1
                    break

        logger.info(f"Collection completed: Success={success_count}, Skipped={skipped_count}, Failed={failed_count}, Total={total}")
        return {
            'success': success_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'total': total,
            'total_records': success_count + skipped_count
        }

    def collect_stock_info(self, stock_code):
        """
        종목 상세 정보 수집

        Args:
            stock_code: 종목 코드

        Returns:
            bool: 성공 여부
        """
        if not self.is_logged_in:
            logger.error("Not logged in")
            return False

        try:
            # API로 정보 조회
            data = self.api.get_stock_info(stock_code)

            if not data:
                logger.warning(f"No info for {stock_code}")
                return False

            # DB에 저장
            with session_scope() as session:
                info = session.query(StockInfo).filter_by(stock_code=stock_code).first()

                # 데이터 파싱 (안전하게)
                def safe_int(value):
                    try:
                        return abs(int(value.strip())) if value else None
                    except:
                        return None

                def safe_float(value):
                    try:
                        return float(value.strip()) if value else None
                    except:
                        return None

                if info:
                    # 업데이트
                    info.market_cap = safe_int(data.get('시가총액'))
                    info.shares_outstanding = safe_int(data.get('상장주식수'))
                    info.per = safe_float(data.get('PER'))
                    info.pbr = safe_float(data.get('PBR'))
                    info.eps = safe_int(data.get('EPS'))
                    info.bps = safe_int(data.get('BPS'))
                else:
                    # 신규 생성
                    info = StockInfo(
                        stock_code=stock_code,
                        market_cap=safe_int(data.get('시가총액')),
                        shares_outstanding=safe_int(data.get('상장주식수')),
                        per=safe_float(data.get('PER')),
                        pbr=safe_float(data.get('PBR')),
                        eps=safe_int(data.get('EPS')),
                        bps=safe_int(data.get('BPS'))
                    )
                    session.add(info)

            logger.info(f"Saved stock info for {stock_code}")
            return True

        except Exception as e:
            logger.error(f"Error collecting stock info for {stock_code}: {e}")
            return False

    def update_latest_prices(self):
        """
        최신 일봉 데이터 업데이트 (일일 업데이트용)

        Returns:
            int: 업데이트된 종목 수
        """
        if not self.is_logged_in:
            logger.error("Not logged in")
            return 0

        # 오늘 날짜
        today = datetime.now().date()

        # 이미 오늘 데이터가 있는 종목 제외
        with session_scope() as session:
            stocks = session.query(Stock).all()
            stock_codes = [s.code for s in stocks]

        updated = 0
        for code in stock_codes:
            try:
                # 오늘 데이터가 있는지 확인
                with session_scope() as session:
                    exists = session.query(DailyPrice).filter_by(
                        stock_code=code,
                        date=today
                    ).first()

                    if exists:
                        continue

                # 최근 1일치만 수집
                records = self.collect_daily_price(code, years=0.01)
                if records > 0:
                    updated += 1

                if updated % 100 == 0:
                    logger.info(f"Updated {updated} stocks...")

            except Exception as e:
                logger.error(f"Error updating {code}: {e}")
                continue

        logger.info(f"Updated {updated} stocks with latest prices")
        return updated

    def collect_minute_price(self, stock_code, interval=1, count=900):
        """
        특정 종목의 분봉 데이터 수집

        Args:
            stock_code: 종목 코드
            interval: 분봉 간격 (1, 5, 10, 30, 60)
            count: 수집 개수 (기본 900개)

        Returns:
            int: 수집된 레코드 수
        """
        if not self.is_logged_in:
            logger.error("Not logged in")
            return 0

        try:
            logger.info(f"Collecting {interval}min price for {stock_code} (count: {count})")

            # 수집 로그 생성
            with session_scope() as session:
                log = CollectionLog(
                    stock_code=stock_code,
                    collection_type=f'minute_{interval}',
                    status='in_progress'
                )
                session.add(log)
                session.flush()
                log_id = log.id

            # API로 데이터 조회
            data_list = self.api.get_minute_price(stock_code, tick=interval, count=count)

            if not data_list:
                logger.warning(f"No minute data for {stock_code}")
                with session_scope() as session:
                    log = session.query(CollectionLog).get(log_id)
                    log.status = 'failed'
                    log.error_message = 'No data returned'
                    log.completed_at = datetime.now()
                return 0

            # DB에 저장
            saved_count = 0
            with session_scope() as session:
                for data in data_list:
                    try:
                        # 시간 파싱 (YYYYMMDDHHmmss)
                        time_str = data['체결시간'].strip()
                        dt = datetime.strptime(time_str, '%Y%m%d%H%M%S')

                        # 이미 존재하는지 확인
                        existing = session.query(MinutePrice).filter_by(
                            stock_code=stock_code,
                            datetime=dt,
                            interval=interval
                        ).first()

                        if existing:
                            continue

                        # 가격 데이터 파싱 (부호 제거)
                        close = abs(int(data['현재가'].strip()))
                        open_price = abs(int(data['시가'].strip()))
                        high = abs(int(data['고가'].strip()))
                        low = abs(int(data['저가'].strip()))
                        volume = int(data['거래량'].strip())

                        # MinutePrice 객체 생성
                        minute_price = MinutePrice(
                            stock_code=stock_code,
                            datetime=dt,
                            interval=interval,
                            open=open_price,
                            high=high,
                            low=low,
                            close=close,
                            volume=volume
                        )
                        session.add(minute_price)
                        saved_count += 1

                    except Exception as e:
                        logger.error(f"Error parsing minute data for {stock_code} at {data.get('체결시간')}: {e}")
                        continue

                # 수집 로그 업데이트
                log = session.query(CollectionLog).get(log_id)
                log.status = 'success'
                log.records_collected = saved_count
                log.completed_at = datetime.now()

            logger.info(f"Saved {saved_count} {interval}min price records for {stock_code}")
            return saved_count

        except Exception as e:
            logger.error(f"Error collecting minute price for {stock_code}: {e}")
            with session_scope() as session:
                if 'log_id' in locals():
                    log = session.query(CollectionLog).get(log_id)
                    log.status = 'failed'
                    log.error_message = str(e)
                    log.completed_at = datetime.now()
            return 0

    def collect_all_minute_prices(self, intervals=[1, 5, 10, 30, 60], count=900, stock_codes=None):
        """
        전체 종목의 분봉 데이터 수집

        Args:
            intervals: 수집할 분봉 간격 리스트 [1, 5, 10, 30, 60]
            count: 각 분봉당 수집 개수
            stock_codes: 수집할 종목 코드 리스트 (None이면 전체)

        Returns:
            dict: 수집 통계
        """
        if not self.is_logged_in:
            logger.error("Not logged in")
            return {'success': 0, 'skipped': 0, 'failed': 0, 'total': 0}

        # 종목 리스트 조회
        if stock_codes:
            with session_scope() as session:
                stocks = session.query(Stock).filter(Stock.code.in_(stock_codes)).all()
                stock_list = [(s.code, s.name) for s in stocks]
        else:
            with session_scope() as session:
                stocks = session.query(Stock).all()
                stock_list = [(s.code, s.name) for s in stocks]

        total = len(stock_list) * len(intervals)
        success_count = 0
        skipped_count = 0
        failed_count = 0

        logger.info(f"Starting minute price collection for {len(stock_list)} stocks, {len(intervals)} intervals")

        for idx, (code, name) in enumerate(stock_list, 1):
            for interval in intervals:
                retry_count = 0
                max_retries = 2

                while retry_count <= max_retries:
                    try:
                        if retry_count == 0:
                            logger.info(f"[{idx}/{len(stock_list)}] Processing {name} ({code}) - {interval}min")
                        else:
                            logger.info(f"[{idx}/{len(stock_list)}] Retrying {name} ({code}) - {interval}min - attempt {retry_count + 1}")

                        records = self.collect_minute_price(code, interval, count)

                        if records > 0:
                            success_count += 1
                        elif records == 0:
                            skipped_count += 1
                        else:
                            failed_count += 1

                        # 진행률 로그
                        current = (idx - 1) * len(intervals) + intervals.index(interval) + 1
                        if current % 10 == 0:
                            progress = (current / total) * 100
                            logger.info(f"Progress: {progress:.1f}% ({current}/{total}), Success: {success_count}, Skipped: {skipped_count}, Failed: {failed_count}")

                        break  # 성공하면 루프 탈출

                    except (ConnectionError, TimeoutError) as e:
                        error_type = type(e).__name__
                        logger.warning(f"{error_type} processing {code} {interval}min: {e}")

                        if retry_count < max_retries:
                            logger.info(f"Waiting 3 seconds before retry...")
                            time.sleep(3)
                            retry_count += 1
                        else:
                            logger.error(f"Failed after {max_retries + 1} attempts for {code} {interval}min")
                            failed_count += 1
                            break

                    except Exception as e:
                        logger.error(f"Error processing {code} {interval}min: {e}")
                        failed_count += 1
                        break

        logger.info(f"Minute price collection completed: Success={success_count}, Skipped={skipped_count}, Failed={failed_count}, Total={total}")
        return {
            'success': success_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'total': total
        }

    def collect_tick_data(self, stock_code, count=600):
        """
        특정 종목의 틱 데이터 수집

        Args:
            stock_code: 종목 코드
            count: 수집 개수 (최대 600)

        Returns:
            int: 수집된 레코드 수
        """
        if not self.is_logged_in:
            logger.error("Not logged in")
            return 0

        try:
            logger.info(f"Collecting tick data for {stock_code} (count: {count})")

            # 수집 로그 생성
            with session_scope() as session:
                log = CollectionLog(
                    stock_code=stock_code,
                    collection_type='tick',
                    status='in_progress'
                )
                session.add(log)
                session.flush()
                log_id = log.id

            # API로 데이터 조회
            data_list = self.api.get_tick_data(stock_code, count=count)

            if not data_list:
                logger.warning(f"No tick data for {stock_code}")
                with session_scope() as session:
                    log = session.query(CollectionLog).get(log_id)
                    log.status = 'failed'
                    log.error_message = 'No data returned'
                    log.completed_at = datetime.now()
                return 0

            # DB에 저장
            saved_count = 0
            with session_scope() as session:
                for data in data_list:
                    try:
                        # 시간 파싱 (HHMMss 형식)
                        time_str = data['체결시간'].strip()

                        # 오늘 날짜 + 시간으로 datetime 생성
                        today = datetime.now().date()
                        if len(time_str) == 6:  # HHMMSS
                            hour = int(time_str[0:2])
                            minute = int(time_str[2:4])
                            second = int(time_str[4:6])
                            dt = datetime.combine(today, datetime.min.time().replace(hour=hour, minute=minute, second=second))
                        else:
                            logger.warning(f"Invalid time format: {time_str}")
                            continue

                        # 이미 존재하는지 확인
                        existing = session.query(TickPrice).filter_by(
                            stock_code=stock_code,
                            datetime=dt
                        ).first()

                        if existing:
                            continue

                        # 가격 데이터 파싱 (부호 제거)
                        price = abs(int(data['현재가'].strip()))
                        volume = int(data['거래량'].strip())

                        # 선택적 필드
                        change = None
                        if data.get('전일대비'):
                            change = abs(int(data['전일대비'].strip()))

                        # TickPrice 객체 생성
                        tick_price = TickPrice(
                            stock_code=stock_code,
                            datetime=dt,
                            price=price,
                            volume=volume,
                            change=change
                        )
                        session.add(tick_price)
                        saved_count += 1

                    except Exception as e:
                        logger.error(f"Error parsing tick data for {stock_code} at {data.get('체결시간')}: {e}")
                        continue

                # 수집 로그 업데이트
                log = session.query(CollectionLog).get(log_id)
                log.status = 'success'
                log.records_collected = saved_count
                log.completed_at = datetime.now()

            logger.info(f"Saved {saved_count} tick records for {stock_code}")
            return saved_count

        except Exception as e:
            logger.error(f"Error collecting tick data for {stock_code}: {e}")
            with session_scope() as session:
                if 'log_id' in locals():
                    log = session.query(CollectionLog).get(log_id)
                    log.status = 'failed'
                    log.error_message = str(e)
                    log.completed_at = datetime.now()
            return 0

    def collect_all_tick_data(self, count=600, stock_codes=None):
        """
        전체 종목의 틱 데이터 수집

        Args:
            count: 각 종목당 틱 개수 (최대 600)
            stock_codes: 수집할 종목 코드 리스트 (None이면 전체)

        Returns:
            dict: 수집 통계
        """
        if not self.is_logged_in:
            logger.error("Not logged in")
            return {'success': 0, 'skipped': 0, 'failed': 0, 'total': 0}

        # 종목 리스트 조회
        if stock_codes:
            with session_scope() as session:
                stocks = session.query(Stock).filter(Stock.code.in_(stock_codes)).all()
                stock_list = [(s.code, s.name) for s in stocks]
        else:
            with session_scope() as session:
                stocks = session.query(Stock).all()
                stock_list = [(s.code, s.name) for s in stocks]

        total = len(stock_list)
        success_count = 0
        skipped_count = 0
        failed_count = 0

        logger.info(f"Starting tick data collection for {total} stocks")

        for idx, (code, name) in enumerate(stock_list, 1):
            retry_count = 0
            max_retries = 2

            while retry_count <= max_retries:
                try:
                    if retry_count == 0:
                        logger.info(f"[{idx}/{total}] Processing {name} ({code}) - tick data")
                    else:
                        logger.info(f"[{idx}/{total}] Retrying {name} ({code}) - attempt {retry_count + 1}")

                    records = self.collect_tick_data(code, count)

                    if records > 0:
                        success_count += 1
                    elif records == 0:
                        skipped_count += 1
                    else:
                        failed_count += 1

                    # 진행률 로그
                    if idx % 10 == 0:
                        progress = (idx / total) * 100
                        logger.info(f"Progress: {progress:.1f}% ({idx}/{total}), Success: {success_count}, Skipped: {skipped_count}, Failed: {failed_count}")

                    break  # 성공하면 루프 탈출

                except (ConnectionError, TimeoutError) as e:
                    error_type = type(e).__name__
                    logger.warning(f"{error_type} processing {code}: {e}")

                    if retry_count < max_retries:
                        logger.info(f"Waiting 3 seconds before retry...")
                        time.sleep(3)
                        retry_count += 1
                    else:
                        logger.error(f"Failed after {max_retries + 1} attempts for {code}")
                        failed_count += 1
                        break

                except Exception as e:
                    logger.error(f"Error processing {code}: {e}")
                    failed_count += 1
                    break

        logger.info(f"Tick data collection completed: Success={success_count}, Skipped={skipped_count}, Failed={failed_count}, Total={total}")
        return {
            'success': success_count,
            'skipped': skipped_count,
            'failed': failed_count,
            'total': total
        }
