"""
완전한 기업분석 시스템 - Flask 없는 순수 함수 버전
실시간 주가 + 재무제표 + 뉴스 분석 통합
GPTs 직접 연결 가능
"""
from datetime import datetime
import json
import os

def analyze_company_complete(company_name, stock_code=None):
    """
    완전한 기업 분석 (Flask 없는 순수 함수)
    
    Args:
        company_name: 기업명 (예: 삼성전자)
        stock_code: 종목코드 (예: 005930, 없으면 자동 추정)
        
    Returns:
        dict: 완전한 기업 분석 결과
    """
    print(f"🔍 '{company_name}' 완전한 기업 분석 시작...")
    analysis_start = datetime.now()
    
    # 종목코드 자동 추정 (간단한 매핑)
    if not stock_code:
        stock_code_map = {
            "삼성전자": "005930",
            "SK하이닉스": "000660", 
            "NAVER": "035420",
            "카카오": "035720",
            "LG전자": "066570"
        }
        stock_code = stock_code_map.get(company_name, "005930")
        print(f"📋 종목코드 자동 설정: {stock_code}")
    
    result = {
        "company_name": company_name,
        "stock_code": stock_code,
        "analysis_timestamp": analysis_start.isoformat(),
        "status": "success",
        "data": {},
        "summary": {}
    }
    
    success_count = 0
    
    # 1. 실시간 주가 데이터
    try:
        from enhanced_safe_extractor import NaverRealTimeExtractor
        extractor = NaverRealTimeExtractor()
        stock_data = extractor.extract_real_time_data(stock_code)
        result["data"]["real_time_stock"] = stock_data
        
        if stock_data.get('extraction_status') == 'success':
            success_count += 1
            result["summary"]["stock_price"] = f"{stock_data['real_time_data']['current_price']:,}원" if stock_data.get('real_time_data') else "추출 실패"
            result["summary"]["change_rate"] = f"{stock_data['real_time_data']['change_rate']:+.2f}%" if stock_data.get('real_time_data') and stock_data['real_time_data']['change_rate'] else "추출 실패"
        
        print("✅ 실시간 주가 추출 완료")
    except Exception as e:
        result["data"]["real_time_stock"] = {"error": str(e)}
        print(f"❌ 실시간 주가 실패: {e}")
    
    # 2. 재무제표 데이터
    try:
        from enhanced_integrated_financial_system import get_financial_data
        financial_data = get_financial_data(company_name)
        result["data"]["financial_analysis"] = financial_data
        
        if financial_data.get('metadata', {}).get('success_rate', 0) > 0.5:
            success_count += 1
            # 주요 재무지표 요약
            fd = financial_data.get('financial_data', {})
            result["summary"]["revenue"] = fd.get('매출액', [None])[0] if fd.get('매출액') else None
            result["summary"]["operating_profit"] = fd.get('영업이익', [None])[0] if fd.get('영업이익') else None
            result["summary"]["roe"] = fd.get('ROE(%)', [None])[0] if fd.get('ROE(%)') else None
        
        print("✅ 재무제표 추출 완료")
    except Exception as e:
        result["data"]["financial_analysis"] = {"error": str(e)}
        print(f"❌ 재무제표 실패: {e}")
    
    # 3. 뉴스 분석
    try:
        from news_collector import collect_company_news
        news_data = collect_company_news(company_name)
        result["data"]["news_analysis"] = news_data
        
        if news_data.get('status') == 'success':
            success_count += 1
            result["summary"]["total_news"] = news_data['statistics']['total_news_count']
            result["summary"]["latest_24h_news"] = news_data['statistics']['latest_24h_count']
            result["summary"]["past_news"] = news_data['statistics']['relevant_past_count']
        
        print("✅ 뉴스 분석 완료")
    except Exception as e:
        result["data"]["news_analysis"] = {"error": str(e)}
        print(f"❌ 뉴스 분석 실패: {e}")
    
    # 분석 완료
    analysis_end = datetime.now()
    analysis_duration = (analysis_end - analysis_start).total_seconds()
    
    result["metadata"] = {
        "analysis_duration_seconds": round(analysis_duration, 2),
        "success_systems": success_count,
        "total_systems": 3,
        "success_rate": success_count / 3,
        "analysis_completed_at": analysis_end.isoformat(),
        "version": "v1.0_no_flask",
        "components": {
            "real_time_stock": "enhanced_safe_extractor (8개 항목)",
            "financial_analysis": "enhanced_integrated_financial_system (33개 항목)",
            "news_analysis": "news_collector v12.0 (24시간 + 과거)"
        }
    }
    
    print(f"🎉 완전한 기업 분석 완료!")
    print(f"   성공 시스템: {success_count}/3")
    print(f"   소요 시간: {analysis_duration:.2f}초")
    
    return result

def save_analysis_result(result, filename=None):
    """분석 결과를 JSON 파일로 저장"""
    if not filename:
        company_name = result['company_name'].replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"analysis_{company_name}_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"💾 분석 결과 저장: {filename}")
    return filename

def quick_analysis(company_name):
    """빠른 기업 분석 (요약 정보만)"""
    result = analyze_company_complete(company_name)
    
    print(f"\n📊 {company_name} 분석 요약:")
    print(f"   주가: {result['summary'].get('stock_price', '정보 없음')}")
    print(f"   등락률: {result['summary'].get('change_rate', '정보 없음')}")
    print(f"   매출액: {result['summary'].get('revenue', '정보 없음')}")
    print(f"   영업이익: {result['summary'].get('operating_profit', '정보 없음')}")
    print(f"   ROE: {result['summary'].get('roe', '정보 없음')}%")
    print(f"   뉴스: 총 {result['summary'].get('total_news', 0)}개")
    
    return result

if __name__ == "__main__":
    # 테스트 실행
    print("🚀 완전한 기업분석 시스템 테스트")
    print("=" * 60)
    
    # 삼성전자 분석
    result = quick_analysis("삼성전자")
    
    # 결과 저장
    filename = save_analysis_result(result)
    print(f"✅ 테스트 완료! 결과 파일: {filename}")
