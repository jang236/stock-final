import json
import time
import os
import requests
import re
import random
from datetime import datetime


class ImprovedCF1001Collector:
    def __init__(self):
        self.session = requests.Session()
        # 더 자연스러운 브라우저 헤더
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        self.results = {}
        self.failed_companies = []

    def load_companies(self):
        """종목 정보 로드"""
        try:
            file_path = os.path.join("company_codes", "stock_companies.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                companies = json.load(f)
            print(f"✅ {len(companies)}개 종목 로드 완료")
            return companies
        except Exception as e:
            print(f"❌ 종목 로드 실패: {e}")
            return {}

    def visit_main_page_first(self, stock_code):
        """메인 페이지 먼저 방문 (자연스러운 패턴)"""
        try:
            # 네이버 금융 메인 페이지 방문
            main_url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"
            print(f"   🌐 메인 페이지 방문: {stock_code}")
            
            response = self.session.get(main_url, timeout=15)
            
            if response.status_code == 200:
                print(f"   ✅ 메인 페이지 방문 성공")
                # 자연스러운 대기 (페이지 로딩 시뮬레이션)
                time.sleep(3)
                return True
            else:
                print(f"   ❌ 메인 페이지 방문 실패: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 메인 페이지 방문 오류: {e}")
            return False

    def get_wisereport_page(self, stock_code):
        """WiseReport 페이지 접속"""
        try:
            # WiseReport 페이지 (iframe 내용)
            wisereport_url = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={stock_code}"
            print(f"   📊 WiseReport 페이지 접속")
            
            # Referer 설정
            self.session.headers['Referer'] = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"
            
            response = self.session.get(wisereport_url, timeout=15)
            
            if response.status_code == 200:
                print(f"   ✅ WiseReport 페이지 접속 성공")
                return response.text
            else:
                print(f"   ❌ WiseReport 페이지 접속 실패: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ WiseReport 페이지 오류: {e}")
            return None

    def extract_parameters(self, page_content):
        """올바른 파라미터 추출"""
        params = {}
        
        # encparam 추출
        encparam_patterns = [
            r"encparam['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
            r"encParam['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]"
        ]
        
        for pattern in encparam_patterns:
            matches = re.findall(pattern, page_content, re.IGNORECASE)
            if matches:
                params['encparam'] = matches[0]
                print(f"   ✅ encparam 추출: {matches[0][:20]}...")
                break
        
        # id 추출 (올바른 Base64 형태)
        id_patterns = [
            r'[\'"]([A-Za-z0-9+/]{8,})[\'"]'
        ]
        
        for pattern in id_patterns:
            matches = re.findall(pattern, page_content)
            for match in matches:
                # Base64 스타일이면서 CSS/JS 관련이 아닌 것
                if (len(match) >= 8 and 
                    not any(word in match.lower() for word in ['css', 'javascript', 'form', 'content'])):
                    # 추가 검증: 실제 ID 패턴인지 확인
                    if any(c in match for c in '+=') or len(match) > 10:
                        params['id'] = match
                        print(f"   ✅ id 추출: {match}")
                        break
            if 'id' in params:
                break
        
        return params

    def build_cf1001_url(self, stock_code, params):
        """올바른 cF1001 URL 생성"""
        if 'encparam' not in params:
            return None
        
        # v2 경로 사용, fin_typ=0, freq_typ=A
        base_url = "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx"
        
        url_params = {
            'cmp_cd': stock_code,
            'fin_typ': '0',
            'freq_typ': 'A',
            'encparam': params['encparam']
        }
        
        # id가 있으면 추가
        if 'id' in params:
            url_params['id'] = params['id']
        
        # URL 조합
        param_str = '&'.join([f"{k}={v}" for k, v in url_params.items()])
        full_url = f"{base_url}?{param_str}"
        
        return full_url

    def test_cf1001_url(self, url, stock_code):
        """cF1001 URL 유효성 테스트"""
        try:
            # AJAX 헤더 설정
            ajax_headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={stock_code}',
                'Cache-Control': 'no-cache'
            }
            
            # 기존 헤더 백업
            original_headers = self.session.headers.copy()
            self.session.headers.update(ajax_headers)
            
            print(f"   🧪 URL 유효성 테스트")
            response = self.session.get(url, timeout=10)
            
            # 헤더 복원
            self.session.headers = original_headers
            
            print(f"   📊 응답 코드: {response.status_code}")
            print(f"   📏 응답 길이: {len(response.text)}")
            
            if response.status_code == 200:
                # HTML 오류 페이지 체크
                if "접속장애" in response.text or "<!DOCTYPE" in response.text:
                    print(f"   ❌ 접속 차단 또는 오류 페이지")
                    return False
                
                # JSON 파싱 시도
                try:
                    data = response.json()
                    print(f"   ✅ JSON 응답 확인")
                    
                    # 재무 데이터 간단 확인
                    if isinstance(data, list) and len(data) > 20:
                        financial_keywords = ['매출액', '영업이익', '당기순이익']
                        data_str = str(data)
                        if any(keyword in data_str for keyword in financial_keywords):
                            print(f"   🎉 재무 데이터 확인!")
                            return True
                    
                    print(f"   ⚠️  JSON이지만 재무 데이터 아님")
                    return True  # URL은 유효하지만 데이터가 다름
                    
                except json.JSONDecodeError:
                    print(f"   ❌ JSON 파싱 실패")
                    return False
            else:
                print(f"   ❌ HTTP 오류")
                return False
                
        except Exception as e:
            print(f"   ❌ 테스트 실패: {e}")
            return False

    def process_single_company(self, company_name, company_info):
        """단일 회사 처리 (매우 신중하게)"""
        stock_code = company_info['code']
        
        print(f"\n📍 처리 시작: {company_name} ({stock_code})")
        
        try:
            # 1단계: 메인 페이지 먼저 방문 (자연스러운 패턴)
            if not self.visit_main_page_first(stock_code):
                return None
            
            # 2단계: WiseReport 페이지 접속
            page_content = self.get_wisereport_page(stock_code)
            if not page_content:
                return None
            
            # 3단계: 파라미터 추출
            print(f"   🔍 파라미터 추출")
            params = self.extract_parameters(page_content)
            if not params or 'encparam' not in params:
                print(f"   ❌ 필수 파라미터 추출 실패")
                return None
            
            # 4단계: URL 생성
            cf1001_url = self.build_cf1001_url(stock_code, params)
            if not cf1001_url:
                print(f"   ❌ URL 생성 실패")
                return None
            
            print(f"   🔗 생성된 URL: {cf1001_url}")
            
            # 5단계: URL 유효성 테스트
            if self.test_cf1001_url(cf1001_url, stock_code):
                result = {
                    "code": stock_code,
                    "cF1001_url": cf1001_url,
                    "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "success",
                    "parameters": params
                }
                print(f"   ✅ {company_name} 성공!")
                return result
            else:
                print(f"   ❌ URL 테스트 실패")
                return None
                
        except Exception as e:
            print(f"   ❌ 처리 실패: {e}")
            return None

    def collect_carefully(self, test_count=5):
        """신중한 수집 (소규모 테스트)"""
        print(f"🚀 개선된 cF1001 collector 시작")
        print(f"📊 {test_count}개 종목 신중한 수집\n")
        
        companies = self.load_companies()
        if not companies:
            return
        
        # 랜덤 선택
        company_items = list(companies.items())
        selected = random.sample(company_items, min(test_count, len(company_items)))
        
        print(f"🎲 선택된 종목들:")
        for i, (name, info) in enumerate(selected, 1):
            print(f"   {i}. {name} ({info['code']})")
        
        print(f"\n⏰ 요청 간격: 10초 (서버 친화적)")
        print(f"{'='*80}")
        
        success_count = 0
        
        for i, (company_name, company_info) in enumerate(selected, 1):
            print(f"\n[{i}/{len(selected)}] 진행률: {i/len(selected)*100:.1f}%")
            
            result = self.process_single_company(company_name, company_info)
            
            if result:
                self.results[company_name] = result
                success_count += 1
            else:
                self.failed_companies.append(company_name)
            
            # 마지막이 아니면 10초 대기
            if i < len(selected):
                print(f"   ⏰ 다음 종목까지 10초 대기... (서버 부하 방지)")
                time.sleep(10)
        
        # 결과 요약
        print(f"\n{'='*80}")
        print(f"📊 수집 완료 요약")
        print(f"{'='*80}")
        print(f"🎯 전체: {len(selected)}개")
        print(f"✅ 성공: {success_count}개 ({success_count/len(selected)*100:.1f}%)")
        print(f"❌ 실패: {len(self.failed_companies)}개")
        
        # 성공한 URL들 출력
        if success_count > 0:
            print(f"\n🎉 성공한 URL 목록:")
            print(f"-" * 80)
            for i, (name, result) in enumerate(self.results.items(), 1):
                print(f"{i}. {name} ({result['code']})")
                print(f"   {result['cF1001_url']}")
                print()
        
        # 결과 저장
        self.save_results()

    def save_results(self):
        """결과 저장"""
        if self.results:
            file_path = "cf1001_urls_improved.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            print(f"💾 성공 결과 저장: {file_path}")
        
        if self.failed_companies:
            file_path = "cf1001_failed_improved.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.failed_companies, f, ensure_ascii=False, indent=2)
            print(f"📝 실패 목록 저장: {file_path}")


def main():
    collector = ImprovedCF1001Collector()
    
    # 5개 종목으로 신중한 테스트
    collector.collect_carefully(test_count=5)
    
    print(f"\n🏁 테스트 완료!")
    print(f"성공률이 높으면 더 많은 종목으로 확장 가능합니다.")


if __name__ == "__main__":
    main()
