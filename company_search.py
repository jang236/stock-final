import json
import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher


class CompanySearchEngine:
    """
    정확한 회사명으로 종목코드를 찾는 검색 엔진 (명확한 일치만)
    """

    def __init__(
            self,
            companies_file_path: str = "company_codes/stock_companies.json",
            urls_file_path: str = "company_codes/cf1001_urls_database.json"):
        """
        초기화

        Args:
            companies_file_path: 회사 코드 JSON 파일 경로
            urls_file_path: cF1001 URL 데이터베이스 파일 경로
        """
        self.companies_file_path = companies_file_path
        self.urls_file_path = urls_file_path
        self.companies_data = {}
        self.urls_data = {}

        # 데이터 로드
        self._load_companies_data()
        self._load_urls_data()

    def _load_companies_data(self):
        """회사 코드 데이터 로드"""
        try:
            with open(self.companies_file_path, 'r', encoding='utf-8') as f:
                self.companies_data = json.load(f)
            print(f"✅ 회사 데이터 로드 완료: {len(self.companies_data)}개 기업")
        except FileNotFoundError:
            print(f"⚠️ 회사 데이터 파일을 찾을 수 없습니다: {self.companies_file_path}")
            self.companies_data = {}
        except Exception as e:
            print(f"❌ 회사 데이터 로드 실패: {e}")
            self.companies_data = {}

    def _load_urls_data(self):
        """cF1001 URL 데이터베이스 로드"""
        try:
            with open(self.urls_file_path, 'r', encoding='utf-8') as f:
                self.urls_data = json.load(f)
            print(f"✅ URL 데이터 로드 완료: {len(self.urls_data)}개 URL")
        except FileNotFoundError:
            print(f"⚠️ URL 데이터베이스 파일을 찾을 수 없습니다: {self.urls_file_path}")
            self.urls_data = {}
        except Exception as e:
            print(f"❌ URL 데이터 로드 실패: {e}")
            self.urls_data = {}

    def search_company(self, company_name: str) -> Optional[Dict]:
        """
        정확한 회사명으로 검색 (완전 일치만)

        Args:
            company_name: 정확한 회사명

        Returns:
            회사 정보 딕셔너리 또는 None
        """
        if not company_name or not company_name.strip():
            return None

        company_name = company_name.strip()

        # 정확한 매칭만 허용
        if company_name in self.companies_data:
            company_info = self.companies_data[company_name]
            result = {
                'company_name': company_name,
                'company_code': company_info.get('code', ''),
                'match_type': 'exact'
            }

            # URL 정보 추가
            self._add_url_info(result)
            return result

        return None

    def _add_url_info(self, result: Dict):
        """검색 결과에 URL 정보 추가"""
        company_name = result['company_name']

        if company_name in self.urls_data:
            url_info = self.urls_data[company_name]
            result['cf1001_url'] = url_info.get('cf1001_url', None)
            result['url_status'] = url_info.get('status', 'unknown')
            result['url_collected_at'] = url_info.get('collected_at', None)
            result[
                'has_financial_data'] = True if result['cf1001_url'] else False
        else:
            result['cf1001_url'] = None
            result['url_status'] = 'not_collected'
            result['url_collected_at'] = None
            result['has_financial_data'] = False

    def get_company_by_code(self, company_code: str) -> Optional[Dict]:
        """종목코드로 회사 정보 조회"""
        for company_name, company_info in self.companies_data.items():
            if company_info.get('code') == company_code:
                result = {
                    'company_name': company_name,
                    'company_code': company_code,
                    'match_type': 'code_match'
                }
                self._add_url_info(result)
                return result
        return None

    def list_companies(self, limit: int = 20) -> List[str]:
        """등록된 회사명 목록 조회"""
        company_names = list(self.companies_data.keys())
        return company_names[:limit]

    def search_companies_starting_with(self,
                                       prefix: str,
                                       limit: int = 10) -> List[str]:
        """특정 문자로 시작하는 회사명들 조회"""
        if not prefix:
            return []

        matching_companies = []
        for company_name in self.companies_data.keys():
            if company_name.startswith(prefix):
                matching_companies.append(company_name)

        return matching_companies[:limit]

    def get_stats(self) -> Dict:
        """데이터베이스 통계"""
        total_companies = len(self.companies_data)
        companies_with_urls = len(self.urls_data)

        return {
            'total_companies':
            total_companies,
            'companies_with_urls':
            companies_with_urls,
            'url_coverage':
            companies_with_urls / total_companies if total_companies > 0 else 0
        }


