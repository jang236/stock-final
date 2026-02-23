"""
🧪 단계적 테스트용 API (Reserved VM 배포 검증)
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import sys
import os

# 간단한 FastAPI 앱
app = FastAPI(
    title="🧪 기업분석 API - 테스트 버전",
    description="Replit Reserved VM 배포 테스트",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    """루트 엔드포인트 - 기본 상태 확인"""
    return {
        "status": "healthy",
        "message": "🧪 Replit Reserved VM 테스트 성공!",
        "python_version": sys.version,
        "timestamp": datetime.now().isoformat(),
        "environment": "Replit Reserved VM",
        "test_phase": "기본 FastAPI 서버 정상 작동",
        "next_steps": [
            "1. 기본 서버 배포 성공 확인",
            "2. 실시간 주가 시스템 추가",
            "3. 재무제표 시스템 추가", 
            "4. 뉴스 시스템 추가",
            "5. 3개 시스템 완전 통합"
        ]
    }

@app.get("/health")
def health_check():
    """헬스체크"""
    return {
        "status": "excellent", 
        "deployment": "Reserved VM",
        "python": sys.version,
        "fastapi": "0.104.1",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test-import")
def test_imports():
    """시스템 라이브러리 테스트"""
    results = {}
    
    # 기본 라이브러리들 테스트
    try:
        import requests
        results["requests"] = "✅ 정상"
    except Exception as e:
        results["requests"] = f"❌ {str(e)}"
    
    try:
        import beautifulsoup4
        results["beautifulsoup4"] = "✅ 정상"
    except Exception as e:
        results["beautifulsoup4"] = f"❌ {str(e)}"
    
    try:
        from bs4 import BeautifulSoup
        results["bs4"] = "✅ 정상"
    except Exception as e:
        results["bs4"] = f"❌ {str(e)}"
    
    # 기존 시스템 파일 확인
    try:
        if os.path.exists("enhanced_safe_extractor.py"):
            results["stock_system"] = "✅ 파일 존재"
        else:
            results["stock_system"] = "❌ 파일 없음"
    except Exception as e:
        results["stock_system"] = f"❌ {str(e)}"
    
    try:
        if os.path.exists("enhanced_integrated_financial_system.py"):
            results["financial_system"] = "✅ 파일 존재"
        else:
            results["financial_system"] = "❌ 파일 없음"
    except Exception as e:
        results["financial_system"] = f"❌ {str(e)}"
    
    return {
        "test_results": results,
        "timestamp": datetime.now().isoformat(),
        "ready_for_integration": all("✅" in v for v in results.values())
    }

if __name__ == "__main__":
    print("🧪 테스트용 API 서버 시작!")
    print(f"Python 버전: {sys.version}")
    print("Reserved VM 배포 테스트 중...")
    
    import uvicorn
    uvicorn.run(
        "main_test:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        access_log=True
    )
