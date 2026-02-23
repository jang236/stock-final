"""
FastAPI 기업분석 서버 - Flask 문제 완전 해결!
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
from typing import Optional

# FastAPI 앱 생성
app = FastAPI(
    title="24시간 기업분석 API",
    description="실시간 주가 + 재무제표 + 뉴스 분석 통합 API",
    version="2.0.0",
    docs_url="/docs",  # 자동 API 문서
    redoc_url="/redoc"  # 대안 문서
)

# 기존 시스템 import 시도
try:
    from company_analyzer import analyze_company_complete
    SYSTEM_READY = True
    print("✅ 기업분석 시스템 로드 완료")
except Exception as e:
    SYSTEM_READY = False
    print(f"⚠️ 기업분석 시스템 로드 실패: {e}")

@app.get("/")
async def root():
    """루트 엔드포인트 - 즉시 응답"""
    return {
        "status": "healthy",
        "api": "FastAPI Company Analysis",
        "version": "2.0.0",
        "system_ready": SYSTEM_READY,
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs",
        "features": [
            "자동 API 문서",
            "타입 안전성",
            "빠른 시작 시간",
            "GPTs Actions 자동 호환"
        ]
    }

@app.get("/health")
async def health_check():
    """헬스체크 - 빠른 응답"""
    return {"status": "ok", "system_ready": SYSTEM_READY}

@app.get("/analyze-company", 
         summary="완전한 기업 분석",
         description="실시간 주가 + 재무제표 + 뉴스 분석을 통합한 종합 기업분석")
async def analyze_company(
    company_name: str = "삼성전자",
    format: Optional[str] = "full"
):
    """
    완전한 기업 분석을 제공합니다.
    
    - **company_name**: 분석할 기업명 (예: 삼성전자, NAVER, SK하이닉스)
    - **format**: 응답 형식 (full: 전체, summary: 요약)
    
    Returns:
        - 실시간 주가 정보 (8개 항목)
        - 재무제표 분석 (33개 재무항목)  
        - 뉴스 분석 (24시간 최신 + 과거 관련)
    """
    try:
        if not SYSTEM_READY:
            return {
                "success": False,
                "company_name": company_name,
                "status": "system_not_ready",
                "message": "분석 시스템 초기화 중입니다",
                "sample_data": True
            }

        print(f"🔍 FastAPI 분석 요청: {company_name}")
        
        # 실제 분석 실행
        result = analyze_company_complete(company_name)
        
        # FastAPI 최적화 응답
        response = {
            "success": True,
            "company_name": company_name,
            "analysis_timestamp": result["analysis_timestamp"],
            "api_version": "FastAPI v2.0",
            "analysis_data": result,
            "gpts_integration": {
                "automatic_docs": "이 API는 /docs에서 자동 문서를 제공합니다",
                "openapi_schema": "GPTs Actions에서 /openapi.json을 사용하세요",
                "type_safety": "모든 파라미터와 응답이 타입 안전합니다"
            }
        }
        
        print(f"✅ FastAPI 분석 완료: {company_name}")
        return response
        
    except Exception as e:
        print(f"❌ FastAPI 분석 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "분석 중 오류가 발생했습니다",
                "company_name": company_name,
                "error_details": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/test")
async def test_api():
    """API 테스트"""
    return {
        "message": "FastAPI 정상 작동! 🚀",
        "system_ready": SYSTEM_READY,
        "advantages": [
            "Flask 문제 완전 해결",
            "자동 API 문서 생성",
            "타입 안전성 확보",
            "빠른 시작 시간",
            "GPTs 즉시 연결"
        ]
    }

if __name__ == "__main__":
    print("🚀 FastAPI 기업분석 서버 시작!")
    print("📋 Flask 대비 개선사항:")
    print("  ✅ 버전 충돌 문제 해결")
    print("  ✅ uvicorn 사용 (gunicorn 대신)")
    print("  ✅ 타입 안전성 확보")
    print("  ✅ 자동 API 문서: http://localhost:8000/docs")
    print("  ✅ GPTs Actions 자동 호환")
    
    uvicorn.run(
        "fastapi_test:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=False
    )
