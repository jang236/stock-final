import requests
import json
import re
import os
import time
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any
from datetime import datetime


class EnhancedIntegratedFinancialSystem:
    """
    A/B 폴더 시스템을 지원하는 향상된 재무정보 추출 시스템
    - 활성 폴더 자동 감지 (company_codes_active 심볼릭 링크 사용)
    - A↔B 전환시 실시간 재로드
    - 기존 34개 재무항목 추출 로직 완전 유지
    """

    def __init__(self, auto_detect_active_folder: bool = True):
        """
        초기화
        
        Args:
            auto_detect_active_folder: 활성 폴더 자동 감지 사용 여부
        """
        self.auto_detect_active_folder = auto_detect_active_folder
        self.active_folder_link = "company_codes_active"
        self.current_active_folder = None
        self.last_check_time = 0
        self.check_interval = 5  # 5초마다 폴더 변경 확인
        
        # 현재 활성 폴더 경로
        self.companies_file_path = None
        self.urls_file_path = None
        
        # 데이터 저장
        self.companies_data = {}
        self.urls_data = {}

        # 34개 재무항목 목록 (기존과 동일)
        self.target_items = [
            "매출액", "영업이익", "영업이익(발표기준)", "세전계속사업이익", "당기순이익", "당기순이익(지배)",
            "당기순이익(비지배)", "자산총계", "부채총계", "자본총계", "자본총계(지배)", "자본총계(비지배)",
            "자본금", "영업활동현금흐름", "투자활동현금흐름", "재무활동현금흐름", "CAPEX", "FCF",
            "이자발생부채", "영업이익률", "순이익률", "ROE(%)", "ROA(%)", "부채비율", "자본유보율",
            "EPS(원)", "PER(배)", "BPS(원)", "PBR(배)", "현금DPS(원)", "현금배당수익률",
            "현금배당성향(%)", "발행주식수(보통주)"
        ]

        print(f"🎯 Enhanced Integrated Financial System 초기화")
        print(f"🔄 A/B 폴더 자동 감지: {'활성화' if auto_detect_active_folder else '비활성화'}")
        
        # 초기 데이터 로드
        self._update_active_folder()
        self._load_data()

    def _get_active_folder(self) -> Optional[str]:
        """현재 활성 폴더 확인"""
        try:
            if os.path.islink(self.active_folder_link):
                target = os.readlink(self.active_folder_link)
                # 절대 경로면 basename만 추출
                if os.path.isabs(target):
                    target = os.path.basename(target)
                return target
        except Exception as e:
            print(f"⚠️ 활성 폴더 확인 실패: {e}")
        return None

    def _update_active_folder(self):
        """활성 폴더 업데이트 및 경로 설정"""
        if not self.auto_detect_active_folder:
            # 자동 감지 비활성화시 기본 경로 사용
            self.companies_file_path = "company_codes/stock_companies.json"
            self.urls_file_path = "company_codes/cf1001_urls_database.json"
            return
        
        new_active_folder = self._get_active_folder()
        
        if new_active_folder != self.current_active_folder:
            self.current_active_folder = new_active_folder
            
            if new_active_folder:
                # 심볼릭 링크를 통한 경로 설정
                self.companies_file_path = os.path.join(self.active_folder_link, "stock_companies.json")
                self.urls_file_path = os.path.join(self.active_folder_link, "cf1001_urls_database.json")
                print(f"🔄 활성 폴더 변경 감지: {new_active_folder}")
            else:
                print(f"⚠️ 활성 폴더를 찾을 수 없습니다. 기본 경로 사용.")
                self.companies_file_path = "company_codes/stock_companies.json"
                self.urls_file_path = "company_codes/cf1001_urls_database.json"
        
        self.last_check_time = time.time()

    def _check_folder_change(self):
        """폴더 변경 확인 (필요시)"""
        if not self.auto_detect_active_folder:
            return
            
        current_time = time.time()
        if current_time - self.last_check_time > self.check_interval:
            old_folder = self.current_active_folder
            self._update_active_folder()
            
            # 폴더가 변경되었으면 데이터 재로드
            if self.current_active_folder != old_folder:
                print(f"🔄 폴더 전환 감지: {old_folder} → {self.current_active_folder}")
                print(f"📊 데이터 재로드 중...")
                self._load_data()

    def _load_data(self):
        """데이터 파일들 로드"""
        try:
            # 폴더 변경 확인
            self._check_folder_change()
            
            # 회사 데이터 로드
            with open(self.companies_file_path, 'r', encoding='utf-8') as f:
                self.companies_data = json.load(f)
            
            # URL 데이터 로드
            with open(self.urls_file_path, 'r', encoding='utf-8') as f:
                self.urls_data = json.load(f)
            
            folder_info = f"({self.current_active_folder})" if self.current_active_folder else ""
            print(f"✅ 데이터 로드 완료 {folder_info}")
            print(f"   회사 데이터: {len(self.companies_data):,}개 기업")
            print(f"   URL 데이터: {len(self.urls_data):,}개 URL")

        except FileNotFoundError as e:
            print(f"❌ 파일을 찾을 수 없습니다: {e}")
            print(f"💡 URL 수집이 완료되지 않았을 수 있습니다.")
            raise
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            raise

    def reload_data(self):
        """수동 데이터 재로드"""
        print(f"🔄 수동 데이터 재로드 요청...")
        self._update_active_folder()
        self._load_data()

    def search_company(self, company_name: str) -> Optional[Dict]:
        """정확한 회사명으로 검색 (기존 로직 유지)"""
        # 폴더 변경 확인
        self._check_folder_change()
        
        if not company_name or not company_name.strip():
            return None

        company_name = company_name.strip()

        if company_name in self.companies_data:
            company_info = self.companies_data[company_name]
            result = {
                'company_name': company_name,
                'company_code': company_info.get('code', ''),
                'match_type': 'exact',
                'active_folder': self.current_active_folder  # 활성 폴더 정보 추가
            }

            # URL 정보 추가
            if company_name in self.urls_data:
                url_info = self.urls_data[company_name]
                result['cf1001_url'] = url_info.get('cF1001_url', None)
                result['url_status'] = url_info.get('status', 'unknown')
                result['url_collected_at'] = url_info.get('collected_at', None)
                result['has_financial_data'] = True if result['cf1001_url'] else False
            else:
                result['cf1001_url'] = None
                result['url_status'] = 'not_collected'
                result['url_collected_at'] = None
                result['has_financial_data'] = False

            return result

        return None

    def extract_financial_data(self, cf1001_url: str, company_code: str = None) -> Dict[str, Any]:
        """cF1001 URL에서 재무데이터 추출 (기존 로직 완전 유지)"""
        try:
            # AJAX 헤더 설정
            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': f'https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={company_code}' if company_code else 'https://navercomp.wisereport.co.kr'
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
            result = self._format_financial_response(financial_data, headers_data, company_code)

            return result

        except Exception as e:
            raise Exception(f"재무데이터 추출 실패: {str(e)}")

    def _find_financial_table(self, soup: BeautifulSoup) -> Optional[Any]:
        """실제 재무데이터가 포함된 테이블 찾기 (기존 로직 유지)"""
        all_tables = soup.find_all('table')

        for table in all_tables:
            table_text = table.get_text()
            if '매출액' in table_text and '영업이익' in table_text and '자산총계' in table_text:
                return table

        return None

    def _extract_headers(self, table: Any) -> List[str]:
        """테이블에서 헤더(시계열 정보) 추출 — 연도 자동 계산"""
        rows = table.find_all('tr')
        current_year = datetime.now().year
        target_years = [str(y) for y in range(current_year - 3, current_year + 1)]

        for row in rows:
            cells = [cell.get_text(strip=True) for cell in row.find_all(['th', 'td'])]
            # 연도 정보가 포함된 행을 헤더로 인식 (동적 연도)
            if any(year in cell for year in target_years for cell in cells):
                # 첫 번째 셀이 빈 경우 제거
                if cells and not cells[0]:
                    return cells[1:]
                return cells

        # 기본 헤더 반환 (동적 연도)
        y = current_year
        return [f'{y-3}/12(IFRS연결)', f'{y-2}/12(IFRS연결)', f'{y-1}/12(IFRS연결)', f'{y}/12(E)(IFRS연결)', f'{y-1}/09(IFRS연결)', f'{y-1}/12(IFRS연결)', f'{y}/03(IFRS연결)', f'{y}/06(E)(IFRS연결)']

    def _extract_financial_items(self, table: Any) -> Dict[str, List[str]]:
        """테이블에서 재무항목 데이터 추출 (기존 로직 유지)"""
        rows = table.find_all('tr')
        financial_data = {}

        for row in rows:
            cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]

            if len(cells) > 1:  # 최소 2개 셀 필요
                item_name = cells[0]
                values = cells[1:]

                # 목표 재무항목과 매칭
                matched_target = self._match_financial_item(item_name)
                if matched_target:
                    financial_data[matched_target] = values

        return financial_data

    def _match_financial_item(self, item_name: str) -> Optional[str]:
        """재무항목명을 목표 항목과 매칭 (기존 로직 유지)"""
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
        """재무 데이터 값 정제 (기존 로직 유지)"""
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

    def _format_financial_response(self, financial_data: Dict[str, List[str]], headers: List[str], company_code: str = None) -> Dict[str, Any]:
        """최종 응답 형태로 포맷팅 (기존 로직 유지)"""

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
                cleaned_values = [self._clean_financial_value(val) for val in raw_values]
                formatted_data[target_item] = cleaned_values
            else:
                formatted_data[target_item] = [None, None, None, None]
                missing_items.append(target_item)

        # 최종 결과
        result = {
            "company_info": {
                "code": company_code,
                "extracted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "active_folder": self.current_active_folder  # 활성 폴더 정보 추가
            },
            "financial_data": formatted_data,
            "periods": annual_periods,
            "metadata": {
                "total_items": len(self.target_items),
                "extracted_items": len(self.target_items) - len(missing_items),
                "success_rate": (len(self.target_items) - len(missing_items)) / len(self.target_items),
                "missing_items": missing_items,
                "data_source": "네이버 증권 cF1001 API",
                "active_folder": self.current_active_folder
            }
        }

        return result

    def get_complete_financial_data(self, company_name: str) -> Dict[str, Any]:
        """
        회사명으로 완전한 재무정보 추출 (A/B 폴더 지원)
        
        Args:
            company_name: 정확한 회사명
            
        Returns:
            완전한 재무정보 딕셔너리
        """
        print(f"🔍 '{company_name}' 재무정보 추출 시작...")
        
        # 폴더 변경 확인
        self._check_folder_change()

        # 1단계: 회사 검색
        company_info = self.search_company(company_name)
        if not company_info:
            raise ValueError(f"회사를 찾을 수 없습니다: '{company_name}'\n정확한 회사명을 입력해주세요.")

        folder_info = f" (활성 폴더: {company_info['active_folder']})" if company_info['active_folder'] else ""
        print(f"✅ 회사 정보 확인: {company_info['company_name']} ({company_info['company_code']}){folder_info}")

        # 2단계: URL 확인
        if not company_info['has_financial_data']:
            raise ValueError(f"'{company_name}'의 재무데이터 URL이 수집되지 않았습니다.\nURL 수집이 완료될 때까지 기다려주세요.")

        print(f"✅ 재무데이터 URL 확인됨")

        # 3단계: 재무데이터 추출
        try:
            financial_data = self.extract_financial_data(company_info['cf1001_url'], company_info['company_code'])

            # 회사 정보 추가
            financial_data['company_info']['name'] = company_info['company_name']
            financial_data['company_info']['url_collected_at'] = company_info['url_collected_at']

            print(f"✅ 재무데이터 추출 완료: {financial_data['metadata']['success_rate']*100:.1f}% 성공")

            return financial_data

        except Exception as e:
            raise Exception(f"재무데이터 추출 중 오류 발생: {str(e)}")

    def get_system_stats(self) -> Dict[str, Any]:
        """시스템 통계 정보 (A/B 폴더 정보 포함)"""
        # 폴더 변경 확인
        self._check_folder_change()
        
        total_companies = len(self.companies_data)
        companies_with_urls = len(self.urls_data)

        return {
            "total_companies": total_companies,
            "companies_with_urls": companies_with_urls,
            "url_coverage": companies_with_urls / total_companies if total_companies > 0 else 0,
            "target_financial_items": len(self.target_items),
            "active_folder": self.current_active_folder,
            "auto_detect_enabled": self.auto_detect_active_folder
        }


