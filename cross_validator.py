"""
🎯 네이버 + 다음 증권 교차검증 시스템
현실적이고 간단한 정확성 향상 솔루션
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from dataclasses import dataclass
from typing import Optional, Tuple
import logging

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

class CrossValidatedStockExtractor:
    """네이버 + 다음 교차검증 주식 데이터 추출기"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        options = Options()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            logging.info("✅ Chrome 드라이버 초기화 완료")
        except Exception as e:
            logging.error(f"❌ 드라이버 초기화 실패: {e}")
            raise
    
    def extract_stock_data(self, symbol: str) -> StockData:
        """메인 추출 함수 - 교차검증 포함"""
        
        print(f"\n🎯 {symbol} 교차검증 추출 시작...")
        print("=" * 60)
        
        # 1. 네이버 데이터 추출
        naver_data = self.extract_from_naver(symbol)
        
        # 2. 다음 데이터 추출  
        daum_data = self.extract_from_daum(symbol)
        
        # 3. 교차검증 및 최종 결과
        final_data = self.cross_validate(naver_data, daum_data, symbol)
        
        print(f"\n📊 최종 결과 (신뢰도: {final_data.confidence:.1%})")
        print("=" * 60)
        self.print_final_result(final_data)
        
        return final_data
    
    def extract_from_naver(self, symbol: str) -> Optional[StockData]:
        """네이버 증권에서 데이터 추출"""
        
        print("🔍 네이버 증권 데이터 추출 중...")
        
        try:
            url = f'https://finance.naver.com/item/main.naver?code={symbol}'
            self.driver.get(url)
            
            # 페이지 로딩 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "today"))
            )
            time.sleep(2)  # 추가 대기 (동적 콘텐츠)
            
            data = StockData(symbol=symbol)
            
            # 회사명
            try:
                company_element = self.driver.find_element(By.CSS_SELECTOR, ".wrap_company h2")
                data.company_name = company_element.text.strip()
            except:
                data.company_name = "Unknown"
            
            # 현재가
            try:
                price_element = self.driver.find_element(By.CSS_SELECTOR, ".today .blind")
                price_text = price_element.text.replace(',', '')
                data.current_price = float(price_text)
            except Exception as e:
                logging.warning(f"네이버 현재가 추출 실패: {e}")
                return None
            
            # 전일대비
            try:
                change_elements = self.driver.find_elements(By.CSS_SELECTOR, ".today .change")
                if change_elements:
                    change_text = change_elements[0].text
                    # +400, -400 형태에서 숫자 추출
                    change_match = re.search(r'([+-]?)([\d,]+)', change_text)
                    if change_match:
                        sign = change_match.group(1)
                        value = float(change_match.group(2).replace(',', ''))
                        data.change = value if sign != '-' else -value
            except Exception as e:
                logging.warning(f"네이버 전일대비 추출 실패: {e}")
            
            # 등락률
            try:
                rate_elements = self.driver.find_elements(By.CSS_SELECTOR, ".today .rate")
                if rate_elements:
                    rate_text = rate_elements[0].text.replace('%', '').replace('+', '')
                    data.change_percent = float(rate_text)
            except Exception as e:
                logging.warning(f"네이버 등락률 추출 실패: {e}")
            
            # 거래량 (여러 방법 시도)
            volume_found = False
            
            # 방법 1: 메인 영역
            try:
                volume_element = self.driver.find_element(By.ID, "_volume")
                volume_text = volume_element.text.replace(',', '')
                data.volume = int(volume_text)
                volume_found = True
            except:
                pass
            
            # 방법 2: 테이블에서 검색
            if not volume_found:
                try:
                    tables = self.driver.find_elements(By.TAG_NAME, "table")
                    for table in tables:
                        table_text = table.text
                        if '거래량' in table_text:
                            # 거래량 패턴 찾기
                            volume_patterns = re.findall(r'거래량[:\s]*([0-9,]+)', table_text)
                            if volume_patterns:
                                data.volume = int(volume_patterns[0].replace(',', ''))
                                volume_found = True
                                break
                except:
                    pass
            
            # 거래대금
            try:
                # 여러 패턴으로 거래대금 찾기
                page_text = self.driver.page_source
                trading_patterns = [
                    r'거래대금[:\s]*([0-9,]+)\s*백만',
                    r'거래대금[:\s]*([0-9,]+)\s*억'
                ]
                
                for pattern in trading_patterns:
                    matches = re.findall(pattern, page_text)
                    if matches:
                        value = float(matches[0].replace(',', ''))
                        if '백만' in pattern:
                            data.trading_value = value / 100  # 백만 → 억
                        else:
                            data.trading_value = value  # 이미 억
                        break
            except Exception as e:
                logging.warning(f"네이버 거래대금 추출 실패: {e}")
            
            # 시가총액
            try:
                page_text = self.driver.page_source
                market_cap_match = re.search(r'시가총액[:\s]*([0-9,조억만]+)', page_text)
                if market_cap_match:
                    data.market_cap = market_cap_match.group(1)
            except:
                pass
            
            data.source = "naver"
            print("✅ 네이버 데이터 추출 완료")
            print(f"   현재가: {data.current_price:,}원, 거래량: {data.volume:,}주")
            return data
            
        except Exception as e:
            logging.error(f"❌ 네이버 추출 전체 실패: {e}")
            return None
    
    def extract_from_daum(self, symbol: str) -> Optional[StockData]:
        """다음 증권에서 데이터 추출"""
        
        print("🔍 다음 증권 데이터 추출 중...")
        
        try:
            url = f'https://finance.daum.net/quotes/A{symbol}'
            self.driver.get(url)
            
            # 페이지 로딩 대기
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".price"))
            )
            time.sleep(2)
            
            data = StockData(symbol=symbol)
            
            # 현재가
            try:
                price_element = self.driver.find_element(By.CSS_SELECTOR, ".price")
                price_text = price_element.text.replace(',', '').replace('원', '')
                data.current_price = float(price_text)
            except Exception as e:
                logging.warning(f"다음 현재가 추출 실패: {e}")
                return None
            
            # 전일대비 및 등락률
            try:
                change_elements = self.driver.find_elements(By.CSS_SELECTOR, ".rate")
                if len(change_elements) >= 2:
                    # 전일대비
                    change_text = change_elements[0].text
                    change_match = re.search(r'([+-]?)([\d,]+)', change_text)
                    if change_match:
                        sign = change_match.group(1)
                        value = float(change_match.group(2).replace(',', ''))
                        data.change = value if sign != '-' else -value
                    
                    # 등락률
                    rate_text = change_elements[1].text.replace('%', '').replace('+', '')
                    data.change_percent = float(rate_text)
            except Exception as e:
                logging.warning(f"다음 전일대비/등락률 추출 실패: {e}")
            
            # 거래량
            try:
                # 다음 페이지에서 거래량 찾기
                volume_elements = self.driver.find_elements(By.XPATH, "//td[contains(text(), '거래량')]/following-sibling::td")
                if volume_elements:
                    volume_text = volume_elements[0].text.replace(',', '').replace('주', '')
                    data.volume = int(volume_text)
                else:
                    # 대안 방법
                    page_text = self.driver.page_source
                    volume_match = re.search(r'거래량[:\s]*([0-9,]+)', page_text)
                    if volume_match:
                        data.volume = int(volume_match.group(1).replace(',', ''))
            except Exception as e:
                logging.warning(f"다음 거래량 추출 실패: {e}")
            
            data.source = "daum"
            print("✅ 다음 데이터 추출 완료")
            print(f"   현재가: {data.current_price:,}원, 거래량: {data.volume:,}주")
            return data
            
        except Exception as e:
            logging.error(f"❌ 다음 추출 전체 실패: {e}")
            return None
    
    def cross_validate(self, naver_data: Optional[StockData], daum_data: Optional[StockData], symbol: str) -> StockData:
        """교차검증 및 최종 데이터 결정"""
        
        print("\n🔍 교차검증 분석 중...")
        
        # 둘 다 실패한 경우
        if not naver_data and not daum_data:
            print("❌ 모든 소스에서 데이터 추출 실패")
            return StockData(symbol=symbol, source="failed", confidence=0.0)
        
        # 한쪽만 성공한 경우
        if naver_data and not daum_data:
            print("⚠️ 다음 데이터 없음, 네이버 데이터만 사용")
            naver_data.confidence = 0.7
            return naver_data
        
        if daum_data and not naver_data:
            print("⚠️ 네이버 데이터 없음, 다음 데이터만 사용")
            daum_data.confidence = 0.7
            return daum_data
        
        # 둘 다 성공한 경우 - 교차검증
        print("✅ 양쪽 데이터 모두 확보, 교차검증 진행")
        
        # 핵심 데이터 비교
        price_diff = abs(naver_data.current_price - daum_data.current_price)
        price_diff_percent = price_diff / naver_data.current_price * 100
        
        volume_diff = abs(naver_data.volume - daum_data.volume) if naver_data.volume > 0 and daum_data.volume > 0 else 0
        volume_diff_percent = volume_diff / max(naver_data.volume, daum_data.volume) * 100 if max(naver_data.volume, daum_data.volume) > 0 else 0
        
        print(f"📊 차이 분석:")
        print(f"   현재가 차이: {price_diff:,.0f}원 ({price_diff_percent:.2f}%)")
        print(f"   거래량 차이: {volume_diff:,}주 ({volume_diff_percent:.2f}%)")
        
        # 신뢰도 계산
        confidence = 1.0
        
        if price_diff_percent > 1.0:  # 1% 이상 차이
            confidence -= 0.2
            print("⚠️ 현재가 차이가 큼")
        
        if volume_diff_percent > 10.0:  # 10% 이상 차이
            confidence -= 0.1
            print("⚠️ 거래량 차이가 큼")
        
        # 최종 데이터 결정 (네이버 우선, 평균값 사용)
        final_data = StockData(symbol=symbol)
        final_data.company_name = naver_data.company_name or daum_data.company_name
        
        # 현재가: 평균값 (차이가 작을 때만)
        if price_diff_percent < 2.0:
            final_data.current_price = round((naver_data.current_price + daum_data.current_price) / 2)
            print("📊 현재가: 평균값 사용")
        else:
            final_data.current_price = naver_data.current_price
            print("📊 현재가: 네이버 데이터 우선 사용")
        
        # 거래량: 더 합리적인 값 선택
        if volume_diff_percent < 15.0 and naver_data.volume > 0 and daum_data.volume > 0:
            final_data.volume = int((naver_data.volume + daum_data.volume) / 2)
            print("📊 거래량: 평균값 사용")
        elif naver_data.volume > 0:
            final_data.volume = naver_data.volume
            print("📊 거래량: 네이버 데이터 사용")
        else:
            final_data.volume = daum_data.volume
            print("📊 거래량: 다음 데이터 사용")
        
        # 나머지 데이터는 네이버 우선
        final_data.change = naver_data.change or daum_data.change
        final_data.change_percent = naver_data.change_percent or daum_data.change_percent
        final_data.trading_value = naver_data.trading_value or daum_data.trading_value
        final_data.market_cap = naver_data.market_cap or daum_data.market_cap
        
        final_data.source = "cross_validated"
        final_data.confidence = confidence
        
        if confidence >= 0.9:
            print("🏆 높은 신뢰도 - 데이터 일치성 우수")
        elif confidence >= 0.8:
            print("✅ 양호한 신뢰도 - 데이터 신뢰 가능")
        else:
            print("⚠️ 낮은 신뢰도 - 추가 검증 권장")
        
        return final_data
    
    def print_final_result(self, data: StockData):
        """최종 결과 출력"""
        
        status_emoji = "🏆" if data.confidence >= 0.9 else "✅" if data.confidence >= 0.8 else "⚠️"
        
        print(f"""
{status_emoji} {data.company_name} ({data.symbol}) - {data.source}
💰 현재가: {data.current_price:,}원
📈 전일대비: {data.change:+,}원 ({data.change_percent:+.2f}%)
📊 거래량: {data.volume:,}주
💵 거래대금: {data.trading_value:.0f}억원
🏢 시가총액: {data.market_cap}
🎯 신뢰도: {data.confidence:.1%}
        """)
    
    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            print("🔚 브라우저 종료")

# 사용 예시
def main():
    """메인 실행 함수"""
    
    extractor = CrossValidatedStockExtractor(headless=True)
    
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
        else:
            print("\n❌ 데이터 추출에 실패했습니다.")
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    finally:
        extractor.close()

if __name__ == "__main__":
    main()
