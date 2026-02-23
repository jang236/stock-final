import json
import time
import os
import requests
import re
import random
from concurrent.futures import ThreadPoolExecutor, as_completed


class CF1001Collector:
    def __init__(self, max_workers=2):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
            'Connection': 'keep-alive'
        })
        self.urls_db = {}
        self.failed_companies = []
        self.max_workers = max_workers

    def load_companies(self):
        try:
            file_path = os.path.join("company_codes", "stock_companies.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                companies = json.load(f)
            print(f"✅ {len(companies)}개 종목 로드 완료")
            return companies
        except Exception as e:
            print(f"❌ 종목 로드 실패: {e}")
            return {}

    def extract_encparam(self, page_text):
        patterns = [
            r"encparam:\s*['\"]([\w+/=]+)['\"]",
            r"encparam['\"]?\s*[:=]\s*['\"]([\w+/=]+)['\"]"
        ]
        for pattern in patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                return matches[0]
        return None

    def get_cf1001_url(self, company_name, stock_code):
        try:
            # 1단계: 메인 페이지 접속
            main_url = f"https://navercomp.wisereport.co.kr/company/c1010001.aspx?cmp_cd={stock_code}"
            response = self.session.get(main_url, timeout=10)
            
            # 2단계: encparam 추출
            encparam = self.extract_encparam(response.text)
            if not encparam:
                return None
            
            # 3단계: AJAX URL 생성 및 테스트
            base_url = "https://navercomp.wisereport.co.kr/company/ajax/cF1001.aspx"
            
            # 여러 조합 시도
            combinations = [
                {'flag': 4, 'cmp_cd': stock_code, 'grp_cd': '03', 'encparam': encparam},
                {'flag': 4, 'cmp_cd': stock_code, 'grp_cd': '01', 'encparam': encparam}
            ]
            
            for params in combinations:
                param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
                test_url = f"{base_url}?{param_str}"
                
                if self.test_url(test_url, stock_code):
                    return test_url
            
            return None
            
        except Exception as e:
            print(f"❌ {company_name} 오류: {e}")
            return None

    def test_url(self, url, stock_code):
        try:
            # AJAX 헤더 설정
            ajax_headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'https://navercomp.wisereport.co.kr/company/c1010001.aspx?cmp_cd={stock_code}'
            }
            
            # 헤더 업데이트
            old_headers = self.session.headers.copy()
            self.session.headers.update(ajax_headers)
            
            # 요청
            response = self.session.get(url, timeout=5)
            
            # 헤더 복원
            self.session.headers = old_headers
            
            # 검증
            if response.status_code == 200:
                try:
                    data = response.json()
                    return isinstance(data, dict)
                except:
                    return False
            return False
            
        except:
            return False

    def process_company(self, company_data):
        company_name, details = company_data
        stock_code = details['code']
        
        print(f"📍 처리중: {company_name}({stock_code})")
        
        cf1001_url = self.get_cf1001_url(company_name, stock_code)
        
        if cf1001_url:
            result = {
                "code": stock_code,
                "cF1001_url": cf1001_url,
                "collected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "success"
            }
            print(f"✅ {company_name} 성공")
            return company_name, result
        else:
            print(f"❌ {company_name} 실패")
            return company_name, None

    def collect_urls(self, test_mode=False):
        companies = self.load_companies()
        
        if test_mode:
            items = list(companies.items())
            random.shuffle(items)
            companies = dict(items[:10])  # 10개만 테스트
            print(f"🧪 테스트 모드: {len(companies)}개 종목")
        
        print(f"🚀 {len(companies)}개 종목 수집 시작")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.process_company, company_data): company_data[0]
                for company_data in companies.items()
            }
            
            for future in as_completed(futures):
                company_name, result = future.result()
                if result:
                    self.urls_db[company_name] = result
                else:
                    self.failed_companies.append(company_name)
        
        success_count = len(self.urls_db)
        total_count = len(companies)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        print(f"\n📊 수집 완료: {success_count}/{total_count} ({success_rate:.1f}%)")
        return self.urls_db

    def save_results(self):
        if self.urls_db:
            file_path = os.path.join("company_codes", "cf1001_urls_success.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.urls_db, f, ensure_ascii=False, indent=2)
            print(f"✅ 성공 데이터 저장: {file_path} ({len(self.urls_db)}개)")
        
        if self.failed_companies:
            file_path = os.path.join("company_codes", "cf1001_failed.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.failed_companies, f, ensure_ascii=False, indent=2)
            print(f"📝 실패 데이터 저장: {file_path} ({len(self.failed_companies)}개)")


def main():
    print("🚀 cF1001 URL 수집기 v2.0")
    
    collector = CF1001Collector(max_workers=2)
    
    try:
        # 1단계: 테스트 실행
        print("1️⃣ 테스트 수집 (10개 종목)")
        test_results = collector.collect_urls(test_mode=True)
        
        if len(test_results) > 0:
            success_rate = len(test_results) / 10 * 100
            print(f"✅ 테스트 성공률: {success_rate:.1f}%")
            
            if success_rate >= 30:
                response = input("\n전체 수집을 진행하시겠습니까? (y/N): ")
                if response.lower() == 'y':
                    print("2️⃣ 전체 수집 시작")
                    collector = CF1001Collector(max_workers=2)
                    all_results = collector.collect_urls(test_mode=False)
                    collector.save_results()
                    print("🎉 전체 수집 완료!")
            else:
                print("❌ 성공률이 낮습니다")
        else:
            print("❌ 테스트 실패")
            
        collector.save_results()
        
    except KeyboardInterrupt:
        print("\n⏹️ 중단됨")
        collector.save_results()


if __name__ == "__main__":
    main()
