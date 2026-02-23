import json
import time
import os
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, parse_qs, urlparse
import random
from concurrent.futures import ThreadPoolExecutor, as_completed


class MassCF1001Collector:

    def __init__(self, max_workers=3):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.urls_db = {}
        self.failed_companies = []
        self.max_workers = max_workers

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

    def extract_cf1001_from_page(self, company_name, stock_code):
        """올바른 방식으로 cF1001 URL 추출"""
        try:
            # 1단계: 메인 페이지 접속해서 encparam 추출
            main_url = f"https://navercomp.wisereport.co.kr/company/c1010001.aspx?cmp_cd={stock_code}"
            
            response = self.session.get(main_url, timeout=15)
            response.raise_for_status()
            
            # encparam 추출
            encparam = self.extract_encparam(response.text)
            
            if not encparam:
                print(f"❌ {company_name} encparam 추출 실패")
                return None
            
            # 2단계: 올바른 AJAX URL 생성
            cf1001_url = self.build_correct_ajax_url(stock_code, encparam)
            
            if cf1001_url:
                print(f"✅ {company_name} URL 생성 성공")
                return cf1001_url
            else:
                print(f"❌ {company_name} URL 생성 실패")
                return None

        except Exception as e:
            print(f"❌ {company_name}({stock_code}) 추출 실패: {e}")
            return None

    def extract_encparam(self, page_text):
        """페이지에서 encparam 추출"""
        patterns = [
            r"encparam:\s*['\"]([\w+/=]+)['\"]",
            r"encparam['\"]?\s*[:=]\s*['\"]([\w+/=]+)['\"]",
            r"encParam['\"]?\s*[:=]\s*['\"]([\w+/=]+)['\"]"
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                return matches[0]
        return None

    def build_correct_ajax_url(self, stock_code, encparam):
        """올바른 AJAX URL 구성"""
        
        # 기본 URL과 파라미터
        base_url = "https://navercomp.wisereport.co.kr/company/ajax/cF1001.aspx"
        
        # 여러 파라미터 조합 시도
        param_combinations = [
            {'flag': 4, 'cmp_cd': stock_code, 'grp_cd': '03', 'encparam': encparam},
            {'flag': 4, 'cmp_cd': stock_code, 'grp_cd': '01', 'encparam': encparam},
            {'flag': 2, 'cmp_cd': stock_code, 'grp_cd': '03', 'encparam': encparam},
            {'flag': 2, 'cmp_cd': stock_code, 'grp_cd': '01', 'encparam': encparam}
        ]
        
        for params in param_combinations:
            # URL 생성
            param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
            test_url = f"{base_url}?{param_str}"
            
            # 유효성 검사
            if self.test_url_validity(test_url, quick=True):
                return test_url
        
        return None

    def test_url_validity(self, url, quick=False):
        """URL 유효성 검사 (올바른 방식)"""
        try:
            # URL에서 종목코드 추출
            stock_match = re.search(r'cmp_cd=(\d+)', url)
            if not stock_match:
                return False
                
            stock_code = stock_match.group(1)
            
            # 1단계: 메인 페이지 먼저 방문 (세션 설정)
            main_url = f"https://navercomp.wisereport.co.kr/company/c1010001.aspx?cmp_cd={stock_code}"
            try:
                self.session.get(main_url, timeout=5)
            except:
                pass  # 세션 설정 실패해도 계속 진행
            
            # 2단계: AJAX 헤더 설정
            ajax_headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': main_url
            }
            
            # 기존 헤더 백업
            original_headers = self.session.headers.copy()
            self.session.headers.update(ajax_headers)
            
            try:
                # 3단계: AJAX 요청
                timeout = 5 if quick else 10
                response = self.session.get(url, timeout=timeout)
                
                if response.status_code != 200:
                    return False
                
                # 4단계: 응답 검증
                if quick:
                    # 빠른 검사: 기본적인 JSON 응답만 확인
                    try:
                        data = response.json()
                        return isinstance(data, dict)
                    except:
                        return False
                else:
                    # 상세 검사: 실제 재무 데이터 확인
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            # dt 필드에 실제 데이터가 있는지 확인
                            if data.get('dt') and data['dt'] != 'null':
                                return True
                            # 다른 재무 관련 필드들 확인
                            financial_indicators = ['sales', 'revenue', 'income', 'asset', 'debt']
                            response_str = str(data).lower()
                            if any(indicator in response_str for indicator in financial_indicators):
                                return True
                            # 최소한 구조화된 JSON이면 유효한 것으로 간주
                            return len(str(data)) > 50
                        return False
                    except:
                        return len(response.content) > 20
                        
            finally:
                # 헤더 복원
                self.session.headers = original_headers
                
        except Exception as e:
            return False

    def process_single_company(self, company_data):
        """단일 종목 처리 (멀티스레딩용)"""
        company_name, details = company_data
        stock_code = details['code']
        
        try:
            print(f"📍 처리 중: {company_name}({stock_code})")
            
            cf1001_url = self.extract_cf1001_from_page(company_name, stock_code)
            
            if cf1001_url:
                # 상세 검증
                if self.test_url_validity(cf1001_url, quick=False):
                    result = {
                        "code": stock_code,
                        "cF1001_url": cf1001_url,
                        "collected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "success"
                    }
                    print(f"✅ {company_name} 성공")
                    return company_name, result
                else:
                    print(f"⚠️ {company_name} URL 검증 실패")
            else:
                print(f"❌ {company_name} URL 추출 실패")
            
            # 실패한 경우
            return company_name, {
                "code": stock_code,
                "status": "failed",
                "failed_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            print(f"❌ {company_name} 처리 중 오류: {e}")
            return company_name, {
                "code": stock_code,
                "status": "error",
                "error": str(e),
                "failed_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }

    def collect_all_urls(self, test_mode=False, batch_size=50):
        """전체 URL 수집 (배치 처리)"""
        companies = self.load_companies()
        
        if test_mode:
            # 테스트 모드: 랜덤 20개 종목 (더 적은 수로 빠른 테스트)
            items = list(companies.items())
            random.shuffle(items)
            companies = dict(items[:20])
            print(f"🧪 테스트 모드: {len(companies)}개 종목")
        
        total_companies = len(companies)
        success_count = 0
        company_items = list(companies.items())
        
        print(f"🚀 전체 {total_companies}개 종목 수집 시작")
        
        # 배치 단위로 처리
        for batch_start in range(0, total_companies, batch_size):
            batch_end = min(batch_start + batch_size, total_companies)
            batch_companies = company_items[batch_start:batch_end]
            
            print(f"\n📦 배치 {batch_start//batch_size + 1}: {batch_start+1}-{batch_end} ({len(batch_companies)}개 종목)")
            
            # 멀티스레딩으로 배치 처리
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_company = {
                    executor.submit(self.process_single_company, company_data): company_data[0]
                    for company_data in batch_companies
                }
                
                batch_success = 0
                for future in as_completed(future_to_company):
                    company_name, result = future.result()
                    
                    if result.get("status") == "success":
                        self.urls_db[company_name] = result
                        success_count += 1
                        batch_success += 1
                    else:
                        self.failed_companies.append({
                            "name": company_name,
                            "code": result.get("code"),
                            "reason": result.get("error", "URL 추출 실패")
                        })
            
            print(f"🎯 배치 {batch_start//batch_size + 1} 완료: {batch_success}/{len(batch_companies)}개 성공")
            
            # 배치마다 중간 저장
            self.save_progress(batch_start // batch_size + 1)
            
            # 요청 간격 (서버 부하 방지)
            if batch_end < total_companies:
                print("⏳ 2초 대기 중...")
                time.sleep(2)
                
        print(f"\n📋 전체 수집 완료: {success_count}/{total_companies}개 성공 ({success_count/total_companies*100:.1f}%)")
        return self.urls_db

    def save_progress(self, batch_num):
        """진행 상황 저장"""
        try:
            # 성공한 URL들 저장
            if self.urls_db:
                success_file = os.path.join("company_codes", f"cf1001_urls_batch_{batch_num}.json")
                with open(success_file, 'w', encoding='utf-8') as f:
                    json.dump(self.urls_db, f, ensure_ascii=False, indent=2)
                print(f"💾 배치 {batch_num} 성공 데이터 저장: {len(self.urls_db)}개")
            
            # 실패한 종목들 저장
            if self.failed_companies:
                failed_file = os.path.join("company_codes", f"cf1001_failed_batch_{batch_num}.json")
                with open(failed_file, 'w', encoding='utf-8') as f:
                    json.dump(self.failed_companies, f, ensure_ascii=False, indent=2)
                print(f"📝 배치 {batch_num} 실패 데이터 저장: {len(self.failed_companies)}개")
                
        except Exception as e:
            print(f"❌ 진행 상황 저장 실패: {e}")

    def save_final_results(self):
        """최종 결과 저장"""
        try:
            # 최종 성공 파일
            if self.urls_db:
                final_file = os.path.join("company_codes", "cf1001_urls_final.json")
                with open(final_file, 'w', encoding='utf-8') as f:
                    json.dump(self.urls_db, f, ensure_ascii=False, indent=2)
                print(f"✅ 최종 성공 데이터 저장: {final_file} ({len(self.urls_db)}개)")
            
            # 실패 리포트
            if self.failed_companies:
                failed_file = os.path.join("company_codes", "cf1001_failed_final.json")
                with open(failed_file, 'w', encoding='utf-8') as f:
                    json.dump(self.failed_companies, f, ensure_ascii=False, indent=2)
                print(f"📋 실패 리포트 저장: {failed_file} ({len(self.failed_companies)}개)")
            
            # 요약 리포트
            total_processed = len(self.urls_db) + len(self.failed_companies)
            summary = {
                "total_processed": total_processed,
                "successful": len(self.urls_db),
                "failed": len(self.failed_companies),
                "success_rate": (len(self.urls_db) / total_processed * 100) if total_processed > 0 else 0,
                "completed_at": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            summary_file = os.path.join("company_codes", "cf1001_collection_summary.json")
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            print(f"📊 수집 요약 저장: {summary_file}")
            
        except Exception as e:
