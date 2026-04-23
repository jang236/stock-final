"""MCP 서버 — stock-final의 재무분석 기능을 MCP 도구로 노출.

5개 도구 블랙박스 공개:
  - analyze_company      : 4-in-1 완전 통합 분석 (주가+재무+뉴스+차트)
  - get_stock_price      : 실시간 주가 + 8개 핵심 항목
  - get_financial_data   : 재무제표 34개 항목
  - get_company_news     : 기업 뉴스
  - get_chart_analysis   : 차트 기술적 분석 (MA/RSI/MACD/BB)

구현 방식:
- HTTP localhost 호출 대신 main.py의 async 엔드포인트 함수를 직접 import 호출.
- Replit Autoscale의 localhost 라우팅 불확실성 회피.
- 이벤트 루프 공유 (async 네이티브).
"""
from typing import Optional
import json
import asyncio

from fastapi import HTTPException
from fastapi.responses import Response
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
# main.py 함수 직접 호출 헬퍼
# (Lazy import로 순환 참조 회피: main.py는 import 시 mcp_server를 로드함)
# ─────────────────────────────────────────────
def _unwrap(result):
    """FastAPI endpoint 함수의 반환값을 dict로 정규화.

    - 이미 dict면 그대로
    - fastapi.Response 면 body JSON 파싱
    - 기타는 그대로 반환
    """
    if isinstance(result, dict):
        return result
    if isinstance(result, Response):
        body = getattr(result, "body", b"")
        if isinstance(body, (bytes, bytearray)) and body:
            try:
                return json.loads(body)
            except Exception:
                return {"raw": body.decode("utf-8", errors="replace")[:4000]}
    return result


async def _invoke(func_name: str, *args, **kwargs) -> dict:
    """main 모듈의 엔드포인트 함수 직접 호출.

    - async 함수: await
    - sync 함수: asyncio.to_thread (이벤트 루프 블로킹 방지)
    """
    try:
        import main as _main  # lazy: 순환 회피
        func = getattr(_main, func_name, None)
        if func is None:
            return {"error": "function_not_found", "name": func_name}
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            # sync 함수는 스레드풀에서 실행 (Naver 스크래핑 블로킹 I/O 안전 처리)
            result = await asyncio.to_thread(func, *args, **kwargs)
        return _unwrap(result)
    except HTTPException as he:
        return {
            "error": f"http_{he.status_code}",
            "detail": he.detail if isinstance(he.detail, (dict, list, str)) else str(he.detail),
        }
    except Exception as e:
        return {"error": f"{type(e).__name__}", "detail": str(e)[:300]}


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
        company_name: 기업명 (한글/영어 지원).
        format: "full" | "summary" | "gpts".
    """
    return await _invoke(
        "analyze_company_complete",
        company_name=company_name,
        format=format,
    )


# ─────────────────────────────────────────────
# Tool 2. get_stock_price
# ─────────────────────────────────────────────
@mcp.tool()
async def get_stock_price(company_name: str) -> dict:
    """기업의 실시간 주가와 관련 지표 8가지를 조회합니다."""
    return await _invoke("get_real_time_stock", company_name=company_name)


# ─────────────────────────────────────────────
# Tool 3. get_financial_data
# ─────────────────────────────────────────────
@mcp.tool()
async def get_financial_data(company_name: str) -> dict:
    """기업의 재무제표 34개 핵심 항목을 최근 4년치 조회합니다."""
    return await _invoke("get_financial_analysis", company_name=company_name)


# ─────────────────────────────────────────────
# Tool 4. get_company_news
# ─────────────────────────────────────────────
@mcp.tool()
async def get_company_news(company_name: str) -> dict:
    """기업 관련 뉴스를 네이버 뉴스 API 기반으로 조회합니다."""
    return await _invoke("get_news_analysis", company_name=company_name)


# ─────────────────────────────────────────────
# Tool 5. get_chart_analysis
# ─────────────────────────────────────────────
@mcp.tool()
async def get_chart_analysis(symbol: str) -> dict:
    """종목의 차트 기술적 분석 (MA, RSI, MACD, 볼린저밴드).

    Args:
        symbol: 종목 코드 (6자리). 예: "005930" (삼성전자).
    """
    return await _invoke("chart_analysis", symbol=symbol)
