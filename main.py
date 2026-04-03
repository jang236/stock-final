"""
🚀 5단계: 4-in-1 완전 통합 기업분석 API
실시간 주가 + 재무제표 + 뉴스 + 차트분석 → 한 번의 API 호출로 완전한 기업분석
"""
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import requests as http_requests
import sys
import os
from datetime import datetime, timezone, timedelta

# KST 시간대 설정
KST = timezone(timedelta(hours=9))

def get_kst_now():
    """현재 KST 시간 반환"""
    return datetime.now(KST)
from typing import Optional

# FastAPI 앱 생성 (배포 준비)
app = FastAPI(
    title="🚀 ALL-IN-ONE 기업분석 API",
    description="""
    **완전한 기업분석을 한 번의 API 호출로!**
    
    ## 🎯 혁신적 통합 시스템
    - **실시간 주가**: 8개 핵심 항목 (현재가, 등락률, 거래량 등)
    - **재무제표**: 34개 재무항목 (매출액, 영업이익, ROE 등)
    - **뉴스 분석**: 24시간 최신 + 과거 관련 뉴스
    - **차트 분석**: 기술적 지표 (이동평균, RSI, MACD, 볼린저밴드)
    
    ## 💫 한 번의 API 호출로 완전한 기업분석
    \`/analyze-company?company_name=삼성전자\`
    
    ## 🤖 GPTs Actions 완벽 최적화
    ChatGPT에서 "삼성전자 분석해줘"로 사용 가능
    """,
    version="7.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🛡️ 4개 시스템 안전 로드
STOCK_SYSTEM_READY = False
FINANCIAL_SYSTEM_READY = False
NEWS_SYSTEM_READY = False
CHART_SYSTEM_READY = False
NaverRealTimeExtractor = None
get_financial_data = None
collect_company_news = None
chart_service = None

# 시스템 로드
try:
    from enhanced_safe_extractor import NaverRealTimeExtractor
    STOCK_SYSTEM_READY = True
    print("✅ 실시간 주가 시스템 로드 성공!")
except Exception as e:
    print(f"⚠️ 실시간 주가 시스템 로드 실패: {e}")

try:
    from enhanced_integrated_financial_system import get_financial_data
    FINANCIAL_SYSTEM_READY = True
    print("✅ 재무제표 시스템 로드 성공!")
except Exception as e:
    print(f"⚠️ 재무제표 시스템 로드 실패: {e}")

try:
    from news_collector import collect_company_news
    NEWS_SYSTEM_READY = True
    print("✅ 뉴스 시스템 로드 성공!")
except Exception as e:
    print(f"⚠️ 뉴스 시스템 로드 실패: {e}")

try:
    from chart_service import ChartService
    chart_service = ChartService()
    db_status = chart_service.get_db_status()
    if db_status.get('status') == 'ready' and db_status.get('total_stocks', 0) > 0:
        CHART_SYSTEM_READY = True
        print(f"✅ 차트 분석 시스템 로드 성공! ({db_status['total_stocks']}종목, {db_status['total_rows']:,}행)")
    else:
        print(f"⚠️ 차트 DB가 비어있습니다. chart_collector.py를 먼저 실행하세요.")
except Exception as e:
    print(f"⚠️ 차트 분석 시스템 로드 실패: {e}")

# 일일 자동 업데이트 스케줄러 시작
try:
    from chart_scheduler import start_chart_scheduler
    start_chart_scheduler()
except Exception as e:
    print(f"⚠️ 차트 스케줄러 시작 실패: {e}")

# 재무 URL 자동 수집 스케줄러 시작
try:
    from financial_url_scheduler import start_financial_scheduler
    start_financial_scheduler()
except Exception as e:
    print(f"⚠️ 재무 URL 스케줄러 시작 실패: {e}")

SYSTEM_READY = all([STOCK_SYSTEM_READY, FINANCIAL_SYSTEM_READY, NEWS_SYSTEM_READY])

@app.get("/")
def root():
    return {
        "api": "🚀 ALL-IN-ONE 기업분석 API",
        "status": "ready_for_deployment" if SYSTEM_READY else "partial_ready",
        "version": "7.0.0",
        "integration_level": "완전 통합 (4-in-1)",
        "deployment_step": "5단계 - 차트 분석 통합",
        "systems_status": {
            "stock_system": "✅ 준비완료" if STOCK_SYSTEM_READY else "❌ 확인 필요",
            "financial_system": "✅ 준비완료" if FINANCIAL_SYSTEM_READY else "❌ 확인 필요",
            "news_system": "✅ 준비완료" if NEWS_SYSTEM_READY else "❌ 확인 필요",
            "chart_system": "✅ 준비완료" if CHART_SYSTEM_READY else "❌ 확인 필요"
        },
        "revolutionary_features": [
            "🔥 4-in-1 완전 통합 (한 번의 API 호출)",
            "⚡ 70+ 데이터 항목 제공",
            "🎯 GPTs Actions 완벽 최적화",
            "📊 실시간 주가 8개 항목",
            "📈 재무제표 34개 항목",
            "📰 네이버 뉴스 API 연동",
            "📉 차트 기술적 분석 (MA, RSI, MACD, BB)"
        ],
        "endpoints": {
            "🚀 ultimate": "/analyze-company?company_name=기업명 - 완전 통합 분석",
            "📊 individual": {
                "stock": "/stock/{company_name}",
                "financial": "/financial/{company_name}",
                "news": "/news/{company_name}"
            },
            "📉 chart": {
                "analysis": "/api/chart/{symbol}/analysis",
                "daily": "/api/chart/{symbol}",
                "status": "/api/chart/status"
            }
        },
        "ready_for_gpts": SYSTEM_READY
    }

@app.get("/health")
def health():
    return {
        "status": "excellent",
        "deployment_ready": SYSTEM_READY,
        "integration_step": "4단계_완전_통합",
        "all_systems": "✅ 준비완료" if SYSTEM_READY else "⚠️ 부분 준비"
    }

# 🚀 완전 통합 API - 핵심 기능!
@app.get("/analyze-company")
async def analyze_company_complete(
    company_name: str = Query(..., description="분석할 기업명", example="삼성전자"),
    format: Optional[str] = Query("full", description="응답 형식", enum=["full", "summary", "gpts"])
):
    """
    🚀 **완전 통합 기업분석 API (ALL-IN-ONE)**
    
    ### 🎯 혁신적 통합 분석
    한 번의 API 호출로 다음을 모두 제공:
    - **실시간 주가 분석** (8개 핵심 항목)
    - **재무제표 분석** (34개 재무항목)
    - **뉴스 분석** (24시간 + 과거 이슈)
    
    ### 📊 총 50+ 데이터 항목
    완전한 기업 분석에 필요한 모든 정보
    
    ### 🤖 GPTs 완벽 최적화
    ChatGPT에서 "삼성전자 분석해줘"로 사용 가능
    """
    if not SYSTEM_READY:
        missing_systems = []
        if not STOCK_SYSTEM_READY:
            missing_systems.append("실시간 주가")
        if not FINANCIAL_SYSTEM_READY:
            missing_systems.append("재무제표")
        if not NEWS_SYSTEM_READY:
            missing_systems.append("뉴스")
        
        raise HTTPException(
            status_code=503,
            detail={
                "error": "시스템 준비 미완료",
                "missing_systems": missing_systems,
                "suggestion": "모든 시스템 파일을 확인하세요"
            }
        )
    
    try:
        print(f"🚀 {company_name} 완전 통합 분석 시작...")
        analysis_start = get_kst_now()
        
        # 종목코드 자동 추출 (다단계 검색)
        stock_code = None
        
        # 1단계: 차트 DB에서 정확한 종목명 검색 (가장 신뢰도 높음)
        if CHART_SYSTEM_READY and chart_service:
            try:
                search_results = chart_service.search_stocks(company_name)
                for r in search_results:
                    if r.get('name') == company_name:
                        stock_code = r.get('symbol')
                        print(f"✅ 차트DB 정확 매칭: {company_name} → {stock_code}")
                        break
                if not stock_code and search_results:
                    stock_code = search_results[0].get('symbol')
                    print(f"✅ 차트DB 부분 매칭: {company_name} → {stock_code} ({search_results[0].get('name')})")
            except Exception as e:
                print(f"⚠️ 차트DB 검색 실패: {e}")
        
        # 2단계: stock_companies.json 직접 검색
        if not stock_code:
            try:
                import json
                companies_path = os.path.join(os.path.dirname(__file__), 'company_codes_active', 'stock_companies.json')
                if not os.path.exists(companies_path):
                    companies_path = os.path.join(os.path.dirname(__file__), 'company_codes_b', 'stock_companies.json')
                if os.path.exists(companies_path):
                    with open(companies_path, 'r', encoding='utf-8') as f:
                        companies_json = json.load(f)
                    if company_name in companies_json:
                        stock_code = companies_json[company_name].get('code', '')
                        print(f"✅ JSON 매칭: {company_name} → {stock_code}")
                    else:
                        for name, info in companies_json.items():
                            if company_name in name or name in company_name:
                                stock_code = info.get('code', '')
                                print(f"✅ JSON 부분 매칭: {company_name} → {stock_code} ({name})")
                                break
            except Exception as e:
                print(f"⚠️ JSON 검색 실패: {e}")
        
        # 3단계: 최종 fallback — 절대 기본값 사용 금지, 에러 반환
        if not stock_code:
            raise HTTPException(
                status_code=404,
                detail={"error": f"'{company_name}' 종목을 찾을 수 없습니다.", "suggestion": "정확한 종목명을 입력해주세요 (예: 삼성전자, 현대차, SK하이닉스)"}
            )
        
        print(f"🎯 최종 종목코드: {company_name} → {stock_code}")
        
        # 차트 이미지 URL 생성 (네이버 CDN 직접 사용 — ChatGPT 렌더링 호환성)
        naver_chart_url = f"https://ssl.pstatic.net/imgfinance/chart/item/candle/day/{stock_code}.png"
        proxy_chart_url = f"https://jaemubunseoggi-2.replit.app/chart/{stock_code}.png"
        chart_markdown = f"![{company_name} 일봉차트]({naver_chart_url})"

        # 결과 컨테이너
        complete_analysis = {
            "success": True,
            "company_name": company_name,
            "stock_code": stock_code,
            "⚠️_DISPLAY_FIRST": chart_markdown,
            "chart_url": naver_chart_url,
            "chart_proxy_url": proxy_chart_url,
            "chart_markdown": chart_markdown,
            "chart_search_query": f"KRX:{stock_code}",
            "analysis_type": "완전 통합 분석 (ALL-IN-ONE)",
            "timestamp": analysis_start.isoformat(),
            "data": {},
            "summary": {},
            "api_version": "8.0.0"
        }
        
        success_count = 0
        errors = {}
        
        # 1. 실시간 주가 분석
        try:
            print(f"  📊 실시간 주가 분석 중...")
            extractor = NaverRealTimeExtractor()
            stock_result = extractor.extract_real_time_data(stock_code)
            
            if stock_result.get('extraction_status') == 'success':
                complete_analysis["data"]["real_time_stock"] = stock_result
                success_count += 1
                
                # 주가 핵심 지표 요약
                rt_data = stock_result.get('real_time_data', {})
                complete_analysis["summary"]["current_price"] = rt_data.get('current_price')
                complete_analysis["summary"]["change_rate"] = rt_data.get('change_rate')
                complete_analysis["summary"]["volume"] = rt_data.get('volume')
                complete_analysis["summary"]["market_cap"] = rt_data.get('market_cap')
                
                print(f"  ✅ 실시간 주가 분석 완료")
            else:
                errors["stock"] = stock_result.get('error', '추출 실패')
                
        except Exception as e:
            errors["stock"] = str(e)
            print(f"  ❌ 실시간 주가 분석 실패: {e}")
        
        # 2. 재무제표 분석
        try:
            print(f"  📈 재무제표 분석 중...")
            financial_result = get_financial_data(company_name)
            
            success_rate = financial_result.get('metadata', {}).get('success_rate', 0)
            if success_rate > 0:
                complete_analysis["data"]["financial_analysis"] = financial_result
                success_count += 1
                
                # 재무 핵심 지표 요약
                fd = financial_result.get('financial_data', {})
                complete_analysis["summary"]["revenue"] = fd.get('매출액', [None])[0] if fd.get('매출액') else None
                complete_analysis["summary"]["operating_profit"] = fd.get('영업이익', [None])[0] if fd.get('영업이익') else None
                complete_analysis["summary"]["roe"] = fd.get('ROE(%)', [None])[0] if fd.get('ROE(%)') else None
                
                print(f"  ✅ 재무제표 분석 완료")
            else:
                errors["financial"] = "재무데이터 추출 실패"
                
        except Exception as e:
            errors["financial"] = str(e)
            print(f"  ❌ 재무제표 분석 실패: {e}")
        
        # 3. 뉴스 분석
        try:
            print(f"  📰 뉴스 분석 중...")
            news_result = collect_company_news(company_name)
            
            if news_result.get('status') == 'success':
                complete_analysis["data"]["news_analysis"] = news_result
                success_count += 1
                
                # 뉴스 핵심 지표 요약
                complete_analysis["summary"]["news_count"] = news_result.get('news_count', 0)
                
                print(f"  ✅ 뉴스 분석 완료")
            else:
                errors["news"] = news_result.get('error', '뉴스 추출 실패')
                
        except Exception as e:
            errors["news"] = str(e)
            print(f"  ❌ 뉴스 분석 실패: {e}")
        
        # 4. 차트 기술적 분석
        if CHART_SYSTEM_READY and chart_service:
            try:
                print(f"  📉 차트 기술적 분석 중...")
                chart_result = chart_service.analyze(stock_code)
                if "error" not in chart_result:
                    complete_analysis["data"]["chart_analysis"] = chart_result
                    success_count += 1
                    # 차트 핵심 지표 요약
                    ca = chart_result.get("analysis", {})
                    complete_analysis["summary"]["trend"] = ca.get("trend")
                    complete_analysis["summary"]["rsi"] = ca.get("rsi")
                    complete_analysis["summary"]["rsi_signal"] = ca.get("rsi_signal")
                    complete_analysis["summary"]["ma_alignment"] = ca.get("ma_alignment")
                    complete_analysis["summary"]["cross"] = ca.get("cross")
                    complete_analysis["summary"]["volume_trend"] = ca.get("volume_trend")
                    print(f"  ✅ 차트 기술적 분석 완료")
                else:
                    errors["chart"] = chart_result["error"]
            except Exception as e:
                errors["chart"] = str(e)
                print(f"  ❌ 차트 분석 실패: {e}")
        
        # 분석 완료 처리
        total_systems = 4 if CHART_SYSTEM_READY else 3
        analysis_end = get_kst_now()
        analysis_duration = (analysis_end - analysis_start).total_seconds()
        
        # 메타데이터
        complete_analysis["metadata"] = {
            "analysis_duration_seconds": round(analysis_duration, 2),
            "success_systems": success_count,
            "total_systems": total_systems,
            "success_rate": round(success_count / total_systems, 2),
            "analysis_completed_at": analysis_end.isoformat(),
            "errors": errors if errors else None,
            "integration_level": "완전 통합 (4-in-1)" if CHART_SYSTEM_READY else "완전 통합 (3-in-1)",
            "data_quality": "premium" if success_count >= 3 else "partial"
        }
        
        # 응답 형식 처리
        if format == "summary":
            return {
                "success": True,
                "company_name": company_name,
                "analysis_type": "완전 통합 요약",
                "summary": complete_analysis["summary"],
                "metadata": complete_analysis["metadata"]
            }
        elif format == "gpts":
            # GPTs 전용 최적화 형식
            return {
                "success": True,
                "company_name": company_name,
                "analysis_type": "GPTs 최적화 통합분석",
                "summary": complete_analysis["summary"],
                "gpts_guide": {
                    "usage": "이 데이터로 종합적인 기업분석 리포트를 작성할 수 있습니다",
                    "analysis_approach": [
                        "현재 주가 상황 및 시장 반응 분석",
                        "재무 성과 및 건전성 평가", 
                        "최근 뉴스 이슈 및 시장 영향 분석",
                        "종합 투자 의견 및 리스크 요인 제시"
                    ]
                },
                "metadata": complete_analysis["metadata"]
            }
        else:
            # 전체 형식
            return complete_analysis
            
    except Exception as e:
        print(f"❌ {company_name} 완전 통합 분석 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "완전 통합 분석 중 오류 발생",
                "company_name": company_name,
                "error_details": str(e)
            }
        )

