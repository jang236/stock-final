"""
📅 재무 URL 자동 수집 스케줄러
매일 06:00 KST에 비활성 폴더에 수집 → 완료 후 A/B 교체
main.py에서 start_financial_scheduler()를 호출하면 백그라운드로 동작
"""
import threading
import time
import json
import os
import re
import requests
from datetime import datetime, timedelta, timezone
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

KST = timezone(timedelta(hours=9))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class FinancialURLAutoCollector:
    """A/B 폴더 자동 교체 재무 URL 수집기"""

    def __init__(self, delay=0.5, max_workers=3):
        self.delay = delay
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Connection': 'keep-alive',
        })
        self.collected_urls = {}
        self.failed_companies = []
        self.lock = threading.Lock()

    def get_active_folder(self) -> str:
        """현재 활성 폴더 이름 반환"""
        active_file = os.path.join(BASE_DIR, "company_codes_active")
        try:
            if os.path.islink(active_file):
                target = os.readlink(active_file)
                return os.path.basename(target)
            elif os.path.isfile(active_file):
                with open(active_file, 'r') as f:
                    return f.read().strip()
        except Exception as e:
            print(f"⚠️ 활성 폴더 확인 실패: {e}")
        return "company_codes_b"  # 기본값

    def get_target_folder(self) -> str:
        """수집 대상 (비활성) 폴더 반환"""
        active = self.get_active_folder()
        return "company_codes_a" if active == "company_codes_b" else "company_codes_b"

    def swap_active_folder(self, new_active: str):
        """활성 폴더 교체"""
        active_file = os.path.join(BASE_DIR, "company_codes_active")
        try:
            # 심볼릭 링크인 경우
            if os.path.islink(active_file):
                os.remove(active_file)
                os.symlink(new_active, active_file)
            else:
                # 일반 텍스트 파일인 경우
                with open(active_file, 'w') as f:
                    f.write(new_active)
            print(f"✅ 활성 폴더 교체: → {new_active}")
        except Exception as e:
            print(f"❌ 활성 폴더 교체 실패: {e}")

    def load_companies(self, folder: str) -> dict:
        """지정 폴더에서 종목 리스트 로드"""
        file_path = os.path.join(BASE_DIR, folder, "stock_companies.json")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                companies = json.load(f)
            print(f"✅ {len(companies)}개 종목 로드 ({folder})")
            return companies
        except Exception as e:
            print(f"❌ 종목 로드 실패: {e}")
            return {}

    def extract_token(self, company_name: str, stock_code: str) -> str:
        """단일 종목 cF1001 URL 추출 — Naver 본문 + WiseReport iframe 둘 다 시도"""
        urls_to_try = [
            f"https://finance.naver.com/item/coinfo.naver?code={stock_code}",
            f"https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd={stock_code}",
        ]

        for url in urls_to_try:
            try:
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
                content = resp.text

                # 방법 1: 완성된 cF1001 URL 직접 찾기
                cf1001_matches = re.findall(
                    r'https://navercomp\.wisereport\.co\.kr/v2/company/ajax/cF1001\.aspx[^"\'>\s]*',
                    content
                )
                for match in cf1001_matches:
                    if stock_code in match:
                        return match

                # 방법 2: encparam + id 추출 후 URL 조합
                encparam = None
                id_param = None

                enc_patterns = [
                    r'encparam\s*[:=]\s*["\']([A-Za-z0-9+/=]+)["\']',
                    r'&encparam=([A-Za-z0-9+/=]+)',
                    r'cF1001\.aspx[^"]*encparam=([A-Za-z0-9+/=]+)',
                ]
                id_patterns = [
                    r'["\']?id["\']?\s*[:=]\s*["\']([A-Za-z0-9+/=]+)["\']',
                    r'&id=([A-Za-z0-9+/=]+)',
                ]

                for p in enc_patterns:
                    m = re.findall(p, content, re.IGNORECASE)
                    if m:
                        encparam = max(m, key=len)
                        break

                for p in id_patterns:
                    m = re.findall(p, content, re.IGNORECASE)
                    if m:
                        id_param = max(m, key=len)
                        break

                if encparam and id_param:
                    return (f"https://navercomp.wisereport.co.kr/v2/company/ajax/"
                            f"cF1001.aspx?cmp_cd={stock_code}&fin_typ=0&freq_typ=A"
                            f"&encparam={encparam}&id={id_param}")

            except Exception:
                continue

        return None

    def collect_single(self, item: tuple) -> bool:
        """단일 종목 수집"""
        company_name, details = item
        stock_code = details['code']

        try:
            time.sleep(self.delay)
            cf1001_url = self.extract_token(company_name, stock_code)

            if cf1001_url:
                with self.lock:
                    self.collected_urls[company_name] = {
                        "code": stock_code,
                        "cF1001_url": cf1001_url,
                        "collected_at": datetime.now(KST).isoformat(),
                        "status": "success"
                    }
                return True
            else:
                with self.lock:
                    self.failed_companies.append({
                        "name": company_name,
                        "code": stock_code
                    })
                return False

        except Exception:
            with self.lock:
                self.failed_companies.append({
                    "name": company_name,
                    "code": stock_code
                })
            return False

    def run_collection(self, target_folder: str) -> dict:
        """전체 수집 실행"""
        companies = self.load_companies(target_folder)
        if not companies:
            return {"success": False, "error": "종목 로드 실패"}

        total = len(companies)
        self.collected_urls = {}
        self.failed_companies = []

        print(f"\n🚀 재무 URL 수집 시작: {total}개 종목")
        print(f"⚙️ 딜레이: {self.delay}초, 병렬: {self.max_workers}개")
        start_time = time.time()

        items = list(companies.items())
        batch_size = 50
        success_count = 0

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(items) + batch_size - 1) // batch_size

            print(f"📦 배치 {batch_num}/{total_batches} ({len(batch)}개)")

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self.collect_single, item): item[0] for item in batch}
                for future in as_completed(futures):
                    if future.result():
                        success_count += 1

            # 진행률 저장
            progress = {
                "last_completed_index": min(i + batch_size, total) - 1,
                "total_companies": total,
                "completed_count": min(i + batch_size, total),
                "success_count": success_count,
                "failed_count": len(self.failed_companies),
                "last_run_date": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"),
                "collection_mode": f"auto_scheduler_{target_folder}",
                "folder_type": target_folder.split("_")[-1]
            }
            progress_path = os.path.join(BASE_DIR, target_folder, "cf1001_progress.json")
            with open(progress_path, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)

        elapsed = time.time() - start_time
        elapsed_min = elapsed / 60

        # 결과 저장
        urls_path = os.path.join(BASE_DIR, target_folder, "cf1001_urls_database.json")
        with open(urls_path, 'w', encoding='utf-8') as f:
            json.dump(self.collected_urls, f, ensure_ascii=False, indent=2)

        failed_path = os.path.join(BASE_DIR, target_folder, "cf1001_failed.json")
        with open(failed_path, 'w', encoding='utf-8') as f:
            json.dump(self.failed_companies, f, ensure_ascii=False, indent=2)

        success_rate = success_count / total * 100 if total > 0 else 0
        print(f"\n📋 수집 완료: {success_count}/{total} ({success_rate:.1f}%)")
        print(f"⏱️ 소요 시간: {elapsed_min:.1f}분")

        return {
            "success": True,
            "total": total,
            "success_count": success_count,
            "failed_count": len(self.failed_companies),
            "success_rate": success_rate,
            "elapsed_minutes": round(elapsed_min, 1),
            "target_folder": target_folder
        }


