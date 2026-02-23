import requests
import re
from bs4 import BeautifulSoup


def debug_single_company(stock_code="005930", company_name="삼성전자"):
    """단일 기업 토큰 추출 디버그"""

    print(f"🔧 {company_name}({stock_code}) 디버그 시작")

    session = requests.Session()
    session.headers.update({
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    # 재무 페이지 접속
    coinfo_url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"
    print(f"🌐 접속 URL: {coinfo_url}")

    try:
        response = session.get(coinfo_url, timeout=15)
        response.raise_for_status()
        content = response.text

        print(f"📄 페이지 크기: {len(content)} 문자")
        print(f"📊 응답 상태: {response.status_code}")

        # 1. 전체 cF1001 URL 찾기
        print("\n🔍 1. 완성된 cF1001 URL 검색:")
        cf1001_urls = re.findall(
            r'https://navercomp\.wisereport\.co\.kr[^"\'>\s]*cF1001[^"\'>\s]*',
            content)
        for i, url in enumerate(cf1001_urls):
            print(f"   URL {i+1}: {url}")

        # 2. encparam 후보들 찾기
        print("\n🔍 2. encparam 후보 검색:")
        encparam_patterns = [
            (r'encparam["\s]*[:=]["\s]*["\']([A-Za-z0-9+/=]+)["\']',
             'JavaScript 변수'),
            (r'"encparam"["\s]*:["\s]*"([A-Za-z0-9+/=]+)"', 'JSON 객체'),
            (r'encparam=([A-Za-z0-9+/=]+)', 'URL 파라미터'),
            (r'[A-Za-z0-9+/=]{30,}', 'Base64 후보 (30자 이상)'),
        ]

        encparam_found = None
        for pattern, desc in encparam_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            print(f"   {desc}: {len(matches)}개 발견")
            for j, match in enumerate(matches[:3]):  # 처음 3개만 출력
                print(
                    f"      {j+1}. {match[:50]}{'...' if len(match) > 50 else ''}"
                )
                if not encparam_found and len(match) >= 20:
                    encparam_found = match

        # 3. id 후보들 찾기
        print("\n🔍 3. id 후보 검색:")
        id_patterns = [
            (r'["\s]id["\s]*[:=]["\s]*"([A-Za-z0-9+/=]+)"', 'JavaScript 변수'),
            (r'"id"["\s]*:["\s]*"([A-Za-z0-9+/=]+)"', 'JSON 객체'),
            (r'&id=([A-Za-z0-9+/=]+)', 'URL 파라미터'),
        ]

        id_found = None
        for pattern, desc in id_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            print(f"   {desc}: {len(matches)}개 발견")
            for j, match in enumerate(matches[:3]):
                print(f"      {j+1}. {match}")
                if not id_found:
                    id_found = match

        # 4. wisereport 관련 문자열 찾기
        print("\n🔍 4. wisereport 관련 문자열:")
        wisereport_matches = re.findall(r'wisereport[^"\'>\s]{0,100}', content,
                                        re.IGNORECASE)
        for i, match in enumerate(wisereport_matches[:5]):
            print(f"   {i+1}. {match}")

        # 5. 수동 URL 조합 시도
        if encparam_found and id_found:
            print(f"\n🔧 5. 수동 URL 조합 시도:")
            test_url = f"https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd={stock_code}&fin_typ=0&freq_typ=A&encparam={encparam_found}&id={id_found}"
            print(f"   테스트 URL: {test_url[:100]}...")

            # URL 유효성 테스트
            try:
                test_response = session.get(test_url, timeout=10)
                print(f"   응답 상태: {test_response.status_code}")
                print(f"   응답 크기: {len(test_response.content)} bytes")
                if test_response.status_code == 200 and len(
                        test_response.content) > 100:
                    print("   ✅ URL 유효함!")
                    return test_url
                else:
                    print("   ❌ URL 무효함")
            except Exception as e:
                print(f"   ❌ URL 테스트 실패: {e}")

        # 6. 페이지 소스 일부 저장
        debug_file = f"debug_{stock_code}.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n💾 전체 페이지 소스 저장: {debug_file}")

        return None

    except Exception as e:
        print(f"❌ 디버그 실패: {e}")
        return None


def main():
    """메인 디버그 함수"""
    print("🚀 토큰 추출 디버그 시작")

    # 테스트할 종목들
    test_stocks = [
        ("005930", "삼성전자"),
        ("035420", "NAVER"),
        ("000660", "SK하이닉스"),
    ]

    for stock_code, company_name in test_stocks:
        print("\n" + "=" * 80)
        result = debug_single_company(stock_code, company_name)
        if result:
            print(f"🎉 {company_name} 성공: {result[:80]}...")
            break
        print("\n")


if __name__ == "__main__":
    main()
