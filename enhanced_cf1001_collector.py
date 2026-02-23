import json
import time
import os
import requests
import re
import random
import sys
from datetime import datetime


class EnhancedCF1001Collector:
    """
    A/B 폴더 시스템 + 200개 자동휴식 기능을 지원하는 업그레이드된 CF1001 수집기
    기존 검증된 connect_to_existing.py 로직 완전 적용
    + A/B 폴더 시스템 + 200개 배치 + 7-12분 휴식 + 2-3.5초 랜덤 딜레이
    """
    def __init__(self, folder_type='a'):
        """
        초기화
        folder_type: 'a' 또는 'b' - 수집할 폴더 지정
        """
        self.folder_type = folder_type.lower()
        if self.folder_type not in ['a', 'b']:
            raise ValueError("folder_type은 'a' 또는 'b'여야 합니다")
            
        self.session = requests.Session()
        
        # User-Agent 로테이션 (로봇 탐지 회피)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        # 기존 성공했던 헤더를 기본으로 설정
        self.update_headers()
        
        self.results = {}
        self.failed_companies = []
        
        # A/B 폴더 시스템 적용
        self.base_folder = f"company_codes_{self.folder_type}"
        self.companies_file = os.path.join(self.base_folder, "stock_companies.json")
        self.database_file = os.path.join(self.base_folder, "cf1001_urls_database.json")
        self.progress_file = os.path.join(self.base_folder, "cf1001_progress.json")
        self.failed_file = os.path.join(self.base_folder, "cf1001_failed.json")
        
        # 자동 휴식 설정 (검증된 설정 그대로)
        self.batch_size = 200  # 배치당 200개
        self.rest_min = 7      # 최소 휴식 시간 (분)
        self.rest_max = 12     # 최대 휴식 시간 (분)
        
        # 폴더 생성
        os.makedirs(self.base_folder, exist_ok=True)
        
        print(f"🎯 Enhanced CF1001 Collector - A/B + 자동휴식 시스템")
        print(f"📁 대상 폴더: {self.base_folder}")
        print(f"⚡ 수집 설정: 200개 배치 + 7-12분 휴식 + 2-3.5초 딜레이")

    def update_headers(self):
        """User-Agent 로테이션으로 헤더 업데이트 (로봇 탐지 회피)"""
        user_agent = random.choice(self.user_agents)
        # 기존 성공했던 헤더 그대로 유지, User-Agent만 로테이션
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })

    def load_companies(self):
        """종목 정보 로드 - 기존 코드 완전 그대로"""
        try:
            with open(self.companies_file, 'r', encoding='utf-8') as f:
                companies = json.load(f)
            print(f"✅ {len(companies)}개 종목 로드 완료 ({self.base_folder})")
            return companies
        except Exception as e:
            print(f"❌ 종목 로드 실패: {e}")
            return {}

    def load_progress(self):
        """진행 상황 로드 - 자동휴식 필드 추가"""
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            return progress
        except:
            return {
                "last_completed_index": -1,
                "total_companies": 0,
                "completed_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "cycle_count": 0,
                "total_rest_time": 0,
                "last_run_date": None,
                "collection_mode": f"auto_rest_200_batch_{self.folder_type}_folder",
                "folder_type": self.folder_type
            }

    def save_progress(self, progress):
        """진행 상황 저장 - 기존 코드 완전 그대로"""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 진행 상황 저장 실패: {e}")

    def load_database(self):
        """기존 URL 데이터베이스 로드 - 기존 코드 완전 그대로"""
        try:
            with open(self.database_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def save_database(self, database):
        """URL 데이터베이스 저장 - 기존 코드 완전 그대로"""
        try:
            with open(self.database_file, 'w', encoding='utf-8') as f:
                json.dump(database, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 데이터베이스 저장 실패: {e}")
            return False

    def load_failed_list(self):
        """실패 목록 로드 - 기존 코드 완전 그대로"""
        try:
            with open(self.failed_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def save_failed_list(self, failed_list):
        """실패 목록 저장 - 기존 코드 완전 그대로"""
        try:
            with open(self.failed_file, 'w', encoding='utf-8') as f:
                json.dump(failed_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 실패 목록 저장 실패: {e}")

    def take_rest(self, cycle_num, total_cycles, completed_count, total_companies):
        """회차별 휴식 - 검증된 로직 완전 그대로"""
        rest_minutes = random.uniform(self.rest_min, self.rest_max)
        rest_seconds = rest_minutes * 60
        
        print(f"\n{'='*70}")
        print(f"😴 사이클 {cycle_num} 완료 - 휴식 시간 ({self.folder_type.upper()} 폴더)")
        print(f"{'='*70}")
        print(f"⏰ 휴식 시간: {rest_minutes:.1f}분")
        print(f"📊 전체 진행률: {completed_count}/{total_companies} ({completed_count/total_companies*100:.1f}%)")
        
        # 남은 작업 예상
        remaining_companies = total_companies - completed_count
        remaining_cycles = (remaining_companies + self.batch_size - 1) // self.batch_size
        remaining_time_hours = remaining_cycles * (9 + rest_minutes) / 60
        
        print(f"📅 남은 사이클: {remaining_cycles}개")
        print(f"⏳ 예상 완료까지: 약 {remaining_time_hours:.1f}시간")
        
        print(f"\n💡 휴식하는 이유:")
        print(f"   • 200개 배치 완료 (로봇 탐지 회피)")
        print(f"   • 서버 부하 분산")
        print(f"   • 안정적인 수집 보장")
        
        print(f"\n💤 휴식 카운트다운:")
        
        # 1분마다 카운트다운
        total_minutes = int(rest_minutes)
        for minute in range(total_minutes):
            remaining_minutes = total_minutes - minute
            print(f"   ⏰ {remaining_minutes}분 남음... 😴")
            time.sleep(60)
        
        # 나머지 초
        remaining_seconds = rest_seconds - (total_minutes * 60)
        if remaining_seconds > 0:
            print(f"   ⏰ {remaining_seconds:.0f}초 남음...")
            time.sleep(remaining_seconds)
        
        print(f"\n🚀 휴식 완료! 다음 사이클 시작합니다.")
        print(f"{'='*70}")
        
        return rest_minutes

    def visit_main_page_first(self, stock_code):
        """메인 페이지 먼저 방문 - 검증된 코드 + 랜덤 딜레이"""
        try:
            # 네이버 금융 메인 페이지 방문
            main_url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"
            
            response = self.session.get(main_url, timeout=15)
            
            if response.status_code == 200:
                # 검증된 랜덤 딜레이 (1.0-2.0초)
                sleep_time = random.uniform(1.0, 2.0)
                time.sleep(sleep_time)
                return True
            else:
                return False
                
        except Exception as e:
            return False

    def get_wisereport_page(self, stock_code):
        """WiseReport 페이지 접속 - 기존 성공 코드 완전 그대로"""
        try:
            # WiseReport 페이지 (iframe 내용)
            wisereport_url = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={stock_code}"
            
            # Referer 설정
            self.session.headers['Referer'] = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"
            
            response = self.session.get(wisereport_url, timeout=15)
            
            if response.status_code == 200:
                return response.text
            else:
                return None
                
        except Exception as e:
            return None

    def extract_parameters(self, page_content):
        """올바른 파라미터 추출 - 기존 성공 코드 완전 그대로"""
        params = {}
        
        # encparam 추출
        encparam_patterns = [
            r"encparam['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
            r"encParam['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]"
        ]
        
        for pattern in encparam_patterns:
            matches = re.findall(pattern, page_content, re.IGNORECASE)
            if matches:
                params['encparam'] = matches[0]
                break
        
        # id 추출 (올바른 Base64 형태) - 기존 성공 코드 완전 그대로
        id_patterns = [
            r'[\'"]([A-Za-z0-9+/]{8,})[\'"]'
        ]
        
        for pattern in id_patterns:
            matches = re.findall(pattern, page_content)
            for match in matches:
                # Base64 스타일이면서 CSS/JS 관련이 아닌 것
                if (len(match) >= 8 and 
                    not any(word in match.lower() for word in ['css', 'javascript', 'form', 'content'])):
                    # 추가 검증: 실제 ID 패턴인지 확인
                    if any(c in match for c in '+=') or len(match) > 10:
                        params['id'] = match
                        break
            if 'id' in params:
                break
        
        return params

    def build_cf1001_url(self, stock_code, params):
        """올바른 cF1001 URL 생성 - 기존 성공 코드 완전 그대로"""
        if 'encparam' not in params:
            return None
        
        # v2 경로 사용, fin_typ=0, freq_typ=A
        base_url = "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx"
        
        url_params = {
            'cmp_cd': stock_code,
            'fin_typ': '0',
            'freq_typ': 'A',
            'encparam': params['encparam']
        }
        
        # id가 있으면 추가
        if 'id' in params:
            url_params['id'] = params['id']
        
        # URL 조합
        param_str = '&'.join([f"{k}={v}" for k, v in url_params.items()])
        full_url = f"{base_url}?{param_str}"
        
        return full_url

    def test_cf1001_url(self, url, stock_code):
        """cF1001 URL 유효성 테스트 - 기존 성공 코드 완전 그대로"""
        try:
            # AJAX 헤더 설정
            ajax_headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={stock_code}',
                'Cache-Control': 'no-cache'
            }
            
            # 기존 헤더 백업
            original_headers = self.session.headers.copy()
            self.session.headers.update(ajax_headers)
            
            response = self.session.get(url, timeout=10)
            
            # 헤더 복원
            self.session.headers = original_headers
            
            if response.status_code == 200:
                # 접속장애 페이지만 체크 (더 관대하게)
                if "접속장애" in response.text:
                    return False
                
                # HTTP 200이고 접속장애가 아니면 성공으로 처리
                return True
            else:
                return False
                
        except Exception as e:
            return False

    def process_single_company(self, company_name, company_info, index, total):
        """단일 회사 처리 - 검증된 간소화 버전 + User-Agent 로테이션"""
        stock_code = company_info['code']
        
        print(f"[{index+1:4d}/{total:4d}] 📍 {company_name} ({stock_code})")
        
        # 매 요청마다 User-Agent 로테이션 (로봇 탐지 회피)
        self.update_headers()
        
        try:
            if not self.visit_main_page_first(stock_code):
                print(f"   ❌ 메인 페이지 실패")
                return None
            
            page_content = self.get_wisereport_page(stock_code)
            if not page_content:
                print(f"   ❌ WiseReport 실패")
                return None
            
            params = self.extract_parameters(page_content)
            if not params or 'encparam' not in params:
                print(f"   ❌ 파라미터 실패")
                return None
            
            print(f"   ✅ encparam: {params['encparam'][:15]}...")
            
            cf1001_url = self.build_cf1001_url(stock_code, params)
            if not cf1001_url:
                print(f"   ❌ URL 생성 실패")
                return None
            
            if self.test_cf1001_url(cf1001_url, stock_code):
                result = {
                    "code": stock_code,
                    "cF1001_url": cf1001_url,
                    "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "success",
                    "parameters": params,
                    "folder": self.folder_type  # A/B 폴더 정보 추가
                }
                print(f"   ✅ 성공!")
                return result
            else:
                print(f"   ❌ URL 테스트 실패")
                return None
                
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            return None

    def collect_batch(self, batch_size=None):
        """
        200개 자동휴식 수집 - 검증된 연속수집 로직 완전 적용
        batch_size 파라미터는 무시되고 항상 200개 고정 (검증된 설정)
        """
        print(f"🚀 Enhanced CF1001 Collector - 200개 자동휴식 시스템")
        print(f"📁 수집 대상: {self.base_folder}")
        print(f"📊 배치 설정: 200개 고정 + 7-12분 휴식")
        print(f"⚡ 딜레이: 2.0-3.5초 랜덤 (네이버 감시 회피)")
        print(f"{'='*70}")
        
        companies = self.load_companies()
        if not companies:
            print(f"❌ {self.base_folder}에 종목 데이터가 없습니다!")
            return "no_companies"
        
        # 배치 처리를 위한 데이터 로드
        progress = self.load_progress()
        database = self.load_database()
        failed_list = self.load_failed_list()
        
        # 회사 목록을 리스트로 변환 (순서 보장)
        company_items = list(companies.items())
        total_companies = len(company_items)
        
        # 진행 상황 업데이트
        progress["total_companies"] = total_companies
        
        # 사이클 계산 (200개 고정)
        total_cycles = (total_companies + self.batch_size - 1) // self.batch_size
        
        print(f"📊 전체 진행 상황:")
        print(f"   총 기업: {total_companies:,}개")
        print(f"   완료: {progress['completed_count']:,}개")
        print(f"   남은 기업: {total_companies - progress['completed_count']:,}개")
        print(f"   총 사이클: {total_cycles}개 (200개씩)")
        
        # 예상 완료 시간 계산
        remaining_companies = total_companies - progress['completed_count']
        remaining_cycles = (remaining_companies + self.batch_size - 1) // self.batch_size
        estimated_hours = remaining_cycles * 16 / 60  # 평균 16분 per cycle
        
        print(f"   남은 사이클: {remaining_cycles}개")
        print(f"   예상 완료: 약 {estimated_hours:.1f}시간")
        print("=" * 70)
        
        # 연속 수집 시작
        while progress["completed_count"] < total_companies:
            # 현재 배치 범위 (200개 고정)
            start_index = progress["last_completed_index"] + 1
            end_index = min(start_index + self.batch_size, total_companies)
            current_batch = company_items[start_index:end_index]
            
            if not current_batch:
                print("🎉 모든 종목 수집이 완료되었습니다!")
                break
            
            # 사이클 정보
            cycle_num = (start_index // self.batch_size) + 1
            
            print(f"\n🔄 사이클 {cycle_num}/{total_cycles} 시작")
            print(f"📍 범위: {start_index+1}~{end_index}번 ({len(current_batch)}개)")
            
            batch_start_time = datetime.now()
            batch_success = 0
            batch_failed = 0
            
            # 배치 처리 (200개)
            for i, (company_name, company_info) in enumerate(current_batch):
                current_index = start_index + i
                
                result = self.process_single_company(company_name, company_info, current_index, total_companies)
                
                if result:
                    database[company_name] = result
                    batch_success += 1
                    progress["success_count"] += 1
                else:
                    failed_list.append(company_name)
                    batch_failed += 1
                    progress["failed_count"] += 1
                
                progress["completed_count"] += 1
                progress["last_completed_index"] = current_index
                
                # 20개마다 중간 저장 (검증된 설정)
                if (i + 1) % 20 == 0:
                    self.save_database(database)
                    self.save_progress(progress)
                    self.save_failed_list(failed_list)
                    print(f"   💾 중간 저장 ({i+1}/{len(current_batch)})")
                
                # 검증된 랜덤 딜레이 (2.0-3.5초)
                if i < len(current_batch) - 1:
                    sleep_time = random.uniform(2.0, 3.5)
                    time.sleep(sleep_time)
            
            # 배치 완료 처리
            batch_end_time = datetime.now()
            batch_duration = (batch_end_time - batch_start_time).total_seconds() / 60
            
            progress["cycle_count"] = cycle_num
            progress["last_run_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.save_database(database)
            self.save_progress(progress)
            self.save_failed_list(failed_list)
            
            # 배치 결과
            print(f"\n📊 사이클 {cycle_num} 완료!")
            print(f"   소요시간: {batch_duration:.1f}분")
            print(f"   성공: {batch_success}개 ({batch_success/len(current_batch)*100:.1f}%)")
            print(f"   실패: {batch_failed}개")
            print(f"   전체 진행률: {progress['completed_count']}/{total_companies} ({progress['completed_count']/total_companies*100:.1f}%)")
            
            # 휴식 (마지막이 아니면)
            if progress["completed_count"] < total_companies:
                rest_time = self.take_rest(cycle_num, total_cycles, progress['completed_count'], total_companies)
                progress["total_rest_time"] = progress.get("total_rest_time", 0) + rest_time
                self.save_progress(progress)
            else:
                print(f"\n🎉 전체 수집 완료!")
                break
        
        # 최종 결과
        print(f"\n{'='*70}")
        print(f"🎉 {self.folder_type.upper()} 폴더 자동 휴식 수집 완료!")
        print(f"{'='*70}")
        print(f"📊 최종 결과:")
        print(f"   총 처리: {progress['completed_count']:,}개")
        print(f"   성공: {progress['success_count']:,}개 ({progress['success_count']/progress['completed_count']*100:.1f}%)")
        print(f"   실패: {progress['failed_count']:,}개")
        print(f"   총 사이클: {progress['cycle_count']}회")
        print(f"   총 휴식시간: {progress.get('total_rest_time', 0):.1f}분")
        
        print(f"\n💾 저장된 파일:")
        print(f"   - URL 데이터베이스: {self.database_file}")
        print(f"   - 진행 상황: {self.progress_file}")
        print(f"   - 실패 목록: {self.failed_file}")
        
        return "completed"


def main():
    """메인 함수 - 명령행 인자 처리"""
    if len(sys.argv) < 2:
        print("❌ 사용법: python enhanced_cf1001_collector.py <folder_type>")
        print("   folder_type: 'a' 또는 'b'")
        print()
        print("📝 예시:")
        print("   python enhanced_cf1001_collector.py a")
        print("   python enhanced_cf1001_collector.py b")
        print()
        print("⚡ 특징:")
        print("   - 200개 배치 고정")
        print("   - 7-12분 자동 휴식")
        print("   - 2-3.5초 랜덤 딜레이")
        print("   - A/B 폴더 시스템")
        return
    
    folder_type = sys.argv[1].lower()
    if folder_type not in ['a', 'b']:
        print("❌ folder_type은 'a' 또는 'b'여야 합니다")
        return
    
    print(f"🎯 Enhanced CF1001 Collector - 200개 자동휴식 시스템")
    print(f"📁 대상 폴더: company_codes_{folder_type}")
    print(f"📊 배치 설정: 200개 고정 + 7-12분 휴식")
    print(f"{'='*50}")
    
    collector = EnhancedCF1001Collector(folder_type)
    result = collector.collect_batch()
    
    print(f"\n🏁 수집 완료: {result}")


if __name__ == "__main__":
    main()
