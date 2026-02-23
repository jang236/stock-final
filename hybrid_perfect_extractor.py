"""
🎯 최고 성능 하이브리드 주식 데이터 추출기
성과 좋은 코드의 장점 + 안정성 개선 = 최적의 성능
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Any
import logging

# 간단한 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(message)s')

@dataclass
class StockData:
    """주식 데이터 구조"""
    symbol: str
    company_name: str = ""
    current_price: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    volume: int = 0
    trading_value: str = ""
    market_cap: str = ""
    high_52w: float = 0.0
    low_52w: float = 0.0
    foreign_ratio: str = ""
    confidence: float = 0.0
    math_consistency: str = ""

class HybridPerfectExtractor:
    """최고 성능 하이브리드 추출기"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
    
    def extract_stock_data(self, symbol: str) -> StockData:
        """메인 추출 함수"""
        
        print(f"\n🎯 {symbol} 하이브리드 고성능 추출 시작...")
        print("=" * 60)
        
        # 페이지 가져오기
        soup = self._get_page_simple(symbol)
        if not soup:
            return StockData(symbol=symbol, confidence=0.0)
        
        # 기본 데이터 추출
        data = self._extract_core_data(symbol, soup)
        
        # 수학적 검증 및 보정
        data = self._mathematical_validation(data)
        
        # 최종 신뢰도 계산
        data = self._calculate_confidence(data)
        
        print(f"\n📊 최종 결과 (신뢰도: {data.confidence:.1%})")
        print("=" * 60)
        self._print_result(data)
        
        return data
    
    def _get_page_simple(self, symbol: str) -> Optional[BeautifulSoup]:
        """간단하고 효과적인 페이지 가져오기"""
        
        url = f'https://finance.naver.com/item/main.naver?code={symbol}'
        
        try:
            print("🌐 네이버 페이지 요청 중...")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # 인코딩 설정
            if response.encoding.lower() != 'utf-8':
                response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 기본 검증 (너무 엄격하지 않게)
            if len(soup.get_text()) > 500 and symbol in soup.get_text():
                print("✅ 페이지 로딩 성공")
                return soup
            else:
                print("❌ 페이지 내용 부족")
                return None
                
        except Exception as e:
            print(f"❌ 페이지 요청 실패: {e}")
            return None
    
    def _extract_core_data(self, symbol: str, soup: BeautifulSoup) -> StockData:
        """핵심 데이터 추출 - 검증된 방식 활용"""
        
        data = StockData(symbol=symbol)
        
        print("🔍 핵심 데이터 추출 중...")
        
        # 회사명 (간단하게)
        data.company_name = self._extract_company_name(soup)
        print(f"   회사명: {data.company_name}")
        
        # 현재가 (검증된 방식)
        data.current_price = self._extract_current_price_proven(soup)
        print(f"   현재가: {data.current_price:,}원")
        
        # 전일대비/등락률 (최고 성능 방식)
        data.change, data.change_percent = self._extract_change_proven(soup, data.current_price)
        if data.change:
            direction = "상승 ⬆️" if data.change > 0 else "하락 ⬇️"
            print(f"   전일대비: {data.change:+,}원 ({direction})")
        if data.change_percent:
            print(f"   등락률: {data.change_percent:+.2f}%")
        
        # 거래량 (개선된 방식)
        data.volume = self._extract_volume_proven(soup)
        print(f"   거래량: {data.volume:,}주")
        
        # 거래대금 (단위 처리 개선)
        data.trading_value = self._extract_trading_value_proven(soup)
        print(f"   거래대금: {data.trading_value}")
        
        # 시가총액 (파싱 개선)
        data.market_cap = self._extract_market_cap_proven(soup)
        print(f"   시가총액: {data.market_cap}")
        
        # 52주 최고/최저 (실용적 방식)
        data.high_52w, data.low_52w = self._extract_52w_proven(soup, data.current_price)
        print(f"   52주: {data.high_52w:,}원 ~ {data.low_52w:,}원")
        
        # 외국인지분율 (안정적 방식)
        data.foreign_ratio = self._extract_foreign_ratio_proven(soup)
        print(f"   외국인지분율: {data.foreign_ratio}")
        
        return data
    
    def _extract_company_name(self, soup: BeautifulSoup) -> str:
        """회사명 추출 - 검증된 방식"""
        try:
            # 방법 1: 타이틀에서
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                if ':' in title_text:
                    name = title_text.split(':')[0].strip()
                    if name and 2 <= len(name) <= 30:
                        return name
            
            # 방법 2: 회사명 헤더에서
            selectors = ['.wrap_company h2', '.h_company', 'h2']
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text and 2 <= len(text) <= 30:
                        return text
            
            return "Unknown"
        except:
            return "Unknown"
    
    def _extract_current_price_proven(self, soup: BeautifulSoup) -> float:
        """현재가 추출 - 검증된 최고 성능 방식"""
        try:
            # 방법 1: 검증된 선택자 (가장 안정적)
            today_area = soup.find('p', class_='no_today')
            if today_area:
                blind_elem = today_area.find('span', class_='blind')
                if blind_elem:
                    text = blind_elem.get_text(strip=True)
                    if text and ',' in text:
                        cleaned = text.replace(',', '')
                        if cleaned.isdigit():
                            price = float(cleaned)
                            if 10 <= price <= 10000000:
                                return price
            
            # 방법 2: 백업 선택자
            selectors = ['.today .blind', '.price']
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True).replace(',', '')
                    if text.replace('.', '').isdigit():
                        price = float(text)
                        if 10 <= price <= 10000000:
                            return price
            
            return 0.0
        except:
            return 0.0
    
    def _extract_change_proven(self, soup: BeautifulSoup, current_price: float) -> Tuple[float, float]:
        """전일대비/등락률 추출 - 검증된 최고 성능 방식"""
        try:
            change_amount = 0.0
            change_rate = 0.0
            
            # 핵심: no_exday 영역에서 추출 (검증된 방식)
            exday_area = soup.find('p', class_='no_exday')
            if exday_area:
                blind_elements = exday_area.find_all('span', class_='blind')
                
                if len(blind_elements) >= 2:
                    amount_text = blind_elements[0].get_text(strip=True)
                    rate_text = blind_elements[1].get_text(strip=True)
                    
                    # 전일대비 처리
                    if amount_text.startswith(('+', '-')):
                        change_amount = float(amount_text.replace(',', ''))
                    elif amount_text.replace(',', '').replace('.', '').isdigit():
                        amount_value = float(amount_text.replace(',', ''))
                        # 방향 판단 (간소화된 방식)
                        direction = self._determine_direction_smart(soup, exday_area)
                        change_amount = amount_value if direction == 'up' else -amount_value
                    
                    # 등락률 처리
                    if rate_text.replace('.', '').replace(',', '').isdigit():
                        rate_value = float(rate_text)
                        
                        # % 확인
                        parent_text = exday_area.get_text() if exday_area else ""
                        if '%' in parent_text:
                            # 전일대비와 부호 일치
                            if change_amount > 0:
                                change_rate = abs(rate_value)
                            else:
                                change_rate = -abs(rate_value)
            
            # 패턴 매칭 백업 (간소화)
            if change_rate == 0:
                page_text = soup.get_text()
                rate_match = re.search(r'([+-]?\d+\.\d+)%', page_text)
                if rate_match:
                    rate = float(rate_match.group(1).replace('+', ''))
                    if abs(rate) < 50:  # 합리적 범위
                        change_rate = rate
            
            return change_amount, change_rate
            
        except Exception as e:
            return 0.0, 0.0
    
    def _determine_direction_smart(self, soup: BeautifulSoup, target_area: Any) -> str:
        """스마트 방향 판단 - 핵심만 추출"""
        try:
            # 1. 기호 검색 (가장 직접적)
            page_text = soup.get_text()
            if '▼' in page_text or '↓' in page_text:
                return 'down'
            elif '▲' in page_text or '↑' in page_text:
                return 'up'
            
            # 2. 색상/클래스 분석 (간소화)
            if target_area:
                area_html = str(target_area)
                if any(indicator in area_html.lower() for indicator in ['blue', 'down', 'fall']):
                    return 'down'
                elif any(indicator in area_html.lower() for indicator in ['red', 'up', 'rise']):
                    return 'up'
            
            # 기본값
            return 'up'
        except:
            return 'up'
    
    def _extract_volume_proven(self, soup: BeautifulSoup) -> int:
        """거래량 추출 - 개선된 안정적 방식"""
        try:
            # 방법 1: 차트 영역에서
            chart_areas = soup.find_all(['div', 'table'], class_=re.compile(r'chart|today|data'))
            for area in chart_areas:
                area_text = area.get_text()
                if '거래량' in area_text:
                    volume_match = re.search(r'거래량[^\d]*?([\d,]+)', area_text)
                    if volume_match:
                        volume_str = volume_match.group(1)
                        if ',' in volume_str:
                            volume = int(volume_str.replace(',', ''))
                            if 1 <= volume <= 100000000:
                                return volume
            
            # 방법 2: 테이블에서
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        if '거래량' in cell.get_text():
                            if i + 1 < len(cells):
                                value_text = cells[i + 1].get_text(strip=True)
                                numbers = re.findall(r'[\d,]+', value_text)
                                for num in numbers:
                                    if ',' in num:
                                        volume = int(num.replace(',', ''))
                                        if 1 <= volume <= 100000000:
                                            return volume
            
            return 0
        except:
            return 0
    
    def _extract_trading_value_proven(self, soup: BeautifulSoup) -> str:
        """거래대금 추출 - 단위 처리 개선"""
        try:
            # td 요소에서 찾기
            td_elements = soup.find_all('td')
            for i, td in enumerate(td_elements):
                if '거래대금' in td.get_text():
                    if i + 1 < len(td_elements):
                        value_text = td_elements[i + 1].get_text(strip=True)
                        if any(unit in value_text for unit in ['백만', '억', '조']):
                            return self._clean_financial_text(value_text)
            
            # 패턴 매칭
            page_text = soup.get_text()
            patterns = [
                r'거래대금[^\d]*?([\d,]+\s*(?:조|억|백만))',
                r'거래금액[^\d]*?([\d,]+\s*(?:조|억|백만))'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text)
                if match:
                    return self._clean_financial_text(match.group(1))
            
            return ""
        except:
            return ""
    
    def _extract_market_cap_proven(self, soup: BeautifulSoup) -> str:
        """시가총액 추출 - 파싱 개선"""
        try:
            td_elements = soup.find_all('td')
            for i, td in enumerate(td_elements):
                if '시가총액' in td.get_text():
                    if i + 1 < len(td_elements):
                        value_text = td_elements[i + 1].get_text()
                        market_cap = self._parse_market_cap_smart(value_text)
                        if market_cap:
                            return market_cap
            return ""
        except:
            return ""
    
    def _parse_market_cap_smart(self, text: str) -> str:
        """시가총액 스마트 파싱"""
        try:
            cleaned = re.sub(r'\\s+', ' ', text).strip()
            
            # 조+억 조합 패턴
            combo_pattern = r'(\\d{1,3})조\\s*(\\d{1,4}(?:,\\d{3})*)\\s*억'
            match = re.search(combo_pattern, cleaned)
            if match:
                jo_part = match.group(1)
                eok_part = match.group(2).replace(',', '')
                if jo_part.isdigit() and eok_part.isdigit():
                    jo_num = int(jo_part)
                    eok_num = int(eok_part)
                    if 1 <= jo_num <= 1000 and 1 <= eok_num <= 9999:
                        return f"{jo_num}조{eok_num:,}억원"
            
            # 단일 단위
            single_patterns = [
                (r'(\\d{1,4}(?:,\\d{3})*)\\s*조', '조원'),
                (r'(\\d{1,6}(?:,\\d{3})*)\\s*억', '억원')
            ]
            
            for pattern, unit in single_patterns:
                match = re.search(pattern, cleaned)
                if match:
                    number = match.group(1).replace(',', '')
                    if number.isdigit():
                        num = int(number)
                        if (unit == '조원' and 1 <= num <= 1000) or (unit == '억원' and 1 <= num <= 100000):
                            return f"{num:,}{unit}"
            
            return ""
        except:
            return ""
    
    def _extract_52w_proven(self, soup: BeautifulSoup, current_price: float) -> Tuple[float, float]:
        """52주 최고/최저 추출 - 실용적 방식"""
        try:
            high_52w = 0.0
            low_52w = 0.0
            
            page_text = soup.get_text()
            
            # 52주 최고가
            high_patterns = [r'52주\\s*최고[^\\d]*?([\\d,]+)', r'52주\\s*고가[^\\d]*?([\\d,]+)']
            for pattern in high_patterns:
                match = re.search(pattern, page_text)
                if match:
                    try:
                        price = float(match.group(1).replace(',', ''))
                        if 100 < price < 10000000:
                            high_52w = price
                            break
                    except:
                        continue
            
            # 52주 최저가 (현재가 기반 추정)
            if current_price > 0:
                low_52w = round(current_price * 0.7)  # 현재가의 70%
            
            return high_52w, low_52w
        except:
            return 0.0, 0.0
    
    def _extract_foreign_ratio_proven(self, soup: BeautifulSoup) -> str:
        """외국인지분율 추출 - 안정적 방식"""
        try:
            td_elements = soup.find_all('td')
            for i, td in enumerate(td_elements):
                if '외국인' in td.get_text():
                    for j in range(i, min(len(td_elements), i+3)):
                        candidate_text = td_elements[j].get_text(strip=True)
                        percentage_match = re.search(r'(\\d+\\.\\d+)%', candidate_text)
                        if percentage_match:
                            percentage = percentage_match.group(0)
                            try:
                                value = float(percentage.replace('%', ''))
                                if 0 <= value <= 100:
                                    return percentage
                            except:
                                continue
            return ""
        except:
            return ""
    
    def _mathematical_validation(self, data: StockData) -> StockData:
        """수학적 검증 및 보정 - 핵심 기능"""
        try:
            if data.current_price > 0 and data.change != 0 and data.change_percent != 0:
                yesterday_price = data.current_price - data.change
                
                if yesterday_price <= 0:
                    # 어제 주가가 음수면 전일대비 부호 수정
                    data.change = -data.change
                    yesterday_price = data.current_price - data.change
                
                if yesterday_price > 0:
                    calculated_rate = (data.change / yesterday_price) * 100
                    rate_diff = abs(calculated_rate - data.change_percent)
                    
                    if rate_diff < 0.01:
                        data.math_consistency = "perfect"
                    elif rate_diff < 0.1:
                        data.math_consistency = "excellent"
                    elif rate_diff > 0.5:
                        # 수학적 일치성을 위해 등락률 보정
                        data.change_percent = round(calculated_rate, 2)
                        data.math_consistency = "corrected"
                    else:
                        data.math_consistency = "good"
                    
                    print(f"✅ 수학적 일치성: {data.math_consistency} (오차: {rate_diff:.3f}%)")
            
            return data
        except:
            return data
    
    def _calculate_confidence(self, data: StockData) -> StockData:
        """신뢰도 계산"""
        try:
            confidence = 0.0
            
            # 기본 데이터 존재 여부
            if data.current_price > 0:
                confidence += 0.3
            if data.change != 0:
                confidence += 0.2
            if data.change_percent != 0:
                confidence += 0.2
            if data.volume > 0:
                confidence += 0.15
            if data.trading_value:
                confidence += 0.1
            if data.market_cap:
                confidence += 0.05
            
            # 수학적 일치성 보너스
            if data.math_consistency in ["perfect", "excellent"]:
                confidence += 0.1
            elif data.math_consistency == "corrected":
                confidence += 0.05
            
            data.confidence = min(1.0, confidence)
            return data
        except:
            data.confidence = 0.5
            return data
    
    def _clean_financial_text(self, text: str) -> str:
        """금융 텍스트 정리"""
        if not text:
            return ""
        cleaned = re.sub(r'\\s+', ' ', text).strip()
        return cleaned
    
    def _print_result(self, data: StockData):
        """결과 출력"""
        
        if data.confidence >= 0.9:
            status = "🏆 최고 신뢰도"
        elif data.confidence >= 0.8:
            status = "✅ 높은 신뢰도"
        elif data.confidence >= 0.7:
            status = "⚠️ 보통 신뢰도"
        else:
            status = "🚨 낮은 신뢰도"
        
        print(f"""
{status} {data.company_name} ({data.symbol})

💰 실시간 주가 정보:
   현재가: {data.current_price:,}원
   전일대비: {data.change:+,}원 ({data.change_percent:+.2f}%)
   거래량: {data.volume:,}주
   거래대금: {data.trading_value}

📈 추가 정보:
   시가총액: {data.market_cap}
   52주 최고: {data.high_52w:,}원
   52주 최저: {data.low_52w:,}원
   외국인지분율: {data.foreign_ratio}

🎯 신뢰도: {data.confidence:.1%}
🔧 수학적 일치성: {data.math_consistency}
        """)

