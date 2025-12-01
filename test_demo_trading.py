#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데모 모드 테스트 - 미국주식 거래 확인
"""
import subprocess
import sys
import time
import re

def test_demo_mode():
    print("=" * 60)
    print("🔍 데모 모드 실행 및 미국주식 거래 확인")
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
    
    # 로그 패턴
    patterns = {
        'us_market': re.compile(r'(US Market|미국|overseas)', re.I),
        'trading_cycle': re.compile(r'Trading Cycle|거래 사이클'),
        'error_500': re.compile(r'500 에러|초당 거래건수'),
        'us_trading': re.compile(r'Trading US Stocks|미국 주식'),
        'us_stocks': re.compile(r'(AAPL|MSFT|GOOGL|AMZN|TSLA|NASDAQ|NYSE)'),
        'buy_sell': re.compile(r'(BUY|SELL|매수|매도|Buying US stock)')
    }
    
    found_patterns = {k: [] for k in patterns.keys()}
    
    try:
        # 데모 모드 선택
        process.stdin.write('1\n')
        process.stdin.flush()
        print("✅ 데모 모드 선택됨")
        
        # 60초 동안 로그 수집
        print("\n📊 로그 모니터링 중... (60초)")
        start_time = time.time()
        
        while time.time() - start_time < 60:
            line = process.stdout.readline()
            if not line:
                break
                
            # 패턴 매칭
            for key, pattern in patterns.items():
                if pattern.search(line):
                    found_patterns[key].append(line.strip())
                    print(f"  [{key}] {line.strip()}")
        
        # 프로세스 종료
        process.terminate()
        process.wait(timeout=5)
        
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
    except Exception as e:
        print(f"❌ 오류: {e}")
        if process.poll() is None:
            process.kill()
    
    # 결과 분석
    print("\n" + "=" * 60)
    print("📋 분석 결과:")
    print("=" * 60)
    
    issues = []
    
    # 1. 500 에러 확인
    if found_patterns['error_500']:
        print(f"❌ 500 에러 발견: {len(found_patterns['error_500'])}건")
        for err in found_patterns['error_500'][:3]:
            print(f"   - {err}")
        issues.append("500 에러가 여전히 발생함")
    else:
        print("✅ 500 에러 없음")
    
    # 2. 미국 시장 활성화 확인
    if found_patterns['us_market']:
        print(f"✅ US 마켓 활성화 확인: {len(found_patterns['us_market'])}건")
    else:
        print("❌ US 마켓 활성화 없음")
        issues.append("미국 시장이 활성화되지 않음")
    
    # 3. 미국주식 거래 확인
    if found_patterns['us_trading']:
        print(f"✅ 미국주식 거래 로직 실행: {len(found_patterns['us_trading'])}건")
        if found_patterns['us_stocks']:
            print(f"✅ 미국 종목 확인: {len(found_patterns['us_stocks'])}건")
        else:
            print("❌ 미국 종목 분석 없음")
            issues.append("미국 종목 분석이 실행되지 않음")
    else:
        print("❌ 미국주식 거래 로직 미실행")
        issues.append("미국주식 거래 로직이 실행되지 않음")
    
    # 4. 실제 매매 확인
    if found_patterns['buy_sell']:
        print(f"✅ 매수/매도 시도: {len(found_patterns['buy_sell'])}건")
        for trade in found_patterns['buy_sell'][:3]:
            print(f"   - {trade}")
    else:
        print("⚠️  매수/매도 시도 없음")
    
    # 개선 필요사항
    if issues:
        print("\n🔧 개선 필요사항:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("\n✅ 모든 기능 정상 작동!")

if __name__ == "__main__":
    test_demo_mode()