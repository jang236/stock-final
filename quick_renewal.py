#!/usr/bin/env python3
"""🚀 원클릭 갱신 스크립트"""

from safe_transition_manager import SafeTransitionManager
from enhanced_cf1001_collector import EnhancedCF1001Collector

def quick_renewal():
    print("🚀 원클릭 갱신 시작!")
    
    # 1. 현재 상태 확인
    manager = SafeTransitionManager()
    status = manager.get_system_status()
    current_active = status["active_folder"].lower()
    target_folder = "b" if current_active == "a" else "a"
    
    print(f"📊 현재 활성: {current_active.upper()} → 갱신 대상: {target_folder.upper()}")
    
    # 2. 새 URL 수집
    print(f"🔄 {target_folder.upper()} 폴더에 새 URL 수집...")
    collector = EnhancedCF1001Collector(target_folder=target_folder)
    result = collector.collect_batch(batch_size=50)
    
    if result["status"] == "success" and result["success_rate"] >= 95:
        print(f"✅ URL 수집 성공: {result['success_rate']:.1f}%")
        
        # 3. A↔B 전환
        print(f"🔄 {current_active.upper()}→{target_folder.upper()} 전환...")
        if manager.switch_active_folder(target_folder):
            print("🎉 갱신 완료!")
            return True
        else:
            print("❌ 전환 실패")
            return False
    else:
        print("❌ URL 수집 실패")
        return False

if __name__ == "__main__":
    quick_renewal()
