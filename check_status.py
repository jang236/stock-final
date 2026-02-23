#!/usr/bin/env python3
"""📊 상태 체크 스크립트"""

from safe_transition_manager import SafeTransitionManager
from datetime import datetime

def check_status():
    manager = SafeTransitionManager()
    status = manager.get_system_status()
    
    print("📊 현재 시스템 상태")
    print("=" * 30)
    print(f"🟢 활성 폴더: {status['active_folder']}")
    print(f"📊 URL 보유: {status['active_status']['url_count']}개")
    print(f"📈 성공률: {status['active_status']['success_rate']:.1f}%")
    print(f"🔄 전환 횟수: {status['switch_count']}회")
    print(f"⏰ 체크 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    check_status()
