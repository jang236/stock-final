#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 네이버 증권 주가 데이터 완전 추출기 (향상된 버전)
- 현재가 추출 강화 (다층 폴백 시스템)
- 거래대금 단위 정확한 파싱
- 동종업종 종목 리스트 추출
- 100% 정확도 목표
"""

import requests
import re
import json
import sys
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional, Tuple
import time

class EnhancedUltimateExtractor:
    """향상된 네이버 증권 데이터 추출기"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def extract_perfect_data(self, stock_code: str) -> Dict[str, Any]:
        """완벽한 주가 데이터 추출"""
        
        print(f"🎯 {stock_code} 향상된 추출 시스템 시작...")
        
        # 네이버 증권 페이지 요청
        url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            return {"error": f"페이지 요청 실패: {e}"}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 회사명 추출
        company_name = self._extract_company_name(soup)
        
        # 결과 딕셔너리 초기화
        result = {
            "company_name": company_name,
            "stock_code": stock_code,
            "extraction_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "success_count": 0,
            "total_fields": 12
        }
        
        # 각 데이터 추출
        extractors = [
            ("current_price", self._extract_current_price_enhanced),
            ("change_data", self._extract_change_data_enhanced),
            ("trading_volume", self._extract_trading_volume_enhanced),
            ("trading_value", self._extract_trading_value_enhanced),
            ("market_cap", self._extract_market_cap_enhanced),
            ("week52_high", self._extract_52week_high),
            ("week52_low", self._extract_52week_low),
            ("foreign_ratio", self._extract_foreign_ratio),
            ("investment_opinion", self._extract_investment_opinion),
            ("sector_info", self._extract_sector_info_enhanced)
        ]
        
        for field_name, extractor_func in extractors:
            print(f"🔍 {field_name} 추출 중...")
            try:
                value = extractor_func(soup)
                result[field_name] = value
                if value is not None:
                    result["success_count"] += 1
                    print(f"✅ {field_name}: {value}")
                else:
                    print(f"❌ {field_name}: 추출 실패")
            except Exception as e:
                result[field_name] = None
                print(f"❌ {field_name}: 오류 - {e}")
        
        # 성공률 계산
        success_rate = (result["success_count"] / result["total_fields"]) * 100
        result["success_rate"] = round(success_rate, 1)
        
        # 품질 등급
        if success_rate >= 90:
            result["quality_grade"] = "🏆 완벽"
        elif success_rate >= 70:
            result["quality_grade"] = "🥇 우수"
        elif success_rate >= 50:
            result["quality_grade"] = "🥈 양호"
        else:
            result["quality_grade"] = "🥉 보통"
        
        return result
    
    def _extract_company_name(self, soup) -> Optional[str]:
        """회사명 추출"""
        try:
            # 여러 방법으로 회사명 찾기
            selectors = [
                'h2 a',
                '.wrap_company h2',
                'title'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text and len(text) > 1:
                        return text.split('(')[0].strip()
        except:
            pass
        return None
    
    def _extract_current_price_enhanced(self, soup) -> Optional[int]:
        """현재가 추출 - 강화된 다층 폴백 시스템"""
        
        # 1단계: 기존 blind 클래스 방식
        try:
            no_today = soup.find('div', class_='no_today')
            if no_today:
                price_element = no_today.find('span', class_='blind')
                if price_element:
                    price_text = price_element.get_text(strip=True).replace(',', '')
                    if price_text.isdigit():
                        price_value = int(price_text)
                        if 10 <= price_value <= 10000000:  # 합리적 범위
                            return price_value
        except:
            pass
        
        # 2단계: no_today 영역의 모든 숫자 패턴
        try:
            no_today = soup.find('div', class_='no_today')
            if no_today:
                text_content = no_today.get_text()
                price_patterns = re.findall(r'(\d{1,3}(?:,\d{3})*)', text_content)
                for pattern in price_patterns:
                    price_value = int(pattern.replace(',', ''))
                    if 10 <= price_value <= 10000000:
                        return price_value
        except:
            pass
        
        # 3단계: 페이지 전체에서 현재가 패턴 검색
        try:
            page_text = soup.get_text()
            # 현재가 주변 키워드와 함께 있는 숫자 찾기
            current_patterns = [
                r'현재가[:\s]*(\d{1,3}(?:,\d{3})*)',
                r'현재[:\s]*(\d{1,3}(?:,\d{3})*)',
                r'종가[:\s]*(\d{1,3}(?:,\d{3})*)'
            ]
            
            for pattern in current_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    price_value = int(match.replace(',', ''))
                    if 10 <= price_value <= 10000000:
                        return price_value
        except:
            pass
        
        # 4단계: 첫 번째 합리적인 가격 패턴
        try:
            price_patterns = re.findall(r'(\d{1,3}(?:,\d{3})*)', soup.get_text())
            for pattern in price_patterns:
                price_value = int(pattern.replace(',', ''))
                if 100 <= price_value <= 1000000:  # 더 좁은 합리적 범위
                    return price_value
        except:
            pass
        
        return None
    
    def _extract_change_data_enhanced(self, soup) -> Dict[str, Any]:
        """전일대비/등락률 추출 - 향상된 방향 판단"""
        
        result = {
            "change_amount": None,
            "change_rate": None,
            "direction": None
        }
        
        try:
            # no_exday 영역에서 전일대비/등락률 추출
            no_exday = soup.find('span', class_='no_exday')
            if not no_exday:
                no_exday = soup.find('div', class_='no_exday')
            
            if no_exday:
                text_content = no_exday.get_text()
                
                # 전일대비 숫자 추출
                change_patterns = re.findall(r'(\d{1,3}(?:,\d{3})*)', text_content)
                if len(change_patterns) >= 2:
                    change_amount = int(change_patterns[0].replace(',', ''))
                    change_rate = float(change_patterns[1].replace(',', ''))
                    
                    # 방향 판단 - 강화된 6단계 검증
                    direction = self._determine_direction_enhanced(soup, no_exday)
                    
                    # 부호 적용
                    if direction == "하락":
                        change_amount = -abs(change_amount)
                        change_rate = -abs(change_rate)
                    else:
                        change_amount = abs(change_amount)
                        change_rate = abs(change_rate)
                    
                    result["change_amount"] = change_amount
                    result["change_rate"] = change_rate
                    result["direction"] = direction
        except Exception as e:
            print(f"전일대비 추출 오류: {e}")
        
        return result
    
    def _determine_direction_enhanced(self, soup, target_element) -> str:
        """향상된 방향 판단 시스템 - 7단계 검증"""
        
        up_signals = 0
        down_signals = 0
        
        print("    🎯 방향 판단 시작...")
        
        # 1단계: 타겟 요소 클래스 분석
        if target_element:
            classes = target_element.get('class', [])
            class_text = ' '.join(classes)
            
            down_keywords = ['down', 'minus', 'fall', 'decrease', 'red']
            up_keywords = ['up', 'plus', 'rise', 'increase', 'blue']
            
            for keyword in down_keywords:
                if keyword in class_text.lower():
                    down_signals += 1
                    print(f"    클래스 감지 (하락): {keyword}")
            
            for keyword in up_keywords:
                if keyword in class_text.lower():
                    up_signals += 1
                    print(f"    클래스 감지 (상승): {keyword}")
        
        # 2단계: 부모 요소들 분석 (5단계 상위까지)
        current = target_element
        for level in range(5):
            if current and current.parent:
                current = current.parent
                classes = current.get('class', [])
                class_text = ' '.join(classes)
                
                if any(keyword in class_text.lower() for keyword in ['down', 'minus', 'fall']):
                    down_signals += 1
                    print(f"    부모{level+1} 클래스 (하락): {class_text}")
                elif any(keyword in class_text.lower() for keyword in ['up', 'plus', 'rise']):
                    up_signals += 1
                    print(f"    부모{level+1} 클래스 (상승): {class_text}")
        
        # 3단계: 색상 분석 확장
        try:
            page_text = soup.get_text()
            style_elements = soup.find_all(attrs={"style": True})
            
            for element in style_elements:
                style = element.get('style', '').lower()
                if 'color' in style:
                    if any(color in style for color in ['red', '#ff', '#f00', 'rgb(255']):
                        down_signals += 1
                        print(f"    색상 감지 (하락): 빨간색")
                    elif any(color in style for color in ['blue', '#00f', '#0000ff', 'rgb(0,0,255']):
                        down_signals += 1  # 네이버에서는 파란색이 하락
                        print(f"    색상 감지 (하락): 파란색")
        except:
            pass
        
        # 4단계: 텍스트 키워드 분석 확장
        if target_element:
            text_content = target_element.get_text()
            
            down_patterns = [
                r'하락', r'▼', r'↓', r'감소', r'하향', r'-\d',
                r'마이너스', r'내림', r'떨어짐', r'▾'
            ]
            up_patterns = [
                r'상승', r'▲', r'↑', r'증가', r'상향', r'\+\d',
                r'플러스', r'오름', r'올라감', r'▴'
            ]
            
            for pattern in down_patterns:
                if re.search(pattern, text_content):
                    down_signals += 1
                    print(f"    키워드 감지 (하락): {pattern}")
            
            for pattern in up_patterns:
                if re.search(pattern, text_content):
                    up_signals += 1
                    print(f"    키워드 감지 (상승): {pattern}")
        
        # 5단계: 특수 기호 패턴
        if target_element:
            text = target_element.get_text()
            
            # 특수 패턴들
            if re.search(r'▼\s*\d+', text):
                down_signals += 2
                print(f"    특수 패턴 (하락): ▼숫자")
            elif re.search(r'▲\s*\d+', text):
                up_signals += 2
                print(f"    특수 패턴 (상승): ▲숫자")
            
            if re.search(r'-\s*\d+', text):
                down_signals += 1
                print(f"    특수 패턴 (하락): -숫자")
            elif re.search(r'\+\s*\d+', text):
                up_signals += 1
                print(f"    특수 패턴 (상승): +숫자")
        
        # 6단계: 주변 요소 분석
        if target_element:
            siblings = target_element.find_next_siblings()[:3]
            for sibling in siblings:
                if sibling:
                    sibling_text = sibling.get_text()
                    if any(keyword in sibling_text for keyword in ['하락', '▼', '감소']):
                        down_signals += 1
                        print(f"    주변 요소 (하락): {sibling_text[:20]}")
                    elif any(keyword in sibling_text for keyword in ['상승', '▲', '증가']):
                        up_signals += 1
                        print(f"    주변 요소 (상승): {sibling_text[:20]}")
        
        # 7단계: 최종 결정
        print(f"    방향 신호: 상승 {up_signals}, 하락 {down_signals}")
        
        if down_signals > up_signals:
            result = "하락"
            print(f"    → 최종 방향: {result} (하락 신호 우세)")
        elif up_signals > down_signals:
            result = "상승"
            print(f"    → 최종 방향: {result} (상승 신호 우세)")
        else:
            # 동점일 경우 추가 판단
            result = "보합" if down_signals == 0 and up_signals == 0 else "하락"
            print(f"    → 최종 방향: {result} (기본값)")
        
        return result
    
    def _extract_trading_volume_enhanced(self, soup) -> Optional[str]:
        """거래량 추출 - 향상된 정확도"""
        
        try:
            # 1단계: 거래량 키워드 주변 검색
            page_text = soup.get_text()
            volume_patterns = [
                r'거래량[:\s]*(\d{1,3}(?:,\d{3})*)',
                r'거래량.*?(\d{1,3}(?:,\d{3})*)',
                r'Volume[:\s]*(\d{1,3}(?:,\d{3})*)'
            ]
            
            for pattern in volume_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    volume = int(match.replace(',', ''))
                    if 1 <= volume <= 100000000:  # 1주 ~ 1억주
                        return f"{match}주"
            
            # 2단계: 테이블에서 거래량 찾기
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        if '거래량' in cell.get_text():
                            if i + 1 < len(cells):
                                volume_text = cells[i + 1].get_text(strip=True)
                                volume_match = re.search(r'(\d{1,3}(?:,\d{3})*)', volume_text)
                                if volume_match:
                                    volume = int(volume_match.group(1).replace(',', ''))
                                    if 1 <= volume <= 100000000:
                                        return f"{volume_match.group(1)}주"
            
            # 3단계: 차트 영역 우선 검색
            chart_area = soup.find('div', {'id': 'chart_area'})
            if chart_area:
                volume_match = re.search(r'(\d{1,3}(?:,\d{3})*)', chart_area.get_text())
                if volume_match:
                    volume = int(volume_match.group(1).replace(',', ''))
                    if 1000 <= volume <= 50000000:  # 더 좁은 범위
                        return f"{volume_match.group(1)}주"
            
        except Exception as e:
            print(f"거래량 추출 오류: {e}")
        
        return None
    
    def _extract_trading_value_enhanced(self, soup) -> Optional[str]:
        """거래대금 추출 - 정확한 단위 처리"""
        
        try:
            page_text = soup.get_text()
            
            # 거래대금 패턴들 (단위별로 정확히 구분)
            patterns = [
                (r'거래대금[:\s]*(\d{1,3}(?:,\d{3})*)\s*억', '억원'),
                (r'거래대금[:\s]*(\d{1,3}(?:,\d{3})*)\s*백만', '백만원'),
                (r'거래대금[:\s]*(\d{1,3}(?:,\d{3})*)\s*천만', '천만원'),
                (r'(\d{1,3}(?:,\d{3})*)\s*억.*?거래', '억원'),
                (r'(\d{1,3}(?:,\d{3})*)\s*백만.*?거래', '백만원')
            ]
            
            for pattern, unit in patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    value = int(match.replace(',', ''))
                    
                    # 합리적 범위 검증
                    if unit == '억원' and 1 <= value <= 50000:
                        return f"{match}억원"
                    elif unit == '백만원' and 1 <= value <= 500000:
                        # 100백만 이상이면 억 단위로 변환
                        if value >= 100:
                            converted_value = value // 100
                            remainder = value % 100
                            if remainder == 0:
                                return f"{converted_value}억원"
                            else:
                                return f"{converted_value}.{remainder:02d}억원"
                        else:
                            return f"{match}백만원"
                    elif unit == '천만원' and 1 <= value <= 10000:
                        return f"{match}천만원"
            
            # 일반적인 숫자 패턴에서 거래대금 추정
            trading_patterns = re.findall(r'(\d{1,3}(?:,\d{3})*)', page_text)
            for pattern in trading_patterns:
                value = int(pattern.replace(',', ''))
                # 전형적인 거래대금 범위 (억 단위)
                if 10 <= value <= 10000:
                    # 주변 텍스트에서 거래대금 관련 키워드 확인
                    context_start = max(0, page_text.find(pattern) - 50)
                    context_end = min(len(page_text), page_text.find(pattern) + 50)
                    context = page_text[context_start:context_end]
                    
                    if any(keyword in context for keyword in ['거래대금', '거래금액', 'trading']):
                        return f"{pattern}억원"
            
        except Exception as e:
            print(f"거래대금 추출 오류: {e}")
        
        return None
    
    def _extract_market_cap_enhanced(self, soup) -> Optional[str]:
        """시가총액 추출 - 향상된 정확도"""
        
        try:
            page_text = soup.get_text()
            
            # 시가총액 패턴들
            patterns = [
                r'시가총액[:\s]*(\d{1,3}(?:,\d{3})*)\s*조',
                r'시가총액[:\s]*(\d{1,3}(?:,\d{3})*)\s*억',
                r'시총[:\s]*(\d{1,3}(?:,\d{3})*)\s*조',
                r'시총[:\s]*(\d{1,3}(?:,\d{3})*)\s*억'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    value = int(match.replace(',', ''))
                    
                    if '조' in pattern and 1 <= value <= 1000:
                        return f"{match}조원"
                    elif '억' in pattern and 1 <= value <= 100000:
                        return f"{match}억원"
            
            # 테이블에서 시가총액 찾기
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        cell_text = cell.get_text(strip=True)
                        if '시가총액' in cell_text or '시총' in cell_text:
                            if i + 1 < len(cells):
                                value_cell = cells[i + 1]
                                value_text = value_cell.get_text(strip=True)
                                
                                # 조원 단위
                                trillion_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*조', value_text)
                                if trillion_match:
                                    return f"{trillion_match.group(1)}조원"
                                
                                # 억원 단위
                                billion_match = re.search(r'(\d{1,3}(?:,\d{3})*)\s*억', value_text)
                                if billion_match:
                                    return f"{billion_match.group(1)}억원"
            
        except Exception as e:
            print(f"시가총액 추출 오류: {e}")
        
        return None
    
    def _extract_52week_high(self, soup) -> Optional[str]:
        """52주 최고가 추출"""
        
        try:
            page_text = soup.get_text()
            
            patterns = [
                r'52주.*?최고[:\s]*(\d{1,3}(?:,\d{3})*)',
                r'최고가[:\s]*(\d{1,3}(?:,\d{3})*)',
                r'High[:\s]*(\d{1,3}(?:,\d{3})*)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    value = int(match.replace(',', ''))
                    if 100 <= value <= 10000000:
                        return f"{match}원"
        except:
            pass
        
        return None
    
    def _extract_52week_low(self, soup) -> Optional[str]:
        """52주 최저가 추출"""
        
        try:
            page_text = soup.get_text()
            
            patterns = [
                r'52주.*?최저[:\s]*(\d{1,3}(?:,\d{3})*)',
                r'최저가[:\s]*(\d{1,3}(?:,\d{3})*)',
                r'Low[:\s]*(\d{1,3}(?:,\d{3})*)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    value = int(match.replace(',', ''))
                    if 10 <= value <= 1000000:
                        return f"{match}원"
        except:
            pass
        
        return None
    
    def _extract_foreign_ratio(self, soup) -> Optional[str]:
        """외국인지분율 추출"""
        
        try:
            page_text = soup.get_text()
            
            patterns = [
                r'외국인지분율[:\s]*(\d+(?:\.\d+)?)\s*%',
                r'외국인[:\s]*(\d+(?:\.\d+)?)\s*%',
                r'외인[:\s]*(\d+(?:\.\d+)?)\s*%'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    ratio = float(match)
                    if 0 <= ratio <= 100:
                        return f"{match}%"
        except:
            pass
        
        return None
    
    def _extract_investment_opinion(self, soup) -> Optional[str]:
        """투자의견 추출"""
        
        try:
            # 투자의견 관련 키워드들
            opinion_keywords = ['매수', '매도', '보유', '중립', 'BUY', 'SELL', 'HOLD']
            
            # 테이블에서 투자의견 찾기
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        if '투자의견' in cell.get_text() or 'opinion' in cell.get_text().lower():
                            if i + 1 < len(cells):
                                opinion_text = cells[i + 1].get_text(strip=True)
                                for keyword in opinion_keywords:
                                    if keyword in opinion_text:
                                        return opinion_text
            
            # 페이지 전체에서 투자의견 패턴 찾기
            page_text = soup.get_text()
            for keyword in opinion_keywords:
                if keyword in page_text:
                    # 주변 텍스트와 함께 추출
                    start_idx = page_text.find(keyword)
                    context = page_text[max(0, start_idx-20):start_idx+20]
                    if '투자' in context or 'opinion' in context.lower():
                        return keyword
        except:
            pass
        
        return None
    
    def _extract_sector_info_enhanced(self, soup) -> Dict[str, Any]:
        """동종업종 정보 추출 - 향상된 버전"""
        
        result = {
            "sector_name": None,
            "sector_companies": []
        }
        
        try:
            # 1단계: 동종업종 섹션 찾기
            page_text = soup.get_text()
            
            # 업종명 추출
            sector_patterns = [
                r'동종업종[:\s]*([가-힣]+)',
                r'업종[:\s]*([가-힣]+)',
                r'섹터[:\s]*([가-힣]+)'
            ]
            
            for pattern in sector_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    if len(match) > 1:
                        result["sector_name"] = match
                        break
                if result["sector_name"]:
                    break
            
            # 2단계: 동종업종 종목 리스트 추출
            sector_companies = []
            
            # 방법 1: 동종업종 테이블 찾기
            tables = soup.find_all('table')
            for table in tables:
                table_text = table.get_text()
                if '동종업종' in table_text or '비교' in table_text:
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # 헤더 제외
                        cells = row.find_all(['td', 'th'])
                        if cells:
                            company_name = cells[0].get_text(strip=True)
                            # 한글 회사명 패턴 확인
                            if re.match(r'^[가-힣]+.*', company_name) and len(company_name) >= 2:
                                if company_name not in sector_companies:
                                    sector_companies.append(company_name)
            
            # 방법 2: 링크 패턴으로 종목 찾기
            if len(sector_companies) < 5:
                links = soup.find_all('a', href=re.compile(r'code=\d{6}'))
                for link in links:
                    company_name = link.get_text(strip=True)
                    if re.match(r'^[가-힣]+.*', company_name) and len(company_name) >= 2:
                        if company_name not in sector_companies:
                            sector_companies.append(company_name)
            
            # 방법 3: 일반적인 회사명 패턴 찾기
            if len(sector_companies) < 5:
                company_patterns = re.findall(r'([가-힣]{2,}(?:전자|화학|건설|금융|제약|바이오|테크|시스템|소프트|산업))', page_text)
                for company in company_patterns:
                    if company not in sector_companies:
                        sector_companies.append(company)
            
            # 상위 10개 종목만 반환
            result["sector_companies"] = sector_companies[:10]
            
        except Exception as e:
            print(f"동종업종 추출 오류: {e}")
        
        return result

def main():
    """메인 함수"""
    
    if len(sys.argv) != 2:
        print("사용법: python enhanced_ultimate_extractor.py <종목코드>")
        print("예시: python enhanced_ultimate_extractor.py 389680")
        sys.exit(1)
    
    stock_code = sys.argv[1]
    
    print(f"입력된 종목: {stock_code}")
    print("🎯 향상된 완전 해결 버전")
    print("=" * 80)
    
    # 추출기 실행
    extractor = EnhancedUltimateExtractor()
    result = extractor.extract_perfect_data(stock_code)
    
    # 결과 출력
    print("\n" + "=" * 80)
    print("📊 향상된 추출 결과 완성!")
    print("=" * 80)
    
    if "error" in result:
        print(f"❌ 오류: {result['error']}")
        return
    
    # 핵심 정보 출력
    print(f"회사명: {result.get('company_name', 'N/A')}")
    print(f"종목코드: {result.get('stock_code', 'N/A')}")
    
    print(f"\n💰 실시간 주가 정보:")
    print(f"  현재가: {result.get('current_price', 'N/A')}원" if result.get('current_price') else "  현재가: 추출 실패")
    
    change_data = result.get('change_data', {})
    if change_data.get('change_amount') is not None:
        direction_emoji = "⬆️" if change_data.get('direction') == "상승" else "⬇️" if change_data.get('direction') == "하락" else "➡️"
        print(f"  전일대비: {change_data.get('change_amount')}원 ({change_data.get('direction')} {direction_emoji})")
        print(f"  등락률: {change_data.get('change_rate')}%")
    else:
        print(f"  전일대비: 추출 실패")
        print(f"  등락률: 추출 실패")
    
    print(f"  거래량: {result.get('trading_volume', '추출 실패')}")
    print(f"  거래대금: {result.get('trading_value', '추출 실패')}")
    print(f"  시가총액: {result.get('market_cap', '추출 실패')}")
    
    print(f"\n📈 52주 정보:")
    print(f"  52주 최고: {result.get('week52_high', '추출 실패')}")
    print(f"  52주 최저: {result.get('week52_low', '추출 실패')}")
    
    print(f"\n📊 추가 정보:")
    print(f"  외국인지분율: {result.get('foreign_ratio', '추출 실패')}")
    print(f"  투자의견: {result.get('investment_opinion', '추출 실패')}")
    
    sector_info = result.get('sector_info', {})
    print(f"\n🏢 동종업종:")
    print(f"  업종명: {sector_info.get('sector_name', '추출 실패')}")
    companies = sector_info.get('sector_companies', [])
    if companies:
        print(f"  관련기업: {', '.join(companies[:5])}{'...' if len(companies) > 5 else ''}")
    else:
        print(f"  관련기업: 추출 실패")
    
    print(f"\n🎯 성과 지표:")
    print(f"  성공률: {result.get('success_rate', 0)}%")
    print(f"  품질 평가: {result.get('quality_grade', 'N/A')}")
    
    # JSON 파일로 저장
    filename = f"enhanced_perfect_{stock_code}_result.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📁 결과를 '{filename}'에 저장했습니다.")

if __name__ == "__main__":
    main()
