#!/bin/bash
echo "🧪 전체 규모별 시가총액 최종 테스트"

echo "💰 현대차 (41조 6,682억원 예상):"
curl -s "https://stock-final.replit.app/analyze-company?company_name=%ED%98%84%EB%8C%80%EC%B0%A8" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    rt_data = data['data']['real_time_stock']['real_time_data']
    print(f'  현재가: {rt_data[\"current_price\"]}원')
    print(f'  시가총액: {rt_data[\"market_cap\"]}')
    if '41조' in rt_data['market_cap'] and '6,682' in rt_data['market_cap']:
        print('  ✅ 성공!')
    else:
        print('  ❌ 실패')
except: print('  ❌ API 호출 실패')
"

echo ""
echo "💰 삼성전자 (353조원 예상):"
curl -s "https://stock-final.replit.app/analyze-company?company_name=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    rt_data = data['data']['real_time_stock']['real_time_data']
    print(f'  현재가: {rt_data[\"current_price\"]}원')
    print(f'  시가총액: {rt_data[\"market_cap\"]}')
    if '353조' in rt_data['market_cap']:
        print('  ✅ 성공!')
    else:
        print('  ❌ 실패')
except: print('  ❌ API 호출 실패')
"

echo ""
echo "💰 두산에너빌리티 (43조 8,144억원 예상):"
curl -s "https://stock-final.replit.app/analyze-company?company_name=%EB%91%90%EC%82%B0%EC%97%90%EB%84%88%EB%B9%8C%EB%A6%AC%ED%8B%B0" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    rt_data = data['data']['real_time_stock']['real_time_data']
    print(f'  현재가: {rt_data[\"current_price\"]}원')
    print(f'  시가총액: {rt_data[\"market_cap\"]}')
    if '43조' in rt_data['market_cap'] and '8,144' in rt_data['market_cap']:
        print('  ✅ 성공!')
    else:
        print('  ❌ 실패')
except: print('  ❌ API 호출 실패')
"
