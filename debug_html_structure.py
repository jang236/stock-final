import requests
from bs4 import BeautifulSoup
import re

def debug_naver_finance_structure(stock_code="000660"):
    """
    네이버 증권 페이지 HTML 구조 상세 분석
    정확한 데이터 위치 찾기
    """
    url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    print(f"🔍 {stock_code} 네이버 증권 HTML 구조 분석...")
    print("=" * 80)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 모든 숫자가 포함된 요소 찾기
        print("📊 1. 페이지 내 모든 큰 숫자들 (거래량 후보):")
        all_numbers = re.findall(r'[\d,]+', soup.get_text())
        large_numbers = [num for num in all_numbers if ',' in num and len(num.replace(',', '')) >= 6]
        
        for i, num in enumerate(large_numbers[:20]):  # 상위 20개만
            value = int(num.replace(',', ''))
            if 1000000 <= value <= 10000000:  # 100만 ~ 1000만 (거래량 추정 범위)
                print(f"  🎯 {num} ({value:,}) - 거래량 후보")
            else:
                print(f"     {num} ({value:,})")
        
        # 2. "거래량" 키워드 주변 HTML 구조 분석
        print(f"\n📊 2. '거래량' 키워드 주변 HTML 구조:")
        volume_keywords = soup.find_all(string=re.compile(r'거래량'))
        
        for i, keyword in enumerate(volume_keywords[:3]):
            print(f"\n  거래량 키워드 #{i+1}:")
            parent = keyword.parent
            if parent:
                print(f"    부모 태그: {parent.name} - {parent.get('class', 'no class')}")
                
                # 주변 형제 요소들 확인
                siblings = parent.find_next_siblings()[:5]
                for j, sibling in enumerate(siblings):
                    if sibling and sibling.name:
                        text = sibling.get_text(strip=True)
                        if text and re.search(r'[\d,]+', text):
                            print(f"    형제 #{j+1}: {sibling.name} - '{text}'")
                
                # 부모의 부모까지 확인
                grandparent = parent.parent
                if grandparent:
                    gp_text = grandparent.get_text(strip=True)
                    numbers = re.findall(r'[\d,]+', gp_text)
                    if numbers:
                        print(f"    조부모 숫자들: {numbers}")
        
        # 3. "52주" 키워드 주변 분석
        print(f"\n📊 3. '52주' 키워드 주변 HTML 구조:")
        week52_keywords = soup.find_all(string=re.compile(r'52주'))
        
        for i, keyword in enumerate(week52_keywords[:3]):
            print(f"\n  52주 키워드 #{i+1}: '{keyword.strip()}'")
            parent = keyword.parent
            if parent:
                # 전체 컨텍스트 확인
                container = parent.parent if parent.parent else parent
                container_text = container.get_text()
                
                # 52주 최고/최저 패턴 찾기
                high_low_pattern = re.search(r'52주.*?(\d[\d,]*)\s*.*?(\d[\d,]*)', container_text)
                if high_low_pattern:
                    num1, num2 = high_low_pattern.groups()
                    print(f"    발견된 숫자들: {num1}, {num2}")
                    
                    val1 = int(num1.replace(',', ''))
                    val2 = int(num2.replace(',', ''))
                    
                    if val1 > val2:
                        print(f"    📈 추정 최고가: {val1:,}, 📉 추정 최저가: {val2:,}")
                    else:
                        print(f"    📈 추정 최고가: {val2:,}, 📉 추정 최저가: {val1:,}")
        
        # 4. 테이블 구조 분석
        print(f"\n📊 4. 테이블 구조 분석:")
        tables = soup.find_all('table')
        
        for i, table in enumerate(tables[:5]):  # 상위 5개 테이블만
            table_text = table.get_text()
            if '거래량' in table_text or '52주' in table_text:
                print(f"\n  테이블 #{i+1}:")
                rows = table.find_all('tr')
                
                for j, row in enumerate(rows[:10]):  # 상위 10개 행만
                    row_text = row.get_text(strip=True)
                    if '거래량' in row_text or '52주' in row_text:
                        print(f"    행 #{j+1}: {row_text[:100]}...")
                        
                        cells = row.find_all(['td', 'th'])
                        for k, cell in enumerate(cells):
                            cell_text = cell.get_text(strip=True)
                            if re.search(r'[\d,]+', cell_text):
                                print(f"      셀 #{k+1}: '{cell_text}'")
        
        # 5. CSS 클래스별 분석
        print(f"\n📊 5. 주요 CSS 클래스별 숫자 분석:")
        
        important_classes = ['.blind', '.num', '.tah', '.center', 'td', 'span']
        
        for css_class in important_classes:
            elements = soup.select(css_class)
            numbers_found = []
            
            for elem in elements[:50]:  # 각 클래스당 50개까지만
                text = elem.get_text(strip=True)
                if re.match(r'^[\d,]+$', text) and ',' in text:
                    try:
                        value = int(text.replace(',', ''))
                        if 1000 <= value <= 10000000:  # 관심 범위
                            numbers_found.append((text, value))
                    except:
                        pass
            
            if numbers_found:
                print(f"\n  {css_class} 클래스에서 발견된 숫자들:")
                for text, value in numbers_found[:10]:  # 상위 10개만
                    print(f"    {text} ({value:,})")
        
        print(f"\n✅ HTML 구조 분석 완료!")
        
    except Exception as e:
        print(f"❌ 분석 실패: {e}")

if __name__ == "__main__":
    # SK하이닉스 HTML 구조 분석
    debug_naver_finance_structure("000660")
    
    print("\n" + "="*80)
    print("🔧 다음 단계:")
    print("1. 위 분석 결과에서 정확한 거래량 위치 확인")
    print("2. 52주 최고/최저가 정확한 패턴 확인")  
    print("3. 추출 함수 수정")
    print("4. 재테스트 및 검증")
