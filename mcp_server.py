"""MCP 서버 — stock-final의 재무분석 기능을 MCP 도구로 노출.

5개 도구 블랙박스 공개:
  - analyze_company      : 4-in-1 완전 통합 분석 (주가+재무+뉴스+차트)
  - get_stock_price      : 실시간 주가 + 8개 핵심 항목
  - get_financial_data   : 재무제표 34개 항목
  - get_company_news     : 기업 뉴스
  - get_chart_analysis   : 차트 기술적 분석 (MA/RSI/MACD/BB)

구현: async httpx로 로컬 FastAPI 호출 (동기 requests는 이벤트 루프 블로킹 이슈로 제외).
"""
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

# ─────────────────────────────────────────────
# DNS rebinding 보호 비활성화 (Replit 원격 호스트 허용)
# ─────────────────────────────────────────────
_transport_security = None
_candidate_imports = [
    "mcp.server.transport_security",
    "mcp.server.fastmcp.utilities.transport_security",
    "mcp.server.fastmcp.transport_security",
    "mcp.server.auth.transport_security",
]
for _modpath in _candidate_imports:
    try:
        _mod = __import__(_modpath, fromlist=["TransportSecuritySettings"])
        _TSS = getattr(_mod, "TransportSecuritySettings", None)
        if _TSS:
            _transport_security = _TSS(enable_dns_rebinding_protection=False)
            break
    except (ImportError, AttributeError, TypeError):
        continue

if _transport_security is not None:
    mcp = FastMCP("stock-final", transport_security=_transport_security)
else:
    mcp = FastMCP("stock-final")
    for _attr in ("_settings", "settings"):
        _s = getattr(mcp, _attr, None)
        if _s is not None and hasattr(_s, "transport_security"):
            try:
                _s.transport_security.enable_dns_rebinding_protection = False
            except AttributeError:
                pass

# ─────────────────────────────────────────────
# 비동기 로컬 HTTP 호출 (동일 프로세스 FastAPI)
# ─────────────────────────────────────────────
LOCAL_BASE = "http://localhost:8000"
DEFAULT_TIMEOUT = 45.0  # Naver 스크래핑 최대 30초 + 여유


async def _call_local(
    path: str,
    params: Optional[dict] = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict:
    """비동기 로컬 FastAPI 호출. 실패 시 error dict 반환."""
    try:
        async with httpx.AsyncClient(
            base_url=LOCAL_BASE, timeout=timeout
        ) as client:
            resp = await client.get(path, params=params or {})
            if resp.status_code == 200:
                return resp.json()
            return {
                "error": f"HTTP {resp.status_code}",
                "detail": resp.text[:400] if resp.text else "",
            }
    except httpx.TimeoutException:
        return {"error": "timeout", "detail": f"응답 지연 ({timeout}s 초과)"}
    except Exception as e:
        return {"error": f"{type(e).__name__}", "detail": str(e)[:200]}


# ─────────────────────────────────────────────
# Tool 1. analyze_company — 4-in-1 통합
# ─────────────────────────────────────────────
@mcp.tool()
async def analyze_company(
    company_name: str,
    format: str = "full",
) -> dict:
    """한 번의 호출로 기업의 실시간 주가·재무제표·뉴스·차트를 통합 분석합니다.

    Args:
        company_name: 기업명 (한글/영어 지원). 예: "삼성전자", "SK하이닉스", "NAVER".
        format: "full" (전체), "summary" (요약), "gpts" (GPTs 최적화).

    Returns:
        통합 분석 결과 (주가 8항목 + 재무 34항목 + 뉴스 + 차트 분석).
    """
    return await _call_local(
        "/analyze-company",
        {"company_name": company_name, "format": format},
    )


# ─────────────────────────────────────────────
# Tool 2. get_stock_price
# ─────────────────────────────────────────────
@mcp.tool()
async def get_stock_price(company_name: str) -> dict:
    """기업의 실시간 주가와 관련 지표 8가지를 조회합니다.

    Args:
        company_name: 기업명.

    Returns:
        현재가, 전일비, 등락률, 거래량, 거래대금, 시가총액, 외국인지분율 등.
    """
    return await _call_local(f"/stock/{company_name}", timeout=20.0)


# ─────────────────────────────────────────────
# Tool 3. get_financial_data
# ─────────────────────────────────────────────
@mcp.tool()
async def get_financial_data(company_name: str) -> dict:
    """기업의 재무제표 34개 핵심 항목을 최근 4년치 조회합니다.

    Args:
        company_name: 기업명.

    Returns:
        매출액, 영업이익, 순이익, ROE, PER, PBR, EPS, BPS 등 34개 항목.
    """
    return await _call_local(f"/financial/{company_name}")


# ─────────────────────────────────────────────
# Tool 4. get_company_news
# ─────────────────────────────────────────────
@mcp.tool()
async def get_company_news(company_name: str) -> dict:
    """기업 관련 뉴스를 네이버 뉴스 API 기반으로 조회합니다.

    Args:
        company_name: 기업명.

    Returns:
        최신 24시간 + 관련 과거 뉴스 목록.
    """
    return await _call_local(f"/news/{company_name}", timeout=20.0)


# ─────────────────────────────────────────────
# Tool 5. get_chart_analysis
# ─────────────────────────────────────────────
@mcp.tool()
async def get_chart_analysis(symbol: str) -> dict:
    """종목의 차트 기술적 분석 (MA, RSI, MACD, 볼린저밴드).

    Args:
        symbol: 종목 코드 (6자리). 예: "005930" (삼성전자), "000660" (SK하이닉스).

    Returns:
        이동평균선, RSI, MACD, 볼린저밴드 등 기술적 지표.
    """
    return await _call_local(f"/api/chart/{symbol}/analysis", timeout=20.0)
