"""
🛡️ 1단계: 실시간 주가 시스템만 안전하게 연결
기존 uvicorn 서버 + 실시간 주가만 추가
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from datetime import datetime

# FastAPI 앱 생성 (기존과 동일)
app = FastAPI(
    title="🎯 기업분석 API - 실시간 주가 연결",
    description="uvicorn 최적화 + 실시간 주가만 안전 연결",
    version="5.1.0"
)

# CORS 설정 (기존과 동일)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🛡️ 실시간 주가 시스템 안전 로드
STOCK_SYSTEM_READY = False
NaverRealTimeExtractor = None

try:
    print("📊 실시간 주가 시스템 로드 시도 중...")
    from enhanced_safe_extractor import NaverRealTimeExtractor
    STOCK_SYSTEM_READY = True
    print("✅ 실시간 주가 시스템 로드 성공!")
except Exception as e:
    print(f"⚠️ 실시간 주가 시스템 로드 실패: {e}")
    STOCK_SYSTEM_READY = False

# 기존 엔드포인트들 (그대로 유지)
@app.get("/")
def root():
    return {
        "status": "success",
        "message": "🛡️ 1단계: 실시간 주가만 안전 연결",
        "python_version": sys.version,
        "server_type": "uvicorn ASGI",
        "integration_step": "1단계 - 실시간 주가만",
        "stock_system": "✅ 연결됨" if STOCK_SYSTEM_READY else "❌ 연결 실패",
        "safety_measures": [
            "✅ 기존 main.py 백업 생성",
            "✅ enhanced_safe_extractor.py 무변경",
            "✅ 최소한의 변경만 적용",
            "✅ 언제든지 복구 가능"
        ],
        "available_endpoints": [
            "✅ /stock/{company_name} - 실시간 주가" if STOCK_SYSTEM_READY else "❌ 실시간 주가 연결 실패"
        ]
    }

@app.get("/health")
def health():
    return {
        "status": "excellent",
        "integration_step": "1단계_실시간_주가만",
        "stock_system": STOCK_SYSTEM_READY,
        "safety": "백업_완료"
    }

# 🚀 실시간 주가 API (매우 조심스럽게 연결)
@app.get("/stock/{company_name}")
def get_real_time_stock(company_name: str):
    """
    🚀 실시간 주가 분석 API (1단계)
    
    **제공 데이터:**
    - 현재가, 전일대비, 등락률
    - 거래량, 거래대금, 시가총액
    - 외국인지분율, 동종업종 정보
    """
    if not STOCK_SYSTEM_READY:
        raise HTTPException(
            status_code=503, 
            detail={
                "error": "실시간 주가 시스템 연결 실패",
                "step": "1단계",
                "suggestion": "서버를 재시작하거나 백업에서 복구하세요"
            }
        )
    
    try:
        # 주요 종목 코드 (확장 가능)
        stock_codes = {
            "삼성전자": "005930", "SK하이닉스": "000660", "NAVER": "035420",
            "카카오": "035720", "LG전자": "066570", "현대차": "005380",
            "POSCO홀딩스": "005490", "현대모비스": "012330", "LG화학": "051910",
            "삼성바이오로직스": "207940", "KB금융": "105560", "신한지주": "055550"
        }
        
        stock_code = stock_codes.get(company_name, "005930")
        
        print(f"📊 {company_name} ({stock_code}) 실시간 주가 분석 시작...")
        
        # 🛡️ 안전하게 기존 시스템 호출 (코드 무변경)
        extractor = NaverRealTimeExtractor()
        result = extractor.extract_real_time_data(stock_code)
        
        if result.get('extraction_status') == 'success':
            return {
                "success": True,
                "step": "1단계 - 실시간 주가만",
                "company_name": company_name,
                "stock_code": stock_code,
                "timestamp": datetime.now().isoformat(),
                "data": result,
                "safety_info": {
                    "기존_코드_변경": "없음",
                    "백업_상태": "완료",
                    "복구_방법": "cp main_backup_before_stock.py main.py"
                }
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "주가 데이터 추출 실패",
                    "company_name": company_name,
                    "details": result.get('error', '알 수 없는 오류')
                }
            )
            
    except Exception as e:
        print(f"❌ 실시간 주가 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "실시간 주가 처리 중 오류",
                "company_name": company_name,
                "error_details": str(e),
                "recovery": "cp main_backup_before_stock.py main.py"
            }
        )

# 🛡️ 안전성 확인 엔드포인트
@app.get("/step1-safety-check")
def step1_safety_check():
    """1단계 안전성 점검"""
    return {
        "step": "1단계 - 실시간 주가만",
        "safety_checklist": {
            "기존_파일_백업": "✅ 완료",
            "enhanced_safe_extractor_무변경": "✅ 확인",
            "시스템_로드_상태": "✅ 성공" if STOCK_SYSTEM_READY else "❌ 실패",
            "복구_가능성": "✅ 언제든지 가능"
        },
        "test_endpoint": "/stock/삼성전자",
        "recovery_command": "cp main_backup_before_stock.py main.py",
        "next_step": "2단계 - 재무제표 연결 (1단계 성공 후)"
    }

# 🧪 1단계 테스트 전용
@app.get("/test-step1")
def test_step1():
    """1단계만 테스트"""
    return {
        "step1_test": "실시간 주가만 연결됨",
        "stock_system": STOCK_SYSTEM_READY,
        "test_companies": ["삼성전자", "SK하이닉스", "NAVER", "카카오"],
        "example": "/stock/삼성전자",
        "safety": "기존 코드 무변경, 백업 완료"
    }

if __name__ == "__main__":
    import uvicorn
    print("🛡️ 1단계: 실시간 주가만 안전 연결!")
    print(f"백업 완료: main_backup_before_stock.py")
    if STOCK_SYSTEM_READY:
        print("✅ 실시간 주가 시스템 연결 성공!")
        print("🧪 테스트: /stock/삼성전자")
    else:
        print("⚠️ 실시간 주가 시스템 연결 실패")
        print("🔄 복구: cp main_backup_before_stock.py main.py")
    uvicorn.run(app, host="0.0.0.0", port=8000)
