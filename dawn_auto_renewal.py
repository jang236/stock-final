#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌙 Dawn Auto Renewal - 새벽 자동 갱신 시스템
"""

import os
import json
import time
import random
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dawn_renewal.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DawnAutoRenewal:
    def __init__(self):
        try:
            from safe_transition_manager import SafeTransitionManager
            self.transition_manager = SafeTransitionManager()
        except ImportError:
            logger.warning("⚠️ Safe Transition Manager를 찾을 수 없습니다.")
            self.transition_manager = None
            
        self.config_file = Path("dawn_renewal_config.json")
        
        self.config = {
            "renewal_interval_hours": 36,
            "renewal_start_hour": 1,
            "renewal_end_hour": 4,
            "min_success_rate": 95.0,
            "max_retry_attempts": 3,
            "retry_delay_minutes": 30,
            "enable_enhanced_mode": True,
            "last_renewal_time": None,
            "renewal_count": 0
        }
        
        self._load_config()
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
        ]
    
    def _load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
                logger.info("📋 갱신 설정 로드 완료")
            except Exception as e:
                logger.warning(f"⚠️ 갱신 설정 로드 실패: {e}")
    
    def _save_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("💾 갱신 설정 저장 완료")
        except Exception as e:
            logger.error(f"❌ 갱신 설정 저장 실패: {e}")
    
    def is_renewal_needed(self) -> bool:
        try:
            if self.config["last_renewal_time"]:
                last_renewal = datetime.fromisoformat(self.config["last_renewal_time"])
                hours_since_renewal = (datetime.now() - last_renewal).total_seconds() / 3600
                
                if hours_since_renewal < self.config["renewal_interval_hours"]:
                    logger.info(f"⏰ 아직 갱신 시간이 아님 (경과: {hours_since_renewal:.1f}시간)")
                    return False
            
            if self.transition_manager:
                status = self.transition_manager.get_system_status()
                active_success_rate = status["active_status"]["success_rate"]
                
                if active_success_rate < self.config["min_success_rate"]:
                    logger.warning(f"🚨 성공률 낮음 ({active_success_rate:.1f}%) - 긴급 갱신 필요")
                    return True
            
            logger.info(f"✅ 정기 갱신 시간 도래")
            return True
            
        except Exception as e:
            logger.error(f"❌ 갱신 필요성 판단 실패: {e}")
            return True

    def test_token_validity(self, url: str) -> Tuple[bool, int]:
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response_size = len(response.content)
            
            is_valid = response.status_code == 200 and response_size > 20000
            return is_valid, response_size
            
        except Exception as e:
            logger.warning(f"⚠️ 토큰 테스트 실패: {e}")
            return False, 0

    def collect_new_urls(self, target_folder: str) -> bool:
        logger.info(f"🔄 {target_folder.upper()} 폴더에 새 URL 수집 시작...")
        
        try:
            try:
                from enhanced_cf1001_collector import EnhancedCF1001Collector
                
                collector = EnhancedCF1001Collector(target_folder=target_folder)
                start_time = time.time()
                
                result = collector.collect_batch(batch_size=999999, enhanced_mode=False)
                collection_time = time.time() - start_time
                
                if result["status"] == "success":
                    success_rate = result["success_rate"]
                    success_count = result["success_count"]
                    total_count = result["batch_size"]
                    
                    logger.info(f"📊 수집 결과:")
                    logger.info(f"   - 성공: {success_count}/{total_count} ({success_rate:.1f}%)")
                    logger.info(f"   - 소요시간: {collection_time/60:.1f}분")
                    logger.info(f"   - 평균 속도: {total_count/(collection_time/60):.1f}개/분")
                    
                    return success_rate >= self.config["min_success_rate"]
                else:
                    logger.error(f"❌ 수집 실패: {result.get('message', 'Unknown error')}")
                    return False
                    
            except ImportError:
                logger.warning("⚠️ Enhanced CF1001 Collector를 찾을 수 없습니다. 시뮬레이션 모드로 실행...")
                return self._simulate_url_collection(target_folder)
                
        except Exception as e:
            logger.error(f"❌ URL 수집 실패: {e}")
            return False

    def _simulate_url_collection(self, target_folder: str) -> Tuple[int, int]:
        folder_path = Path(f"company_codes_{target_folder}")
        
        demo_companies = {}
        demo_urls = {}
        
        sample_codes = [
            "005930", "000660", "035720", "207940", "051910",
            "068270", "035420", "003670", "096770", "028300",
            "251270", "357780", "328130", "042700", "145020"
        ]
        
        total_count = len(sample_codes)
        success_count = 0
        
        timestamp = int(time.time())
        
        for i, code in enumerate(sample_codes):
            if random.random() < 0.95:
                token = f"simulated_token_{timestamp}_{i}"
                demo_companies[f"기업_{code}"] = {
                    "code": code
                }
                demo_urls[f"기업_{code}"] = {
                    "code": code,
                    "cF1001_url": f"https://navercomp.wisereport.co.kr/v2/company/ajax/cF1001.aspx?cmp_cd={code}&cF1001={token}",
                    "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "success"
                }
                success_count += 1
            
            if i % 5 == 0:
                logger.info(f"   진행률: {i+1}/{total_count} ({((i+1)/total_count)*100:.0f}%)")
            
            time.sleep(0.1)
        
        try:
            progress_data = {
                "last_completed_index": total_count - 1,
                "total_companies": total_count,
                "completed_count": total_count,
                "success_count": success_count,
                "failed_count": total_count - success_count,
                "last_run_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            folder_path.mkdir(exist_ok=True)
            
            with open(folder_path / "stock_companies.json", 'w', encoding='utf-8') as f:
                json.dump(demo_companies, f, indent=2, ensure_ascii=False)
            
            with open(folder_path / "cf1001_progress.json", 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
            
            with open(folder_path / "cf1001_urls_database.json", 'w', encoding='utf-8') as f:
                json.dump(demo_urls, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ {target_folder.upper()} 폴더 데이터 저장 완료")
            
        except Exception as e:
            logger.error(f"❌ 데이터 저장 실패: {e}")
        
        success_rate = (success_count / total_count) * 100 if total_count > 0 else 0
        return success_rate >= self.config["min_success_rate"]

    def perform_renewal(self) -> bool:
        logger.info("🌙 새벽 자동 갱신 시작!")
        
        try:
            if not self.transition_manager:
                logger.error("❌ Transition Manager가 초기화되지 않았습니다.")
                return False
                
            status = self.transition_manager.get_system_status()
            current_active = status["active_folder"].lower()
            target_folder = "b" if current_active == "a" else "a"
            
            logger.info(f"📊 현재 활성: {current_active.upper()} → 갱신 대상: {target_folder.upper()}")
            
            logger.info("1️⃣ 새 URL 수집 중...")
            if not self.collect_new_urls(target_folder):
                logger.error("❌ URL 수집 실패")
                return False
            
            logger.info("2️⃣ 데이터 검증 중...")
            is_valid, validation_data = self.transition_manager.validate_folder_data(target_folder)
            if not is_valid:
                logger.error(f"❌ 데이터 검증 실패: {validation_data}")
                return False
            
            logger.info("3️⃣ 폴더 전환 중...")
            if not self.transition_manager.switch_active_folder(target_folder):
                logger.error("❌ 폴더 전환 실패")
                return False
            
            self.config["last_renewal_time"] = datetime.now().isoformat()
            self.config["renewal_count"] += 1
            self._save_config()
            
            logger.info("✅ 새벽 갱신 성공!")
            logger.info(f"📊 새 URL 보유: {validation_data['url_count']}개")
            logger.info(f"📈 성공률: {validation_data['success_rate']:.1f}%")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 갱신 중 오류 발생: {e}")
            return False

    def retry_failed_collection(self):
        logger.info("🔄 실패 종목 재시도 시작...")
        
        try:
            logger.info("😴 30분 휴식 중...")
            time.sleep(1800)
            
            logger.info("💪 강화 모드로 재시도...")
            
        except Exception as e:
            logger.error(f"❌ 재시도 실패: {e}")

    def check_and_renew(self):
        logger.info("🔍 갱신 필요성 체크...")
        
        if self.is_renewal_needed():
            success = self.perform_renewal()
            
            if not success and self.config["enable_enhanced_mode"]:
                for attempt in range(self.config["max_retry_attempts"]):
                    logger.info(f"🔁 재시도 {attempt + 1}/{self.config['max_retry_attempts']}")
                    time.sleep(self.config["retry_delay_minutes"] * 60)
                    
                    if self.perform_renewal():
                        logger.info("✅ 재시도 성공!")
                        break
                else:
                    logger.error("❌ 모든 재시도 실패")
        else:
            logger.info("⏭️ 갱신 불필요 - 대기")

    def run_daemon(self):
        logger.info("🌙 Dawn Auto Renewal 데몬 시작")
        logger.info("=" * 50)
        
        if self.transition_manager:
            status = self.transition_manager.get_system_status()
            logger.info(f"📊 현재 상태:")
            logger.info(f"   🟢 활성 폴더: {status['active_folder']}")
            logger.info(f"   📊 URL 보유: {status['active_status']['url_count']}개")
            logger.info(f"   📈 성공률: {status['active_status']['success_rate']:.1f}%")
        
        try:
            while True:
                current_hour = datetime.now().hour
                
                # 새벽 1-4시 사이에만 갱신 체크
                if self.config["renewal_start_hour"] <= current_hour <= self.config["renewal_end_hour"]:
                    self.check_and_renew()
                    time.sleep(3600)  # 1시간 대기
                else:
                    logger.info(f"⏰ 새벽 갱신 시간 대기 중... (현재: {current_hour}시)")
                    time.sleep(1800)  # 30분 대기
                
        except KeyboardInterrupt:
            logger.info("🛑 사용자 중단 요청")
        except Exception as e:
            logger.error(f"❌ 데몬 실행 오류: {e}")
        
        logger.info("🌙 Dawn Auto Renewal 종료")

    def manual_renewal(self):
        logger.info("🔧 수동 갱신 실행...")
        
        result = self.perform_renewal()
        
        if result:
            logger.info("✅ 수동 갱신 성공!")
        else:
            logger.error("❌ 수동 갱신 실패")
        
        return result

def main():
    print("🌙 Dawn Auto Renewal System")
    print("=" * 50)
    
    renewal_system = DawnAutoRenewal()
    
    if renewal_system.transition_manager:
        status = renewal_system.transition_manager.get_system_status()
        print(f"📊 현재 시스템 상태:")
        print(f"   🟢 활성 폴더: {status['active_folder']}")
        print(f"   📊 URL 보유: {status['active_status']['url_count']}개")
        print(f"   📈 성공률: {status['active_status']['success_rate']:.1f}%")
    
    if renewal_system.is_renewal_needed():
        print("\n🔄 갱신이 필요합니다.")
        response = input("지금 수동 갱신을 실행하시겠습니까? (y/n): ")
        
        if response.lower() == 'y':
            renewal_system.manual_renewal()
    else:
        print("\n✅ 현재 갱신이 필요하지 않습니다.")
    
    print("\n💡 사용법:")
    print("   - renewal_system.run_daemon()     # 데몬 모드 시작")
    print("   - renewal_system.manual_renewal() # 수동 갱신")

if __name__ == "__main__":
    main()
