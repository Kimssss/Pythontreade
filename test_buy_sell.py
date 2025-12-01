#!/usr/bin/env python3
"""
모의투자 매수/매도 실제 테스트
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

def test_buy_sell():
    """매수/매도 테스트"""
    print("=" * 60)
    print("💰 모의투자 매수/매도 테스트")
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
        # 1. 현재 잔고 확인
        print("\n1️⃣ 현재 계좌 상태")
        print("-" * 40)
        cash = api.get_available_cash()
        print(f"가용 현금: {cash:,.0f}원")
        
        holdings = api.get_holding_stocks()
        print(f"보유 종목: {len(holdings)}개")
        
        # 2. 테스트할 종목 선택 (카카오 - 035720)
        test_code = '035720'  # 카카오
        print(f"\n2️⃣ 테스트 종목: 카카오 ({test_code})")
        print("-" * 40)
        
        # 현재가 조회
        price_info = api.get_stock_price(test_code)
        if price_info and price_info.get('rt_cd') == '0':
            output = price_info.get('output', {})
            current_price = int(output.get('stck_prpr', 0))
            print(f"현재가: {current_price:,}원")
            print(f"전일대비: {output.get('prdy_vrss', 'N/A')}원 ({output.get('prdy_ctrt', 'N/A')}%)")
            
            # 3. 매수 테스트
            if cash > current_price:
                buy_qty = 1  # 1주만 매수
                print(f"\n3️⃣ 매수 주문")
                print("-" * 40)
                print(f"매수 수량: {buy_qty}주")
                print(f"예상 금액: {current_price * buy_qty:,}원")
                
                # 매수 주문 실행
                buy_result = api.buy_stock(
                    stock_code=test_code,
                    quantity=buy_qty,
                    order_type="03"  # 시장가
                )
                
                if buy_result and buy_result.get('rt_cd') == '0':
                    output = buy_result.get('output', {})
                    order_no = output.get('ODNO')
                    print(f"✅ 매수 주문 성공!")
                    print(f"   주문번호: {order_no}")
                    print(f"   주문시각: {output.get('ORD_TMD', '')}")
                    
                    # 5초 대기
                    print("\n⏳ 5초 대기...")
                    time.sleep(5)
                    
                    # 4. 보유 종목 재확인
                    print("\n4️⃣ 매수 후 보유 종목 확인")
                    print("-" * 40)
                    new_holdings = api.get_holding_stocks()
                    kakao_holding = None
                    
                    for holding in new_holdings:
                        if holding['stock_code'] == test_code:
                            kakao_holding = holding
                            print(f"✅ 카카오 보유 확인!")
                            print(f"   보유 수량: {holding['quantity']}주")
                            print(f"   평균 단가: {holding['avg_price']:,}원")
                            print(f"   평가 금액: {holding['eval_amt']:,}원")
                            print(f"   수익률: {holding['profit_rate']:.2f}%")
                            break
                    
                    # 5. 매도 테스트
                    if kakao_holding:
                        print(f"\n5️⃣ 매도 주문")
                        print("-" * 40)
                        print(f"매도 수량: {kakao_holding['quantity']}주")
                        
                        # 매도 주문 실행
                        sell_result = api.sell_stock(
                            stock_code=test_code,
                            quantity=kakao_holding['quantity'],
                            order_type="03"  # 시장가
                        )
                        
                        if sell_result and sell_result.get('rt_cd') == '0':
                            output = sell_result.get('output', {})
                            print(f"✅ 매도 주문 성공!")
                            print(f"   주문번호: {output.get('ODNO')}")
                            print(f"   주문시각: {output.get('ORD_TMD', '')}")
                        else:
                            print(f"❌ 매도 주문 실패: {sell_result}")
                    else:
                        print("❌ 매수한 종목을 찾을 수 없음")
                        
                else:
                    print(f"❌ 매수 주문 실패")
                    if buy_result:
                        print(f"   오류코드: {buy_result.get('rt_cd')}")
                        print(f"   메시지: {buy_result.get('msg1')}")
                        print(f"   상세: {buy_result.get('output', {})}")
            else:
                print("\n⚠️ 잔고 부족으로 매수 불가")
                print(f"   필요 금액: {current_price:,}원")
                print(f"   가용 현금: {cash:,}원")
        else:
            print("❌ 현재가 조회 실패")
        
        # 6. 최종 잔고 확인
        print(f"\n6️⃣ 최종 계좌 상태")
        print("-" * 40)
        final_cash = api.get_available_cash()
        print(f"가용 현금: {final_cash:,.0f}원")
        print(f"거래 전후 차이: {final_cash - cash:+,.0f}원")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_buy_sell()