import requests
import time


def test_known_tokens():
    """우리가 확인한 기존 토큰들의 현재 상태 확인"""

    print("🔍 기존 토큰들의 유효성 검사 시작")

    # 우리가 이전에 확인한 토큰들
    known_tokens = [{
        "company": "삼성전자",
        "code": "005930",
        "url":
        "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=005930&fin_typ=0&freq_typ=A&encparam=ellZa1pGQUIvYWt2U2ZDWi9yc0tQdz09&id=ZTRzQlVCd0",
        "when": "오전에 확인"
    }, {
        "company": "삼성전자",
        "code": "005930",
        "url":
        "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=005930&fin_typ=0&freq_typ=A&encparam=MERqUlVkcVhRNHhJL2JDbWVFcHFhQT09&id=VGVTbkwxZ2",
        "when": "오후에 확인"
    }, {
        "company": "NAVER",
        "code": "035420",
        "url":
        "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=035420&fin_typ=0&freq_typ=A&encparam=VnI0MnRwd0Rwd3FFdjFOa1BnUEI4dz09&id=QmZIZ20rMn",
        "when": "시크릿모드에서 확인"
    }, {
        "company": "NAVER",
        "code": "035420",
        "url":
        "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=035420&fin_typ=0&freq_typ=A&encparam=dG1Yc2swQ2VwUXI5UWtOUmMvZkxlZz09&id=bG05RlB6cn",
        "when": "일반모드에서 확인"
    }, {
        "company": "신한금융지주",
        "code": "055550",
        "url":
        "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=055550&fin_typ=0&freq_typ=A&encparam=b0JMTlJ4dmh0V01VQ3VxVGRWb2p0Zz09&id=ZlEwemUxRm",
        "when": "시크릿모드에서 확인"
    }]

    session = requests.Session()
    session.headers.update({
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    valid_tokens = []
    invalid_tokens = []

    for i, token_info in enumerate(known_tokens):
        company = token_info['company']
        code = token_info['code']
        url = token_info['url']
        when = token_info['when']

        print(f"\n📊 테스트 {i+1}: {company}({code}) - {when}")
        print(f"🔗 URL: {url[:80]}...")

        try:
            response = session.get(url, timeout=10)
            content_size = len(response.content)

            print(f"📈 응답 상태: {response.status_code}")
            print(f"📏 응답 크기: {content_size} bytes")

            if response.status_code == 200 and content_size > 100:
                # 내용 미리보기
                try:
                    content = response.content.decode('euc-kr',
                                                      errors='ignore')
                    preview = content[:200].replace('\n',
                                                    ' ').replace('\t', ' ')
                    print(f"📄 내용 미리보기: {preview}...")

                    # 에러 키워드 체크
                    error_keywords = [
                        'error', 'exception', 'fail', '오류', '에러', 'not found'
                    ]
                    has_error = any(keyword in content.lower()
                                    for keyword in error_keywords)

                    if not has_error:
                        print(f"✅ {company} 토큰 유효!")
                        valid_tokens.append(token_info)
                    else:
                        print(f"❌ {company} 응답에 오류 포함")
                        invalid_tokens.append(token_info)

                except Exception as decode_error:
                    print(f"⚠️ {company} 응답 디코딩 실패: {decode_error}")
                    invalid_tokens.append(token_info)
            else:
                print(f"❌ {company} 무효한 응답")
                invalid_tokens.append(token_info)

        except Exception as e:
            print(f"❌ {company} 연결 실패: {e}")
            invalid_tokens.append(token_info)

        # 요청 간격
        time.sleep(1)

    # 결과 요약
    print(f"\n{'='*80}")
    print(f"📋 검사 완료:")
    print(f"✅ 유효한 토큰: {len(valid_tokens)}개")
    print(f"❌ 무효한 토큰: {len(invalid_tokens)}개")

    if valid_tokens:
        print(f"\n🎉 유효한 토큰들:")
        for token in valid_tokens:
            print(f"   • {token['company']} ({token['when']})")

    if invalid_tokens:
        print(f"\n💔 무효한 토큰들:")
        for token in invalid_tokens:
            print(f"   • {token['company']} ({token['when']})")

    return valid_tokens, invalid_tokens


def suggest_next_steps(valid_tokens, invalid_tokens):
    """결과에 따른 다음 단계 제안"""

    print(f"\n🎯 다음 단계 제안:")

    if len(valid_tokens) >= 2:
        print("✅ 옵션 1: 유효한 토큰들로 cF1001 API 구현 진행")
        print("✅ 옵션 2: 유효한 토큰 패턴 분석하여 생성 규칙 찾기")

    elif len(valid_tokens) == 1:
        print("⚠️ 옵션 1: 유효한 1개 토큰으로 테스트 API 구현")
        print("🔄 옵션 2: 브라우저에서 새 토큰 수동 수집")

    else:
        print("❌ 모든 토큰 만료됨")
        print("🔄 옵션 1: 브라우저에서 새 토큰 수동 수집")
        print("🔄 옵션 2: cF1002 기반 API로 전환")
        print("🔧 옵션 3: 다른 토큰 추출 방법 시도")


if __name__ == "__main__":
    print("🚀 기존 토큰 유효성 검사 시작")

    valid_tokens, invalid_tokens = test_known_tokens()
    suggest_next_steps(valid_tokens, invalid_tokens)

    print(f"\n💡 이 결과를 바탕으로 다음 전략을 결정하겠습니다!")
