"""
🛡️ 3단계: 실시간 주가 + 재무제표 + 뉴스 완전 통합
모든 3개 시스템 연결 완료
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from datetime import datetime

# FastAPI 앱 생성
app = FastAPI(
    title="🎯 기업분석 API - 3개 시스템 완전 통합",
    description="uvicorn 최적화 + 실시간 주가 + 재무제표 + 네이버 뉴스",
    version="5.3.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🛡️ 3개 시스템 안전 로드
STOCK_SYSTEM_READY = False
FINANCIAL_SYSTEM_READY = False
NEWS_SYSTEM_READY = False

NaverRealTimeExtractor = None
get_financial_data = None
collect_company_news = None

# 실시간 주가 시스템 (1단계)
try:
    from enhanced_safe_extractor import NaverRealTimeExtractor
    STOCK_SYSTEM_READY = True
    print("✅ 실시간 주가 시스템 유지!")
except Exception as e:
    print(f"⚠️ 실시간 주가 시스템 오류: {e}")

# 재무제표 시스템 (2단계)
try:
    from enhanced_integrated_financial_system import get_financial_data
    FINANCIAL_SYSTEM_READY = True
    print("✅ 재무제표 시스템 유지!")
except Exception as e:
    print(f"⚠️ 재무제표 시스템 오류: {e}")

# 뉴스 시스템 (3단계 새로 추가)
try:
    print("📰 뉴스 시스템 로드 시도 중...")
    from news_collector import collect_company_news
    NEWS_SYSTEM_READY = True
    print("✅ 뉴스 시스템 로드 성공!")
except Exception as e:
    print(f"⚠️ 뉴스 시스템 로드 실패: {e}")

@app.get("/")
def root():
    total_systems = sum([STOCK_SYSTEM_READY, FINANCIAL_SYSTEM_READY, NEWS_SYSTEM_READY])
    
    return {
        "status": "success",
        "message": "🎉 3개 시스템 완전 통합 완료!",
        "integration_step": "3단계 - 모든 시스템 연결",
        "systems_status": {
            "stock_system": "✅ 연결됨" if STOCK_SYSTEM_READY else "❌ 연결 실패",
            "financial_system": "✅ 연결됨" if FINANCIAL_SYSTEM_READY else "❌ 연결 실패",
            "news_system": "✅ 연결됨" if NEWS_SYSTEM_READY else "❌ 연결 실패"
        },
        "ready_systems": f"{total_systems}/3",
        "available_endpoints": [
            "✅ /stock/{company_name} - 실시간 주가 (8개 항목)" if STOCK_SYSTEM_READY else "❌ 주가 시스템 오류",
            "✅ /financial/{company_name} - 재무제표 (34개 항목)" if FINANCIAL_SYSTEM_READY else "❌ 재무 시스템 오류",
            "✅ /news/{company_name} - 네이버 뉴스" if NEWS_SYSTEM_READY else "❌ 뉴스 시스템 오류",
            "✅ /analyze-company?company_name={name} - 3-in-1 통합" if total_systems == 3 else "❌ 일부 시스템 오류"
        ],
        "total_data_points": "50+ 데이터 항목",
        "ready_for_gpts": total_systems == 3
    }

@app.get("/health")
def health():
    return {
        "status": "excellent",
        "step": "3단계_완전_통합",
        "stock_system": STOCK_SYSTEM_READY,
        "financial_system": FINANCIAL_SYSTEM_READY,
        "news_system": NEWS_SYSTEM_READY
    }

# 🚀 실시간 주가 API (1단계 기능 유지)
@app.get("/stock/{company_name}")
def get_real_time_stock(company_name: str):
    """실시간 주가 분석 API"""
    if not STOCK_SYSTEM_READY:
        raise HTTPException(status_code=503, detail="실시간 주가 시스템 사용 불가")
    
    try:
        stock_codes = {
            "삼성전자": "005930", "SK하이닉스": "000660", "NAVER": "035420",
            "카카오": "035720", "LG전자": "066570", "현대차": "005380",
            "POSCO홀딩스": "005490", "현대모비스": "012330", "LG화학": "051910"
        }
        
        stock_code = stock_codes.get(company_name, "005930")
        extractor = NaverRealTimeExtractor()
        result = extractor.extract_real_time_data(stock_code)
        
        if result.get('extraction_status') == 'success':
            return {
                "success": True,
                "company_name": company_name,
                "data_type": "real_time_stock",
                "timestamp": datetime.now().isoformat(),
                "data": result
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📈 재무제표 API (2단계 기능 유지)
@app.get("/financial/{company_name}")
def get_financial_analysis(company_name: str):
    """재무제표 분석 API"""
    if not FINANCIAL_SYSTEM_READY:
        raise HTTPException(status_code=503, detail="재무제표 시스템 사용 불가")
    
    try:
        result = get_financial_data(company_name)
        
        if result and result.get('metadata', {}).get('success_rate', 0) > 0:
            return {
                "success": True,
                "company_name": company_name,
                "data_type": "financial_analysis",
                "timestamp": datetime.now().isoformat(),
                "data": result
            }
        else:
            raise HTTPException(status_code=404, detail="재무제표 데이터 없음")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📰 뉴스 API (3단계 새로 추가)
@app.get("/news/{company_name}")
def get_company_news(company_name: str):
    """
    📰 기업 뉴스 분석 API (3단계 신규)
    
    **제공 데이터:**
    - 네이버 뉴스 검색 결과
    - 최신순 정렬
    - HTML 태그 제거 및 정제
    - 실시간 수집
    """
    if not NEWS_SYSTEM_READY:
        raise HTTPException(
            status_code=503, 
            detail={
                "error": "뉴스 시스템 사용 불가",
                "api_key": "네이버 API 키 확인 필요"
            }
        )
    
    try:
        print(f"📰 {company_name} 뉴스 분석 시작...")
        
        result = collect_company_news(company_name)
        
        if result.get('status') == 'success':
            return {
                "success": True,
                "company_name": company_name,
                "data_type": "news_analysis",
                "timestamp": datetime.now().isoformat(),
                "data": result,
                "summary": {
                    "총_뉴스_수": result.get('total_count', 0),
                    "API_상태": "정상",
                    "수집_시간": result.get('collection_time')
                }
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "뉴스 수집 실패",
                    "details": result.get('error')
                }
            )
            
    except Exception as e:
        print(f"❌ 뉴스 시스템 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 🎯 3-in-1 완전 통합 API
@app.get("/analyze-company")
def analyze_company_complete(company_name: str):
    """
    🎯 3-in-1 완전 통합 기업분석 API
    
    **한 번의 호출로 모든 분석:**
    - 실시간 주가 (8개 항목)
    - 재무제표 (34개 항목)  
    - 네이버 뉴스
    
    **GPTs Actions 최적화**
    """
    # 시스템 상태 확인
    available_systems = sum([STOCK_SYSTEM_READY, FINANCIAL_SYSTEM_READY, NEWS_SYSTEM_READY])
    
    if available_systems == 0:
        raise HTTPException(status_code=503, detail="모든 시스템 사용 불가")
    
    try:
        result = {
            "success": True,
            "company_name": company_name,
            "analysis_type": "3-in-1 완전 통합",
            "timestamp": datetime.now().isoformat(),
            "data": {},
            "summary": {},
            "available_systems": available_systems,
            "total_systems": 3
        }
        
        # 실시간 주가 (가능시)
        if STOCK_SYSTEM_READY:
            try:
                stock_codes = {"삼성전자": "005930", "SK하이닉스": "000660", "NAVER": "035420", "카카오": "035720"}
                stock_code = stock_codes.get(company_name, "005930")
                extractor = NaverRealTimeExtractor()
                stock_result = extractor.extract_real_time_data(stock_code)
                
                if stock_result.get('extraction_status') == 'success':
                    result["data"]["real_time_stock"] = stock_result
                    rt_data = stock_result.get('real_time_data', {})
                    result["summary"]["current_price"] = rt_data.get('current_price')
                    result["summary"]["change_rate"] = rt_data.get('change_rate')
            except Exception as e:
                result["data"]["real_time_stock"] = {"error": str(e)}
        
        # 재무제표 (가능시)
        if FINANCIAL_SYSTEM_READY:
            try:
                financial_result = get_financial_data(company_name)
                if financial_result and financial_result.get('metadata', {}).get('success_rate', 0) > 0:
                    result["data"]["financial_analysis"] = financial_result
                    fd = financial_result.get('financial_data', {})
                    result["summary"]["revenue"] = fd.get('매출액', [None])[0]
                    result["summary"]["roe"] = fd.get('ROE(%)', [None])[0]
            except Exception as e:
                result["data"]["financial_analysis"] = {"error": str(e)}
        
        # 뉴스 분석 (가능시)
        if NEWS_SYSTEM_READY:
            try:
                news_result = collect_company_news(company_name)
                if news_result.get('status') == 'success':
                    result["data"]["news_analysis"] = news_result
                    result["summary"]["news_count"] = news_result.get('total_count', 0)
            except Exception as e:
                result["data"]["news_analysis"] = {"error": str(e)}
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 🛡️ 3단계 완료 확인
@app.get("/step3-complete")
def step3_complete():
    """3단계 완료 상태 확인"""
    total_systems = sum([STOCK_SYSTEM_READY, FINANCIAL_SYSTEM_READY, NEWS_SYSTEM_READY])
    
    return {
        "step": "3단계 - 완전 통합 완료",
        "systems_ready": f"{total_systems}/3",
        "individual_status": {
            "실시간_주가": "✅ 정상" if STOCK_SYSTEM_READY else "❌ 오류",
            "재무제표": "✅ 정상" if FINANCIAL_SYSTEM_READY else "❌ 오류",
            "네이버_뉴스": "✅ 정상" if NEWS_SYSTEM_READY else "❌ 오류"
        },
        "integration_endpoints": [
            "/stock/삼성전자",
            "/financial/삼성전자", 
            "/news/삼성전자",
            "/analyze-company?company_name=삼성전자"
        ],
        "ready_for_gpts": total_systems == 3,
        "next_step": "GPTs Actions 연결" if total_systems == 3 else "시스템 오류 해결"
    }

if __name__ == "__main__":
    import uvicorn
    total = sum([STOCK_SYSTEM_READY, FINANCIAL_SYSTEM_READY, NEWS_SYSTEM_READY])
    print(f"🎯 3단계: 3개 시스템 완전 통합! ({total}/3)")
    uvicorn.run(app, host="0.0.0.0", port=8000)
