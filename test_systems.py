"""
기존 3개 시스템 실제 작동 테스트
"""
import sys
import traceback
from datetime import datetime

def test_real_time_stock():
    """실시간 주가 시스템 테스트"""
    print("🔍 실시간 주가 시스템 테스트 중...")
    try:
        from enhanced_safe_extractor import NaverRealTimeExtractor
        extractor = NaverRealTimeExtractor()
        
        # 삼성전자 테스트
        result = extractor.extract_real_time_data("005930")
        
        if result.get('extraction_status') == 'success':
            data = result.get('real_time_data', {})
            print(f"✅ 실시간 주가 성공!")
            print(f"   현재가: {data.get('current_price', 'N/A')}")
            print(f"   등락률: {data.get('change_rate', 'N/A')}")
            return True
        else:
            print(f"⚠️ 실시간 주가 부분 실패: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 실시간 주가 오류: {e}")
        print(f"상세 오류: {traceback.format_exc()}")
        return False

def test_financial_system():
    """재무제표 시스템 테스트"""
    print("🔍 재무제표 시스템 테스트 중...")
    try:
        from enhanced_integrated_financial_system import get_financial_data
        
        # 삼성전자 테스트
        result = get_financial_data("삼성전자")
        
        if result.get('metadata', {}).get('success_rate', 0) > 0:
            print(f"✅ 재무제표 성공!")
            financial_data = result.get('financial_data', {})
            print(f"   매출액: {financial_data.get('매출액', ['N/A'])[0]}")
            print(f"   영업이익: {financial_data.get('영업이익', ['N/A'])[0]}")
            return True
        else:
            print(f"⚠️ 재무제표 부분 실패: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 재무제표 오류: {e}")
        print(f"상세 오류: {traceback.format_exc()}")
        return False

def test_news_system():
    """뉴스 분석 시스템 테스트"""
    print("🔍 뉴스 분석 시스템 테스트 중...")
    try:
        from news_collector import collect_company_news
        
        # 삼성전자 테스트
        result = collect_company_news("삼성전자")
        
        if result.get('status') == 'success':
            stats = result.get('statistics', {})
            print(f"✅ 뉴스 분석 성공!")
            print(f"   총 뉴스: {stats.get('total_news_count', 'N/A')}개")
            print(f"   24시간 뉴스: {stats.get('latest_24h_count', 'N/A')}개")
            return True
        else:
            print(f"⚠️ 뉴스 분석 부분 실패: {result}")
            return False
            
    except Exception as e:
        print(f"❌ 뉴스 분석 오류: {e}")
        print(f"상세 오류: {traceback.format_exc()}")
        return False

def main():
    """전체 시스템 테스트"""
    print("🚀 기존 3개 시스템 종합 테스트 시작")
    print(f"⏰ 테스트 시작 시간: {datetime.now()}")
    print("=" * 60)
    
    results = []
    
    # 각 시스템 테스트
    results.append(("실시간 주가", test_real_time_stock()))
    print("")
    
    results.append(("재무제표", test_financial_system()))
    print("")
    
    results.append(("뉴스 분석", test_news_system()))
    print("")
    
    # 결과 요약
    print("=" * 60)
    print("📊 테스트 결과 요약:")
    
    success_count = 0
    for system_name, success in results:
        status = "✅ 성공" if success else "❌ 실패"
        print(f"   {system_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n🎯 전체 성공률: {success_count}/3 ({success_count/3*100:.1f}%)")
    
    if success_count == 3:
        print("🎉 모든 시스템이 정상 작동합니다!")
        print("✅ FastAPI 배포 준비 완료!")
    elif success_count >= 1:
        print("⚠️ 일부 시스템만 작동합니다.")
        print("🔧 문제가 있는 시스템을 확인하고 수정이 필요합니다.")
    else:
        print("❌ 모든 시스템에 문제가 있습니다.")
        print("🔧 파일 및 환경 설정을 다시 확인해야 합니다.")
    
    print(f"⏰ 테스트 완료 시간: {datetime.now()}")

if __name__ == "__main__":
    main()
