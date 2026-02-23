import requests
import json
import pandas as pd
from io import StringIO
from datetime import datetime
import os


class WorkingTokenSystem:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # 현재 확인된 작동하는 토큰들
        self.working_tokens = {
            "삼성전자": {
                "code":
                "005930",
                "cf1001_urls": [{
                    "url":
                    "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=005930&fin_typ=0&freq_typ=A&encparam=R3AvQTVUVkhlMC9DNTVFb0RhRDFoZz09&id=VGVTbkwxZ2",
                    "collected_at": "2025-06-14_latest",
                    "status": "confirmed_working"
                }, {
                    "url":
                    "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=005930&fin_typ=0&freq_typ=A&encparam=MERqUlVkcVhRNHhJL2JDbWVFcHFhQT09&id=VGVTbkwxZ2",
                    "collected_at": "2025-06-14_afternoon",
                    "status": "confirmed_working"
                }]
            },
            # 다른 기업들도 추가 예정
        }

    def test_working_tokens(self):
        """현재 보유한 토큰들의 유효성 재검증"""
        print("🔍 작동하는 토큰들 재검증 시작")

        valid_count = 0

        for company, data in self.working_tokens.items():
            print(f"\n📊 {company}({data['code']}) 검증:")

            for i, token_info in enumerate(data['cf1001_urls']):
                url = token_info['url']
                collected_at = token_info['collected_at']

                try:
                    response = self.session.get(url, timeout=10)

                    if response.status_code == 200 and len(
                            response.content) > 100:
                        print(
                            f"   ✅ 토큰 {i+1} ({collected_at}): 유효 ({len(response.content)} bytes)"
                        )
                        token_info['last_verified'] = datetime.now().isoformat(
                        )
                        token_info['verification_status'] = 'valid'
                        valid_count += 1
                    else:
                        print(f"   ❌ 토큰 {i+1} ({collected_at}): 무효")
                        token_info['verification_status'] = 'invalid'

                except Exception as e:
                    print(f"   ❌ 토큰 {i+1} ({collected_at}): 오류 - {e}")
                    token_info['verification_status'] = 'error'

        print(f"\n📋 검증 완료: {valid_count}개 유효한 토큰 확인")
        return valid_count

    def get_cf1001_data(self, company_name):
        """특정 기업의 cF1001 데이터 수집"""
        if company_name not in self.working_tokens:
            print(f"❌ {company_name}: 토큰 없음")
            return None

        company_data = self.working_tokens[company_name]
        stock_code = company_data['code']

        print(f"📊 {company_name}({stock_code}) cF1001 데이터 수집")

        # 유효한 토큰 중 첫 번째 사용
        for token_info in company_data['cf1001_urls']:
            if token_info.get('verification_status') == 'valid':
                url = token_info['url']

                try:
                    print(f"🔗 토큰 사용: {token_info['collected_at']}")
                    response = self.session.get(url, timeout=15)
                    response.raise_for_status()

                    # EUC-KR 디코딩
                    content = response.content.decode('euc-kr',
                                                      errors='ignore')

                    # HTML 테이블 파싱
                    tables = pd.read_html(StringIO(content), encoding='euc-kr')

                    if tables:
                        print(f"✅ {company_name}: {len(tables)}개 테이블 수집 성공")

                        # 테이블 데이터 처리
                        financial_data = self.parse_cf1001_tables(tables)

                        return {
                            "company_name": company_name,
                            "stock_code": stock_code,
                            "data_source": "cF1001",
                            "tables_count": len(tables),
                            "financial_data": financial_data,
                            "collected_at": datetime.now().isoformat(),
                            "token_used": token_info['collected_at']
                        }
                    else:
                        print(f"⚠️ {company_name}: 테이블 파싱 실패")

                except Exception as e:
                    print(f"❌ {company_name} 데이터 수집 실패: {e}")
                    continue

        print(f"❌ {company_name}: 모든 토큰 실패")
        return None

    def parse_cf1001_tables(self, tables):
        """cF1001 테이블들을 우리가 원하는 형태로 파싱"""
        financial_data = {}

        try:
            for i, df in enumerate(tables):
                print(f"   📋 테이블 {i+1} 처리 중... (크기: {df.shape})")

                # 테이블 정리
                df = df.dropna(axis=0, how='all')
                df = df.dropna(axis=1, how='all')

                if df.empty:
                    continue

                # 멀티인덱스 처리
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(-1)

                # 첫 번째 컬럼을 인덱스로 설정
                if len(df.columns) > 1:
                    df = df.set_index(df.columns[0])

                # 데이터 추출
                table_data = {}
                for col in df.columns:
                    for idx, value in df[col].items():
                        if pd.notna(value) and idx is not None:
                            clean_key = str(idx).replace('*', '').strip()

                            if isinstance(value, (int, float)):
                                table_data[clean_key] = f"{float(value):,}"
                            else:
                                table_data[clean_key] = str(value)

                if table_data:
                    financial_data[f"table_{i+1}"] = table_data
                    print(f"      → {len(table_data)}개 항목 추출")

            return financial_data

        except Exception as e:
            print(f"❌ 테이블 파싱 오류: {e}")
            return {}

    def add_new_token(self, company_name, stock_code, cf1001_url, note=""):
        """새로운 토큰 추가"""
        if company_name not in self.working_tokens:
            self.working_tokens[company_name] = {
                "code": stock_code,
                "cf1001_urls": []
            }

        new_token = {
            "url": cf1001_url,
            "collected_at": datetime.now().isoformat(),
            "note": note,
            "status": "pending_verification"
        }

        self.working_tokens[company_name]["cf1001_urls"].append(new_token)
        print(f"✅ {company_name} 새 토큰 추가됨")

    def save_token_database(self, filename="working_tokens_db.json"):
        """토큰 데이터베이스 저장"""
        try:
            file_path = os.path.join("company_codes", filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.working_tokens, f, ensure_ascii=False, indent=2)
            print(f"💾 토큰 DB 저장: {file_path}")
            return file_path
        except Exception as e:
            print(f"❌ 저장 실패: {e}")
            return None

    def create_main_api_integration(self):
        """main.py에 통합할 수 있는 함수 생성"""
        integration_code = '''
def get_cf1001_financial_data(company_name):
    """cF1001 기반 재무데이터 수집 (main.py 통합용)"""

    # 작동하는 토큰들 (주기적 업데이트 필요)
    working_tokens = {
        "삼성전자": {
            "code": "005930",
            "url": "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=005930&fin_typ=0&freq_typ=A&encparam=R3AvQTVUVkhlMC9DNTVFb0RhRDFoZz09&id=VGVTbkwxZ2"
        }
    }

    if company_name not in working_tokens:
        return {"error": f"{company_name}: cF1001 토큰 없음"}

    token_data = working_tokens[company_name]

    try:
        response = requests.get(token_data["url"], headers=get_headers(), timeout=15)
        response.raise_for_status()

        content = response.content.decode('euc-kr', errors='ignore')
        tables = pd.read_html(StringIO(content), encoding='euc-kr')

        # 테이블 파싱 로직
        financial_data = {}
        for i, df in enumerate(tables):
            # 파싱 로직 구현
            pass

        return financial_data

    except Exception as e:
        return {"error": f"cF1001 데이터 수집 실패: {e}"}
'''

        with open("cf1001_integration.py", "w", encoding="utf-8") as f:
            f.write(integration_code)

        print("📄 main.py 통합용 코드 생성: cf1001_integration.py")


