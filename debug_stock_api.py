# 🔍 네이버 주식 API 디버깅 코드
import requests
import json

def debug_stock_api(stock_code='137080'):
    """API 응답을 자세히 분석하는 디버깅 함수"""
    
    print(f"🔍 디버깅 시작: {stock_code}")
    print("="*50)
    
    # URL 구성
    url = f"https://finance.naver.com/item/item_right_ajax.naver?type=recent&code={stock_code}&page=1"
    print(f"📡 요청 URL: {url}")
    
    # 헤더 추가 (브라우저처럼 보이게)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': f'https://finance.naver.com/item/main.naver?code={stock_code}',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    }
    
    try:
        # API 호출
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"📊 응답 상태코드: {response.status_code}")
        print(f"📊 응답 헤더: {dict(response.headers)}")
        print(f"📊 응답 크기: {len(response.text)} bytes")
        
        # 응답 내용 확인
        print("\n📋 응답 내용 (처음 500자):")
        print("-" * 30)
        print(response.text[:500])
        print("-" * 30)
        
        if response.status_code == 200:
            try:
                # JSON 파싱 시도
                data = response.json()
                print(f"\n✅ JSON 파싱 성공!")
                print(f"📊 응답 데이터 구조:")
                
                # 응답 데이터 구조 분석
                for key, value in data.items():
                    if isinstance(value, list):
                        print(f"  {key}: 리스트 (길이: {len(value)})")
                        if len(value) > 0:
                            print(f"    첫 번째 항목 타입: {type(value[0])}")
                    else:
                        print(f"  {key}: {type(value).__name__} = {value}")
                
                # item_list 상세 확인
                if 'item_list' in data:
                    print(f"\n🎯 item_list 분석:")
                    print(f"  길이: {len(data['item_list'])}")
                    
                    if len(data['item_list']) > 0:
                        print(f"  첫 번째 항목:")
                        first_item = data['item_list'][0]
                        for k, v in first_item.items():
                            print(f"    {k}: {v}")
                    else:
                        print("  ❌ item_list가 비어있음!")
                        
                        # 다른 키들 확인
                        print("\n🔍 다른 키들 확인:")
                        for key in data.keys():
                            if key != 'item_list':
                                print(f"  {key}: {data[key]}")
                
                return data
                
            except json.JSONDecodeError as e:
                print(f"\n❌ JSON 파싱 실패: {e}")
                print("응답이 JSON 형식이 아닐 수 있습니다.")
                
                # HTML 응답인지 확인
                if response.text.strip().startswith('<'):
                    print("📄 HTML 응답을 받았습니다. 네이버가 차단했을 가능성이 높습니다.")
                    
                return None
                
        else:
            print(f"\n❌ HTTP 오류: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 네트워크 오류: {e}")
        return None
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        return None

def test_different_approaches():
    """다양한 접근 방법 테스트"""
    
    print("\n🚀 다양한 방법으로 테스트해보기")
    print("="*50)
    
    stock_code = '137080'
    
    # 방법 1: 기본 요청
    print("\n1️⃣ 기본 요청 테스트:")
    debug_stock_api(stock_code)
    
    # 방법 2: 다른 종목으로 테스트
    print("\n2️⃣ 다른 종목(삼성전자) 테스트:")
    debug_stock_api('005930')
    
    # 방법 3: 세션 사용
    print("\n3️⃣ 세션 사용 테스트:")
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.naver.com/',
    })
    
    try:
        url = f"https://finance.naver.com/item/item_right_ajax.naver?type=recent&code={stock_code}&page=1"
        response = session.get(url)
        print(f"세션 응답 상태: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"세션 응답 데이터 키: {list(data.keys())}")
    except Exception as e:
        print(f"세션 테스트 실패: {e}")

if __name__ == "__main__":
    # 상세 디버깅 실행
    debug_stock_api()
    
    # 다양한 접근법 테스트
    test_different_approaches()
