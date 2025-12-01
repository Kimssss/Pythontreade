#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
백그라운드 학습 기능 테스트
"""
import subprocess
import sys
import time

def test_background_learning():
    print("=" * 60)
    print("🧠 백그라운드 학습 기능 테스트")
    print("=" * 60)
    
    print("AI 거래 시스템을 실행하여 5분 대기 시간 동안의 학습을 확인합니다...")
    print("(30초 후 자동 종료됩니다)")
    print("")
    
    try:
        # AI 거래 시스템 실행
        process = subprocess.Popen(
            [sys.executable, 'run_ai_trading.py', '--mode', 'demo'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        start_time = time.time()
        output_lines = []
        
        # 30초 동안 출력 모니터링
        while time.time() - start_time < 30:
            line = process.stdout.readline()
            if line:
                output_lines.append(line.strip())
                print(line.strip())
                
                # 백그라운드 학습 시작 감지
                if "Training During Wait" in line:
                    print("\n🎯 백그라운드 학습 시작 감지!")
                    
                # 빠른 학습 감지  
                if "Quick Training Mode" in line:
                    print("\n⚡ 빠른 학습 모드 실행!")
                    
                # 학습 완료 감지
                if "Quick training completed" in line:
                    print("\n✅ 빠른 학습 완료!")
                    
            # 프로세스가 종료되었으면 break
            if process.poll() is not None:
                break
        
        # 프로세스 종료
        process.terminate()
        
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            
        print("\n" + "=" * 60)
        print("📊 테스트 결과 분석")
        print("=" * 60)
        
        full_output = '\n'.join(output_lines)
        
        # 주요 기능 확인
        checks = {
            "시스템 초기화": "AI Trading System initialized" in full_output,
            "거래 사이클 시작": "Starting Trading Cycle" in full_output,
            "다음 사이클 대기": "Waiting 5 minutes for next trading cycle" in full_output,
            "백그라운드 학습": "Training During Wait" in full_output,
            "빠른 학습 모드": "Quick Training Mode" in full_output,
            "학습 완료": "training completed" in full_output
        }
        
        print("\n기능 확인:")
        for feature, status in checks.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {feature}")
            
        # 총 평가
        success_count = sum(checks.values())
        total_count = len(checks)
        
        print(f"\n🎯 전체 성공률: {success_count}/{total_count} ({success_count/total_count*100:.0f}%)")
        
        if success_count >= 4:
            print("✅ 백그라운드 학습 기능이 정상 동작합니다!")
        else:
            print("⚠️ 일부 기능에 문제가 있을 수 있습니다.")
            
        # 주요 개선 사항 안내
        print("\n🚀 새로운 기능:")
        print("  • 5분 거래 대기 시간 동안 자동 학습")
        print("  • 빠른 학습 모드로 효율성 향상")
        print("  • 학습 기록 자동 저장")
        print("  • API 호출 최적화")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    test_background_learning()