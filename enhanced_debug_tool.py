import requests
from bs4 import BeautifulSoup
import re

def find_exact_volume_location(stock_code="000660"):
    """
    거래량의 정확한 HTML 위치와 컨텍스트 분석
    현재가와 구분하는 명확한 방법 찾기
    """
    url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    }
    
    print(f"🔍 {stock_code} 거래량 정확 위치 특정 분석...")
    print("=" * 80)
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 모든 .blind 요소의 컨텍스트 분석
        print("📊 1. .blind 클래스 요소들의 주변 컨텍스트:")
        blind_elements = soup.select('.blind')
        
        for i, elem in enumerate(blind_elements):
            text = elem.get_text(strip=True)
            if re.match(r'^[\d,]+$', text):  # 순수 숫자만
                value = int(text.replace(',', ''))
                
                # 부모와 조부모의 컨텍스트 확인
                parent_context = ""
                if elem.parent:
                    parent_context = elem.parent.get('class', ['no-class'])
                    if elem.parent.parent:
                        grandparent_text = elem.parent.parent.get_text()[:50]
                    else:
                        grandparent_text = "no-grandparent"
                else:
                    grandparent_text = "no-parent"
                
                print(f"  #{i+1}: {text} ({value:,})")
                print(f"      부모 클래스: {parent_context}")
                print(f"      조부모 텍스트: {grandparent_text.strip()}")
                
                # 거래량 후보 식별
                if 1000000 <= value <= 50000000:  # 거래량 범위
                    print(f"      🎯 거래량 후보! 컨텍스트 상세 분석 필요")
                elif 100000 <= value <= 500000:  # 현재가 범위
                    print(f"      💰 현재가 후보")
                print()
        
        # 2. "거래량" 키워드 주변 HTML 구조 상세 분석
        print("📊 2. '거래량' 키워드 주변 상세 HTML 구조:")
        volume_keywords = soup.find_all(string=re.compile(r'거래량'))
        
        for i, keyword in enumerate(volume_keywords):
            print(f"\n  거래량 키워드 #{i+1}: '{keyword.strip()}'")
            
            # 부모 요소 상세 분석
            parent = keyword.parent
            if parent:
                print(f"    부모: <{parent.name}> {parent.get('class', 'no-class')}")
                
                # 인접한 모든 요소들 확인
                next_elements = []
                current = parent
                for j in range(10):  # 다음 10개 요소까지 확인
                    if current.next_sibling:
                        current = current.next_sibling
                        if hasattr(current, 'get_text'):
                            text = current.get_text(strip=True)
                            if text and re.search(r'[\d,]+', text):
                                next_elements.append(f"다음{j+1}: {text}")
                
                print(f"    다음 요소들: {next_elements}")
                
                # 같은 레벨의 형제 요소들
                siblings = parent.find_next_siblings()[:5]
                for j, sibling in enumerate(siblings):
                    if sibling and hasattr(sibling, 'get_text'):
                        text = sibling.get_text(strip=True)
                        if text:
                            print(f"    형제 #{j+1}: <{sibling.name}> '{text[:30]}...'")
                            # .blind 클래스 확인
                            blind_in_sibling = sibling.select('.blind')
                            for blind in blind_in_sibling:
                                blind_text = blind.get_text(strip=True)
                                if re.match(r'^[\d,]+$', blind_text):
                                    print(f"      🎯 발견! .blind: {blind_text}")
        
        # 3. 테이블에서 "거래량" 셀의 정확한 위치
        print("📊 3. 테이블 내 거래량 셀 정확 위치:")
        tables = soup.find_all('table')
        
        for table_idx, table in enumerate(tables):
            table_text = table.get_text()
            if '거래량' in table_text:
                print(f"\n  테이블 #{table_idx+1} (거래량 포함):")
                
                rows = table.find_all('tr')
                for row_idx, row in enumerate(rows):
                    row_text = row.get_text(strip=True)
                    if '거래량' in row_text:
                        print(f"    행 #{row_idx+1}: {row_text}")
                        
                        cells = row.find_all(['td', 'th'])
                        for cell_idx, cell in enumerate(cells):
                            cell_text = cell.get_text(strip=True)
                            print(f"      셀 #{cell_idx+1}: '{cell_text}'")
                            
                            # 각 셀 내부의 .blind 요소 확인
                            cell_blinds = cell.select('.blind')
                            for blind in cell_blinds:
                                blind_text = blind.get_text(strip=True)
                                if re.match(r'^[\d,]+$', blind_text):
                                    value = int(blind_text.replace(',', ''))
                                    if 1000000 <= value <= 50000000:
                                        print(f"        🎯🎯 거래량 발견! {blind_text} ({value:,})")
        
        # 4. 현재가 vs 거래량 구분 전략
        print("📊 4. 현재가 vs 거래량 구분 전략:")
        
        # 현재가 확실히 찾기
        current_price_candidates = []
        for elem in blind_elements:
            text = elem.get_text(strip=True)
            if re.match(r'^[\d,]+$', text):
                value = int(text.replace(',', ''))
                if 100000 <= value <= 500000:  # 현재가 범위
                    parent_context = str(elem.parent.parent) if elem.parent and elem.parent.parent else ""
                    if 'no_today' in parent_context or 'today' in parent_context:
                        current_price_candidates.append(value)
                        print(f"  현재가 후보: {value:,}원 (컨텍스트: no_today/today)")
        
        # 거래량 후보들
        volume_candidates = []
        for elem in blind_elements:
            text = elem.get_text(strip=True)
            if re.match(r'^[\d,]+$', text):
                value = int(text.replace(',', ''))
                if 1000000 <= value <= 50000000:  # 거래량 범위
                    volume_candidates.append(value)
                    print(f"  거래량 후보: {value:,}주")
        
        print(f"\n🎯 결론:")
        print(f"  현재가 후보들: {current_price_candidates}")
        print(f"  거래량 후보들: {volume_candidates}")
        
        if current_price_candidates and volume_candidates:
            current_price = current_price_candidates[0]
            volume = volume_candidates[0]
            print(f"  📈 확정 현재가: {current_price:,}원")
            print(f"  📊 확정 거래량: {volume:,}주")
            print(f"  🎯 구분 기준: 현재가는 'no_today' 컨텍스트, 거래량은 1M+ 범위")
        
        print(f"\n✅ 거래량 정확 위치 분석 완료!")
        
    except Exception as e:
        print(f"❌ 분석 실패: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        stock_code = sys.argv[1]
    else:
        stock_code = "000660"  # 기본값
    
    print(f"🎯 종목코드: {stock_code} 분석 시작")
    find_exact_volume_location(stock_code)