def start_financial_scheduler():
    """재무 URL 일일 자동 수집 스케줄러 시작 (백그라운드 스레드)"""

    def scheduler_loop():
        print("📅 재무 URL 스케줄러 시작 - 매일 10:30 KST 수집")

        while True:
            now = datetime.now(KST)

            # 다음 10:30 KST 계산 (매일, 주말 포함)
            target = now.replace(hour=10, minute=30, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)

            wait_seconds = (target - now).total_seconds()
            hours = int(wait_seconds // 3600)
            mins = int((wait_seconds % 3600) // 60)
            print(f"  ⏰ 다음 재무 수집: {target.strftime('%Y-%m-%d %H:%M')} KST ({hours}시간 {mins}분 후)")

            # 대기 (1분마다 체크)
            while (target - datetime.now(KST)).total_seconds() > 0:
                time.sleep(60)

            # 수집 실행
            try:
                print(f"\n🔄 재무 URL 자동 수집 시작: {datetime.now(KST).strftime('%Y-%m-%d %H:%M')}")

                collector = FinancialURLAutoCollector(delay=0.5, max_workers=3)

                # 비활성 폴더에 수집
                target_folder = collector.get_target_folder()
                active_folder = collector.get_active_folder()
                print(f"📁 현재 활성: {active_folder} → 수집 대상: {target_folder}")

                result = collector.run_collection(target_folder)

                if result["success"] and result["success_rate"] >= 95.0:
                    # 성공률 95% 이상이면 A/B 교체
                    print(f"✅ 수집 성공 ({result['success_rate']:.1f}%) — 폴더 교체 실행")
                    collector.swap_active_folder(target_folder)
                    print(f"🔄 활성 폴더 교체 완료: {active_folder} → {target_folder}")
                elif result["success"]:
                    print(f"⚠️ 수집 완료했으나 성공률 부족 ({result['success_rate']:.1f}%) — 교체 보류")
                else:
                    print(f"❌ 수집 실패: {result.get('error', 'unknown')}")

                print(f"✅ 재무 URL 자동 수집 종료: {datetime.now(KST).strftime('%Y-%m-%d %H:%M')}")

            except Exception as e:
                print(f"❌ 재무 URL 자동 수집 실패: {e}")

    thread = threading.Thread(target=scheduler_loop, daemon=True, name="financial-url-scheduler")
    thread.start()
    return thread


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # 테스트 모드: 즉시 수집 실행
        print("🧪 테스트 모드: 즉시 수집 실행")
        collector = FinancialURLAutoCollector(delay=0.5, max_workers=3)

        target_folder = collector.get_target_folder()
        active_folder = collector.get_active_folder()
        print(f"📁 현재 활성: {active_folder} → 수집 대상: {target_folder}")

        result = collector.run_collection(target_folder)
        print(f"\n📊 결과: {json.dumps(result, ensure_ascii=False, indent=2)}")

        if result["success"] and result["success_rate"] >= 95.0:
            swap = input("\n🔄 활성 폴더를 교체하시겠습니까? (y/N): ").strip().lower()
            if swap == 'y':
                collector.swap_active_folder(target_folder)
    else:
        # 스케줄러 모드
        print("📅 재무 URL 스케줄러 독립 실행 모드")
        start_financial_scheduler()
        while True:
            time.sleep(3600)
