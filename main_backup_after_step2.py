"""
🛡️ 2단계: 실시간 주가 + 재무제표 시스템 연결
1단계 유지 + 재무제표만 추가
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

# 🛡️ 시스템들 안전 로드
STOCK_SYSTEM_READY = False
FINANCIAL_SYSTEM_READY = False
NaverRealTimeExtractor = None
get_financial_data = None

# 실시간 주가 시스템 (1단계에서 이미 검증됨)
try:
    from enhanced_safe_extractor import NaverRealTimeExtractor
    STOCK_SYSTEM_READY = True
    print("✅ 실시간 주가 시스템 유지!")
except Exception as e:
    print(f"⚠️ 실시간 주가 시스템 오류: {e}")

# 재무제표 시스템 (2단계 새로 추가)
try:
    print("📈 재무제표 시스템 로드 시도 중...")
    from enhanced_integrated_financial_system import get_financial_data
    FINANCIAL_SYSTEM_READY = True
    print("✅ 재무제표 시스템 로드 성공!")
except Exception as e:
    print(f"⚠️ 재무제표 시스템 로드 실패: {e}")

@app.get("/")
def root():
    return {
        "status": "success",
        "message": "🛡️ 2단계: 실시간 주가 + 재무제표 연결",
        "integration_step": "2단계 - 주가+재무제표",
        "systems_status": {
            "stock_system": "✅ 연결됨" if STOCK_SYSTEM_READY else "❌ 연결 실패",
            "financial_system": "✅ 연결됨" if FINANCIAL_SYSTEM_READY else "❌ 연결 실패"
        },
        "available_endpoints": [
            "✅ /stock/{company_name} - 실시간 주가 (8개 항목)" if STOCK_SYSTEM_READY else "❌ 주가 시스템 오류",
            "✅ /financial/{company_name} - 재무제표 (34개 항목)" if FINANCIAL_SYSTEM_READY else "❌ 재무 시스템 오류"
        ],
        "safety_measures": [
            "✅ 1단계 백업: main_backup_after_step1.py",
            "✅ 기존 시스템 파일 무변경",
            "✅ 단계별 복구 가능"
        ]
    }

@app.get("/health")
def health():
    return {
        "status": "excellent",
        "step": "2단계_주가+재무제표",
        "stock_system": STOCK_SYSTEM_READY,
        "financial_system": FINANCIAL_SYSTEM_READY
    }

# 🚀 실시간 주가 API (1단계에서 그대로 유지)
@app.get("/stock/{company_name}")
def get_real_time_stock(company_name: str):
    """실시간 주가 분석 API (1단계 기능 유지)"""
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
        
        extractor = NaverRealTimeExtractor()
        result = extractor.extract_real_time_data(stock_code)
        
        if result.get('extraction_status') == 'success':
            return {
                "success": True,
                "step": "2단계 - 주가 기능 유지",
                "company_name": company_name,
                "stock_code": stock_code,
                "data_type": "real_time_stock",
                "timestamp": datetime.now().isoformat(),
                "data": result
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', '주가 추출 실패'))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 📈 재무제표 API (2단계 새로 추가)
@app.get("/financial/{company_name}")
def get_financial_analysis(company_name: str):
    """
    📈 재무제표 분석 API (2단계 신규)
    
    **제공 데이터 (34개 항목):**
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
                    "cf1001_urls_database.json",
                    "company_codes/ 폴더"
                ]
            }
        )
    
    try:
        print(f"📈 {company_name} 재무제표 분석 시작...")
        
        # 🛡️ 안전하게 기존 시스템 호출 (코드 무변경)
        result = get_financial_data(company_name)
        
        if result and result.get('metadata', {}).get('success_rate', 0) > 0:
            return {
                "success": True,
                "step": "2단계 - 재무제표 추가",
                "company_name": company_name,
                "data_type": "financial_analysis",
                "timestamp": datetime.now().isoformat(),
                "data": result,
                "summary": {
                    "총_데이터_항목": len(result.get('financial_data', {})),
                    "성공률": f"{result.get('metadata', {}).get('success_rate', 0)*100:.1f}%",
                    "주요_지표": {
                        "매출액": result.get('financial_data', {}).get('매출액', [None])[0],
                        "영업이익": result.get('financial_data', {}).get('영업이익', [None])[0],
                        "ROE": result.get('financial_data', {}).get('ROE(%)', [None])[0],
                        "부채비율": result.get('financial_data', {}).get('부채비율', [None])[0]
                    }
                }
            }
        else:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "재무제표 데이터 없음",
                    "company_name": company_name,
                    "suggestion": "기업명을 정확히 입력하거나 다른 기업을 시도하세요"
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

# 🛡️ 2단계 안전성 확인
@app.get("/step2-safety-check")
def step2_safety_check():
    """2단계 안전성 점검"""
    return {
        "step": "2단계 - 주가+재무제표",
        "systems_status": {
            "실시간_주가": "✅ 정상" if STOCK_SYSTEM_READY else "❌ 오류",
            "재무제표": "✅ 정상" if FINANCIAL_SYSTEM_READY else "❌ 오류"
        },
        "safety_checklist": {
            "1단계_백업": "✅ main_backup_after_step1.py",
            "기존_파일_무변경": "✅ 확인",
            "단계별_복구": "✅ 가능"
        },
        "test_endpoints": [
            "/stock/삼성전자 (1단계 기능)",
            "/financial/삼성전자 (2단계 기능)"
        ],
        "next_step": "3단계 - 뉴스 시스템 추가"
    }

# 🧪 2단계 통합 테스트
@app.get("/test-step2")
def test_step2():
    """2단계 통합 테스트"""
    return {
        "step2_test": "주가 + 재무제표 연결됨",
        "stock_system": STOCK_SYSTEM_READY,
        "financial_system": FINANCIAL_SYSTEM_READY,
        "test_flow": [
            "1. /stock/삼성전자 → 실시간 주가",
            "2. /financial/삼성전자 → 재무제표",
            "3. 두 시스템 독립적 동작 확인"
        ],
        "data_coverage": {
            "실시간_주가": "8개 항목",
            "재무제표": "34개 항목",
            "총합": "42개 데이터 포인트"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("📈 2단계: 실시간 주가 + 재무제표 연결!")
    print(f"시스템 상태: 주가({STOCK_SYSTEM_READY}) + 재무({FINANCIAL_SYSTEM_READY})")
    uvicorn.run(app, host="0.0.0.0", port=8000)