def get_financial_data(company_name: str) -> Dict[str, Any]:
    """
    간편한 재무정보 추출 함수 (A/B 폴더 자동 지원)
    
    Args:
        company_name: 정확한 회사명
        
    Returns:
        완전한 재무정보 딕셔너리
    """
    system = EnhancedIntegratedFinancialSystem()
    return system.get_complete_financial_data(company_name)


def test_enhanced_system():
    """A/B 폴더 지원 시스템 테스트"""
    print("🚀 Enhanced 재무정보 시스템 테스트 시작")
    print("🔄 A/B 폴더 전환 시스템 지원")
    print("=" * 70)

    try:
        # 시스템 초기화
        system = EnhancedIntegratedFinancialSystem()

        # 시스템 통계
        stats = system.get_system_stats()
        print(f"\n📊 시스템 통계:")
        print(f"  활성 폴더: {stats['active_folder']}")
        print(f"  전체 기업: {stats['total_companies']:,}개")
        print(f"  URL 보유: {stats['companies_with_urls']:,}개 ({stats['url_coverage']*100:.1f}%)")
        print(f"  재무항목: {stats['target_financial_items']}개")
        print(f"  자동 감지: {'활성화' if stats['auto_detect_enabled'] else '비활성화'}")

        # 재무데이터가 있는 회사들 찾기
        print(f"\n🔍 재무데이터 보유 기업 확인...")
        companies_with_data = []

        test_companies = ["삼성전자", "LG전자", "NAVER", "카카오", "SK하이닉스"]

        for company in test_companies:
            company_info = system.search_company(company)
            if company_info and company_info['has_financial_data']:
                companies_with_data.append(company)
                print(f"  ✅ {company}: 재무데이터 URL 보유")
            else:
                print(f"  ❌ {company}: 재무데이터 URL 없음")

        # 실제 재무데이터 추출 테스트
        if companies_with_data:
            test_company = companies_with_data[0]
            print(f"\n🎯 '{test_company}' 완전한 재무데이터 추출 테스트:")
            print("-" * 50)

            financial_data = system.get_complete_financial_data(test_company)

            # 결과 요약 출력
            print(f"\n📊 추출 결과:")
            print(f"  회사명: {financial_data['company_info']['name']}")
            print(f"  종목코드: {financial_data['company_info']['code']}")
            print(f"  활성 폴더: {financial_data['company_info']['active_folder']}")
            print(f"  추출 성공률: {financial_data['metadata']['success_rate']*100:.1f}%")
            print(f"  데이터 기간: {financial_data['periods']}")

            # 주요 재무데이터 샘플
            print(f"\n💰 주요 재무데이터 샘플:")
            sample_items = ["매출액", "영업이익", "당기순이익", "자산총계", "ROE(%)"]
            for item in sample_items:
                values = financial_data['financial_data'].get(item, [])
                print(f"  {item}: {values}")

            # 결과 파일 저장
            output_filename = f"enhanced_financial_data_{test_company}.json"
            with open(output_filename, 'w', encoding='utf-8') as f:
                json.dump(financial_data, f, ensure_ascii=False, indent=2)
            print(f"\n📁 완전한 결과를 '{output_filename}'에 저장했습니다.")

            return True

        else:
            print(f"\n⚠️ 재무데이터를 가진 테스트 기업이 없습니다.")
            print(f"URL 수집이 더 진행된 후 다시 테스트해주세요.")
            return False

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    # Enhanced 시스템 테스트 실행
    test_enhanced_system()
