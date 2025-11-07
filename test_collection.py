"""
GUI 없이 데이터 수집 테스트
"""

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from collectors.stock_collector import StockCollector

def test_connection():
    """키움 API 연결 테스트"""
    print("=" * 50)
    print("키움 API 연결 테스트")
    print("=" * 50)

    collector = StockCollector()

    print("\n1. 로그인 시도...")
    if collector.login():
        print("✓ 로그인 성공")

        # 로그인 정보 확인
        user_id = collector.api.get_login_info("USER_ID")
        user_name = collector.api.get_login_info("USER_NAME")
        print(f"✓ 사용자: {user_name} ({user_id})")

        # 코스피 종목 수 확인
        print("\n2. 종목 리스트 확인...")
        kospi_list = collector.api.get_code_list_by_market('0')
        print(f"✓ 코스피 종목 수: {len(kospi_list)}개")

        # 샘플 종목 확인
        if kospi_list:
            sample_code = kospi_list[0]
            sample_name = collector.api.get_master_code_name(sample_code)
            print(f"✓ 샘플 종목: {sample_code} ({sample_name})")

        print("\n3. 로그아웃...")
        collector.logout()
        print("✓ 로그아웃 완료")

        print("\n테스트 성공!")
        return True
    else:
        print("✗ 로그인 실패")
        print("\n가능한 원인:")
        print("1. 키움증권 Open API+ 모듈이 설치되지 않음")
        print("2. 키움증권에 로그인되지 않음")
        print("3. 32비트 서버가 실행되지 않음")
        return False

if __name__ == '__main__':
    test_connection()
