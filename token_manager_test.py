"""
cF1001 토큰 추출 테스트 시스템
기존 파일들을 절대 건드리지 않고 안전하게 테스트
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import time

class TokenExtractorTest:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        self.test_results = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'extraction_methods': {},
            'token_tests': {},
            'summary': {}
        }
    
    def test_all_extraction_methods(self):
        """모든 토큰 추출 방법 테스트"""
        print("🔬 1단계: 토큰 추출 테스트 시작")
        print("=" * 50)
        
        # 방법 A: JavaScript 파싱
        print("\n📄 방법 A: JavaScript에서 encparam 추출...")
        token_a = self.extract_from_javascript()
        
        # 방법 B: 네트워크 요청 모니터링
        print("\n🌐 방법 B: 네트워크 요청에서 encparam 추출...")
        token_b = self.extract_from_network_requests()
        
        # 방법 C: HTML 숨겨진 필드에서 추출
        print("\n🔍 방법 C: HTML 숨겨진 필드에서 추출...")
        token_c = self.extract_from_hidden_fields()
        
        # 결과 정리
        tokens = {
            'method_a_javascript': token_a,
            'method_b_network': token_b, 
            'method_c_hidden_fields': token_c
        }
        
        # 성공한 토큰들 확인
        valid_tokens = {}
        for method, token in tokens.items():
            if token:
                print(f"✅ {method}: {token[:20]}...")
                valid_tokens[method] = token
            else:
                print(f"❌ {method}: 추출 실패")
        
        self.test_results['extraction_methods'] = tokens
        
        print(f"\n📊 토큰 추출 결과: {len(valid_tokens)}/3 개 방법 성공")
        return valid_tokens
    
    def extract_from_javascript(self):
        """방법 A: JavaScript 코드에서 encparam 추출 - 개선된 버전"""
        try:
            url = "https://finance.naver.com/item/main.naver?code=005930"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            print(f"    📄 페이지 크기: {len(response.text):,} 바이트")
            
            # 더 많은 패턴으로 검색
            patterns = [
                r'encparam["\']?\s*[:=]\s*["\']([^"\']+)["\']',
                r'cF1001\.aspx[^"\']*encparam=([^&"\']+)',
                r'encparam=([A-Za-z0-9+/=]+)',
                r'encParam["\']?\s*[:=]\s*["\']([^"\']+)["\']',  # 대소문자 다른 경우
                r'enc_param["\']?\s*[:=]\s*["\']([^"\']+)["\']', # 언더스코어 있는 경우
                r'token["\']?\s*[:=]\s*["\']([A-Za-z0-9+/=]{20,})["\']', # 일반적인 토큰 패턴
                r'param["\']?\s*[:=]\s*["\']([A-Za-z0-9+/=]{20,})["\']', # param 패턴
            ]
            
            # 먼저 cF1001이 언급되는지 확인
            if 'cF1001' in response.text:
                print("    💡 cF1001 발견! 토큰 검색 중...")
                cf1001_sections = []
                # cF1001 주변 텍스트 추출
                for match in re.finditer(r'cF1001[^"\n]{0,200}', response.text):
                    cf1001_sections.append(match.group())
                    print(f"    🔍 cF1001 섹션: {match.group()[:100]}...")
                
                # 각 섹션에서 토큰 패턴 찾기
                for section in cf1001_sections:
                    for pattern in patterns:
                        matches = re.findall(pattern, section)
                        if matches:
                            token = matches[0]
                            if len(token) > 15:
                                print(f"    💡 패턴 발견: {pattern}")
                                print(f"    🎯 토큰: {token[:30]}...")
                                return token
            else:
                print("    ⚠️ cF1001이 페이지에서 발견되지 않음")
            
            # 전체 텍스트에서 긴 Base64 같은 문자열 찾기
            long_strings = re.findall(r'[A-Za-z0-9+/=]{30,100}', response.text)
            if long_strings:
                print(f"    🔍 긴 문자열 {len(long_strings)}개 발견, 검증 중...")
                for i, string in enumerate(long_strings[:5]):  # 처음 5개만 테스트
                    print(f"    🧪 문자열 {i+1}: {string[:30]}...")
                    # 이 문자열이 토큰인지 간단 테스트
                    if self.quick_token_test(string):
                        print(f"    ✅ 유효한 토큰 발견!")
                        return string
            
            print("    ❌ JavaScript에서 유효한 토큰을 찾을 수 없음")
            return None
            
        except Exception as e:
            print(f"    ❌ JavaScript 추출 오류: {e}")
            return None
    
    def quick_token_test(self, token):
        """토큰 후보의 빠른 유효성 테스트"""
        try:
            url = "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx"
            params = {
                'cmp_cd': '005930',
                'fin_typ': '0',
                'freq_typ': 'A',
                'encparam': token,
                'id': 'hiddenfinGubun'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=5)
            
            # 간단한 성공 여부만 확인
            if response.status_code == 200 and len(response.text) > 500:
                return True
            return False
            
        except:
            return False
    
    def extract_from_network_requests(self):
        """방법 B: 실제 네트워크 요청에서 encparam 추출 - 개선된 버전"""
        try:
            url = "https://finance.naver.com/item/main.naver?code=005930"
            
            # 세션 사용해서 쿠키 유지
            session = requests.Session()
            session.headers.update(self.headers)
            
            # 메인 페이지 먼저 방문
            response = session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            print(f"    🌐 응답 크기: {len(response.text):,} 바이트")
            
            # 모든 script 태그에서 Ajax 요청 패턴 찾기
            scripts = soup.find_all('script')
            print(f"    📜 스크립트 태그 {len(scripts)}개 발견")
            
            ajax_patterns = [
                r'\$\.ajax\([^}]+cF1001[^}]+\)',
                r'jindo\.\$Ajax\([^}]+cF1001[^}]+\)',
                r'XMLHttpRequest[^}]+cF1001[^}]+',
                r'fetch\([^}]+cF1001[^}]+\)',
            ]
            
            for i, script in enumerate(scripts):
                if script.string and 'cF1001' in script.string:
                    print(f"    💡 스크립트 {i}에서 cF1001 발견!")
                    script_text = script.string
                    
                    # Ajax 요청 패턴 찾기
                    for pattern in ajax_patterns:
                        ajax_matches = re.findall(pattern, script_text, re.DOTALL)
                        for ajax_call in ajax_matches:
                            print(f"    🔍 Ajax 호출: {ajax_call[:100]}...")
                            
                            # 이 Ajax 호출에서 encparam 추출
                            param_patterns = [
                                r'encparam["\']?\s*[:=]\s*["\']([^"\']+)',
                                r'encParam["\']?\s*[:=]\s*["\']([^"\']+)',
                                r'"encparam":\s*"([^"]+)"',
                                r'&encparam=([^&"\']+)',
                            ]
                            
                            for param_pattern in param_patterns:
                                param_matches = re.findall(param_pattern, ajax_call)
                                if param_matches:
                                    token = param_matches[0]
                                    if len(token) > 15:
                                        print(f"    🎯 토큰 발견: {token[:30]}...")
                                        return token
            
            print("    ❌ 네트워크 요청에서 유효한 토큰을 찾을 수 없음")
            return None
            
        except Exception as e:
            print(f"    ❌ 네트워크 요청 추출 오류: {e}")
            return None
    
    def extract_from_hidden_fields(self):
        """방법 C: HTML의 숨겨진 입력 필드에서 추출 - 개선된 버전"""
        try:
            url = "https://finance.naver.com/item/main.naver?code=005930"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            print(f"    🔍 HTML 크기: {len(response.text):,} 바이트")
            
            # 1. 모든 input 필드 확인 (hidden이 아닌 것도 포함)
            all_inputs = soup.find_all('input')
            print(f"    📝 input 필드 {len(all_inputs)}개 발견")
            
            for input_field in all_inputs:
                name = input_field.get('name', '').lower()
                value = input_field.get('value', '')
                input_type = input_field.get('type', '')
                
                # encparam 관련 이름들 확인
                if any(keyword in name for keyword in ['encparam', 'enc_param', 'token', 'param']):
                    if len(value) > 15:
                        print(f"    💡 input 필드 발견: {name} = {value[:30]}...")
                        return value
            
            # 2. 모든 data- 속성 확인
            all_elements = soup.find_all(attrs={"data-encparam": True}) + \
                          soup.find_all(attrs={"data-token": True}) + \
                          soup.find_all(attrs={"data-param": True})
            
            for elem in all_elements:
                for attr_name, attr_value in elem.attrs.items():
                    if 'param' in attr_name.lower() or 'token' in attr_name.lower():
                        if len(str(attr_value)) > 15:
                            print(f"    💡 data 속성 발견: {attr_name} = {str(attr_value)[:30]}...")
                            return str(attr_value)
            
            # 3. JavaScript 변수 선언에서 찾기
            script_vars = re.findall(r'var\s+(\w*[Pp]aram\w*|.*[Tt]oken.*)\s*=\s*["\']([^"\']{15,})["\']', response.text)
            if script_vars:
                print(f"    💡 JavaScript 변수 {len(script_vars)}개 발견")
                for var_name, var_value in script_vars:
                    print(f"    🔍 변수: {var_name} = {var_value[:30]}...")
                    if self.quick_token_test(var_value):
                        print(f"    ✅ 유효한 토큰!")
                        return var_value
            
            # 4. 메타 태그 확인
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                name = meta.get('name', '').lower()
                content = meta.get('content', '')
                
                if any(keyword in name for keyword in ['token', 'param', 'enc']):
                    if len(content) > 15:
                        print(f"    💡 메타 태그 발견: {name} = {content[:30]}...")
                        return content
            
            print("    ❌ 숨겨진 필드에서 유효한 토큰을 찾을 수 없음")
            return None
            
        except Exception as e:
            print(f"    ❌ 숨겨진 필드 추출 오류: {e}")
            return None
    
    def test_token_validity(self, tokens):
        """추출한 토큰들의 유효성 테스트"""
        print("\n🧪 토큰 유효성 테스트 시작")
        print("=" * 50)
        
        test_stocks = ["005930", "000660"]  # 삼성전자, SK하이닉스
        valid_tokens = {}
        
        for method, token in tokens.items():
            print(f"\n🔍 {method} 토큰 테스트...")
            success_count = 0
            
            for stock_code in test_stocks:
                if self.test_single_request(stock_code, token):
                    success_count += 1
                    print(f"    ✅ {stock_code}: 성공")
                else:
                    print(f"    ❌ {stock_code}: 실패")
            
            success_rate = (success_count / len(test_stocks)) * 100
            print(f"    📊 성공률: {success_rate:.1f}%")
            
            self.test_results['token_tests'][method] = {
                'token': token,
                'success_rate': success_rate,
                'test_details': {}
            }
            
            if success_rate >= 50:  # 50% 이상 성공하면 유효한 토큰
                valid_tokens[method] = token
        
        return valid_tokens
    
    def test_single_request(self, stock_code, token):
        """단일 종목으로 토큰 테스트"""
        try:
            url = "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx"
            params = {
                'cmp_cd': stock_code,
                'fin_typ': '0',
                'freq_typ': 'A', 
                'encparam': token,
                'id': 'hiddenfinGubun'
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            # 응답이 JSON이고 유효한 데이터인지 확인
            if response.status_code == 200:
                try:
                    data = response.json()
                    # 재무데이터가 있는지 확인
                    if 'result' in data or '매출액' in response.text:
                        return True
                except:
                    # JSON이 아니어도 재무데이터가 있으면 성공
                    if len(response.text) > 1000 and '매출액' in response.text:
                        return True
            
            return False
            
        except Exception as e:
            return False
    
    def save_test_results(self, valid_tokens):
        """테스트 결과 저장"""
        self.test_results['summary'] = {
            'total_methods_tested': 3,
            'successful_extractions': len([t for t in self.test_results['extraction_methods'].values() if t]),
            'valid_tokens': len(valid_tokens),
            'best_token': None,
            'recommendation': None
        }
        
        # 가장 좋은 토큰 선택
        if valid_tokens:
            best_method = max(
                self.test_results['token_tests'].keys(),
                key=lambda x: self.test_results['token_tests'][x]['success_rate']
            )
            self.test_results['summary']['best_token'] = {
                'method': best_method,
                'token': valid_tokens[best_method],
                'success_rate': self.test_results['token_tests'][best_method]['success_rate']
            }
            
            if self.test_results['token_tests'][best_method]['success_rate'] >= 80:
                self.test_results['summary']['recommendation'] = "PROCEED_TO_STEP2"
            else:
                self.test_results['summary']['recommendation'] = "NEED_IMPROVEMENT"
        else:
            self.test_results['summary']['recommendation'] = "ALL_FAILED"
        
        # 결과 파일로 저장
        with open('token_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 테스트 결과를 'token_test_results.json'에 저장했습니다.")
    
    def print_summary(self, valid_tokens):
        """테스트 결과 요약 출력"""
        print("\n" + "=" * 60)
        print("🎯 1단계 테스트 결과 요약")
        print("=" * 60)
        
        # 추출 성공률
        extraction_success = len([t for t in self.test_results['extraction_methods'].values() if t])
        print(f"📄 토큰 추출: {extraction_success}/3 개 방법 성공")
        
        # 유효성 테스트 결과
        if valid_tokens:
            print(f"✅ 유효한 토큰: {len(valid_tokens)}개 발견")
            
            best_method = max(
                self.test_results['token_tests'].keys(),
                key=lambda x: self.test_results['token_tests'][x]['success_rate']
            )
            best_rate = self.test_results['token_tests'][best_method]['success_rate']
            print(f"🏆 최고 성능: {best_method} ({best_rate:.1f}%)")
            
            # 다음 단계 안내
            if best_rate >= 80:
                print(f"\n🚀 2단계 진행 가능! 우수한 토큰 발견!")
                print(f"다음 명령어: python token_manager_test.py step2")
            else:
                print(f"\n⚠️ 토큰 품질 개선 필요. 추가 방법 시도 권장.")
        else:
            print(f"❌ 유효한 토큰을 찾지 못했습니다.")
            print(f"🔧 다른 추출 방법 개발 필요")
        
        print(f"\n📊 상세 결과: token_test_results.json 파일 확인")

def run_step1_test():
    """1단계 테스트 실행"""
    print("🔬 cF1001 토큰 추출 및 검증 테스트")
    print("⚠️  기존 파일들은 절대 수정하지 않습니다!")
    print("=" * 60)
    
    tester = TokenExtractorTest()
    
    # 1. 토큰 추출 테스트
    extracted_tokens = tester.test_all_extraction_methods()
    
    if not extracted_tokens:
        print("\n❌ 모든 추출 방법 실패. 테스트 중단.")
        return False
    
    # 2. 토큰 유효성 테스트  
    valid_tokens = tester.test_token_validity(extracted_tokens)
    
    # 3. 결과 저장 및 요약
    tester.save_test_results(valid_tokens)
    tester.print_summary(valid_tokens)
    
    return len(valid_tokens) > 0

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "step2":
        print("🚀 2단계는 1단계 성공 후 별도 안내드리겠습니다!")
    else:
        success = run_step1_test()
        
        if success:
            print(f"\n✅ 1단계 성공! 계속 진행하시겠어요?")
        else:
            print(f"\n❌ 1단계 실패. 문제 해결 후 재시도 필요.")
