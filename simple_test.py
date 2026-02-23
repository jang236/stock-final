import requests
import json
import re
import os
from pprint import pprint


class SimpleFinancialTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'X-Requested-With': 'XMLHttpRequest'
        })

    def extract_tokens(self, stock_code):
        """실시간으로 encparam과 id 추출"""
        try:
            main_url = f"https://navercomp.wisereport.co.kr/company/c1010001.aspx?cmp_cd={stock_code}"
            print(f"📍 메인 페이지 접속: {main_url}")
            
            response = self.session.get(main_url, timeout=15)
            print(f"   상태코드: {response.status_code}")
            
            if response.status_code != 200:
                return None, None
            
            # encparam 추출
            encparam_patterns = [
                r"encparam['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
                r"encParam['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]"
            ]
            
            encparam = None
            for pattern in encparam_patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                if matches:
                    encparam = matches[0]
                    break
            
            # 특별한 ID 패턴 찾기 (Base64 스타일의 긴 문자열)
            id_patterns = [
                r'id[\'"]?\s*[:=]\s*[\'"]([A-Za-z0-9+/=]{8,})[\'"]',
                r'[\'"]([A-Za-z0-9+/=]{10,})[\'"]'
            ]
            
            id_value = None
            for pattern in id_patterns:
                matches = re.findall(pattern, response.text)
                for match in matches:
                    # 일반적인 HTML ID 제외, Base64 스타일만
                    if (len(match) >= 8 and 
                        match not in ['Form1', 'contentWrap', 'all_contentWrap'] and
                        any(c in match for c in '+=/')):  # Base64 특징
                        id_value = match
                        break
                if id_value:
                    break
            
            print(f"   encparam: {encparam[:20]}... (발견)" if encparam else "   encparam: 없음")
            print(f"   id: {id_value}" if id_value else "   id: 없음")
            
            return encparam, id_value
            
        except Exception as e:
            print(f"   ❌ 토큰 추출 실패: {e}")
            return None, None

    def test_cf1001_api(self, stock_code, encparam, id_value=None):
        """cF1001 API 테스트"""
        print(f"\n🔬 cF1001 API 테스트")
        
        base_url = "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx"
        
        # 여러 파라미터 조합
        test_cases = [
            {
                'name': 'fin_typ=0, freq_typ=A (with id)',
                'params': {
                    'cmp_cd': stock_code,
                    'fin_typ': '0',
                    'freq_typ': 'A',
                    'encparam': encparam,
                    'id': id_value
                }
            } if id_value else None,
            {
                'name': 'fin_typ=0, freq_typ=A (no id)',
                'params': {
                    'cmp_cd': stock_code,
                    'fin_typ': '0',
                    'freq_typ': 'A',
                    'encparam': encparam
                }
            },
            {
                'name': 'fin_typ=4, freq_typ=A (with id)',
                'params': {
                    'cmp_cd': stock_code,
                    'fin_typ': '4',
                    'freq_typ': 'A',
                    'encparam': encparam,
                    'id': id_value
                }
            } if id_value else None,
            {
                'name': 'fin_typ=4, freq_typ=A (no id)',
                'params': {
                    'cmp_cd': stock_code,
                    'fin_typ': '4',
                    'freq_typ': 'A',
                    'encparam': encparam
                }
            }
        ]
        
        # None 제거
        test_cases = [case for case in test_cases if case is not None]
        
        # Referer 설정
        self.session.headers['Referer'] = f'https://navercomp.wisereport.co.kr/company/c1010001.aspx?cmp_cd={stock_code}'
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n   테스트 {i}: {case['name']}")
            print(f"   파라미터: {case['params']}")
            
            try:
                response = self.session.get(base_url, params=case['params'], timeout=10)
                print(f"   응답 코드: {response.status_code}")
                print(f"   응답 길이: {len(response.text)}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"   ✅ JSON 파싱 성공")
                        
                        # 데이터 타입 확인
                        if isinstance(data, list):
                            print(f"   📊 리스트 형태 데이터: {len(data)}개 항목")
                            
                            # 재무 항목들 찾기
                            financial_keywords = ['매출액', '영업이익', '당기순이익', '자산총계', 'ROE', 'PER']
                            found_items = []
                            
                            for item in data[:50]:  # 처음 50개만 확인
                                if isinstance(item, str):
                                    for keyword in financial_keywords:
                                        if keyword in item:
                                            found_items.append(item)
                            
                            if found_items:
                                print(f"   🎯 재무 항목 발견: {found_items}")
                                print(f"   🎉 성공! 이것이 재무데이터입니다!")
                                
                                # 전체 데이터 저장
                                with open(f'financial_data_{stock_code}.json', 'w', encoding='utf-8') as f:
                                    json.dump(data, f, ensure_ascii=False, indent=2)
                                print(f"   💾 전체 데이터 저장: financial_data_{stock_code}.json")
                                
                                return data
                            else:
                                print(f"   ❌ 재무 항목 없음")
                                
                        elif isinstance(data, dict):
                            print(f"   📊 딕셔너리 형태: {list(data.keys())}")
                            if 'dt' in data:
                                print(f"   dt 내용: {type(data['dt'])}")
                        else:
                            print(f"   📊 데이터 타입: {type(data)}")
                            
                    except json.JSONDecodeError:
                        print(f"   ❌ JSON 파싱 실패")
                        print(f"   응답 내용: {response.text[:200]}...")
                else:
                    print(f"   ❌ HTTP 오류")
                    
            except Exception as e:
                print(f"   ❌ 요청 실패: {e}")
        
        return None

    def analyze_financial_data(self, data, stock_code):
        """재무 데이터 분석"""
        print(f"\n📊 {stock_code} 재무 데이터 분석")
        
        if not isinstance(data, list):
            print("❌ 리스트 형태가 아님")
            return
        
        print(f"📏 전체 데이터 길이: {len(data)}")
        
        # 34개 목표 항목
        target_items = [
            "매출액", "영업이익", "영업이익(발표기준)", "세전계속사업이익", "당기순이익",
            "당기순이익(지배)", "당기순이익(비지배)", "자산총계", "부채총계", "자본총계",
            "자본총계(지배)", "자본총계(비지배)", "자본금", "영업활동현금흐름", "투자활동현금흐름",
            "재무활동현금흐름", "CAPEX", "FCF", "이자발생부채", "영업이익률", "순이익률",
            "ROE(%)", "ROA(%)", "부채비율", "자본유보율", "EPS(원)", "PER(배)", "BPS(원)",
            "PBR(배)", "현금DPS(원)", "현금배당수익률", "현금배당성향(%)", "발행주식수(보통주)"
        ]
        
        found_items = {}
        
        for i, item in enumerate(data):
            if isinstance(item, str) and item in target_items:
                # 해당 항목의 값들 찾기 (다음 몇 개 요소)
                values = []
                for j in range(i+1, min(i+10, len(data))):
                    if isinstance(data[j], str) and data[j] in target_items:
                        break
                    values.append(data[j])
                found_items[item] = values
        
        print(f"\n🎯 발견된 재무 항목: {len(found_items)}개")
        for item, values in found_items.items():
            print(f"   ✅ {item}: {values[:3]}...")  # 처음 3개 값만
        
        # 결과 저장
        result = {
            "stock_code": stock_code,
            "total_data_length": len(data),
            "found_financial_items": len(found_items),
            "financial_data": found_items
        }
        
        with open(f'analyzed_financial_{stock_code}.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"💾 분석 결과 저장: analyzed_financial_{stock_code}.json")
        
        return result


def main():
    print("🧪 간단한 재무데이터 테스트 시작\n")
    
    tester = SimpleFinancialTester()
    
    # 테스트할 종목들
    test_stocks = [
        ('네이버', '035420'),
        ('삼성전자', '005930'),
        ('이노와이어리스', '073490')
    ]
    
    for company_name, stock_code in test_stocks:
        print(f"{'='*80}")
        print(f"🏢 {company_name}({stock_code}) 테스트")
        print(f"{'='*80}")
        
        # 1단계: 토큰 추출
        encparam, id_value = tester.extract_tokens(stock_code)
        
        if encparam:
            # 2단계: API 테스트
            financial_data = tester.test_cf1001_api(stock_code, encparam, id_value)
            
            if financial_data:
                # 3단계: 데이터 분석
                tester.analyze_financial_data(financial_data, stock_code)
                print(f"🎉 {company_name} 성공!")
            else:
                print(f"❌ {company_name} 재무데이터 가져오기 실패")
        else:
            print(f"❌ {company_name} 토큰 추출 실패")
        
        print(f"\n⏳ 다음 종목까지 3초 대기...")
        import time
        time.sleep(3)
    
    print(f"\n🎉 전체 테스트 완료!")


if __name__ == "__main__":
    main()
