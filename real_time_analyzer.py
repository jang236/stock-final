import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional, Any


class NaverStockAnalyzer:
    """
    네이버 증권에서 실시간 주가 데이터 추출 분석기
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

    def analyze_stock_page(self, stock_code: str) -> Dict[str, Any]:
        """
        네이버 증권 페이지 분석

        Args:
            stock_code: 종목코드 (예: "005930")

        Returns:
            분석된 데이터 딕셔너리
        """
        url = f"https://finance.naver.com/item/main.naver?code={stock_code}"

        print(f"🔍 네이버 증권 페이지 분석 시작: {stock_code}")
        print(f"URL: {url}")

        try:
            # 페이지 요청
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            print(f"✅ 페이지 요청 성공 (크기: {len(response.text)} bytes)")

            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')

            result = {
                'stock_code': stock_code,
                'url': url,
                'analysis_results': {}
            }

            # 1. 기본 실시간 데이터 분석
            result['analysis_results'][
                'basic_data'] = self._analyze_basic_data(soup)

            # 2. 52주 데이터 분석
            result['analysis_results'][
                'week52_data'] = self._analyze_52week_data(soup)

            # 3. 거래 정보 분석
            result['analysis_results'][
                'trading_data'] = self._analyze_trading_data(soup)

            # 4. 동종업종 비교 분석
            result['analysis_results'][
                'sector_data'] = self._analyze_sector_comparison(soup)

            # 5. 전체 페이지 구조 분석
            result['analysis_results'][
                'page_structure'] = self._analyze_page_structure(soup)

            return result

        except Exception as e:
            print(f"❌ 페이지 분석 실패: {e}")
            return {'error': str(e), 'stock_code': stock_code}

    def _analyze_basic_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """기본 실시간 데이터 분석"""
        print("📊 기본 실시간 데이터 분석 중...")

        basic_data = {
            'current_price': None,
            'change': None,
            'change_rate': None,
            'volume': None,
            'market_cap': None,
            'found_elements': []
        }

        # 현재가 찾기 (여러 패턴 시도)
        price_patterns = [
            'span.blind', '.no_today .blind', '#_nowVal', '.no_today',
            'em.no_today'
        ]

        for pattern in price_patterns:
            elements = soup.select(pattern)
            if elements:
                for elem in elements[:3]:  # 처음 3개만 확인
                    text = elem.get_text(strip=True)
                    if text and ',' in text and text.replace(',',
                                                             '').isdigit():
                        basic_data['found_elements'].append({
                            'pattern':
                            pattern,
                            'text':
                            text,
                            'type':
                            'possible_price'
                        })

        # 등락 정보 찾기
        change_patterns = [
            '.no_exday', '.change_rate', '.ico.ico_up', '.ico.ico_down'
        ]

        for pattern in change_patterns:
            elements = soup.select(pattern)
            if elements:
                for elem in elements[:2]:
                    text = elem.get_text(strip=True)
                    if text:
                        basic_data['found_elements'].append({
                            'pattern':
                            pattern,
                            'text':
                            text,
                            'type':
                            'possible_change'
                        })

        # 거래량 찾기
        volume_keywords = ['거래량', '거래대금']
        for keyword in volume_keywords:
            elements = soup.find_all(text=re.compile(keyword))
            for elem in elements[:2]:
                parent = elem.parent
                if parent:
                    basic_data['found_elements'].append({
                        'pattern':
                        f'text_search_{keyword}',
                        'text':
                        parent.get_text(strip=True),
                        'type':
                        'possible_volume'
                    })

        return basic_data

    def _analyze_52week_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """52주 최고/최저가 분석"""
        print("📈 52주 데이터 분석 중...")

        week52_data = {'high_52w': None, 'low_52w': None, 'found_elements': []}

        # 52주 관련 키워드 검색
        keywords = ['52주', '최고', '최저', '52week']

        for keyword in keywords:
            elements = soup.find_all(text=re.compile(keyword))
            for elem in elements[:3]:
                parent = elem.parent
                if parent:
                    week52_data['found_elements'].append({
                        'keyword':
                        keyword,
                        'text':
                        parent.get_text(strip=True),
                        'html':
                        str(parent)[:200]
                    })

        return week52_data

    def _analyze_trading_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """거래 정보 분석 (평균거래량, 외국인)"""
        print("💹 거래 정보 분석 중...")

        trading_data = {
            'avg_volume': None,
            'foreign_net': None,
            'found_elements': []
        }

        # 평균거래량 관련 키워드
        volume_keywords = ['평균거래량', '평균 거래량', '거래량']

        for keyword in volume_keywords:
            elements = soup.find_all(text=re.compile(keyword))
            for elem in elements[:2]:
                parent = elem.parent
                if parent:
                    trading_data['found_elements'].append({
                        'keyword':
                        keyword,
                        'text':
                        parent.get_text(strip=True),
                        'type':
                        'volume_related'
                    })

        # 외국인 관련 키워드
        foreign_keywords = ['외국인', '기관', '순매수', '순매도']

        for keyword in foreign_keywords:
            elements = soup.find_all(text=re.compile(keyword))
            for elem in elements[:2]:
                parent = elem.parent
                if parent:
                    trading_data['found_elements'].append({
                        'keyword':
                        keyword,
                        'text':
                        parent.get_text(strip=True),
                        'type':
                        'foreign_related'
                    })

        return trading_data

    def _analyze_sector_comparison(self,
                                   soup: BeautifulSoup) -> Dict[str, Any]:
        """동종업종 비교 분석"""
        print("🏢 동종업종 비교 분석 중...")

        sector_data = {
            'sector_name': None,
            'sector_companies': [],
            'found_elements': []
        }

        # 동종업종 관련 키워드
        sector_keywords = ['동종업종', '같은업종', '업종', '비교', '동일업종']

        for keyword in sector_keywords:
            elements = soup.find_all(text=re.compile(keyword))
            for elem in elements[:3]:
                parent = elem.parent
                if parent:
                    sector_data['found_elements'].append({
                        'keyword':
                        keyword,
                        'text':
                        parent.get_text(strip=True),
                        'html':
                        str(parent)[:300]
                    })

        # 테이블 형태의 비교 데이터 찾기
        tables = soup.find_all('table')
        for i, table in enumerate(tables[:5]):  # 처음 5개 테이블만
            table_text = table.get_text()
            if any(keyword in table_text for keyword in sector_keywords):
                sector_data['found_elements'].append({
                    'type': 'table',
                    'table_index': i,
                    'text': table_text[:500],
                    'html': str(table)[:500]
                })

        return sector_data

    def _analyze_page_structure(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """전체 페이지 구조 분석"""
        print("🔧 페이지 구조 분석 중...")

        structure = {
            'total_tables': len(soup.find_all('table')),
            'total_divs': len(soup.find_all('div')),
            'total_spans': len(soup.find_all('span')),
            'scripts_count': len(soup.find_all('script')),
            'main_classes': [],
            'important_ids': []
        }

        # 주요 클래스 찾기
        elements_with_class = soup.find_all(class_=True)
        class_counts = {}
        for elem in elements_with_class:
            for cls in elem.get('class', []):
                if cls not in class_counts:
                    class_counts[cls] = 0
                class_counts[cls] += 1

        # 자주 사용되는 클래스들
        sorted_classes = sorted(class_counts.items(),
                                key=lambda x: x[1],
                                reverse=True)
        structure['main_classes'] = sorted_classes[:10]

        # 중요한 ID들
        elements_with_id = soup.find_all(id=True)
        for elem in elements_with_id:
            elem_id = elem.get('id')
            if elem_id and ('price' in elem_id.lower() or 'now'
                            in elem_id.lower() or 'today' in elem_id.lower()):
                structure['important_ids'].append({
                    'id':
                    elem_id,
                    'tag':
                    elem.name,
                    'text':
                    elem.get_text(strip=True)[:100]
                })

        return structure


def test_stock_analyzer():
    """주식 분석기 테스트"""
    print("🚀 네이버 증권 실시간 데이터 분석기 테스트")
    print("=" * 60)

    analyzer = NaverStockAnalyzer()

    # 삼성전자로 테스트
    stock_code = "005930"
    print(f"테스트 종목: {stock_code} (삼성전자)")

    result = analyzer.analyze_stock_page(stock_code)

    if 'error' in result:
        print(f"❌ 분석 실패: {result['error']}")
        return False

    print(f"\n📊 분석 결과 요약:")
    print(f"종목코드: {result['stock_code']}")

    # 기본 데이터 결과
    basic = result['analysis_results']['basic_data']
    print(f"\n1. 기본 실시간 데이터:")
    print(f"   발견된 요소: {len(basic['found_elements'])}개")
    for elem in basic['found_elements'][:3]:
        print(f"   - {elem['type']}: {elem['text'][:50]}")

    # 52주 데이터 결과
    week52 = result['analysis_results']['week52_data']
    print(f"\n2. 52주 데이터:")
    print(f"   발견된 요소: {len(week52['found_elements'])}개")
    for elem in week52['found_elements'][:2]:
        print(f"   - {elem['keyword']}: {elem['text'][:50]}")

    # 거래 정보 결과
    trading = result['analysis_results']['trading_data']
    print(f"\n3. 거래 정보:")
    print(f"   발견된 요소: {len(trading['found_elements'])}개")
    for elem in trading['found_elements'][:3]:
        print(f"   - {elem['type']}: {elem['text'][:50]}")

    # 동종업종 결과
    sector = result['analysis_results']['sector_data']
    print(f"\n4. 동종업종 비교:")
    print(f"   발견된 요소: {len(sector['found_elements'])}개")
    for elem in sector['found_elements'][:2]:
        print(f"   - {elem['keyword']}: {elem['text'][:50]}")

    # 페이지 구조
    structure = result['analysis_results']['page_structure']
    print(f"\n5. 페이지 구조:")
    print(f"   테이블: {structure['total_tables']}개")
    print(f"   주요 클래스: {structure['main_classes'][:3]}")
    print(f"   중요 ID: {len(structure['important_ids'])}개")

    # 결과 저장
    import json
    with open('naver_stock_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n📁 상세 분석 결과를 'naver_stock_analysis.json'에 저장했습니다.")
    print(f"✅ 1단계 페이지 분석 완료!")

    return True


if __name__ == "__main__":
    test_stock_analyzer()
