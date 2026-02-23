import json
import os
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from typing import Dict
from contextlib import asynccontextmanager
import uvicorn
import time
from datetime import datetime
import re

STOCK_DATA: Dict[str, str] = {}

# cF1001 작동하는 토큰들
CF1001_TOKENS = {
    "삼성전자": {
        "code": "005930",
        "cf1001_url":
        "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=005930&fin_typ=0&freq_typ=A&encparam=R3AvQTVUVkhlMC9DNTVFb0RhRDFoZz09&id=VGVTbkwxZ2",
        "last_verified": "2025-06-14"
    }
    # 추가 토큰들은 여기에 추가
}


def load_stock_data():
    global STOCK_DATA
    try:
        file_path = os.path.join("company_codes", "stock_companies.json")
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            STOCK_DATA = {
                name: details['code']
                for name, details in raw_data.items()
            }
        print(f"✅ {len(STOCK_DATA)}개 종목 코드를 성공적으로 로드했습니다.")
    except Exception as e:
        print(f"❌ [치명적 오류] 'company_codes/stock_companies.json' 파일 로드 실패: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 서버 시작... 데이터를 로드합니다.")
    load_stock_data()
    yield
    print("👋 서버 종료.")


app = FastAPI(lifespan=lifespan)


def get_headers():
    return {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }


def get_realtime_info(stock_code: str) -> dict:
    try:
        url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content,
                             'html.parser',
                             from_encoding='euc-kr')

        price_element = soup.select_one(
            'div.today > p.no_today > em > span.blind')
        price = price_element.text.strip() if price_element else "정보 없음"

        company = soup.select_one('div.wrap_company h2 a')
        change_info = soup.select_one('p.no_exday')

        market_cap_td = soup.find('th', string='시가총액')
        market_cap = market_cap_td.find_next_sibling(
            'td').text.strip() if market_cap_td else "정보 없음"

        change_price_val = "0"
        rate_val = "0.00%"
        if change_info:
            price_em = change_info.select_one('em')
            if price_em:
                spans = price_em.select('span.blind')
                if spans:
                    price_val = spans[0].text.strip()
                    if '상승' in price_em.text:
                        change_price_val = f"+{price_val}"
                    elif '하락' in price_em.text:
                        change_price_val = f"-{price_val}"
            rate_em_list = change_info.select('em')
            if len(rate_em_list) > 1:
                rate_em = rate_em_list[1]
                spans = rate_em.select('span.blind')
                if spans:
                    rate_val_str = spans[0].text.strip()
                    if '상승' in rate_em.text: rate_val = f"+{rate_val_str}%"
                    elif '하락' in rate_em.text: rate_val = f"-{rate_val_str}%"

        return {
            "회사명": company.text.strip() if company else "정보 없음",
            "현재가": price,
            "전일대비": change_price_val,
            "등락률": rate_val,
            "시가총액": market_cap,
        }
    except Exception as e:
        return {"error": f"실시간 정보 수집 중 오류 발생: {e}"}


