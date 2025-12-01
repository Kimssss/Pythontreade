#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
빠른 시스템 체크 - 주요 문제점 확인
"""
import os
import sys
from datetime import datetime
import time

# 환경 변수 설정
os.environ['TRADING_MODE'] = 'demo'

# 모듈 import
from ai_trading_system.main_trading_system import AITradingSystem

def check_issues():
    print("=" * 60)
    print("🔍 시스템 체크")
    print("=" * 60)
    
    # 1. 시장 시간 체크
    print("\n1. 현재 시장 상태:")
    now = datetime.now()
    hour = now.hour
    
    # 간단한 시장 시간 체크
    korean_open = 9 <= hour < 16
    us_open = hour >= 23 or hour < 6  # 겨울 시간 기준
    
    print(f"   - 한국 시장: {'열림' if korean_open else '닫힘'}")
    print(f"   - 미국 시장: {'열림' if us_open else '닫힘'}")
    print(f"   - 현재 시각: {now}")
    
    # 2. 미국 시장 시간 확인
    print("\n2. 미국 시장 거래 시간:")
    print("   - 여름(DST): 22:30 - 05:00 KST")
    print("   - 겨울: 23:30 - 06:00 KST")
    
    # 3. 현재 활성 시장 확인
    system = AITradingSystem(mode='demo')
    active = system.get_active_markets()
    print(f"\n3. 시스템이 인식한 활성 시장: {active}")
    
    # 4. 해외 API 초기화 체크
    print("\n4. 해외 API 초기화 확인:")
    try:
        system.kis_api.initialize_overseas_api()
        if hasattr(system.kis_api, 'overseas') and system.kis_api.overseas:
            print("   ✅ 해외 API 초기화 성공")
        else:
            print("   ❌ 해외 API 초기화 실패")
    except Exception as e:
        print(f"   ❌ 오류: {e}")
    
    # 5. 미국주식 거래 가능 확인
    print("\n5. 미국주식 거래 테스트:")
    if active['us']:
        print("   ✅ 미국 시장 활성화됨 - 거래 가능")
        print("   - _trade_us_stocks() 함수가 호출됨")
    else:
        print("   ❌ 미국 시장 비활성 - 거래 불가")
        print("   - 미국 시장 시간이 아니거나 설정 문제")
    
    # 6. Rate Limit 설정 확인
    print("\n6. Rate Limit 설정:")
    print("   - 국내 API: 초당 20회")
    print("   - 해외 API: 초당 2-3회 (보수적)")
    print("   - 500 에러시 대기: 2-10초")
    
    print("\n" + "=" * 60)
    print("🎯 권장사항:")
    if not active['us']:
        print("   - 미국 시장 시간(22:30-05:00)에 실행하세요")
    print("   - 500 에러 발생시 API 호출 간격을 늘려주세요")
    print("   - global_screener.py의 await asyncio.sleep(3)을 5로 늘리세요")
    print("=" * 60)

if __name__ == "__main__":
    check_issues()