#!/usr/bin/env python3
"""
미국 주식 매수/매도 테스트
"""
import os
import sys
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 환경변수 설정
os.environ['KIS_DEMO_APPKEY'] = 'PSpRavS44ke8s1UZ8sn8VuOiXIXEE2QcMj2I'
os.environ['KIS_DEMO_APPSECRET'] = 'acvrN9QSZYfam2V2rAEyFsUisSv1dyDo8kXD3JXHeGQUqxLtZrQYngSlb/RVqhsxuAhPnbJodPXyakzqrxbsBX54ZOZnkduxKFnqqEqxgFte+UjmZvxgyRPx4BrxzUnZY6zEH3qh9n8tzDm6J6oEdyVURXIES26lIEca5BZ7+YyHgG87YKQ='
os.environ['KIS_DEMO_ACCOUNT'] = '50144239-01'

from ai_trading_system.utils.kis_api import KisAPIEnhanced

def test_us_stock():
    """미국 주식 테스트"""
    print("=" * 60)
    print("🇺🇸 미국 주식 거래 테스트")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # API 초기화
    api = KisAPIEnhanced(
        appkey=os.environ['KIS_DEMO_APPKEY'],
        appsecret=os.environ['KIS_DEMO_APPSECRET'],
        account_no=os.environ['KIS_DEMO_ACCOUNT'],
        is_real=False,
        min_request_interval=0.5
    )
    
    # 캐시된 토큰 로드
    import pickle
    try:
        with open('cache/token_demo_PSpRavS44k.pkl', 'rb') as f:
            cached = pickle.load(f)
            api.access_token = cached['access_token']
            api.token_expire_time = cached['token_expire_time']
            print("✅ 토큰 로드 성공")
    except:
        if not api.get_access_token():
            print("❌ 토큰 발급 실패")
            return
    
    try:
        # 해외주식 API 초기화
        api.initialize_overseas_api()
        print("✅ 해외주식 API 초기화 성공")
        
        # 1. 해외주식 잔고 확인
        print("\n1️⃣ 해외주식 계좌 상태")
        print("-" * 40)
        
        balance = api.overseas.get_overseas_balance()
        if balance:
            usd_cash = balance.get('foreign_currency_amount', 0)
            print(f"USD 잔고: ${usd_cash:,.2f}")
            holdings = balance.get('holdings', [])
            print(f"보유 종목: {len(holdings)}개")
            if holdings:
                for holding in holdings[:5]:
                    print(f"  - {holding['name']} ({holding['symbol']}): {holding['quantity']}주")
        else:
            print("해외주식 잔고 조회 실패")
            usd_cash = 0
        
        # 2. 미국 시장 시간 확인
        print("\n2️⃣ 미국 시장 상태")
        print("-" * 40)
        now = datetime.now()
        hour = now.hour
        
        # 한국 시간 기준 미국 시장 시간
        if (hour >= 23 or hour < 6) or (hour == 22 and now.minute >= 30):
            print("✅ 미국 시장 개장 시간")
        else:
            print("❌ 미국 시장 마감 (한국시간 22:30 ~ 06:00)")
            print("⚠️ 마감 시간에도 테스트 진행")
        
        # 3. AAPL 현재가 조회
        test_symbol = 'AAPL'
        print(f"\n3️⃣ {test_symbol} 현재가 조회")
        print("-" * 40)
        
        price_info = api.overseas.get_overseas_price('NASD', test_symbol)
        if price_info:
            current_price = price_info['current_price']
            print(f"종목: Apple Inc.")
            print(f"현재가: ${current_price}")
            print(f"변동률: {price_info['change_rate']}%")
            print(f"거래량: {price_info['volume']:,}")
            
            # 4. 매수 테스트 (1주)
            if usd_cash >= current_price:
                print(f"\n4️⃣ 매수 주문 테스트")
                print("-" * 40)
                print(f"매수 종목: {test_symbol}")
                print(f"매수 수량: 1주")
                print(f"예상 금액: ${current_price}")
                
                # 매수 주문
                buy_result = api.overseas.buy_overseas_stock(
                    exchange='NASD',
                    symbol=test_symbol,
                    quantity=1,
                    order_type='00'  # 시장가
                )
                
                if buy_result and buy_result.get('rt_cd') == '0':
                    output = buy_result.get('output', {})
                    print("✅ 매수 주문 성공!")
                    print(f"   주문번호: {output.get('ODNO')}")
                    
                    # 5초 대기
                    print("\n⏳ 5초 대기...")
                    time.sleep(5)
                    
                    # 5. 보유 확인
                    print("\n5️⃣ 매수 후 보유 종목 확인")
                    print("-" * 40)
                    new_balance = api.overseas.get_overseas_balance()
                    if new_balance:
                        new_holdings = new_balance.get('holdings', [])
                        aapl_holding = None
                        for holding in new_holdings:
                            if holding['symbol'] == test_symbol:
                                aapl_holding = holding
                                print(f"✅ {test_symbol} 보유 확인!")
                                print(f"   보유 수량: {holding['quantity']}주")
                                print(f"   평균 단가: ${holding['avg_price']}")
                                print(f"   평가 금액: ${holding['eval_amount']}")
                                break
                        
                        # 6. 매도 테스트
                        if aapl_holding:
                            print(f"\n6️⃣ 매도 주문 테스트")
                            print("-" * 40)
                            print(f"매도 수량: {aapl_holding['quantity']}주")
                            
                            sell_result = api.overseas.sell_overseas_stock(
                                exchange='NASD',
                                symbol=test_symbol,
                                quantity=aapl_holding['quantity'],
                                order_type='00'  # 시장가
                            )
                            
                            if sell_result and sell_result.get('rt_cd') == '0':
                                print("✅ 매도 주문 성공!")
                                print(f"   주문번호: {sell_result.get('output', {}).get('ODNO')}")
                            else:
                                print(f"❌ 매도 주문 실패: {sell_result}")
                else:
                    print(f"❌ 매수 주문 실패")
                    if buy_result:
                        print(f"   오류코드: {buy_result.get('rt_cd')}")
                        print(f"   메시지: {buy_result.get('msg1')}")
                        print(f"   상세: {buy_result}")
            else:
                print(f"\n⚠️ USD 잔고 부족")
                print(f"   필요 금액: ${current_price}")
                print(f"   USD 잔고: ${usd_cash}")
                
                # 잔고가 없어도 주문 가능한지 테스트
                print("\n💡 잔고 없이 매수 테스트 (오류 확인용)")
                buy_test = api.overseas.buy_overseas_stock(
                    exchange='NASD',
                    symbol=test_symbol,
                    quantity=1,
                    order_type='00'
                )
                if buy_test:
                    print(f"응답: {buy_test}")
        else:
            print("❌ 현재가 조회 실패")
        
        # 7. 최종 상태 확인
        print("\n7️⃣ 최종 계좌 상태")
        print("-" * 40)
        final_balance = api.overseas.get_overseas_balance()
        if final_balance:
            print(f"USD 잔고: ${final_balance.get('foreign_currency_amount', 0):,.2f}")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_us_stock()