def find_company(company_name: str,
                 search_engine: CompanySearchEngine = None) -> Optional[Dict]:
    """
    정확한 회사명으로만 검색하는 함수

    Args:
        company_name: 정확한 회사명
        search_engine: 검색 엔진 인스턴스 (없으면 새로 생성)

    Returns:
        회사 정보 또는 None
    """
    if not search_engine:
        search_engine = CompanySearchEngine()

    # 정확한 회사명 검색만
    return search_engine.search_company(company_name)


def test_company_search():
    """회사 검색 시스템 테스트"""
    print("🚀 회사명 검색 시스템 테스트 시작")
    print("=" * 60)

    try:
        # 검색 엔진 초기화
        search_engine = CompanySearchEngine()

        # 통계 출력
        stats = search_engine.get_stats()
        print(f"\n📊 데이터베이스 통계:")
        print(f"  전체 기업 수: {stats['total_companies']:,}개")
        print(f"  URL 보유 기업: {stats['companies_with_urls']:,}개")
        print(f"  URL 커버리지: {stats['url_coverage']*100:.1f}%")

        # 정확한 회사명 검색 테스트 (종목코드 제외)
        test_queries = [
            "삼성전자",
            "LG전자",
            "네이버",
            "카카오",
            "현대자동차",
            "SK하이닉스",
            "NAVER",  # 영문명 테스트
            "잘못된회사명"  # 존재하지 않는 회사명
        ]

        print(f"\n🔍 정확한 매칭 테스트:")
        for query in test_queries:
            print(f"\n검색어: '{query}'")
            result = search_engine.search_company(query)

            if result:
                print(
                    f"  ✅ {result['company_name']} ({result['company_code']})")
                print(f"     매칭방식: {result['match_type']}")
                print(
                    f"     재무데이터: {'✅' if result['has_financial_data'] else '❌'}"
                )
            else:
                print(f"  ❌ 검색 결과 없음 - 정확한 회사명을 입력해주세요")

        # 회사명 목록 일부 출력
        print(f"\n📋 등록된 회사명 예시 (처음 20개):")
        company_list = search_engine.list_companies(20)
        for i, company in enumerate(company_list, 1):
            print(f"  {i:2d}. {company}")

        # 특정 문자로 시작하는 회사들
        print(f"\n🔤 '삼성'으로 시작하는 회사들:")
        samsung_companies = search_engine.search_companies_starting_with(
            "삼성", 10)
        for company in samsung_companies:
            print(f"  - {company}")

        return search_engine

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return None


# 간편 검색 함수들
def search_company_simple(company_name: str) -> Optional[str]:
    """정확한 회사명 → 종목코드 간편 변환"""
    result = find_company(company_name)
    return result['company_code'] if result else None


def get_company_financial_url(company_name: str) -> Optional[str]:
    """정확한 회사명 → cF1001 URL 간편 조회"""
    result = find_company(company_name)
    return result[
        'cf1001_url'] if result and result['has_financial_data'] else None


def is_valid_company_name(company_name: str) -> bool:
    """회사명이 등록된 정확한 이름인지 확인"""
    result = find_company(company_name)
    return result is not None


if __name__ == "__main__":
    # 테스트 실행
    test_company_search()
