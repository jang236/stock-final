"""
📈 코스피/코스닥 차트 데이터 수집기
네이버 증권 차트 API → SQLite 저장
"""
import requests
import sqlite3
import json
import re
import time
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

KST = timezone(timedelta(hours=9))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chart_data.db")
NAVER_CHART_URL = "https://fchart.stock.naver.com/siseJson.naver"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


class ChartCollector:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """SQLite 데이터베이스 및 테이블 초기화"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS chart_data (
                symbol TEXT NOT NULL,
                date TEXT NOT NULL,
                open INTEGER,
                high INTEGER,
                low INTEGER,
                close INTEGER,
                volume INTEGER,
                foreign_ratio REAL,
                PRIMARY KEY (symbol, date)
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_chart_symbol ON chart_data(symbol)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_chart_date ON chart_data(date)")
        c.execute("""
            CREATE TABLE IF NOT EXISTS collection_meta (
                symbol TEXT PRIMARY KEY,
                name TEXT,
                market TEXT,
                last_collected TEXT,
                row_count INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def fetch_chart_data(self, symbol: str, start_date: str, end_date: str) -> list:
        """네이버 증권 API에서 일봉 데이터 조회
        Args:
            symbol: 종목코드 (예: '005930')
            start_date: 시작일 (예: '20240323')
            end_date: 종료일 (예: '20250323')
        Returns:
            list of dict: [{date, open, high, low, close, volume, foreign_ratio}, ...]
        """
        params = {
            "symbol": symbol,
            "requestType": "1",
            "startTime": start_date,
            "endTime": end_date,
            "timeframe": "day"
        }
        try:
            resp = requests.get(NAVER_CHART_URL, params=params, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                return []

            rows = []
            for line in resp.text.strip().split("\n"):
                match = re.search(r'\["(\d{8})",\s*(\d*),\s*(\d*),\s*(\d*),\s*(\d*),\s*(\d*),\s*([\d.]*)\]', line)
                if match:
                    safe_int = lambda v: int(v) if v and v.strip() else 0
                    safe_float = lambda v: float(v) if v and v.strip() else 0.0
                    close_val = safe_int(match.group(5))
                    # 종가가 0인 행은 거래 없는 날이므로 스킵
                    if close_val == 0:
                        continue
                    rows.append({
                        "date": match.group(1),
                        "open": safe_int(match.group(2)),
                        "high": safe_int(match.group(3)),
                        "low": safe_int(match.group(4)),
                        "close": close_val,
                        "volume": safe_int(match.group(6)),
                        "foreign_ratio": safe_float(match.group(7))
                    })
            return rows
        except Exception as e:
            print(f"  ⚠️ {symbol} API 에러: {e}")
            return []

    def save_to_db(self, symbol: str, data: list, name: str = "", market: str = ""):
        """수집된 차트 데이터를 SQLite에 저장 (UPSERT)"""
        if not data:
            return 0
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        inserted = 0
        for row in data:
            c.execute("""
                INSERT OR REPLACE INTO chart_data 
                (symbol, date, open, high, low, close, volume, foreign_ratio)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (symbol, row["date"], row["open"], row["high"], row["low"],
                  row["close"], row["volume"], row["foreign_ratio"]))
            inserted += 1

        now = datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("""
            INSERT OR REPLACE INTO collection_meta (symbol, name, market, last_collected, row_count)
            VALUES (?, ?, ?, ?, ?)
        """, (symbol, name, market, now, inserted))
        conn.commit()
        conn.close()
        return inserted

    def collect_single(self, symbol: str, name: str = "", market: str = "",
                       days: int = 365) -> int:
        """단일 종목 차트 데이터 수집"""
        end_date = datetime.now(KST).strftime("%Y%m%d")
        start_date = (datetime.now(KST) - timedelta(days=days)).strftime("%Y%m%d")

        data = self.fetch_chart_data(symbol, start_date, end_date)
        if data:
            saved = self.save_to_db(symbol, data, name, market)
            return saved
        return 0

    # ─── 종목 리스트 확보 ───

    def fetch_stock_list(self) -> list:
        """종목 리스트 확보 (stock_companies.json 우선, 없으면 네이버 크롤링)"""
        stocks = []

        # 1차: stock_companies.json 파일에서 로드
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stock_companies.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    stock_data = json.load(f)

                if isinstance(stock_data, dict):
                    # 형식: {"회사명": {"code": "종목코드"}, ...}
                    for name, details in stock_data.items():
                        code = details.get("code", "") if isinstance(details, dict) else str(details)
                        if code and name:
                            stocks.append({
                                "symbol": code,
                                "name": name,
                                "market": "KOSPI"
                            })
                elif isinstance(stock_data, list):
                    # 형식: [{"code": "xxx", "name": "yyy"}, ...] 또는 [["name", "code"], ...]
                    for item in stock_data:
                        if isinstance(item, dict):
                            code = item.get("code", "")
                            name = item.get("name", "")
                        elif isinstance(item, (list, tuple)) and len(item) >= 2:
                            name, code = str(item[0]), str(item[1])
                        else:
                            continue
                        if code and name:
                            stocks.append({
                                "symbol": code,
                                "name": name,
                                "market": "KOSPI"
                            })

                print(f"  📋 stock_companies.json에서 {len(stocks)}종목 로드")
                if stocks:
                    return stocks
            except Exception as e:
                print(f"  ⚠️ stock_companies.json 로드 실패: {e}")

        # 2차: 네이버 증권 크롤링 (fallback)
        print("  📋 네이버 증권에서 종목 리스트 크롤링...")
        for market_type, market_name in [("0", "KOSPI"), ("1", "KOSDAQ")]:
            try:
                page = 1
                while True:
                    list_url = (
                        f"https://finance.naver.com/sise/sise_market_sum.naver"
                        f"?sosok={market_type}&page={page}"
                    )
                    resp = requests.get(list_url, headers=HEADERS, timeout=15)
                    if resp.status_code != 200:
                        break

                    codes = re.findall(
                        r'href="/item/main\.naver\?code=(\d{6})"[^>]*>\s*([^<]+)',
                        resp.text
                    )
                    if not codes:
                        break

                    for code, name in codes:
                        name = name.strip()
                        if name and code not in [s["symbol"] for s in stocks]:
                            stocks.append({
                                "symbol": code,
                                "name": name,
                                "market": market_name
                            })
                    page += 1
                    time.sleep(0.2)

                print(f"  {market_name}: {sum(1 for s in stocks if s['market']==market_name)}종목")
            except Exception as e:
                print(f"  ⚠️ {market_name} 종목 리스트 수집 에러: {e}")

        return stocks

    # ─── 전량 수집 ───

    def collect_all(self, days: int = 365, delay: float = 0.3,
                    progress_file: str = "chart_collect_progress.json"):
        """전 종목 차트 데이터 수집 (백그라운드 실행용)"""
        print("=" * 60)
        print("📈 코스피/코스닥 차트 데이터 수집기")
        print("=" * 60)

        # 종목 리스트 확보
        print("\n📋 종목 리스트 수집 중...")
        stocks = self.fetch_stock_list()
        if not stocks:
            print("❌ 종목 리스트를 가져올 수 없습니다.")
            return

        # 기존 진행상황 로드
        completed = set()
        if os.path.exists(progress_file):
            try:
                with open(progress_file, "r") as f:
                    progress = json.load(f)
                    completed = set(progress.get("completed", []))
                    print(f"  기존 진행: {len(completed)}종목 완료")
            except:
                pass

        # 수집 시작
        total = len(stocks)
        remaining = [s for s in stocks if s["symbol"] not in completed]
        success_count = len(completed)
        fail_count = 0

        print(f"\n전체: {total}개 / 완료: {len(completed)}개 / 남은: {len(remaining)}개")
        print(f"API 호출 간격: {delay}초")
        print("=" * 60)

        for i, stock in enumerate(remaining, 1):
            sym = stock["symbol"]
            name = stock["name"]
            market = stock["market"]

            try:
                rows = self.collect_single(sym, name, market, days)
                if rows > 0:
                    success_count += 1
                    print(f"  [{len(completed)+i}/{total}] {sym} ({name}) → {rows}행 ✅")
                else:
                    fail_count += 1
                    print(f"  [{len(completed)+i}/{total}] {sym} ({name}) → 데이터없음 ⚠️")
            except Exception as e:
                fail_count += 1
                print(f"  [{len(completed)+i}/{total}] {sym} ({name}) → 에러: {e} ❌")

            completed.add(sym)

            # 100종목마다 중간 저장
            if i % 100 == 0:
                with open(progress_file, "w") as f:
                    json.dump({
                        "completed": list(completed),
                        "success": success_count,
                        "failed": fail_count,
                        "total": total,
                        "last_update": datetime.now(KST).isoformat()
                    }, f, ensure_ascii=False, indent=2)
                print(f"\n  --- 중간 저장 (완료: {success_count}/{total}) ---\n")

            time.sleep(delay)

        # 최종 저장
        with open(progress_file, "w") as f:
            json.dump({
                "completed": list(completed),
                "success": success_count,
                "failed": fail_count,
                "total": total,
                "last_update": datetime.now(KST).isoformat(),
                "status": "completed"
            }, f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 60)
        print(f"✅ 수집 완료! 성공: {success_count} / 실패: {fail_count} / 전체: {total}")
        print("=" * 60)

    # ─── 일일 업데이트 ───

    def daily_update(self, delay: float = 0.3):
        """일일 차트 데이터 업데이트 (당일 데이터만 추가)"""
        print(f"\n📅 일일 업데이트 시작: {datetime.now(KST).strftime('%Y-%m-%d %H:%M')}")

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        stocks = c.execute("SELECT symbol, name, market FROM collection_meta").fetchall()
        conn.close()

        if not stocks:
            print("  ⚠️ 수집된 종목이 없습니다. collect_all()을 먼저 실행하세요.")
            return

        # 최근 5일 데이터 업데이트 (주말/공휴일 고려)
        end_date = datetime.now(KST).strftime("%Y%m%d")
        start_date = (datetime.now(KST) - timedelta(days=7)).strftime("%Y%m%d")

        success = 0
        fail = 0
        total = len(stocks)

        for i, (sym, name, market) in enumerate(stocks, 1):
            data = self.fetch_chart_data(sym, start_date, end_date)
            if data:
                self.save_to_db(sym, data, name, market)
                success += 1
            else:
                fail += 1

            if i % 500 == 0:
                print(f"  진행: {i}/{total} (성공: {success})")
            time.sleep(delay)

        print(f"  ✅ 일일 업데이트 완료: 성공 {success} / 실패 {fail} / 전체 {total}")

    # ─── 상태 확인 ───

    def get_status(self) -> dict:
        """수집 현황 조회"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        total_rows = c.execute("SELECT COUNT(*) FROM chart_data").fetchone()[0]
        total_stocks = c.execute("SELECT COUNT(DISTINCT symbol) FROM chart_data").fetchone()[0]
        latest = c.execute("SELECT MAX(date) FROM chart_data").fetchone()[0]
        oldest = c.execute("SELECT MIN(date) FROM chart_data").fetchone()[0]
        conn.close()
        return {
            "total_rows": total_rows,
            "total_stocks": total_stocks,
            "date_range": f"{oldest} ~ {latest}" if oldest else "N/A",
            "db_size_mb": round(os.path.getsize(self.db_path) / 1024 / 1024, 2) if os.path.exists(self.db_path) else 0
        }


# ─── 메인 실행 ───
if __name__ == "__main__":
    import sys

    collector = ChartCollector()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "status":
            status = collector.get_status()
            print(f"📊 차트 DB 현황")
            print(f"  종목 수: {status['total_stocks']}")
            print(f"  총 행수: {status['total_rows']:,}")
            print(f"  기간: {status['date_range']}")
            print(f"  DB 크기: {status['db_size_mb']} MB")
        elif cmd == "daily":
            collector.daily_update()
        elif cmd == "test":
            symbol = sys.argv[2] if len(sys.argv) > 2 else "005930"
            rows = collector.collect_single(symbol, "테스트")
            print(f"  {symbol}: {rows}행 수집 완료")
            print(collector.get_status())
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python chart_collector.py [status|daily|test [symbol]]")
    else:
        # 기본: 전량 수집
        collector.collect_all()
