"""
기존 수집된 토큰의 유효성 테스트
"""

import requests
import json
from datetime import datetime

def test_existing_token():
    """기존 토큰이 아직 유효한지 테스트"""
    print("🔬 기존 토큰 유효성 테스트")
    print("=" * 50)
    
    # 기존 토큰
    existing_token = "dTZzbEdXQmlLMEtmb0dGZlV6QXRmUT09"
    collected_date = "2025-06-15 02:28:40"
    
    print(f"📅 토큰 수집일: {collected_date}")
    print(f"🔑 토큰: {existing_token}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    # 테스트할 종목들
    test_stocks = [
        ("060310", "3S"),
        ("005930", "삼성전자"), 
        ("000660", "SK하이닉스")
    ]
    
    results = {}
    
    for stock_code, company_name in test_stocks:
        print(f"\n🧪 {company_name} ({stock_code}) 테스트...")
        
        try:
            url = "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx"
            params = {
                'cmp_cd': stock_code,
                'fin_typ': '0',
                'freq_typ': 'A',
                'encparam': existing_token,
                'id': 'hiddenfinGubun'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            print(f"    📡 응답 코드: {response.status_code}")
            print(f"    📄 응답 크기: {len(response.text):,} 바이트")
            
            # 성공 여부 판단
            if response.status_code == 200:
                content = response.text
                
                # 재무데이터 키워드 확인
                financial_keywords = ['매출액', '영업이익', '당기순이익', 'result']
                found_keywords = [kw for kw in financial_keywords if kw in content]
                
                if found_keywords:
                    print(f"    ✅ 성공! 재무데이터 발견: {found_keywords}")
                    results[company_name] = {
                        'status': 'success',
                        'response_size': len(content),
                        'keywords_found': found_keywords
                    }
                    
                    # 샘플 데이터 출력
                    if len(content) > 1000:
                        print(f"    📊 데이터 미리보기: {content[:200]}...")
                else:
                    print(f"    ❌ 실패: 재무데이터 키워드 없음")
                    results[company_name] = {
                        'status': 'failed',
                        'reason': 'no_financial_data',
                        'content_preview': content[:100]
                    }
            else:
                print(f"    ❌ 실패: HTTP {response.status_code}")
                results[company_name] = {
                    'status': 'failed', 
                    'reason': f'http_{response.status_code}'
                }
                
        except Exception as e:
            print(f"    ❌ 오류: {e}")
            results[company_name] = {
                'status': 'error',
                'error': str(e)
            }
    
    # 결과 요약
    print("\n" + "=" * 50)
    print("📊 기존 토큰 테스트 결과")
    print("=" * 50)
    
    success_count = len([r for r in results.values() if r['status'] == 'success'])
    total_count = len(results)
    success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
    
    print(f"✅ 성공: {success_count}/{total_count} ({success_rate:.1f}%)")
    
    for company, result in results.items():
        status_emoji = "✅" if result['status'] == 'success' else "❌"
        print(f"   {status_emoji} {company}: {result['status']}")
    
    # 결과에 따른 다음 단계 안내
    if success_rate >= 50:
        print(f"\n🎉 기존 토큰이 아직 유효합니다!")
        print(f"💡 전략: 이 토큰으로 모든 URL 업데이트")
        return existing_token, True
    elif success_rate > 0:
        print(f"\n⚠️ 기존 토큰이 부분적으로 유효합니다")
        print(f"💡 전략: 새 토큰 찾기 또는 토큰 갱신 필요")
        return existing_token, False
    else:
        print(f"\n❌ 기존 토큰이 완전히 만료되었습니다")
        print(f"💡 전략: 새로운 토큰 추출 방법 필요")
        return None, False

def extract_token_from_similar_page():
    """재무정보 페이지에서 토큰 추출 시도"""
    print(f"\n🔍 재무정보 페이지에서 토큰 찾기...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    # 재무정보 관련 페이지들 시도
    pages_to_try = [
        "https://finance.naver.com/item/coinfo.naver?code=005930",
        "https://finance.naver.com/item/main.naver?code=005930",
        "https://comp.fnguide.com/SVO2/ASP/SVD_Corp.asp?pGB=1&gicode=A005930"
    ]
    
    import re
    
    for page_url in pages_to_try:
        try:
            print(f"    🌐 페이지 확인: {page_url}")
            response = requests.get(page_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                content = response.text
                
                # cF1001 또는 encparam 찾기
                if 'cF1001' in content:
                    print(f"    💡 cF1001 발견!")
                    
                    # encparam 패턴 찾기
                    patterns = [
                        r'encparam=([A-Za-z0-9+/=]+)',
                        r'encparam["\']?\s*[:=]\s*["\']([^"\']+)',
                    ]
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            new_token = matches[0]
                            print(f"    🎯 새 토큰 발견: {new_token}")
                            return new_token
                
                # 긴 Base64 문자열 찾기
                base64_candidates = re.findall(r'[A-Za-z0-9+/]{20,}={0,2}', content)
                if base64_candidates:
                    print(f"    🔍 Base64 후보 {len(base64_candidates)}개 발견")
                    for candidate in base64_candidates[:3]:
                        if len(candidate) >= 20:
                            print(f"    🧪 후보 테스트: {candidate[:20]}...")
                            # 간단 테스트 (여기서는 생략)
                            
        except Exception as e:
            print(f"    ❌ 페이지 오류: {e}")
    
    return None

if __name__ == "__main__":
    # 기존 토큰 테스트
    token, is_valid = test_existing_token()
    
    # 기존 토큰이 실패하면 다른 페이지에서 찾기
    if not is_valid:
        new_token = extract_token_from_similar_page()
        if new_token:
            print(f"\n🎉 새로운 토큰 발견: {new_token}")
        else:
            print(f"\n❌ 새로운 토큰을 찾지 못했습니다")
