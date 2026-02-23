import requests
import re
from datetime import datetime


def parse_cf1001_data_fixed(html_content):
    """실제 cF1001 데이터 구조에 맞춘 파싱 로직"""

    try:
        # 1. 주요재무정보 섹션 찾기
        # 데이터가 테이블 형태가 아닌 텍스트 형태로 되어 있음

        financial_data = {}

        # 2. 연도/분기 헤더 추출
        # "2022/12(IFRS연결)" 패턴 찾기
        year_pattern = r'(\d{4}/\d{2}(?:\([^)]+\))?(?:\([^)]+\))?|\d{4}/\d{2}\([^)]*E[^)]*\))'
        year_matches = re.findall(year_pattern, html_content)

        # 중복 제거 및 정렬
        years = []
        seen = set()
        for year in year_matches:
            if year not in seen and ('2022' in year or '2023' in year
                                     or '2024' in year or '2025' in year
                                     or '2026' in year):
                years.append(year)
                seen.add(year)

        print(f"📅 발견된 연도/분기: {years}")

        # 3. 재무 항목별 데이터 추출
        financial_items = [
            '매출액', '영업이익', '영업이익(발표기준)', '세전계속사업이익', '당기순이익', '당기순이익(지배)',
            '당기순이익(비지배)', '자산총계', '부채총계', '자본총계', '자본총계(지배)', '자본총계(비지배)',
            '자본금', '영업활동현금흐름', '투자활동현금흐름', '재무활동현금흐름', 'CAPEX', 'FCF',
            '이자발생부채', '영업이익률', '순이익률', 'ROE\\(%\\)', 'ROA\\(%\\)', '부채비율',
            '자본유보율', 'EPS\\(원\\)', 'PER\\(배\\)', 'BPS\\(원\\)', 'PBR\\(배\\)',
            '현금DPS\\(원\\)', '현금배당수익률', '현금배당성향\\(%\\)', '발행주식수\\(보통주\\)'
        ]

        # 4. 각 재무 항목별로 데이터 라인 찾기
        for item in financial_items:
            # 정규식에서 특수문자 처리
            item_pattern = item.replace('(', '\\(').replace(')',
                                                            '\\)').replace(
                                                                '%', '%')

            # 해당 항목의 라인 찾기
            line_pattern = f'{item_pattern}\\s+([\\d,.-]+(?:\\s+[\\d,.-]+)*)'
            matches = re.findall(line_pattern, html_content)

            if matches:
                # 숫자들을 분리
                numbers = re.findall(r'[\\d,.-]+', matches[0])

                # 연도별 매핑
                item_data = {}
                for i, year in enumerate(years[:len(numbers)]):
                    if i < len(numbers):
                        # 쉼표 제거하고 숫자로 변환 시도
                        value = numbers[i].replace(',', '')
                        try:
                            # 숫자인 경우 포맷팅
                            if value and value not in ['-', '']:
                                numeric_value = float(value)
                                item_data[
                                    year] = f"{numeric_value:,.0f}" if numeric_value.is_integer(
                                    ) else f"{numeric_value:,.2f}"
                            else:
                                item_data[year] = "정보없음"
                        except:
                            item_data[year] = value if value else "정보없음"

                if item_data:
                    # 원래 항목명으로 저장 (정규식 특수문자 제거)
                    clean_item = item.replace('\\', '')
                    financial_data[clean_item] = item_data
                    print(f"✅ {clean_item}: {len(item_data)}개 연도 데이터 추출")

        # 5. 데이터 분류
        classified_data = {
            "손익계산서": {},
            "재무상태표": {},
            "현금흐름표": {},
            "재무비율": {},
            "메타정보": {
                "data_source": "cF1001",
                "extraction_method": "regex_parsing",
                "total_items": len(financial_data),
                "years_covered": len(years),
                "collected_at": datetime.now().isoformat()
            }
        }

        # 6. 항목별 분류
        income_items = [
            '매출액', '영업이익', '영업이익(발표기준)', '세전계속사업이익', '당기순이익', '당기순이익(지배)',
            '당기순이익(비지배)'
        ]
        balance_items = [
            '자산총계', '부채총계', '자본총계', '자본총계(지배)', '자본총계(비지배)', '자본금'
        ]
        cashflow_items = [
            '영업활동현금흐름', '투자활동현금흐름', '재무활동현금흐름', 'CAPEX', 'FCF', '이자발생부채'
        ]
        ratio_items = [
            '영업이익률', '순이익률', 'ROE(%)', 'ROA(%)', '부채비율', '자본유보율', 'EPS(원)',
            'PER(배)', 'BPS(원)', 'PBR(배)', '현금DPS(원)', '현금배당수익률', '현금배당성향(%)',
            '발행주식수(보통주)'
        ]

        for item, data in financial_data.items():
            if item in income_items:
                classified_data["손익계산서"][item] = data
            elif item in balance_items:
                classified_data["재무상태표"][item] = data
            elif item in cashflow_items:
                classified_data["현금흐름표"][item] = data
            elif item in ratio_items:
                classified_data["재무비율"][item] = data
            else:
                classified_data["재무비율"][item] = data  # 기본적으로 재무비율에 포함

        return classified_data

    except Exception as e:
        print(f"❌ cF1001 파싱 오류: {e}")
        return {"error": f"cF1001 파싱 실패: {e}"}


