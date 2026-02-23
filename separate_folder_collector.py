#!/usr/bin/env python3
"""
분리된 폴더를 사용하는 cF1001 수집기
기존 데이터는 그대로 두고 새 폴더에 수집합니다.
"""

import json
import time
import os
import requests
import re
import random
from datetime import datetime
import shutil


class SeparateFolderCF1001Collector:
    def __init__(self, new_folder="company_codes_new"):
        self.session = requests.Session()
        # 성공했던 헤더 그대로 유지
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
        
        # 새로운 폴더 경로 설정
        self.new_folder = new_folder
        self.old_folder = "company_codes"
        
        # 새 폴더의 파일 경로들
        self.companies_file = os.path.join(self.new_folder, "stock_companies.json")
        self.database_file = os.path.join(self.new_folder, "cf1001_urls_database.json")
        self.progress_file = os.path.join(self.new_folder, "cf1001_progress.json")
        self.failed_file = os.path.join(self.new_folder, "cf1001_failed.json")
        
        # 초기 설정
        self.setup_new_folder()

    def setup_new_folder(self):
        """새 폴더 설정 및 필요한 파일 복사"""
        print(f"🗂️ 새로운 수집 폴더 설정: {self.new_folder}")
        print("=" * 60)
        
        # 새 폴더 생성
        if not os.path.exists(self.new_folder):
            os.makedirs(self.new_folder)
            print(f"✅ 새 폴더 생성: {self.new_folder}")
        else:
            print(f"📁 폴더 이미 존재: {self.new_folder}")
        
        # stock_companies.json 복사 (기업 정보는 동일)
        old_companies_file = os.path.join(self.old_folder, "stock_companies.json")
        if os.path.exists(old_companies_file) and not os.path.exists(self.companies_file):
            shutil.copy2(old_companies_file, self.companies_file)
            print(f"✅ 기업 정보 복사: {old_companies_file} → {self.companies_file}")
        
        # 새로운 진행 상황 파일 생성
        if not os.path.exists(self.progress_file):
            initial_progress = {
                "last_completed_index": -1,
                "total_companies": 2879,
                "completed_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "last_run_date": None,
                "start_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "collection_reason": "새로운 토큰 수집 (분리된 폴더)",
                "previous_folder": self.old_folder
            }
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(initial_progress, f, ensure_ascii=False, indent=2)
            print(f"✅ 새로운 진행 상황 생성: {self.progress_file}")
        
        # 빈 실패 목록 생성
        if not os.path.exists(self.failed_file):
            with open(self.failed_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            print(f"✅ 실패 목록 초기화: {self.failed_file}")
        
        # 빈 데이터베이스 생성
        if not os.path.exists(self.database_file):
            with open(self.database_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            print(f"✅ 새로운 데이터베이스 생성: {self.database_file}")
        
        print(f"\n📊 폴더 비교:")
        print(f"🔒 기존 폴더: {self.old_folder} (보존됨)")
        if os.path.exists(os.path.join(self.old_folder, "cf1001_urls_database.json")):
            with open(os.path.join(self.old_folder, "cf1001_urls_database.json"), 'r', encoding='utf-8') as f:
                old_data = json.load(f)
                print(f"     기존 URL: {len(old_data)}개")
        
        print(f"🆕 새 폴더: {self.new_folder} (새로 수집)")
        with open(self.database_file, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
            print(f"     새 URL: {len(new_data)}개 (시작)")
        
        print("=" * 60)

    def load_companies(self):
        """종목 정보 로드"""
        try:
            with open(self.companies_file, 'r', encoding='utf-8') as f:
                companies = json.load(f)
            print(f"✅ {len(companies)}개 종목 로드 완료 (from {self.new_folder})")
            return companies
        except Exception as e:
            print(f"❌ 종목 로드 실패: {e}")
            return {}

    def load_progress(self):
        """진행 상황 로드"""
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
                "last_run_date": None
            }

    def save_progress(self, progress):
        """진행 상황 저장"""
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 진행 상황 저장 실패: {e}")

    def load_database(self):
        """URL 데이터베이스 로드"""
        try:
            with open(self.database_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def save_database(self, database):
        """URL 데이터베이스 저장"""
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

    def visit_main_page_first(self, stock_code):
        """메인 페이지 먼저 방문"""
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
        
        # id 추출
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
        """cF1001 URL 생성"""
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
        """cF1001 URL 유효성 테스트"""
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
            
            print(f"   📊 응답 코드: {response.status_code}")
            print(f"   📏 응답 길이: {len(response.text)}")
            
            if response.status_code == 200:
                if "접속장애" in response.text:
                    print(f"   ❌ 접속 차단 페이지")
                    return False
                
                print(f"   ✅ URL 유효 확인 (HTTP 200)")
                return True
            else:
                print(f"   ❌ HTTP 오류: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ❌ 테스트 실패: {e}")
            return False

    def process_single_company(self, company_name, company_info, index, total):
        """단일 회사 처리"""
        stock_code = company_info['code']
        
        print(f"[{index+1:4d}/{total:4d}] 📍 처리 시작: {company_name} ({stock_code})")
        
        try:
            # 1단계: 메인 페이지 먼저 방문
            print(f"   🌐 메인 페이지 방문: {stock_code}")
            if not self.visit_main_page_first(stock_code):
                print(f"   ❌ 메인 페이지 방문 실패")
                return None
            print(f"   ✅ 메인 페이지 방문 성공")
            
            # 2단계: WiseReport 페이지 접속
            print(f"   📊 WiseReport 페이지 접속")
            page_content = self.get_wisereport_page(stock_code)
            if not page_content:
                print(f"   ❌ WiseReport 페이지 접속 실패")
                return None
            print(f"   ✅ WiseReport 페이지 접속 성공")
            
            # 3단계: 파라미터 추출
            print(f"   🔍 파라미터 추출")
            params = self.extract_parameters(page_content)
            if not params or 'encparam' not in params:
                print(f"   ❌ 필수 파라미터 추출 실패")
                return None
            
            print(f"   ✅ encparam 추출: {params['encparam'][:20]}...")
            if 'id' in params:
                print(f"   ✅ id 추출: {params['id']}")
            
            # 4단계: URL 생성
            cf1001_url = self.build_cf1001_url(stock_code, params)
            if not cf1001_url:
                print(f"   ❌ URL 생성 실패")
                return None
            
            print(f"   🔗 생성된 URL: {cf1001_url}")
            
            # 5단계: URL 유효성 테스트
            print(f"   🧪 URL 유효성 테스트")
            if self.test_cf1001_url(cf1001_url, stock_code):
                result = {
                    "code": stock_code,
                    "cF1001_url": cf1001_url,
                    "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "success",
                    "parameters": params,
                    "collection_folder": self.new_folder
                }
                print(f"   ✅ {company_name} 성공!")
                return result
            else:
                print(f"   ❌ URL 테스트 실패")
                return None
                
        except Exception as e:
            print(f"   ❌ 처리 실패: {e}")
            return None

    def collect_batch(self, batch_size=100):
        """배치 수집 (분리된 폴더 버전)"""
        print(f"🚀 분리된 폴더 cF1001 수집기 (안전한 방식)")
        print(f"📁 새 수집 폴더: {self.new_folder}")
        print(f"📁 기존 폴더: {self.old_folder} (보존됨)")
        print(f"📊 배치 크기: {batch_size}개")
        print(f"⚡ 대기시간: 2-3.5초 랜덤")
        print(f"{'='*70}")
        
        companies = self.load_companies()
        if not companies:
            return
        
        progress = self.load_progress()
        database = self.load_database()
        failed_list = self.load_failed_list()
        
        company_items = list(companies.items())
        total_companies = len(company_items)
        progress["total_companies"] = total_companies
        
        start_index = progress["last_completed_index"] + 1
        end_index = min(start_index + batch_size, total_companies)
        
        if start_index >= total_companies:
            print("🎉 모든 종목 수집이 완료되었습니다!")
            return
        
        current_batch = company_items[start_index:end_index]
        
        print(f"📊 전체 진행 상황:")
        print(f"   전체 종목: {total_companies:,}개")
        print(f"   완료된 종목: {progress['completed_count']:,}개")
        print(f"   이번 배치: {start_index+1}~{end_index}번 ({len(current_batch)}개)")
        print(f"   전체 진행률: {progress['completed_count']/total_companies*100:.1f}%")
        print(f"\n⚡ 예상 완료 시간:")
        remaining_companies = total_companies - progress['completed_count']
        estimated_seconds = remaining_companies * 2.75
        estimated_hours = estimated_seconds / 3600
        print(f"   남은 종목: {remaining_companies:,}개")
        print(f"   예상 소요시간: {estimated_hours:.1f}시간")
        print(f"{'='*70}")
        
        success_count = 0
        
        for i, (company_name, company_info) in enumerate(current_batch):
            current_index = start_index + i
            
            result = self.process_single_company(company_name, company_info, current_index, total_companies)
            
            if result:
                self.results[company_name] = result
                database[company_name] = result
                success_count += 1
                progress["success_count"] += 1
            else:
                self.failed_companies.append(company_name)
                failed_list.append(company_name)
                progress["failed_count"] += 1
            
            progress["completed_count"] += 1
            progress["last_completed_index"] = current_index
            
            # 10개마다 중간 저장
            if (i + 1) % 10 == 0:
                self.save_database(database)
                self.save_progress(progress)
                self.save_failed_list(failed_list)
                print(f"   💾 중간 저장 완료 ({i+1}개 처리)")
            
            # 마지막이 아니면 랜덤 대기
            if i < len(current_batch) - 1:
                sleep_time = random.uniform(2.0, 3.5)
                print(f"   ⏰ 다음 종목까지 {sleep_time:.1f}초 대기...")
                time.sleep(sleep_time)
        
        # 최종 저장
        progress["last_run_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_database(database)
        self.save_progress(progress)
        self.save_failed_list(failed_list)
        
        # 결과 요약
        print(f"\n{'='*70}")
        print(f"📊 배치 완료 요약")
        print(f"{'='*70}")
        print(f"📁 수집 폴더: {self.new_folder}")
        print(f"🎯 이번 배치: {len(current_batch)}개")
        print(f"✅ 성공: {success_count}개 ({success_count/len(current_batch)*100:.1f}%)")
        print(f"❌ 실패: {len(self.failed_companies)}개")
        
        # 성공한 URL들 출력
        if success_count > 0:
            print(f"\n🎉 성공한 URL 목록:")
            print(f"-" * 70)
            for i, (name, result) in enumerate(self.results.items(), 1):
                print(f"{i}. {name} ({result['code']})")
                print(f"   {result['cF1001_url']}")
                print()
        
        # 진행 상황 안내
        remaining = total_companies - progress['completed_count']
        if remaining > 0:
            estimated_batches = (remaining + batch_size - 1) // batch_size
            estimated_total_hours = remaining * 2.75 / 3600
            print(f"📅 남은 배치: 약 {estimated_batches}회")
            print(f"⚡ 전체 완료까지: 약 {estimated_total_hours:.1f}시간")
            print(f"🚀 다음 실행: python separate_folder_collector.py")
        else:
            print(f"🎉 전체 수집 완료!")
        
        print(f"\n💾 저장된 파일:")
        print(f"   - URL 데이터베이스: {self.database_file}")
        print(f"   - 진행 상황: {self.progress_file}")
        print(f"   - 실패 목록: {self.failed_file}")


def main():
    # 새 폴더 이름을 현재 날짜로 설정
    folder_name = f"company_codes_{datetime.now().strftime('%Y%m%d')}"
    
    collector = SeparateFolderCF1001Collector(new_folder=folder_name)
    collector.collect_batch(batch_size=100)


if __name__ == "__main__":
    main()
