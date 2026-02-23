import json
import requests
import os
from pprint import pprint


class FinancialDataTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        })

    def load_success_urls(self):
        """성공한 cF1001 URL들 로드"""
        try:
            file_path = os.path.join("company_codes", "cf1001_urls_success.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ {len(data)}개 성공 URL 로드")
            return data
        except Exception as e:
            print(f"❌ 파일 로드 실패: {e}")
            return {}

    def get_financial_data(self, company_name, url_data):
        """실제 재무 데이터 가져오기"""
        try:
            url = url_data['cF1001_url']
            stock_code = url_data['code']
            
            # Referer 헤더 설정
            self.session.headers['Referer'] = f'https://navercomp.wisereport.co.kr/company/c1010001.aspx?cmp_cd={stock_code}'
            
            print(f"\n📊 {company_name}({stock_code}) 재무 데이터 요청...")
            print(f"🔗 URL: {url}")
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ 응답 성공 - 상태코드: {response.status_code}")
                    
                    # 응답 구조 분석
                    self.analyze_response_structure(company_name, data)
                    return data
                    
                except json.JSONDecodeError as e:
                    print(f"❌ JSON 파싱 실패: {e}")
                    print(f"📝 응답 내용: {response.text[:200]}...")
                    return None
            else:
                print(f"❌ HTTP 오류: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ 요청 실패: {e}")
            return None

    def analyze_response_structure(self, company_name, data):
        """응답 데이터 구조 분석"""
        print(f"\n🔍 {company_name} 응답 구조 분석:")
        
        if isinstance(data, dict):
            print(f"📋 최상위 키들: {list(data.keys())}")
            
            # 주요 키 분석
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    print(f"📊 {key}: 리스트 (길이: {len(value)})")
                    if isinstance(value[0], dict):
                        print(f"   └─ 첫 번째 항목 키들: {list(value[0].keys())}")
                elif isinstance(value, dict):
                    print(f"📊 {key}: 객체 (키 개수: {len(value)})")
                    print(f"   └─ 하위 키들: {list(value.keys())}")
                else:
                    print(f"📊 {key}: {type(value).__name__} - {str(value)[:50]}...")
        else:
            print(f"📊 응답 타입: {type(data).__name__}")
            print(f"📊 응답 내용: {str(data)[:200]}...")

    def find_financial_items(self, data):
        """34개 재무 항목 찾기"""
        target_items = [
            "매출액", "영업이익", "당기순이익", "자산총계", "부채총계", 
            "자본총계", "영업활동현금흐름", "ROE", "PER", "EPS", "BPS"
        ]
        
        found_items = {}
        
        def search_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # 키 이름에서 재무 항목 찾기
                    for target in target_items:
                        if target in str(key) or target in str(value):
                            found_items[target] = {
                                'path': current_path,
                                'value': value
                            }
                    
                    search_recursive(value, current_path)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    search_recursive(item, f"{path}[{i}]")
        
        search_recursive(data)
        return found_items

    def test_all_companies(self):
        """모든 성공한 회사들 테스트"""
        success_urls = self.load_success_urls()
        
        if not success_urls:
            print("❌ 테스트할 URL이 없습니다.")
            return
        
        print(f"🧪 {len(success_urls)}개 회사 재무 데이터 테스트 시작\n")
        
        results = {}
        
        for i, (company_name, url_data) in enumerate(success_urls.items(), 1):
            print(f"\n{'='*60}")
            print(f"🏢 [{i}/{len(success_urls)}] {company_name}")
            print(f"{'='*60}")
            
            financial_data = self.get_financial_data(company_name, url_data)
            
            if financial_data:
                # 재무 항목 찾기
                found_items = self.find_financial_items(financial_data)
                
                results[company_name] = {
                    'success': True,
                    'found_financial_items': len(found_items),
                    'financial_items': found_items,
                    'raw_data_keys': list(financial_data.keys()) if isinstance(financial_data, dict) else []
                }
                
                print(f"🎯 발견된 재무 항목: {len(found_items)}개")
                if found_items:
                    for item, info in found_items.items():
                        print(f"   ✅ {item}: {info['path']}")
            else:
                results[company_name] = {
                    'success': False,
                    'error': '데이터 가져오기 실패'
                }
            
            # 요청 간격 (서버 부하 방지)
            if i < len(success_urls):
                print("⏳ 2초 대기...")
                import time
                time.sleep(2)
        
        # 최종 결과 요약
        self.print_summary(results)
        
        # 결과 저장
        self.save_test_results(results)
        
        return results

    def print_summary(self, results):
        """테스트 결과 요약 출력"""
        print(f"\n{'='*60}")
        print("📊 재무 데이터 테스트 결과 요약")
        print(f"{'='*60}")
        
        total = len(results)
        success = sum(1 for r in results.values() if r['success'])
        fail = total - success
        
        print(f"🎯 전체 테스트: {total}개")
        print(f"✅ 성공: {success}개 ({success/total*100:.1f}%)")
        print(f"❌ 실패: {fail}개 ({fail/total*100:.1f}%)")
        
        if success > 0:
            # 재무 항목 발견 통계
            financial_counts = [r['found_financial_items'] for r in results.values() if r['success']]
            avg_items = sum(financial_counts) / len(financial_counts)
            print(f"📈 평균 발견 재무 항목: {avg_items:.1f}개")
            
            # 가장 많이 발견된 회사
            best_company = max(
                [(name, data) for name, data in results.items() if data['success']], 
                key=lambda x: x[1]['found_financial_items']
            )
            print(f"🏆 최다 발견: {best_company[0]} ({best_company[1]['found_financial_items']}개)")

    def save_test_results(self, results):
        """테스트 결과 저장"""
        file_path = os.path.join("company_codes", "financial_test_results.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"💾 테스트 결과 저장: {file_path}")


def main():
    print("🧪 재무 데이터 테스트 시작")
    
    tester = FinancialDataTester()
    results = tester.test_all_companies()
    
    print("\n🎉 테스트 완료!")


if __name__ == "__main__":
    main()
