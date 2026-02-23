import requests
import re
import json
import time
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup


class NaverPageAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })

    def analyze_naver_page(self, stock_code):
        """네이버 종목 페이지 완전 분석"""
        print(f"🔍 네이버 페이지 분석 시작: {stock_code}")
        
        # 1단계: 메인 페이지 접속
        main_url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"
        print(f"📍 메인 페이지 접속: {main_url}")
        
        try:
            response = self.session.get(main_url, timeout=15)
            print(f"   상태코드: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   ❌ 메인 페이지 접속 실패")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 2단계: iframe 찾기
            print(f"\n🔍 iframe 분석")
            iframes = soup.find_all('iframe')
            financial_iframe = None
            
            for iframe in iframes:
                src = iframe.get('src', '')
                if 'finsum' in src or 'financial' in src or 'c1010001' in src:
                    financial_iframe = src
                    print(f"   ✅ 재무 iframe 발견: {src}")
                    break
            
            if not financial_iframe:
                print(f"   ❌ 재무 iframe을 찾을 수 없음")
                # 모든 iframe 출력
                print(f"   발견된 iframe들:")
                for i, iframe in enumerate(iframes):
                    print(f"     {i+1}. {iframe.get('src', 'src 없음')}")
                return None
            
            # 3단계: iframe 페이지 분석
            if not financial_iframe.startswith('http'):
                if financial_iframe.startswith('//'):
                    financial_iframe = 'https:' + financial_iframe
                elif financial_iframe.startswith('/'):
                    financial_iframe = 'https://finance.naver.com' + financial_iframe
                else:
                    financial_iframe = 'https://finance.naver.com/' + financial_iframe
            
            print(f"\n🔍 iframe 페이지 분석: {financial_iframe}")
            
            iframe_response = self.session.get(financial_iframe, timeout=15)
            print(f"   상태코드: {iframe_response.status_code}")
            
            if iframe_response.status_code != 200:
                print(f"   ❌ iframe 페이지 접속 실패")
                return None
            
            # 4단계: JavaScript 분석
            print(f"\n🔍 JavaScript 분석")
            iframe_soup = BeautifulSoup(iframe_response.text, 'html.parser')
            
            # 스크립트 태그에서 cF1001 관련 코드 찾기
            scripts = iframe_soup.find_all('script')
            cf1001_patterns = []
            
            for script in scripts:
                if script.string:
                    script_content = script.string
                    
                    # cF1001 관련 패턴 찾기
                    cf1001_matches = re.findall(r'cF1001[^;]*', script_content, re.MULTILINE | re.DOTALL)
                    if cf1001_matches:
                        cf1001_patterns.extend(cf1001_matches)
                    
                    # AJAX 호출 패턴 찾기
                    ajax_patterns = [
                        r'\$\.getJSON\([^}]*cF1001[^}]*\}[^)]*\)',
                        r'\$\.ajax\([^}]*cF1001[^}]*\}[^)]*\)',
                        r'fetch\([^}]*cF1001[^}]*\)'
                    ]
                    
                    for pattern in ajax_patterns:
                        matches = re.findall(pattern, script_content, re.MULTILINE | re.DOTALL)
                        if matches:
                            cf1001_patterns.extend(matches)
            
            if cf1001_patterns:
                print(f"   ✅ cF1001 관련 코드 발견:")
                for i, pattern in enumerate(cf1001_patterns[:3], 1):  # 상위 3개만
                    clean_pattern = ' '.join(pattern.split())
                    print(f"     {i}. {clean_pattern[:100]}...")
            
            # 5단계: 파라미터 추출
            print(f"\n🔍 파라미터 추출")
            extracted_params = self.extract_parameters_from_page(iframe_response.text, stock_code)
            
            # 6단계: 실제 API 호출 시도
            if extracted_params:
                print(f"\n🔍 실제 API 호출 시도")
                api_result = self.test_extracted_api(extracted_params, stock_code)
                return {
                    'main_url': main_url,
                    'iframe_url': financial_iframe,
                    'cf1001_patterns': cf1001_patterns,
                    'extracted_params': extracted_params,
                    'api_result': api_result
                }
            
            return {
                'main_url': main_url,
                'iframe_url': financial_iframe,
                'cf1001_patterns': cf1001_patterns,
                'extracted_params': None,
                'api_result': None
            }
            
        except Exception as e:
            print(f"   ❌ 분석 실패: {e}")
            return None

    def extract_parameters_from_page(self, page_content, stock_code):
        """페이지에서 API 파라미터 추출"""
        print(f"   📋 파라미터 추출 시작")
        
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
                print(f"     ✅ encparam: {matches[0][:20]}...")
                break
        
        # id 추출 (Base64 스타일의 특별한 ID)
        id_patterns = [
            r'[\'"]([A-Za-z0-9+/=]{8,})[\'"]'
        ]
        
        for pattern in id_patterns:
            matches = re.findall(pattern, page_content)
            for match in matches:
                # Base64 스타일이면서 일반적인 HTML ID가 아닌 것
                if (len(match) >= 8 and 
                    any(c in match for c in '+/=') and
                    match not in ['Form1', 'contentWrap', 'text/javascript']):
                    params['id'] = match
                    print(f"     ✅ id: {match}")
                    break
            if 'id' in params:
                break
        
        # fin_typ, freq_typ 찾기
        fin_typ_pattern = r"fin_typ['\"]?\s*[:=]\s*['\"]?([^'\">\s]+)['\"]?"
        freq_typ_pattern = r"freq_typ['\"]?\s*[:=]\s*['\"]?([^'\">\s]+)['\"]?"
        
        fin_typ_matches = re.findall(fin_typ_pattern, page_content, re.IGNORECASE)
        if fin_typ_matches:
            params['fin_typ'] = fin_typ_matches[0]
            print(f"     ✅ fin_typ: {fin_typ_matches[0]}")
        
        freq_typ_matches = re.findall(freq_typ_pattern, page_content, re.IGNORECASE)
        if freq_typ_matches:
            params['freq_typ'] = freq_typ_matches[0]
            print(f"     ✅ freq_typ: {freq_typ_matches[0]}")
        
        # 기본값 설정
        if 'fin_typ' not in params:
            params['fin_typ'] = '0'
            print(f"     ⚠️  fin_typ 기본값 사용: 0")
        
        if 'freq_typ' not in params:
            params['freq_typ'] = 'A'
            print(f"     ⚠️  freq_typ 기본값 사용: A")
        
        params['cmp_cd'] = stock_code
        
        return params if 'encparam' in params else None

    def test_extracted_api(self, params, stock_code):
        """추출된 파라미터로 실제 API 테스트"""
        print(f"   🧪 API 테스트 시작")
        
        # 여러 URL 패턴 시도
        base_urls = [
            "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx",
            "https://navercomp.wisereport.co.kr/company/ajax/cF1001.aspx",
            "https://companyinfo.stock.naver.com/v1/company/ajax/cF1001.aspx"
        ]
        
        # AJAX 헤더 설정
        ajax_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f'https://finance.naver.com/item/coinfo.naver?code={stock_code}',
            'Cache-Control': 'no-cache'
        }
        
        original_headers = self.session.headers.copy()
        self.session.headers.update(ajax_headers)
        
        for base_url in base_urls:
            print(f"     테스트 URL: {base_url}")
            print(f"     파라미터: {params}")
            
            try:
                response = self.session.get(base_url, params=params, timeout=10)
                print(f"     응답 코드: {response.status_code}")
                print(f"     응답 길이: {len(response.text)}")
                
                if response.status_code == 200:
                    # JSON 파싱 시도
                    try:
                        data = response.json()
                        print(f"     ✅ JSON 파싱 성공")
                        
                        # 재무 데이터인지 확인
                        if self.is_financial_data(data):
                            print(f"     🎉 재무 데이터 발견!")
                            
                            # 결과 저장
                            with open(f'financial_success_{stock_code}.json', 'w', encoding='utf-8') as f:
                                json.dump({
                                    'url': base_url,
                                    'params': params,
                                    'data': data
                                }, f, ensure_ascii=False, indent=2)
                            
                            self.session.headers = original_headers
                            return {
                                'success': True,
                                'url': base_url,
                                'params': params,
                                'data_preview': str(data)[:500],
                                'full_data_file': f'financial_success_{stock_code}.json'
                            }
                        else:
                            print(f"     ❌ 재무 데이터가 아님")
                            
                    except json.JSONDecodeError:
                        print(f"     ❌ JSON 파싱 실패")
                        print(f"     응답 내용: {response.text[:200]}...")
                else:
                    print(f"     ❌ HTTP 오류")
                    
            except Exception as e:
                print(f"     ❌ 요청 실패: {e}")
        
        self.session.headers = original_headers
        return {'success': False, 'message': '모든 URL 패턴 실패'}

    def is_financial_data(self, data):
        """재무 데이터인지 확인"""
        if isinstance(data, list) and len(data) > 30:
            # 리스트에서 재무 항목 찾기
            financial_keywords = ['매출액', '영업이익', '당기순이익', '자산총계', 'ROE', 'PER']
            text_data = str(data)
            return any(keyword in text_data for keyword in financial_keywords)
        
        if isinstance(data, dict) and 'dt' in data:
            return data['dt'] is not None and len(str(data['dt'])) > 100
        
        return False


