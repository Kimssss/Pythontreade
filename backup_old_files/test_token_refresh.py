#!/usr/bin/env python3
"""
토큰 자동 갱신 기능 테스트 스크립트
"""

import time
from datetime import datetime, timedelta
from kis_api import KisAPI
from config import Config

def test_token_refresh():
    """토큰 자동 갱신 기능 테스트"""
    print("=== 토큰 자동 갱신 기능 테스트 ===")
    
    # 데모 계정 정보로 API 인스턴스 생성
    demo_account_info = Config.get_account_info('demo')
    api = KisAPI(
        demo_account_info['appkey'], 
        demo_account_info['appsecret'], 
        demo_account_info['account'], 
        is_real=False
    )
    
    print("1. 초기 토큰 발급 테스트")
    if api.get_access_token():
        print(f"   ✓ 초기 토큰 발급 성공")
        print(f"   - 토큰: {api.access_token[:20]}...")
        print(f"   - 만료시간: {api.token_expire_time}")
    else:
        print("   ✗ 초기 토큰 발급 실패")
        return
    
    print("\n2. 토큰 만료 검사 테스트")
    print(f"   - 현재 시간: {datetime.now()}")
    print(f"   - 토큰 만료시간: {api.token_expire_time}")
    print(f"   - 토큰 만료 여부: {api.is_token_expired()}")
    
    print("\n3. API 호출 테스트 (토큰 자동 갱신 확인)")
    
    # 잔고 조회로 테스트
    print("   잔고 조회 중...")
    balance = api.get_balance()
    if balance and balance.get('rt_cd') == '0':
        print("   ✓ 잔고 조회 성공")
    else:
        print("   ✗ 잔고 조회 실패")
    
    # 삼성전자 현재가 조회로 테스트  
    print("   삼성전자 현재가 조회 중...")
    price = api.get_stock_price("005930")
    if price and price.get('rt_cd') == '0':
        current_price = price['output']['stck_prpr']
        print(f"   ✓ 현재가 조회 성공: {current_price}원")
    else:
        print("   ✗ 현재가 조회 실패")
    
    print("\n4. 토큰 강제 만료 테스트")
    # 토큰 만료시간을 과거로 설정하여 강제 만료
    api.token_expire_time = datetime.now() - timedelta(minutes=1)
    print(f"   - 강제 만료 설정: {api.token_expire_time}")
    print(f"   - 만료 확인: {api.is_token_expired()}")
    
    print("   토큰 갱신 후 API 호출 테스트...")
    balance = api.get_balance()
    if balance and balance.get('rt_cd') == '0':
        print("   ✓ 토큰 자동 갱신 및 API 호출 성공")
        print(f"   - 새 토큰: {api.access_token[:20]}...")
        print(f"   - 새 만료시간: {api.token_expire_time}")
    else:
        print("   ✗ 토큰 자동 갱신 실패")

def test_token_error_handling():
    """토큰 에러 처리 테스트"""
    print("\n=== 토큰 에러 처리 테스트 ===")
    
    demo_account_info = Config.get_account_info('demo')
    api = KisAPI(
        demo_account_info['appkey'], 
        demo_account_info['appsecret'], 
        demo_account_info['account'], 
        is_real=False
    )
    
    # 잘못된 토큰으로 설정
    print("1. 잘못된 토큰으로 API 호출 테스트")
    api.access_token = "invalid_token_12345"
    api.token_expire_time = datetime.now() + timedelta(hours=1)  # 아직 만료되지 않은 것으로 설정
    
    print("   잔고 조회 시도 (잘못된 토큰)...")
    balance = api.get_balance()
    if balance and balance.get('rt_cd') == '0':
        print("   ✓ 토큰 자동 갱신 후 API 호출 성공")
    else:
        print("   ⚠ API 호출 결과 확인 필요")

if __name__ == "__main__":
    try:
        test_token_refresh()
        test_token_error_handling()
        print("\n=== 테스트 완료 ===")
    except Exception as e:
        print(f"테스트 중 오류 발생: {e}")