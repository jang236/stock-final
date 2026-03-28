"""
📊 차트 데이터 조회 + 기술적 지표 계산 서비스
SQLite에서 데이터를 읽어 이동평균, RSI, MACD, 볼린저밴드 등을 계산
"""
import sqlite3
import os
import math
from datetime import datetime, timedelta, timezone
from typing import Optional

KST = timezone(timedelta(hours=9))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chart_data.db")


class ChartService:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    def _query(self, sql: str, params: tuple = ()) -> list:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ─── 기본 조회 ───

    def get_daily(self, symbol: str, days: int = 60) -> list:
        """일봉 데이터 조회 (최근 N일)"""
        return self._query(
            "SELECT * FROM chart_data WHERE symbol=? ORDER BY date DESC LIMIT ?",
            (symbol, days)
        )

    def get_range(self, symbol: str, start: str, end: str) -> list:
        """기간 지정 일봉 조회"""
        return self._query(
            "SELECT * FROM chart_data WHERE symbol=? AND date BETWEEN ? AND ? ORDER BY date",
            (symbol, start, end)
        )

    def get_weekly(self, symbol: str, weeks: int = 52) -> list:
        """주봉 데이터 생성 (일봉에서 계산)"""
        days_needed = weeks * 7
        daily = self._query(
            "SELECT * FROM chart_data WHERE symbol=? ORDER BY date DESC LIMIT ?",
            (symbol, days_needed)
        )
        if not daily:
            return []

        daily.reverse()  # 날짜 오름차순

        weekly = []
        current_week = []
        for row in daily:
            # ISO 주 기준으로 그룹핑
            dt = datetime.strptime(row["date"], "%Y%m%d")
            week_key = dt.isocalendar()[:2]  # (year, week)

            if current_week and datetime.strptime(current_week[0]["date"], "%Y%m%d").isocalendar()[:2] != week_key:
                weekly.append(self._aggregate_week(current_week))
                current_week = []
            current_week.append(row)

        if current_week:
            weekly.append(self._aggregate_week(current_week))

        return weekly[-weeks:]

    def _aggregate_week(self, days: list) -> dict:
        return {
            "date": days[-1]["date"],  # 주 마지막 거래일
            "open": days[0]["open"],
            "high": max(d["high"] for d in days),
            "low": min(d["low"] for d in days),
            "close": days[-1]["close"],
            "volume": sum(d["volume"] for d in days),
            "foreign_ratio": days[-1]["foreign_ratio"]
        }

    # ─── 기술적 지표 계산 ───

    def calc_moving_averages(self, closes: list) -> dict:
        """이동평균선 계산 (5, 10, 20, 60, 120일)"""
        ma = {}
        for period in [5, 10, 20, 60, 120]:
            if len(closes) >= period:
                ma[f"ma{period}"] = round(sum(closes[-period:]) / period)
            else:
                ma[f"ma{period}"] = None
        return ma

    def calc_rsi(self, closes: list, period: int = 14) -> Optional[float]:
        """RSI (Relative Strength Index) 계산"""
        if len(closes) < period + 1:
            return None

        gains, losses = [], []
        for i in range(1, len(closes)):
            diff = closes[i] - closes[i - 1]
            gains.append(max(0, diff))
            losses.append(max(0, -diff))

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)

    def calc_macd(self, closes: list) -> Optional[dict]:
        """MACD (12, 26, 9) 계산"""
        if len(closes) < 26:
            return None

        def ema(data, period):
            k = 2 / (period + 1)
            result = [data[0]]
            for i in range(1, len(data)):
                result.append(data[i] * k + result[-1] * (1 - k))
            return result

        ema12 = ema(closes, 12)
        ema26 = ema(closes, 26)
        macd_line = [ema12[i] - ema26[i] for i in range(len(closes))]
        signal = ema(macd_line, 9)
        histogram = [macd_line[i] - signal[i] for i in range(len(closes))]

        return {
            "macd": round(macd_line[-1]),
            "signal": round(signal[-1]),
            "histogram": round(histogram[-1])
        }

    def calc_bollinger(self, closes: list, period: int = 20) -> Optional[dict]:
        """볼린저 밴드 (20일, 2σ) 계산"""
        if len(closes) < period:
            return None

        recent = closes[-period:]
        middle = sum(recent) / period
        variance = sum((x - middle) ** 2 for x in recent) / period
        std = math.sqrt(variance)

        upper = round(middle + 2 * std)
        lower = round(middle - 2 * std)
        current = closes[-1]

        # 현재가 위치 판단
        if current > upper:
            position = "상단 돌파"
        elif current > middle:
            position = "중단~상단"
        elif current > lower:
            position = "하단~중단"
        else:
            position = "하단 이탈"

        return {
            "upper": upper,
            "middle": round(middle),
            "lower": lower,
            "position": position
        }

    # ─── 종합 분석 ───

    def analyze(self, symbol: str, days: int = 120) -> dict:
        """종합 기술적 분석 (AI 제공용)"""
        rows = self.get_daily(symbol, days)
        if not rows:
            return {"error": f"No data for {symbol}"}

        rows.reverse()  # 날짜 오름차순으로 정렬
        closes = [r["close"] for r in rows]
        current_price = closes[-1]

        # 이동평균선
        ma = self.calc_moving_averages(closes)

        # MA 배열 판단
        ma_values = [v for v in [ma.get("ma5"), ma.get("ma20"), ma.get("ma60"), ma.get("ma120")] if v is not None]
        if len(ma_values) >= 3:
            if ma_values == sorted(ma_values, reverse=True):
                ma_alignment = "정배열 (단기>장기, 상승 추세)"
            elif ma_values == sorted(ma_values):
                ma_alignment = "역배열 (단기<장기, 하락 추세)"
            else:
                ma_alignment = "혼조세"
        else:
            ma_alignment = "데이터 부족"

        # 골든크로스/데드크로스 (5일선 vs 20일선, 최근 5일 이내)
        cross = "없음"
        if len(closes) >= 25:
            for i in range(-5, 0):
                idx = len(closes) + i
                if idx >= 20:
                    ma5_prev = sum(closes[idx-5:idx]) / 5
                    ma20_prev = sum(closes[idx-20:idx]) / 20
                    ma5_curr = sum(closes[idx-4:idx+1]) / 5
                    ma20_curr = sum(closes[idx-19:idx+1]) / 20
                    if ma5_prev < ma20_prev and ma5_curr >= ma20_curr:
                        cross = f"골든크로스 (날짜: {rows[idx]['date']})"
                        break
                    elif ma5_prev > ma20_prev and ma5_curr <= ma20_curr:
                        cross = f"데드크로스 (날짜: {rows[idx]['date']})"
                        break

        # RSI
        rsi = self.calc_rsi(closes)
        if rsi is not None:
            if rsi >= 70:
                rsi_signal = "과매수 (매도 주의)"
            elif rsi >= 60:
                rsi_signal = "강세"
            elif rsi >= 40:
                rsi_signal = "중립"
            elif rsi >= 30:
                rsi_signal = "약세"
            else:
                rsi_signal = "과매도 (매수 기회)"
        else:
            rsi_signal = "데이터 부족"

        # MACD
        macd = self.calc_macd(closes)

        # 볼린저밴드
        bollinger = self.calc_bollinger(closes)

        # 거래량 추세 (최근 5일 vs 이전 20일)
        if len(rows) >= 25:
            vol_recent = sum(r["volume"] for r in rows[-5:]) / 5
            vol_prev = sum(r["volume"] for r in rows[-25:-5]) / 20
            vol_ratio = round(vol_recent / vol_prev, 2) if vol_prev > 0 else 0
            if vol_ratio > 1.5:
                vol_trend = f"급증 ({vol_ratio}배)"
            elif vol_ratio > 1.1:
                vol_trend = f"증가 ({vol_ratio}배)"
            elif vol_ratio > 0.9:
                vol_trend = "보합"
            else:
                vol_trend = f"감소 ({vol_ratio}배)"
        else:
            vol_trend = "데이터 부족"
            vol_ratio = None

        # 추세 판단
        if ma.get("ma20") and ma.get("ma60"):
            if current_price > ma["ma20"] > ma["ma60"]:
                trend = "상승 추세"
            elif current_price < ma["ma20"] < ma["ma60"]:
                trend = "하락 추세"
            elif current_price > ma["ma20"]:
                trend = "단기 반등"
            else:
                trend = "단기 조정"
        else:
            trend = "판단 불가"

        # 지지/저항선 (최근 60일 고가/저가 기반)
        recent_60 = rows[-60:] if len(rows) >= 60 else rows
        highs = sorted(set(r["high"] for r in recent_60), reverse=True)
        lows = sorted(set(r["low"] for r in recent_60))
        resistance = [h for h in highs[:3] if h > current_price]
        support = [l for l in lows[:3] if l < current_price]

        # 최근 N일 데이터 (AI에게 제공)
        recent_data = []
        for r in rows[-20:]:
            entry = {
                "date": r["date"],
                "open": r["open"],
                "high": r["high"],
                "low": r["low"],
                "close": r["close"],
                "volume": r["volume"]
            }
            # 각 날짜별 이동평균 추가
            idx = rows.index(r)
            for period in [5, 20, 60]:
                if idx >= period - 1:
                    entry[f"ma{period}"] = round(
                        sum(rows[j]["close"] for j in range(idx - period + 1, idx + 1)) / period
                    )
            recent_data.append(entry)

        # 메타 정보
        meta_row = self._query(
            "SELECT name, market FROM collection_meta WHERE symbol=?", (symbol,)
        )
        name = meta_row[0]["name"] if meta_row else symbol
        market = meta_row[0]["market"] if meta_row else ""

        return {
            "symbol": symbol,
            "name": name,
            "market": market,
            "current_price": current_price,
            "data_period": f"{rows[0]['date']} ~ {rows[-1]['date']}",
            "data_count": len(rows),
            "analysis": {
                "trend": trend,
                "ma_alignment": ma_alignment,
                "cross": cross,
                "moving_averages": ma,
                "rsi": rsi,
                "rsi_signal": rsi_signal,
                "macd": macd,
                "bollinger": bollinger,
                "volume_trend": vol_trend,
                "volume_ratio": vol_ratio,
                "support": support[:3],
                "resistance": resistance[:3]
            },
            "recent_20days": recent_data
        }

    # ─── 종목 검색 ───

    def search_stocks(self, query: str) -> list:
        """종목명으로 검색"""
        return self._query(
            "SELECT symbol, name, market FROM collection_meta WHERE name LIKE ?",
            (f"%{query}%",)
        )

    def list_available(self) -> dict:
        """수집된 종목 목록"""
        rows = self._query(
            "SELECT market, COUNT(*) as cnt FROM collection_meta GROUP BY market"
        )
        total = self._query("SELECT COUNT(*) as cnt FROM collection_meta")[0]["cnt"]
        return {
            "total": total,
            "by_market": {r["market"]: r["cnt"] for r in rows}
        }

    def get_db_status(self) -> dict:
        """DB 상태 정보"""
        if not os.path.exists(self.db_path):
            return {"status": "not_initialized"}

        total_rows = self._query("SELECT COUNT(*) as cnt FROM chart_data")[0]["cnt"]
        total_stocks = self._query("SELECT COUNT(DISTINCT symbol) as cnt FROM chart_data")[0]["cnt"]
        latest = self._query("SELECT MAX(date) as d FROM chart_data")[0]["d"]
        oldest = self._query("SELECT MIN(date) as d FROM chart_data")[0]["d"]
        db_size = round(os.path.getsize(self.db_path) / 1024 / 1024, 2)

        return {
            "status": "ready",
            "total_stocks": total_stocks,
            "total_rows": total_rows,
            "date_range": f"{oldest} ~ {latest}" if oldest else "N/A",
            "db_size_mb": db_size
        }
