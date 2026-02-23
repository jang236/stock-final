import requests
import json
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from datetime import datetime


class IntegratedFinancialSystem:
    """
    회사명 검색 + 재무데이터 추출 통합 시스템
    """

    def __init__(
            self,
            companies_file_path: str = "company_codes_20250617/stock_companies.json",
            urls_file_path: str = "company_codes_20250617/cf1001_urls_database.json"):
        """
        초기화 (새 URL 데이터베이스 연결)

        Args:
            companies_file_path: 회사 코드 JSON 파일 경로
            urls_file_path: cF1001 URL 데이터베이스 파일 경로
        """
        self.companies_file_path = companies_file_path
        self.urls_file_path = urls_file_path
        self.companies_data = {}
        self.urls_data = {}

        # 34개 재무항목 목록
        self.target_items = [
            "매출액", "영업이익", "영업이익(발표기준)", "세전계속사업이익", "당기순이익", "당기순이익(지배)",
            "당기순이익(비지배)", "자산총계", "부채총계", "자본총계", "자본총계(지배)", "자본총계(비지배)",
            "자본금", "영업활동현금흐름", "투자활동현금흐름", "재무활동현금흐름", "CAPEX", "FCF",
            "이자발생부채", "영업이익률", "순이익률", "ROE(%)", "ROA(%)", "부채비율", "자본유보율",
            "EPS(원)", "PER(배)", "BPS(원)", "PBR(배)", "현금DPS(원)", "현금배당수익률",
            "현금배당성향(%)", "발행주식수(보통주)"
        ]

        # 데이터 로드
        self._load_data()

    def _load_data(self):
        """데이터 파일들 로드"""
        try:
            # 회사 데이터 로드
            with open(self.companies_file_path, 'r', encoding='utf-8') as f:
                self.companies_data = json.load(f)
            print(f"✅ 회사 데이터 로드: {len(self.companies_data)}개 기업")

            # URL 데이터 로드
            with open(self.urls_file_path, 'r', encoding='utf-8') as f:
                self.urls_data = json.load(f)
            print(f"✅ 새 URL 데이터베이스 로드: {len(self.urls_data)}개 URL")

        except FileNotFoundError as e:
            print(f"❌ 파일을 찾을 수 없습니다: {e}")
            raise
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            raise

    def search_company(self, company_name: str) -> Optional[Dict]:
        """정확한 회사명으로 검색"""
        if not company_name or not company_name.strip():
            return None

        company_name = company_name.strip()

        if company_name in self.companies_data:
            company_info = self.companies_data[company_name]
            result = {
                'company_name': company_name,
                'company_code': company_info.get('code', ''),
                'match_type': 'exact'
            }

            # URL 정보 추가
            if company_name in self.urls_data:
                url_info = self.urls_data[company_name]
                result['cf1001_url'] = url_info.get('cF1001_url',
                                                    None)  # 대문자 F로 수정
                result['url_status'] = url_info.get('status', 'unknown')
                result['url_collected_at'] = url_info.get('collected_at', None)
                result['has_financial_data'] = True if result[
                    'cf1001_url'] else False
            else:
                result['cf1001_url'] = None
                result['url_status'] = 'not_collected'
                result['url_collected_at'] = None
                result['has_financial_data'] = False

            return result

        return None

    def extract_financial_data(self,
                               cf1001_url: str,
                               company_code: str = None) -> Dict[str, Any]:
        """cF1001 URL에서 재무데이터 추출"""
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
                "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
                "네이버 증권 cF1001 API (새 URL DB)"
            }
        }

        return result

    def get_complete_financial_data(self, company_name: str) -> Dict[str, Any]:
        """
        회사명으로 완전한 재무정보 추출 (통합 함수)

        Args:
            company_name: 정확한 회사명

        Returns:
            완전한 재무정보 딕셔너리
        """
        print(f"🔍 '{company_name}' 재무정보 추출 시작... (새 URL DB 사용)")

        # 1단계: 회사 검색
        company_info = self.search_company(company_name)
        if not company_info:
            raise ValueError(
                f"회사를 찾을 수 없습니다: '{company_name}'\n정확한 회사명을 입력해주세요.")

        print(
            f"✅ 회사 정보 확인: {company_info['company_name']} ({company_info['company_code']})"
        )

        # 2단계: URL 확인
        if not company_info['has_financial_data']:
            raise ValueError(
                f"'{company_name}'의 재무데이터 URL이 수집되지 않았습니다.\nURL 수집이 완료될 때까지 기다려주세요."
            )

        print(f"✅ 재무데이터 URL 확인됨 (수집일: {company_info['url_collected_at']})")

        # 3단계: 재무데이터 추출
        try:
            financial_data = self.extract_financial_data(
                company_info['cf1001_url'], company_info['company_code'])

            # 회사 정보 추가
            financial_data['company_info']['name'] = company_info[
                'company_name']
            financial_data['company_info']['url_collected_at'] = company_info[
                'url_collected_at']

            print(
                f"✅ 재무데이터 추출 완료: {financial_data['metadata']['success_rate']*100:.1f}% 성공"
            )

            return financial_data

        except Exception as e:
            raise Exception(f"재무데이터 추출 중 오류 발생: {str(e)}")

    def get_system_stats(self) -> Dict[str, Any]:
        """시스템 통계 정보"""
        total_companies = len(self.companies_data)
        companies_with_urls = len(self.urls_data)

        return {
            "total_companies":
            total_companies,
            "companies_with_urls":
            companies_with_urls,
            "url_coverage":
            companies_with_urls /
            total_companies if total_companies > 0 else 0,
            "target_financial_items":
            len(self.target_items),
            "database_version": "새 URL 데이터베이스 (2025-06-17/18)"
        }

    def test_new_urls(self, test_count: int = 5) -> Dict[str, Any]:
        """새 URL 데이터베이스 테스트 (5개 샘플)"""
        print(f"🧪 새 URL 데이터베이스 테스트 시작 ({test_count}개 샘플)")
        print("=" * 70)
        
        # 재무데이터가 있는 회사들 찾기
        companies_with_data = []
        for company_name in self.urls_data.keys():
            if company_name in self.companies_data:
                companies_with_data.append(company_name)
                if len(companies_with_data) >= test_count * 2:  # 여유있게 수집
                    break
        
        if len(companies_with_data) < test_count:
            test_count = len(companies_with_data)
            print(f"⚠️ 테스트 가능한 회사가 {test_count}개만 있습니다.")
        
        # 랜덤 선택
        import random
        test_companies = random.sample(companies_with_data, test_count)
        
        print(f"📋 선택된 테스트 기업들:")
        for i, company in enumerate(test_companies, 1):
            company_code = self.companies_data[company].get('code', 'Unknown')
            url_info = self.urls_data[company]
            print(f"{i}. {company} ({company_code}) - 수집일: {url_info.get('collected_at', 'Unknown')}")
        
        print("=" * 70)
        
        # 테스트 실행
        test_results = {
            'total_tests': test_count,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'success_rate': 0,
            'test_details': [],
            'errors': []
        }
        
        for i, company_name in enumerate(test_companies, 1):
            print(f"\n[{i}/{test_count}] 테스트: {company_name}")
            
            try:
                financial_data = self.get_complete_financial_data(company_name)
                test_results['successful_extractions'] += 1
                
                # 성공 정보 기록
                success_info = {
                    'company_name': company_name,
                    'company_code': financial_data['company_info']['code'],
                    'success_rate': financial_data['metadata']['success_rate'],
                    'extracted_items': financial_data['metadata']['extracted_items'],
                    'url_collected_at': financial_data['company_info']['url_collected_at']
                }
                test_results['test_details'].append(success_info)
                
                print(f"✅ 성공! 추출률: {financial_data['metadata']['success_rate']*100:.1f}%")
                
                # 주요 데이터 샘플 출력
                sample_items = ["매출액", "영업이익", "당기순이익"]
                for item in sample_items:
                    values = financial_data['financial_data'].get(item, [])
                    if values and values[0] is not None:
                        print(f"   {item}: {values[0]:,}" if isinstance(values[0], (int, float)) else f"   {item}: {values[0]}")
                
            except Exception as e:
                test_results['failed_extractions'] += 1
                test_results['errors'].append({
                    'company_name': company_name,
                    'error': str(e)
                })
                print(f"❌ 실패: {str(e)}")
            
            # 테스트 간 딜레이
            if i < test_count:
                print(f"⏰ 2초 대기...")
                import time
                time.sleep(2)
        
        # 최종 통계
        test_results['success_rate'] = test_results['successful_extractions'] / test_count if test_count > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"📊 새 URL DB 테스트 결과")
        print(f"{'='*70}")
        print(f"🎯 전체 테스트: {test_results['total_tests']}개")
        print(f"✅ 성공: {test_results['successful_extractions']}개")
        print(f"❌ 실패: {test_results['failed_extractions']}개")
        print(f"📈 성공률: {test_results['success_rate']*100:.1f}%")
        
        if test_results['success_rate'] >= 0.8:
            print(f"🎉 우수: 새 URL 데이터베이스가 정상적으로 작동합니다!")
        elif test_results['success_rate'] >= 0.6:
            print(f"⚠️ 양호: 대부분 정상 작동하지만 일부 개선이 필요합니다.")
        else:
            print(f"❌ 문제: 새 URL 데이터베이스에 문제가 있을 수 있습니다.")
        
        return test_results