# 기존 개별 API들 (실제 구현)
@app.get("/stock/{company_name}")
def get_real_time_stock(company_name: str):
    """실시간 주가 분석 API"""
    if not STOCK_SYSTEM_READY:
        raise HTTPException(status_code=503, detail="주가 시스템 미준비")
    try:
        # 종목코드 조회
        stock_code = _resolve_stock_code(company_name)
        if not stock_code:
            raise HTTPException(status_code=404, detail=f"'{company_name}' 종목을 찾을 수 없습니다")
        extractor = NaverRealTimeExtractor()
        result = extractor.extract_real_time_data(stock_code)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/financial/{company_name}")
def get_financial_analysis(company_name: str):
    """재무제표 분석 API"""
    if not FINANCIAL_SYSTEM_READY:
        raise HTTPException(status_code=503, detail="재무 시스템 미준비")
    try:
        result = get_financial_data(company_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/news/{company_name}")
def get_news_analysis(company_name: str):
    """뉴스 분석 API"""
    if not NEWS_SYSTEM_READY:
        raise HTTPException(status_code=503, detail="뉴스 시스템 미준비")
    try:
        result = collect_company_news(company_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _resolve_stock_code(company_name: str) -> str:
    """회사명 → 종목코드 변환 (공용 헬퍼)"""
    # 1. 차트 DB 검색
    if CHART_SYSTEM_READY and chart_service:
        try:
            results = chart_service.search_stocks(company_name)
            for r in results:
                if r.get('name') == company_name:
                    return r.get('symbol')
            if results:
                return results[0].get('symbol')
        except:
            pass
    # 2. stock_companies.json
    try:
        import json
        for folder in ['company_codes_active', 'company_codes_b', 'company_codes_a']:
            path = os.path.join(os.path.dirname(__file__), folder, 'stock_companies.json')
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if company_name in data:
                    return data[company_name].get('code', '')
                for name, info in data.items():
                    if company_name in name or name in company_name:
                        return info.get('code', '')
                break
    except:
        pass
    return None

# 📉 차트 분석 API 엔드포인트
@app.get("/api/chart/status")
def chart_db_status():
    """차트 DB 현황 조회"""
    if not CHART_SYSTEM_READY:
        return {"status": "not_ready", "message": "차트 DB가 초기화되지 않았습니다"}
    return chart_service.get_db_status()

@app.get("/api/chart/search")
def chart_search(q: str = Query(..., description="종목명 검색")):
    """종목명으로 차트 데이터 검색"""
    if not CHART_SYSTEM_READY:
        raise HTTPException(status_code=503, detail="차트 시스템 미준비")
    results = chart_service.search_stocks(q)
    return {"query": q, "results": results, "count": len(results)}

@app.get("/api/chart/{symbol}")
def chart_daily(symbol: str, days: int = Query(60, description="조회 일수")):
    """종목코드로 일봉 데이터 조회"""
    if not CHART_SYSTEM_READY:
        raise HTTPException(status_code=503, detail="차트 시스템 미준비")
    data = chart_service.get_daily(symbol, days)
    if not data:
        raise HTTPException(status_code=404, detail=f"{symbol} 차트 데이터 없음")
    return {"symbol": symbol, "days": days, "count": len(data), "data": data}

@app.get("/api/chart/{symbol}/analysis")
def chart_analysis(symbol: str):
    """종목 기술적 분석 (이동평균, RSI, MACD, 볼린저밴드, 골든크로스/데드크로스)"""
    if not CHART_SYSTEM_READY:
        raise HTTPException(status_code=503, detail="차트 시스템 미준비")
    result = chart_service.analyze(symbol)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/api/chart/{symbol}/weekly")
def chart_weekly(symbol: str, weeks: int = Query(52, description="조회 주수")):
    """주봉 데이터 조회"""
    if not CHART_SYSTEM_READY:
        raise HTTPException(status_code=503, detail="차트 시스템 미준비")
    data = chart_service.get_weekly(symbol, weeks)
    if not data:
        raise HTTPException(status_code=404, detail=f"{symbol} 주봉 데이터 없음")
    return {"symbol": symbol, "weeks": weeks, "count": len(data), "data": data}

# 🕐 시간 확인 엔드포인트
@app.get("/check-time")
def check_time():
    """현재 서버 시간 확인"""
    import datetime as dt
    utc_now = dt.datetime.now(dt.timezone.utc)
    kst_now = get_kst_now()
    return {
        "time_check": {
            "kst_time": kst_now.isoformat(),
            "kst_readable": kst_now.strftime("%Y년 %m월 %d일 %H시 %M분"),
            "utc_time": utc_now.isoformat(),
            "timezone": "Asia/Seoul (KST +09:00)"
        },
        "current_kst": {
            "date": kst_now.strftime("%Y-%m-%d"),
            "time": kst_now.strftime("%H:%M:%S"),
            "weekday": kst_now.strftime("%A")
        }
    }

# 📊 차트 이미지 프록시 (네이버 일봉 차트)
@app.get("/chart/{symbol}.png")
def chart_image_proxy(symbol: str):
    """네이버 증권 일봉 캔들차트 이미지 프록시"""
    try:
        naver_url = f"https://ssl.pstatic.net/imgfinance/chart/item/candle/day/{symbol}.png"
        resp = http_requests.get(naver_url, timeout=10, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://finance.naver.com/"
        })
        if resp.status_code == 200:
            return Response(
                content=resp.content,
                media_type="image/png",
                headers={
                    "Cache-Control": "public, max-age=300",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                    "Content-Disposition": f"inline; filename={symbol}.png",
                    "X-Content-Type-Options": "nosniff"
                }
            )
        raise HTTPException(status_code=404, detail=f"차트 이미지 없음: {symbol}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"차트 이미지 조회 실패: {str(e)}")

# 참고: /health 엔드포인트는 150번줄에 이미 정의됨 (중복 제거)

if __name__ == "__main__":
    import uvicorn
    print("🚀 5단계: 4-in-1 완전 통합 (차트 분석 포함)!")
    print(f"✅ 시스템 준비: {SYSTEM_READY}")
    print(f"📉 차트 시스템: {'✅' if CHART_SYSTEM_READY else '❌'}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
