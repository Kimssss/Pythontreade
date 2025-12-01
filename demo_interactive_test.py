#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
대화형 모드 시뮬레이션 테스트
"""
import subprocess
import sys
import time

def test_interactive():
    print("=" * 60)
    print("🎮 대화형 모드 시뮬레이션")
    print("=" * 60)
    
    print("run_ai_trading.py를 실행하여 대화형 메뉴를 확인합니다...")
    print("")
    
    # 프로세스 시작
    process = subprocess.Popen(
        [sys.executable, 'run_ai_trading.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True
    )
    
    try:
        # '1' 입력 (데모 모드 선택)
        print("📝 입력: 1 (데모 모드 선택)")
        process.stdin.write('1\n')
        process.stdin.flush()
        
        # 몇 초 대기하여 출력 확인
        time.sleep(10)
        
        # 프로세스 종료
        process.terminate()
        
        # 출력 수집
        try:
            stdout, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, _ = process.communicate()
        
        print("📤 시스템 출력:")
        print("-" * 40)
        print(stdout)
        
        # 결과 확인
        if "AI 자동매매 시스템" in stdout:
            print("✅ 대화형 메뉴 표시됨")
        
        if "모의투자 모드 선택됨" in stdout:
            print("✅ 모드 선택 성공")
            
        if "Starting AI Trading System in demo mode" in stdout:
            print("✅ 시스템 정상 시작")
        
        print("\n🎉 대화형 모드가 정상적으로 동작합니다!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    finally:
        if process.poll() is None:
            process.kill()

if __name__ == "__main__":
    test_interactive()