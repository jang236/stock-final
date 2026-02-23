#!/usr/bin/env python3
"""
네이버 증권 cF1001 토큰 상태 확인기
랜덤 3개 기업의 토큰 상태를 테스트합니다.
"""

import json
import requests
import random
import time
from datetime import datetime

def load_database():
    """URL 데이터베이스 로드"""
    try:
        with open('company_codes/cf1001_urls_database.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ 데이터베이스 로드 완료: {len(data)}개 기업")
        return data
    except Exception as e:
        print(f"❌ 데이터베이스 로드 실패: {e}")
        return None

def select_random_companies(database, count=3):
    """랜덤하게 기업 선택"""
    companies = []
    company_names = list(database.keys())
    
    # 성공적으로 수집된 기업들만 필터링
    valid_companies = []
    for name, data in database.items():
        if isinstance(data, dict) and 'cF1001_url' in data and data.get('status') == 'success':
            valid_companies.append(name)
    
    if len(valid_companies) < count:
        print(f"⚠️ 유효한 기업이 {len(valid_companies)}개만 있습니다.")
        count = len(valid_companies)
    
    selected = random.sample(valid_companies, count)
    
    for company_name in selected:
        company_data = database[company_name]
        companies.append({
            'name': company_name,
            'code': company_data.get('code', 'Unknown'),
            'url': company_data['cF1001_url'],
            'collected_at': company_data.get('collected_at', 'Unknown'),
            'encparam': company_data.get('parameters', {}).get('encparam', 'Unknown')
        })
    
    return companies

def test_token(company_info):
    """개별 토큰 테스트"""
    print(f"\n🧪 테스트 중: {company_info['name']} ({company_info['code']})")
    print(f"📅 수집일: {company_info['collected_at']}")
    print(f"🔑 토큰: {company_info['encparam'][:20]}...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
        'Referer': 'https://finance.naver.com/',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site'
    }
    
    try:
        response = requests.get(company_info['url'], headers=headers, timeout=10)
        
        print(f"📡 응답 코드: {response.status_code}")
        print(f"📄 응답 크기: {len(response.content)} 바이트")
        
        # 응답 내용 분석
        if response.status_code == 200:
            if len(response.content) > 100:  # 정상적인 데이터
                try:
                    json_data = response.json()
                    if 'result' in json_data and json_data['result']:
                        print("✅ 토큰 상태: 정상 작동")
                        return True
                    else:
                        print("⚠️ 토큰 상태: 빈 데이터")
                        return False
                except:
                    print("⚠️ 토큰 상태: JSON 파싱 실패")
                    return False
            else:
                print("❌ 토큰 상태: 만료됨 (빈 응답)")
                return False
        else:
            print(f"❌ 토큰 상태: HTTP 오류 ({response.status_code})")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 네트워크 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("🚀 네이버 증권 cF1001 토큰 상태 확인 시작")
    print("=" * 60)
    
    # 데이터베이스 로드
    database = load_database()
    if not database:
        return
    
    # 랜덤 3개 기업 선택
    print(f"\n🎲 랜덤 3개 기업 선택 중...")
    companies = select_random_companies(database, 3)
    
    if not companies:
        print("❌ 테스트할 기업을 찾을 수 없습니다.")
        return
    
    print(f"\n📋 선택된 기업들:")
    for i, company in enumerate(companies, 1):
        print(f"{i}. {company['name']} ({company['code']})")
    
    # 토큰 테스트 실행
    print(f"\n🔍 토큰 상태 테스트 시작...")
    print("=" * 60)
    
    success_count = 0
    total_count = len(companies)
    
    for i, company in enumerate(companies, 1):
        print(f"\n[{i}/{total_count}] ", end="")
        if test_token(company):
            success_count += 1
        
        # 요청 간 딜레이
        if i < total_count:
            print("⏰ 2초 대기...")
            time.sleep(2)
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    print(f"✅ 성공: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    print(f"❌ 실패: {total_count - success_count}/{total_count} ({(total_count-success_count)/total_count*100:.1f}%)")
    
    if success_count == 0:
        print("\n🚨 모든 토큰이 만료되었습니다!")
        print("💡 새로운 토큰 수집이 필요합니다.")
    elif success_count < total_count:
        print(f"\n⚠️ 일부 토큰이 만료되었습니다.")
        print("💡 토큰 갱신을 고려해보세요.")
    else:
        print(f"\n🎉 모든 토큰이 정상 작동합니다!")
        print("💡 현재 시스템을 계속 사용할 수 있습니다.")
    
    print(f"\n📅 테스트 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
