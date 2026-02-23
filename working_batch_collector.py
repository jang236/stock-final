import json
import time
import os
import requests
import re
from datetime import datetime


class WorkingBatchCollector:
    def __init__(self):
        self.session = requests.Session()
        # 더 자연스러운 브라우저 헤더 (성공했던 코드와 동일)
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
        
        # 파일 경로
        self.companies_file = os.path.join("company_codes", "stock_companies.json")
        self.database_file = os.path.join("company_codes", "cf1001_urls_database.json")
        self.progress_file = os.path.join("company_codes", "cf1001_progress.json")
        self.failed_file = os.path.join("company_codes", "cf1001_failed.json")

    def load_companies(self):
        """종목 정보 로드"""
        try:
            with open(self.companies_file, 'r', encoding='utf-8') as f:
                companies = json.load(f)
            print(f"✅ {len(companies)}개 종목 로드 완료")
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
        """기존 URL 데이터베이스 로드"""
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
        """메인 페이지 먼저 방문 (자연스러운 패턴) - 성공했던 코드와 동일"""
        try:
            # 네이버 금융 메인 페이지 방문
            main_url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"
            
            response = self.session.get(main_url, timeout=15)
            
            if response.status_code == 200:
                # 자연스러운 대기 (페이지 로딩 시뮬레이션)
                time.sleep(3)
                return True
            else:
                return False
                
        except Exception as e:
            return False

    def get_wisereport_page(self, stock_code):
        """WiseReport 페이지 접속 - 성공했던 코드와 동일"""
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
        """올바른 파라미터 추출 - 성공했던 코드와 완전히 동일"""
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
        
        # id 추출 (올바른 Base64 형태) - 성공했던 코드와 완전히 동일
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
        """올바른 cF1001 URL 생성 - 성공했던 코드와 동일"""
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
        """cF1001 URL 유효성 테스트 - 성공했던 코드와 동일하지만 더 관대하게"""
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
                # HTML 오류 페이지 체크
                if "접속장애" in response.text:
                    return False
                
                # 사용자가 확인했던 것처럼 일단 HTTP 200이면 성공으로 간주
                return True
            else:
                return False
                
        except Exception as e:
            return False

    def process_single_company(self, company_name, company_info, index, total):
        """단일 회사 처리 - 성공했던 코드 기반"""
        stock_code = company_info['code']
        
        print(f"[{index+1:4d}/{total:4d}] {company_name} ({stock_code})")
        
        try:
            # 1단계: 메인 페이지 먼저 방문 (자연스러운 패턴)
            if not self.visit_main_page_first(stock_code):
                print(f"   ❌ 메인 페이지 방문 실패")
                return None
            
            # 2단계: WiseReport 페이지 접속
            page_content = self.get_wisereport_page(stock_code)
            if not page_content:
                print(f"   ❌ WiseReport 페이지 접속 실패")
                return None
            
            # 3단계: 파라미터 추출
            params = self.extract_parameters(page_content)
            if not params or 'encparam' not in params:
                print(f"   ❌ 필수 파라미터 추출 실패")
                return None
            
            # 4단계: URL 생성
            cf1001_url = self.build_cf1001_url(stock_code, params)
            if not cf1001_url:
                print(f"   ❌ URL 생성 실패")
                return None
            
            # 5단계: URL 유효성 테스트
            if self.test_cf1001_url(cf1001_url, stock_code):
                result = {
                    "code": stock_code,
                    "cf1001_url": cf1001_url,
                    "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "success",
                    "parameters": params
                }
                print(f"   ✅ 성공 (id: {params.get('id', 'N/A')[:10]}...)")
                return result
            else:
                print(f"   ❌ URL 테스트 실패")
                return None
                
        except Exception as e:
            print(f"   ❌ 처리 실패: {e}")
            return None

    def run_batch(self, batch_size=100):
        """100개 배치 실행 - 성공했던 로직 기반"""
        print(f"🚀 성공했던 코드 기반 cF1001 URL 수집")
        print(f"📊 배치 크기: {batch_size}개")
        print(f"{'='*70}")
        
        # 데이터 로드
        all_companies = self.load_companies()
        if not all_companies:
            print("❌ 종목 데이터를 로드할 수 없습니다.")
            return
        
        progress = self.load_progress()
        database = self.load_database()
        failed_list = self.load_failed_list()
        
        # 회사 목록을 리스트로 변환 (순서 보장)
        company_items = list(all_companies.items())
        total_companies = len(company_items)
        
        # 진행 상황 업데이트
        progress["total_companies"] = total_companies
        
        # 다음 배치 범위 계산
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
        print(f"\n⏰ 요청 간격: 10초 (서버 친화적)\n")
        
        # 배치 처리
        batch_success = 0
        batch_failed = 0
        
        for i, (company_name, company_info) in enumerate(current_batch):
            current_index = start_index + i
            
            result = self.process_single_company(
                company_name, company_info, current_index, total_companies
            )
            
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
            
            # 10개마다 중간 저장
            if (i + 1) % 10 == 0:
                self.save_database(database)
                self.save_progress(progress)
                self.save_failed_list(failed_list)
                print(f"   💾 중간 저장 완료 ({i+1}개 처리)")
            
            # 마지막이 아니면 대기
            if i < len(current_batch) - 1:
                time.sleep(10)
        
        # 최종 저장
        progress["last_run_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.save_database(database)
        self.save_progress(progress)
        self.save_failed_list(failed_list)
        
        # 결과 요약
        print(f"\n{'='*70}")
        print(f"📊 배치 완료 요약")
        print(f"{'='*70}")
        print(f"🎯 이번 배치: {len(current_batch)}개")
        print(f"✅ 성공: {batch_success}개 ({batch_success/len(current_batch)*100:.1f}%)")
        print(f"❌ 실패: {batch_failed}개")
        print(f"\n📈 전체 진행률: {progress['completed_count']}/{total_companies} ({progress['completed_count']/total_companies*100:.1f}%)")
        
        remaining = total_companies - progress['completed_count']
        if remaining > 0:
            estimated_batches = (remaining + batch_size - 1) // batch_size
            print(f"📅 남은 배치: 약 {estimated_batches}회")
            print(f"\n🚀 다음 실행: python working_batch_collector.py")
        else:
            print(f"\n🎉 전체 수집 완료!")
        
        print(f"\n💾 저장된 파일:")
        print(f"   - URL 데이터베이스: {self.database_file}")
        print(f"   - 진행 상황: {self.progress_file}")
        print(f"   - 실패 목록: {self.failed_file}")


def main():
    collector = WorkingBatchCollector()
    collector.run_batch(batch_size=30)


if __name__ == "__main__":
    main()