def parse_html_table_simple(html_content: str) -> dict:
    """HTML 테이블을 간단히 파싱 (pandas 없이)"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        tables = soup.find_all('table')

        parsed_data = {}

        for table_idx, table in enumerate(tables):
            rows = table.find_all('tr')
            if not rows:
                continue

            table_data = {}
            headers = []

            # 헤더 추출
            header_row = rows[0]
            header_cells = header_row.find_all(['th', 'td'])
            for cell in header_cells:
                headers.append(cell.get_text(strip=True))

            # 데이터 행 처리
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                # 첫 번째 셀을 키로 사용
                row_key = cells[0].get_text(strip=True)
                if not row_key or row_key in ['', ' ']:
                    continue

                # 나머지 셀들을 데이터로 사용
                row_data = {}
                for i, cell in enumerate(cells[1:], 1):
                    if i < len(headers):
                        header = headers[i]
                        value = cell.get_text(strip=True)
                        if value and value not in ['', '-', 'N/A']:
                            row_data[header] = value

                if row_data:
                    table_data[row_key] = row_data

            if table_data:
                parsed_data[f"table_{table_idx + 1}"] = table_data

        return parsed_data

    except Exception as e:
        return {"error": f"HTML 테이블 파싱 실패: {e}"}


def get_cf1002_financial_data(stock_code: str) -> dict:
    """cF1002 API로 재무데이터 수집"""
    try:
        url = f"https://navercomp.wisereport.co.kr/v2/company/cF1002.aspx?cmp_cd={stock_code}&finGubun=MAIN&frq=0"

        response = requests.get(url, headers=get_headers(), timeout=15)
        response.raise_for_status()

        # EUC-KR 인코딩으로 디코드
        content = response.content.decode('euc-kr', errors='ignore')

        # HTML 테이블 파싱
        financial_data = parse_html_table_simple(content)

        if not financial_data:
            return {"error": "cF1002 테이블 파싱 실패"}

        # 메타 정보 추가
        financial_data["meta"] = {
            "data_source":
            "cF1002",
            "content_length":
            len(content),
            "table_count":
            len([k for k in financial_data.keys() if k.startswith("table_")])
        }

        return financial_data

    except Exception as e:
        return {"error": f"cF1002 데이터 수집 실패: {e}"}


def get_cf1001_financial_data(company_name: str) -> dict:
    """cF1001 API로 완전한 재무제표 수집"""
    try:
        if company_name not in CF1001_TOKENS:
            return {"error": f"{company_name}: cF1001 토큰 없음"}

        token_data = CF1001_TOKENS[company_name]
        cf1001_url = token_data["cf1001_url"]

        response = requests.get(cf1001_url, headers=get_headers(), timeout=15)
        response.raise_for_status()

        # EUC-KR 디코딩
        content = response.content.decode('euc-kr', errors='ignore')

        # HTML 테이블 파싱
        financial_data = parse_html_table_simple(content)

        if not financial_data:
            return {"error": "cF1001 테이블 파싱 실패"}

        # 테이블 분류 시도
        classified_data = {}
        for table_key, table_data in financial_data.items():
            if table_key.startswith("table_"):
                # 테이블 내용으로 유형 추정
                table_items = list(table_data.keys())

                if any(keyword in str(table_items)
                       for keyword in ['매출액', '영업이익', '당기순이익']):
                    classified_data["손익계산서"] = table_data
                elif any(keyword in str(table_items)
                         for keyword in ['자산총계', '부채총계', '자본총계']):
                    classified_data["재무상태표"] = table_data
                elif any(keyword in str(table_items)
                         for keyword in ['영업활동', '투자활동', '재무활동']):
                    classified_data["현금흐름표"] = table_data
                else:
                    classified_data[table_key] = table_data

        # 메타 정보 추가
        classified_data["meta"] = {
            "data_source": "cF1001",
            "content_length": len(content),
            "table_count": len(classified_data) - 1,  # meta 제외
            "token_used": token_data["last_verified"]
        }

        return classified_data

    except Exception as e:
        return {"error": f"cF1001 데이터 수집 실패: {e}"}


def get_financial_statements(stock_code: str, company_name: str) -> dict:
    """통합 재무정보 수집"""
    financial_data = {}

    try:
        # 1. cF1002 데이터 수집 (안정적)
        print(f"📊 {company_name} cF1002 데이터 수집 중...")
        cf1002_data = get_cf1002_financial_data(stock_code)
        if "error" not in cf1002_data:
            financial_data["cF1002_summary"] = cf1002_data
            print(f"   ✅ cF1002 성공")
        else:
            print(f"   ❌ cF1002 실패: {cf1002_data['error']}")

        # 2. cF1001 데이터 수집 (토큰 있는 경우)
        if company_name in CF1001_TOKENS:
            print(f"📊 {company_name} cF1001 데이터 수집 중...")
            cf1001_data = get_cf1001_financial_data(company_name)
            if "error" not in cf1001_data:
                financial_data["cF1001_detailed"] = cf1001_data
                print(f"   ✅ cF1001 성공")
            else:
                print(f"   ❌ cF1001 실패: {cf1001_data['error']}")

        # 3. 데이터 통합 정보
        financial_data["data_sources"] = {
            "cF1002_available":
            "error" not in cf1002_data,
            "cF1001_available":
            company_name in CF1001_TOKENS
            and "cF1001_detailed" in financial_data,
            "collection_time":
            datetime.now().isoformat()
        }

        return financial_data

    except Exception as e:
        return {"error": f"통합 재무정보 수집 실패: {e}"}


@app.get("/")
def get_status():
    cf1001_companies = list(CF1001_TOKENS.keys())
    return {
        "status": "ok",
        "message": "통합 API 서버가 정상 동작 중입니다.",
        "loaded_stocks": len(STOCK_DATA),
        "cf1001_available_companies": cf1001_companies,
        "features": {
            "realtime_data": "모든 종목 지원",
            "cF1002_summary": "모든 종목 지원 (안정적 재무데이터)",
            "cF1001_detailed": f"{len(cf1001_companies)}개 종목 지원 (완전한 재무제표)"
        },
        "libraries": {
            "pandas": "미사용 (순수 파이썬 파싱)",
            "beautifulsoup": "사용",
            "requests": "사용"
        }
    }


@app.get("/api/v1/analysis")
def analyze_company(company_name: str):
    stock_code = STOCK_DATA.get(company_name)
    if not stock_code:
        raise HTTPException(status_code=404,
                            detail=f"'{company_name}' 기업을 찾을 수 없습니다.")

    print(f"\n🔍 {company_name}({stock_code}) 분석 시작")

    realtime_info = get_realtime_info(stock_code)
    financial_statements = get_financial_statements(stock_code, company_name)

    return {
        "query": {
            "company_name": company_name,
            "stock_code": stock_code
        },
        "realtime_data": realtime_info,
        "financial_statements": financial_statements
    }


@app.get("/api/v1/cf1002/{company_name}")
def get_cf1002_data(company_name: str):
    """cF1002 전용 엔드포인트"""
    stock_code = STOCK_DATA.get(company_name)
    if not stock_code:
        raise HTTPException(status_code=404,
                            detail=f"'{company_name}' 기업을 찾을 수 없습니다.")

    cf1002_data = get_cf1002_financial_data(stock_code)

    return {
        "query": {
            "company_name": company_name,
            "stock_code": stock_code
        },
        "data_source": "cF1002",
        "financial_data": cf1002_data,
        "collected_at": datetime.now().isoformat()
    }


@app.get("/api/v1/cf1001/{company_name}")
def get_cf1001_data(company_name: str):
    """cF1001 전용 엔드포인트"""
    if company_name not in CF1001_TOKENS:
        raise HTTPException(status_code=404,
                            detail=f"'{company_name}': cF1001 토큰이 없습니다.")

    cf1001_data = get_cf1001_financial_data(company_name)

    return {
        "query": {
            "company_name": company_name,
            "stock_code": CF1001_TOKENS[company_name]["code"]
        },
        "data_source": "cF1001",
        "financial_data": cf1001_data,
        "collected_at": datetime.now().isoformat()
    }


if __name__ == "__main__":
    print("▶️ pandas 없는 통합 FastAPI 서버를 시작합니다.")
    print(f"🔗 cF1001 지원 기업: {list(CF1001_TOKENS.keys())}")
    print("📚 라이브러리: BeautifulSoup + 순수 파이썬 파싱")
    uvicorn.run(app, host="0.0.0.0", port=8000)
