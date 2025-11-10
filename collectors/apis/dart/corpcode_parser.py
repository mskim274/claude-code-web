"""
DART CORPCODE Parser
DART API의 고유번호(corp_code) 파싱 모듈
"""
import requests
import xml.etree.ElementTree as ET
import zipfile
import io
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class CorpCodeParser:
    """
    DART CORPCODE.xml 파싱 클래스
    종목코드(stock_code) → 고유번호(corp_code) 매핑
    """

    CORPCODE_URL = "https://opendart.fss.or.kr/api/corpCode.xml"

    def __init__(self, api_key: str):
        """
        Args:
            api_key: DART API 인증키
        """
        self.api_key = api_key
        self.corp_code_map: Dict[str, str] = {}  # {stock_code: corp_code}
        self.corp_name_map: Dict[str, str] = {}  # {stock_code: corp_name}

    def download_corpcode(self) -> None:
        """
        CORPCODE.xml 다운로드 및 파싱

        DART API에서 ZIP 파일을 다운로드하고,
        압축을 풀어 XML을 파싱하여 매핑 테이블 생성

        Raises:
            Exception: 다운로드 또는 파싱 실패 시
        """
        try:
            logger.info("CORPCODE.xml 다운로드 시작")

            # ZIP 파일 다운로드
            params = {"crtfc_key": self.api_key}
            response = requests.get(
                self.CORPCODE_URL,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            # ZIP 압축 해제
            zip_file = zipfile.ZipFile(io.BytesIO(response.content))
            xml_content = zip_file.read("CORPCODE.xml")

            # XML 파싱
            self._parse_corpcode_xml(xml_content)

            logger.info(f"CORPCODE 파싱 완료: {len(self.corp_code_map)}개 기업")

        except Exception as e:
            logger.error(f"CORPCODE 다운로드 실패: {e}")
            raise

    def _parse_corpcode_xml(self, xml_content: bytes) -> None:
        """
        CORPCODE.xml 파싱하여 매핑 테이블 생성

        Args:
            xml_content: XML 파일 내용 (bytes)
        """
        try:
            # XML 파싱 (CP949 인코딩)
            root = ET.fromstring(xml_content.decode('utf-8'))

            # 각 list 항목 처리
            for item in root.findall('list'):
                corp_code = item.find('corp_code')
                corp_name = item.find('corp_name')
                stock_code = item.find('stock_code')

                if corp_code is not None and stock_code is not None:
                    corp_code_text = corp_code.text
                    stock_code_text = stock_code.text

                    # 상장사만 매핑 (stock_code가 공백이 아닌 경우)
                    if stock_code_text and stock_code_text.strip():
                        self.corp_code_map[stock_code_text.strip()] = corp_code_text

                        if corp_name is not None and corp_name.text:
                            self.corp_name_map[stock_code_text.strip()] = corp_name.text

        except Exception as e:
            logger.error(f"XML 파싱 실패: {e}")
            raise

    def get_corp_code(self, stock_code: str) -> Optional[str]:
        """
        종목코드로 고유번호 조회

        Args:
            stock_code: 종목코드 (6자리)

        Returns:
            고유번호 (8자리), 없으면 None
        """
        return self.corp_code_map.get(stock_code)

    def get_corp_name(self, stock_code: str) -> Optional[str]:
        """
        종목코드로 회사명 조회

        Args:
            stock_code: 종목코드 (6자리)

        Returns:
            회사명, 없으면 None
        """
        return self.corp_name_map.get(stock_code)

    def get_stock_code(self, corp_code: str) -> Optional[str]:
        """
        고유번호로 종목코드 조회 (역매핑)

        Args:
            corp_code: 고유번호 (8자리)

        Returns:
            종목코드 (6자리), 없으면 None
        """
        for stock_code, cc in self.corp_code_map.items():
            if cc == corp_code:
                return stock_code
        return None

    def is_loaded(self) -> bool:
        """
        CORPCODE 데이터가 로드되었는지 확인

        Returns:
            로드 여부
        """
        return len(self.corp_code_map) > 0

    def get_all_stock_codes(self) -> list:
        """
        모든 종목코드 목록 반환

        Returns:
            종목코드 리스트
        """
        return list(self.corp_code_map.keys())

    def get_mapping_count(self) -> int:
        """
        매핑된 종목 개수

        Returns:
            매핑 개수
        """
        return len(self.corp_code_map)