def test_cf1001_parsing():
    """수정된 파싱 로직 테스트"""

    # 삼성전자 cF1001 URL (최신 토큰 - 즉시 업데이트)
    cf1001_url = "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=005930&fin_typ=0&freq_typ=A&encparam=dHdQZzdCY0doQ3czNGFGUXJQODRDUT09&id=ZTRzQlVCd0"

    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    print("🔍 수정된 cF1001 파싱 로직 테스트")

    try:
        # HTML 다운로드
        response = requests.get(cf1001_url, headers=headers, timeout=15)
        response.raise_for_status()

        html_content = response.content.decode('euc-kr', errors='ignore')
        print(f"✅ HTML 다운로드 성공 ({len(html_content)} 문자)")

        if len(html_content) == 0:
            print("❌ HTML 내용이 비어있음 - 토큰 만료 가능성")
            return None

        # 수정된 파싱 로직 적용
        financial_data = parse_cf1001_data_fixed(html_content)

        if "error" in financial_data:
            print(f"❌ 파싱 실패: {financial_data['error']}")
            return None

        # 결과 출력
        print(f"\n🎉 파싱 성공!")
        print(f"📊 추출된 재무제표:")

        for category, items in financial_data.items():
            if category != "메타정보":
                print(f"   📈 {category}: {len(items)}개 항목")

                # 각 카테고리의 샘플 데이터 출력
                sample_count = 0
                for item, years_data in items.items():
                    if sample_count < 3:  # 처음 3개만 출력
                        sample_years = list(years_data.keys())[:3]
                        sample_values = [
                            f"{year}: {years_data[year]}"
                            for year in sample_years
                        ]
                        print(f"      • {item}: {', '.join(sample_values)}")
                        sample_count += 1

                if len(items) > 3:
                    print(f"      ... 외 {len(items)-3}개 항목")

        print(f"\n📊 메타정보:")
        meta = financial_data.get("메타정보", {})
        print(f"   전체 항목: {meta.get('total_items', 0)}개")
        print(f"   연도 범위: {meta.get('years_covered', 0)}개 연도")

        return financial_data

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        return None


if __name__ == "__main__":
    result = test_cf1001_parsing()

    if result:
        print(f"\n💾 결과를 JSON 파일로 저장할까요? (y/n)")
        save_choice = input().strip().lower()

        if save_choice == 'y':
            import json
            with open('cf1001_parsed_result.json', 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✅ 결과 저장: cf1001_parsed_result.json")
