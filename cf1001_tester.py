import json
import time
import os
import requests
import re
import random


class CF1001URLTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
            'Connection': 'keep-alive'
        })

    def load_companies(self):
        """종목 정보 로드"""
        try:
            file_path = os.path.join("company_codes", "stock_companies.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                companies = json.load(f)
            print(f"✅ {len(companies)}개 전체 종목 로드 완료")
            return companies
        except Exception as e:
            print(f"❌ 종목 로드 실패: {e}")
            return {}

    def select_random_companies(self, companies, count=10):
        """랜덤하게 종목 선택"""
        company_items = list(companies.items())
        selected = random.sample(company_items, min(count, len(company_items)))
        return selected

    def extract_encparam(self, page_text):
        """페이지에서 encparam 추출"""
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
        """cF1001 URL 생성"""
        try:
            # 1단계: 메인 페이지 접속
            main_url = f"https://navercomp.wisereport.co.kr/company/c1010001.aspx?cmp_cd={stock_code}"
            response = self.session.get(main_url, timeout=10)
            
            if response.status_code != 200:
                return None, "메인 페이지 접속 실패"
            
            # 2단계: encparam 추출
            encparam = self.extract_encparam(response.text)
            if not encparam:
                return None, "encparam 추출 실패"
            
            # 3단계: cF1001 URL 생성
            url = f"https://navercomp.wisereport.co.kr/company/ajax/cF1001.aspx?flag=4&cmp_cd={stock_code}&grp_cd=03&encparam={encparam}"
            
            # 4단계: URL 유효성 간단 검증
            ajax_headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': main_url
            }
            
            old_headers = self.session.headers.copy()
            self.session.headers.update(ajax_headers)
            
            test_response = self.session.get(url, timeout=5)
            self.session.headers = old_headers
            
            if test_response.status_code == 200:
                return url, "성공"
            else:
                return url, f"검증 실패 (상태코드: {test_response.status_code})"
            
        except Exception as e:
            return None, f"오류: {str(e)}"

    def test_10_companies(self):
        """10개 종목 테스트"""
        print("🎯 10개 종목 cF1001 URL 테스터 시작\n")
        
        # 종목 로드
        companies = self.load_companies()
        if not companies:
            print("❌ 종목 데이터를 로드할 수 없습니다.")
            return
        
        # 랜덤 10개 선택
        selected_companies = self.select_random_companies(companies, 10)
        print(f"🎲 {len(selected_companies)}개 종목 랜덤 선택 완료\n")
        
        results = []
        success_count = 0
        
        print("=" * 80)
        print("📋 cF1001 URL 테스트 결과")
        print("=" * 80)
        
        for i, (company_name, company_info) in enumerate(selected_companies, 1):
            stock_code = company_info['code']
            
            print(f"\n{i:2d}. {company_name} ({stock_code})")
            print(f"    🔄 처리 중...")
            
            url, status = self.get_cf1001_url(company_name, stock_code)
            
            if url and "성공" in status:
                print(f"    ✅ {status}")
                print(f"    🔗 URL: {url}")
                success_count += 1
                
                results.append({
                    "company_name": company_name,
                    "stock_code": stock_code,
                    "url": url,
                    "status": "성공"
                })
            else:
                print(f"    ❌ {status}")
                print(f"    🔗 URL: {url if url else '생성 실패'}")
                
                results.append({
                    "company_name": company_name,
                    "stock_code": stock_code,
                    "url": url,
                    "status": status
                })
            
            # 요청 간격 (서버 부하 방지)
            if i < len(selected_companies):
                time.sleep(2)
        
        # 결과 요약
        print(f"\n" + "=" * 80)
        print(f"📊 테스트 완료 요약")
        print(f"=" * 80)
        print(f"🎯 전체: {len(selected_companies)}개")
        print(f"✅ 성공: {success_count}개 ({success_count/len(selected_companies)*100:.1f}%)")
        print(f"❌ 실패: {len(selected_companies)-success_count}개")
        
        # 성공한 URL들만 따로 출력
        if success_count > 0:
            print(f"\n🎉 성공한 URL 목록 (복사용):")
            print(f"-" * 80)
            
            for i, result in enumerate([r for r in results if r['status'] == '성공'], 1):
                print(f"{i}. {result['company_name']} ({result['stock_code']})")
                print(f"   {result['url']}")
                print()
        
        # 결과 파일 저장
        output_file = "cf1001_test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "test_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_tested": len(selected_companies),
                "success_count": success_count,
                "success_rate": f"{success_count/len(selected_companies)*100:.1f}%",
                "results": results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"💾 상세 결과 저장: {output_file}")
        
        return results


def main():
    tester = CF1001URLTester()
    results = tester.test_10_companies()


if __name__ == "__main__":
    main()
