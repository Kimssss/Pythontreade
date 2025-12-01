#!/usr/bin/env python3
"""
직접 주문 테스트 - 최소 금액으로
"""
import os
import sys
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ['KIS_DEMO_APPKEY'] = 'PSpRavS44ke8s1UZ8sn8VuOiXIXEE2QcMj2I'
os.environ['KIS_DEMO_APPSECRET'] = 'acvrN9QSZYfam2V2rAEyFsUisSv1dyDo8kXD3JXHeGQUqxLtZrQYngSlb/RVqhsxuAhPnbJodPXyakzqrxbsBX54ZOZnkduxKFnqqEqxgFte+UjmZvxgyRPx4BrxzUnZY6zEH3qh9n8tzDm6J6oEdyVURXIES26lIEca5BZ7+YyHgG87YKQ='
os.environ['KIS_DEMO_ACCOUNT'] = '50157423-01'

from ai_trading_system.utils.kis_api import KisAPIEnhanced

def test_direct_order():
    """직접 주문 테스트"""
    print("=" * 60)
    print("💸 모의투자 직접 주문 테스트")
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
    
    # 토큰 로드
    import pickle
    try:
        with open('cache/token_demo_PSpRavS44k.pkl', 'rb') as f:
            cached = pickle.load(f)
            api.access_token = cached['access_token']
            api.token_expire_time = cached['token_expire_time']
            print("✅ 토큰 로드")
    except:
        api.get_access_token()
    
    # 1. 계좌 정보 확인
    print("\n1️⃣ 계좌 정보")
    print("-" * 40)
    
    # 잔고 직접 조회
    balance = api.get_balance()
    if balance and balance.get('rt_cd') == '0':
        output2 = balance.get('output2', [])
        if output2:
            data = output2[0]
            print(f"예수금총금액: {int(data.get('dnca_tot_amt', 0)):,}원")
            print(f"익일정산금액: {int(data.get('nxdy_excc_amt', 0)):,}원")
            print(f"주문가능현금: {int(data.get('ord_psbl_cash', 0)):,}원")
            print(f"출금가능금액: {int(data.get('prvs_rcdl_excc_amt', 0)):,}원")
    
    # 2. 거래량 상위 확인
    print("\n2️⃣ 거래량 상위 종목")
    print("-" * 40)
    
    volume_data = api.get_volume_rank(market="ALL")
    print(f"응답 타입: {type(volume_data)}")
    
    if isinstance(volume_data, list) and len(volume_data) > 0:
        # 첫 번째 종목 확인
        first = volume_data[0]
        print(f"첫 번째 종목 타입: {type(first)}")
        if isinstance(first, dict):
            print(f"종목 정보: {first}")
        
        # 저가 종목 찾기
        for item in volume_data[:10]:
            if isinstance(item, dict):
                price = item.get('price', 0)
                if 1000 <= price <= 10000:
                    print(f"\n테스트 종목: {item.get('name')} ({item.get('code')})")
                    print(f"현재가: {price:,}원")
                    
                    # 3. 매수 시도
                    print("\n3️⃣ 매수 주문 시도")
                    print("-" * 40)
                    
                    # 잔고가 0이어도 모의투자는 가능할 수 있음
                    buy_result = api.buy_stock(
                        stock_code=item.get('code'),
                        quantity=1,
                        order_type="03"  # 시장가
                    )
                    
                    print(f"매수 응답: {buy_result}")
                    
                    if buy_result and buy_result.get('rt_cd') == '0':
                        print("✅ 매수 주문 성공!")
                        output = buy_result.get('output', {})
                        print(f"주문번호: {output}")
                    else:
                        print("❌ 매수 주문 실패")
                        if buy_result:
                            print(f"오류: {buy_result.get('msg1')}")
                            print(f"상세: {buy_result.get('msg2', '')}")
                    
                    break
    else:
        print(f"거래량 데이터 문제: {volume_data}")
    
    # 4. 보유 종목 확인
    print("\n4️⃣ 보유 종목")
    print("-" * 40)
    
    holdings = api.get_holding_stocks()
    print(f"보유 종목 수: {len(holdings)}개")
    for h in holdings:
        print(f"  - {h}")
    
    # 5. 시장 시간 확인
    print("\n5️⃣ 시장 상태")
    print("-" * 40)
    
    from ai_trading_system.main_trading_system import AITradingSystem
    system = AITradingSystem(mode='demo')
    markets = system.get_active_markets()
    
    now = datetime.now()
    print(f"현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"요일: {['월','화','수','목','금','토','일'][now.weekday()]}")
    
    for market, active in markets.items():
        print(f"  {market}: {'🟢 거래가능' if active else '🔴 마감'}")
    
    print("\n✅ 테스트 완료")

if __name__ == "__main__":
    test_direct_order()