def main():
    print("🔍 네이버 페이지 완전 분석기 시작\n")
    
    analyzer = NaverPageAnalyzer()
    
    # 테스트할 종목들
    test_stocks = [
        '009140',  # 경인전자 (사용자가 제공한 종목)
        '005930',  # 삼성전자 (검증용)
        '035420'   # 네이버 (검증용)
    ]
    
    results = {}
    
    for stock_code in test_stocks:
        print(f"{'='*80}")
        print(f"🏢 종목 {stock_code} 완전 분석")
        print(f"{'='*80}")
        
        result = analyzer.analyze_naver_page(stock_code)
        results[stock_code] = result
        
        if result and result.get('api_result', {}).get('success'):
            print(f"🎉 {stock_code} 성공!")
        else:
            print(f"❌ {stock_code} 실패")
        
        print(f"\n⏳ 다음 종목까지 5초 대기...")
        time.sleep(5)
    
    # 전체 결과 저장
    with open('naver_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n🎉 전체 분석 완료!")
    print(f"💾 결과 저장: naver_analysis_results.json")
    
    # 성공한 패턴 요약
    successful_patterns = []
    for stock_code, result in results.items():
        if result and result.get('api_result', {}).get('success'):
            successful_patterns.append({
                'stock_code': stock_code,
                'url': result['api_result']['url'],
                'params': result['api_result']['params']
            })
    
    if successful_patterns:
        print(f"\n🎯 성공한 패턴들:")
        for pattern in successful_patterns:
            print(f"   {pattern['stock_code']}: {pattern['url']}")
            print(f"     파라미터: {pattern['params']}")


if __name__ == "__main__":
    main()
