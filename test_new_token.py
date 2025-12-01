#!/usr/bin/env python3
"""
새 계좌번호로 토큰 재발급 테스트
"""
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ['KIS_DEMO_APPKEY'] = 'PSpRavS44ke8s1UZ8sn8VuOiXIXEE2QcMj2I'
os.environ['KIS_DEMO_APPSECRET'] = 'acvrN9QSZYfam2V2rAEyFsUisSv1dyDo8kXD3JXHeGQUqxLtZrQYngSlb/RVqhsxuAhPnbJodPXyakzqrxbsBX54ZOZnkduxKFnqqEqxgFte+UjmZvxgyRPx4BrxzUnZY6zEH3qh9n8tzDm6J6oEdyVURXIES26lIEca5BZ7+YyHgG87YKQ='
os.environ['KIS_DEMO_ACCOUNT'] = '50157423-01'

from ai_trading_system.utils.kis_api import KisAPIEnhanced

def test_new_token():
    """새 토큰 발급 테스트"""
    print("=" * 60)
    print("🔑 새 계좌번호로 토큰 재발급")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"계좌: {os.environ['KIS_DEMO_ACCOUNT']}")
    print("=" * 60)
    
    # API 초기화
    api = KisAPIEnhanced(
        appkey=os.environ['KIS_DEMO_APPKEY'],
        appsecret=os.environ['KIS_DEMO_APPSECRET'],
        account_no=os.environ['KIS_DEMO_ACCOUNT'],
        is_real=False,
        min_request_interval=0.5
    )
    
    # 새 토큰 발급
    print("\n1️⃣ 토큰 발급")
    print("-" * 40)
    
    if api.get_access_token():
        print("✅ 토큰 발급 성공!")
        print(f"토큰: {api.access_token[:20]}...")
        print(f"만료시간: {api.token_expire_time}")
        
        # 잔고 조회로 검증
        print("\n2️⃣ 토큰 검증 (잔고 조회)")
        print("-" * 40)
        
        cash = api.get_available_cash()
        print(f"가용 현금: {cash:,.0f}원")
        
        if cash == 0:
            print("\n⚠️ 모의투자 계좌에 가상머니가 없습니다.")
            print("한국투자증권 HTS/MTS에서:")
            print("1. 모의투자 메뉴 접속")
            print("2. 가상계좌 관리")
            print("3. 가상머니 충전 (보통 1억원)")
            
        # 간단한 주문 테스트
        print("\n3️⃣ 주문 테스트 (KODEX ETF)")
        print("-" * 40)
        
        result = api.buy_stock(
            stock_code='252670',  # KODEX 200선물인버스2X
            quantity=1,
            order_type="03"  # 시장가
        )
        
        if result:
            print(f"응답코드: {result.get('rt_cd')}")
            print(f"메시지: {result.get('msg1')}")
            if result.get('rt_cd') == '0':
                print("✅ 주문 가능한 계좌입니다!")
            else:
                print("❌ 주문 실패 - 잔고 부족이거나 시장 마감")
        
    else:
        print("❌ 토큰 발급 실패")
        print("API 키와 계좌번호를 확인하세요.")
        
    print("\n✅ 테스트 완료")

if __name__ == "__main__":
    test_new_token()