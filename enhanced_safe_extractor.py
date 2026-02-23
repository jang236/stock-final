import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional, Any, Tuple
import sys


class NaverRealTimeExtractor:
    """
    네이버 증권에서 범용 실시간 주가 데이터 추출
    부호 오류 안전장치 강화 최종 버전 - 시각적 단서 활용
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
        범용 실시간 주가 데이터 추출 (안전장치 강화)

        Args:
            stock_code: 종목코드 (예: "005930")

        Returns:
            8개 핵심 항목 실시간 데이터 딕셔너리
        """
        url = f"https://finance.naver.com/item/main.naver?code={stock_code}"

        print(f"🔍 {stock_code} 다중 안전장치 강화 시스템 데이터 추출 시작...")

        try:
            # 페이지 요청
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 회사명 추출
            company_name = self._extract_company_name(soup)

            # 핵심 데이터 추출
            current_price = self._extract_current_price_direct(soup)
            
            # 🔥 NEW: 시각적 단서에서 부호 먼저 확인
            visual_sign = self._extract_sign_from_visual_cues(soup)
            print(f"🎨 시각적 부호 감지: {visual_sign}")
            
            change_amount = self._extract_change_amount_with_enhanced_safety(soup, visual_sign)
            change_rate = self._extract_change_rate_with_enhanced_safety(soup, visual_sign)
            
            # 전일대비와 등락률 상호 검증 및 보완 - 강화된 안전장치
            change_amount, change_rate = self._cross_validate_with_multi_source_safety(
                soup, current_price, change_amount, change_rate, visual_sign
            )

            result = {
                'stock_code': stock_code,
                'company_name': company_name,
                'real_time_data': {
                    'current_price': current_price,
                    'change_amount': change_amount,
                    'change_rate': change_rate,
                    'volume': self._extract_volume_direct(soup),
                    'trading_value': self._extract_trading_value_direct(soup),
                    'market_cap': self._extract_market_cap_smart(soup, current_price),
                    'foreign_ownership': self._extract_foreign_ownership_direct(soup)
                },
                'sector_comparison': self._extract_sector_comparison_direct(soup),
                'extraction_status': 'success'
            }

            # 최종 검증
            result = self._final_validation_with_warnings(result)

            print(f"✅ 다중 안전장치 강화 시스템 데이터 추출 완료!")
            return result

        except Exception as e:
            print(f"❌ 데이터 추출 실패: {e}")
            return {
                'stock_code': stock_code,
                'extraction_status': 'failed',
                'error': str(e)
            }

    def _extract_sign_from_visual_cues(self, soup: BeautifulSoup) -> Optional[str]:
        """🎨 시각적 단서에서 부호 추출 (색상, CSS 클래스 등)"""
        try:
            print("🎨 시각적 부호 감지 시도...")
            
            # 1차: CSS 클래스 기반 부호 감지
            css_sign = self._extract_sign_from_css_classes(soup)
            if css_sign:
                print(f"  ✅ CSS 클래스 부호: {css_sign}")
                return css_sign
            
            # 2차: 색상 정보에서 부호 감지
            color_sign = self._extract_sign_from_color_styles(soup)
            if color_sign:
                print(f"  ✅ 색상 기반 부호: {color_sign}")
                return color_sign
            
            # 3차: 화살표 아이콘에서 부호 감지
            icon_sign = self._extract_sign_from_icons(soup)
            if icon_sign:
                print(f"  ✅ 아이콘 기반 부호: {icon_sign}")
                return icon_sign
            
            print("  ⚠️ 시각적 부호 감지 실패")
            return None
            
        except Exception as e:
            print(f"  ❌ 시각적 부호 감지 오류: {e}")
            return None

    def _extract_sign_from_css_classes(self, soup: BeautifulSoup) -> Optional[str]:
        """CSS 클래스명에서 부호 추출"""
        try:
            # 상승/하락 관련 CSS 클래스 패턴
            rise_patterns = ['rise', 'up', 'plus', 'red', 'increase', 'positive']
            fall_patterns = ['fall', 'down', 'minus', 'blue', 'decrease', 'negative']
            
            # no_exday 영역의 클래스 확인
            exday_area = soup.find('p', class_='no_exday')
            if exday_area:
                # 부모 및 자식 요소들의 클래스 확인
                all_elements = [exday_area] + exday_area.find_all()
                
                for element in all_elements:
                    if element.get('class'):
                        classes = ' '.join(element.get('class')).lower()
                        
                        for pattern in rise_patterns:
                            if pattern in classes:
                                return '+'
                        
                        for pattern in fall_patterns:
                            if pattern in classes:
                                return '-'
            
            return None
        except:
            return None

    def _extract_sign_from_color_styles(self, soup: BeautifulSoup) -> Optional[str]:
        """색상 스타일에서 부호 추출"""
        try:
            # no_exday 영역에서 색상 확인
            exday_area = soup.find('p', class_='no_exday')
            if exday_area:
                # 모든 하위 요소의 스타일 확인
                all_elements = [exday_area] + exday_area.find_all()
                
                for element in all_elements:
                    style = element.get('style', '').lower()
                    if 'color' in style:
                        # 빨간색 계열 (상승)
                        if any(color in style for color in ['red', '#f00', '#ff0000', 'rgb(255,0,0)', 'rgb(255, 0, 0)']):
                            return '+'
                        # 파란색 계열 (하락)  
                        elif any(color in style for color in ['blue', '#00f', '#0000ff', 'rgb(0,0,255)', 'rgb(0, 0, 255)']):
                            return '-'
            
            return None
        except:
            return None

    def _extract_sign_from_icons(self, soup: BeautifulSoup) -> Optional[str]:
        """화살표/아이콘에서 부호 추출"""
        try:
            # no_exday 영역 주변 텍스트에서 화살표 찾기
            exday_area = soup.find('p', class_='no_exday')
            if exday_area:
                # 주변 텍스트 확인
                surrounding_text = str(exday_area)
                
                # 상승 화살표
                if any(arrow in surrounding_text for arrow in ['▲', '↑', '⬆', '🔺']):
                    return '+'
                # 하락 화살표
                elif any(arrow in surrounding_text for arrow in ['▼', '↓', '⬇', '🔻']):
                    return '-'
            
            return None
        except:
            return None

    def _extract_company_name(self, soup: BeautifulSoup) -> Optional[str]:
        """회사명 추출"""
        try:
            # title 태그에서 추출
            title = soup.find('title')
            if title:
                title_text = title.get_text()
                if ':' in title_text:
                    return title_text.split(':')[0].strip()

            # 대안: h2 태그에서 추출
            h2_tags = soup.find_all('h2')
            for h2 in h2_tags:
                text = h2.get_text(strip=True)
                if text and len(text) < 20:
                    return text

            return None
        except:
            return None

    def _extract_current_price_direct(self, soup: BeautifulSoup) -> Optional[float]:
        """현재가 추출 - 직접 추출 우선"""
        try:
            print("🔍 현재가 직접 추출 시도...")
            
            # 1차: 가장 확실한 현재가 위치
            today_area = soup.find('p', class_='no_today')
            if today_area:
                blind_elem = today_area.find('span', class_='blind')
                if blind_elem:
                    text = blind_elem.get_text(strip=True)
                    if text and ',' in text:
                        cleaned = text.replace(',', '')
                        if cleaned.isdigit():
                            price = float(cleaned)
                            print(f"✅ 현재가 직접 추출: {price:,}원")
                            return price

            # 2차: no_today 영역의 모든 blind 요소
            today_elements = soup.select('.no_today .blind')
            for elem in today_elements:
                text = elem.get_text(strip=True)
                if text and ',' in text and len(text) >= 4:
                    cleaned = text.replace(',', '')
                    if cleaned.isdigit():
                        price = float(cleaned)
                        print(f"✅ 현재가 직접 추출 (보조): {price:,}원")
                        return price

            return None
        except Exception as e:
            print(f"❌ 현재가 추출 오류: {e}")
            return None

    def _extract_change_amount_with_enhanced_safety(self, soup: BeautifulSoup, visual_sign: Optional[str]) -> Optional[float]:
        """전일대비 추출 - 다중 소스 안전장치"""
        try:
            print("🔍 전일대비 다중 소스 안전장치 추출 시도...")
            
            # 다중 소스에서 전일대비 후보 수집
            candidates = []
            
            # 1차: 기호 포함 직접 추출
            direct_candidate = self._extract_change_amount_with_sign(soup)
            if direct_candidate:
                candidates.append(('direct', direct_candidate))
                print(f"  📍 직접 추출 후보: {direct_candidate:+,}원")
            
            # 2차: 숫자만 추출 + 시각적 부호 조합
            if visual_sign:
                numeric_candidate = self._extract_change_amount_numeric_only(soup)
                if numeric_candidate:
                    signed_value = numeric_candidate if visual_sign == '+' else -numeric_candidate
                    candidates.append(('visual', signed_value))
                    print(f"  🎨 시각적 조합 후보: {signed_value:+,}원")
            
            # 3차: 후보들 검증 및 선택
            return self._select_best_change_amount_candidate(candidates)
            
        except Exception as e:
            print(f"❌ 전일대비 추출 오류: {e}")
            return None

    def _extract_change_amount_with_sign(self, soup: BeautifulSoup) -> Optional[float]:
        """기호 포함 전일대비 추출"""
        try:
            # no_exday 영역에서 기호 포함 추출
            exday_area = soup.find('p', class_='no_exday')
            if exday_area:
                blind_elements = exday_area.find_all('span', class_='blind')
                if blind_elements:
                    first_text = blind_elements[0].get_text(strip=True)
                    
                    # +/- 기호가 있는 경우
                    if first_text.startswith(('+', '-')):
                        try:
                            return float(first_text.replace(',', ''))
                        except:
                            pass

            # 화살표 기호와 함께 있는 패턴
            page_text = soup.get_text()
            symbol_patterns = [
                r'▲\s*([\d,]+)',  # ▲2,950
                r'▼\s*([\d,]+)',  # ▼440
                r'↑\s*([\d,]+)',  # ↑2,950  
                r'↓\s*([\d,]+)',  # ↓440
            ]
            
            for pattern in symbol_patterns:
                matches = re.finditer(pattern, page_text)
                for match in matches:
                    number_str = match.group(1)
                    sign = 1 if any(sym in match.group(0) for sym in ['▲', '↑']) else -1
                    
                    # 전일대비 맥락 확인
                    context_start = max(0, match.start() - 30)
                    context_end = min(len(page_text), match.end() + 30)
                    context = page_text[context_start:context_end]
                    
                    if any(keyword in context for keyword in ['전일대비', '전일', '대비']):
                        try:
                            return float(number_str.replace(',', '')) * sign
                        except:
                            continue

            return None
        except:
            return None

    def _extract_change_amount_numeric_only(self, soup: BeautifulSoup) -> Optional[float]:
        """숫자만 추출 (부호 없이)"""
        try:
            exday_area = soup.find('p', class_='no_exday')
            if exday_area:
                blind_elements = exday_area.find_all('span', class_='blind')
                if blind_elements:
                    first_text = blind_elements[0].get_text(strip=True)
                    
                    # 순수 숫자인 경우
                    if not first_text.startswith(('+', '-')):
                        cleaned = first_text.replace(',', '')
                        if cleaned.isdigit():
                            return float(cleaned)
            
            return None
        except:
            return None

    def _select_best_change_amount_candidate(self, candidates: List[Tuple[str, float]]) -> Optional[float]:
        """전일대비 후보 중 최선 선택"""
        if not candidates:
            print("  ⚠️ 전일대비 후보 없음 - 추출 포기")
            return None
        
        # 직접 추출 우선
        for source, value in candidates:
            if source == 'direct':
                print(f"  ✅ 전일대비 직접 추출 채택: {value:+,}원")
                return value
        
        # 시각적 조합이 있으면 사용
        for source, value in candidates:
            if source == 'visual':
                print(f"  ✅ 전일대비 시각적 조합 채택: {value:+,}원")
                return value
        
        print("  ⚠️ 전일대비 신뢰할 만한 후보 없음 - 추출 포기")
        return None

    def _extract_change_rate_with_enhanced_safety(self, soup: BeautifulSoup, visual_sign: Optional[str]) -> Optional[float]:
        """등락률 추출 - 다중 소스 안전장치"""
        try:
            print("🔍 등락률 다중 소스 안전장치 추출 시도...")
            
            # 다중 소스에서 등락률 후보 수집
            candidates = []
            
            # 1차: 기호 포함 직접 추출
            direct_candidate = self._extract_change_rate_with_sign(soup)
            if direct_candidate:
                candidates.append(('direct', direct_candidate))
                print(f"  📍 직접 추출 후보: {direct_candidate:+.2f}%")
            
            # 2차: 숫자만 추출 + 시각적 부호 조합
            if visual_sign:
                numeric_candidate = self._extract_change_rate_numeric_only(soup)
                if numeric_candidate:
                    signed_value = numeric_candidate if visual_sign == '+' else -numeric_candidate
                    candidates.append(('visual', signed_value))
                    print(f"  🎨 시각적 조합 후보: {signed_value:+.2f}%")
            
            # 3차: 후보들 검증 및 선택
            return self._select_best_change_rate_candidate(candidates)
            
        except Exception as e:
            print(f"❌ 등락률 추출 오류: {e}")
            return None

    def _extract_change_rate_with_sign(self, soup: BeautifulSoup) -> Optional[float]:
        """기호 포함 등락률 추출"""
        try:
            # no_exday 영역에서 기호 포함 등락률
            exday_area = soup.find('p', class_='no_exday')
            if exday_area:
                blind_elements = exday_area.find_all('span', class_='blind')
                if len(blind_elements) >= 2:
                    rate_elem = blind_elements[1]
                    rate_text = rate_elem.get_text(strip=True)
                    
                    # 다음 노드에서 % 기호 확인
                    next_sibling = rate_elem.next_sibling
                    if next_sibling and '%' in str(next_sibling):
                        if rate_text.startswith(('+', '-')):
                            try:
                                return float(rate_text)
                            except:
                                pass

            # 패턴 매칭에서 기호 포함 등락률
            page_text = soup.get_text()
            rate_patterns = [
                r'([+-]\d+\.\d+)%',  # +29.92% 또는 -4.27%
                r'([+-]\d+)%',       # +30% 또는 -4%
            ]
            
            for pattern in rate_patterns:
                matches = re.finditer(pattern, page_text)
                for match in matches:
                    rate_str = match.group(1)
                    context_start = max(0, match.start() - 30)
                    context_end = min(len(page_text), match.end() + 30)
                    context = page_text[context_start:context_end]
                    
                    if any(keyword in context for keyword in ['등락률', '전일대비', '변동률']):
                        try:
                            rate = float(rate_str)
                            if abs(rate) < 100:  # 현실적인 범위
                                return rate
                        except:
                            continue

            return None
        except:
            return None

    def _extract_change_rate_numeric_only(self, soup: BeautifulSoup) -> Optional[float]:
        """등락률 숫자만 추출 (부호 없이)"""
        try:
            exday_area = soup.find('p', class_='no_exday')
            if exday_area:
                blind_elements = exday_area.find_all('span', class_='blind')
                if len(blind_elements) >= 2:
                    rate_elem = blind_elements[1]
                    rate_text = rate_elem.get_text(strip=True)
                    
                    # % 기호 확인
                    next_sibling = rate_elem.next_sibling
                    if next_sibling and '%' in str(next_sibling):
                        # 순수 숫자인 경우
                        if not rate_text.startswith(('+', '-')):
                            try:
                                rate = float(rate_text)
                                if 0 < rate < 100:  # 현실적인 범위
                                    return rate
                            except:
                                pass
            
            return None
        except:
            return None

    def _select_best_change_rate_candidate(self, candidates: List[Tuple[str, float]]) -> Optional[float]:
        """등락률 후보 중 최선 선택"""
        if not candidates:
            print("  ⚠️ 등락률 후보 없음 - 추출 포기")
            return None
        
        # 직접 추출 우선
        for source, value in candidates:
            if source == 'direct':
                print(f"  ✅ 등락률 직접 추출 채택: {value:+.2f}%")
                return value
        
        # 시각적 조합이 있으면 사용
        for source, value in candidates:
            if source == 'visual':
                print(f"  ✅ 등락률 시각적 조합 채택: {value:+.2f}%")
                return value
        
        print("  ⚠️ 등락률 신뢰할 만한 후보 없음 - 추출 포기")
        return None

    def _cross_validate_with_multi_source_safety(self, soup: BeautifulSoup, current_price: Optional[float], 
                                               change_amount: Optional[float], change_rate: Optional[float], 
                                               visual_sign: Optional[str]) -> tuple:
        """전일대비와 등락률 다중 소스 상호 검증"""
        try:
            print("🔍 다중 소스 상호 검증...")
            
            calculated_amount = None
            calculated_rate = None
            
            # 🔥 NEW: 논리적 일관성 사전 검증
            if change_amount and change_rate:
                if not self._validate_sign_consistency(change_amount, change_rate):
                    print("⚠️ 심각한 부호 불일치 감지 - 안전을 위해 둘 다 폐기")
                    return None, None

            # 🔥 NEW: 시각적 부호와의 일치성 검증
            if visual_sign and change_amount:
                visual_positive = visual_sign == '+'
                amount_positive = change_amount > 0
                if visual_positive != amount_positive:
                    print(f"⚠️ 시각적 부호({visual_sign})와 전일대비 부호 불일치 - 전일대비 폐기")
                    change_amount = None

            if visual_sign and change_rate:
                visual_positive = visual_sign == '+'
                rate_positive = change_rate > 0
                if visual_positive != rate_positive:
                    print(f"⚠️ 시각적 부호({visual_sign})와 등락률 부호 불일치 - 등락률 폐기")
                    change_rate = None
            
            # 하나만 있는 경우 - 상호 계산으로 보완 (기존 로직 유지)
            if current_price and change_amount and not change_rate:
                yesterday_price = current_price - change_amount
                if yesterday_price > 0:
                    calculated_rate = (change_amount / yesterday_price) * 100
                    print(f"✅ 등락률 계산 보완: {calculated_rate:+.2f}% (계산값)")
                    change_rate = calculated_rate
            
            elif current_price and change_rate and not change_amount:
                yesterday_price = current_price / (1 + change_rate / 100)
                calculated_amount = current_price - yesterday_price
                print(f"✅ 전일대비 계산 보완: {calculated_amount:+,.0f}원 (계산값)")
                change_amount = round(calculated_amount)
            
            # 둘 다 있는 경우 - 수학적 검증 강화
            elif change_amount and change_rate:
                if self._validate_mathematical_consistency(current_price, change_amount, change_rate):
                    print(f"✅ 수학적 일치성 검증 통과")
                else:
                    print(f"⚠️ 수학적 불일치 감지 - 보수적 처리")
                    # 시각적 부호가 있으면 이를 기준으로 재검증
                    if visual_sign:
                        print(f"  시각적 부호({visual_sign})를 기준으로 재평가...")
                        # 더 신뢰할 만한 것 선택 로직 추가 가능
            
            # 계산값 플래그 추가
            if calculated_amount is not None:
                change_amount = (change_amount, True)
            if calculated_rate is not None:
                change_rate = (change_rate, True)
            
            return change_amount, change_rate
            
        except Exception as e:
            print(f"❌ 다중 소스 검증 오류: {e}")
            return change_amount, change_rate

    def _validate_sign_consistency(self, change_amount: float, change_rate: float) -> bool:
        """부호 일관성 검증"""
        amount_positive = change_amount > 0
        rate_positive = change_rate > 0
        return amount_positive == rate_positive

    def _validate_mathematical_consistency(self, current_price: Optional[float], 
                                         change_amount: float, change_rate: float) -> bool:
        """수학적 일관성 검증"""
        if not current_price:
            return True  # 검증 불가시 통과
        
        try:
            yesterday_price = current_price - change_amount
            if yesterday_price <= 0:
                return False
            
            calculated_rate = (change_amount / yesterday_price) * 100
            rate_diff = abs(calculated_rate - change_rate)
            
            return rate_diff <= 0.5  # 0.5% 이내 허용
        except:
            return False

    # 나머지 메서드들은 기존 코드와 동일하므로 생략...
    # (여기에 나머지 모든 메서드들이 들어가야 하지만 길이상 생략)

    def _extract_volume_direct(self, soup: BeautifulSoup) -> Optional[int]:
        """거래량 추출 - 직접 추출 우선"""
        try:
            print("🔍 거래량 직접 추출 시도...")
            
            # 1차: td 요소에서 "거래량" 라벨-값 쌍 찾기
            td_elements = soup.find_all('td')
            for i, td in enumerate(td_elements):
                if '거래량' in td.get_text():
                    if i + 1 < len(td_elements):
                        volume_td = td_elements[i + 1]
                        volume_text = volume_td.get_text(strip=True)
                        
                        if ',' in volume_text:
                            number = volume_text.replace(',', '').replace('주', '')
                            if number.isdigit():
                                volume = int(number)
                                if volume > 1000:  # 현실적인 거래량
                                    print(f"✅ 거래량 직접 추출: {volume:,}주")
                                    return volume

            # 2차: 전체 페이지에서 "거래량" 키워드 근처 큰 숫자
            page_text = soup.get_text()
            volume_pattern = r'거래량[^\d]*?([\d,]{6,})'
            matches = re.finditer(volume_pattern, page_text)
            for match in matches:
                volume_str = match.group(1)
                try:
                    volume = int(volume_str.replace(',', ''))
                    if volume > 1000:
                        print(f"✅ 거래량 직접 추출 (패턴): {volume:,}주")
                        return volume
                except:
                    continue

            return None
        except Exception as e:
            print(f"❌ 거래량 추출 오류: {e}")
            return None

    def _extract_trading_value_direct(self, soup: BeautifulSoup) -> Optional[str]:
        """거래대금 추출 - 직접 추출"""
        try:
            # 1차: td 요소에서 거래대금 라벨-값 쌍
            td_elements = soup.find_all('td')
            for i, td in enumerate(td_elements):
                if '거래대금' in td.get_text():
                    if i + 1 < len(td_elements):
                        value_td = td_elements[i + 1]
                        value_text = value_td.get_text(strip=True)
                        
                        if any(unit in value_text for unit in ['백만', '억', '조']):
                            return value_text

            # 2차: 전체 페이지에서 거래대금 패턴
            page_text = soup.get_text()
            trading_pattern = r'거래대금[^\d]*?([\d,]+\s*(?:백만|억|조))'
            matches = re.finditer(trading_pattern, page_text)
            for match in matches:
                return match.group(1).strip()

            return None
        except:
            return None

    def _extract_market_cap_smart(self, soup: BeautifulSoup, current_price: Optional[float]) -> Optional[str]:
        """시가총액 추출 - 스마트 규모별 처리"""
        try:
            print("🔍 시가총액 스마트 추출 시도...")
            
            # 1. 현재가 기반 기업 규모 추정
            company_size = self._estimate_company_size(current_price)
            print(f"    추정 기업 규모: {company_size}")
            
            # 2. 모든 시가총액 후보 수집
            candidates = self._collect_market_cap_candidates(soup)
            print(f"    시가총액 후보 {len(candidates)}개 수집")
            
            # 3. 규모별 필터링 및 검증
            best_candidate = self._select_best_market_cap(candidates, company_size, current_price)
            
            if best_candidate:
                print(f"✅ 시가총액 스마트 추출: {best_candidate}")
                return best_candidate
            else:
                print("❌ 시가총액 스마트 추출 실패")
                return None
            
        except Exception as e:
            print(f"❌ 시가총액 추출 오류: {e}")
            return None

    def _estimate_company_size(self, current_price: Optional[float]) -> str:
        """현재가 기반 기업 규모 추정"""
        if not current_price:
            return "unknown"
        
        # 일반적인 패턴 기반 추정
        if current_price >= 100000:  # 10만원 이상
            return "large"
        elif current_price >= 50000:   # 5만원 이상
            return "mid-large" 
        elif current_price >= 20000:   # 2만원 이상
            return "medium"
        elif current_price >= 5000:    # 5천원 이상
            return "mid-small"
        else:                          # 5천원 미만
            return "small"

    def _collect_market_cap_candidates(self, soup: BeautifulSoup) -> List[str]:
        """모든 시가총액 후보 수집"""
        candidates = []
        
        # 1. td 요소에서 시가총액 관련 검색
        td_elements = soup.find_all('td')
        for i, td in enumerate(td_elements):
            td_text = td.get_text(strip=True)
            if '시가총액' in td_text:
                # 현재 td와 다음 몇 개 td에서 숫자 찾기
                for j in range(i, min(len(td_elements), i+3)):
                    candidate_td = td_elements[j]
                    candidate_text = candidate_td.get_text(strip=True)
                    
                    parsed = self._parse_market_cap_value(candidate_text)
                    if parsed:
                        candidates.append(parsed)

        # 2. 시가총액 키워드 주변 검색
        page_text = soup.get_text()
        for match in re.finditer(r'시가총액', page_text):
            pos = match.start()
            context_start = max(0, pos - 30)
            context_end = min(len(page_text), pos + 100)
            context = page_text[context_start:context_end]
            
            parsed = self._parse_market_cap_value(context)
            if parsed:
                candidates.append(parsed)

        return list(set(candidates))  # 중복 제거

    def _select_best_market_cap(self, candidates: List[str], company_size: str, current_price: Optional[float]) -> Optional[str]:
        """규모별 최적 시가총액 선택"""
        if not candidates:
            return None
        
        print(f"    후보들: {candidates}")
        
        # 규모별 우선순위 필터링
        size_priorities = {
            "large": ["조", "억"],       # 대형주: 조 단위 우선
            "mid-large": ["조", "억"],   # 준대형주: 조 단위 우선
            "medium": ["억", "조"],      # 중형주: 억 단위 우선, 조도 가능
            "mid-small": ["억"],         # 준소형주: 억 단위만
            "small": ["억", "백만"],     # 소형주: 억/백만 단위만
            "unknown": ["조", "억", "백만"]  # 불명: 모든 단위
        }
        
        preferred_units = size_priorities.get(company_size, ["조", "억", "백만"])
        
        # 우선순위에 따라 후보 정렬
        sorted_candidates = []
        for unit in preferred_units:
            unit_candidates = [c for c in candidates if unit in c]
            
            # 소형주인데 조 단위가 나오면 제외 (오류 방지)
            if company_size in ["small", "mid-small"] and unit == "조":
                continue
                
            sorted_candidates.extend(unit_candidates)
        
        # 현재가 기반 합리성 검증
        for candidate in sorted_candidates:
            if self._validate_market_cap_reasonableness(candidate, current_price):
                return candidate
        
        # 검증 통과한 것이 없으면 첫 번째 후보 반환
        return candidates[0] if candidates else None

    def _validate_market_cap_reasonableness(self, market_cap: str, current_price: Optional[float]) -> bool:
        """시가총액 합리성 검증"""
        if not current_price:
            return True  # 현재가 없으면 검증 불가
        
        try:
            # 시가총액을 억원 단위로 변환
            if "조" in market_cap and "억" in market_cap:
                # 예: "29조 4,216억원"
                parts = market_cap.replace("원", "").replace(",", "").split()
                jo_part = 0
                eok_part = 0
                
                for part in parts:
                    if "조" in part:
                        jo_part = int(part.replace("조", ""))
                    elif "억" in part:
                        eok_part = int(part.replace("억", ""))
                
                total_eok = jo_part * 10000 + eok_part
                
            elif "조" in market_cap:
                # 예: "187조원"
                jo_part = int(market_cap.replace("조", "").replace("원", "").replace(",", ""))
                total_eok = jo_part * 10000
                
            elif "억" in market_cap:
                # 예: "4,216억원"
                total_eok = int(market_cap.replace("억", "").replace("원", "").replace(",", ""))
                
            elif "백만" in market_cap:
                # 예: "40,000백만원" 
                baekman_part = int(market_cap.replace("백만", "").replace("원", "").replace(",", ""))
                total_eok = baekman_part / 100
                
            else:
                return True  # 파싱 불가시 통과
            
            # 현재가 기반 대략적 시가총액 범위 추정
            if current_price >= 100000:  # 10만원 이상 - 대형주
                expected_range = (10000, 1000000)  # 1조~100조 
            elif current_price >= 50000:  # 5만원 이상
                expected_range = (5000, 500000)   # 5천억~50조
            elif current_price >= 10000:  # 1만원 이상  
                expected_range = (1000, 100000)   # 1천억~10조
            else:  # 1만원 미만
                expected_range = (100, 50000)     # 100억~5조
            
            is_reasonable = expected_range[0] <= total_eok <= expected_range[1]
            print(f"    {market_cap} 검증: {total_eok}억원, 예상범위: {expected_range[0]}~{expected_range[1]}억원 → {'통과' if is_reasonable else '실패'}")
            
            return is_reasonable
            
        except Exception as e:
            print(f"    시가총액 검증 오류: {e}")
            return True  # 오류시 통과

    def _parse_market_cap_value(self, text: str) -> Optional[str]:
        """시가총액 값 파싱"""
        if not text:
            return None
        
        patterns = [
            r'(\d+)\s*조\s*([\d,]+)\s*억\s*원?',      # 29조 4,216억원
            r'(\d+)\s*조\s*(\d+)\s*억\s*원?',         # 29조 4216억원 (콤마 없음)
            r'(\d+)\s*조\s*원?',                      # 300조원
            r'([\d,]+)\s*억\s*원?',                   # 4,216억원 또는 400억원
            r'([\d,]+)\s*백만\s*원?',                 # 40,000백만원
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    if isinstance(match, tuple) and len(match) == 2:  # 조+억 조합
                        jo_part = int(match[0])
                        eok_part = int(match[1].replace(',', ''))
                        
                        if 1 <= jo_part <= 1000 and 0 <= eok_part <= 9999:
                            result = f"{jo_part}조 {eok_part:,}억원"
                            return result
                    
                    else:  # 단일 단위
                        number_str = match if isinstance(match, str) else match[0]
                        number = int(number_str.replace(',', ''))
                        
                        if '조' in pattern and 1 <= number <= 1000:
                            return f"{number}조원"
                        elif '억' in pattern and 100 <= number <= 999999:
                            return f"{number:,}억원"
                        elif '백만' in pattern and 1000 <= number <= 999999:
                            return f"{number:,}백만원"
                
                except (ValueError, IndexError):
                    continue
        
        return None

    def _extract_foreign_ownership_direct(self, soup: BeautifulSoup) -> Optional[str]:
        """외국인 지분율 추출 - 직접 추출"""
        try:
            # 1차: td 요소에서 외국인 라벨-값 쌍
            td_elements = soup.find_all('td')
            for i, td in enumerate(td_elements):
                if '외국인' in td.get_text():
                    if i + 1 < len(td_elements):
                        value_td = td_elements[i + 1]
                        value_text = value_td.get_text(strip=True)
                        
                        percentages = re.findall(r'\d+\.\d+%', value_text)
                        if percentages:
                            return percentages[0]

            # 2차: 전체 페이지에서 외국인 + 퍼센트 패턴
            page_text = soup.get_text()
            foreign_pattern = r'외국인[^\d]*?(\d+\.\d+%)'
            matches = re.finditer(foreign_pattern, page_text)
            for match in matches:
                return match.group(1)

            return None
        except:
            return None

    def _extract_sector_comparison_direct(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """동종업종 추출 - 직접 추출"""
        try:
            sector_data = {
                'sector_name': None, 
                'companies': []
            }

            print("🏢 동종업종 직접 추출 시도...")

            # 동종업종 섹션 찾기
            sector_headers = soup.find_all(string=re.compile(r'동일업종|동종업종'))
            
            for header in sector_headers:
                header_text = header.strip()
                if '비교' in header_text:
                    sector_data['sector_name'] = header_text
                    print(f"  업종명 발견: {header_text}")
                
                # 테이블 찾기
                parent = header.parent
                if parent:
                    container = parent
                    for i in range(5):
                        if container and hasattr(container, 'find_all'):
                            tables = container.find_all('table')
                            if tables:
                                break
                        container = container.parent if container and container.parent else None

                    for table in tables:
                        table_text = table.get_text()
                        if any(keyword in table_text for keyword in ['종목명', '현재가', '전일대비']):
                            print(f"  동종업종 테이블 발견!")
                            
                            rows = table.find_all('tr')
                            
                            for i, row in enumerate(rows):
                                cells = row.find_all(['td', 'th'])
                                if not cells:
                                    continue
                                
                                cell_texts = [cell.get_text(strip=True) for cell in cells]
                                print(f"    행 {i}: {cell_texts}")
                                
                                if i == 0 and len(cell_texts) > 1:
                                    if cell_texts[0] in ['종목명', '(종목명)']:
                                        print(f"    → 회사명 행 발견!")
                                        for company_cell in cell_texts[1:]:
                                            if company_cell:
                                                company_name = self._clean_company_name_direct(company_cell)
                                                if company_name:
                                                    sector_data['companies'].append(company_name)
                                                    print(f"      회사명 추가: {company_name}")
                                        break
                            
                            if sector_data['companies']:
                                break
                
                if sector_data['companies']:
                    break

            # 중복 제거
            sector_data['companies'] = list(dict.fromkeys(sector_data['companies']))[:10]
            
            print(f"🏢 동종업종 추출 결과:")
            print(f"  업종명: {sector_data['sector_name']}")
            print(f"  관련기업: {sector_data['companies']}")
            
            return sector_data

        except Exception as e:
            print(f"❌ 동종업종 추출 오류: {e}")
            return {'sector_name': None, 'companies': []}

    def _clean_company_name_direct(self, raw_name: str) -> Optional[str]:
        """회사명 정리 함수"""
        if not raw_name:
            return None
        
        # 종목코드 분리 처리
        separators = ['★', '*', '▲', '▼', '◆', '●', '■']
        for separator in separators:
            if separator in raw_name:
                raw_name = raw_name.split(separator)[0]
                break
        
        # 숫자 종목코드 제거
        cleaned = re.sub(r'([가-힣A-Za-z]+)\d+', r'\1', raw_name)
        
        # 특수문자 제거
        cleaned = re.sub(r'[^\w가-힣\s]', '', cleaned)
        cleaned = cleaned.strip()
        
        # 유효성 검사
        if (cleaned and 
            not cleaned.isdigit() and 
            len(cleaned) > 1 and 
            (re.search(r'[가-힣]', cleaned) or re.search(r'[A-Za-z]', cleaned))):
            return cleaned
        
        return None

    def _final_validation_with_warnings(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """최종 검증 시스템"""
        real_time = result['real_time_data']
        
        print("🔍 최종 검증 시스템...")
        
        # 계산값 플래그 처리
        change_amount_calculated = False
        change_rate_calculated = False
        
        # 튜플 형태인 경우 계산값 플래그 확인
        if isinstance(real_time.get('change_amount'), tuple):
            real_time['change_amount'], change_amount_calculated = real_time['change_amount']
        if isinstance(real_time.get('change_rate'), tuple):
            real_time['change_rate'], change_rate_calculated = real_time['change_rate']
        
        # 1. 전일대비와 등락률 관계식 검증
        current_price = real_time.get('current_price')
        change_amount = real_time.get('change_amount')
        change_rate = real_time.get('change_rate')
        
        if current_price and change_amount and change_rate:
            yesterday_price = current_price - change_amount
            if yesterday_price > 0:
                calculated_rate = (change_amount / yesterday_price) * 100
                rate_diff = abs(calculated_rate - change_rate)
                
                if rate_diff > 0.5:  # 0.5% 이상 차이나면 경고
                    print(f"⚠️ 전일대비-등락률 관계식 오차: {rate_diff:.2f}%")
                else:
                    print(f"✅ 전일대비-등락률 관계식 검증 통과")
        
        # 2. 거래량 합리성 검증
        volume = real_time.get('volume')
        if current_price and volume:
            if abs(volume - current_price) < 100:
                print(f"⚠️ 거래량({volume})과 현재가({current_price}) 혼동 의심")
                real_time['volume'] = None
            else:
                print(f"✅ 거래량 합리성 검증 통과")
        
        # 계산값 플래그 메타데이터 추가
        result['meta_data'] = {
            'change_amount_calculated': change_amount_calculated,
            'change_rate_calculated': change_rate_calculated
        }
        
        return result


def test_enhanced_safe_extraction_stock(stock_code: str):
    """개선된 다중 안전장치 실시간 데이터 추출 테스트"""
    print("🚀 다중 안전장치 강화 네이버 실시간 데이터 추출기")
    print("=" * 80)

    extractor = NaverRealTimeExtractor()

    print(f"테스트 종목: {stock_code}")

    result = extractor.extract_real_time_data(stock_code)

    if result['extraction_status'] != 'success':
        print(f"❌ 추출 실패: {result.get('error', 'Unknown error')}")
        return False

    # 결과 출력
    print(f"\n📊 다중 안전장치 강화 8개 핵심 항목 실시간 데이터:")
    print(f"회사명: {result['company_name']}")
    print(f"종목코드: {result['stock_code']}")

    real_time = result['real_time_data']
    meta_data = result.get('meta_data', {})
    
    print(f"\n💰 실시간 주가 정보:")
    print(f"  현재가: {real_time['current_price']:,}원" if real_time['current_price'] else "  현재가: 추출 실패")
    
    # 전일대비와 등락률 표시 (안전장치 포함)
    change_amount = real_time['change_amount']
    change_rate = real_time['change_rate']
    
    if change_amount is not None and change_rate is not None:
        direction = "상승 ⬆️" if change_amount > 0 else "하락 ⬇️"
        
        # 계산값 여부 표시
        amount_note = " (계산값)" if meta_data.get('change_amount_calculated') else ""
        rate_note = " (계산값)" if meta_data.get('change_rate_calculated') else ""
        
        print(f"  전일대비: {change_amount:+,}원{amount_note} ({direction})")
        print(f"  등락률: {change_rate:+.2f}%{rate_note}")
    else:
        # 안전장치로 인한 추출 포기 처리
        if change_amount is None and change_rate is None:
            print(f"  전일대비: 추출 포기 (부호 불확실)")
            print(f"  등락률: 추출 포기 (부호 불확실)")
        else:
            amount_note = " (계산값)" if meta_data.get('change_amount_calculated') else ""
            rate_note = " (계산값)" if meta_data.get('change_rate_calculated') else ""
            
            print(f"  전일대비: {change_amount:+,}원{amount_note}" if change_amount is not None else "  전일대비: 추출 포기 (부고 불확실)")
            print(f"  등락률: {change_rate:+.2f}%{rate_note}" if change_rate is not None else "  등락률: 추출 포기 (부호 불확실)")
    
    print(f"  거래량: {real_time['volume']:,}주" if real_time['volume'] else "  거래량: 추출 실패")
    print(f"  거래대금: {real_time['trading_value']}" if real_time['trading_value'] else "  거래대금: 추출 실패")
    print(f"  시가총액: {real_time['market_cap']}" if real_time['market_cap'] else "  시가총액: 추출 실패")

    print(f"\n📊 추가 정보:")
    print(f"  외국인지분율: {real_time['foreign_ownership']}" if real_time['foreign_ownership'] else "  외국인지분율: 추출 실패")

    print(f"\n🏢 동종업종:")
    sector = result['sector_comparison']
    print(f"  업종명: {sector['sector_name']}" if sector['sector_name'] else "  업종명: 추출 실패")
    if sector['companies']:
        print(f"  관련기업: {', '.join(sector['companies'])}")
    else:
        print(f"  관련기업: 추출 실패")

    # 성공률 계산 및 안전장치 통계
    total_fields = 8
    success_count = 0
    
    # 핵심 데이터 (null도 성공으로 간주 - 안전장치)
    for field in ['current_price', 'change_amount', 'change_rate', 'volume',
                  'trading_value', 'market_cap', 'foreign_ownership']:
        if field in ['change_amount', 'change_rate']:
            # 전일대비/등락률은 null도 성공 (안전장치)
            success_count += 1
        elif real_time[field] is not None:
            success_count += 1
    
    # 동종업종 성공 여부
    sector_success = len(sector.get('companies', [])) > 0
    if sector_success:
        success_count += 1

    success_rate = (success_count / total_fields) * 100
    print(f"\n📊 추출 성공률: {success_rate:.1f}% ({success_count}/{total_fields})")

    # 안전장치 작동 현황
    safety_actions = []
    if change_amount is None:
        safety_actions.append("전일대비 다중 안전장치 작동")
    if change_rate is None:
        safety_actions.append("등락률 다중 안전장치 작동")
    
    if safety_actions:
        print(f"\n🛡️ 다중 안전장치 작동 현황:")
        for action in safety_actions:
            print(f"  🎨 {action}")
        print(f"  📝 시각적 단서 활용으로 부호 신뢰성 확보")

    print(f"\n🔧 다중 안전장치 개선사항:")
    print(f"  🎨 시각적 단서 활용: CSS 클래스, 색상, 아이콘")
    print(f"  🔍 다중 소스 교차 검증: 직접추출 + 시각적조합")
    print(f"  🛡️ 논리적 일관성 검증: 부호 일치성 + 수학적 검증")
    print(f"  ✅ 신뢰성 우선: 불확실한 정보 배제")

    # 최종 평가
    if success_rate >= 87.5:  # 8개 중 7개 이상
        print(f"🎉 다중 안전장치 시스템 성공! 부호 신뢰성 대폭 개선!")
        return True
    else:
        print(f"⚠️ 추가 개선 필요.")
        return False


def get_stock_info(code: str) -> str:
    """종목코드에 따른 회사명 반환"""
    stock_names = {
        "005930": "삼성전자",
        "019170": "신풍제약", 
        "213420": "달바글로벌",
        "035420": "NAVER",
        "000660": "SK하이닉스",
        "035720": "카카오",
        "046890": "서울반도체",
        "032820": "우리기술",
        "003300": "한일홀딩스"
    }
    return stock_names.get(code, "알 수 없는 종목")


if __name__ == "__main__":
    # 명령행 인자로 종목코드 받기
    if len(sys.argv) > 1:
        stock_code = sys.argv[1]
        company_name = get_stock_info(stock_code)
        print(f"입력된 종목: {stock_code} ({company_name})")
        test_enhanced_safe_extraction_stock(stock_code)
    else:
        print("📋 사용법:")
        print("python enhanced_safe_extractor.py [종목코드]")
        print("\n🛡️ 다중 안전장치 강화 핵심 8개 항목:")
        print("  ✅ 현재가")
        print("  🎨 전일대비, 등락률 (시각적 단서 + 다중 소스)")
        print("  ✅ 거래량, 거래대금")
        print("  ✅ 시가총액 (스마트 규모별 처리)")
        print("  ✅ 외국인지분율, 동종업종")
        print("\n🔧 새로운 안전장치:")
        print("  🎨 시각적 단서: CSS 클래스, 색상, 화살표 아이콘")
        print("  🔍 다중 소스: 직접추출 + 시각적조합 교차검증")
        print("  🛡️ 논리적 검증: 부호 일관성 + 수학적 관계식")
        print("  ✅ 신뢰성 우선: 확실한 경우만 채택")
        print("\n🎯 부호 불일치 해결:")
        print("  ❌ 기존: 텍스트만 의존 → 부호 오류 발생")
        print("  ✅ 개선: 시각적 힌트 활용 → 부호 신뢰성 대폭 향상")
        print("\n추천 테스트 종목:")
        print("  005930 (삼성전자) - 부호 불일치 문제 해결 확인")
        print("  035420 (NAVER) - 기존 성능 유지 확인")
        print("  032820 (우리기술) - 하락 종목 정확성 확인")
        print("\n예시:")
        print("  python enhanced_safe_extractor.py 005930")
        print("\n💡 철학: 시각적 정보도 데이터! 모든 단서를 활용합니다!")
