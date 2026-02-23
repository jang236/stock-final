import json
import time
import os
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from urllib.parse import urljoin


class CF1001MassCollector:

    def __init__(self, max_workers=5, delay_between_requests=1):
        self.max_workers = max_workers
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.collected_urls = {}
        self.failed_companies = []
        self.lock = threading.Lock()

    def load_companies(self):
        """기존 종목 리스트 로드"""
        try:
            file_path = os.path.join("company_codes", "stock_companies.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                companies = json.load(f)
            print(f"✅ {len(companies)}개 종목 코드 로드 완료")
            return companies
        except Exception as e:
            print(f"❌ 종목 코드 로드 실패: {e}")
            return {}

    def extract_tokens_from_page(self, company_name, stock_code):
        """재무 페이지에서 토큰 추출"""
        try:
            # 재무 페이지 접속
            coinfo_url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"

            with self.lock:
                print(f"🔍 {company_name}({stock_code}) 토큰 추출 중...")

            response = self.session.get(coinfo_url, timeout=15)
            response.raise_for_status()

            # 페이지 소스에서 토큰 찾기
            content = response.text

            # 방법 1: script 태그에서 찾기
            encparam = None
            id_param = None

            # encparam 패턴들 (더 광범위하게)
            encparam_patterns = [
                r'encparam["\s]*[:=]["\s]*["\']([A-Za-z0-9+/=]+)["\']',
                r'"encparam"["\s]*:["\s]*"([A-Za-z0-9+/=]+)"',
                r'encparam=([A-Za-z0-9+/=]+)',
                r'&encparam=([A-Za-z0-9+/=]+)',
                r'encparam[^A-Za-z0-9]*([A-Za-z0-9+/=]{20,})',
                r'cF1001\.aspx[^"]*encparam=([A-Za-z0-9+/=]+)',
                r'wisereport[^"]*encparam=([A-Za-z0-9+/=]+)',
                r'["\']([A-Za-z0-9+/=]{30,})["\'][^"]*(?:encparam|cF1001)',
            ]

            # id 패턴들
            id_patterns = [
                r'["\s]id["\s]*[:=]["\s]*"([A-Za-z0-9+/=]+)"',
                r'"id"["\s]*:["\s]*"([A-Za-z0-9+/=]+)"',
                r'&id=([A-Za-z0-9+/=]+)',
                r'id=([A-Za-z0-9+/=]+)',
            ]

            # encparam 찾기
            for pattern in encparam_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # 가장 긴 매치를 선택 (더 완전한 토큰일 가능성)
                    encparam = max(matches, key=len)
                    break

            # id 찾기
            for pattern in id_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # 가장 긴 매치를 선택
                    id_param = max(matches, key=len)
                    break

            # 방법 2: cF1001 URL이 이미 페이지에 있는지 확인
            cf1001_pattern = r'https://navercomp\.wisereport\.co\.kr/v2/company/ajax/cF1001\.aspx[^"\']*'
            cf1001_matches = re.findall(cf1001_pattern, content)

            for match in cf1001_matches:
                if stock_code in match:
                    # 직접 URL을 찾은 경우
                    with self.lock:
                        print(f"✅ {company_name} 직접 URL 발견!")
                    return match

            # 토큰으로 URL 구성
            if encparam and id_param:
                url = f"https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd={stock_code}&fin_typ=0&freq_typ=A&encparam={encparam}&id={id_param}"

                # URL 유효성 검증
                if self.validate_url(url):
                    with self.lock:
                        print(f"✅ {company_name} 토큰 추출 성공")
                    return url
                else:
                    with self.lock:
                        print(f"⚠️ {company_name} 토큰 추출했으나 URL 무효")
            else:
                with self.lock:
                    print(
                        f"⚠️ {company_name} 토큰 추출 실패 (encparam: {bool(encparam)}, id: {bool(id_param)})"
                    )

            return None

        except Exception as e:
            with self.lock:
                print(f"❌ {company_name} 처리 실패: {e}")
            return None

    def validate_url(self, url):
        """URL 유효성 검증"""
        try:
            response = self.session.get(url, timeout=10)
            return response.status_code == 200 and len(response.content) > 100
        except:
            return False

    def collect_single_company(self, company_data):
        """단일 기업 URL 수집"""
        company_name, details = company_data
        stock_code = details['code']

        try:
            # 요청 간격 조절
            time.sleep(self.delay)

            cf1001_url = self.extract_tokens_from_page(company_name,
                                                       stock_code)

            if cf1001_url:
                with self.lock:
                    self.collected_urls[company_name] = {
                        "code": stock_code,
                        "cF1001_url": cf1001_url,
                        "collected_at": datetime.now().isoformat(),
                        "status": "success"
                    }
                return True
            else:
                with self.lock:
                    self.failed_companies.append({
                        "name": company_name,
                        "code": stock_code,
                        "reason": "토큰 추출 실패"
                    })
                return False

        except Exception as e:
            with self.lock:
                self.failed_companies.append({
                    "name": company_name,
                    "code": stock_code,
                    "reason": str(e)
                })
            return False

    def collect_urls_batch(self, companies, batch_size=50):
        """배치 단위로 URL 수집"""
        total_companies = len(companies)
        success_count = 0

        print(f"🚀 {total_companies}개 종목 URL 수집 시작")
        print(f"⚙️ 설정: 동시처리 {self.max_workers}개, 요청간격 {self.delay}초")

        # 회사 리스트를 배치 단위로 분할
        company_items = list(companies.items())

        for i in range(0, len(company_items), batch_size):
            batch = company_items[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(company_items) + batch_size - 1) // batch_size

            print(
                f"\n📦 배치 {batch_num}/{total_batches} 처리 중... ({len(batch)}개 종목)"
            )

            # 병렬 처리
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_company = {
                    executor.submit(self.collect_single_company, company_data):
                    company_data[0]
                    for company_data in batch
                }

                for future in as_completed(future_to_company):
                    company_name = future_to_company[future]
                    try:
                        success = future.result()
                        if success:
                            success_count += 1
                    except Exception as e:
                        print(f"❌ {company_name} 배치 처리 오류: {e}")

            # 배치 간 휴식
            if i + batch_size < len(company_items):
                print(f"⏸️ 배치 간 휴식 ({self.delay * 2}초)...")
                time.sleep(self.delay * 2)

        print(
            f"\n📋 전체 수집 완료: {success_count}/{total_companies}개 성공 ({success_count/total_companies*100:.1f}%)"
        )
        return success_count

    def save_results(self, filename_prefix="cf1001_urls"):
        """수집 결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 성공한 URL들 저장
        success_file = os.path.join("company_codes",
                                    f"{filename_prefix}_{timestamp}.json")
        try:
            with open(success_file, 'w', encoding='utf-8') as f:
                json.dump(self.collected_urls, f, ensure_ascii=False, indent=2)
            print(f"✅ 성공 URL 저장: {success_file}")
        except Exception as e:
            print(f"❌ 성공 URL 저장 실패: {e}")

        # 실패한 종목들 저장
        if self.failed_companies:
            failed_file = os.path.join("company_codes",
                                       f"failed_companies_{timestamp}.json")
            try:
                with open(failed_file, 'w', encoding='utf-8') as f:
                    json.dump(self.failed_companies,
                              f,
                              ensure_ascii=False,
                              indent=2)
                print(f"⚠️ 실패 목록 저장: {failed_file}")
            except Exception as e:
                print(f"❌ 실패 목록 저장 실패: {e}")

        return success_file

    def update_stock_companies_json(self):
        """기존 stock_companies.json에 URL 정보 업데이트"""
        try:
            # 기존 파일 로드
            file_path = os.path.join("company_codes", "stock_companies.json")
            with open(file_path, 'r', encoding='utf-8') as f:
                companies = json.load(f)

            # URL 정보 업데이트
            updated_count = 0
            for company_name, url_data in self.collected_urls.items():
                if company_name in companies:
                    companies[company_name]['cF1001_url'] = url_data[
                        'cF1001_url']
                    companies[company_name]['url_collected_at'] = url_data[
                        'collected_at']
                    updated_count += 1

            # 백업 생성
            backup_file = os.path.join(
                "company_codes",
                f"stock_companies_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(companies, f, ensure_ascii=False, indent=2)

            # 원본 파일 업데이트
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(companies, f, ensure_ascii=False, indent=2)

            print(f"✅ stock_companies.json 업데이트 완료: {updated_count}개 종목")
            print(f"💾 백업 파일: {backup_file}")

        except Exception as e:
            print(f"❌ stock_companies.json 업데이트 실패: {e}")


def main():
    """메인 실행 함수"""
    print("🚀 cF1001 URL 대량 수집 시스템 시작")

    # 수집기 초기화
    collector = CF1001MassCollector(
        max_workers=3,  # 동시 처리 수 (너무 높으면 차단 위험)
        delay_between_requests=1.5  # 요청 간격 (초)
    )

    try:
        # 종목 리스트 로드
        companies = collector.load_companies()

        if not companies:
            print("❌ 종목 데이터가 없습니다.")
            return

        # 사용자 선택
        print(f"\n📊 총 {len(companies)}개 종목 발견")
        print("1. 테스트 모드 (주요 10개 종목)")
        print("2. 소량 수집 (100개 종목)")
        print("3. 대량 수집 (500개 종목)")
        print("4. 전체 수집 (모든 종목)")

        choice = input("\n선택하세요 (1-4): ").strip()

        if choice == "1":
            # 테스트 모드
            test_companies = [
                "삼성전자", "NAVER", "신한금융지주", "SK하이닉스", "카카오", "LG에너지솔루션", "현대차",
                "기아", "삼성바이오로직스", "셀트리온"
            ]
            companies = {
                name: details
                for name, details in companies.items()
                if name in test_companies
            }
            print(f"🧪 테스트 모드: {len(companies)}개 종목")

        elif choice == "2":
            companies = dict(list(companies.items())[:100])
            print(f"📊 소량 수집: {len(companies)}개 종목")

        elif choice == "3":
            companies = dict(list(companies.items())[:500])
            print(f"📊 대량 수집: {len(companies)}개 종목")

        elif choice == "4":
            print(f"📊 전체 수집: {len(companies)}개 종목")
            confirm = input("⚠️ 전체 수집은 시간이 오래 걸립니다. 계속하시겠습니까? (y/N): ")
            if confirm.lower() != 'y':
                print("취소되었습니다.")
                return
        else:
            print("잘못된 선택입니다.")
            return

        # URL 수집 실행
        success_count = collector.collect_urls_batch(companies, batch_size=50)

        # 결과 저장
        if success_count > 0:
            result_file = collector.save_results()

            # stock_companies.json 업데이트 여부 확인
            update_choice = input(
                "\n💾 stock_companies.json에 URL 정보를 업데이트하시겠습니까? (y/N): ")
            if update_choice.lower() == 'y':
                collector.update_stock_companies_json()

            print(f"\n🎉 수집 완료! {success_count}개 URL 확보")
            print("다음 단계: main.py에서 이 URL들을 활용한 API 구현")
        else:
            print("❌ 수집된 URL이 없습니다.")

    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
        if collector.collected_urls:
            collector.save_results("partial_cf1001_urls")
            print("💾 부분 수집 결과가 저장되었습니다.")
    except Exception as e:
        print(f"❌ 전체 프로세스 실패: {e}")


if __name__ == "__main__":
    main()
