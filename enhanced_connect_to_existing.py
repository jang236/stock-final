#!/usr/bin/env python3
"""
기존 진행 중인 수집에 자동 휴식 기능 + 실패 재시도 기능 연결
메인 수집 완료 → 30분 휴식 → 실패 종목 재시도 → 최종 완료
"""

import json
import time
import os
import requests
import re
import random
from datetime import datetime


class EnhancedConnectExistingAutoRest:
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
        
        # 메인 수집 설정
        self.batch_size = 200
        self.rest_min = 7
        self.rest_max = 12
        
        # 실패 재시도 설정
        self.retry_delay_min = 5.0    # 강화된 딜레이
        self.retry_delay_max = 8.0
        self.retry_rest_minutes = 30  # 30분 휴식
        
        self.check_existing_progress()

    def check_existing_progress(self):
        """기존 진행 상황 확인 및 연결"""
        print(f"🔗 기존 수집에 자동 휴식 + 실패 재시도 기능 연결")
        print(f"📁 연결 폴더: {self.folder}")
        print("=" * 70)
        
        if not os.path.exists(self.folder):
            print(f"❌ 폴더를 찾을 수 없습니다: {self.folder}")
            return False
        
        progress = self.load_progress()
        
        print(f"📊 기존 진행 상황:")
        print(f"   완료: {progress['completed_count']}/{progress.get('total_companies', 2879)}")
        print(f"   성공: {progress['success_count']}개")
        print(f"   실패: {progress['failed_count']}개")
        print(f"   성공률: {progress['success_count']/(progress['success_count']+progress['failed_count'])*100:.1f}%")
        
        if progress.get('last_run_date'):
            print(f"   마지막 실행: {progress['last_run_date']}")
        
        database = self.load_database()
        print(f"   URL 보유: {len(database)}개")
        
        # 강화된 기능으로 업그레이드
        if 'retry_enhanced' not in progress:
            progress['retry_enhanced'] = True
            progress['enhancement_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_progress(progress)
            print(f"✅ 실패 재시도 기능 추가 완료")
        
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
        
        total_minutes = int(rest_minutes)
        for minute in range(total_minutes):
            remaining_minutes = total_minutes - minute
            print(f"   ⏰ {remaining_minutes}분 남음... 😴")
            time.sleep(60)
        
        remaining_seconds = rest_seconds - (total_minutes * 60)
        if remaining_seconds > 0:
            print(f"   ⏰ {remaining_seconds:.0f}초 남음...")
            time.sleep(remaining_seconds)
        
        print(f"\n🚀 휴식 완료! 다음 사이클 시작합니다.")
        print(f"{'='*70}")
        
        return rest_minutes

    def take_retry_rest(self):
        """실패 재시도 전 30분 휴식"""
        rest_seconds = self.retry_rest_minutes * 60
        
        print(f"\n{'='*70}")
        print(f"😴 메인 수집 완료 - 실패 재시도 전 휴식")
        print(f"{'='*70}")
        print(f"⏰ 휴식 시간: {self.retry_rest_minutes}분")
        print(f"🎯 휴식 후: 실패 종목 재시도 (강화 모드)")
        
        print(f"\n💡 30분 휴식하는 이유:")
        print(f"   • 서버 부하 시점 회피")
        print(f"   • 일시적 오류 자연 해소")  
        print(f"   • 로봇 탐지 위험 최소화")
        print(f"   • 강화된 설정으로 재시도 준비")
        
        print(f"\n💤 긴 휴식 카운트다운:")
        
        for minute in range(self.retry_rest_minutes):
            remaining_minutes = self.retry_rest_minutes - minute
            if remaining_minutes % 5 == 0 or remaining_minutes <= 5:  # 5분마다 또는 마지막 5분
                print(f"   ⏰ {remaining_minutes}분 남음... 😴")
            time.sleep(60)
        
        print(f"\n🚀 30분 휴식 완료! 실패 종목 재시도를 시작합니다.")
        print(f"{'='*70}")

    def rotate_user_agent(self):
        """User-Agent 로테이션 (강화 모드용)"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        selected_ua = random.choice(user_agents)
        self.session.headers['User-Agent'] = selected_ua
        print(f"   🔄 User-Agent 변경: {selected_ua[:50]}...")

    def visit_main_page_first(self, stock_code, enhanced_mode=False):
        """메인 페이지 방문"""
        try:
            main_url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"
            response = self.session.get(main_url, timeout=15)
            
            if response.status_code == 200:
                if enhanced_mode:
                    sleep_time = random.uniform(2.0, 3.0)  # 강화 모드는 조금 더 길게
                else:
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

    def process_single_company(self, company_name, company_info, index, total, enhanced_mode=False):
        """단일 회사 처리"""
        stock_code = company_info['code']
        
        mode_text = "🔄 재시도" if enhanced_mode else "📍"
        print(f"[{index+1:4d}/{total:4d}] {mode_text} {company_name} ({stock_code})")
        
        try:
            if not self.visit_main_page_first(stock_code, enhanced_mode):
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
                    "retry_success": enhanced_mode
                }
                print(f"   ✅ 성공! {'(재시도 성공)' if enhanced_mode else ''}")
                return result
            else:
                print(f"   ❌ URL 테스트 실패")
                return None
                
        except Exception as e:
            print(f"   ❌ 오류: {e}")
            return None

    def retry_failed_companies(self):
        """실패한 종목들 재시도"""
        print(f"\n🔄 실패 종목 재시도 시작 (강화 모드)")
        print("=" * 70)
        
        # 실패 목록 로드
        failed_list = self.load_failed_list()
        if not failed_list:
            print("✅ 실패한 종목이 없습니다!")
            return 0, 0
        
        companies = self.load_companies()
        database = self.load_database()
        progress = self.load_progress()
        
        print(f"📊 실패 종목 재시도:")
        print(f"   대상 종목: {len(failed_list)}개")
        print(f"   강화 설정: {self.retry_delay_min}-{self.retry_delay_max}초 딜레이")
        print(f"   User-Agent 로테이션 적용")
        print("=" * 70)
        
        # User-Agent 변경
        self.rotate_user_agent()
        
        retry_success = 0
        retry_failed = 0
        new_failed_list = []
        
        for i, company_name in enumerate(failed_list):
            if company_name not in companies:
                print(f"[{i+1:3d}/{len(failed_list):3d}] ❌ {company_name} - 기업 정보 없음")
                new_failed_list.append(company_name)
                retry_failed += 1
                continue
            
            company_info = companies[company_name]
            
            # 강화 모드로 재시도
            result = self.process_single_company(
                company_name, company_info, i, len(failed_list), enhanced_mode=True
            )
            
            if result:
                database[company_name] = result
                retry_success += 1
                progress["success_count"] += 1
                progress["failed_count"] -= 1
            else:
                new_failed_list.append(company_name)
                retry_failed += 1
            
            # 20개마다 중간 저장
            if (i + 1) % 20 == 0:
                self.save_database(database)
                self.save_progress(progress)
                print(f"   💾 재시도 중간 저장 ({i+1}/{len(failed_list)})")
            
            # 강화된 딜레이 (마지막 제외)
            if i < len(failed_list) - 1:
                sleep_time = random.uniform(self.retry_delay_min, self.retry_delay_max)
                print(f"   ⏰ 다음 재시도까지 {sleep_time:.1f}초 대기...")
                time.sleep(sleep_time)
        
        # 새로운 실패 목록 저장
        self.save_failed_list(new_failed_list)
        
        # 진행상황 업데이트
        progress["retry_completed"] = True
        progress["retry_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        progress["retry_success_count"] = retry_success
        progress["retry_failed_count"] = retry_failed
        self.save_progress(progress)
        self.save_database(database)
        
        return retry_success, retry_failed

    def continue_collection_with_retry(self):
        """기존 수집을 자동 휴식 + 실패 재시도 모드로 계속 진행"""
        print(f"🚀 기존 수집 + 실패 재시도 완전 자동화 시작!")
        
        companies = self.load_companies()
        if not companies:
            print("❌ 기업 정보를 로드할 수 없습니다.")
            return
        
        progress = self.load_progress()
        database = self.load_database()
        failed_list = self.load_failed_list()
        
        company_items = list(companies.items())
        total_companies = len(company_items)
        
        # 메인 수집이 완료되었는지 확인
        if progress["completed_count"] >= total_companies:
            print(f"📊 메인 수집이 이미 완료되었습니다!")
            print(f"   총 처리: {progress['completed_count']:,}개")
            print(f"   성공: {progress['success_count']:,}개")
            print(f"   실패: {progress['failed_count']:,}개")
            
            # 바로 실패 재시도로 진행
            if progress['failed_count'] > 0 and not progress.get('retry_completed', False):
                self.take_retry_rest()
                retry_success, retry_failed = self.retry_failed_companies()
                self.print_final_results(progress, retry_success, retry_failed)
            else:
                print(f"✅ 실패 재시도도 이미 완료되었습니다!")
                self.print_final_results(progress, 0, 0)
            return
        
        # 메인 수집 계속 진행
        total_cycles = (total_companies + self.batch_size - 1) // self.batch_size
        
        print(f"\n📊 연결된 진행 상황:")
        print(f"   총 기업: {total_companies:,}개")
        print(f"   완료: {progress['completed_count']:,}개")
        print(f"   남은 기업: {total_companies - progress['completed_count']:,}개")
        print(f"   총 사이클: {total_cycles}개")
        
        remaining_companies = total_companies - progress['completed_count']
        remaining_cycles = (remaining_companies + self.batch_size - 1) // self.batch_size
        estimated_hours = remaining_cycles * 16 / 60
        
        print(f"   남은 사이클: {remaining_cycles}개")
        print(f"   예상 완료: 약 {estimated_hours:.1f}시간 (재시도 포함)")
        print("=" * 70)
        
        # 메인 수집 진행
        while progress["completed_count"] < total_companies:
            start_index = progress["last_completed_index"] + 1
            end_index = min(start_index + self.batch_size, total_companies)
            current_batch = company_items[start_index:end_index]
            
            cycle_num = (start_index // self.batch_size) + 1
            
            print(f"\n🔄 사이클 {cycle_num}/{total_cycles} 시작")
            print(f"📍 범위: {start_index+1}~{end_index}번 ({len(current_batch)}개)")
            
            batch_start_time = datetime.now()
            batch_success = 0
            batch_failed = 0
            
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
                
                if (i + 1) % 20 == 0:
                    self.save_database(database)
                    self.save_progress(progress)
                    self.save_failed_list(failed_list)
                    print(f"   💾 중간 저장 ({i+1}/{len(current_batch)})")
                
                if i < len(current_batch) - 1:
                    sleep_time = random.uniform(2.0, 3.5)
                    time.sleep(sleep_time)
            
            batch_end_time = datetime.now()
            batch_duration = (batch_end_time - batch_start_time).total_seconds() / 60
            
            progress["cycle_count"] = cycle_num
            progress["last_run_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.save_database(database)
            self.save_progress(progress)
            self.save_failed_list(failed_list)
            
            print(f"\n📊 사이클 {cycle_num} 완료!")
            print(f"   소요시간: {batch_duration:.1f}분")
            print(f"   성공: {batch_success}개 ({batch_success/len(current_batch)*100:.1f}%)")
            print(f"   실패: {batch_failed}개")
            print(f"   전체 진행률: {progress['completed_count']}/{total_companies} ({progress['completed_count']/total_companies*100:.1f}%)")
            
            if progress["completed_count"] < total_companies:
                rest_time = self.take_rest(cycle_num, total_cycles, progress['completed_count'], total_companies)
                progress["total_rest_time"] = progress.get("total_rest_time", 0) + rest_time
                self.save_progress(progress)
            else:
                print(f"\n🎉 메인 수집 완료!")
                break
        
        # 메인 수집 완료 후 실패 재시도
        if progress['failed_count'] > 0:
            self.take_retry_rest()
            retry_success, retry_failed = self.retry_failed_companies()
        else:
            print(f"\n🎉 실패한 종목이 없어서 재시도가 필요없습니다!")
            retry_success, retry_failed = 0, 0
        
        # 최종 결과 출력
        self.print_final_results(progress, retry_success, retry_failed)

    def print_final_results(self, progress, retry_success, retry_failed):
        """최종 결과 출력"""
        print(f"\n{'='*70}")
        print(f"🎉 완전 자동화 수집 + 재시도 완료!")
        print(f"{'='*70}")
        
        final_success = progress['success_count']
        final_failed = progress['failed_count'] - retry_success + retry_failed
        total_processed = final_success + final_failed
        
        print(f"📊 최종 결과:")
        print(f"   총 처리: {total_processed:,}개")
        print(f"   최종 성공: {final_success:,}개 ({final_success/total_processed*100:.2f}%)")
        print(f"   최종 실패: {final_failed:,}개")
        
        if retry_success > 0 or retry_failed > 0:
            print(f"\n🔄 재시도 결과:")
            print(f"   재시도 성공: {retry_success}개")
            print(f"   재시도 실패: {retry_failed}개")
            print(f"   재시도 성공률: {retry_success/(retry_success+retry_failed)*100:.1f}%")
        
        print(f"\n📈 전체 개선 효과:")
        original_failed = progress.get('failed_count', 0) + retry_success
        improved_rate = retry_success / original_failed * 100 if original_failed > 0 else 0
        print(f"   원래 실패: {original_failed}개")
        print(f"   재시도로 구제: {retry_success}개")
        print(f"   구제율: {improved_rate:.1f}%")
        
        print(f"\n⏰ 총 소요 시간:")
        if 'start_date' in progress:
            start_time = datetime.strptime(progress['start_date'], "%Y-%m-%d %H:%M:%S")
            current_time = datetime.now()
            total_duration = (current_time - start_time).total_seconds() / 3600
            print(f"   전체 소요시간: {total_duration:.1f}시간")
            print(f"   총 휴식시간: {progress.get('total_rest_time', 0):.1f}분")
        
        print(f"\n💾 저장 위치: {self.folder}/")
        print(f"   - URL 데이터베이스: cf1001_urls_database.json")
        print(f"   - 진행 상황: cf1001_progress.json")
        print(f"   - 실패 목록: cf1001_failed.json")
        
        database = self.load_database()
        print(f"\n✅ 최종 URL 수: {len(database):,}개 수집 완료!")


def main():
    existing_folder = "company_codes_20250617"
    
    collector = EnhancedConnectExistingAutoRest(existing_folder=existing_folder)
    collector.continue_collection_with_retry()


if __name__ == "__main__":
    main()
