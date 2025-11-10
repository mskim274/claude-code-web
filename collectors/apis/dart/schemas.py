"""
DART API Pydantic Schemas
Data validation and serialization for DART OpenAPI
"""
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional


class DARTFinancialStatement(BaseModel):
    """
    재무제표 스키마
    Financial Statement Schema for DART API
    """
    corp_code: str = Field(..., description="고유번호 (8자리)")
    corp_name: str = Field(..., description="회사명")
    year: int = Field(..., description="사업연도 (4자리)", ge=1900, le=2100)
    quarter: int = Field(..., description="분기 (1~4)", ge=1, le=4)

    # 손익계산서 (Income Statement)
    revenue: Optional[int] = Field(None, description="매출액")
    operating_profit: Optional[int] = Field(None, description="영업이익")
    net_income: Optional[int] = Field(None, description="당기순이익")

    # 재무상태표 (Balance Sheet)
    total_assets: Optional[int] = Field(None, description="자산총계")
    total_liabilities: Optional[int] = Field(None, description="부채총계")
    total_equity: Optional[int] = Field(None, description="자본총계")

    # 계산된 재무 지표
    per: Optional[float] = Field(None, description="PER (주가수익비율)")
    pbr: Optional[float] = Field(None, description="PBR (주가순자산비율)")
    roe: Optional[float] = Field(None, description="ROE (자기자본이익률, %)")
    debt_ratio: Optional[float] = Field(None, description="부채비율 (%)")
    operating_margin: Optional[float] = Field(None, description="영업이익률 (%)")
    net_margin: Optional[float] = Field(None, description="순이익률 (%)")

    class Config:
        json_schema_extra = {
            "example": {
                "corp_code": "00126380",
                "corp_name": "삼성전자",
                "year": 2023,
                "quarter": 2,
                "revenue": 302231154000000,
                "operating_profit": 42510611000000,
                "net_income": 35539395000000,
                "total_assets": 448063162000000,
                "total_liabilities": 114963472000000,
                "total_equity": 333099690000000,
                "per": 11.25,
                "pbr": 1.20,
                "roe": 10.67,
                "debt_ratio": 34.52
            }
        }


class DARTDisclosure(BaseModel):
    """
    공시 정보 스키마
    Disclosure Information Schema for DART API
    """
    rcept_no: str = Field(..., description="접수번호 (14자리)")
    corp_code: str = Field(..., description="고유번호 (8자리)")
    corp_name: str = Field(..., description="회사명")
    report_nm: str = Field(..., description="보고서명")
    rcept_dt: date = Field(..., description="접수일자")
    flr_nm: str = Field(..., description="공시제출인명")

    @field_validator('rcept_dt', mode='before')
    @classmethod
    def parse_date(cls, v):
        """날짜 문자열을 date 객체로 변환 (YYYYMMDD 형식 지원)"""
        if isinstance(v, str):
            if len(v) == 8 and v.isdigit():  # YYYYMMDD format
                return date(int(v[:4]), int(v[4:6]), int(v[6:8]))
            # ISO format (YYYY-MM-DD)
            from datetime import datetime
            return datetime.fromisoformat(v).date()
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "rcept_no": "20231114000504",
                "corp_code": "00126380",
                "corp_name": "삼성전자",
                "report_nm": "주요사항보고서(자기주식취득신탁계약체결결정)",
                "rcept_dt": "20231114",
                "flr_nm": "삼성전자"
            }
        }


class DARTCompanyInfo(BaseModel):
    """
    기업 개황 스키마
    Company Information Schema for DART API
    """
    corp_code: str = Field(..., description="고유번호 (8자리)")
    corp_name: str = Field(..., description="정식회사명칭")
    stock_code: str = Field(..., description="종목코드 (6자리)")

    # Optional fields
    corp_name_eng: Optional[str] = Field(None, description="영문명칭")
    ceo_nm: Optional[str] = Field(None, description="대표자명")
    est_dt: Optional[str] = Field(None, description="설립일 (YYYYMMDD)")
    jurir_no: Optional[str] = Field(None, description="법인등록번호")
    bizr_no: Optional[str] = Field(None, description="사업자등록번호")
    addr: Optional[str] = Field(None, description="주소")
    hm_url: Optional[str] = Field(None, description="홈페이지")
    ir_url: Optional[str] = Field(None, description="IR 홈페이지")
    phn_no: Optional[str] = Field(None, description="전화번호")
    fax_no: Optional[str] = Field(None, description="팩스번호")

    @field_validator('stock_code')
    @classmethod
    def validate_stock_code(cls, v):
        """종목코드는 6자리 숫자"""
        if v and len(v) != 6:
            raise ValueError("종목코드는 6자리여야 합니다")
        if v and not v.isdigit():
            raise ValueError("종목코드는 숫자만 포함해야 합니다")
        return v

    @field_validator('corp_code')
    @classmethod
    def validate_corp_code(cls, v):
        """고유번호는 8자리 숫자"""
        if v and len(v) != 8:
            raise ValueError("고유번호는 8자리여야 합니다")
        if v and not v.isdigit():
            raise ValueError("고유번호는 숫자만 포함해야 합니다")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "corp_code": "00126380",
                "corp_name": "삼성전자",
                "corp_name_eng": "SAMSUNG ELECTRONICS CO., LTD.",
                "stock_code": "005930",
                "ceo_nm": "한종희, 경계현",
                "est_dt": "19690113",
                "jurir_no": "1301110006246",
                "bizr_no": "1248100998"
            }
        }


class DARTFinancialStatementItem(BaseModel):
    """
    재무제표 항목 스키마 (API 응답용)
    Individual line item from financial statement API response
    """
    rcept_no: str = Field(..., description="접수번호")
    corp_code: str = Field(..., description="고유번호")
    sj_div: str = Field(..., description="재무제표구분 (BS: 재무상태표, IS: 손익계산서, CIS: 포괄손익계산서, CF: 현금흐름표)")
    account_nm: str = Field(..., description="계정명")
    thstrm_amount: Optional[str] = Field(None, description="당기금액")
    frmtrm_amount: Optional[str] = Field(None, description="전기금액")
    bfefrmtrm_amount: Optional[str] = Field(None, description="전전기금액")

    class Config:
        json_schema_extra = {
            "example": {
                "rcept_no": "20230814000159",
                "corp_code": "00126380",
                "sj_div": "BS",
                "account_nm": "자산총계",
                "thstrm_amount": "448063162000000",
                "frmtrm_amount": "426793908000000",
                "bfefrmtrm_amount": "378464720000000"
            }
        }


class DARTCorpCode(BaseModel):
    """
    CORPCODE.xml 항목 스키마
    Corporate code mapping schema
    """
    corp_code: str = Field(..., description="고유번호 (8자리)")
    corp_name: str = Field(..., description="회사명")
    stock_code: Optional[str] = Field(None, description="종목코드 (6자리, 상장사만)")
    modify_date: str = Field(..., description="최종변경일자 (YYYYMMDD)")

    class Config:
        json_schema_extra = {
            "example": {
                "corp_code": "00126380",
                "corp_name": "삼성전자",
                "stock_code": "005930",
                "modify_date": "20231114"
            }
        }
