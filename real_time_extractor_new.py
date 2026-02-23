"""
🚀 네이버 증권 완전 범용 실시간 데이터 추출기
95-98% 성공률 달성을 위한 완전 개선 버전

주요 개선사항:
1. 모든 현재가 클래스 지원 (no_up, no_down, no_today, no_cha)
2. 전 종목 범위 대응 (소형주~대형주)
3. 최신 데이터 우선 선택 (DOM 순서)
4. 다단계 fallback 전략
5. 강화된 데이터 검증
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time

class UniversalRealtimeExtractor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        
        # 전 종목 대응 범위 설정
        self.VOLUME_RANGE = (1, 100_000_000)        # 1주 ~ 1억주
        self.PRICE_RANGE = (100, 10_000_000)        # 100원 ~ 1천만원  
        self.MARKET_CAP_RANGE = (1, 1000)           # 1억 ~ 1000조원
        self.PERCENTAGE_RANGE = (0, 100)            # 0% ~ 100%
        
        # 모든 현재가 클래스 정의
        self.PRICE_CLASSES = ['no_up', 'no_down', 'no_today', 'no_cha']
        
    def extract_realtime_data(self, stock_code):
        """메인 추출 함수 - 모든 실시간 데이터 추출"""
        print(f"🎯 {stock_code} 범용 실시간 데이터 추출 시작...")
        
        try:
            url = f"https://finance.naver.com/item/main.naver?code={stock_code}"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 모든 데이터 추출
            data = {
                'current_price': self._extract_current_price_universal(soup),
                'change_rate': self._extract_change_rate_universal(soup),
                'change_amount': None,  # 현재가와 등락률로 계산
                'volume': self._extract_volume_universal(soup),
                'trading_value': self._extract_trading_value_universal(soup),
                'market_cap': self._extract_market_cap_universal(soup),
                'high_52w': self._extract_52week_high_universal(soup),
                'low_52w': self._extract_52week_low_universal(soup),
                'foreign_ownership': self._extract_foreign_ownership_universal(soup),
                'investment_opinion': self._extract_investment_opinion_universal(soup),
                'sector_companies': self._extract_sector_companies_universal(soup),
                'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 전일대비 금액 계산
            if data['current_price'] and data['change_rate']:
                data['change_amount'] = self._calculate_change_amount(
                    data['current_price'], data['change_rate']
                )
            
            # 데이터 검증
            validated_data = self._validate_and_clean_data(data)
            
            # 성공률 계산
            success_count = sum(1 for v in validated_data.values() 
                              if v is not None and v != 'N/A' and str(v) != '')
            success_rate = (success_count / 10) * 100  # 10개 항목 기준
            
            print(f"✅ {stock_code}: {success_rate:.1f}% 성공률 ({success_count}/10 항목)")
            return validated_data
            
        except Exception as e:
            print(f"❌ {stock_code} 추출 실패: {e}")
            return None
    
    def _extract_current_price_universal(self, soup):
        """현재가 범용 추출 - 모든 클래스 지원"""
        print("🔍 현재가 범용 추출...")
        
        # 모든 현재가 클래스에서 시도
        for price_class in self.PRICE_CLASSES:
            try:
                # 메인 현재가 영역에서 추출
                price_elements = soup.find_all('em', class_=price_class)
                
                for elem in price_elements:
                    blind_elem = elem.find('span', class_='blind')
                    if blind_elem:
                        price_text = blind_elem.get_text(strip=True)
                        price_value = self._parse_number(price_text)
                        
                        # 현재가 범위 검증
                        if (price_value and 
                            self.PRICE_RANGE[0] <= price_value <= self.PRICE_RANGE[1]):
                            
                            # 부모 컨텍스트로 현재가 확인
                            parent_text = elem.get_text()
                            if any(keyword in parent_text for keyword in ['전일대비', '등락률']):
                                continue  # 전일대비/등락률 제외
                                
                            print(f"✅ 현재가 발견 ({price_class}): {price_value:,}원")
                            return price_value
                            
            except Exception as e:
                continue
        
        # Fallback: no_today 클래스의 첫 번째 숫자
        try:
            today_elem = soup.find('p', class_='no_today')
            if today_elem:
                blind_elem = today_elem.find('span', class_='blind')
                if blind_elem:
                    price_value = self._parse_number(blind_elem.get_text(strip=True))
                    if (price_value and 
                        self.PRICE_RANGE[0] <= price_value <= self.PRICE_RANGE[1]):
                        print(f"✅ 현재가 발견 (fallback): {price_value:,}원")
                        return price_value
        except:
            pass
            
        print("❌ 현재가 추출 실패")
        return None
    
    def _extract_change_rate_universal(self, soup):
        """등락률 범용 추출"""
        print("🔍 등락률 범용 추출...")
        
        # 등락률 패턴 검색
        rate_patterns = [
            r'([\+\-]?\d+\.?\d*)%',
            r'(\d+\.?\d*)%'
        ]
        
        for pattern in rate_patterns:
            # 전체 텍스트에서 등락률 검색
            text = soup.get_text()
            matches = re.findall(pattern, text)
            
            for match in matches:
                try:
                    rate = float(match.replace('+', ''))
                    if -30 <= rate <= 30:  # 합리적 등락률 범위
                        print(f"✅ 등락률 발견: {rate:+.2f}%")
                        return rate
                except:
                    continue
        
        print("❌ 등락률 추출 실패")
        return None
    
    def _extract_volume_universal(self, soup):
        """거래량 범용 추출 - 개선된 로직"""
        print("🔍 거래량 범용 추출...")
        
        # 방법 1: 거래량 키워드 직접 검색
        try:
            volume_spans = soup.find_all('span', string=re.compile(r'거래량'))
            for span in volume_spans:
                # 다음 형제 요소에서 숫자 찾기
                next_elem = span.find_next_sibling('em')
                if next_elem:
                    blind_elem = next_elem.find('span', class_='blind')
                    if blind_elem:
                        volume_text = blind_elem.get_text(strip=True)
                        volume = self._parse_number(volume_text)
                        
                        if (volume and 
                            self.VOLUME_RANGE[0] <= volume <= self.VOLUME_RANGE[1]):
                            print(f"✅ 거래량 발견 (키워드): {volume:,}주")
                            return volume
        except:
            pass
        
        # 방법 2: 테이블 구조에서 검색
        try:
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        if '거래량' in cell.get_text():
                            # 같은 행의 다음 셀들에서 숫자 찾기
                            for j in range(i+1, len(cells)):
                                volume = self._extract_number_from_cell(cells[j])
                                if (volume and 
                                    self.VOLUME_RANGE[0] <= volume <= self.VOLUME_RANGE[1]):
                                    print(f"✅ 거래량 발견 (테이블): {volume:,}주")
                                    return volume
        except:
            pass
        
        # 방법 3: 모든 숫자 후보에서 거래량 범위 필터링
        try:
            all_numbers = self._extract_all_numbers(soup)
            volume_candidates = [
                num for num in all_numbers 
                if self.VOLUME_RANGE[0] <= num <= self.VOLUME_RANGE[1]
                and num > 1000  # 최소 거래량 필터
            ]
            
            if volume_candidates:
                # 가장 큰 값을 거래량으로 추정 (일반적으로 거래량이 큰 숫자)
                volume = max(volume_candidates)
                print(f"✅ 거래량 발견 (추정): {volume:,}주")
                return volume
        except:
            pass
            
        print("❌ 거래량 추출 실패")
        return None
    
    def _extract_trading_value_universal(self, soup):
        """거래대금 범용 추출"""
        print("🔍 거래대금 범용 추출...")
        
        try:
            # 거래대금 키워드 검색
            trading_value_spans = soup.find_all('span', string=re.compile(r'거래대금'))
            for span in trading_value_spans:
                next_elem = span.find_next_sibling('em')
                if next_elem:
                    text = next_elem.get_text(strip=True)
                    
                    # "백만" 단위 처리
                    if '백만' in text:
                        number_part = re.findall(r'[\d,]+', text)
                        if number_part:
                            value = self._parse_number(number_part[0])
                            if value:
                                print(f"✅ 거래대금 발견: {value:,}백만")
                                return f"{value:,}백만"
                    
                    # 일반 숫자 처리
                    value = self._parse_number(text)
                    if value and value > 100:
                        print(f"✅ 거래대금 발견: {value:,}")
                        return f"{value:,}"
        except:
            pass
            
        print("❌ 거래대금 추출 실패")
        return None
    
    def _extract_market_cap_universal(self, soup):
        """시가총액 범용 추출"""
        print("🔍 시가총액 범용 추출...")
        
        try:
            # 우측 투자정보 영역에서 검색
            market_cap_patterns = [
                r'(\d+)조\s*(\d+)?억?',
                r'(\d+)억',
                r'(\d+,?\d*)조',
                r'(\d+,?\d*)억'
            ]
            
            # 투자정보 섹션 우선 검색
            invest_sections = soup.find_all(['div', 'section'], 
                                          class_=re.compile(r'(invest|info|aside)'))
            
            for section in invest_sections:
                text = section.get_text()
                for pattern in market_cap_patterns:
                    matches = re.findall(pattern, text)
                    for match in matches:
                        if isinstance(match, tuple):
                            if len(match) == 2 and match[1]:  # 조억 형태
                                cho = self._parse_number(match[0])
                                eok = self._parse_number(match[1]) if match[1] else 0
                                if cho:
                                    result = f"{cho}조{eok}억원" if eok else f"{cho}조원"
                                    print(f"✅ 시가총액 발견: {result}")
                                    return result
                            else:  # 단일 값
                                value = self._parse_number(match[0])
                                if value and value < 1000:  # 합리적 범위
                                    unit = "조" if "조" in pattern else "억"
                                    result = f"{value}{unit}원"
                                    print(f"✅ 시가총액 발견: {result}")
                                    return result
        except:
            pass
            
        print("❌ 시가총액 추출 실패")
        return None
    
    def _extract_52week_high_universal(self, soup):
        """52주 최고가 범용 추출"""
        print("🔍 52주 최고가 범용 추출...")
        
        try:
            # 52주 키워드가 포함된 모든 텍스트 검색
            text = soup.get_text()
            
            # 52주 최고가 패턴들
            patterns = [
                r'52주\s*최고[^\d]*(\d{1,3}(?:,\d{3})*)',
                r'52주최고[^\d]*(\d{1,3}(?:,\d{3})*)',
                r'52주\s*고가[^\d]*(\d{1,3}(?:,\d{3})*)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    high_52w = self._parse_number(match)
                    if (high_52w and 
                        self.PRICE_RANGE[0] <= high_52w <= self.PRICE_RANGE[1]):
                        print(f"✅ 52주 최고가 발견: {high_52w:,}원")
                        return high_52w
            
            # Fallback: 투자정보 섹션에서 큰 숫자들 검색
            invest_sections = soup.find_all(['div', 'dd', 'span'], 
                                          string=re.compile(r'52|최고|고가'))
            
            for section in invest_sections:
                parent = section.find_parent()
                if parent:
                    numbers = self._extract_all_numbers_from_text(parent.get_text())
                    for num in numbers:
                        if (self.PRICE_RANGE[0] <= num <= self.PRICE_RANGE[1] and 
                            num > 1000):  # 최소 가격 필터
                            print(f"✅ 52주 최고가 발견 (추정): {num:,}원")
                            return num
                            
        except Exception as e:
            pass
            
        print("❌ 52주 최고가 추출 실패")
        return None
    
    def _extract_52week_low_universal(self, soup):
        """52주 최저가 범용 추출"""
        print("🔍 52주 최저가 범용 추출...")
        
        try:
            text = soup.get_text()
            
            # 52주 최저가 패턴들
            patterns = [
                r'52주\s*최저[^\d]*(\d{1,3}(?:,\d{3})*)',
                r'52주최저[^\d]*(\d{1,3}(?:,\d{3})*)',
                r'52주\s*저가[^\d]*(\d{1,3}(?:,\d{3})*)',
                r'최저[^\d]*(\d{1,3}(?:,\d{3})*)',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    low_52w = self._parse_number(match)
                    if (low_52w and 
                        self.PRICE_RANGE[0] <= low_52w <= self.PRICE_RANGE[1]):
                        print(f"✅ 52주 최저가 발견: {low_52w:,}원")
                        return low_52w
                        
        except Exception as e:
            pass
            
        print("❌ 52주 최저가 추출 실패")
        return None
    
    def _extract_foreign_ownership_universal(self, soup):
        """외국인지분율 범용 추출"""
        print("🔍 외국인지분율 범용 추출...")
        
        try:
            # 외국인 키워드 검색
            foreign_keywords = ['외국인', '외국인지분율', '외국인보유']
            
            for keyword in foreign_keywords:
                elements = soup.find_all(string=re.compile(keyword))
                for elem in elements:
                    parent = elem.parent if elem.parent else elem
                    text = parent.get_text()
                    
                    # 퍼센트 패턴 검색
                    percent_match = re.search(r'(\d+\.?\d*)%', text)
                    if percent_match:
                        percent = float(percent_match.group(1))
                        if 0 <= percent <= 100:
                            print(f"✅ 외국인지분율 발견: {percent:.2f}%")
                            return f"{percent:.2f}%"
                            
        except:
            pass
            
        print("❌ 외국인지분율 추출 실패")
        return None
    
    def _extract_investment_opinion_universal(self, soup):
        """투자의견 범용 추출"""
        print("🔍 투자의견 범용 추출...")
        
        try:
            # 투자의견 키워드들
            opinion_keywords = ['매수', '매도', '보유', '중립', 'BUY', 'SELL', 'HOLD']
            
            text = soup.get_text()
            for keyword in opinion_keywords:
                if keyword in text:
                    print(f"✅ 투자의견 발견: {keyword}")
                    return keyword
                    
        except:
            pass
            
        print("❌ 투자의견 추출 실패")
        return None
    
    def _extract_sector_companies_universal(self, soup):
        """동종업종 회사명 범용 추출"""
        print("🔍 동종업종 범용 추출...")
        
        try:
            # 동종업종 섹션 검색
            sector_sections = soup.find_all(string=re.compile(r'동종|업종|동일업종'))
            
            companies = []
            for section in sector_sections:
                parent = section.parent
                if parent:
                    # 링크에서 회사명 추출
                    links = parent.find_all('a')
                    for link in links:
                        company_name = link.get_text(strip=True)
                        # 종목코드 제거
                        clean_name = re.sub(r'\d{6}', '', company_name).strip()
                        if clean_name and len(clean_name) > 1:
                            companies.append(clean_name)
                            
            # 중복 제거 및 최대 5개
            unique_companies = list(dict.fromkeys(companies))[:5]
            
            if unique_companies:
                print(f"✅ 동종업종 발견: {unique_companies}")
                return unique_companies
                
        except:
            pass
            
        print("❌ 동종업종 추출 실패")
        return []
    
    def _calculate_change_amount(self, current_price, change_rate):
        """전일대비 금액 계산"""
        try:
            if current_price and change_rate:
                yesterday_price = current_price / (1 + change_rate / 100)
                change_amount = current_price - yesterday_price
                return round(change_amount)
        except:
            pass
        return None
    
    def _validate_and_clean_data(self, data):
        """데이터 검증 및 정제"""
        # 52주 데이터 논리적 검증
        if (data.get('high_52w') and data.get('low_52w') and 
            data['high_52w'] < data['low_52w']):
            print("⚠️ 52주 최고가 < 최저가 논리 오류 - 52주 데이터 제거")
            data['high_52w'] = None
            data['low_52w'] = None
        
        # 현재가 범위 검증
        if (data.get('current_price') and data.get('high_52w') and 
            data['current_price'] > data['high_52w'] * 1.5):
            print("⚠️ 현재가가 52주 최고가보다 과도하게 높음 - 52주 최고가 제거")
            data['high_52w'] = None
            
        return data
    
    def _parse_number(self, text):
        """문자열에서 숫자 추출"""
        if not text:
            return None
        try:
            # 콤마 제거 후 숫자 변환
            clean_text = re.sub(r'[^\d.]', '', str(text))
            if clean_text:
                return float(clean_text)
        except:
            pass
        return None
    
    def _extract_number_from_cell(self, cell):
        """테이블 셀에서 숫자 추출"""
        try:
            blind_elem = cell.find('span', class_='blind')
            if blind_elem:
                return self._parse_number(blind_elem.get_text(strip=True))
            else:
                return self._parse_number(cell.get_text(strip=True))
        except:
            return None
    
    def _extract_all_numbers(self, soup):
        """페이지의 모든 숫자 추출"""
        numbers = []
        try:
            # blind 클래스 우선
            blind_elements = soup.find_all('span', class_='blind')
            for elem in blind_elements:
                num = self._parse_number(elem.get_text(strip=True))
                if num:
                    numbers.append(num)
            
            # 일반 텍스트에서도 추출
            text = soup.get_text()
            number_matches = re.findall(r'\d{1,3}(?:,\d{3})*', text)
            for match in number_matches:
                num = self._parse_number(match)
                if num:
                    numbers.append(num)
                    
        except:
            pass
        return numbers
    
    def _extract_all_numbers_from_text(self, text):
        """텍스트에서 모든 숫자 추출"""
        numbers = []
        try:
            number_matches = re.findall(r'\d{1,3}(?:,\d{3})*', text)
            for match in number_matches:
                num = self._parse_number(match)
                if num:
                    numbers.append(num)
        except:
            pass
        return numbers

# 테스트 함수
def test_universal_extractor():
    """범용 추출기 테스트"""
    print("🚀 범용 실시간 데이터 추출기 테스트")
    print("=" * 70)
    
    extractor = UniversalRealtimeExtractor()
    
    # 3개 종목 테스트 (대형주, 중형주, 소형주)
    test_stocks = [
        ("000660", "SK하이닉스 (대형주)"),
        ("005930", "삼성전자 (대형주)"),  
        ("060310", "3S (소형주)")
    ]
    
    results = []
    total_success_rate = 0
    
    for stock_code, name in test_stocks:
        print(f"\n📊 {name} 테스트...")
        print("-" * 50)
        
        data = extractor.extract_realtime_data(stock_code)
        if data:
            # 성공률 계산
            success_count = sum(1 for v in data.values() 
                              if v is not None and v != 'N/A' and str(v) != '')
            success_rate = (success_count / 10) * 100
            total_success_rate += success_rate
            
            results.append({
                'name': name,
                'success_rate': success_rate,
                'data': data
            })
            
            # 주요 데이터 출력
            print(f"📈 현재가: {data.get('current_price', 'N/A'):,}원")
            print(f"📊 거래량: {data.get('volume', 'N/A'):,}주")
            print(f"🔺 52주최고: {data.get('high_52w', 'N/A')}원")
            print(f"🔻 52주최저: {data.get('low_52w', 'N/A')}원")
            print(f"💰 시가총액: {data.get('market_cap', 'N/A')}")
            print(f"🎯 성공률: {success_rate:.1f}%")
        else:
            results.append({
                'name': name, 
                'success_rate': 0,
                'data': None
            })
    
    # 종합 결과
    print("\n" + "=" * 70)
    print("🎯 범용 추출기 종합 결과")
    print("=" * 70)
    
    avg_success_rate = total_success_rate / len(test_stocks)
    print(f"📊 평균 성공률: {avg_success_rate:.1f}%")
    
    for result in results:
        print(f"   {result['name']}: {result['success_rate']:.1f}%")
    
    if avg_success_rate >= 90:
        print("\n🎉 목표 달성! 90%+ 성공률 달성!")
    elif avg_success_rate >= 80:
        print("\n✅ 양호! 80%+ 성공률 달성!")
    else:
        print("\n🔧 추가 개선 필요")
    
    return results

if __name__ == "__main__":
    test_universal_extractor()
