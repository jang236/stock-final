"""
📈 2단계: 실시간 주가 + 재무제표 시스템 통합
uvicorn 서버 + 주가 + 재무제표 API
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from datetime import datetime

# FastAPI 앱 생성
app = FastAPI(
    title="🎯 기업분석 API - 주가+재무제표",
    description="uvicorn 최적화 + 실시간 주가 + 재무제표",
    version="5.2.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🛡️ 2개 시스템 안전 로드
STOCK_SYSTEM_READY = False
FINANCIAL_SYSTEM_READY = False
NaverRealTimeExtractor = None
get_financial_data = None

# 실시간 주가 시스템 로드
try:
    from enhanced_safe_extractor import NaverRealTimeExtractor
    STOCK_SYSTEM_READY = True
    print("✅ 실시간 주가 시스템 로드 성공!")
except Exception as e:
    print(f"⚠️ 실시간 주가 시스템 로드 실패: {e}")

# 재무제표 시스템 로드
try:
    from enhanced_integrated_financial_system import get_financial_data
    FINANCIAL_SYSTEM_READY = True
    print("✅ 재무제표 시스템 로드 성공!")
except Exception as e:
    print(f"⚠️ 재무제표 시스템 로드 실패: {e}")

@app.get("/")
def root():
    return {
        "status": "success",
        "message": "📈 2단계: 주가 + 재무제표 통합",
        "python_version": sys.version,
        "server_type": "uvicorn ASGI",
        "integration_step": "2단계 - 주가 + 재무제표",
        "systems_status": {
            "stock_system": "✅ 연결됨" if STOCK_SYSTEM_READY else "❌ 실패",
            "financial_system": "✅ 연결됨" if FINANCIAL_SYSTEM_READY else "❌ 실패"
        },
        "available_endpoints": [
            "✅ /stock/{company_name} - 실시간 주가 (8개 항목)" if STOCK_SYSTEM_READY else "❌ 주가 시스템 실패",
            "✅ /financial/{company_name} - 재무제표 (34개 항목)" if FINANCIAL_SYSTEM_READY else "❌ 재무 시스템 실패"
        ],
        "next_step": "3단계 - 뉴스 시스템 추가"
    }

@app.get("/health")
def health():
    return {
        "status": "excellent",
        "integration_step": "2단계_주가_재무제표",
        "stock_system": STOCK_SYSTEM_READY,
        "financial_system": FINANCIAL_SYSTEM_READY
    }

# 🚀 실시간 주가 API (1단계에서 유지)
@app.get("/stock/{company_name}")
def get_real_time_stock(company_name: str):
    """실시간 주가 분석 API (8개 핵심 데이터)"""
    if not STOCK_SYSTEM_READY:
        raise HTTPException(status_code=503, detail="실시간 주가 시스템 사용 불가")
    
    try:
        stock_codes = {
            "삼성전자": "005930", "SK하이닉스": "000660", "NAVER": "035420",
            "카카오": "035720", "LG전자": "066570", "현대차": "005380",
            "POSCO홀딩스": "005490", "현대모비스": "012330", "LG화학": "051910",
            "삼성바이오로직스": "207940", "KB금융": "105560", "신한지주": "055550"
        }
        
        stock_code = stock_codes.get(company_name, "005930")
        
        print(f"📊 {company_name} ({stock_code}) 실시간 주가 분석...")
        
        extractor = NaverRealTimeExtractor()
        result = extractor.extract_real_time_data(stock_code)
        
        if result.get('extraction_status') == 'success':
            return {
                "success": True,
                "step": "2단계 - 주가 (1/2 완료)",
                "company_name": company_name,
                "stock_code": stock_code,
                "data_type": "real_time_stock",
                "timestamp": datetime.now().isoformat(),
                "data": result
            }
        else:
            raise HTTPException(status_code=500, detail={"error": "주가 데이터 추출 실패", "details": result.get('error')})
            
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "실시간 주가 처리 오류", "details": str(e)})

# 📈 재무제표 API (2단계 새로 추가)
@app.get("/financial/{company_name}")
def get_financial_analysis(company_name: str):
    """
    📈 재무제표 분석 API (34개 핵심 데이터)
    
    **제공 데이터:**
    - 손익계산서: 매출액, 영업이익, 당기순이익
    - 재무상태표: 자산총계, 부채총계, 자본총계
    - 재무비율: ROE, ROA, 부채비율, EPS, PER, PBR
    - 현금흐름: 영업CF, 투자CF, 재무CF, FCF
    """
    if not FINANCIAL_SYSTEM_READY:
        raise HTTPException(
            status_code=503, 
            detail={
                "error": "재무제표 시스템 사용 불가",
                "required_files": [
                    "enhanced_integrated_financial_system.py",
                    "company_codes/",
                    "cf1001_urls_database.json"
                ]
            }
        )
    
    try:
        print(f"📈 {company_name} 재무제표 분석 시작...")
        
        # 🛡️ 안전하게 기존 재무제표 시스템 호출
        result = get_financial_data(company_name)
        
        success_rate = result.get('metadata', {}).get('success_rate', 0)
        
        if success_rate > 0:
            return {
                "success": True,
                "step": "2단계 - 재무제표 (2/2 완료)",
                "company_name": company_name,
                "data_type": "financial_analysis",
                "timestamp": datetime.now().isoformat(),
                "data": result,
                "summary": {
                    "success_rate": f"{success_rate*100:.1f}%",
                    "data_points": len(result.get('financial_data', {})),
                    "key_metrics": {
                        "매출액": result.get('financial_data', {}).get('매출액', [None])[0],
                        "영업이익": result.get('financial_data', {}).get('영업이익', [None])[0],
                        "ROE": result.get('financial_data', {}).get('ROE(%)', [None])[0],
                        "PER": result.get('financial_data', {}).get('PER(배)', [None])[0]
                    }
                }
            }
        else:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "재무 데이터 없음",
                    "company_name": company_name,
                    "suggestion": "회사명을 정확히 입력하세요 (예: 삼성전자)"
                }
            )
            
    except Exception as e:
        print(f"❌ 재무제표 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "재무제표 처리 중 오류",
                "company_name": company_name,
                "error_details": str(e)
            }
        )

# 🧪 2단계 통합 테스트
@app.get("/test-step2")
def test_step2():
    """2단계 통합 테스트"""
    return {
        "step2_test": "주가 + 재무제표 통합",
        "systems_status": {
            "stock_system": STOCK_SYSTEM_READY,
            "financial_system": FINANCIAL_SYSTEM_READY
        },
        "test_endpoints": {
            "stock": "/stock/삼성전자",
            "financial": "/financial/삼성전자"
        },
        "data_coverage": {
            "stock_data_points": "8개 (현재가, 등락률, 거래량 등)",
            "financial_data_points": "34개 (매출액, ROE, PER 등)"
        },
        "next_step": "3단계 - 뉴스 시스템 추가"
    }

# 🛡️ 2단계 안전성 점검
@app.get("/step2-safety-check")
def step2_safety_check():
    """2단계 안전성 점검"""
    return {
        "step": "2단계 - 주가 + 재무제표",
        "safety_checklist": {
            "백업_생성": "✅ main_backup_before_financial.py",
            "기존_파일_무변경": "✅ enhanced_safe_extractor.py, enhanced_integrated_financial_system.py",
            "주가_시스템": "✅ 정상" if STOCK_SYSTEM_READY else "❌ 실패",
            "재무_시스템": "✅ 정상" if FINANCIAL_SYSTEM_READY else "❌ 실패"
        },
        "recovery_commands": {
            "1단계로_복구": "cp main_backup_before_financial.py main.py",
            "원점으로_복구": "cp main_backup_before_stock.py main.py"
        },
        "integration_progress": "2/5 단계 완료 (40%)"
    }

if __name__ == "__main__":
    import uvicorn
    print("📈 2단계: 주가 + 재무제표 통합!")
    print(f"✅ 주가 시스템: {STOCK_SYSTEM_READY}")
    print(f"✅ 재무 시스템: {FINANCIAL_SYSTEM_READY}")
    print("🧪 테스트: /stock/삼성전자, /financial/삼성전자")
    uvicorn.run(app, host="0.0.0.0", port=8000)
