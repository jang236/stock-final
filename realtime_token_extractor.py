import requests
import time
import re
from urllib.parse import urlparse, parse_qs
import json


class RealtimeTokenExtractor:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def extract_tokens_advanced_method(self, stock_code, company_name):
        """고급 토큰 추출 방법 - 여러 시도를 통한 토큰 발견"""
        print(f"🔍 {company_name}({stock_code}) 실시간 토큰 추출 시작...")

        try:
            # 방법 1: 메인 재무 페이지에서 AJAX 호출 모니터링
            coinfo_url = f"https://finance.naver.com/item/coinfo.naver?code={stock_code}"
            print(f"📊 재무 페이지 접속: {coinfo_url}")

            # 첫 번째 요청 - 페이지 로드
            response = self.session.get(coinfo_url, timeout=15)
            response.raise_for_status()

            # 쿠키 및 세션 정보 확보
            cookies = response.cookies

            # 방법 2: 알려진 패턴으로 토큰 생성 시도
            token_candidates = self.generate_token_candidates(stock_code)

            for i, (encparam, id_param) in enumerate(token_candidates):
                print(f"🧪 토큰 후보 {i+1} 테스트 중...")

                test_url = f"https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd={stock_code}&fin_typ=0&freq_typ=A&encparam={encparam}&id={id_param}"

                if self.validate_cf1001_url(test_url):
                    print(f"✅ {company_name} 토큰 후보 {i+1} 성공!")
                    return test_url

            # 방법 3: 다른 네이버 재무 페이지들 탐색
            alternative_urls = [
                f"https://finance.naver.com/item/main.naver?code={stock_code}",
                f"https://finance.naver.com/item/coinfo.naver?code={stock_code}&fin_typ=0",
                f"https://companyinfo.stock.naver.com/company/cF1001.aspx?cmp_cd={stock_code}",
            ]

            for alt_url in alternative_urls:
                print(f"🔄 대안 페이지 시도: {alt_url}")
                try:
                    response = self.session.get(alt_url, timeout=10)
                    if response.status_code == 200:
                        # 이 페이지에서 토큰 찾기 시도
                        found_url = self.extract_from_page_content(
                            response.text, stock_code)
                        if found_url:
                            print(f"✅ {company_name} 대안 페이지에서 발견!")
                            return found_url
                except:
                    continue

            # 방법 4: 리버스 엔지니어링 접근
            reverse_url = self.reverse_engineer_token(stock_code)
            if reverse_url and self.validate_cf1001_url(reverse_url):
                print(f"✅ {company_name} 리버스 엔지니어링 성공!")
                return reverse_url

            print(f"❌ {company_name} 모든 방법 실패")
            return None

        except Exception as e:
            print(f"❌ {company_name} 토큰 추출 오류: {e}")
            return None

    def generate_token_candidates(self, stock_code):
        """알려진 패턴을 기반으로 토큰 후보 생성"""
        candidates = []

        # 우리가 확인한 실제 토큰들의 패턴 분석
        known_patterns = [
            # 삼성전자 패턴들
            ("ellZa1pGQUIvYWt2U2ZDWi9yc0tQdz09", "ZTRzQlVCd0"),
            ("MERqUlVkcVhRNHhJL2JDbWVFcHFhQT09", "VGVTbkwxZ2"),

            # NAVER 패턴들
            ("VnI0MnRwd0Rwd3FFdjFOa1BnUEI4dz09", "QmZIZ20rMn"),
            ("dG1Yc2swQ2VwUXI5UWtOUmMvZkxlZz09", "bG05RlB6cn"),

            # 신한금융지주 패턴
            ("b0JMTlJ4dmh0V01VQ3VxVGRWb2p0Zz09", "ZlEwemUxRm"),
        ]

        candidates.extend(known_patterns)

        # 패턴 기반 생성 시도
        import base64
        import hashlib

        # 종목코드 기반 해시 생성
        for salt in ["naver", "wisereport", "finance", stock_code]:
            try:
                # 간단한 해시 기반 토큰 생성
                hash_input = f"{stock_code}_{salt}".encode('utf-8')
                hash_result = hashlib.md5(hash_input).hexdigest()

                # Base64 인코딩
                encparam_candidate = base64.b64encode(
                    hash_result[:24].encode()).decode()
                id_candidate = base64.b64encode(
                    hash_result[24:32].encode()).decode()

                candidates.append((encparam_candidate, id_candidate))
            except:
                continue

        return candidates[:10]  # 상위 10개만 테스트

    def extract_from_page_content(self, content, stock_code):
        """페이지 내용에서 토큰 추출 (향상된 버전)"""
        try:
            # 더 넓은 범위의 패턴 검색
            patterns = [
                # Base64 형태의 긴 문자열들
                r'([A-Za-z0-9+/]{28,}={0,2})',
                # URL에서 직접 추출
                r'navercomp\.wisereport\.co\.kr[^"\']*cF1001[^"\']*',
                # JavaScript 변수에서 추출
                r'encparam[^A-Za-z0-9]*([A-Za-z0-9+/=]{20,})',
                r'["\']([A-Za-z0-9+/=]{30,})["\'][^"]*(?:encparam|token)',
            ]

            found_tokens = set()

            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                found_tokens.update(matches)

            # 발견된 토큰들로 조합 시도
            token_list = list(found_tokens)
            for i, encparam in enumerate(token_list):
                for j, id_param in enumerate(token_list):
                    if i != j and len(encparam) >= 20 and len(id_param) >= 8:
                        test_url = f"https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd={stock_code}&fin_typ=0&freq_typ=A&encparam={encparam}&id={id_param}"

                        if self.validate_cf1001_url(test_url):
                            return test_url

            return None

        except Exception as e:
            print(f"⚠️ 페이지 내용 분석 실패: {e}")
            return None

    def reverse_engineer_token(self, stock_code):
        """리버스 엔지니어링을 통한 토큰 생성"""
        try:
            import hashlib
            import base64
            from datetime import datetime

            # 시간 기반 토큰 생성 시도
            current_time = datetime.now()

            time_variations = [
                current_time.strftime("%Y%m%d"),
                current_time.strftime("%Y%m%d%H"),
                current_time.strftime("%H%M"),
                str(int(current_time.timestamp())),
            ]

            for time_var in time_variations:
                # 종목코드 + 시간 조합
                combined = f"{stock_code}_{time_var}_naver"

                # 해시 생성
                hash_obj = hashlib.sha256(combined.encode('utf-8'))
                hash_hex = hash_obj.hexdigest()

                # Base64 인코딩으로 토큰 생성
                encparam = base64.b64encode(hash_hex[:32].encode()).decode()
                id_param = base64.b64encode(hash_hex[32:42].encode()).decode()

                test_url = f"https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd={stock_code}&fin_typ=0&freq_typ=A&encparam={encparam}&id={id_param}"

                if self.validate_cf1001_url(test_url):
                    return test_url

            return None

        except Exception as e:
            print(f"⚠️ 리버스 엔지니어링 실패: {e}")
            return None

    def validate_cf1001_url(self, url):
        """cF1001 URL 유효성 검증"""
        try:
            response = self.session.get(url, timeout=5)

            # 성공 조건: 200 응답 + 100바이트 이상 내용
            if response.status_code == 200 and len(response.content) > 100:
                # 내용이 에러 메시지가 아닌지 확인
                content = response.content.decode('euc-kr', errors='ignore')

                # 에러 키워드 체크
                error_keywords = ['error', 'exception', 'fail', '오류', '에러']
                if any(keyword in content.lower()
                       for keyword in error_keywords):
                    return False

                return True

            return False

        except:
            return False

    def get_cf1001_data(self, stock_code, company_name):
        """전체 프로세스: 토큰 추출 + 데이터 수집"""
        print(f"\n🚀 {company_name}({stock_code}) cF1001 데이터 수집 시작")

        # 1. 토큰 추출
        cf1001_url = self.extract_tokens_advanced_method(
            stock_code, company_name)

        if not cf1001_url:
            print(f"❌ {company_name} 토큰 추출 실패")
            return None

        # 2. 데이터 수집
        try:
            print(f"📊 {company_name} 재무데이터 수집 중...")
            response = self.session.get(cf1001_url, timeout=15)
            response.raise_for_status()

            # 데이터 파싱
            content = response.content.decode('euc-kr', errors='ignore')

            # 간단한 데이터 확인
            if len(content) > 1000:
                print(f"✅ {company_name} 데이터 수집 성공 ({len(content)} 문자)")

                return {
                    "company_name":
                    company_name,
                    "stock_code":
                    stock_code,
                    "cf1001_url":
                    cf1001_url,
                    "data_size":
                    len(content),
                    "content_preview":
                    content[:500] + "..." if len(content) > 500 else content,
                    "status":
                    "success"
                }
            else:
                print(f"⚠️ {company_name} 데이터 크기 부족")
                return None

        except Exception as e:
            print(f"❌ {company_name} 데이터 수집 실패: {e}")
            return None


def test_realtime_extraction():
    """실시간 토큰 추출 테스트"""
    print("🚀 실시간 토큰 추출 시스템 테스트")

    extractor = RealtimeTokenExtractor()

    test_companies = [
        ("삼성전자", "005930"),
        ("NAVER", "035420"),
        ("SK하이닉스", "000660"),
        ("신한금융지주", "055550"),
        ("카카오", "035720"),
    ]

    results = []
    success_count = 0

    for company_name, stock_code in test_companies:
        print("\n" + "=" * 80)

        result = extractor.get_cf1001_data(stock_code, company_name)

        if result:
            results.append(result)
            success_count += 1
            print(f"🎉 {company_name} 성공!")
        else:
            print(f"💔 {company_name} 실패")

        # 서버 부하 방지
        time.sleep(2)

    print(f"\n{'='*80}")
    print(f"📋 테스트 완료: {success_count}/{len(test_companies)}개 성공")

    # 결과 저장
    if results:
        try:
            with open('realtime_cf1001_results.json', 'w',
                      encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print("💾 결과 저장: realtime_cf1001_results.json")
        except Exception as e:
            print(f"❌ 결과 저장 실패: {e}")

    return results


if __name__ == "__main__":
    test_realtime_extraction()
