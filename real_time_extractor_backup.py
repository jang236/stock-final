import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional, Any
from datetime import datetime


class UniversalRealTimeExtractor:
    """
    모든 상장기업에 범용적으로 적용되는 실시간 주가 데이터 추출기
    다양한 페이지 구조에 대응하는 다중 패턴 방식
    """

    def __init__(self):
        self.headers = {
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    def extract_real_time_data(self, stock_code: str) -> Dict[str, Any]:
        """
        범용 실시간 주가 데이터 추출

        Args:
            stock_code: 종목코드 (예: "005930", "060310")

        Returns:
            모든 종목에 적용 가능한 실시간 데이터
        """
        url = f"https://finance.naver.com/item/main.naver?code={stock_code}"

        print(f"🔍 {stock_code} 범용 실시간 데이터 추출 시작...")

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 회사명 추출
            company_name = self._extract_company_name(soup)

            result = {
                'stock_code': stock_code,
                'company_name': company_name,
                'real_time_data': {
                    'current_price': self._extract_current_price_universal(soup),
                    'change_amount': self._extract_change_amount_universal(soup),
                    'change_rate': self._extract_change_rate_universal(soup),
                    'volume': self._extract_volume_universal(soup),
                    'trading_value': self._extract_trading_value_universal(soup),
                    'market_cap': self._extract_market_cap_universal(soup),
                    'high_52w': self._extract_52week_high_universal(soup),
                    'low_52w': self._extract_52week_low_universal(soup),
                    'foreign_ownership': self._extract_foreign_ownership_universal(soup),
                    'investment_opinion': self._extract_investment_opinion_universal(soup),
                    'updated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                },
                'sector_comparison': self._extract_sector_comparison_universal(soup),
                'extraction_status': 'success'
            }

            # 데이터 검증 및 일관성 확인
            result = self._validate_universal_data(result)

            print(f"✅ 범용 실시간 데이터 추출 완료!")
            return result

        except Exception as e:
            print(f"❌ 데이터 추출 실패: {e}")
            return {
                'stock_code': stock_code,
                'extraction_status': 'failed',
                'error': str(e)
            }

    def _extract_company_name(self, soup: BeautifulSoup) -> Optional[str]:
        """회사명 추출 - 범용"""
        try:
            # 방법 1: title 태그
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                if ':' in title_text:
                    return title_text.split(':')[0].strip()

            # 방법 2: h2 태그
            h2_tags = soup.find_all('h2')
            for h2 in h2_tags:
                text = h2.get_text(strip=True)
                if text and len(text) < 20:
                    return text

            return None
        except:
            return None

    def _extract_current_price_universal(self, soup: BeautifulSoup) -> Optional[float]:
        """현재가 추출 - 범용 다중 패턴"""
        try:
            patterns = [
                # 패턴 1: 대형주 방식 (삼성전자 등)
                '.no_today .blind',
                # 패턴 2: 중소형주 방식 (3S 등)
                '.today .blind',
                # 패턴 3: 일반적인 blind 클래스
                'span.blind',
                # 패턴 4: 특정 영역의 em > span
                'p.no_today em span.blind'
            ]

            for pattern in patterns:
                elements = soup.select(pattern)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if text and ',' in text:
                        cleaned = text.replace(',', '')
                        if cleaned.isdigit():
                            value = float(cleaned)
                            # 현실적인 주가 범위 확인
                            if 100 <= value <= 10000000:
                                print(f"✅ 현재가 발견 (패턴: {pattern}): {value:,}원")
                                return value

            return None
        except:
            return None

    def _extract_change_amount_universal(self, soup: BeautifulSoup) -> Optional[float]:
        """전일대비 추출 - 범용 다중 패턴"""
        try:
            # 현재가에서 등락률을 이용해 역산하는 방법 우선 사용
            current_price = self._extract_current_price_universal(soup)
            change_rate = self._extract_change_rate_universal(soup)
            
            if current_price and change_rate:
                # 전일종가 = 현재가 / (1 + 등락률/100)
                previous_close = current_price / (1 + change_rate / 100)
                change_amount = current_price - previous_close
                print(f"✅ 전일대비 계산 (역산): {change_amount:+,.0f}원")
                return round(change_amount)

            # 직접 추출 방법들
            patterns = [
                '.no_exday',
                '.change_rate',
                'p.no_exday em span.blind'
            ]

            for pattern in patterns:
                elements = soup.select(pattern)
                for elem in elements:
                    text = elem.get_text()
                    
                    # ▼35 또는 ▲35 형태
                    if '▼' in text or '▲' in text:
                        sign = -1 if '▼' in text else 1
                        numbers = re.findall(r'[\d,]+', text)
                        if numbers:
                            try:
                                value = float(numbers[0].replace(',', '')) * sign
                                if abs(value) < 100000:  # 현실적인 변동폭
                                    print(f"✅ 전일대비 발견 (직접): {value:+,}원")
                                    return value
                            except:
                                continue

            return None
        except:
            return None

    def _extract_change_rate_universal(self, soup: BeautifulSoup) -> Optional[float]:
        """등락률 추출 - 범용 다중 패턴"""
        try:
            # %가 포함된 모든 텍스트에서 찾기
            percent_elements = soup.find_all(string=re.compile(r'[+-]?\d+\.\d+%'))
            for elem in percent_elements:
                rate_str = elem.strip().replace('%', '').replace('+', '')
                try:
                    rate = float(rate_str)
                    if abs(rate) < 50:  # 현실적인 등락률
                        print(f"✅ 등락률 발견: {rate:+.2f}%")
                        return rate
                except:
                    continue

            return None
        except:
            return None

    def _extract_volume_universal(self, soup: BeautifulSoup) -> Optional[int]:
        """거래량 추출 - 범용 다중 패턴"""
        try:
            # 방법 1: "거래량" 텍스트 기준으로 찾기
            volume_keywords = soup.find_all(string=re.compile(r'거래량'))
            for keyword in volume_keywords:
                parent = keyword.parent
                if parent:
                    # 주변 텍스트에서 큰 숫자 찾기
                    parent_text = parent.parent.get_text() if parent.parent else parent.get_text()
                    
                    # 쉼표가 포함된 6자리 이상의 숫자 찾기
                    numbers = re.findall(r'[\d,]+', parent_text)
                    for num in numbers:
                        if ',' in num:
                            cleaned = num.replace(',', '')
                            if cleaned.isdigit() and len(cleaned) >= 3:  # 3자리 이상
                                value = int(cleaned)
                                # 현실적인 거래량 범위 (100 ~ 1억주)
                                if 100 <= value <= 100000000:
                                    print(f"✅ 거래량 발견: {value:,}주")
                                    return value

            # 방법 2: 테이블에서 거래량 찾기
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    row_text = row.get_text()
                    if '거래량' in row_text:
                        numbers = re.findall(r'[\d,]+', row_text)
                        for num in numbers:
                            if ',' in num and len(num) >= 5:
                                try:
                                    value = int(num.replace(',', ''))
                                    if 100 <= value <= 100000000:
                                        print(f"✅ 거래량 발견 (테이블): {value:,}주")
                                        return value
                                except:
                                    continue

            return None
        except:
            return None

    def _extract_trading_value_universal(self, soup: BeautifulSoup) -> Optional[str]:
        """거래대금 추출 - 범용"""
        try:
            trading_keywords = soup.find_all(string=re.compile(r'거래대금'))
            for keyword in trading_keywords:
                parent = keyword.parent
                if parent:
                    parent_text = parent.parent.get_text() if parent.parent else parent.get_text()
                    
                    # 백만, 억 단위 찾기
                    if '백만' in parent_text or '억' in parent_text:
                        patterns = [r'[\d,]+\s*백만', r'[\d,]+\s*억']
                        for pattern in patterns:
                            matches = re.findall(pattern, parent_text)
                            if matches:
                                return matches[0].strip()

            return None
        except:
            return None

    def _extract_market_cap_universal(self, soup: BeautifulSoup) -> Optional[str]:
        """시가총액 추출 - 범용 다중 패턴"""
        try:
            # 방법 1: "시가총액" 텍스트 기준
            cap_keywords = soup.find_all(string=re.compile(r'시가총액'))
            for keyword in cap_keywords:
                parent = keyword.parent
                if parent:
                    # 여러 단계 부모까지 확인
                    for i in range(3):
                        container = parent
                        for j in range(i + 1):
                            container = container.parent if container and container.parent else container
                        
                        if container:
                            text = container.get_text()
                            
                            # 다양한 패턴 시도
                            patterns = [
                                r'\d+조\s*[\d,]*억원?',  # 1,242억원
                                r'[\d,]+억원?',         # 1242억원
                                r'\d+조원?'             # 1조원
                            ]
                            
                            for pattern in patterns:
                                matches = re.findall(pattern, text)
                                if matches:
                                    result = matches[0]
                                    if not result.endswith('원'):
                                        result += '원'
                                    print(f"✅ 시가총액 발견: {result}")
                                    return result

            # 방법 2: 테이블에서 찾기
            tables = soup.find_all('table')
            for table in tables:
                table_text = table.get_text()
                if '시가총액' in table_text:
                    patterns = [r'[\d,]+억원?', r'\d+조\s*[\d,]*억원?']
                    for pattern in patterns:
                        matches = re.findall(pattern, table_text)
                        if matches:
                            result = matches[0]
                            if not result.endswith('원'):
                                result += '원'
                            print(f"✅ 시가총액 발견 (테이블): {result}")
                            return result

            return None
        except:
            return None

    def _extract_52week_high_universal(self, soup: BeautifulSoup) -> Optional[float]:
        """52주 최고가 추출 - 범용"""
        try:
            # "52주최고" 또는 "최고" 키워드 찾기
            high_keywords = soup.find_all(string=re.compile(r'52주최고|최고'))
            for keyword in high_keywords:
                parent = keyword.parent
                if parent:
                    # 주변 컨테이너에서 숫자 찾기
                    for i in range(3):
                        container = parent
                        for j in range(i + 1):
                            container = container.parent if container and container.parent else container
                        
                        if container:
                            text = container.get_text()
                            # 쉼표가 포함된 4-7자리 숫자 찾기
                            numbers = re.findall(r'[\d,]+', text)
                            for num in numbers:
                                if ',' in num:
                                    try:
                                        value = float(num.replace(',', ''))
                                        # 현실적인 주가 범위
                                        if 1000 <= value <= 10000000:
                                            print(f"✅ 52주 최고가 발견: {value:,}원")
                                            return value
                                    except:
                                        continue

            return None
        except:
            return None

    def _extract_52week_low_universal(self, soup: BeautifulSoup) -> Optional[float]:
        """52주 최저가 추출 - 범용"""
        try:
            # "52주최저" 또는 "최저" 키워드 찾기
            low_keywords = soup.find_all(string=re.compile(r'52주최저|최저'))
            for keyword in low_keywords:
                if '52주최고' not in keyword:  # 최고가와 구분
                    parent = keyword.parent
                    if parent:
                        # 주변 컨테이너에서 숫자 찾기
                        for i in range(3):
                            container = parent
                            for j in range(i + 1):
                                container = container.parent if container and container.parent else container
                            
                            if container:
                                text = container.get_text()
                                numbers = re.findall(r'[\d,]+', text)
                                for num in numbers:
                                    if ',' in num:
                                        try:
                                            value = float(num.replace(',', ''))
                                            # 현실적인 주가 범위
                                            if 100 <= value <= 1000000:
                                                print(f"✅ 52주 최저가 발견: {value:,}원")
                                                return value
                                        except:
                                            continue

            return None
        except:
            return None

    def _extract_foreign_ownership_universal(self, soup: BeautifulSoup) -> Optional[str]:
        """외국인 지분율 추출 - 범용"""
        try:
            foreign_keywords = soup.find_all(string=re.compile(r'외국인'))
            for keyword in foreign_keywords:
                parent = keyword.parent
                if parent:
                    container = parent.parent if parent.parent else parent
                    text = container.get_text()
                    
                    # 퍼센트 찾기
                    percentages = re.findall(r'\d+\.\d+%|\d+%', text)
                    if percentages:
                        return percentages[0]

            return None
        except:
            return None

    def _extract_investment_opinion_universal(self, soup: BeautifulSoup) -> Optional[str]:
        """투자의견 추출 - 범용"""
        try:
            keywords = ['매수', '중립', '매도', '투자의견']
            for keyword in keywords:
                elements = soup.find_all(string=re.compile(keyword))
                for elem in elements:
                    parent = elem.parent
                    if parent:
                        text = parent.get_text(strip=True)
                        if any(opinion in text for opinion in ['매수', '중립', '매도']):
                            return text

            return None
        except:
            return None

    def _extract_sector_comparison_universal(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """동종업종 비교 추출 - 범용"""
        try:
            sector_data = {'sector_name': None, 'companies': []}

            # 동종업종 관련 텍스트 찾기
            sector_keywords = soup.find_all(string=re.compile(r'동일업종|동종업종'))
            
            for keyword in sector_keywords:
                if '비교' in keyword:
                    sector_data['sector_name'] = keyword.strip()
                
                parent = keyword.parent
                if parent:
                    # 주변 테이블에서 회사명들 찾기
                    for i in range(5):
                        container = parent
                        for j in range(i + 1):
                            container = container.parent if container and container.parent else container
                        
                        if container and hasattr(container, 'find_all'):
                            tables = container.find_all('table')
                            for table in tables:
                                table_text = table.get_text()
                                if any(keyword in table_text for keyword in ['현재가', '전일대비']):
                                    rows = table.find_all('tr')
                                    
                                    for row in rows:
                                        cells = row.find_all(['td', 'th'])
                                        for cell in cells:
                                            text = cell.get_text(strip=True)
                                            # 회사명 정리
                                            for separator in ['★', '*', '▲', '▼']:
                                                if separator in text:
                                                    text = text.split(separator)[0]
                                                    break
                                            
                                            # 숫자 제거 (종목코드)
                                            text = re.sub(r'\d+', '', text).strip()
                                            
                                            # 유효한 회사명인지 확인
                                            if (text and len(text) > 1 and len(text) < 20 and 
                                                re.search(r'[가-힣]', text) and 
                                                text not in ['종목명', '현재가', '전일대비', '등락률']):
                                                if text not in sector_data['companies']:
                                                    sector_data['companies'].append(text)

            # 중복 제거 및 상위 5개사만
            sector_data['companies'] = sector_data['companies'][:5]
            
            return sector_data

        except:
            return {'sector_name': None, 'companies': []}

    def _validate_universal_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """범용 데이터 검증"""
        real_time = result['real_time_data']
        
        # 전일대비와 등락률 일관성 확인
        change_amount = real_time.get('change_amount')
        change_rate = real_time.get('change_rate')
        
        if change_amount is not None and change_rate is not None:
            amount_positive = change_amount > 0
            rate_positive = change_rate > 0
            
            if amount_positive != rate_positive:
                print(f"⚠️ 전일대비({change_amount}) vs 등락률({change_rate}) 부호 불일치 감지")
                real_time['change_rate'] = abs(change_rate) if amount_positive else -abs(change_rate)
                print(f"✅ 등락률 수정: {real_time['change_rate']}")
        
        return result


# 기존 인터페이스 호환성을 위한 클래스 별칭
NaverRealTimeExtractor = UniversalRealTimeExtractor


def test_universal_extraction():
    """범용 추출기 테스트"""
    print("🚀 범용 실시간 데이터 추출기 테스트")
    print("=" * 60)

    extractor = UniversalRealTimeExtractor()

    # 다양한 종목으로 테스트
    test_stocks = [
        ("005930", "삼성전자"),
        ("060310", "3S"),
        ("000660", "SK하이닉스")
    ]

    for stock_code, company_name in test_stocks:
        print(f"\n📊 {company_name} ({stock_code}) 테스트...")
        result = extractor.extract_real_time_data(stock_code)
        
        if result['extraction_status'] == 'success':
            real_time = result['real_time_data']
            success_count = sum(1 for field in [
                'current_price', 'change_amount', 'change_rate', 'volume',
                'trading_value', 'market_cap', 'high_52w', 'low_52w',
                'foreign_ownership', 'investment_opinion'
            ] if real_time[field] is not None)
            
            success_rate = (success_count / 10) * 100
            print(f"✅ {company_name}: {success_rate:.1f}% 성공률")
        else:
            print(f"❌ {company_name}: 추출 실패")

    print(f"\n✅ 범용 추출기 테스트 완료!")


if __name__ == "__main__":
    test_universal_extraction()