def main():
    """메인 테스트 함수"""
    print("🚀 작동하는 토큰 시스템 테스트")

    system = WorkingTokenSystem()

    # 1. 토큰 유효성 검증
    valid_count = system.test_working_tokens()

    if valid_count > 0:
        print(f"\n🎉 {valid_count}개 유효한 토큰 확인!")

        # 2. 실제 데이터 수집 테스트
        print(f"\n📊 실제 데이터 수집 테스트:")

        for company in system.working_tokens.keys():
            print(f"\n{'='*60}")
            result = system.get_cf1001_data(company)

            if result:
                print(f"🎉 {company} 성공!")
                print(f"   📋 테이블 수: {result['tables_count']}")
                print(f"   📊 데이터 항목: {len(result['financial_data'])}개 그룹")

                # 데이터 미리보기
                for table_name, table_data in result['financial_data'].items():
                    print(f"   📈 {table_name}: {len(table_data)}개 항목")
                    sample_items = list(table_data.items())[:3]
                    for key, value in sample_items:
                        print(f"      • {key}: {value}")
            else:
                print(f"💔 {company} 실패")

        # 3. 토큰 DB 저장
        system.save_token_database()

        # 4. main.py 통합 코드 생성
        system.create_main_api_integration()

        print(f"\n🎯 다음 단계: main.py에 cF1001 기능 추가")

    else:
        print(f"\n❌ 유효한 토큰이 없습니다. 새 토큰 수집이 필요합니다.")


if __name__ == "__main__":
    main()
