#!/usr/bin/env python3
"""
기존 진행 중인 수집에 자동 휴식 기능 연결
company_codes_20250617 폴더의 진행상황을 이어받아서 계속 진행
"""

import json
import time
import os
import requests
import re
import random
from datetime import datetime


class ConnectExistingAutoRest:
    def __init__(self, existing_folder="company_codes_20250617"):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
        
        self.results = {}
        self.failed_companies = []
        
        # 기존 폴더 사용
        self.folder = existing_folder
        self.companies_file = os.path.join(self.folder, "stock_companies.json")
        self.database_file = os.path.join(self.folder, "cf1001_urls_database.json")
        self.progress_file = os.path.join(self.folder, "cf1001_progress.json")
        self.failed_file = os.path.join(self.folder, "cf1001_failed.json")
        
        # 자동 휴식 설정
        self.batch_size = 200  # 배치당 200개
        self.rest_min = 7      # 최소 휴식 시간 (분)
        self.rest_max = 12     # 최대 휴식 시간 (분)
        
        self.check_existing_progress()

    def check_existing_progress(self):
        """기존 진행 상황 확인 및 연결"""
        print(f"🔗 기존 수집에 자동 휴식 기능 연결")
        print(f"📁 연결 폴더: {self.folder}")
        print("=" * 70)
        
        if not os.path.exists(self.folder):
            print(f"❌ 폴더를 찾을 수 없습니다: {self.folder}")
            return False
        
        # 기존 진행 상황 로드
        progress = self.load_progress()
        
        print(f"📊 기존 진행 상황:")
        print(f"   완료: {progress['completed_count']}/{progress.get('total_companies', 2879)}")
        print(f"   성공: {progress['success_count']}개")
        print(f"   실패: {progress['failed_count']}개")
        print(f"   성공률: {progress['success_count']/(progress['success_count']+progress['failed_count'])*100:.1f}%")
        
        if progress.get('last_run_date'):
            print(f"   마지막 실행: {progress['last_run_date']}")
        
        # 데이터베이스 상태 확인
        database = self.load_database()
        print(f"   URL 보유: {len(database)}개")
        
        # 자동 휴식 설정으로 진행상황 업데이트
        if 'collection_mode' not in progress:
            progress['collection_mode'] = 'auto_rest_200_batch_connected'
            progress['connection_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            progress['cycle_count'] = progress.get('cycle_count', 0)
            progress['total_rest_time'] = progress.get('total_rest_time', 0)
            self.save_progress(progress)
            print(f"✅ 자동 휴식 모드로 업그레이드 완료")
        
        print("=" * 70)
        return True

    def load_progress(self):
        """진행 상황 로드"""
        try:
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            return progress
        except:
            return {
                "last_completed_index": -1,
                "total_companies": 2879,
                "completed_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "cycle_count": 0,
                "total_rest_time": 0,
                "last_run_date": None
            }

    def save_progress(self, progress):
        """진행 상황 저장"""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 진행 상황 저장 실패: {e}")

    def load_companies(self):
        """종목 정보 로드"""
        try:
            with open(self.companies_file, 'r', encoding='utf-8') as f:
                companies = json.load(f)
            return companies
        except Exception as e:
            print(f"❌ 종목 로드 실패: {e}")
            return {}

    def load_database(self):
        """데이터베이스 로드"""
        try:
            with open(self.database_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def save_database(self, database):
        """데이터베이스 저장"""
        try:
            with open(self.database_file, 'w', encoding='utf-8') as f:
                json.dump(database, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 데이터베이스 저장 실패: {e}")
            return False

    def load_failed_list(self):
        """실패 목록 로드"""
        try:
            with open(self.failed_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def save_failed_list(self, failed_list):
        """실패 목록 저장"""
        try:
            with open(self.failed_file, 'w', encoding='utf-8') as f:
                json.dump(failed_list, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 실패 목록 저장 실패: {e}")

    def take_rest(self, cycle_num, total_cycles, completed_count, total_companies):
        """회차별 휴식"""
        rest_minutes = random.uniform(self.rest_min, self.rest_max)
        rest_seconds = rest_minutes * 60
        
        print(f"\n{'='*70}")
        print(f"😴 사이클 {cycle_num} 완료 - 휴식 시간")
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
        """메인 페이지 방문"""
        try:
            main_url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"
            response = self.session.get(main_url, timeout=15)
            
            if response.status_code == 200:
                sleep_time = random.uniform(1.0, 2.0)
                time.sleep(sleep_time)
                return True
            else:
                return False
        except Exception as e:
            return False

    def get_wisereport_page(self, stock_code):
        """WiseReport 페이지 접속"""
        try:
            wisereport_url = f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={stock_code}"
            self.session.headers['Referer'] = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"
            response = self.session.get(wisereport_url, timeout=15)
            
            if response.status_code == 200:
                return response.text
            else:
                return None
        except Exception as e:
            return None

    def extract_parameters(self, page_content):
        """파라미터 추출"""
        params = {}
        
        encparam_patterns = [
            r"encparam['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]",
            r"encParam['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]"
        ]
        
        for pattern in encparam_patterns:
            matches = re.findall(pattern, page_content, re.IGNORECASE)
            if matches:
                params['encparam'] = matches[0]
                break
        
        id_patterns = [
            r'[\'"]([A-Za-z0-9+/]{8,})[\'"]'
        ]
        
        for pattern in id_patterns:
            matches = re.findall(pattern, page_content)
            for match in matches:
                if (len(match) >= 8 and 
                    not any(word in match.lower() for word in ['css', 'javascript', 'form', 'content'])):
                    if any(c in match for c in '+=') or len(match) > 10:
                        params['id'] = match
                        break
            if 'id' in params:
                break
        
        return params

    def build_cf1001_url(self, stock_code, params):
        """URL 생성"""
        if 'encparam' not in params:
            return None
        
        base_url = "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx"
        
        url_params = {
            'cmp_cd': stock_code,
            'fin_typ': '0',
            'freq_typ': 'A',
            'encparam': params['encparam']
        }
        
        if 'id' in params:
            url_params['id'] = params['id']
        
        param_str = '&'.join([f"{k}={v}" for k, v in url_params.items()])
        full_url = f"{base_url}?{param_str}"
        
        return full_url

    def test_cf1001_url(self, url, stock_code):
        """URL 테스트"""
        try:
            ajax_headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f'https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={stock_code}',
                'Cache-Control': 'no-cache'
            }
            
            original_headers = self.session.headers.copy()
            self.session.headers.update(ajax_headers)
            
            response = self.session.get(url, timeout=10)
            self.session.headers = original_headers
            
            if response.status_code == 200:
                if "접속장애" in response.text:
                    return False
                return True
            else:
                return False
                
        except Exception as e:
            return False

    def process_single_company(self, company_name, company_info, index, total):
        """단일 회사 처리 (간소화 버전)"""
        stock_code = company_info['code']
        
        print(f"[{index+1:4d}/{total:4d}] 📍 {company_name} ({stock_code})")
        
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
                    "parameters": params
                }
                print(f"   ✅ 성공!")
                return result
            else:
                print(f"   ❌ URL 테스트 실패")
                return None
                
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            return None

    def continue_collection_with_rest(self):
        """기존 수집을 자동 휴식 모드로 계속 진행"""
        print(f"🚀 기존 수집에 자동 휴식 기능 연결하여 계속 진행!")
        
        companies = self.load_companies()
        if not companies:
            print("❌ 기업 정보를 로드할 수 없습니다.")
            return
        
        progress = self.load_progress()
        database = self.load_database()
        failed_list = self.load_failed_list()
        
        company_items = list(companies.items())
        total_companies = len(company_items)
        
        # 사이클 계산
        total_cycles = (total_companies + self.batch_size - 1) // self.batch_size
        
        print(f"\n📊 연결된 진행 상황:")
        print(f"   총 기업: {total_companies:,}개")
        print(f"   완료: {progress['completed_count']:,}개")
        print(f"   남은 기업: {total_companies - progress['completed_count']:,}개")
        print(f"   총 사이클: {total_cycles}개")
        
        # 예상 완료 시간 계산
        remaining_companies = total_companies - progress['completed_count']
        remaining_cycles = (remaining_companies + self.batch_size - 1) // self.batch_size
        estimated_hours = remaining_cycles * 16 / 60  # 평균 16분 per cycle
        
        print(f"   남은 사이클: {remaining_cycles}개")
        print(f"   예상 완료: 약 {estimated_hours:.1f}시간")
        print("=" * 70)
        
        # 수집 계속 진행
        while progress["completed_count"] < total_companies:
            # 현재 배치 범위
            start_index = progress["last_completed_index"] + 1
            end_index = min(start_index + self.batch_size, total_companies)
            current_batch = company_items[start_index:end_index]
            
            # 사이클 정보
            cycle_num = (start_index // self.batch_size) + 1
            
            print(f"\n🔄 사이클 {cycle_num}/{total_cycles} 시작")
            print(f"📍 범위: {start_index+1}~{end_index}번 ({len(current_batch)}개)")
            
            batch_start_time = datetime.now()
            batch_success = 0
            batch_failed = 0
            
            # 배치 처리
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
                
                # 20개마다 중간 저장
                if (i + 1) % 20 == 0:
                    self.save_database(database)
                    self.save_progress(progress)
                    self.save_failed_list(failed_list)
                    print(f"   💾 중간 저장 ({i+1}/{len(current_batch)})")
                
                # 딜레이
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
        print(f"🎉 연결된 자동 휴식 수집 완료!")
        print(f"{'='*70}")
        print(f"📊 최종 결과:")
        print(f"   총 처리: {progress['completed_count']:,}개")
        print(f"   성공: {progress['success_count']:,}개 ({progress['success_count']/progress['completed_count']*100:.1f}%)")
        print(f"   실패: {progress['failed_count']:,}개")
        print(f"   총 사이클: {progress['cycle_count']}회")
        print(f"   총 휴식시간: {progress.get('total_rest_time', 0):.1f}분")


def main():
    # 기존 폴더명을 확인하여 연결
    existing_folder = "company_codes_20250617"
    
    collector = ConnectExistingAutoRest(existing_folder=existing_folder)
    collector.continue_collection_with_rest()


if __name__ == "__main__":
    main()
