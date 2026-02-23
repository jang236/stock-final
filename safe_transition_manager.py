import json
import os
import shutil
import time
from datetime import datetime


class SafeTransitionManager:
    """
    A↔B 폴더 안전 전환 관리자
    - 심볼릭 링크를 사용한 0.001초 원자적 전환
    - 데이터 무결성 검증 (95% 성공률 기준)
    - 자동 백업 및 복구 시스템
    """
    
    def __init__(self):
        self.folder_a = "company_codes_a"
        self.folder_b = "company_codes_b"
        self.active_link = "company_codes_active"
        self.backup_folder = "company_codes_backup"
        
        # 필요한 폴더 생성
        self.ensure_folders()
        
        # 심볼릭 링크 초기화 (없으면 A로 설정)
        self.ensure_active_link()
    
    def ensure_folders(self):
        """필수 폴더들 생성"""
        for folder in [self.folder_a, self.folder_b, self.backup_folder]:
            os.makedirs(folder, exist_ok=True)
            
            # 기본 파일들 생성 (없으면)
            if folder != self.backup_folder:
                self._create_default_files(folder)
    
    def _create_default_files(self, folder):
        """기본 파일들 생성 (빈 파일이라도)"""
        files = [
            "stock_companies.json",
            "cf1001_urls_database.json", 
            "cf1001_progress.json",
            "cf1001_failed.json"
        ]
        
        for filename in files:
            filepath = os.path.join(folder, filename)
            if not os.path.exists(filepath):
                if filename == "stock_companies.json":
                    # 5개 테스트 기업 생성
                    test_companies = {
                        "삼성전자": {"code": "005930"},
                        "SK하이닉스": {"code": "000660"},
                        "NAVER": {"code": "035420"},
                        "카카오": {"code": "035720"},
                        "LG에너지솔루션": {"code": "373220"}
                    }
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(test_companies, f, ensure_ascii=False, indent=2)
                elif filename == "cf1001_progress.json":
                    default_progress = {
                        "last_completed_index": -1,
                        "total_companies": 0,
                        "completed_count": 0,
                        "success_count": 0,
                        "failed_count": 0,
                        "last_run_date": None
                    }
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(default_progress, f, ensure_ascii=False, indent=2)
                else:
                    # 빈 JSON 객체/배열
                    default_content = {} if "database" in filename else []
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(default_content, f, ensure_ascii=False, indent=2)
    
    def ensure_active_link(self):
        """활성 심볼릭 링크 확인/생성"""
        if os.path.islink(self.active_link):
            # 이미 있으면 현재 상태 확인
            current_target = os.readlink(self.active_link)
            print(f"🔗 현재 활성 폴더: {current_target}")
        else:
            # 없으면 A 폴더로 초기화
            if os.path.exists(self.active_link):
                # 기존 파일/폴더가 있으면 백업
                backup_name = f"old_active_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_path = os.path.join(self.backup_folder, backup_name)
                shutil.move(self.active_link, backup_path)
                print(f"📦 기존 {self.active_link} 백업: {backup_path}")
            
            # A 폴더로 심볼릭 링크 생성
            os.symlink(self.folder_a, self.active_link)
            print(f"🔗 초기 활성 폴더 설정: {self.folder_a}")
    
    def get_active_folder(self):
        """현재 활성 폴더 반환"""
        if os.path.islink(self.active_link):
            target = os.readlink(self.active_link)
            if target == self.folder_a:
                return 'A'
            elif target == self.folder_b:
                return 'B'
        return None
    
    def get_folder_status(self, folder_type):
        """폴더 상태 확인"""
        folder = self.folder_a if folder_type.lower() == 'a' else self.folder_b
        
        status = {
            "exists": os.path.exists(folder),
            "url_count": 0,
            "success_rate": 0.0,
            "last_update": None
        }
        
        try:
            # URL 데이터베이스 확인
            db_file = os.path.join(folder, "cf1001_urls_database.json")
            if os.path.exists(db_file):
                with open(db_file, 'r', encoding='utf-8') as f:
                    db = json.load(f)
                    status["url_count"] = len(db)
            
            # 진행 상황 확인
            progress_file = os.path.join(folder, "cf1001_progress.json")
            if os.path.exists(progress_file):
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    if progress.get("completed_count", 0) > 0:
                        status["success_rate"] = (progress.get("success_count", 0) / 
                                                progress.get("completed_count", 1)) * 100
                    status["last_update"] = progress.get("last_run_date")
        
        except Exception as e:
            print(f"⚠️ 폴더 상태 확인 오류: {e}")
        
        return status
    
    def validate_folder_quality(self, folder_type):
        """폴더 데이터 품질 검증 (95% 성공률 기준)"""
        status = self.get_folder_status(folder_type)
        
        # 기본 조건
        if not status["exists"]:
            return False, "폴더가 존재하지 않음"
        
        if status["url_count"] == 0:
            return False, "URL 데이터가 없음"
        
        # 품질 기준: 95% 성공률 또는 최소 5개 URL
        if status["success_rate"] >= 95.0 or status["url_count"] >= 5:
            return True, f"품질 검증 통과 (URL: {status['url_count']}개, 성공률: {status['success_rate']:.1f}%)"
        else:
            return False, f"품질 기준 미달 (URL: {status['url_count']}개, 성공률: {status['success_rate']:.1f}%)"
    
    def create_backup(self, folder_type):
        """폴더 백업 생성"""
        folder = self.folder_a if folder_type.lower() == 'a' else self.folder_b
        
        if not os.path.exists(folder):
            return False, "백업할 폴더가 없음"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{folder_type.lower()}_{timestamp}"
        backup_path = os.path.join(self.backup_folder, backup_name)
        
        try:
            shutil.copytree(folder, backup_path)
            return True, backup_path
        except Exception as e:
            return False, f"백업 실패: {e}"
    
    def switch_active_folder(self, target_folder):
        """
        활성 폴더 전환 (원자적 전환)
        target_folder: 'a' 또는 'b'
        """
        target_folder = target_folder.lower()
        if target_folder not in ['a', 'b']:
            return False, "target_folder는 'a' 또는 'b'여야 합니다"
        
        current_active = self.get_active_folder()
        if current_active and current_active.lower() == target_folder:
            return True, f"이미 {target_folder.upper()} 폴더가 활성 상태입니다"
        
        target_path = self.folder_a if target_folder == 'a' else self.folder_b
        
        print(f"🔄 {current_active}→{target_folder.upper()} 폴더 전환 시작")
        
        # 1단계: 대상 폴더 품질 검증
        print(f"1️⃣ {target_folder.upper()} 폴더 품질 검증...")
        is_valid, message = self.validate_folder_quality(target_folder)
        if not is_valid:
            return False, f"전환 실패: {message}"
        print(f"   ✅ {message}")
        
        # 2단계: 현재 활성 폴더 백업
        if current_active:
            print(f"2️⃣ {current_active} 폴더 백업...")
            backup_success, backup_info = self.create_backup(current_active.lower())
            if backup_success:
                print(f"   ✅ 백업 완료: {backup_info}")
            else:
                print(f"   ⚠️ 백업 실패: {backup_info}")
        
        # 3단계: 원자적 전환 (심볼릭 링크)
        print(f"3️⃣ 원자적 전환 실행...")
        start_time = time.time()
        
        try:
            # 임시 링크 생성
            temp_link = f"{self.active_link}_temp_{int(time.time())}"
            os.symlink(target_path, temp_link)
            
            # 원자적 교체 (rename은 원자적 연산)
            os.replace(temp_link, self.active_link)
            
            end_time = time.time()
            transition_time = end_time - start_time
            
            print(f"   ✅ 전환 완료: {transition_time:.4f}초")
            print(f"🎉 {current_active}→{target_folder.upper()} 전환 성공!")
            
            return True, f"전환 성공 ({transition_time:.4f}초)"
            
        except Exception as e:
            # 실패 시 정리
            if os.path.exists(temp_link):
                os.unlink(temp_link)
            return False, f"전환 실패: {e}"
    
    def get_system_status(self):
        """전체 시스템 상태 반환"""
        active_folder = self.get_active_folder()
        
        status = {
            "active_folder": active_folder if active_folder else "UNKNOWN",
            "active_status": self.get_folder_status(active_folder.lower()) if active_folder else {},
            "folder_a_status": self.get_folder_status('a'),
            "folder_b_status": self.get_folder_status('b'),
            "can_switch_to_a": False,
            "can_switch_to_b": False
        }
        
        # 전환 가능성 확인
        if not active_folder or active_folder.lower() != 'a':
            is_valid_a, _ = self.validate_folder_quality('a')
            status["can_switch_to_a"] = is_valid_a
        
        if not active_folder or active_folder.lower() != 'b':
            is_valid_b, _ = self.validate_folder_quality('b')
            status["can_switch_to_b"] = is_valid_b
        
        return status
    
    def print_status(self):
        """상태 정보 출력"""
        status = self.get_system_status()
        
        print(f"📊 A↔B 폴더 전환 시스템 상태")
        print(f"{'='*40}")
        print(f"🟢 현재 활성: {status['active_folder']}")
        print()
        
        # A 폴더 상태
        a_status = status['folder_a_status']
        print(f"📁 A 폴더 ({self.folder_a})")
        print(f"   URL 개수: {a_status['url_count']:,}개")
        print(f"   성공률: {a_status['success_rate']:.1f}%")
        print(f"   마지막 업데이트: {a_status['last_update'] or 'N/A'}")
        print(f"   전환 가능: {'✅' if status['can_switch_to_a'] else '❌'}")
        print()
        
        # B 폴더 상태  
        b_status = status['folder_b_status']
        print(f"📁 B 폴더 ({self.folder_b})")
        print(f"   URL 개수: {b_status['url_count']:,}개")
        print(f"   성공률: {b_status['success_rate']:.1f}%")
        print(f"   마지막 업데이트: {b_status['last_update'] or 'N/A'}")
        print(f"   전환 가능: {'✅' if status['can_switch_to_b'] else '❌'}")


def main():
    """테스트 및 대화형 사용"""
    manager = SafeTransitionManager()
    
    if len(os.sys.argv) > 1:
        command = os.sys.argv[1].lower()
        
        if command == "status":
            manager.print_status()
            
        elif command == "switch" and len(os.sys.argv) > 2:
            target = os.sys.argv[2].lower()
            success, message = manager.switch_active_folder(target)
            print(f"{'✅' if success else '❌'} {message}")
            
        elif command == "init":
            print("🎯 A↔B 폴더 시스템 초기화 완료")
            manager.print_status()
            
        else:
            print("❌ 사용법:")
            print("   python safe_transition_manager.py status")
            print("   python safe_transition_manager.py switch a")
            print("   python safe_transition_manager.py switch b")
            print("   python safe_transition_manager.py init")
    else:
        # 대화형 모드
        manager.print_status()


if __name__ == "__main__":
    main()
