#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
수정사항 직접 검증 - 500 에러 확인
"""
import subprocess
import sys
import time
import re

def test_demo_with_fixes():
    print("=" * 60)
    print("🧪 데모 모드 실행 - 500 에러 확인 테스트")
    print("=" * 60)
    
    # 프로세스 시작
    process = subprocess.Popen(
        [sys.executable, 'run_ai_trading.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # 패턴 정의
    error_500_pattern = re.compile(r'500 에러|초당 거래건수')
    us_trading_pattern = re.compile(r'Buying US stock|US stock buy order|미국주식')
    module_error_pattern = re.compile(r'ModuleNotFoundError.*market_hours')
    
    error_500_count = 0
    us_trading_events = []
    module_errors = []
    
    try:
        # 데모 모드 선택
        process.stdin.write('1\n')
        process.stdin.flush()
        print("✅ 데모 모드 선택됨\n")
        
        # 90초 동안 로그 모니터링
        print("📊 로그 모니터링 중... (90초)")
        start_time = time.time()
        line_count = 0
        
        while time.time() - start_time < 90:
            line = process.stdout.readline()
            if not line:
                break
            
            line_count += 1
            
            # 500 에러 체크
            if error_500_pattern.search(line):
                error_500_count += 1
                print(f"❌ [500 ERROR #{error_500_count}] {line.strip()}")
            
            # US 거래 체크
            elif us_trading_pattern.search(line):
                us_trading_events.append(line.strip())
                print(f"🇺🇸 [US TRADE] {line.strip()}")
            
            # 모듈 에러 체크
            elif module_error_pattern.search(line):
                module_errors.append(line.strip())
                print(f"📦 [MODULE ERROR] {line.strip()}")
            
            # 중요 로그만 출력
            elif any(keyword in line for keyword in ['Trading Cycle', 'Trading US Stocks', 'successful', 'failed']):
                print(f"📌 {line.strip()}")
        
        # 프로세스 종료
        process.terminate()
        process.wait(timeout=5)
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        if process.poll() is None:
            process.kill()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    print(f"\n1️⃣ 500 에러 발생: {error_500_count}건")
    if error_500_count > 0:
        print("   ⚠️ 500 에러가 여전히 발생합니다!")
        print("   💡 권장사항:")
        print("      - global_screener.py의 sleep을 5초에서 10초로 증가")
        print("      - API 호출 간격을 더 늘려야 합니다")
    else:
        print("   ✅ 500 에러 없음!")
    
    print(f"\n2️⃣ 미국주식 거래: {len(us_trading_events)}건")
    if us_trading_events:
        print("   ✅ 미국주식 거래 실행됨:")
        for event in us_trading_events[:3]:
            print(f"      - {event}")
    else:
        print("   ❌ 미국주식 거래가 실행되지 않음")
    
    print(f"\n3️⃣ 모듈 에러: {len(module_errors)}건")
    if module_errors:
        print("   ⚠️ market_hours 모듈 에러가 여전히 발생!")
        for err in module_errors[:2]:
            print(f"      - {err}")
    else:
        print("   ✅ 모듈 에러 해결됨!")
    
    print(f"\n📈 총 처리 라인: {line_count}")
    
    # 최종 판정
    print("\n" + "=" * 60)
    if error_500_count == 0 and len(us_trading_events) > 0 and len(module_errors) == 0:
        print("🎉 모든 문제가 해결되었습니다!")
    else:
        print("⚠️ 아직 해결이 필요한 문제가 있습니다:")
        if error_500_count > 0:
            print("   - 500 에러 개선 필요")
        if len(us_trading_events) == 0:
            print("   - 미국주식 거래 로직 점검 필요")
        if len(module_errors) > 0:
            print("   - 모듈 import 에러 수정 필요")
    print("=" * 60)

if __name__ == "__main__":
    test_demo_with_fixes()