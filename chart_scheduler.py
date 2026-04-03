"""
📅 차트 데이터 일일 자동 업데이트 스케줄러
매일 15:40 KST (장 마감 직후)에 chart_collector.daily_update() 실행
main.py에서 start_chart_scheduler()를 호출하면 백그라운드로 동작
"""
import threading
import time
from datetime import datetime, timedelta, timezone

KST = timezone(timedelta(hours=9))

def start_chart_scheduler():
    """차트 데이터 일일 업데이트 스케줄러 시작 (백그라운드 스레드)"""
    def scheduler_loop():
        print("📅 차트 스케줄러 시작 - 매일 15:40 KST 업데이트 (장 마감 직후)")
        while True:
            now = datetime.now(KST)
            # 다음 15:40 KST 계산 (장 마감 15:30 직후)
            target = now.replace(hour=15, minute=40, second=0, microsecond=0)
            if now >= target:
                target += timedelta(days=1)

            wait_seconds = (target - now).total_seconds()
            hours = int(wait_seconds // 3600)
            mins = int((wait_seconds % 3600) // 60)
            print(f"  ⏰ 다음 업데이트: {target.strftime('%Y-%m-%d %H:%M')} KST ({hours}시간 {mins}분 후)")

            # 대기 (1분마다 체크하여 프로세스 종료 시 빠르게 반응)
            while (target - datetime.now(KST)).total_seconds() > 0:
                time.sleep(60)

            # 일일 업데이트 실행
            try:
                print(f"\n🔄 일일 차트 업데이트 시작: {datetime.now(KST).strftime('%Y-%m-%d %H:%M')}")
                from chart_collector import ChartCollector
                collector = ChartCollector()
                collector.daily_update(delay=0.3)
                print(f"✅ 일일 차트 업데이트 완료: {datetime.now(KST).strftime('%Y-%m-%d %H:%M')}")
            except Exception as e:
                print(f"❌ 일일 차트 업데이트 실패: {e}")

    thread = threading.Thread(target=scheduler_loop, daemon=True, name="chart-scheduler")
    thread.start()
    return thread


if __name__ == "__main__":
    # 테스트용: 단독 실행
    print("차트 스케줄러 테스트 모드")
    start_chart_scheduler()
    # 메인 스레드 유지
    while True:
        time.sleep(3600)
