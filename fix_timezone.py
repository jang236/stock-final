# 시간대 수정 스크립트
print("🕐 KST 시간대 적용 중...")

# main.py 파일 읽기
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. datetime import 부분 수정
old_import = "from datetime import datetime"
new_import = """from datetime import datetime, timezone, timedelta

# KST 시간대 설정
KST = timezone(timedelta(hours=9))

def get_kst_now():
    \"\"\"현재 KST 시간 반환\"\"\"
    return datetime.now(KST)"""

content = content.replace(old_import, new_import)

# 2. datetime.now() 호출을 get_kst_now()로 변경
content = content.replace("datetime.now().isoformat()", "get_kst_now().isoformat()")
content = content.replace("analysis_start = datetime.now()", "analysis_start = get_kst_now()")
content = content.replace("analysis_end = datetime.now()", "analysis_end = get_kst_now()")
content = content.replace("datetime.now()", "get_kst_now()")

# 3. 시간 확인 엔드포인트 추가
time_check_endpoint = '''

# 🕐 시간 확인 엔드포인트
@app.get("/check-time")
def check_time():
    """현재 서버 시간 확인"""
    import datetime as dt
    
    utc_now = dt.datetime.now(dt.timezone.utc)
    kst_now = get_kst_now()
    
    return {
        "time_check": {
            "kst_time": kst_now.isoformat(),
            "kst_readable": kst_now.strftime("%Y년 %m월 %d일 %H시 %M분"),
            "utc_time": utc_now.isoformat(),
            "timezone": "Asia/Seoul (KST +09:00)"
        },
        "current_kst": {
            "date": kst_now.strftime("%Y-%m-%d"),
            "time": kst_now.strftime("%H:%M:%S"),
            "weekday": kst_now.strftime("%A")
        }
    }'''

# if __name__ == "__main__": 이전에 엔드포인트 추가
if 'if __name__ == "__main__":' in content:
    content = content.replace('if __name__ == "__main__":', time_check_endpoint + '\n\nif __name__ == "__main__":')

# 수정된 내용 저장
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ KST 시간대 적용 완료!")
print("🔄 서버가 1-2분 내 자동 재시작됩니다.")
print("📝 테스트: /check-time 엔드포인트에서 확인")
