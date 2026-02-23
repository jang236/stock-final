import json
import time
import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, parse_qs, urlparse


class SimpleCF1001Collector:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.urls_db = {}

    def load_companies(self):
        """기존 종목 리스트 로드"""
        try:
            file_path = os.path.join("company_codes", "stock_companies.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                companies = json.load(f)
            print(f"✅ {len(companies)}개 종목 코드 로드 완료")
            return companies
        except Exception as e:
            print(f"❌ 종목 코드 로드 실패: {e}")
            return {}

    def extract_cf1001_from_page(self, company_name, stock_code):
        """페이지 소스에서 cF1001 URL 추출"""
        try:
            # 재무 페이지 접속
            url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"
            print(f"📍 {company_name}({stock_code}) 페이지 분석 중...")

            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # 페이지 소스에서 JavaScript 코드 찾기
            soup = BeautifulSoup(response.content, 'html.parser')

            # 방법 1: JavaScript에서 URL 패턴 찾기
            scripts = soup.find_all('script')
            cf1001_url = None

            for script in scripts:
                if script.string:
                    script_content = script.string

                    # cF1001.aspx가 포함된 URL 패턴 찾기
                    cf1001_matches = re.findall(
                        r'https?://[^"\']*cF1001\.aspx[^"\']*', script_content)

                    for match in cf1001_matches:
                        if stock_code in match:
                            cf1001_url = match
                            break

                    if cf1001_url:
                        break

            # 방법 2: 직접 API 호출해보기 (encparam 생성 시도)
            if not cf1001_url:
                cf1001_url = self.generate_cf1001_url(stock_code)

            if cf1001_url:
                print(f"✅ {company_name} cF1001 URL 추출 성공")
                return cf1001_url
            else:
                print(f"⚠️ {company_name} cF1001 URL 찾지 못함")
                return None

        except Exception as e:
            print(f"❌ {company_name} URL 추출 실패: {e}")
            return None

    def generate_cf1001_url(self, stock_code):
        """cF1001 URL 생성 시도 (패턴 분석 기반)"""
        try:
            # 먼저 기본 재무 페이지에 숨겨진 파라미터가 있는지 확인
            coinfo_url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"
            response = self.session.get(coinfo_url)

            # HTML에서 숨겨진 input 필드나 JavaScript 변수 찾기
            soup = BeautifulSoup(response.content, 'html.parser')

            # encparam과 id 값을 찾기 위한 패턴들
            patterns = [
                r'encparam["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'id["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'cmp_cd["\']?\s*[:=]\s*["\']([^"\']+)["\']'
            ]

            encparam = None
            id_param = None

            page_text = str(soup)

            for pattern in patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    if 'encparam' in pattern:
                        encparam = matches[0]
                    elif 'id' in pattern and not id_param:
                        id_param = matches[0]

            # URL 조합 시도
            if encparam and id_param:
                url = f"https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd={stock_code}&fin_typ=0&freq_typ=A&encparam={encparam}&id={id_param}"
                return url

            return None

        except Exception as e:
            print(f"❌ URL 생성 실패: {e}")
            return None

    def test_url_validity(self, url):
        """URL이 유효한지 테스트"""
        try:
            response = self.session.get(url, timeout=5)
            return response.status_code == 200 and len(response.content) > 100
        except:
            return False

    def collect_urls(self, test_mode=True):
        """URL 수집 실행"""
        companies = self.load_companies()

        if test_mode:
            # 테스트 모드: 주요 종목만
            test_companies = ["삼성전자", "NAVER", "신한금융지주", "SK하이닉스", "카카오"]
            companies = {
                name: details
                for name, details in companies.items()
                if name in test_companies
            }
            print(f"🧪 테스트 모드: {len(companies)}개 종목으로 제한")

        success_count = 0

        for company_name, details in companies.items():
            stock_code = details['code']

            try:
                cf1001_url = self.extract_cf1001_from_page(
                    company_name, stock_code)

                if cf1001_url:
                    # URL 유효성 테스트
                    if self.test_url_validity(cf1001_url):
                        self.urls_db[company_name] = {
                            "code": stock_code,
                            "cF1001_url": cf1001_url
                        }
                        success_count += 1
                        print(f"✅ {company_name} URL 검증 완료")
                    else:
                        print(f"⚠️ {company_name} URL 유효하지 않음")

                # 요청 간격
                time.sleep(1)

            except Exception as e:
                print(f"❌ {company_name} 처리 중 오류: {e}")
                continue

        print(f"📋 수집 완료: {success_count}/{len(companies)}개 성공")
        return self.urls_db

    def save_urls(self, filename="cf1001_urls_simple.json"):
        """수집된 URL을 파일로 저장"""
        try:
            file_path = os.path.join("company_codes", filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.urls_db, f, ensure_ascii=False, indent=2)
            print(f"✅ URL 데이터베이스 저장 완료: {file_path}")
        except Exception as e:
            print(f"❌ 파일 저장 실패: {e}")


def main():
    """메인 실행 함수"""
    try:
        print("🚀 cF1001 URL 수집 시작 (Selenium 없는 방식)")

        collector = SimpleCF1001Collector()

        # 테스트 모드로 실행
        urls_db = collector.collect_urls(test_mode=True)

        if urls_db:
            collector.save_urls("cf1001_urls_simple.json")

            # 결과 출력
            print("\n📊 수집 결과:")
            for company, data in urls_db.items():
                print(f"• {company}: {data['code']}")
                print(f"  URL: {data['cF1001_url'][:80]}...")
        else:
            print("❌ 수집된 URL이 없습니다.")
            print("💡 수동으로 몇 개 URL을 추가해보겠습니다.")

            # 수동 URL 추가 (테스트용)
            manual_urls = {
                "NAVER": {
                    "code":
                    "035420",
                    "cF1001_url":
                    "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=035420&fin_typ=0&freq_typ=A&encparam=VnI0MnRwd0Rwd3FFdjFOa1BnUEI4dz09&id=QmZIZ20rMn"
                },
                "신한금융지주": {
                    "code":
                    "055550",
                    "cF1001_url":
                    "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=055550&fin_typ=0&freq_typ=A&encparam=b0JMTlJ4dmh0V01VQ3VxVGRWb2p0Zz09&id=ZlEwemUxRm"
                }
            }

            collector.urls_db = manual_urls
            collector.save_urls("cf1001_urls_manual.json")
            print("✅ 수동 URL 저장 완료")

    except Exception as e:
        print(f"❌ 전체 프로세스 실패: {e}")


if __name__ == "__main__":
    main()
