"""
📊 차트 데이터 조회 + 기술적 지표 계산 서비스
SQLite에서 데이터를 읽어 이동평균, RSI, MACD, 볼린저밴드 등을 계산
"""
import sqlite3
import os
import math
import requests
import re
from datetime import datetime, timedelta, timezone
from typing import Optional

KST = timezone(timedelta(hours=9))
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chart_data.db")
NAVER_CHART_URL = "https://fchart.stock.naver.com/siseJson.naver"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


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

    # ─── 당일 데이터 실시간 보정 ───

    def _supplement_today(self, symbol: str, rows: list) -> list:
        """DB 데이터가 오늘자가 아니면 네이버 API에서 실시간 보정"""
        today = datetime.now(KST).strftime("%Y%m%d")

        # 주말이면 보정 불필요
        weekday = datetime.now(KST).weekday()
        if weekday >= 5:  # 토(5), 일(6)
            return rows

        # 이미 오늘 데이터가 있으면 패스
        if rows and rows[-1]["date"] >= today:
            return rows

        # 장 시작 전(09:00 이전)이면 패스
        hour = datetime.now(KST).hour
        if hour < 9:
            return rows

        # 네이버 차트 API에서 최근 7일만 조회 (1회 HTTP 호출)
        try:
            end = today
            start = (datetime.now(KST) - timedelta(days=7)).strftime("%Y%m%d")
            params = {
                "symbol": symbol,
                "requestType": "1",
                "startTime": start,
                "endTime": end,
                "timeframe": "day"
            }
            resp = requests.get(NAVER_CHART_URL, params=params, headers=HEADERS, timeout=10)
            if resp.status_code != 200:
                return rows

            existing_dates = {r["date"] for r in rows}
            safe_int = lambda v: int(v) if v and v.strip() else 0
            safe_float = lambda v: float(v) if v and v.strip() else 0.0

            for line in resp.text.strip().split("\n"):
                match = re.search(
                    r'\["(\d{8})",\s*(\d*),\s*(\d*),\s*(\d*),\s*(\d*),\s*(\d*),\s*([\d.]*)\]',
                    line
                )
                if match:
                    date_val = match.group(1)
                    close_val = safe_int(match.group(5))
                    if close_val == 0 or date_val in existing_dates:
                        continue
                    rows.append({
                        "date": date_val,
                        "open": safe_int(match.group(2)),
                        "high": safe_int(match.group(3)),
                        "low": safe_int(match.group(4)),
                        "close": close_val,
                        "volume": safe_int(match.group(6)),
                        "foreign_ratio": safe_float(match.group(7)),
                        "symbol": symbol
                    })

            rows.sort(key=lambda x: x["date"])
        except Exception as e:
            print(f"  ⚠️ 당일 보정 실패 ({symbol}): {e}")

        return rows

    # ─── 고급 분석 ───

    def calc_similar_periods(self, rows: list, closes: list, current_rsi: float, macd_data: dict) -> list:
        """과거 유사 구간 비교 — RSI·MACD가 현재와 비슷했던 과거 시점 + 이후 수익률"""
        if not current_rsi or not macd_data or len(closes) < 80:
            return []

        current_macd_positive = macd_data.get("histogram", 0) > 0
        similar = []

        # 과거 데이터를 순회하며 유사 구간 탐색 (최근 20일은 제외)
        for i in range(30, len(closes) - 20):
            # RSI 계산 (해당 시점까지의 데이터)
            segment = closes[:i+1]
            past_rsi = self.calc_rsi(segment)
            if past_rsi is None:
                continue

            # RSI 유사도 (±5 범위)
            if abs(past_rsi - current_rsi) > 5:
                continue

            # MACD 방향 유사도
            past_macd = self.calc_macd(segment)
            if not past_macd:
                continue
            past_macd_positive = past_macd.get("histogram", 0) > 0
            if past_macd_positive != current_macd_positive:
                continue

            # 이후 수익률 계산
            base_price = closes[i]
            returns = {}
            for days, label in [(5, "return_5d"), (20, "return_20d"), (60, "return_60d")]:
                if i + days < len(closes):
                    ret = round((closes[i + days] - base_price) / base_price * 100, 1)
                    returns[label] = ret
                else:
                    returns[label] = None

            similar.append({
                "date": rows[i]["date"],
                "rsi": past_rsi,
                "macd_histogram": past_macd["histogram"],
                "price": base_price,
                **returns
            })

        # 최대 5개만 반환 (가장 최근 유사 구간부터)
        similar = similar[-5:] if len(similar) > 5 else similar

        # 통계 요약
        if similar:
            valid_5d = [s["return_5d"] for s in similar if s.get("return_5d") is not None]
            valid_20d = [s["return_20d"] for s in similar if s.get("return_20d") is not None]
            valid_60d = [s["return_60d"] for s in similar if s.get("return_60d") is not None]

            summary = {
                "count": len(similar),
                "avg_return_5d": round(sum(valid_5d) / len(valid_5d), 1) if valid_5d else None,
                "avg_return_20d": round(sum(valid_20d) / len(valid_20d), 1) if valid_20d else None,
                "avg_return_60d": round(sum(valid_60d) / len(valid_60d), 1) if valid_60d else None,
                "win_rate_20d": round(sum(1 for r in valid_20d if r > 0) / len(valid_20d) * 100) if valid_20d else None
            }
        else:
            summary = {"count": 0}

        return {"periods": similar, "summary": summary}

    def calc_disparity(self, closes: list) -> dict:
        """이동평균선 이격도 추이 — 현재 이격도 + 1년 내 맥락"""
        result = {}
        current_price = closes[-1]

        for period, label in [(20, "ma20"), (60, "ma60")]:
            if len(closes) < period:
                continue

            # 현재 이격도
            ma_value = sum(closes[-period:]) / period
            current_disparity = round((current_price / ma_value - 1) * 100, 1)

            # 과거 이격도 히스토리 (최대 250일)
            history = []
            for i in range(period, len(closes)):
                ma_at_i = sum(closes[i-period:i]) / period
                disp = round((closes[i] / ma_at_i - 1) * 100, 1)
                history.append(disp)

            if not history:
                continue

            # 통계
            max_disp = max(history)
            min_disp = min(history)
            avg_disp = round(sum(history) / len(history), 1)

            # 백분위 (현재 이격도가 히스토리에서 어느 위치인지)
            below = sum(1 for h in history if h < current_disparity)
            percentile = round(below / len(history) * 100)

            result[label] = {
                "current": current_disparity,
                "ma_value": round(ma_value),
                "max_1y": max_disp,
                "min_1y": min_disp,
                "avg_1y": avg_disp,
                "percentile": percentile,
                "interpretation": self._interpret_disparity(current_disparity, percentile, label)
            }

        return result

    def _interpret_disparity(self, disparity: float, percentile: int, ma_type: str) -> str:
        """이격도 해석"""
        if percentile <= 10:
            return f"하위 {percentile}% — 극단적 이격, 반등 가능성 높음"
        elif percentile <= 25:
            return f"하위 {percentile}% — 과도한 이격, 회귀 가능성"
        elif percentile >= 90:
            return f"상위 {100-percentile}% — 극단적 괴리, 조정 가능성 높음"
        elif percentile >= 75:
            return f"상위 {100-percentile}% — 과열 구간, 주의 필요"
        else:
            return f"중립 구간 ({percentile}%)"

    def calc_volume_anomaly(self, rows: list) -> dict:
        """거래량 이상 감지 — 가격·거래량 조합 해석"""
        if len(rows) < 25:
            return {"signal": "데이터 부족"}

        today = rows[-1]
        today_vol = today["volume"]
        today_change = (today["close"] - rows[-2]["close"]) / rows[-2]["close"] * 100 if len(rows) >= 2 else 0

        # 평균 거래량
        vol_5d = sum(r["volume"] for r in rows[-6:-1]) / 5  # 오늘 제외 5일
        vol_20d = sum(r["volume"] for r in rows[-21:-1]) / 20  # 오늘 제외 20일

        ratio_5d = round(today_vol / vol_5d, 2) if vol_5d > 0 else 0
        ratio_20d = round(today_vol / vol_20d, 2) if vol_20d > 0 else 0

        # 거래량 + 가격 방향 조합 해석
        if ratio_20d >= 2.0:
            if today_change > 0:
                signal = "거래량 폭증 + 상승 → 세력 매수 가능, 추세 전환 시그널"
                level = "매우 강함"
            else:
                signal = "거래량 폭증 + 하락 → 투매 또는 손절 물량, 바닥 확인 필요"
                level = "매우 강함"
        elif ratio_20d >= 1.5:
            if today_change > 0:
                signal = "거래량 증가 + 상승 → 건전한 상승, 추세 지속 가능"
                level = "강함"
            else:
                signal = "거래량 증가 + 하락 → 매도 압력 증가, 추가 하락 주의"
                level = "강함"
        elif ratio_20d <= 0.5:
            if today_change > 0:
                signal = "거래량 급감 + 상승 → 상승 동력 약화, 신뢰도 낮음"
                level = "약함"
            else:
                signal = "거래량 급감 + 하락 → 관심 감소, 바닥 다지기 가능"
                level = "약함"
        else:
            signal = "거래량 보합권 → 특이사항 없음"
            level = "보통"

        return {
            "today_volume": today_vol,
            "avg_5d": round(vol_5d),
            "avg_20d": round(vol_20d),
            "ratio_5d": ratio_5d,
            "ratio_20d": ratio_20d,
            "price_change": round(today_change, 2),
            "signal": signal,
            "level": level
        }

    def calc_support_resistance_strength(self, rows: list, closes: list, ma: dict) -> dict:
        """지지/저항선 강도 점수 (1~10)"""
        if len(rows) < 60:
            return {"support": [], "resistance": []}

        current_price = closes[-1]
        recent_60 = rows[-60:]

        # 지지선/저항선 후보 추출
        highs = sorted(set(r["high"] for r in recent_60), reverse=True)
        lows = sorted(set(r["low"] for r in recent_60))
        resistance_candidates = [h for h in highs[:5] if h > current_price]
        support_candidates = [l for l in lows[:5] if l < current_price]

        def score_level(price_level, is_support=True):
            score = 0
            reasons = []

            # 1. 이동평균선 근접 (±2% 이내) — 최대 3점
            for period, ma_key in [(20, "ma20"), (60, "ma60"), (120, "ma120")]:
                ma_val = ma.get(ma_key)
                if ma_val and abs(ma_val - price_level) / price_level < 0.02:
                    score += 3
                    reasons.append(f"이동평균선 {period}일 근접")
                    break  # 하나만 카운트

            # 2. 과거 지지/저항 횟수 — 최대 4점
            touch_count = 0
            for r in recent_60:
                if is_support:
                    if abs(r["low"] - price_level) / price_level < 0.02:
                        touch_count += 1
                else:
                    if abs(r["high"] - price_level) / price_level < 0.02:
                        touch_count += 1
            touch_score = min(touch_count, 4)
            score += touch_score
            if touch_count > 0:
                reasons.append(f"과거 {touch_count}회 {'지지' if is_support else '저항'}")

            # 3. 거래량 집중 구간 — 최대 3점
            vol_at_level = []
            for r in recent_60:
                if abs(r["close"] - price_level) / price_level < 0.03:
                    vol_at_level.append(r["volume"])
            if vol_at_level:
                avg_vol = sum(r["volume"] for r in recent_60) / len(recent_60)
                vol_ratio = sum(vol_at_level) / len(vol_at_level) / avg_vol if avg_vol > 0 else 0
                if vol_ratio > 1.5:
                    score += 3
                    reasons.append("거래량 집중 구간")
                elif vol_ratio > 1.0:
                    score += 1
                    reasons.append("거래량 소폭 집중")

            return {
                "price": price_level,
                "score": min(score, 10),
                "reasons": reasons,
                "vs_current": round((price_level - current_price) / current_price * 100, 1)
            }

        support_scored = [score_level(p, is_support=True) for p in support_candidates[:3]]
        resistance_scored = [score_level(p, is_support=False) for p in resistance_candidates[:3]]

        # 점수 내림차순 정렬
        support_scored.sort(key=lambda x: x["score"], reverse=True)
        resistance_scored.sort(key=lambda x: x["score"], reverse=True)

        return {
            "support": support_scored,
            "resistance": resistance_scored
        }

    # ─── 종합 분석 ───

    def analyze(self, symbol: str, days: int = 120) -> dict:
        """종합 기술적 분석 (AI 제공용)"""
        rows = self.get_daily(symbol, days)
        if not rows:
            return {"error": f"No data for {symbol}"}

        rows.reverse()  # 날짜 오름차순으로 정렬

        # 당일 데이터 실시간 보정 (DB에 오늘 데이터 없으면 네이버 API에서 가져옴)
        rows = self._supplement_today(symbol, rows)

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

        # ─── 고급 분석 계산 ───
        advanced = {}
        try:
            advanced["similar_periods"] = self.calc_similar_periods(rows, closes, rsi, macd)
        except Exception as e:
            advanced["similar_periods"] = {"error": str(e)}
        try:
            advanced["disparity"] = self.calc_disparity(closes)
        except Exception as e:
            advanced["disparity"] = {"error": str(e)}
        try:
            advanced["volume_anomaly"] = self.calc_volume_anomaly(rows)
        except Exception as e:
            advanced["volume_anomaly"] = {"error": str(e)}
        try:
            advanced["support_resistance_strength"] = self.calc_support_resistance_strength(rows, closes, ma)
        except Exception as e:
            advanced["support_resistance_strength"] = {"error": str(e)}

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
            "advanced_analysis": advanced,
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
