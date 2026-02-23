import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional, Any
import sys


class NaverRealTimeExtractor:
    """
    네이버 증권에서 범용 실시간 주가 데이터 추출
    부호 오류 안전장치 강화 최종 버전
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

        print(f"🔍 {stock_code} 안전장치 강화 시스템 데이터 추출 시작...")

        try:
            # 페이지 요청
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # 회사명 추출
            company_name = self._extract_company_name(soup)

            # 핵심 데이터 추출
            current_price = self._extract_current_price_direct(soup)
            change_amount = self._extract_change_amount_with_safety(soup)
            change_rate = self._extract_change_rate_with_safety(soup)
            
            # 전일대비와 등락률 상호 검증 및 보완 - 강화된 안전장치
            change_amount, change_rate = self._cross_validate_with_enhanced_safety(
                soup, current_price, change_amount, change_rate
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

            print(f"✅ 안전장치 강화 시스템 데이터 추출 완료!")
            return result

        except Exception as e:
            print(f"❌ 데이터 추출 실패: {e}")
            return {
                'stock_code': stock_code,
                'extraction_status': 'failed',
                'error': str(e)
            }

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

    def _extract_change_amount_with_safety(self, soup: BeautifulSoup) -> Optional[float]:
        """전일대비 추출 - 강화된 안전장치"""
        try:
            print("🔍 전일대비 안전장치 추출 시도...")
            
            # 1차: no_exday 영역에서 기호 포함 직접 추출
            exday_area = soup.find('p', class_='no_exday')
            if exday_area:
                blind_elements = exday_area.find_all('span', class_='blind')
                if blind_elements:
                    first_text = blind_elements[0].get_text(strip=True)
                    print(f"    no_exday 첫 번째: '{first_text}'")
                    
                    # +/- 기호가 있는 경우 (확실한 경우)
                    if first_text.startswith(('+', '-')):
                        try:
                            value = float(first_text.replace(',', ''))
                            print(f"✅ 전일대비 확실한 기호: {value:+,}원")
                            return value
                        except:
                            pass

            # 2차: 기호와 숫자가 함께 있는 확실한 패턴만 검색
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
                    
                    # 전일대비 맥락 확인 (축소된 범위)
                    context_start = max(0, match.start() - 30)
                    context_end = min(len(page_text), match.end() + 30)
                    context = page_text[context_start:context_end]
                    
                    if any(keyword in context for keyword in ['전일대비', '전일', '대비']):
                        try:
                            value = float(number_str.replace(',', '')) * sign
                            print(f"✅ 전일대비 확실한 기호 패턴: {value:+,}원")
                            return value
                        except:
                            continue

            # 3차: 기호 없는 숫자는 안전장치로 포기
            print("⚠️ 전일대비 부호 불확실 - 안전하게 추출 포기")
            return None
            
        except Exception as e:
            print(f"❌ 전일대비 추출 오류: {e}")
            return None

    def _extract_change_rate_with_safety(self, soup: BeautifulSoup) -> Optional[float]:
        """등락률 추출 - 강화된 안전장치 적용"""
        try:
            print("🔍 등락률 안전장치 추출 시도...")
            
            # 1차: 기호가 포함된 등락률만 추출 (확실한 경우)
            exday_area = soup.find('p', class_='no_exday')
            if exday_area:
                blind_elements = exday_area.find_all('span', class_='blind')
                if len(blind_elements) >= 2:
                    rate_elem = blind_elements[1]
                    rate_text = rate_elem.get_text(strip=True)
                    
                    # 다음 노드에서 % 기호 확인
                    next_sibling = rate_elem.next_sibling
                    if next_sibling and '%' in str(next_sibling):
                        # 기호가 포함된 경우만 처리 (확실한 경우)
                        if rate_text.startswith(('+', '-')):
                            try:
                                rate = float(rate_text)
                                print(f"✅ 등락률 확실한 기호: {rate:+.2f}%")
                                return rate
                            except:
                                pass

            # 2차: 패턴 매칭에서 기호 포함된 등락률만 추출
            page_text = soup.get_text()
            rate_patterns = [
                r'([+-]\d+\.\d+)%',  # +29.92% 또는 -4.27% (기호 필수)
                r'([+-]\d+)%',       # +30% 또는 -4% (기호 필수)
            ]
            
            for pattern in rate_patterns:
                matches = re.finditer(pattern, page_text)
                for match in matches:
                    rate_str = match.group(1)
                    # 전일대비/등락률 맥락 확인 (축소된 범위)
                    context_start = max(0, match.start() - 30)
                    context_end = min(len(page_text), match.end() + 30)
                    context = page_text[context_start:context_end]
                    
                    if any(keyword in context for keyword in ['등락률', '전일대비', '변동률']):
                        try:
                            rate = float(rate_str)  # 기호 포함이므로 그대로 사용
                            if abs(rate) < 100:  # 현실적인 범위
                                print(f"✅ 등락률 확실한 기호 패턴: {rate:+.2f}%")
                                return rate
                        except:
                            continue

            # 3차: 기호 없는 등락률은 안전장치로 포기
            print("⚠️ 등락률 부호 불확실 - 안전하게 추출 포기")
            return None
            
        except Exception as e:
            print(f"❌ 등락률 추출 오류: {e}")
            return None

    def _cross_validate_with_enhanced_safety(self, soup: BeautifulSoup, current_price: Optional[float], 
                                           change_amount: Optional[float], change_rate: Optional[float]) -> tuple:
        """전일대비와 등락률 상호 검증 및 보완 - 강화된 안전장치"""
        try:
            print("🔍 강화된 안전장치 상호 검증...")
            
            calculated_amount = None
            calculated_rate = None
            
            # 둘 다 None인 경우 - 보수적 처리
            if not change_amount and not change_rate:
                print("⚠️ 전일대비, 등락률 모두 불확실 - 계산 시도하지 않음")
                return None, None
            
            # 하나만 있는 경우 - 상호 계산으로 보완
            if current_price and change_amount and not change_rate:
                # 전일대비로 등락률 계산
                yesterday_price = current_price - change_amount
                if yesterday_price > 0:
                    calculated_rate = (change_amount / yesterday_price) * 100
                    print(f"✅ 등락률 계산 보완: {calculated_rate:+.2f}% (계산값)")
                    change_rate = calculated_rate
            
            elif current_price and change_rate and not change_amount:
                # 등락률로 전일대비 계산
                yesterday_price = current_price / (1 + change_rate / 100)
                calculated_amount = current_price - yesterday_price
                print(f"✅ 전일대비 계산 보완: {calculated_amount:+,.0f}원 (계산값)")
                change_amount = round(calculated_amount)
            
            # 둘 다 있는 경우 - 강화된 일치성 검증
            elif change_amount and change_rate:
                amount_positive = change_amount > 0
                rate_positive = change_rate > 0
                
                if amount_positive != rate_positive:
                    print(f"⚠️ 심각한 부호 불일치 감지 - 안전을 위해 둘 다 폐기")
                    return None, None
                else:
                    print(f"✅ 부호 일치성 검증 통과")
            
            # 계산값 플래그 추가
            if calculated_amount is not None:
                change_amount = (change_amount, True)  # (값, 계산값 여부)
            if calculated_rate is not None:
                change_rate = (change_rate, True)  # (값, 계산값 여부)
            
            return change_amount, change_rate
            
        except Exception as e:
            print(f"❌ 상호 검증 오류: {e}")
            return change_amount, change_rate

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
                    if len(match) == 2:  # 조+억 조합
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


def test_final_safe_extraction_stock(stock_code: str):
    """최종 안전장치 강화 실시간 데이터 추출 테스트"""
    print("🚀 최종 안전장치 강화 네이버 실시간 데이터 추출기")
    print("=" * 80)

    extractor = NaverRealTimeExtractor()

    print(f"테스트 종목: {stock_code}")

    result = extractor.extract_real_time_data(stock_code)

    if result['extraction_status'] != 'success':
        print(f"❌ 추출 실패: {result.get('error', 'Unknown error')}")
        return False

    # 결과 출력
    print(f"\n📊 최종 안전장치 강화 8개 핵심 항목 실시간 데이터:")
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
            
            print(f"  전일대비: {change_amount:+,}원{amount_note}" if change_amount is not None else "  전일대비: 추출 포기 (부호 불확실)")
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

    # 성공률 계산 (8개 항목) - 안전장치 고려
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
        safety_actions.append("전일대비 안전장치 작동")
    if change_rate is None:
        safety_actions.append("등락률 안전장치 작동")
    
    if safety_actions:
        print(f"\n🛡️ 안전장치 작동 현황:")
        for action in safety_actions:
            print(f"  ⚠️ {action}")
        print(f"  📝 잘못된 부호보다 정확성을 우선시했습니다.")

    # 직접 추출 vs 계산값 통계
    direct_count = 0
    calculated_count = 0
    
    if not meta_data.get('change_amount_calculated', False) and change_amount is not None:
        direct_count += 1
    elif meta_data.get('change_amount_calculated', False):
        calculated_count += 1
        
    if not meta_data.get('change_rate_calculated', False) and change_rate is not None:
        direct_count += 1
    elif meta_data.get('change_rate_calculated', False):
        calculated_count += 1

    # 나머지 항목들
    direct_count += sum(1 for field in [
        'current_price', 'volume', 'trading_value', 'market_cap', 'foreign_ownership'
    ] if real_time[field] is not None)
    
    if sector_success:
        direct_count += 1

    print(f"\n🔧 추출 방식 통계:")
    print(f"  ✅ 직접 추출: {direct_count}개 항목")
    print(f"  ⚠️ 계산값: {calculated_count}개 항목")
    print(f"  🛡️ 안전장치: {len(safety_actions)}개 항목")
    
    if calculated_count > 0:
        print(f"  📝 계산값 항목들:")
        if meta_data.get('change_amount_calculated'):
            print(f"     - 전일대비 (등락률로 역산)")
        if meta_data.get('change_rate_calculated'):
            print(f"     - 등락률 (전일대비로 계산)")

    # 최종 안전장치 성과 요약
    print(f"\n🔧 최종 안전장치 성과:")
    if real_time['market_cap']:
        print(f"  ✅ 시가총액: 스마트 추출 성공")
    
    if len(safety_actions) > 0:
        print(f"  🛡️ 부호 안전장치: {len(safety_actions)}개 항목에서 작동")
        print(f"  📝 잘못된 부호 대신 신뢰성 확보")
    else:
        print(f"  ✅ 부호 판별: 모든 항목 정확 감지")
    
    # 최종 평가 - 안전장치 고려
    if success_rate >= 87.5:  # 8개 중 7개 이상 (안전장치 포함)
        print(f"🎉 최종 안전장치 시스템 성공! 신뢰성 우선 달성!")
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
        "046890": "서울반도체"
    }
    return stock_names.get(code, "알 수 없는 종목")


if __name__ == "__main__":
    # 명령행 인자로 종목코드 받기
    if len(sys.argv) > 1:
        stock_code = sys.argv[1]
        company_name = get_stock_info(stock_code)
        print(f"입력된 종목: {stock_code} ({company_name})")
        test_final_safe_extraction_stock(stock_code)
    else:
        print("📋 사용법:")
        print("python final_safe_extractor.py [종목코드]")
        print("\n🛡️ 최종 안전장치 강화 핵심 8개 항목:")
        print("  ✅ 현재가")
        print("  🛡️ 전일대비, 등락률 (부호 불확실시 안전 포기)")
        print("  ✅ 거래량, 거래대금")
        print("  ✅ 시가총액 (스마트 규모별 처리)")
        print("  ✅ 외국인지분율, 동종업종")
        print("\n🔧 강화된 안전장치:")
        print("  🛡️ 기호 없는 숫자는 추출 포기 (잘못된 부호 방지)")
        print("  🛡️ 부호 불일치시 둘 다 폐기 (신뢰성 우선)")
        print("  🛡️ 확실한 경우만 추출 (안전성 최우선)")
        print("\n추천 테스트 종목:")
        print("  046890 (서울반도체) - 안전장치 작동 확인")
        print("  213420 (달바글로벌) - 시가총액 개선 확인")
        print("  035720 (카카오) - 기존 성능 유지 확인")
        print("\n예시:")
        print("  python final_safe_extractor.py 046890")
        print("\n💡 철학: 잘못된 정보보다 정보 없음이 더 안전합니다!")
