import requests
import json
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any


class FinancialDataExtractor:
    """
    네이버 증권 cF1001 API를 통한 완전한 재무데이터 추출 시스템
    """

    def __init__(self):
        self.target_items = [
            "매출액", "영업이익", "영업이익(발표기준)", "세전계속사업이익", "당기순이익", "당기순이익(지배)",
            "당기순이익(비지배)", "자산총계", "부채총계", "자본총계", "자본총계(지배)", "자본총계(비지배)",
            "자본금", "영업활동현금흐름", "투자활동현금흐름", "재무활동현금흐름", "CAPEX", "FCF",
            "이자발생부채", "영업이익률", "순이익률", "ROE(%)", "ROA(%)", "부채비율", "자본유보율",
            "EPS(원)", "PER(배)", "BPS(원)", "PBR(배)", "현금DPS(원)", "현금배당수익률",
            "현금배당성향(%)", "발행주식수(보통주)"
        ]

    def extract_financial_data(self,
                               cf1001_url: str,
                               company_code: str = None) -> Dict[str, Any]:
        """
        cF1001 URL에서 완전한 재무데이터 추출

        Args:
            cf1001_url: 완전한 cF1001 API URL
            company_code: 종목코드 (선택사항)

        Returns:
            완전한 재무데이터 딕셔너리
        """
        try:
            # AJAX 헤더 설정
            headers = {
                'Accept':
                'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With':
                'XMLHttpRequest',
                'User-Agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer':
                f'https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={company_code}'
                if company_code else 'https://navercomp.wisereport.co.kr'
            }

            # API 호출
            response = requests.get(cf1001_url, headers=headers, timeout=30)
            response.raise_for_status()

            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')

            # 실제 재무데이터 테이블 찾기
            financial_table = self._find_financial_table(soup)
            if not financial_table:
                raise ValueError("재무데이터 테이블을 찾을 수 없습니다")

            # 헤더 추출
            headers_data = self._extract_headers(financial_table)

            # 재무데이터 추출
            financial_data = self._extract_financial_items(financial_table)

            # 결과 포맷팅
            result = self._format_financial_response(financial_data,
                                                     headers_data,
                                                     company_code)

            return result

        except Exception as e:
            raise Exception(f"재무데이터 추출 실패: {str(e)}")

    def _find_financial_table(self, soup: BeautifulSoup) -> Optional[Any]:
        """실제 재무데이터가 포함된 테이블 찾기"""
        all_tables = soup.find_all('table')

        for table in all_tables:
            table_text = table.get_text()
            if '매출액' in table_text and '영업이익' in table_text and '자산총계' in table_text:
                return table

        return None

    def _extract_headers(self, table: Any) -> List[str]:
        """테이블에서 헤더(시계열 정보) 추출"""
        rows = table.find_all('tr')

        for row in rows:
            cells = [
                cell.get_text(strip=True)
                for cell in row.find_all(['th', 'td'])
            ]
            # 연도 정보가 포함된 행을 헤더로 인식
            if any('2022' in cell or '2023' in cell or '2024' in cell
                   or '2025' in cell for cell in cells):
                # 첫 번째 셀이 빈 경우 제거
                if cells and not cells[0]:
                    return cells[1:]
                return cells

        # 기본 헤더 반환
        return [
            '2022/12(IFRS연결)', '2023/12(IFRS연결)', '2024/12(IFRS연결)',
            '2025/12(E)(IFRS연결)', '2024/09(IFRS연결)', '2024/12(IFRS연결)',
            '2025/03(IFRS연결)', '2025/06(E)(IFRS연결)'
        ]

    def _extract_financial_items(self, table: Any) -> Dict[str, List[str]]:
        """테이블에서 재무항목 데이터 추출"""
        rows = table.find_all('tr')
        financial_data = {}

        for row in rows:
            cells = [
                cell.get_text(strip=True)
                for cell in row.find_all(['td', 'th'])
            ]

            if len(cells) > 1:  # 최소 2개 셀 필요
                item_name = cells[0]
                values = cells[1:]

                # 목표 재무항목과 매칭
                matched_target = self._match_financial_item(item_name)
                if matched_target:
                    financial_data[matched_target] = values

        return financial_data

    def _match_financial_item(self, item_name: str) -> Optional[str]:
        """재무항목명을 목표 항목과 매칭"""
        # 정확한 매칭 우선
        if item_name in self.target_items:
            return item_name

        # 부분 매칭
        for target_item in self.target_items:
            if target_item in item_name or item_name in target_item:
                # 더 정확한 매칭을 위한 추가 조건들
                if target_item == "영업이익(발표기준)" and "발표기준" in item_name:
                    return target_item
                elif target_item == "당기순이익(지배)" and "지배" in item_name and "당기순이익" in item_name:
                    return target_item
                elif target_item == "당기순이익(비지배)" and "비지배" in item_name and "당기순이익" in item_name:
                    return target_item
                elif target_item == "자본총계(지배)" and "지배" in item_name and "자본총계" in item_name:
                    return target_item
                elif target_item == "자본총계(비지배)" and "비지배" in item_name and "자본총계" in item_name:
                    return target_item
                elif "(" not in target_item and "(" not in item_name:  # 괄호 없는 일반 매칭
                    return target_item

        return None

    def _clean_financial_value(self, value: str) -> Optional[float]:
        """재무 데이터 값 정제 (문자열 → 숫자)"""
        if not value or value.strip() == '' or value == 'N/A':
            return None

        try:
            # 콤마 제거 및 마이너스 처리
            cleaned = value.replace(',', '').replace('\\-', '-').strip()
            if cleaned == '' or cleaned == '-':
                return None
            return float(cleaned)
        except (ValueError, TypeError):
            return None

    def _format_financial_response(self,
                                   financial_data: Dict[str, List[str]],
                                   headers: List[str],
                                   company_code: str = None) -> Dict[str, Any]:
        """최종 응답 형태로 포맷팅"""

        # 연간 데이터만 추출 (처음 4개 컬럼)
        annual_headers = headers[:4] if len(headers) >= 4 else headers
        annual_periods = []

        for header in annual_headers:
            # 연도/월 정보 추출 및 정리
            period_match = re.search(r'(\d{4}/\d{2})', header)
            if period_match:
                period = period_match.group(1)
                if '(E)' in header:
                    period += 'E'
                annual_periods.append(period)

        # 재무데이터 정리
        formatted_data = {}
        missing_items = []

        for target_item in self.target_items:
            if target_item in financial_data:
                raw_values = financial_data[target_item][:4]  # 연간 데이터만
                cleaned_values = [
                    self._clean_financial_value(val) for val in raw_values
                ]
                formatted_data[target_item] = cleaned_values
            else:
                formatted_data[target_item] = [None, None, None, None]
                missing_items.append(target_item)

        # 최종 결과
        result = {
            "company_info": {
                "code": company_code,
                "extracted_at": self._get_current_timestamp()
            },
            "financial_data": formatted_data,
            "periods": annual_periods,
            "metadata": {
                "total_items":
                len(self.target_items),
                "extracted_items":
                len(self.target_items) - len(missing_items),
                "success_rate": (len(self.target_items) - len(missing_items)) /
                len(self.target_items),
                "missing_items":
                missing_items,
                "data_source":
                "네이버 증권 cF1001 API"
            }
        }

        return result

    def _get_current_timestamp(self) -> str:
        """현재 시간 타임스탬프"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_company_financial_data(company_name: str = None,
                               company_code: str = None,
                               cf1001_url: str = None) -> Dict[str, Any]:
    """
    회사명 또는 종목코드로 재무정보 추출

    Args:
        company_name: 회사명 (예: "삼성전자")
        company_code: 종목코드 (예: "005930")
        cf1001_url: 직접 제공된 cF1001 URL

    Returns:
        완전한 재무정보 딕셔너리
    """
    if not cf1001_url:
        raise ValueError(
            "현재는 cf1001_url을 직접 제공해야 합니다. 추후 회사명/종목코드 검색 기능이 추가될 예정입니다.")

    extractor = FinancialDataExtractor()
    return extractor.extract_financial_data(cf1001_url, company_code)


# 테스트 함수
def test_financial_extraction():
    """재무데이터 추출 테스트"""
    print("🚀 재무데이터 추출 시스템 테스트 시작")
    print("=" * 60)

    # 테스트 URL (제공받은 성공 URL)
    test_url = "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=002360&fin_typ=0&freq_typ=A&encparam=dGFYekMzd3lrckdKVzdDU0p6cGFVQT09&id=hiddenfinGubun"

    try:
        # 재무데이터 추출
        result = get_company_financial_data(company_code="002360",
                                            cf1001_url=test_url)

        print("✅ 재무데이터 추출 성공!")
        print(f"📊 추출 성공률: {result['metadata']['success_rate']*100:.1f}%")
        print(
            f"📈 추출된 항목: {result['metadata']['extracted_items']}/{result['metadata']['total_items']}개"
        )
        print(f"📅 데이터 기간: {result['periods']}")

        # 샘플 데이터 출력
        print(f"\n💰 주요 재무데이터 샘플:")
        sample_items = ["매출액", "영업이익", "당기순이익", "자산총계", "ROE(%)"]
        for item in sample_items:
            values = result['financial_data'].get(item, [])
            print(f"  {item}: {values}")

        if result['metadata']['missing_items']:
            print(f"\n⚠️ 누락된 항목: {result['metadata']['missing_items']}")

        # JSON 저장
        with open('sample_financial_data.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n📁 결과를 'sample_financial_data.json'에 저장했습니다.")

        return result

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return None


if __name__ == "__main__":
    # 테스트 실행
    test_financial_extraction()
