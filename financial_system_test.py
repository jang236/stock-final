#!/usr/bin/env python3
"""
새 URL 데이터베이스 연결 재무정보 시스템 테스트
5개 기업 샘플로 재무정보 추출 테스트
"""

import json
import requests
import random
import re
from datetime import datetime
import time


class FinancialSystemTest:
    def __init__(self, new_db_folder="company_codes_20250617"):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://finance.naver.com/'
        })
        
        self.new_db_folder = new_db_folder
        self.database_file = f"{new_db_folder}/cf1001_urls_database.json"
        self.companies_file = f"{new_db_folder}/stock_companies.json"

    def load_new_database(self):
        """새 URL 데이터베이스 로드"""
        try:
            with open(self.database_file, 'r', encoding='utf-8') as f:
                database = json.load(f)
            print(f"✅ 새 URL 데이터베이스 로드 완료: {len(database)}개")
            return database
        except Exception as e:
            print(f"❌ 새 URL 데이터베이스 로드 실패: {e}")
            return {}

    def load_companies_info(self):
        """기업 정보 로드"""
        try:
            with open(self.companies_file, 'r', encoding='utf-8') as f:
                companies = json.load(f)
            print(f"✅ 기업 정보 로드 완료: {len(companies)}개")
            return companies
        except Exception as e:
            print(f"❌ 기업 정보 로드 실패: {e}")
            return {}

    def select_test_companies(self, database, companies_info, count=5):
        """테스트용 기업 5개 선택 (대/중/소형주 골고루)"""
        
        # 성공적으로 URL이 있는 기업들만 필터링
        valid_companies = []
        for name, data in database.items():
            if isinstance(data, dict) and data.get('status') == 'success' and 'cF1001_url' in data:
                company_code = data.get('code', '')
                
                # 기업 정보가 있는지 확인
                if name in companies_info:
                    company_info = companies_info[name]
                    market_cap = company_info.get('시가총액', 0)
                    
                    # 시가총액 기준으로 분류
                    if market_cap > 10000000:  # 100억 이상
                        category = 'large'
                    elif market_cap > 1000000:  # 10억 이상
                        category = 'medium'
                    else:
                        category = 'small'
                    
                    valid_companies.append({
                        'name': name,
                        'code': company_code,
                        'url': data['cF1001_url'],
                        'collected_at': data.get('collected_at', 'Unknown'),
                        'category': category,
                        'market_cap': market_cap
                    })
        
        if len(valid_companies) < count:
            print(f"⚠️ 유효한 기업이 {len(valid_companies)}개만 있습니다.")
            count = len(valid_companies)
        
        # 카테고리별로 분류
        large_companies = [c for c in valid_companies if c['category'] == 'large']
        medium_companies = [c for c in valid_companies if c['category'] == 'medium']
        small_companies = [c for c in valid_companies if c['category'] == 'small']
        
        # 골고루 선택
        selected = []
        
        # 대형주 2개
        if large_companies:
            selected.extend(random.sample(large_companies, min(2, len(large_companies))))
        
        # 중형주 2개  
        if medium_companies and len(selected) < count:
            needed = min(2, count - len(selected))
            selected.extend(random.sample(medium_companies, min(needed, len(medium_companies))))
        
        # 소형주 1개
        if small_companies and len(selected) < count:
            needed = count - len(selected)
            selected.extend(random.sample(small_companies, min(needed, len(small_companies))))
        
        # 부족하면 남은 것 중에서 랜덤 선택
        if len(selected) < count:
            remaining = [c for c in valid_companies if c not in selected]
            needed = count - len(selected)
            selected.extend(random.sample(remaining, min(needed, len(remaining))))
        
        return selected[:count]

    def extract_financial_data(self, company_info):
        """개별 기업 재무정보 추출"""
        
        print(f"\n📊 재무정보 추출: {company_info['name']} ({company_info['code']})")
        print(f"🏷️ 분류: {company_info['category']}형주")
        print(f"💰 시가총액: {company_info['market_cap']:,}백만원")
        print(f"🔗 URL: {company_info['url'][:80]}...")
        print(f"📅 수집일: {company_info['collected_at']}")
        
        try:
            # cF1001 URL 요청
            response = self.session.get(company_info['url'], timeout=15)
            
            print(f"📡 응답 상태: {response.status_code}")
            print(f"📄 응답 크기: {len(response.content):,} 바이트")
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'data': None
                }
            
            if len(response.content) < 100:
                return {
                    'success': False, 
                    'error': '빈 응답 (토큰 만료 가능성)',
                    'data': None
                }
            
            # HTML 응답 파싱
            html_content = response.text
            
            # 재무 데이터 추출
            financial_data = self.parse_financial_html(html_content)
            
            if financial_data:
                print(f"✅ 재무정보 추출 성공!")
                for key, value in financial_data.items():
                    print(f"   {key}: {value}")
                
                return {
                    'success': True,
                    'error': None,
                    'data': financial_data,
                    'response_size': len(response.content),
                    'extraction_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                return {
                    'success': False,
                    'error': '재무정보 파싱 실패',
                    'data': None,
                    'response_size': len(response.content)
                }
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 네트워크 오류: {e}")
            return {
                'success': False,
                'error': f'네트워크 오류: {str(e)}',
                'data': None
            }
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return {
                'success': False,
                'error': f'처리 오류: {str(e)}',
                'data': None
            }

    def parse_financial_html(self, html_content):
        """HTML에서 재무정보 추출"""
        
        financial_data = {}
        
        # 주요 재무 키워드들
        financial_keywords = {
            '매출액': ['매출액', '총매출액', '영업수익'],
            '영업이익': ['영업이익', '영업손익'],
            '순이익': ['순이익', '당기순이익', '순손익'],
            '자산총계': ['자산총계', '총자산'],
            '부채총계': ['부채총계', '총부채'],
            '자본총계': ['자본총계', '총자본', '자본금']
        }
        
        try:
            # HTML 테이블에서 숫자 패턴 찾기
            for main_key, keywords in financial_keywords.items():
                for keyword in keywords:
                    # 키워드 다음에 나오는 숫자 패턴 찾기
                    pattern = f'{keyword}.*?([0-9,]+(?:\.[0-9]+)?)'
                    matches = re.findall(pattern, html_content, re.IGNORECASE)
                    
                    if matches:
                        # 가장 큰 숫자를 선택 (보통 연간 데이터)
                        numbers = []
                        for match in matches:
                            try:
                                # 쉼표 제거하고 숫자로 변환
                                num_str = match.replace(',', '')
                                if '.' in num_str:
                                    numbers.append(float(num_str))
                                else:
                                    numbers.append(int(num_str))
                            except:
                                continue
                        
                        if numbers:
                            # 가장 큰 값 선택 (연간 데이터일 가능성)
                            financial_data[main_key] = max(numbers)
                            break
            
            # 기본적인 재무 비율 계산
            if '매출액' in financial_data and '영업이익' in financial_data:
                if financial_data['매출액'] > 0:
                    financial_data['영업이익률'] = round(
                        (financial_data['영업이익'] / financial_data['매출액']) * 100, 2
                    )
            
            if '매출액' in financial_data and '순이익' in financial_data:
                if financial_data['매출액'] > 0:
                    financial_data['순이익률'] = round(
                        (financial_data['순이익'] / financial_data['매출액']) * 100, 2
                    )
            
            # 데이터가 있으면 반환, 없으면 None
            return financial_data if financial_data else None
            
        except Exception as e:
            print(f"❌ HTML 파싱 오류: {e}")
            return None

    def run_test(self):
        """전체 테스트 실행"""
        
        print("🧪 새 URL 데이터베이스 재무정보 시스템 테스트 시작")
        print("=" * 70)
        
        # 데이터 로드
        database = self.load_new_database()
        if not database:
            print("❌ 데이터베이스 로드 실패로 테스트를 중단합니다.")
            return
        
        companies_info = self.load_companies_info()
        if not companies_info:
            print("❌ 기업 정보 로드 실패로 테스트를 중단합니다.")
            return
        
        # 테스트 기업 선택
        print(f"\n🎯 테스트 기업 5개 선택 중...")
        test_companies = self.select_test_companies(database, companies_info, 5)
        
        if not test_companies:
            print("❌ 테스트할 기업을 찾을 수 없습니다.")
            return
        
        print(f"\n📋 선택된 테스트 기업들:")
        for i, company in enumerate(test_companies, 1):
            print(f"{i}. {company['name']} ({company['code']}) - {company['category']}형주")
        
        print("=" * 70)
        
        # 테스트 실행
        test_results = []
        successful_tests = 0
        
        for i, company in enumerate(test_companies, 1):
            print(f"\n[{i}/5] 테스트 진행...")
            
            result = self.extract_financial_data(company)
            result['company_info'] = company
            test_results.append(result)
            
            if result['success']:
                successful_tests += 1
                print(f"✅ 성공")
            else:
                print(f"❌ 실패: {result['error']}")
            
            # 테스트 간 딜레이
            if i < len(test_companies):
                print(f"⏰ 2초 대기...")
                time.sleep(2)
        
        # 결과 요약
        self.print_test_summary(test_results, successful_tests)
        
        # 상세 결과 저장
        self.save_test_results(test_results)

    def print_test_summary(self, test_results, successful_tests):
        """테스트 결과 요약 출력"""
        
        print(f"\n{'='*70}")
        print(f"📊 테스트 결과 요약")
        print(f"{'='*70}")
        
        total_tests = len(test_results)
        success_rate = (successful_tests / total_tests) * 100
        
        print(f"🎯 전체 테스트: {total_tests}개")
        print(f"✅ 성공: {successful_tests}개")
        print(f"❌ 실패: {total_tests - successful_tests}개")
        print(f"📈 성공률: {success_rate:.1f}%")
        
        # 성공한 테스트들의 상세 정보
        if successful_tests > 0:
            print(f"\n🎉 성공한 재무정보 추출:")
            print(f"-" * 70)
            
            for result in test_results:
                if result['success']:
                    company = result['company_info']
                    data = result['data']
                    
                    print(f"📊 {company['name']} ({company['category']}형주)")
                    print(f"   응답 크기: {result['response_size']:,} 바이트")
                    print(f"   추출 항목: {len(data)}개")
                    
                    # 주요 재무 데이터 표시
                    for key, value in list(data.items())[:3]:  # 처음 3개만
                        if '률' in key:
                            print(f"   {key}: {value}%")
                        else:
                            print(f"   {key}: {value:,}")
                    print()
        
        # 실패 분석
        failed_results = [r for r in test_results if not r['success']]
        if failed_results:
            print(f"❌ 실패 원인 분석:")
            error_types = {}
            for result in failed_results:
                error = result['error']
                error_types[error] = error_types.get(error, 0) + 1
            
            for error, count in error_types.items():
                print(f"   • {error}: {count}건")
        
        # 전체 평가
        print(f"\n🎯 전체 평가:")
        if success_rate >= 80:
            print(f"✅ 우수: 새 URL 데이터베이스가 재무정보 시스템과 잘 호환됩니다!")
        elif success_rate >= 60:
            print(f"⚠️ 양호: 일부 개선이 필요하지만 사용 가능합니다.")
        else:
            print(f"❌ 문제: 재무정보 추출에 문제가 있습니다. 추가 분석이 필요합니다.")

    def save_test_results(self, test_results):
        """테스트 결과를 JSON 파일로 저장"""
        
        output_file = f"financial_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(test_results, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n💾 테스트 결과 저장: {output_file}")
            print(f"   상세 결과는 파일에서 확인할 수 있습니다.")
            
        except Exception as e:
            print(f"❌ 결과 저장 실패: {e}")


def main():
    tester = FinancialSystemTest()
    tester.run_test()


if __name__ == "__main__":
    main()