def get_financial_data(company_name: str) -> Dict[str, Any]:
    """
    간편한 재무정보 추출 함수 (새 URL DB 사용)

    Args:
        company_name: 정확한 회사명

    Returns:
        완전한 재무정보 딕셔너리
    """
    system = IntegratedFinancialSystem()
    return system.get_complete_financial_data(company_name)


def test_new_url_database():
    """새 URL 데이터베이스 통합 테스트"""
    print("🚀 새 URL 데이터베이스 통합 재무정보 시스템 테스트")
    print("=" * 70)

    try:
        # 시스템 초기화
        system = IntegratedFinancialSystem()

        # 시스템 통계
        stats = system.get_system_stats()
        print(f"\n📊 시스템 통계:")
        print(f"  전체 기업: {stats['total_companies']:,}개")
        print(f"  새 URL 보유: {stats['companies_with_urls']:,}개 ({stats['url_coverage']*100:.1f}%)")
        print(f"  재무항목: {stats['target_financial_items']}개")
        print(f"  데이터베이스: {stats['database_version']}")

        # 새 URL DB 테스트
        test_results = system.test_new_urls(test_count=5)
        
        # 테스트 결과 파일 저장
        output_filename = f"new_url_db_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n💾 테스트 결과 저장: {output_filename}")

        return test_results['success_rate'] >= 0.6

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    # 새 URL 데이터베이스 통합 시스템 테스트 실행
    test_new_url_database()