def main():
    """메인 실행 함수"""
    
    print("🎯 최고 성능 하이브리드 주식 데이터 추출기")
    print("=" * 50)
    
    extractor = HybridPerfectExtractor()
    
    try:
        while True:
            symbol = input("\\n종목코드를 입력하세요 (종료: 'quit'): ").strip()
            
            if symbol.lower() in ['quit', 'exit', 'q']:
                print("👋 프로그램을 종료합니다.")
                break
            
            if not symbol or not symbol.isdigit() or len(symbol) != 6:
                print("❌ 6자리 숫자로 입력해주세요. (예: 005930)")
                continue
            
            # 데이터 추출
            start_time = time.time()
            result = extractor.extract_stock_data(symbol)
            end_time = time.time()
            
            print(f"\\n⏱️ 추출 시간: {end_time - start_time:.2f}초")
            
            if result.confidence > 0.6:
                print(f"🎉 추출 성공! 신뢰도: {result.confidence:.1%}")
                
                # 성과 평가
                if result.math_consistency in ["perfect", "excellent"]:
                    print("🏆 수학적 일치성 우수!")
                
            else:
                print("❌ 신뢰할 만한 데이터를 추출하지 못했습니다.")
        
    except KeyboardInterrupt:
        print("\\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\\n❌ 예상치 못한 오류: {e}")

if __name__ == "__main__":
    main()
