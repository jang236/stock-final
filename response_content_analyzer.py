#!/usr/bin/env python3
"""
토큰 응답 내용 분석기
실제 응답이 무엇인지 상세히 분석합니다.
"""

import json
import requests
import random

def analyze_token_response():
    """토큰 응답 상세 분석"""
    
    # 데이터베이스에서 랜덤 1개 선택
    with open('company_codes/cf1001_urls_database.json', 'r', encoding='utf-8') as f:
        database = json.load(f)
    
    # 성공 상태인 기업들 중 랜덤 선택
    valid_companies = []
    for name, data in database.items():
        if isinstance(data, dict) and 'cF1001_url' in data and data.get('status') == 'success':
            valid_companies.append((name, data))
    
    # 메디포스트 우선 선택 (28KB 응답이 있었던 기업)
    target_company = None
    for name, data in valid_companies:
        if '메디포스트' in name or data.get('code') == '078160':
            target_company = (name, data)
            break
    
    # 메디포스트가 없으면 랜덤 선택
    if not target_company:
        target_company = random.choice(valid_companies)
    
    company_name, company_data = target_company
    
    print(f"🧪 분석 대상: {company_name} ({company_data.get('code')})")
    print(f"📅 수집일: {company_data.get('collected_at')}")
    print(f"🔗 URL: {company_data['cF1001_url']}")
    print("=" * 80)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Referer': 'https://finance.naver.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    try:
        response = requests.get(company_data['cF1001_url'], headers=headers, timeout=15)
        
        print(f"📡 HTTP 상태: {response.status_code}")
        print(f"📄 응답 크기: {len(response.content):,} 바이트")
        print(f"🗂️ Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        
        # 응답 내용 분석
        content = response.text
        print(f"\n📋 응답 내용 분석:")
        print(f"   전체 길이: {len(content):,} 문자")
        print(f"   첫 100자: {repr(content[:100])}")
        print(f"   끝 100자: {repr(content[-100:])}")
        
        # JSON 시도
        print(f"\n🔍 JSON 파싱 시도:")
        try:
            json_data = json.loads(content)
            print(f"✅ JSON 파싱 성공!")
            print(f"   타입: {type(json_data)}")
            if isinstance(json_data, dict):
                print(f"   키들: {list(json_data.keys())}")
                if 'result' in json_data:
                    print(f"   result 타입: {type(json_data['result'])}")
                    if isinstance(json_data['result'], list):
                        print(f"   result 길이: {len(json_data['result'])}")
                        if len(json_data['result']) > 0:
                            print(f"   첫 번째 항목: {json_data['result'][0]}")
            elif isinstance(json_data, list):
                print(f"   리스트 길이: {len(json_data)}")
                if len(json_data) > 0:
                    print(f"   첫 번째 항목: {json_data[0]}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON 파싱 실패: {e}")
            print(f"   오류 위치: {e.pos}")
            if e.pos < len(content):
                print(f"   오류 주변: {repr(content[max(0, e.pos-20):e.pos+20])}")
        
        # HTML 체크
        if '<html' in content.lower() or '<!doctype' in content.lower():
            print(f"\n🌐 HTML 컨텐츠 감지됨")
            
            # 특정 패턴 찾기
            patterns_to_check = [
                'cF1001',
                'encparam',
                '재무제표',
                '매출액',
                'error',
                'expired',
                'invalid'
            ]
            
            print(f"🔍 패턴 검색:")
            for pattern in patterns_to_check:
                count = content.lower().count(pattern.lower())
                if count > 0:
                    print(f"   '{pattern}': {count}회 발견")
        
        # 특별한 응답 패턴 체크
        print(f"\n🎯 특별 패턴 체크:")
        if len(content) == 0:
            print("   빈 응답 - 토큰 완전 만료")
        elif len(content) < 100:
            print(f"   짧은 응답 - 오류 메시지 가능성: {repr(content)}")
        elif 'application/json' in response.headers.get('Content-Type', ''):
            print("   JSON Content-Type이지만 파싱 실패 - 형식 문제")
        elif len(content) > 10000:
            print("   대용량 응답 - 실제 데이터일 가능성")
            
            # 재무제표 관련 키워드 찾기
            financial_keywords = ['매출액', '영업이익', '순이익', '자산총계', '부채총계', '자본총계']
            found_keywords = []
            for keyword in financial_keywords:
                if keyword in content:
                    found_keywords.append(keyword)
            
            if found_keywords:
                print(f"   ✅ 재무제표 키워드 발견: {found_keywords}")
                print("   → 토큰이 작동하고 있을 가능성!")
            else:
                print("   ❌ 재무제표 키워드 미발견")
        
    except Exception as e:
        print(f"❌ 요청 실패: {e}")

if __name__ == "__main__":
    analyze_token_response()
