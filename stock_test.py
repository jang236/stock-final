# 🚀 초간단 네이버 주식 API 테스트
# 복사해서 Python에 붙여넣고 실행하세요!

import requests

# 🎯 종목코드만 바꿔서 테스트하세요
stock_code = '137080'  # 나래나노텍

# API 호출
url = f"https://finance.naver.com/item/item_right_ajax.naver?type=recent&code={stock_code}&page=1"

try:
    response = requests.get(url)
    data = response.json()
    
    if data['item_list']:
        stock = data['item_list'][0]
        
        print("✅ 성공!")
        print(f"종목명: {stock['itemname']}")
        print(f"현재가: {stock['now_val']}원") 
        print(f"전일대비: {stock['change_val']}원")
        print(f"등락률: {stock['change_rate']}%")
        
    else:
        print("❌ 데이터 없음")
        
except Exception as e:
    print(f"❌ 오류: {e}")
    print("💡 requests 라이브러리 설치 필요할 수 있습니다.")
    print("   터미널에서: pip install requests")
