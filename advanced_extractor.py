"""
🎯 고도화된 BeautifulSoup 네이버+다음 교차검증 시스템
안정적이고 정교한 정적 HTML 파싱 + 교차검증
"""

import requests
from bs4 import BeautifulSoup
import re
import time
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
import logging
from urllib.parse import quote

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class StockData:
    """주식 데이터 구조"""
    symbol: str
    company_name: str = ""
    current_price: float = 0
    change: float = 0
    change_percent: float = 0
    volume: int = 0
    trading_value: float = 0
    market_cap: str = ""
    high_52w: float = 0
    low_52w: float = 0
    foreign_ratio: float = 0
    source: str = ""
    confidence: float = 0.0
    extraction_details: Dict = None

class AdvancedStockExtractor:
    """고도화된 BeautifulSoup 주식 데이터 추출기"""
    
    def __init__(self):
        self.session = requests.Session()
        # 실제 브라우저처럼 보이는 헤더
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def extract_stock_data(self, symbol: str) -> StockData:
        """메인 추출 함수 - 네이버 + 다음 교차검증"""
        
        print(f"\n🎯 {symbol} 고도화된 교차검증 추출 시작...")
        print("=" * 60)
        
        # 1. 네이버 데이터 추출
        naver_data = self.extract_from_naver_advanced(symbol)
        
        # 2. 다음 데이터 추출
        daum_data = self.extract_from_daum_advanced(symbol)
        
        # 3. 교차검증 및 최종 결과
        final_data = self.cross_validate_advanced(naver_data, daum_data, symbol)
        
        print(f"\n📊 최종 결과 (신뢰도: {final_data.confidence:.1%})")
        print("=" * 60)
        self.print_final_result(final_data)
        
        return final_data
    
    def extract_from_naver_advanced(self, symbol: str) -> Optional[StockData]:
        """네이버 증권에서 고도화된 데이터 추출"""
        
        print("🔍 네이버 증권 고도화 추출 중...")
        
        try:
            url = f'https://finance.naver.com/item/main.naver?code={symbol}'
            
            # 여러 번 시도 (네트워크 안정성)
            for attempt in range(3):
                try:
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    break
                except Exception as e:
                    if attempt == 2:
                        logging.error(f"네이버 접속 실패: {e}")
                        return None
                    time.sleep(1)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            data = StockData(symbol=symbol)
            extraction_details = {}
            
            # 회사명 추출 (여러 방법)
            company_name = self._extract_company_name_naver(soup)
            data.company_name = company_name
            extraction_details['company_name_method'] = 'multiple_selectors'
            
            # 현재가 추출 (다중 전략)
            current_price, price_method = self._extract_current_price_naver(soup)
            if current_price:
                data.current_price = current_price
                extraction_details['price_method'] = price_method
            else:
                print("❌ 네이버 현재가 추출 실패")
                return None
            
            # 전일대비/등락률 추출
            change, change_percent, change_method = self._extract_change_naver(soup)
            data.change = change
            data.change_percent = change_percent
            extraction_details['change_method'] = change_method
            
            # 거래량 추출 (스마트 다중 전략)
            volume, volume_method = self._extract_volume_naver(soup, current_price)
            data.volume = volume
            extraction_details['volume_method'] = volume_method
            
            # 거래대금 추출
            trading_value, trading_method = self._extract_trading_value_naver(soup)
            data.trading_value = trading_value
            extraction_details['trading_method'] = trading_method
            
            # 시가총액 추출
            market_cap = self._extract_market_cap_naver(soup)
            data.market_cap = market_cap
            
            # 52주 최고/최저가
            high_52w, low_52w = self._extract_52w_range_naver(soup)
            data.high_52w = high_52w
            data.low_52w = low_52w
            
            # 외국인지분율
            foreign_ratio = self._extract_foreign_ratio_naver(soup)
            data.foreign_ratio = foreign_ratio
            
            data.source = "naver_advanced"
            data.extraction_details = extraction_details
            
            print("✅ 네이버 고도화 추출 완료")
            print(f"   현재가: {data.current_price:,}원 ({price_method})")
            print(f"   거래량: {data.volume:,}주 ({volume_method})")
            
            return data
            
        except Exception as e:
            logging.error(f"❌ 네이버 고도화 추출 실패: {e}")
            return None
    
    def _extract_company_name_naver(self, soup: BeautifulSoup) -> str:
        """회사명 추출 - 다중 선택자"""
        selectors = [
            '.wrap_company h2',
            '.h_company',
            '.name_company',
            'h2[class*="company"]'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)
            except:
                continue
        
        return "Unknown"
    
    def _extract_current_price_naver(self, soup: BeautifulSoup) -> Tuple[Optional[float], str]:
        """현재가 추출 - 다중 전략"""
        
        # 전략 1: 메인 표시 영역
        try:
            price_element = soup.select_one('.today .blind')
            if price_element:
                price_text = price_element.get_text(strip=True).replace(',', '')
                return float(price_text), "main_today_blind"
        except:
            pass
        
        # 전략 2: no_today 클래스
        try:
            price_element = soup.select_one('p.no_today')
            if price_element:
                price_text = price_element.get_text(strip=True).replace(',', '')
                # 숫자만 추출
                price_match = re.search(r'(\d+(?:,\d{3})*)', price_text)
                if price_match:
                    return float(price_match.group(1).replace(',', '')), "no_today_class"
        except:
            pass
        
        # 전략 3: 큰 숫자 패턴 찾기
        try:
            # 가격 범위에 맞는 숫자 찾기 (1,000 ~ 1,000,000)
            all_text = soup.get_text()
            price_patterns = re.findall(r'(\d{1,3}(?:,\d{3})*)', all_text)
            
            for pattern in price_patterns:
                price = float(pattern.replace(',', ''))
                if 1000 <= price <= 1000000:  # 합리적인 주가 범위
                    return price, "pattern_matching"
        except:
            pass
        
        # 전략 4: 테이블에서 현재가 찾기
        try:
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        if '현재가' in cell.get_text():
                            # 다음 셀에서 가격 찾기
                            if i + 1 < len(cells):
                                price_text = cells[i + 1].get_text(strip=True).replace(',', '')
                                price_match = re.search(r'(\d+)', price_text)
                                if price_match:
                                    return float(price_match.group(1)), "table_search"
        except:
            pass
        
        return None, "failed"
    
    def _extract_change_naver(self, soup: BeautifulSoup) -> Tuple[float, float, str]:
        """전일대비/등락률 추출"""
        
        change = 0.0
        change_percent = 0.0
        method = "unknown"
        
        try:
            # 방법 1: today 영역에서 추출
            today_section = soup.select_one('.today')
            if today_section:
                # 전일대비
                change_elements = today_section.select('.change')
                if change_elements:
                    change_text = change_elements[0].get_text(strip=True)
                    change_match = re.search(r'([+-]?)([\d,]+)', change_text)
                    if change_match:
                        sign = change_match.group(1)
                        value = float(change_match.group(2).replace(',', ''))
                        change = value if sign != '-' else -value
                
                # 등락률
                rate_elements = today_section.select('.rate')
                if rate_elements:
                    rate_text = rate_elements[0].get_text(strip=True)
                    rate_text = rate_text.replace('%', '').replace('+', '')
                    try:
                        change_percent = float(rate_text)
                    except:
                        pass
                
                method = "today_section"
        except:
            pass
        
        # 방법 2: 패턴 매칭으로 백업
        if change == 0 or change_percent == 0:
            try:
                all_text = soup.get_text()
                
                # 전일대비 패턴
                change_patterns = re.findall(r'전일대비[:\s]*([+-]?[\d,]+)', all_text)
                if change_patterns:
                    change_text = change_patterns[0].replace(',', '')
                    if change_text.startswith('+'):
                        change = float(change_text[1:])
                    elif change_text.startswith('-'):
                        change = -float(change_text[1:])
                    else:
                        change = float(change_text)
                
                # 등락률 패턴
                rate_patterns = re.findall(r'([+-]?\d+\.\d+)%', all_text)
                if rate_patterns:
                    change_percent = float(rate_patterns[0])
                
                if method == "unknown":
                    method = "pattern_matching"
            except:
                pass
        
        return change, change_percent, method
    
    def _extract_volume_naver(self, soup: BeautifulSoup, current_price: float) -> Tuple[int, str]:
        """거래량 추출 - 스마트 다중 전략"""
        
        candidates = []
        
        # 전략 1: ID 기반 검색
        try:
            volume_element = soup.find(id='_volume')
            if volume_element:
                volume_text = volume_element.get_text(strip=True).replace(',', '')
                volume = int(volume_text)
                candidates.append((volume, "id_volume", 100))
        except:
            pass
        
        # 전략 2: 테이블에서 거래량 검색
        try:
            tables = soup.find_all('table')
            for table_idx, table in enumerate(tables):
                table_text = table.get_text()
                if '거래량' in table_text:
                    # 거래량 패턴 찾기
                    volume_patterns = re.findall(r'거래량[:\s]*([0-9,]+)', table_text)
                    for pattern in volume_patterns:
                        volume = int(pattern.replace(',', ''))
                        candidates.append((volume, f"table_{table_idx}", 90))
        except:
            pass
        
        # 전략 3: 모든 숫자 패턴에서 합리적인 거래량 찾기
        try:
            all_text = soup.get_text()
            number_patterns = re.findall(r'(\d{1,3}(?:,\d{3})*)', all_text)
            
            for pattern in number_patterns:
                volume = int(pattern.replace(',', ''))
                
                # 거래량 합리성 검증
                if self._is_reasonable_volume(volume, current_price):
                    candidates.append((volume, "pattern_reasonable", 80))
        except:
            pass
        
        # 전략 4: 거래량 키워드 근처에서 찾기
        try:
            all_text = soup.get_text()
            volume_sections = re.split(r'거래량', all_text)
            
            for section in volume_sections[1:]:  # 거래량 이후 텍스트들
                numbers = re.findall(r'(\d{1,3}(?:,\d{3})*)', section[:100])  # 근처 100자만
                for number in numbers:
                    volume = int(number.replace(',', ''))
                    if 1000 <= volume <= 100000000:  # 합리적 범위
                        candidates.append((volume, "keyword_proximity", 70))
                        break
        except:
            pass
        
        # 후보 중 최적값 선택
        if candidates:
            # 점수순으로 정렬
            candidates.sort(key=lambda x: x[2], reverse=True)
            
            # 최고 점수 그룹에서 중간값 선택 (이상치 제거)
            top_score = candidates[0][2]
            top_candidates = [c for c in candidates if c[2] == top_score]
            
            if len(top_candidates) == 1:
                return top_candidates[0][0], top_candidates[0][1]
            else:
                # 여러 후보가 있으면 중간값 선택
                volumes = [c[0] for c in top_candidates]
                volumes.sort()
                median_volume = volumes[len(volumes) // 2]
                for candidate in top_candidates:
                    if candidate[0] == median_volume:
                        return candidate[0], f"{candidate[1]}_median"
        
        return 0, "failed"
    
    def _is_reasonable_volume(self, volume: int, current_price: float) -> bool:
        """거래량 합리성 검증"""
        
        # 기본 범위 체크
        if not (1000 <= volume <= 100000000):
            return False
        
        # 거래대금 기반 검증 (대략적)
        if current_price > 0:
            trading_value_estimate = volume * current_price / 100000000  # 억원
            if trading_value_estimate > 10000:  # 1조원 이상은 비현실적
                return False
        
        return True
    
    def _extract_trading_value_naver(self, soup: BeautifulSoup) -> Tuple[float, str]:
        """거래대금 추출"""
        
        try:
            all_text = soup.get_text()
            
            # 패턴 1: 거래대금 XXX백만
            pattern1 = re.search(r'거래대금[:\s]*([0-9,]+)\s*백만', all_text)
            if pattern1:
                value = float(pattern1.group(1).replace(',', ''))
                return value / 100, "pattern_million"  # 백만 → 억
            
            # 패턴 2: 거래대금 XXX억
            pattern2 = re.search(r'거래대금[:\s]*([0-9,]+)\s*억', all_text)
            if pattern2:
                value = float(pattern2.group(1).replace(',', ''))
                return value, "pattern_billion"
            
        except:
            pass
        
        return 0.0, "failed"
    
    def _extract_market_cap_naver(self, soup: BeautifulSoup) -> str:
        """시가총액 추출"""
        
        try:
            all_text = soup.get_text()
            market_cap_match = re.search(r'시가총액[:\s]*([0-9,조억만\s]+)', all_text)
            if market_cap_match:
                return market_cap_match.group(1).strip()
        except:
            pass
        
        return ""
    
    def _extract_52w_range_naver(self, soup: BeautifulSoup) -> Tuple[float, float]:
        """52주 최고/최저가 추출"""
        
        high_52w = 0.0
        low_52w = 0.0
        
        try:
            all_text = soup.get_text()
            
            # 52주 최고가
            high_patterns = [
                r'52주\s*최고[:\s]*([0-9,]+)',
                r'최고가[:\s]*([0-9,]+)',
            ]
            
            for pattern in high_patterns:
                match = re.search(pattern, all_text)
                if match:
                    high_52w = float(match.group(1).replace(',', ''))
                    break
            
            # 52주 최저가
            low_patterns = [
                r'52주\s*최저[:\s]*([0-9,]+)',
                r'최저가[:\s]*([0-9,]+)',
            ]
            
            for pattern in low_patterns:
                match = re.search(pattern, all_text)
                if match:
                    low_52w = float(match.group(1).replace(',', ''))
                    break
            
        except:
            pass
        
        return high_52w, low_52w
    
    def _extract_foreign_ratio_naver(self, soup: BeautifulSoup) -> float:
        """외국인지분율 추출"""
        
        try:
            all_text = soup.get_text()
            foreign_match = re.search(r'외국인[^0-9]*([0-9.]+)%', all_text)
            if foreign_match:
                return float(foreign_match.group(1))
        except:
            pass
        
        return 0.0
    
    def extract_from_daum_advanced(self, symbol: str) -> Optional[StockData]:
        """다음 증권에서 고도화된 데이터 추출"""
        
        print("🔍 다음 증권 고도화 추출 중...")
        
        try:
            url = f'https://finance.daum.net/quotes/A{symbol}'
            
            # 여러 번 시도
            for attempt in range(3):
                try:
                    response = self.session.get(url, timeout=10)
                    response.raise_for_status()
                    break
                except Exception as e:
                    if attempt == 2:
                        logging.error(f"다음 접속 실패: {e}")
                        return None
                    time.sleep(1)
            
            soup = BeautifulSoup(response.content, 'html.parser')
            data = StockData(symbol=symbol)
            
            # 현재가 추출
            current_price = self._extract_current_price_daum(soup)
            if current_price:
                data.current_price = current_price
            else:
                print("❌ 다음 현재가 추출 실패")
                return None
            
            # 전일대비/등락률
            change, change_percent = self._extract_change_daum(soup)
            data.change = change
            data.change_percent = change_percent
            
            # 거래량
            volume = self._extract_volume_daum(soup)
            data.volume = volume
            
            data.source = "daum_advanced"
            
            print("✅ 다음 고도화 추출 완료")
            print(f"   현재가: {data.current_price:,}원, 거래량: {data.volume:,}주")
            
            return data
            
        except Exception as e:
            logging.error(f"❌ 다음 고도화 추출 실패: {e}")
            return None
    
    def _extract_current_price_daum(self, soup: BeautifulSoup) -> Optional[float]:
        """다음 현재가 추출"""
        
        selectors = [
            '.price',
            '.txt_price',
            '[class*="price"]'
        ]
        
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    price_text = element.get_text(strip=True).replace(',', '').replace('원', '')
                    return float(price_text)
            except:
                continue
        
        return None
    
    def _extract_change_daum(self, soup: BeautifulSoup) -> Tuple[float, float]:
        """다음 전일대비/등락률 추출"""
        
        change = 0.0
        change_percent = 0.0
        
        try:
            # rate 클래스에서 추출
            rate_elements = soup.select('.rate')
            if len(rate_elements) >= 2:
                # 전일대비
                change_text = rate_elements[0].get_text(strip=True)
                change_match = re.search(r'([+-]?)([\d,]+)', change_text)
                if change_match:
                    sign = change_match.group(1)
                    value = float(change_match.group(2).replace(',', ''))
                    change = value if sign != '-' else -value
                
                # 등락률
                rate_text = rate_elements[1].get_text(strip=True).replace('%', '').replace('+', '')
                change_percent = float(rate_text)
        except:
            pass
        
        return change, change_percent
    
    def _extract_volume_daum(self, soup: BeautifulSoup) -> int:
        """다음 거래량 추출"""
        
        try:
            # 거래량 테이블 검색
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        if '거래량' in cell.get_text():
                            if i + 1 < len(cells):
                                volume_text = cells[i + 1].get_text(strip=True).replace(',', '').replace('주', '')
                                return int(volume_text)
        except:
            pass
        
        # 패턴 매칭 백업
        try:
            all_text = soup.get_text()
            volume_match = re.search(r'거래량[:\s]*([0-9,]+)', all_text)
            if volume_match:
                return int(volume_match.group(1).replace(',', ''))
        except:
            pass
        
        return 0
    
    def cross_validate_advanced(self, naver_data: Optional[StockData], daum_data: Optional[StockData], symbol: str) -> StockData:
        """고도화된 교차검증"""
        
        print("\n🔍 고도화된 교차검증 분석 중...")
        
        # 둘 다 실패한 경우
        if not naver_data and not daum_data:
            print("❌ 모든 소스에서 데이터 추출 실패")
            return StockData(symbol=symbol, source="failed", confidence=0.0)
        
        # 한쪽만 성공한 경우
        if naver_data and not daum_data:
            print("⚠️ 다음 데이터 없음, 네이버 데이터만 사용")
            confidence = 0.75 if naver_data.current_price > 0 else 0.3
            naver_data.confidence = confidence
            return naver_data
        
        if daum_data and not naver_data:
            print("⚠️ 네이버 데이터 없음, 다음 데이터만 사용")
            confidence = 0.7 if daum_data.current_price > 0 else 0.3
            daum_data.confidence = confidence
            return daum_data
        
        # 둘 다 성공한 경우 - 고도화된 교차검증
        print("✅ 양쪽 데이터 모두 확보, 고도화된 교차검증 진행")
        
        # 핵심 데이터 비교 분석
        analysis = self._detailed_comparison(naver_data, daum_data)
        
        # 최종 데이터 구성
        final_data = self._construct_final_data(naver_data, daum_data, analysis, symbol)
        
        return final_data
    
    def _detailed_comparison(self, naver_data: StockData, daum_data: StockData) -> Dict:
        """상세 비교 분석"""
        
        analysis = {}
        
        # 현재가 비교
        if naver_data.current_price > 0 and daum_data.current_price > 0:
            price_diff = abs(naver_data.current_price - daum_data.current_price)
            price_diff_percent = price_diff / naver_data.current_price * 100
            analysis['price_diff'] = price_diff
            analysis['price_diff_percent'] = price_diff_percent
            analysis['price_consistent'] = price_diff_percent < 1.0
        else:
            analysis['price_consistent'] = False
        
        # 거래량 비교
        if naver_data.volume > 0 and daum_data.volume > 0:
            volume_diff = abs(naver_data.volume - daum_data.volume)
            volume_diff_percent = volume_diff / max(naver_data.volume, daum_data.volume) * 100
            analysis['volume_diff'] = volume_diff
            analysis['volume_diff_percent'] = volume_diff_percent
            analysis['volume_consistent'] = volume_diff_percent < 15.0
        else:
            analysis['volume_consistent'] = False
        
        # 전일대비 비교
        if naver_data.change != 0 and daum_data.change != 0:
            change_diff = abs(naver_data.change - daum_data.change)
            analysis['change_consistent'] = change_diff < 100  # 100원 이내
        else:
            analysis['change_consistent'] = False
        
        # 등락률 비교
        if naver_data.change_percent != 0 and daum_data.change_percent != 0:
            rate_diff = abs(naver_data.change_percent - daum_data.change_percent)
            analysis['rate_consistent'] = rate_diff < 0.5  # 0.5% 이내
        else:
            analysis['rate_consistent'] = False
        
        print(f"📊 상세 비교 분석:")
        if 'price_diff' in analysis:
            print(f"   현재가 차이: {analysis['price_diff']:,.0f}원 ({analysis['price_diff_percent']:.2f}%) - {'✅' if analysis['price_consistent'] else '⚠️'}")
        if 'volume_diff' in analysis:
            print(f"   거래량 차이: {analysis['volume_diff']:,}주 ({analysis['volume_diff_percent']:.2f}%) - {'✅' if analysis['volume_consistent'] else '⚠️'}")
        
        return analysis
    
    def _construct_final_data(self, naver_data: StockData, daum_data: StockData, analysis: Dict, symbol: str) -> StockData:
        """최종 데이터 구성"""
        
        final_data = StockData(symbol=symbol)
        
        # 신뢰도 계산
        confidence = 1.0
        consistent_count = 0
        total_checks = 0
        
        for key in ['price_consistent', 'volume_consistent', 'change_consistent', 'rate_consistent']:
            if key in analysis:
                total_checks += 1
                if analysis[key]:
                    consistent_count += 1
                else:
                    confidence -= 0.15
        
        # 기본 신뢰도 보정
        if total_checks > 0:
            consistency_ratio = consistent_count / total_checks
            confidence = max(0.5, min(1.0, confidence * (0.7 + 0.3 * consistency_ratio)))
        
        # 회사명 (네이버 우선)
        final_data.company_name = naver_data.company_name or daum_data.company_name
        
        # 현재가 (일치성에 따라 결정)
        if analysis.get('price_consistent', False):
            final_data.current_price = round((naver_data.current_price + daum_data.current_price) / 2)
            print("📊 현재가: 평균값 사용 (일치성 양호)")
        elif naver_data.current_price > 0:
            final_data.current_price = naver_data.current_price
            print("📊 현재가: 네이버 데이터 우선 사용")
        else:
            final_data.current_price = daum_data.current_price
            print("📊 현재가: 다음 데이터 사용")
        
        # 거래량 (더 신뢰할 만한 값 선택)
        if analysis.get('volume_consistent', False):
            final_data.volume = int((naver_data.volume + daum_data.volume) / 2)
            print("📊 거래량: 평균값 사용 (일치성 양호)")
        elif naver_data.volume > 0 and daum_data.volume > 0:
            # 더 합리적인 값 선택 (현재가 기준 거래대금 검증)
            naver_trading_est = naver_data.volume * final_data.current_price / 100000000
            daum_trading_est = daum_data.volume * final_data.current_price / 100000000
            
            # 50억~5000억 범위 내에서 선택
            if 50 <= naver_trading_est <= 5000:
                final_data.volume = naver_data.volume
                print("📊 거래량: 네이버 데이터 사용 (합리성 검증)")
            elif 50 <= daum_trading_est <= 5000:
                final_data.volume = daum_data.volume
                print("📊 거래량: 다음 데이터 사용 (합리성 검증)")
            else:
                final_data.volume = min(naver_data.volume, daum_data.volume)
                print("📊 거래량: 최소값 사용 (보수적 선택)")
        elif naver_data.volume > 0:
            final_data.volume = naver_data.volume
            print("📊 거래량: 네이버 데이터만 사용")
        else:
            final_data.volume = daum_data.volume
            print("📊 거래량: 다음 데이터만 사용")
        
        # 나머지 데이터는 네이버 우선 (더 풍부한 정보)
        final_data.change = naver_data.change or daum_data.change
        final_data.change_percent = naver_data.change_percent or daum_data.change_percent
        final_data.trading_value = naver_data.trading_value or daum_data.trading_value
        final_data.market_cap = naver_data.market_cap or daum_data.market_cap
        final_data.high_52w = naver_data.high_52w or daum_data.high_52w
        final_data.low_52w = naver_data.low_52w or daum_data.low_52w
        final_data.foreign_ratio = naver_data.foreign_ratio or daum_data.foreign_ratio
        
        final_data.source = "cross_validated_advanced"
        final_data.confidence = confidence
        
        # 신뢰도 평가
        if confidence >= 0.9:
            print("🏆 높은 신뢰도 - 데이터 일치성 우수")
        elif confidence >= 0.8:
            print("✅ 양호한 신뢰도 - 데이터 신뢰 가능")
        elif confidence >= 0.7:
            print("⚠️ 보통 신뢰도 - 일부 불일치 존재")
        else:
            print("🚨 낮은 신뢰도 - 추가 검증 필요")
        
        return final_data
    
    def print_final_result(self, data: StockData):
        """최종 결과 출력"""
        
        status_emoji = "🏆" if data.confidence >= 0.9 else "✅" if data.confidence >= 0.8 else "⚠️" if data.confidence >= 0.7 else "🚨"
        
        print(f"""
{status_emoji} {data.company_name} ({data.symbol}) - {data.source}

💰 실시간 주가 정보:
   현재가: {data.current_price:,}원
   전일대비: {data.change:+,}원 ({data.change_percent:+.2f}%)
   거래량: {data.volume:,}주
   거래대금: {data.trading_value:.0f}억원

📈 추가 정보:
   시가총액: {data.market_cap}
   52주 최고: {data.high_52w:,}원
   52주 최저: {data.low_52w:,}원
   외국인지분율: {data.foreign_ratio:.2f}%

🎯 신뢰도: {data.confidence:.1%}
        """)

# 사용 예시
def main():
    """메인 실행 함수"""
    
    extractor = AdvancedStockExtractor()
    
    try:
        # 종목 코드 입력
        symbol = input("종목코드를 입력하세요 (예: 047810): ").strip()
        
        if not symbol:
            print("❌ 종목코드를 입력해주세요.")
            return
        
        # 데이터 추출
        result = extractor.extract_stock_data(symbol)
        
        if result.confidence > 0:
            print(f"\n🎉 추출 성공! 신뢰도: {result.confidence:.1%}")
            
            # 상세 정보 (옵션)
            if hasattr(result, 'extraction_details') and result.extraction_details:
                print(f"\n🔧 추출 방법 상세:")
                for key, value in result.extraction_details.items():
                    print(f"   {key}: {value}")
        else:
            print("\n❌ 데이터 추출에 실패했습니다.")
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")

if __name__ == "__main__":
    main()
