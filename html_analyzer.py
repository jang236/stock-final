import requests
from bs4 import BeautifulSoup
import re


def analyze_cf1001_html():
    """삼성전자 cF1001 HTML 구조 분석"""

    # 삼성전자 cF1001 토큰 URL (새로 업데이트된 토큰)
    cf1001_url = "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=035420&fin_typ=0&freq_typ=A&encparam=VnI0MnRwd0Rwd3FFdjFOa1BnUEI4dz09&id=QmZIZ20rMn"

    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    print("🔍 삼성전자 cF1001 HTML 구조 분석 시작")
    print(f"🔗 URL: {cf1001_url[:80]}...")

    try:
        # HTML 다운로드
        response = requests.get(cf1001_url, headers=headers, timeout=15)
        response.raise_for_status()

        # EUC-KR 디코딩
        html_content = response.content.decode('euc-kr', errors='ignore')

        print(f"✅ HTML 다운로드 성공 ({len(html_content)} 문자)")

        # 1. HTML 파일로 저장
        filename = "cf1001_samsung_raw.html"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"💾 HTML 파일 저장: {filename}")

        # 2. 기본 구조 분석
        soup = BeautifulSoup(html_content, 'html.parser')

        print(f"\n📊 HTML 구조 분석:")
        print(f"   📄 전체 길이: {len(html_content):,} 문자")

        # 테이블 개수
        tables = soup.find_all('table')
        print(f"   📋 테이블 개수: {len(tables)}개")

        # 각 테이블 정보
        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            print(f"   📈 테이블 {i+1}: {len(rows)}개 행")

            if rows:
                # 첫 번째 행 (헤더) 분석
                first_row = rows[0]
                cells = first_row.find_all(['th', 'td'])
                print(f"      📊 첫 행 셀 개수: {len(cells)}개")

                # 헤더 내용 미리보기
                headers_preview = []
                for cell in cells[:5]:  # 처음 5개만
                    text = cell.get_text(strip=True)
                    headers_preview.append(text[:10] +
                                           "..." if len(text) > 10 else text)
                print(f"      📝 헤더 미리보기: {headers_preview}")

        # 3. 재무 키워드 검색
        financial_keywords = [
            '매출액', '영업이익', '당기순이익', '자산총계', '부채총계', '자본총계', '영업활동현금흐름',
            '투자활동현금흐름', '재무활동현금흐름'
        ]

        found_keywords = []
        for keyword in financial_keywords:
            if keyword in html_content:
                found_keywords.append(keyword)

        print(f"\n💰 발견된 재무 키워드 ({len(found_keywords)}개):")
        for keyword in found_keywords:
            print(f"   ✅ {keyword}")

        # 4. HTML 내용 미리보기 (처음 1000자)
        print(f"\n📄 HTML 내용 미리보기 (처음 1000자):")
        print("-" * 80)
        preview = html_content[:1000].replace('\n', ' ').replace('\t', ' ')
        # 연속된 공백 제거
        preview = re.sub(r'\s+', ' ', preview)
        print(preview)
        print("-" * 80)

        # 5. 테이블 내용 샘플 추출
        if tables:
            print(f"\n📋 첫 번째 테이블 상세 분석:")
            first_table = tables[0]
            rows = first_table.find_all('tr')

            for i, row in enumerate(rows[:5]):  # 처음 5행만
                cells = row.find_all(['th', 'td'])
                row_data = []
                for cell in cells:
                    text = cell.get_text(strip=True)
                    row_data.append(text[:15] +
                                    "..." if len(text) > 15 else text)
                print(f"   행 {i+1}: {row_data}")

        # 6. 분석 요약
        print(f"\n📝 분석 요약:")
        print(f"   ✅ HTML 다운로드: 성공")
        print(f"   ✅ 파일 저장: {filename}")
        print(f"   📊 테이블 수: {len(tables)}개")
        print(f"   💰 재무 키워드: {len(found_keywords)}개 발견")
        print(f"   📏 데이터 크기: {len(html_content):,} 문자")

        if len(tables) > 0:
            print(f"   🎉 테이블 구조 확인됨 - 파싱 로직 수정 가능")
        else:
            print(f"   ⚠️ 테이블 없음 - HTML 구조 재검토 필요")

        return html_content, tables

    except Exception as e:
        print(f"❌ 분석 실패: {e}")
        return None, None


if __name__ == "__main__":
    analyze_cf1001_html()
    print(f"\n💡 다음 단계: cf1001_samsung_raw.html 파일을 열어서 실제 구조를 확인하세요!")
