#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
30분 실전 모의투자 테스트
"""
import subprocess
import sys
import time
import signal
from datetime import datetime, timedelta

class LongTermTester:
    def __init__(self):
        self.process = None
        self.start_time = None
        self.test_duration = 30 * 60  # 30분
        self.error_count = 0
        self.trade_count = 0
        self.learning_count = 0
        
    def start_test(self):
        print("=" * 80)
        print("🕒 30분 실전 모의투자 테스트 시작")
        print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"종료 예정: {(datetime.now() + timedelta(minutes=30)).strftime('%H:%M:%S')}")
        print("=" * 80)
        
        self.start_time = time.time()
        
        # AI 거래 시스템 실행
        self.process = subprocess.Popen(
            [sys.executable, 'run_ai_trading.py', '--mode', 'demo'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        try:
            self.monitor_process()
        except KeyboardInterrupt:
            print("\n⚠️ 사용자가 테스트를 중단했습니다.")
        finally:
            self.cleanup()
    
    def monitor_process(self):
        """프로세스 모니터링 및 로그 분석"""
        error_patterns = [
            "500 에러",
            "Error in main loop",
            "Failed to",
            "❌",
            "UnboundLocalError",
            "Exception"
        ]
        
        success_patterns = [
            "Quick training completed",
            "Screened",
            "TRADING ACTIVE", 
            "✅"
        ]
        
        while self.process.poll() is None:
            # 시간 확인
            elapsed = time.time() - self.start_time
            if elapsed > self.test_duration:
                print(f"\n⏰ 30분 테스트 완료!")
                break
                
            # 출력 읽기
            line = self.process.stdout.readline()
            if line:
                line = line.strip()
                
                # 진행 상황 출력 (중요한 로그만)
                if any(pattern in line for pattern in success_patterns + error_patterns):
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"[{timestamp}] {line}")
                
                # 에러 카운팅
                if any(pattern in line for pattern in error_patterns):
                    self.error_count += 1
                    if self.error_count > 50:  # 에러가 너무 많으면 중단
                        print(f"\n🚨 에러가 너무 많습니다 ({self.error_count}개). 테스트를 중단합니다.")
                        break
                
                # 성공 카운팅
                if "Quick training completed" in line:
                    self.learning_count += 1
                if "Screened" in line and "stocks" in line:
                    self.trade_count += 1
                
                # 5분마다 상태 리포트
                if int(elapsed) % 300 == 0 and int(elapsed) > 0:
                    self.print_status_report(elapsed)
            
            # CPU 부하 방지
            time.sleep(0.1)
    
    def print_status_report(self, elapsed):
        """5분마다 상태 보고"""
        minutes = int(elapsed // 60)
        remaining = int((self.test_duration - elapsed) // 60)
        
        print(f"\n" + "="*60)
        print(f"📊 {minutes}분 경과 상태 리포트")
        print(f"📊 남은 시간: {remaining}분")
        print(f"❌ 에러 발생: {self.error_count}회")
        print(f"📈 거래 사이클: {self.trade_count}회")
        print(f"🧠 학습 완료: {self.learning_count}회")
        
        # 에러율 계산
        total_events = self.error_count + self.trade_count + self.learning_count
        if total_events > 0:
            error_rate = (self.error_count / total_events) * 100
            print(f"⚠️ 에러율: {error_rate:.1f}%")
        
        print("="*60 + "\n")
    
    def cleanup(self):
        """정리 작업"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
        
        # 최종 리포트
        elapsed = time.time() - self.start_time if self.start_time else 0
        self.print_final_report(elapsed)
    
    def print_final_report(self, elapsed):
        """최종 결과 보고"""
        print("\n" + "="*80)
        print("🏁 30분 실전 테스트 최종 결과")
        print("="*80)
        
        print(f"⏱️ 실제 실행 시간: {elapsed/60:.1f}분")
        print(f"❌ 총 에러 발생: {self.error_count}회")
        print(f"📈 거래 사이클: {self.trade_count}회") 
        print(f"🧠 학습 완료: {self.learning_count}회")
        
        total_events = self.error_count + self.trade_count + self.learning_count
        if total_events > 0:
            error_rate = (self.error_count / total_events) * 100
            success_rate = ((self.trade_count + self.learning_count) / total_events) * 100
            
            print(f"\n📊 성능 지표:")
            print(f"   에러율: {error_rate:.1f}%")
            print(f"   성공율: {success_rate:.1f}%")
            
            if error_rate < 20:
                print("✅ 시스템이 안정적으로 작동합니다!")
            elif error_rate < 50:
                print("⚠️ 일부 개선이 필요합니다.")
            else:
                print("🚨 시스템에 심각한 문제가 있습니다.")
        
        print("\n📝 주요 발견 사항:")
        if self.error_count > 20:
            print("   - API 호출 빈도를 더 줄여야 합니다")
        if self.learning_count > 0:
            print(f"   - 백그라운드 학습이 {self.learning_count}회 성공했습니다")
        if self.trade_count > 0:
            print(f"   - 거래 사이클이 {self.trade_count}회 실행되었습니다")
        
        print("="*80)

def main():
    tester = LongTermTester()
    
    # 신호 처리기 설정
    def signal_handler(signum, frame):
        print("\n\n⚠️ 중단 신호를 받았습니다. 정리 중...")
        tester.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    tester.start_test()

if __name__ == "__main__":
    main()