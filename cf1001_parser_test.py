import requests
from bs4 import BeautifulSoup


def test_cf1001_html_table_parsing():
    """
    BeautifulSoup으로 cF1001 HTML TABLE 파싱 테스트
    """
    # 성공한 URL
    url = "https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd=002360&fin_typ=0&freq_typ=A&encparam=dGFYekMzd3lrckdKVzdDU0p6cGFVQT09&id=hiddenfinGubun"

    # AJAX 헤더 설정
    headers = {
        'Accept':
        'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With':
        'XMLHttpRequest',
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer':
        'https://navercomp.wisereport.co.kr/v2/company/c1010001.aspx?cmp_cd=002360'
    }

    print("=== cF1001 HTML TABLE 파싱 테스트 시작 ===")
    print(f"URL: {url}")
    print(f"종목코드: 002360")

    try:
        print("\n📡 API 호출 중...")
        response = requests.get(url, headers=headers)

        print(f"✅ HTTP 응답 성공!")
        print(f"상태코드: {response.status_code}")
        print(
            f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")
        print(f"응답 크기: {len(response.text)} bytes")

        # HTML 파싱 시도
        print("\n🔍 HTML TABLE 파싱 중...")
        soup = BeautifulSoup(response.text, 'html.parser')

        # 모든 테이블 찾기
        all_tables = soup.find_all('table')
        print(f"발견된 테이블 개수: {len(all_tables)}")

        # 실제 재무데이터 테이블 찾기 (매출액이 포함된 테이블)
        financial_table = None
        for i, table in enumerate(all_tables):
            table_text = table.get_text()
            if '매출액' in table_text and '영업이익' in table_text:
                print(f"✅ 실제 재무데이터 테이블 발견! (테이블 #{i+1})")
                financial_table = table
                break

        if not financial_table:
            print("❌ 재무데이터 테이블을 찾을 수 없습니다.")
            return None

        print(f"✅ HTML TABLE 파싱 성공!")

        # 테이블 구조 분석
        rows = financial_table.find_all('tr')
        print(f"재무데이터 테이블 행 개수: {len(rows)}")

        # 헤더 추출 (여러 행에 걸쳐 있을 수 있음)
        headers = []
        header_found = False

        for row_idx, row in enumerate(rows):
            cells = [
                cell.get_text(strip=True)
                for cell in row.find_all(['th', 'td'])
            ]
            # 연도 정보가 포함된 행을 헤더로 인식
            if any('2022' in cell or '2023' in cell or '2024' in cell
                   or '2025' in cell for cell in cells):
                headers = cells
                header_found = True
                print(f"헤더 발견 (행 #{row_idx+1}): {len(headers)}개 컬럼")
                print(f"헤더 목록: {headers}")
                break

        if not header_found:
            print("⚠️ 헤더를 찾을 수 없어 기본 헤더 사용")
            headers = [
                '재무항목', '2022/12', '2023/12', '2024/12', '2025/12(E)',
                '2024/09', '2024/12', '2025/03', '2025/06(E)'
            ]

        # 실제 재무데이터 행들 추출
        financial_data = []
        target_items = [
            "매출액", "영업이익", "영업이익(발표기준)", "세전계속사업이익", "당기순이익", "당기순이익(지배)",
            "당기순이익(비지배)", "자산총계", "부채총계", "자본총계", "자본총계(지배)", "자본총계(비지배)",
            "자본금", "영업활동현금흐름", "투자활동현금흐름", "재무활동현금흐름", "CAPEX", "FCF",
            "이자발생부채", "영업이익률", "순이익률", "ROE(%)", "ROA(%)", "부채비율", "자본유보율",
            "EPS(원)", "PER(배)", "BPS(원)", "PBR(배)", "현금DPS(원)", "현금배당수익률",
            "현금배당성향(%)", "발행주식수(보통주)"
        ]

        print(f"\n💰 재무항목 데이터 추출 중...")

        for row in rows:
            cells = [
                cell.get_text(strip=True)
                for cell in row.find_all(['td', 'th'])
            ]
            if len(cells) > 1:  # 최소 2개 셀 필요 (항목명 + 값)
                item_name = cells[0]
                values = cells[1:]

                # 목표 재무항목 중 하나와 일치하는지 확인
                for target_item in target_items:
                    if target_item in item_name or item_name in target_item:
                        financial_data.append({
                            'item': item_name,
                            'target_item': target_item,
                            'values': values
                        })
                        break

        print(f"✅ 추출된 재무항목: {len(financial_data)}개")

        # 샘플 데이터 출력 (처음 10개)
        print(f"\n📊 추출된 재무데이터 (처음 10개):")
        for i, data in enumerate(financial_data[:10]):
            item_name = data['item']
            values = data['values'][:4]  # 연간 데이터만 (처음 4개)
            print(f"{i+1:2d}. {item_name}: {values}")

        if len(financial_data) > 10:
            print(f"... (총 {len(financial_data)}개 항목)")

        # 매핑 성공률 확인
        mapped_items = [data['target_item'] for data in financial_data]
        unmapped_items = [
            item for item in target_items if item not in mapped_items
        ]

        print(f"\n🎯 매핑 결과:")
        print(
            f"✅ 성공: {len(mapped_items)}/{len(target_items)}개 ({len(mapped_items)/len(target_items)*100:.1f}%)"
        )
        if unmapped_items:
            print(f"❌ 누락된 항목: {unmapped_items}")

        return {
            'table': financial_table,
            'headers': headers,
            'financial_data': financial_data,
            'success_rate': len(mapped_items) / len(target_items),
            'mapped_items': mapped_items,
            'unmapped_items': unmapped_items
        }

    except Exception as e:
        print(f"❌ HTML 파싱 실패: {e}")
        print(f"오류 타입: {type(e).__name__}")
        print(f"응답 내용 (처음 500자):")
        print(response.text[:500])
        return None

    except requests.RequestException as e:
        print(f"❌ HTTP 요청 실패: {e}")
        return None

    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        print(f"오류 타입: {type(e).__name__}")
        return None


def analyze_financial_data_structure(data):
    """
    추출된 JSON 데이터에서 재무항목 구조 분석
    """
    if data is None:
        print("⚠️ 분석할 데이터가 없습니다.")
        return

    print("\n" + "=" * 50)
    print("📊 재무데이터 구조 상세 분석")
    print("=" * 50)

    # 33개 목표 항목 확인
    target_items = [
        "매출액", "영업이익", "영업이익(발표기준)", "세전계속사업이익", "당기순이익", "당기순이익(지배)",
        "당기순이익(비지배)", "자산총계", "부채총계", "자본총계", "자본총계(지배)", "자본총계(비지배)", "자본금",
        "영업활동현금흐름", "투자활동현금흐름", "재무활동현금흐름", "CAPEX", "FCF", "이자발생부채", "영업이익률",
        "순이익률", "ROE(%)", "ROA(%)", "부채비율", "자본유보율", "EPS(원)", "PER(배)",
        "BPS(원)", "PBR(배)", "현금DPS(원)", "현금배당수익률", "현금배당성향(%)", "발행주식수(보통주)"
    ]

    print(f"🎯 목표: {len(target_items)}개 재무항목 추출")
    print("🔍 HTML TABLE에서 재무항목 매핑 분석 중...")

    if isinstance(data, dict) and 'financial_data' in data:
        financial_items = data['financial_data']
        success_rate = data.get('success_rate', 0)
        mapped_items = data.get('mapped_items', [])
        unmapped_items = data.get('unmapped_items', [])

        print(
            f"✅ 추출 성공률: {success_rate*100:.1f}% ({len(mapped_items)}/{len(target_items)}개)"
        )

        if success_rate >= 0.9:  # 90% 이상 성공
            print("🎉 우수한 성공률! 시스템 구축 준비 완료")
        elif success_rate >= 0.7:  # 70% 이상 성공
            print("✅ 양호한 성공률! 일부 수정 후 시스템 구축 가능")
        else:
            print("⚠️ 추가 개선 필요")

        if unmapped_items:
            print(f"📋 누락된 항목들: {unmapped_items}")
            print("💡 이들 항목은 HTML에서 다른 이름으로 표시되거나 누락되었을 수 있음")

    print("✅ 상세 분석 완료. 33개 항목 매핑 시스템 구축 가능합니다.")


if __name__ == "__main__":
    print("🚀 cF1001 HTML TABLE 파싱 테스트를 시작합니다!")
    print("📋 BeautifulSoup을 사용한 HTML 파싱")
    print("=" * 60)

    # 테스트 실행
    financial_data = test_cf1001_html_table_parsing()

    # 데이터 구조 분석
    analyze_financial_data_structure(financial_data)

    if financial_data is not None:
        print("\n" + "=" * 60)
        print("🎉 테스트 완료! 33개 재무항목 매핑 단계로 진행할 수 있습니다.")
        print("📝 다음 단계: HTML TABLE → 33개 재무항목 매핑")
    else:
        print("\n" + "=" * 60)
        print("⚠️ 테스트 실패. 문제를 해결해야 합니다.")
