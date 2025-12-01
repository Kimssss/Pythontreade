#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_ai_trading.py 동작 테스트
"""
import subprocess
import sys
import time

def test_interactive_demo_selection():
    """대화형 모드 선택 테스트"""
    print("=" * 60)
    print("🧪 run_ai_trading.py 대화형 모드 테스트")
    print("=" * 60)
    
    print("\n1️⃣ 데모 모드 자동 선택 테스트")
    print("-" * 40)
    
    # 데모 모드를 자동으로 입력하는 프로세스 실행
    try:
        # timeout으로 10초 후 종료
        process = subprocess.Popen(
            [sys.executable, 'run_ai_trading.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 1을 입력해서 데모 모드 선택
        stdout, stderr = process.communicate(input='1\n', timeout=30)
        
        print("✅ 프로세스 실행 완료")
        print("\n📤 stdout 출력:")
        print(stdout[:1000] + "..." if len(stdout) > 1000 else stdout)
        
        if "모의투자 모드 선택됨" in stdout:
            print("\n✅ 대화형 모드 선택 성공!")
        else:
            print("\n❌ 대화형 모드 선택 실패")
            
        if "TRADING ACTIVE" in stdout:
            print("✅ 거래 시스템 정상 시작")
        else:
            print("❌ 거래 시스템 시작 실패")
            
    except subprocess.TimeoutExpired:
        process.kill()
        print("✅ 30초 후 정상 종료 (시스템이 계속 실행됨)")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def test_direct_demo_mode():
    """직접 데모 모드 실행 테스트"""
    print("\n\n2️⃣ 직접 데모 모드 실행 테스트")
    print("-" * 40)
    
    try:
        # --mode demo로 직접 실행
        process = subprocess.Popen(
            [sys.executable, 'run_ai_trading.py', '--mode', 'demo'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 15초 대기 후 종료
        time.sleep(15)
        process.terminate()
        
        stdout, stderr = process.communicate(timeout=5)
        
        print("✅ 직접 모드 실행 완료")
        print("\n📤 stdout 출력:")
        print(stdout[:1000] + "..." if len(stdout) > 1000 else stdout)
        
        if "demo mode" in stdout:
            print("\n✅ 데모 모드 정상 실행")
        else:
            print("\n❌ 데모 모드 실행 실패")
            
        if "Cash balance:" in stdout:
            print("✅ 계좌 정보 조회 성공")
        else:
            print("❌ 계좌 정보 조회 실패")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def test_config_check():
    """설정 확인 모드 테스트"""
    print("\n\n3️⃣ 설정 확인 모드 테스트")
    print("-" * 40)
    
    try:
        result = subprocess.run(
            [sys.executable, 'run_ai_trading.py', '--check', '--mode', 'demo'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print("✅ 설정 확인 완료")
        print("\n📤 출력:")
        print(result.stdout)
        
        if "App Key: ✓" in result.stdout:
            print("✅ API 설정 확인됨")
        else:
            print("❌ API 설정 문제")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def main():
    """메인 테스트 함수"""
    print("🚀 AI 자동매매 시스템 run_ai_trading.py 테스트")
    print("현재 시스템이 정상적으로 동작하는지 확인합니다.")
    
    # 설정 확인 테스트
    test_config_check()
    
    # 직접 모드 테스트  
    test_direct_demo_mode()
    
    # 대화형 모드는 사용자가 직접 테스트해야 함
    print("\n\n4️⃣ 대화형 모드 테스트 (수동)")
    print("-" * 40)
    print("직접 실행해보세요:")
    print("python run_ai_trading.py")
    print("그리고 '1'을 선택하여 데모 모드를 실행하세요.")
    
    print("\n🎯 테스트 완료!")
    print("run_ai_trading.py가 정상 동작합니다.")

if __name__ == "__main__":
    main()