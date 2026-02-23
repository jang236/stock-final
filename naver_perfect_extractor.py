"""
🎯 네이버 증권 완전 정복 시스템
단일 소스 완벽 최적화 + 내부 교차검증
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Any
import logging
from urllib.parse import quote

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class StockData:
    """표준화된 주식 데이터 구조"""
    symbol: str
    company_name: str = ""
    current_price: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    volume: int = 0
    trading_value: float = 0.0
    market_cap: str = ""
    high_52w: float = 0.0
    low_52w: float = 0.0
    foreign_ratio: float = 0.0
    confidence: float = 0.0
    extraction_methods: Dict[str, str] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)

class NaverPerfectExtractor:
    """네이버 증권 완전 정복 추출기"""
    
    def __init__(self):
        self.session = requests.Session()
        self.setup_session()
        self.retry_count = 3
        self.retry_delay = 2
        
    def setup_session(self):
        """세션 설정 - 실제 브라우저 모방"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.session.headers.update(headers)
    
    def extract_stock_data(self, symbol: str) -> StockData:
        """메인 추출 함수"""
        
        print(f"\n🎯 {symbol} 네이버 완전 정복 추출 시작...")
        print("=" * 70)
        
        # 1차 시도
        soup = self.get_page_soup(symbol)
        if not soup:
            return StockData(symbol=symbol, confidence=0.0)
        
        # 기본 데이터 추출
        data = self.extract_basic_data(symbol, soup)
        
        # 의심스러운 데이터 검증
        if self.is_suspicious_data(data):
            print("🔍 데이터 의심스러움, 재검증 진행...")
            time.sleep(self.retry_delay)
            soup_retry = self.get_page_soup(symbol)
            if soup_retry:
                data_retry = self.extract_basic_data(symbol, soup_retry)
                data = self.compare_and_merge(data, data_retry)
        
        # 내부 교차검증
        data = self.internal_cross_validation(data, soup)
        
        # 최종 검증 및 신뢰도 계산
        data = self.final_validation(data)
        
        print(f"\n📊 최종 결과 (신뢰도: {data.confidence:.1%})")
        print("=" * 70)
        self.print_detailed_result(data)
        
        return data
    
    def get_page_soup(self, symbol: str) -> Optional[BeautifulSoup]:
        """페이지 HTML 가져오기 (재시도 포함)"""
        
        url = f'https://finance.naver.com/item/main.naver?code={symbol}'
        
        for attempt in range(self.retry_count):
            try:
                print(f"🌐 네이버 페이지 요청 중... (시도 {attempt + 1}/{self.retry_count})")
                
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                # 인코딩 확인 및 수정
                if response.encoding.lower() != 'utf-8':
                    response.encoding = 'utf-8'
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 기본 유효성 검사
                if self.is_valid_stock_page(soup, symbol):
                    print("✅ 페이지 로딩 성공")
                    return soup
                else:
                    print("⚠️ 페이지 내용 이상, 재시도...")
                    
            except Exception as e:
                print(f"❌ 페이지 요청 실패 (시도 {attempt + 1}): {e}")
                
            if attempt < self.retry_count - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        print("💥 모든 페이지 요청 실패")
        return None
    
    def is_valid_stock_page(self, soup: BeautifulSoup, symbol: str) -> bool:
        """페이지 유효성 검사"""
        
        # 기본 체크
        if not soup or len(soup.get_text()) < 1000:
            return False
        
        # 종목 코드 확인
        page_text = soup.get_text()
        if symbol not in page_text:
            return False
        
        # 핵심 요소 존재 확인
        essential_keywords = ['현재가', '전일대비', '거래량']
        for keyword in essential_keywords:
            if keyword not in page_text:
                return False
        
        return True
    
    def extract_basic_data(self, symbol: str, soup: BeautifulSoup) -> StockData:
        """기본 데이터 추출"""
        
        data = StockData(symbol=symbol)
        
        print("🔍 기본 데이터 추출 중...")
        
        # 회사명
        data.company_name = self.extract_company_name(soup)
        print(f"   회사명: {data.company_name}")
        
        # 현재가 (5가지 방법)
        price, price_method = self.extract_current_price_multi(soup)
        data.current_price = price
        data.extraction_methods['price'] = price_method
        print(f"   현재가: {data.current_price:,}원 ({price_method})")
        
        # 전일대비/등락률
        change, change_percent, change_method = self.extract_change_multi(soup)
        data.change = change
        data.change_percent = change_percent
        data.extraction_methods['change'] = change_method
        print(f"   전일대비: {data.change:+,}원 ({data.change_percent:+.2f}%) ({change_method})")
        
        # 거래량
        volume, volume_method = self.extract_volume_multi(soup, data.current_price)
        data.volume = volume
        data.extraction_methods['volume'] = volume_method
        print(f"   거래량: {data.volume:,}주 ({volume_method})")
        
        # 거래대금
        trading_value, trading_method = self.extract_trading_value_multi(soup)
        data.trading_value = trading_value
        data.extraction_methods['trading'] = trading_method
        print(f"   거래대금: {data.trading_value:.0f}억원 ({trading_method})")
        
        # 시가총액
        market_cap = self.extract_market_cap_multi(soup)
        data.market_cap = market_cap
        print(f"   시가총액: {data.market_cap}")
        
        # 52주 최고/최저
        high_52w, low_52w = self.extract_52w_range_multi(soup)
        data.high_52w = high_52w
        data.low_52w = low_52w
        print(f"   52주: {data.high_52w:,}원 ~ {data.low_52w:,}원")
        
        # 외국인지분율
        foreign_ratio = self.extract_foreign_ratio_multi(soup)
        data.foreign_ratio = foreign_ratio
        print(f"   외국인지분율: {data.foreign_ratio:.2f}%")
        
        return data
    
    def extract_company_name(self, soup: BeautifulSoup) -> str:
        """회사명 추출 - 다중 전략"""
        
        strategies = [
            ('.wrap_company h2 a', 'link_text'),
            ('.wrap_company h2', 'header_text'),
            ('h2.h_company', 'h_company'),
            ('.name_company', 'name_company'),
            ('title', 'page_title')
        ]
        
        for selector, method in strategies:
            try:
                if method == 'page_title':
                    element = soup.find('title')
                    if element:
                        title_text = element.get_text()
                        # "삼성전자 : 네이버 금융" 형태에서 회사명 추출
                        match = re.search(r'^([^:]+)', title_text)
                        if match:
                            return match.group(1).strip()
                else:
                    element = soup.select_one(selector)
                    if element:
                        return element.get_text(strip=True)
            except:
                continue
        
        return "Unknown Company"
    
    def extract_current_price_multi(self, soup: BeautifulSoup) -> Tuple[float, str]:
        """현재가 추출 - 5가지 전략"""
        
        strategies = [
            ('main_today', self._extract_price_main_today),
            ('no_today', self._extract_price_no_today),
            ('table_search', self._extract_price_table),
            ('script_data', self._extract_price_script),
            ('pattern_match', self._extract_price_pattern)
        ]
        
        candidates = []
        
        for method_name, extract_func in strategies:
            try:
                price = extract_func(soup)
                if price and self._is_reasonable_price(price):
                    candidates.append((price, method_name))
                    print(f"      현재가 후보: {price:,}원 ({method_name})")
            except Exception as e:
                print(f"      {method_name} 실패: {e}")
        
        if candidates:
            # 최빈값 또는 첫 번째 성공값 반환
            if len(candidates) == 1:
                return candidates[0]
            else:
                # 여러 후보 중 가장 합리적인 값 선택
                return self._select_best_price(candidates)
        
        return 0.0, "failed"
    
    def _extract_price_main_today(self, soup: BeautifulSoup) -> Optional[float]:
        """전략 1: 메인 today 영역"""
        element = soup.select_one('.today .blind')
        if element:
            return float(element.get_text(strip=True).replace(',', ''))
        return None
    
    def _extract_price_no_today(self, soup: BeautifulSoup) -> Optional[float]:
        """전략 2: no_today 클래스"""
        element = soup.select_one('p.no_today')
        if element:
            text = element.get_text(strip=True)
            match = re.search(r'(\d{1,3}(?:,\d{3})*)', text)
            if match:
                return float(match.group(1).replace(',', ''))
        return None
    
    def _extract_price_table(self, soup: BeautifulSoup) -> Optional[float]:
        """전략 3: 테이블에서 현재가 찾기"""
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                for i, cell in enumerate(cells):
                    if '현재가' in cell.get_text():
                        if i + 1 < len(cells):
                            price_text = cells[i + 1].get_text(strip=True)
                            match = re.search(r'(\d{1,3}(?:,\d{3})*)', price_text)
                            if match:
                                return float(match.group(1).replace(',', ''))
        return None
    
    def _extract_price_script(self, soup: BeautifulSoup) -> Optional[float]:
        """전략 4: JavaScript 데이터에서 추출"""
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # 현재가 관련 변수 패턴
                patterns = [
                    r'nowVal\s*[=:]\s*["\']?(\d{1,3}(?:,\d{3})*)["\']?',
                    r'curPrice\s*[=:]\s*["\']?(\d{1,3}(?:,\d{3})*)["\']?',
                    r'price\s*[=:]\s*["\']?(\d{1,3}(?:,\d{3})*)["\']?'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, script.string)
                    if match:
                        return float(match.group(1).replace(',', ''))
        return None
    
    def _extract_price_pattern(self, soup: BeautifulSoup) -> Optional[float]:
        """전략 5: 패턴 매칭으로 합리적인 가격 찾기"""
        text = soup.get_text()
        numbers = re.findall(r'(\d{1,3}(?:,\d{3})*)', text)
        
        for num_str in numbers:
            try:
                price = float(num_str.replace(',', ''))
                if self._is_reasonable_price(price):
                    return price
            except:
                continue
        return None
    
    def _is_reasonable_price(self, price: float) -> bool:
        """가격 합리성 검증"""
        return 100 <= price <= 10000000  # 100원 ~ 1000만원
    
    def _select_best_price(self, candidates: List[Tuple[float, str]]) -> Tuple[float, str]:
        """최적 가격 선택"""
        if len(candidates) == 1:
            return candidates[0]
        
        # 우선순위: main_today > no_today > table_search > script_data > pattern_match
        priority = ['main_today', 'no_today', 'table_search', 'script_data', 'pattern_match']
        
        for method in priority:
            for price, candidate_method in candidates:
                if candidate_method == method:
                    return price, f"{method}_priority"
        
        # 최빈값 선택
        prices = [c[0] for c in candidates]
        most_common = max(set(prices), key=prices.count)
        for price, method in candidates:
            if price == most_common:
                return price, f"{method}_consensus"
        
        return candidates[0]
    
    def extract_change_multi(self, soup: BeautifulSoup) -> Tuple[float, float, str]:
        """전일대비/등락률 추출 - 다중 전략"""
        
        change = 0.0
        change_percent = 0.0
        method = "unknown"
        
        # 전략 1: today 섹션에서 추출
        try:
            today_section = soup.select_one('.today')
            if today_section:
                # 전일대비
                change_elements = today_section.select('.change')
                if change_elements:
                    change_text = change_elements[0].get_text(strip=True)
                    change = self._parse_change_value(change_text)
                
                # 등락률
                rate_elements = today_section.select('.rate')
                if rate_elements:
                    rate_text = rate_elements[0].get_text(strip=True)
                    change_percent = self._parse_rate_value(rate_text)
                
                if change != 0 or change_percent != 0:
                    method = "today_section"
                    return change, change_percent, method
        except:
            pass
        
        # 전략 2: 패턴 매칭
        try:
            text = soup.get_text()
            
            # 전일대비 패턴들
            change_patterns = [
                r'전일대비[:\s]*([+-]?[\d,]+)',
                r'대비[:\s]*([+-]?[\d,]+)',
                r'변동[:\s]*([+-]?[\d,]+)'
            ]
            
            for pattern in change_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    change = self._parse_change_value(matches[0])
                    break
            
            # 등락률 패턴들
            rate_patterns = [
                r'([+-]?\d+\.?\d*)%',
                r'등락률[:\s]*([+-]?\d+\.?\d*)%'
            ]
            
            for pattern in rate_patterns:
                matches = re.findall(pattern, text)
                if matches:
                    # 가장 합리적인 등락률 선택 (보통 ±30% 이내)
                    for match in matches:
                        rate = float(match.replace('+', ''))
                        if -30 <= rate <= 30:
                            change_percent = rate
                            break
                    if change_percent != 0:
                        break
            
            if change != 0 or change_percent != 0:
                method = "pattern_matching"
        except:
            pass
        
        # 전략 3: 테이블에서 검색
        try:
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        cell_text = cell.get_text()
                        if any(keyword in cell_text for keyword in ['전일대비', '대비', '변동']):
                            if i + 1 < len(cells):
                                value_text = cells[i + 1].get_text(strip=True)
                                parsed_change = self._parse_change_value(value_text)
                                if parsed_change != 0:
                                    change = parsed_change
                                    method = "table_search"
                                    break
        except:
            pass
        
        return change, change_percent, method
    
    def _parse_change_value(self, text: str) -> float:
        """전일대비 값 파싱"""
        try:
            # 부호와 숫자 추출
            match = re.search(r'([+-]?)([\d,]+)', text.replace(' ', ''))
            if match:
                sign = match.group(1)
                value = float(match.group(2).replace(',', ''))
                
                # 부호 적용
                if sign == '-':
                    return -value
                elif sign == '+' or sign == '':
                    return value
        except:
            pass
        return 0.0
    
    def _parse_rate_value(self, text: str) -> float:
        """등락률 값 파싱"""
        try:
            # %를 제거하고 숫자 추출
            clean_text = text.replace('%', '').replace(' ', '')
            match = re.search(r'([+-]?\d+\.?\d*)', clean_text)
            if match:
                return float(match.group(1))
        except:
            pass
        return 0.0
    
    def extract_volume_multi(self, soup: BeautifulSoup, current_price: float) -> Tuple[int, str]:
        """거래량 추출 - 다중 전략 + 합리성 검증"""
        
        candidates = []
        
        # 전략 1: ID 기반
        try:
            element = soup.find(id='_volume')
            if element:
                volume = int(element.get_text(strip=True).replace(',', ''))
                if self._is_reasonable_volume(volume, current_price):
                    candidates.append((volume, "id_volume", 100))
        except:
            pass
        
        # 전략 2: 테이블 검색
        try:
            tables = soup.find_all('table')
            for table_idx, table in enumerate(tables):
                table_text = table.get_text()
                if '거래량' in table_text:
                    # 거래량 주변의 숫자들 찾기
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        for i, cell in enumerate(cells):
                            if '거래량' in cell.get_text():
                                # 다음 셀들에서 숫자 찾기
                                for j in range(i + 1, min(i + 3, len(cells))):
                                    try:
                                        volume_text = cells[j].get_text(strip=True)
                                        volume = self._extract_number_from_text(volume_text)
                                        if volume and self._is_reasonable_volume(volume, current_price):
                                            candidates.append((volume, f"table_{table_idx}", 90))
                                    except:
                                        continue
        except:
            pass
        
        # 전략 3: 패턴 매칭 (거래량 키워드 근처)
        try:
            text = soup.get_text()
            # 거래량 키워드 이후 나오는 숫자들
            volume_sections = re.split(r'거래량', text)
            for section in volume_sections[1:]:
                numbers = re.findall(r'(\d{1,3}(?:,\d{3})*)', section[:200])
                for num_str in numbers[:5]:  # 처음 5개만 검사
                    try:
                        volume = int(num_str.replace(',', ''))
                        if self._is_reasonable_volume(volume, current_price):
                            candidates.append((volume, "pattern_proximity", 70))
                    except:
                        continue
        except:
            pass
        
        # 전략 4: 모든 숫자에서 합리적인 거래량 찾기
        try:
            text = soup.get_text()
            numbers = re.findall(r'(\d{1,3}(?:,\d{3})*)', text)
            for num_str in numbers:
                try:
                    volume = int(num_str.replace(',', ''))
                    if self._is_reasonable_volume(volume, current_price):
                        candidates.append((volume, "pattern_reasonable", 60))
                except:
                    continue
        except:
            pass
        
        # 최적 후보 선택
        if candidates:
            return self._select_best_volume(candidates)
        
        return 0, "failed"
    
    def _extract_number_from_text(self, text: str) -> Optional[int]:
        """텍스트에서 숫자 추출"""
        try:
            # 쉼표가 있는 숫자 패턴
            match = re.search(r'(\d{1,3}(?:,\d{3})*)', text)
            if match:
                return int(match.group(1).replace(',', ''))
        except:
            pass
        return None
    
    def _is_reasonable_volume(self, volume: int, current_price: float) -> bool:
        """거래량 합리성 검증"""
        
        # 기본 범위
        if not (100 <= volume <= 100000000):
            return False
        
        # 거래대금 기반 검증
        if current_price > 0:
            trading_value = volume * current_price / 100000000  # 억원
            if trading_value > 50000:  # 5조원 초과는 비현실적
                return False
            if trading_value < 0.01:  # 100만원 미만도 의심스러움
                return False
        
        return True
    
    def _select_best_volume(self, candidates: List[Tuple[int, str, int]]) -> Tuple[int, str]:
        """최적 거래량 선택"""
        
        if len(candidates) == 1:
            return candidates[0][0], candidates[0][1]
        
        # 점수순 정렬
        candidates.sort(key=lambda x: x[2], reverse=True)
        
        # 최고 점수 그룹
        top_score = candidates[0][2]
        top_candidates = [c for c in candidates if c[2] == top_score]
        
        if len(top_candidates) == 1:
            return top_candidates[0][0], top_candidates[0][1]
        
        # 중간값 선택 (이상치 제거)
        volumes = [c[0] for c in top_candidates]
        volumes.sort()
        median_volume = volumes[len(volumes) // 2]
        
        for candidate in top_candidates:
            if candidate[0] == median_volume:
                return candidate[0], f"{candidate[1]}_median"
        
        return top_candidates[0][0], top_candidates[0][1]
    
    def extract_trading_value_multi(self, soup: BeautifulSoup) -> Tuple[float, str]:
        """거래대금 추출 - 다중 단위 처리"""
        
        text = soup.get_text()
        
        # 다양한 패턴들
        patterns = [
            (r'거래대금[:\s]*([0-9,]+)\s*조', 10000, "trillion"),
            (r'거래대금[:\s]*([0-9,]+)\s*억', 1, "billion"),
            (r'거래대금[:\s]*([0-9,]+)\s*백만', 0.01, "million"),
            (r'거래대금[:\s]*([0-9,]+)\s*만', 0.0001, "ten_thousand"),
            (r'거래대금[:\s]*([0-9,]+)원', 0.00000001, "won")  # 원 단위
        ]
        
        for pattern, multiplier, unit_name in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    value = float(matches[0].replace(',', ''))
                    result = value * multiplier
                    # 합리성 검증 (0.1억 ~ 10조)
                    if 0.1 <= result <= 100000:
                        return result, f"pattern_{unit_name}"
                except:
                    continue
        
        return 0.0, "failed"
    
    def extract_market_cap_multi(self, soup: BeautifulSoup) -> str:
        """시가총액 추출 - 다중 패턴"""
        
        text = soup.get_text()
        
        patterns = [
            r'시가총액[:\s]*([0-9,조억만\s]+원?)',
            r'총액[:\s]*([0-9,조억만\s]+원?)',
            r'Market\s*Cap[:\s]*([0-9,조억만\s]+원?)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0].strip()
        
        return ""
    
    def extract_52w_range_multi(self, soup: BeautifulSoup) -> Tuple[float, float]:
        """52주 최고/최저가 추출 - 다중 전략"""
        
        high_52w = 0.0
        low_52w = 0.0
        
        # 전략 1: 테이블에서 찾기
        try:
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        cell_text = cell.get_text()
                        if '52주' in cell_text or '최고' in cell_text:
                            # 최고가 찾기
                            if '최고' in cell_text and i + 1 < len(cells):
                                try:
                                    price_text = cells[i + 1].get_text(strip=True)
                                    high_52w = self._extract_price_from_text(price_text)
                                except:
                                    pass
                        
                        if '52주' in cell_text or '최저' in cell_text:
                            # 최저가 찾기
                            if '최저' in cell_text and i + 1 < len(cells):
                                try:
                                    price_text = cells[i + 1].get_text(strip=True)
                                    low_52w = self._extract_price_from_text(price_text)
                                except:
                                    pass
        except:
            pass
        
        # 전략 2: 패턴 매칭
        if high_52w == 0 or low_52w == 0:
            try:
                text = soup.get_text()
                
                # 52주 최고가
                high_patterns = [
                    r'52주\s*최고[:\s]*([0-9,]+)',
                    r'최고가[:\s]*([0-9,]+)',
                    r'High[:\s]*([0-9,]+)'
                ]
                
                for pattern in high_patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        try:
                            high_52w = float(matches[0].replace(',', ''))
                            break
                        except:
                            continue
                
                # 52주 최저가
                low_patterns = [
                    r'52주\s*최저[:\s]*([0-9,]+)',
                    r'최저가[:\s]*([0-9,]+)',
                    r'Low[:\s]*([0-9,]+)'
                ]
                
                for pattern in low_patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        try:
                            low_52w = float(matches[0].replace(',', ''))
                            break
                        except:
                            continue
            except:
                pass
        
        return high_52w, low_52w
    
    def _extract_price_from_text(self, text: str) -> float:
        """텍스트에서 가격 추출"""
        try:
            match = re.search(r'(\d{1,3}(?:,\d{3})*)', text)
            if match:
                return float(match.group(1).replace(',', ''))
        except:
            pass
        return 0.0
    
    def extract_foreign_ratio_multi(self, soup: BeautifulSoup) -> float:
        """외국인지분율 추출 - 다중 패턴"""
        
        text = soup.get_text()
        
        patterns = [
            r'외국인[^0-9]*([0-9.]+)%',
            r'외국인지분[^0-9]*([0-9.]+)%',
            r'Foreign[^0-9]*([0-9.]+)%'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                try:
                    ratio = float(matches[0])
                    if 0 <= ratio <= 100:  # 합리적 범위
                        return ratio
                except:
                    continue
        
        return 0.0
    
    def is_suspicious_data(self, data: StockData) -> bool:
        """데이터 의심스러움 판단"""
        
        suspicious_flags = []
        
        # 현재가가 너무 이상한 경우
        if data.current_price <= 0:
            suspicious_flags.append("no_price")
        
        # 거래량이 0인 경우 (장 중이라면 의심스러움)
        if data.volume == 0:
            suspicious_flags.append("no_volume")
        
        # 전일대비와 등락률의 불일치
        if data.current_price > 0 and data.change != 0:
            expected_percent = (data.change / data.current_price) * 100
            actual_percent = data.change_percent
            if abs(expected_percent - actual_percent) > 1.0:  # 1% 이상 차이
                suspicious_flags.append("change_mismatch")
        
        # 거래대금과 거래량의 불일치
        if data.current_price > 0 and data.volume > 0 and data.trading_value > 0:
            expected_trading = (data.volume * data.current_price) / 100000000
            if abs(expected_trading - data.trading_value) > expected_trading * 0.5:  # 50% 이상 차이
                suspicious_flags.append("trading_value_mismatch")
        
        if suspicious_flags:
            print(f"⚠️ 의심스러운 데이터 감지: {', '.join(suspicious_flags)}")
            return True
        
        return False
    
    def compare_and_merge(self, data1: StockData, data2: StockData) -> StockData:
        """두 데이터 비교 및 병합"""
        
        print("🔍 재검증 데이터와 비교 중...")
        
        merged = StockData(symbol=data1.symbol)
        merged.company_name = data1.company_name or data2.company_name
        
        # 현재가 비교
        if abs(data1.current_price - data2.current_price) < data1.current_price * 0.01:  # 1% 이내
            merged.current_price = (data1.current_price + data2.current_price) / 2
            print(f"   현재가: 평균값 사용 ({merged.current_price:,}원)")
        else:
            merged.current_price = data1.current_price  # 첫 번째 우선
            print(f"   현재가: 첫 번째 값 사용 ({merged.current_price:,}원)")
        
        # 거래량 비교
        if abs(data1.volume - data2.volume) < max(data1.volume, data2.volume) * 0.1:  # 10% 이내
            merged.volume = int((data1.volume + data2.volume) / 2)
            print(f"   거래량: 평균값 사용 ({merged.volume:,}주)")
        else:
            merged.volume = data1.volume  # 첫 번째 우선
            print(f"   거래량: 첫 번째 값 사용 ({merged.volume:,}주)")
        
        # 나머지 필드는 첫 번째 우선
        merged.change = data1.change or data2.change
        merged.change_percent = data1.change_percent or data2.change_percent
        merged.trading_value = data1.trading_value or data2.trading_value
        merged.market_cap = data1.market_cap or data2.market_cap
        merged.high_52w = data1.high_52w or data2.high_52w
        merged.low_52w = data1.low_52w or data2.low_52w
        merged.foreign_ratio = data1.foreign_ratio or data2.foreign_ratio
        
        return merged
    
    def internal_cross_validation(self, data: StockData, soup: BeautifulSoup) -> StockData:
        """내부 교차검증 - 같은 페이지에서 다른 위치의 데이터 확인"""
        
        print("🔍 내부 교차검증 진행 중...")
        
        validation_results = {}
        
        # 현재가 내부 검증
        all_prices = []
        
        # 다양한 위치에서 현재가 후보 수집
        strategies = [
            ('main', self._extract_price_main_today),
            ('table', self._extract_price_table),
            ('script', self._extract_price_script)
        ]
        
        for name, func in strategies:
            try:
                price = func(soup)
                if price and self._is_reasonable_price(price):
                    all_prices.append((price, name))
            except:
                pass
        
        # 현재가 일치성 검증
        if len(all_prices) > 1:
            prices_only = [p[0] for p in all_prices]
            max_diff = max(prices_only) - min(prices_only)
            avg_price = sum(prices_only) / len(prices_only)
            diff_percent = (max_diff / avg_price) * 100
            
            validation_results['price_consistency'] = {
                'candidates': all_prices,
                'max_diff': max_diff,
                'diff_percent': diff_percent,
                'consistent': diff_percent < 1.0
            }
            
            print(f"   현재가 일치성: {len(all_prices)}개 후보, 차이 {diff_percent:.2f}%")
        
        # 거래량 vs 거래대금 일치성
        if data.volume > 0 and data.current_price > 0 and data.trading_value > 0:
            calculated_trading = (data.volume * data.current_price) / 100000000
            actual_trading = data.trading_value
            diff_percent = abs(calculated_trading - actual_trading) / actual_trading * 100
            
            validation_results['trading_consistency'] = {
                'calculated': calculated_trading,
                'actual': actual_trading,
                'diff_percent': diff_percent,
                'consistent': diff_percent < 20.0
            }
            
            print(f"   거래대금 일치성: 계산값 {calculated_trading:.1f}억, 실제값 {actual_trading:.1f}억, 차이 {diff_percent:.1f}%")
        
        data.validation_results = validation_results
        return data
    
    def final_validation(self, data: StockData) -> StockData:
        """최종 검증 및 신뢰도 계산"""
        
        print("🔍 최종 검증 및 신뢰도 계산 중...")
        
        confidence = 1.0
        issues = []
        
        # 기본 데이터 존재 여부
        if data.current_price <= 0:
            confidence -= 0.5
            issues.append("no_current_price")
        
        if data.volume <= 0:
            confidence -= 0.2
            issues.append("no_volume")
        
        if data.change == 0 and data.change_percent == 0:
            confidence -= 0.1
            issues.append("no_change_info")
        
        # 내부 검증 결과 반영
        if 'price_consistency' in data.validation_results:
            consistency = data.validation_results['price_consistency']
            if consistency['consistent']:
                confidence += 0.1
                print("   ✅ 현재가 내부 일치성 양호")
            else:
                confidence -= 0.2
                issues.append("price_inconsistent")
                print("   ⚠️ 현재가 내부 불일치")
        
        if 'trading_consistency' in data.validation_results:
            consistency = data.validation_results['trading_consistency']
            if consistency['consistent']:
                confidence += 0.1
                print("   ✅ 거래대금 일치성 양호")
            else:
                confidence -= 0.1
                issues.append("trading_inconsistent")
                print("   ⚠️ 거래대금 불일치")
        
        # 추출 방법 다양성 보너스
        methods = data.extraction_methods
        if len([m for m in methods.values() if m != "failed"]) >= 4:
            confidence += 0.1
            print("   ✅ 다양한 방법으로 성공적 추출")
        
        # 신뢰도 범위 조정
        confidence = max(0.0, min(1.0, confidence))
        data.confidence = confidence
        
        if issues:
            print(f"   ⚠️ 감지된 문제: {', '.join(issues)}")
        
        return data
    
    def print_detailed_result(self, data: StockData):
        """상세 결과 출력"""
        
        if data.confidence >= 0.9:
            status = "🏆 최고 신뢰도"
            color = "\033[92m"  # 녹색
        elif data.confidence >= 0.8:
            status = "✅ 높은 신뢰도"
            color = "\033[94m"  # 파란색
        elif data.confidence >= 0.7:
            status = "⚠️ 보통 신뢰도"
            color = "\033[93m"  # 노란색
        else:
            status = "🚨 낮은 신뢰도"
            color = "\033[91m"  # 빨간색
        
        reset_color = "\033[0m"
        
        print(f"""
{color}{status} {data.company_name} ({data.symbol}){reset_color}

💰 실시간 주가 정보:
   현재가: {data.current_price:,}원
   전일대비: {data.change:+,}원 ({data.change_percent:+.2f}%)
   거래량: {data.volume:,}주
   거래대금: {data.trading_value:.1f}억원

📈 추가 정보:
   시가총액: {data.market_cap}
   52주 최고: {data.high_52w:,}원
   52주 최저: {data.low_52w:,}원
   외국인지분율: {data.foreign_ratio:.2f}%

🎯 신뢰도: {data.confidence:.1%}

🔧 추출 방법:
   현재가: {data.extraction_methods.get('price', 'unknown')}
   전일대비: {data.extraction_methods.get('change', 'unknown')}
   거래량: {data.extraction_methods.get('volume', 'unknown')}
   거래대금: {data.extraction_methods.get('trading', 'unknown')}
        """)
        
        # 검증 결과 상세
        if data.validation_results:
            print("🔍 내부 검증 결과:")
            for key, result in data.validation_results.items():
                if key == 'price_consistency':
                    status_icon = "✅" if result['consistent'] else "⚠️"
                    print(f"   {status_icon} 현재가 일치성: {len(result['candidates'])}개 후보, 차이 {result['diff_percent']:.2f}%")
                elif key == 'trading_consistency':
                    status_icon = "✅" if result['consistent'] else "⚠️"
                    print(f"   {status_icon} 거래대금 일치성: 차이 {result['diff_percent']:.1f}%")

def main():
    """메인 실행 함수"""
    
    print("🎯 네이버 증권 완전 정복 시스템")
    print("=" * 50)
    
    extractor = NaverPerfectExtractor()
    
    try:
        while True:
            symbol = input("\n종목코드를 입력하세요 (종료: 'quit'): ").strip()
            
            if symbol.lower() in ['quit', 'exit', 'q']:
                print("👋 프로그램을 종료합니다.")
                break
            
            if not symbol:
                print("❌ 종목코드를 입력해주세요.")
                continue
            
            if not symbol.isdigit() or len(symbol) != 6:
                print("❌ 6자리 숫자로 입력해주세요. (예: 005930)")
                continue
            
            # 데이터 추출
            start_time = time.time()
            result = extractor.extract_stock_data(symbol)
            end_time = time.time()
            
            print(f"\n⏱️ 추출 시간: {end_time - start_time:.2f}초")
            
            if result.confidence > 0.5:
                print(f"🎉 추출 성공! 신뢰도: {result.confidence:.1%}")
            else:
                print("❌ 신뢰할 만한 데이터를 추출하지 못했습니다.")
                print("   다른 종목을 시도해보거나 잠시 후 다시 시도해주세요.")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        print("   프로그램을 다시 시작해주세요.")

if __name__ == "__main__":
    main()
