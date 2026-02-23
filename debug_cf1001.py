import requests
import re
import json
import time


class CF1001Debugger:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def extract_all_params(self, html_text):
        """페이지에서 모든 가능한 파라미터 추출"""
        patterns = {
            'encparam': [
                r"encparam['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
                r"encParam['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]"
            ],
            'id': [
                r"id['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
                r"ID['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]"
            ],
            'flag': [
                r"flag['\"]?\s*[:=]\s*['\"]?(\d+)['\"]?",
                r"FLAG['\"]?\s*[:=]\s*['\"]?(\d+)['\"]?"
            ],
            'grp_cd': [
                r"grp_cd['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
                r"grpCd['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]"
            ]
        }
        
        found_params = {}
        
        for param_name, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, html_text, re.IGNORECASE)
                if matches:
                    found_params[param_name] = matches
                    print(f"✅ {param_name}: {matches}")
        
        return found_params

    def analyze_javascript_calls(self, html_text):
        """JavaScript에서 실제 호출 방식 분석"""
        print("\n🔍 JavaScript 호출 패턴 분석:")
        
        # AJAX 호출 패턴들
        ajax_patterns = [
            r"\$\.getJSON\(['\"](/[^'\"]+)['\"][^}]*{([^}]+)}",
            r"\$\.ajax\(\s*{[^}]*url\s*:\s*['\"](/[^'\"]+)['\"][^}]*data\s*:\s*{([^}]+)}",
            r"fetch\(['\"](/[^'\"]+)['\"]"
        ]
        
        for i, pattern in enumerate(ajax_patterns):
            matches = re.findall(pattern, html_text, re.DOTALL)
            if matches:
                print(f"📋 패턴 {i+1}: {matches}")
        
        # cF1001 관련 호출 찾기
        cf1001_pattern = r"cF1001[^;]*"
        cf1001_calls = re.findall(cf1001_pattern, html_text)
        if cf1001_calls:
            print(f"🎯 cF1001 관련 호출:")
            for call in cf1001_calls[:3]:  # 상위 3개만
                print(f"   {call}")

    def test_different_approaches(self, stock_code):
        """다양한 접근 방식 테스트"""
        print(f"\n🧪 {stock_code} 다양한 방식 테스트")
        
        # 1단계: 메인 페이지 접속
        main_url = f"https://navercomp.wisereport.co.kr/company/c1010001.aspx?cmp_cd={stock_code}"
        print(f"📍 메인 페이지 접속: {main_url}")
        
        response = self.session.get(main_url)
        print(f"   상태코드: {response.status_code}")
        
        if response.status_code != 200:
            print("❌ 메인 페이지 접속 실패")
            return
        
        # 2단계: 파라미터 추출
        print("\n📋 파라미터 추출:")
        params = self.extract_all_params(response.text)
        
        # 3단계: JavaScript 분석
        self.analyze_javascript_calls(response.text)
        
        # 4단계: 다양한 조합으로 테스트
        if 'encparam' in params and params['encparam']:
            encparam = params['encparam'][0]
            print(f"\n🔑 사용할 encparam: {encparam}")
            
            test_combinations = [
                # flag, grp_cd 조합들
                {'flag': '1', 'grp_cd': '01'},
                {'flag': '1', 'grp_cd': '03'},
                {'flag': '2', 'grp_cd': '01'},
                {'flag': '2', 'grp_cd': '03'},
                {'flag': '4', 'grp_cd': '01'},
                {'flag': '4', 'grp_cd': '03'},
                # id 파라미터 포함 시도
                {'flag': '4', 'grp_cd': '03', 'id': 'test'},
            ]
            
            # id 파라미터가 있으면 추가
            if 'id' in params and params['id']:
                test_combinations.append({
                    'flag': '4', 
                    'grp_cd': '03', 
                    'id': params['id'][0]
                })
            
            for i, combo in enumerate(test_combinations):
                print(f"\n🔬 테스트 {i+1}: {combo}")
                self.test_cf1001_call(stock_code, encparam, combo)
                time.sleep(1)
        else:
            print("❌ encparam을 찾을 수 없습니다")

    def test_cf1001_call(self, stock_code, encparam, params_combo):
        """실제 cF1001 호출 테스트"""
        try:
            # AJAX 헤더 설정
            ajax_headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'https://navercomp.wisereport.co.kr/company/c1010001.aspx?cmp_cd={stock_code}',
                'Cache-Control': 'no-cache'
            }
            
            # 기존 헤더 백업 및 업데이트
            original_headers = self.session.headers.copy()
            self.session.headers.update(ajax_headers)
            
            # 파라미터 구성
            params = {
                'cmp_cd': stock_code,
                'encparam': encparam,
                **params_combo
            }
            
            # URL 구성
            url = "https://navercomp.wisereport.co.kr/company/ajax/cF1001.aspx"
            
            print(f"   📡 요청: {url}")
            print(f"   📋 파라미터: {params}")
            
            # 요청 실행
            response = self.session.get(url, params=params, timeout=10)
            
            print(f"   📊 응답 코드: {response.status_code}")
            print(f"   📏 응답 길이: {len(response.text)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   ✅ JSON 파싱 성공")
                    
                    # 응답 내용 분석
                    if isinstance(data, dict):
                        if 'dt' in data:
                            if data['dt'] is None:
                                print(f"   ⚠️  dt가 null")
                            elif isinstance(data['dt'], list):
                                print(f"   📋 dt 리스트 길이: {len(data['dt'])}")
                                if len(data['dt']) > 0 and isinstance(data['dt'][0], dict):
                                    keys = list(data['dt'][0].keys())
                                    print(f"   🔑 dt[0] 키들: {keys[:5]}...")
                                    
                                    # 재무 관련 키 찾기
                                    financial_keywords = ['매출', '영업', '순이익', '자산', '부채', 'SALES', 'PROFIT', 'ASSET']
                                    found_financial = []
                                    for key in keys:
                                        for keyword in financial_keywords:
                                            if keyword in str(key).upper():
                                                found_financial.append(key)
                                    
                                    if found_financial:
                                        print(f"   🎯 재무 관련 키: {found_financial}")
                                    else:
                                        print(f"   ❌ 재무 관련 키 없음")
                        print(f"   📄 전체 구조: {list(data.keys())}")
                    
                    # 성공적인 응답인지 판단
                    if self.is_valid_financial_response(data):
                        print(f"   🎉 유효한 재무 데이터!")
                        return True, data
                    else:
                        print(f"   ❌ 유효하지 않은 응답")
                        
                except json.JSONDecodeError:
                    print(f"   ❌ JSON 파싱 실패")
                    print(f"   📝 응답 내용: {response.text[:200]}...")
            else:
                print(f"   ❌ HTTP 오류")
            
            # 헤더 복원
            self.session.headers = original_headers
            
        except Exception as e:
            print(f"   ❌ 요청 실패: {e}")
        
        return False, None

    def is_valid_financial_response(self, data):
        """유효한 재무 데이터 응답인지 확인"""
        if not isinstance(data, dict) or 'dt' not in data:
            return False
        
        if data['dt'] is None:
            return False
        
        if isinstance(data['dt'], list) and len(data['dt']) > 0:
            if isinstance(data['dt'][0], dict):
                keys = list(data['dt'][0].keys())
                # 의미있는 키가 있는지 확인
                if len(keys) > 5:  # 최소한 5개 이상의 키
                    return True
        
        return False


def main():
    print("🔍 cF1001 디버깅 시작")
    
    debugger = CF1001Debugger()
    
    # 테스트할 종목들
    test_stocks = ['073490', '131970', '272110']  # 성공했던 종목들
    
    for stock_code in test_stocks:
        print(f"\n{'='*80}")
        print(f"🏢 {stock_code} 종목 분석")
        print(f"{'='*80}")
        
        debugger.test_different_approaches(stock_code)
        
        print(f"\n⏳ 다음 종목까지 3초 대기...")
        time.sleep(3)
    
    print("\n🎉 디버깅 완료!")


if __name__ == "__main__":
    main()
