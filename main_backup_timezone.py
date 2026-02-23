"""
🚀 4단계: 3-in-1 완전 통합 기업분석 API
실시간 주가 + 재무제표 + 뉴스 → 한 번의 API 호출로 완전한 기업분석
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from datetime import datetime
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
    
    ## 💫 한 번의 API 호출로 완전한 기업분석
    `/analyze-company?company_name=삼성전자`
    
    ## 🤖 GPTs Actions 완벽 최적화
    ChatGPT에서 "삼성전자 분석해줘"로 사용 가능
    """,
    version="6.0.0"
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

SYSTEM_READY = all([STOCK_SYSTEM_READY, FINANCIAL_SYSTEM_READY, NEWS_SYSTEM_READY])

@app.get("/")
def root():
    return {
        "api": "🚀 ALL-IN-ONE 기업분석 API",
        "status": "ready_for_deployment" if SYSTEM_READY else "partial_ready",
        "version": "6.0.0",
        "integration_level": "완전 통합 (3-in-1)",
        "deployment_step": "4단계 - 첫 배포 준비",
        "systems_status": {
            "stock_system": "✅ 준비완료" if STOCK_SYSTEM_READY else "❌ 확인 필요",
            "financial_system": "✅ 준비완료" if FINANCIAL_SYSTEM_READY else "❌ 확인 필요",
            "news_system": "✅ 준비완료" if NEWS_SYSTEM_READY else "❌ 확인 필요"
        },
        "revolutionary_features": [
            "🔥 3-in-1 완전 통합 (한 번의 API 호출)",
            "⚡ 50+ 데이터 항목 제공",
            "🎯 GPTs Actions 완벽 최적화",
            "📊 실시간 주가 8개 항목",
            "📈 재무제표 34개 항목",
            "📰 네이버 뉴스 API 연동"
        ],
        "endpoints": {
            "🚀 ultimate": "/analyze-company?company_name=기업명 - 완전 통합 분석",
            "📊 individual": {
                "stock": "/stock/{company_name}",
                "financial": "/financial/{company_name}",
                "news": "/news/{company_name}"
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
        analysis_start = datetime.now()
        
        # 종목코드 매핑
        stock_codes = {
            "삼성전자": "005930", "SK하이닉스": "000660", "NAVER": "035420",
            "카카오": "035720", "LG전자": "066570", "현대차": "005380",
            "POSCO홀딩스": "005490", "현대모비스": "012330", "LG화학": "051910",
            "삼성바이오로직스": "207940", "KB금융": "105560", "신한지주": "055550"
        }
        stock_code = stock_codes.get(company_name, "005930")
        
        # 결과 컨테이너
        complete_analysis = {
            "success": True,
            "company_name": company_name,
            "stock_code": stock_code,
            "analysis_type": "완전 통합 분석 (ALL-IN-ONE)",
            "timestamp": analysis_start.isoformat(),
            "data": {},
            "summary": {},
            "api_version": "6.0.0"
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
        
        # 분석 완료 처리
        analysis_end = datetime.now()
        analysis_duration = (analysis_end - analysis_start).total_seconds()
        
        # 메타데이터
        complete_analysis["metadata"] = {
            "analysis_duration_seconds": round(analysis_duration, 2),
            "success_systems": success_count,
            "total_systems": 3,
            "success_rate": success_count / 3,
            "analysis_completed_at": analysis_end.isoformat(),
            "errors": errors if errors else None,
            "integration_level": "완전 통합 (ALL-IN-ONE)",
            "data_quality": "premium" if success_count >= 2 else "partial"
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

# 기존 개별 API들 (유지)
@app.get("/stock/{company_name}")
def get_real_time_stock(company_name: str):
    """실시간 주가 분석 API"""
    # ... (기존 코드 유지)
    pass

@app.get("/financial/{company_name}")
def get_financial_analysis(company_name: str):
    """재무제표 분석 API"""
    # ... (기존 코드 유지)
    pass

@app.get("/news/{company_name}")
def get_news_analysis(company_name: str):
    """뉴스 분석 API"""
    # ... (기존 코드 유지)
    pass

# 🧪 4단계 통합 테스트
@app.get("/test-step4")
def test_step4():
    """4단계 통합 테스트"""
    return {
        "step4_test": "3-in-1 완전 통합",
        "integration_complete": SYSTEM_READY,
        "ultimate_endpoint": "/analyze-company?company_name=삼성전자",
        "deployment_ready": SYSTEM_READY,
        "gpts_ready": SYSTEM_READY,
        "next_action": "🚀 Deploy 버튼 클릭 (첫 배포)!" if SYSTEM_READY else "시스템 확인 필요"
    }

# 🚀 배포 준비 상태
@app.get("/deployment-ready")
def deployment_ready():
    """배포 준비 상태 확인"""
    return {
        "deployment_status": "✅ 준비완료" if SYSTEM_READY else "❌ 준비 미완료",
        "integration_complete": SYSTEM_READY,
        "api_endpoints": {
            "main": "/analyze-company?company_name=삼성전자",
            "docs": "/docs",
            "health": "/health"
        },
        "deployment_action": "🚀 Deploy 버튼을 클릭하여 첫 배포를 시작하세요!" if SYSTEM_READY else "시스템 확인 후 배포하세요",
        "post_deployment": "배포 성공 후 → 5단계 GPTs Actions 연결"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 4단계: 3-in-1 완전 통합 + 첫 배포 준비!")
    print(f"✅ 시스템 준비: {SYSTEM_READY}")
    if SYSTEM_READY:
        print("🎉 완전 통합 API 준비완료!")
        print("🚀 Deploy 버튼을 클릭하여 첫 배포를 시작하세요!")
        print("🧪 테스트: /analyze-company?company_name=삼성전자")
    else:
        print("⚠️ 시스템 확인 필요")
    uvicorn.run(app, host="0.0.0.0", port=8000)
