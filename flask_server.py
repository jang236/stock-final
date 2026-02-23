import json
import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

# 전역 변수
STOCK_DATA = {}

# cF1001 작동하는 토큰들
CF1001_TOKENS = {
    "삼성전자": {
        "code": "005930",
        "cf1001_url":
        "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=005930&fin_typ=0&freq_typ=A&encparam=R3AvQTVUVkhlMC9DNTVFb0RhRDFoZz09&id=VGVTbkwxZ2",
        "last_verified": "2025-06-14"
    }
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
        print(f"❌ 종목 코드 로드 실패: {e}")


def get_headers():
    return {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }


def parse_html_table_simple(html_content):
    """HTML 테이블을 간단히 파싱"""
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

                row_key = cells[0].get_text(strip=True)
                if not row_key:
                    continue

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


def get_cf1001_financial_data(company_name):
    """cF1001 데이터 수집"""
    try:
        if company_name not in CF1001_TOKENS:
            return {"error": f"{company_name}: cF1001 토큰 없음"}

        token_data = CF1001_TOKENS[company_name]
        cf1001_url = token_data["cf1001_url"]

        print(f"📊 {company_name} cF1001 데이터 수집 중...")
        response = requests.get(cf1001_url, headers=get_headers(), timeout=15)
        response.raise_for_status()

        content = response.content.decode('euc-kr', errors='ignore')
        financial_data = parse_html_table_simple(content)

        if not financial_data:
            return {"error": "cF1001 테이블 파싱 실패"}

        # 테이블 분류
        classified_data = {}
        for table_key, table_data in financial_data.items():
            if table_key.startswith("table_"):
                table_items = str(list(table_data.keys()))

                if any(keyword in table_items
                       for keyword in ['매출액', '영업이익', '당기순이익']):
                    classified_data["손익계산서"] = table_data
                elif any(keyword in table_items
                         for keyword in ['자산총계', '부채총계', '자본총계']):
                    classified_data["재무상태표"] = table_data
                elif any(keyword in table_items
                         for keyword in ['영업활동', '투자활동', '재무활동']):
                    classified_data["현금흐름표"] = table_data
                else:
                    classified_data[table_key] = table_data

        classified_data["meta"] = {
            "data_source": "cF1001",
            "content_length": len(content),
            "table_count": len(classified_data) - 1,
            "collected_at": datetime.now().isoformat()
        }

        print(f"✅ {company_name} cF1001 수집 성공 ({len(classified_data)-1}개 테이블)")
        return classified_data

    except Exception as e:
        error_msg = f"cF1001 데이터 수집 실패: {e}"
        print(f"❌ {company_name} {error_msg}")
        return {"error": error_msg}


def get_cf1002_financial_data(stock_code):
    """cF1002 데이터 수집"""
    try:
        url = f"https://navercomp.wisereport.co.kr/v2/company/cF1002.aspx?cmp_cd={stock_code}&finGubun=MAIN&frq=0"

        print(f"📊 {stock_code} cF1002 데이터 수집 중...")
        response = requests.get(url, headers=get_headers(), timeout=15)
        response.raise_for_status()

        content = response.content.decode('euc-kr', errors='ignore')
        financial_data = parse_html_table_simple(content)

        if not financial_data:
            return {"error": "cF1002 테이블 파싱 실패"}

        financial_data["meta"] = {
            "data_source":
            "cF1002",
            "content_length":
            len(content),
            "table_count":
            len([k for k in financial_data.keys() if k.startswith("table_")]),
            "collected_at":
            datetime.now().isoformat()
        }

        print(f"✅ {stock_code} cF1002 수집 성공")
        return financial_data

    except Exception as e:
        error_msg = f"cF1002 데이터 수집 실패: {e}"
        print(f"❌ {stock_code} {error_msg}")
        return {"error": error_msg}


@app.route('/')
def get_status():
    cf1001_companies = list(CF1001_TOKENS.keys())
    return jsonify({
        "status": "ok",
        "message": "Flask 기반 API 서버가 정상 동작 중입니다.",
        "loaded_stocks": len(STOCK_DATA),
        "cf1001_available_companies": cf1001_companies,
        "features": {
            "realtime_data": "개발 예정",
            "cF1002_summary": "모든 종목 지원",
            "cF1001_detailed": f"{len(cf1001_companies)}개 종목 지원"
        },
        "framework": "Flask (FastAPI 대신)"
    })


@app.route('/api/v1/cf1001/<company_name>')
def get_cf1001_data(company_name):
    """cF1001 전용 엔드포인트"""
    if company_name not in CF1001_TOKENS:
        return jsonify({"error": f"'{company_name}': cF1001 토큰이 없습니다."}), 404

    cf1001_data = get_cf1001_financial_data(company_name)

    return jsonify({
        "query": {
            "company_name": company_name,
            "stock_code": CF1001_TOKENS[company_name]["code"]
        },
        "data_source": "cF1001",
        "financial_data": cf1001_data,
        "collected_at": datetime.now().isoformat()
    })


@app.route('/api/v1/cf1002/<company_name>')
def get_cf1002_data(company_name):
    """cF1002 전용 엔드포인트"""
    stock_code = STOCK_DATA.get(company_name)
    if not stock_code:
        return jsonify({"error": f"'{company_name}' 기업을 찾을 수 없습니다."}), 404

    cf1002_data = get_cf1002_financial_data(stock_code)

    return jsonify({
        "query": {
            "company_name": company_name,
            "stock_code": stock_code
        },
        "data_source": "cF1002",
        "financial_data": cf1002_data,
        "collected_at": datetime.now().isoformat()
    })


@app.route('/api/v1/analysis')
def analyze_company():
    """통합 분석 엔드포인트"""
    company_name = request.args.get('company_name')
    if not company_name:
        return jsonify({"error": "company_name 파라미터가 필요합니다."}), 400

    stock_code = STOCK_DATA.get(company_name)
    if not stock_code:
        return jsonify({"error": f"'{company_name}' 기업을 찾을 수 없습니다."}), 404

    print(f"\n🔍 {company_name}({stock_code}) 통합 분석 시작")

    # cF1002 데이터 수집
    cf1002_data = get_cf1002_financial_data(stock_code)

    # cF1001 데이터 수집 (토큰 있는 경우)
    cf1001_data = None
    if company_name in CF1001_TOKENS:
        cf1001_data = get_cf1001_financial_data(company_name)

    financial_statements = {
        "data_sources": {
            "cF1002_available": "error" not in cf1002_data,
            "cF1001_available": cf1001_data is not None
            and "error" not in cf1001_data,
            "collection_time": datetime.now().isoformat()
        }
    }

    if "error" not in cf1002_data:
        financial_statements["cF1002_summary"] = cf1002_data

    if cf1001_data and "error" not in cf1001_data:
        financial_statements["cF1001_detailed"] = cf1001_data

    return jsonify({
        "query": {
            "company_name": company_name,
            "stock_code": stock_code
        },
        "realtime_data": {
            "message": "개발 예정"
        },
        "financial_statements": financial_statements
    })


if __name__ == "__main__":
    print("🚀 Flask 기반 API 서버를 시작합니다.")
    print(f"🔗 cF1001 지원 기업: {list(CF1001_TOKENS.keys())}")

    # 종목 데이터 로드
    load_stock_data()

    # Flask 서버 실행
    app.run(host="0.0.0.0", port=8000, debug=True)
