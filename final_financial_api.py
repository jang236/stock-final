from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import json
import os
import re
from typing import Dict, Optional, List
import uvicorn


app = FastAPI(title="Stock Financial Data API", version="2.0")


class FinancialData(BaseModel):
    """재무 데이터 응답 모델"""
    code: str
    company_name: str
    data: Dict
    collected_at: str
    data_periods: List[str]


class StockFinancialAPI:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        })
        self.companies = self.load_companies()
        self.cf1001_urls = self.load_cf1001_urls()

    def load_companies(self):
        """종목 정보 로드"""
        try:
            file_path = os.path.join("company_codes", "stock_companies.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"종목 로드 실패: {e}")
            return {}

    def load_cf1001_urls(self):
        """수집된 cF1001 URL 로드"""
        try:
            file_path = os.path.join("company_codes", "cf1001_urls_success.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"cF1001 URL 로드 실패: {e}")
            return {}

    def get_company_name(self, stock_code: str) -> str:
        """종목코드로 회사명 찾기"""
        for name, info in self.companies.items():
            if info['code'] == stock_code:
                return name
        return f"종목_{stock_code}"

    def extract_encparam_and_id(self, stock_code: str):
        """실시간으로 encparam과 id 추출"""
        try:
            main_url = f"https://navercomp.wisereport.co.kr/company/c1010001.aspx?cmp_cd={stock_code}"
            response = self.session.get(main_url, timeout=10)
            
            # encparam 추출
            encparam_patterns = [
                r"encparam['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
                r"encParam['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]"
            ]
            
            encparam = None
            for pattern in encparam_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                if matches:
                    encparam = matches[0]
                    break
            
            # id 추출 (특정 패턴의 ID)
            id_patterns = [
                r'id[\'"]?\s*[:=]\s*[\'"]([A-Za-z0-9+/=]{8,})[\'"]'
            ]
            
            id_value = None
            for pattern in id_patterns:
                matches = re.findall(pattern, response.text)
                # 랜덤 ID 같은 것들 찾기 (길이 8 이상의 Base64 스타일)
                for match in matches:
                    if len(match) >= 8 and not match in ['Form1', 'contentWrap']:
                        id_value = match
                        break
                if id_value:
                    break
            
            return encparam, id_value
            
        except Exception as e:
            print(f"토큰 추출 실패: {e}")
            return None, None

    def get_financial_data_from_cf1001(self, stock_code: str):
        """cF1001 API로 재무 데이터 가져오기"""
        try:
            # 1단계: 실시간 토큰 추출
            encparam, id_value = self.extract_encparam_and_id(stock_code)
            
            if not encparam:
                return None
            
            # 2단계: cF1001 API 호출
            base_url = "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx"
            
            # 여러 파라미터 조합 시도
            param_combinations = [
                {
                    'cmp_cd': stock_code,
                    'fin_typ': '0',
                    'freq_typ': 'A',
                    'encparam': encparam,
                    'id': id_value
                } if id_value else {
                    'cmp_cd': stock_code,
                    'fin_typ': '0', 
                    'freq_typ': 'A',
                    'encparam': encparam
                },
                {
                    'cmp_cd': stock_code,
                    'fin_typ': '4',
                    'freq_typ': 'A', 
                    'encparam': encparam,
                    'id': id_value
                } if id_value else {
                    'cmp_cd': stock_code,
                    'fin_typ': '4',
                    'freq_typ': 'A',
                    'encparam': encparam
                }
            ]
            
            # Referer 설정
            self.session.headers['Referer'] = f'https://navercomp.wisereport.co.kr/company/c1010001.aspx?cmp_cd={stock_code}'
            
            for params in param_combinations:
                try:
                    response = self.session.get(base_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # 유효한 재무 데이터인지 확인
                        if self.is_valid_financial_data(data):
                            return self.parse_financial_data(data)
                            
                except Exception as e:
                    continue
            
            return None
            
        except Exception as e:
            print(f"재무 데이터 가져오기 실패: {e}")
            return None

    def is_valid_financial_data(self, data):
        """유효한 재무 데이터인지 확인"""
        if not isinstance(data, dict):
            return False
            
        # 리스트 형태의 재무 데이터가 있는지 확인
        if isinstance(data, list) and len(data) > 30:  # 재무 항목들
            return True
            
        # dt 키가 있고 유효한 데이터인지 확인
        if 'dt' in data and data['dt'] and len(data['dt']) > 10:
            return True
            
        return False

    def parse_financial_data(self, raw_data):
        """재무 데이터 파싱하여 34개 항목으로 구조화"""
        
        # 목표 34개 재무 항목
        target_items = {
            "매출액": None,
            "영업이익": None,
            "영업이익(발표기준)": None,
            "세전계속사업이익": None,
            "당기순이익": None,
            "당기순이익(지배)": None,
            "당기순이익(비지배)": None,
            "자산총계": None,
            "부채총계": None,
            "자본총계": None,
            "자본총계(지배)": None,
            "자본총계(비지배)": None,
            "자본금": None,
            "영업활동현금흐름": None,
            "투자활동현금흐름": None,
            "재무활동현금흐름": None,
            "CAPEX": None,
            "FCF": None,
            "이자발생부채": None,
            "영업이익률": None,
            "순이익률": None,
            "ROE(%)": None,
            "ROA(%)": None,
            "부채비율": None,
            "자본유보율": None,
            "EPS(원)": None,
            "PER(배)": None,
            "BPS(원)": None,
            "PBR(배)": None,
            "현금DPS(원)": None,
            "현금배당수익률": None,
            "현금배당성향(%)": None,
            "발행주식수(보통주)": None
        }
        
        try:
            # 리스트 형태 데이터 처리 (개발자 도구에서 본 형태)
            if isinstance(raw_data, list):
                # 첫 번째가 항목명, 나머지가 연도별 데이터
                periods = []
                financial_data = {}
                
                # 재무 항목 매칭
                for i, item in enumerate(raw_data):
                    if isinstance(item, str):
                        # 재무 항목명인 경우
                        if item in target_items:
                            # 다음 항목들이 해당 연도 데이터
                            values = []
                            j = i + 1
                            while j < len(raw_data) and isinstance(raw_data[j], (int, float, str)):
                                if isinstance(raw_data[j], str) and raw_data[j] in target_items:
                                    break
                                values.append(raw_data[j])
                                j += 1
                            target_items[item] = values
                
                return {
                    "financial_items": target_items,
                    "periods": periods,
                    "raw_data_length": len(raw_data)
                }
            
            # dt 키가 있는 경우
            elif isinstance(raw_data, dict) and 'dt' in raw_data:
                return {
                    "financial_items": target_items,
                    "periods": [],
                    "dt_data": raw_data['dt']
                }
            
            return {
                "financial_items": target_items,
                "periods": [],
                "raw_data": raw_data
            }
            
        except Exception as e:
            print(f"데이터 파싱 실패: {e}")
            return {
                "financial_items": target_items,
                "periods": [],
                "error": str(e),
                "raw_data": str(raw_data)[:1000]
            }


# FastAPI 인스턴스 생성
financial_api = StockFinancialAPI()


@app.get("/")
async def root():
    return {"message": "Stock Financial Data API", "version": "2.0"}


@app.get("/companies")
async def get_companies():
    """등록된 회사 목록 조회"""
    return {
        "total_companies": len(financial_api.companies),
        "cf1001_available": len(financial_api.cf1001_urls),
        "companies": list(financial_api.companies.keys())[:10]  # 처음 10개만
    }


@app.get("/financial/{stock_code}")
async def get_financial_data(stock_code: str):
    """종목코드로 재무 데이터 조회"""
    
    # 종목 코드 검증
    company_name = financial_api.get_company_name(stock_code)
    
    if not company_name.startswith("종목_"):
        # 등록된 종목인 경우
        
        # cF1001로 재무 데이터 가져오기
        financial_data = financial_api.get_financial_data_from_cf1001(stock_code)
        
        if financial_data:
            return FinancialData(
                code=stock_code,
                company_name=company_name,
                data=financial_data,
                collected_at="2025-06-14",
                data_periods=financial_data.get("periods", [])
            )
        else:
            raise HTTPException(status_code=404, detail="재무 데이터를 가져올 수 없습니다")
    else:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다")


@app.get("/test/{stock_code}")
async def test_financial_data(stock_code: str):
    """재무 데이터 테스트용 엔드포인트"""
    
    try:
        # 실시간 토큰 추출 테스트
        encparam, id_value = financial_api.extract_encparam_and_id(stock_code)
        
        # cF1001 호출 테스트
        financial_data = financial_api.get_financial_data_from_cf1001(stock_code)
        
        return {
            "stock_code": stock_code,
            "encparam_found": bool(encparam),
            "id_found": bool(id_value),
            "financial_data_success": bool(financial_data),
            "encparam": encparam[:20] + "..." if encparam else None,
            "id_value": id_value,
            "data_preview": str(financial_data)[:500] if financial_data else None
        }
        
    except Exception as e:
        return {
            "stock_code": stock_code,
            "error": str(e)
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
