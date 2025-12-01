#!/usr/bin/env python3
"""
최종 매수 테스트 - 저가 종목
"""
import os
import sys
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ['KIS_DEMO_APPKEY'] = 'PSpRavS44ke8s1UZ8sn8VuOiXIXEE2QcMj2I'
os.environ['KIS_DEMO_APPSECRET'] = 'acvrN9QSZYfam2V2rAEyFsUisSv1dyDo8kXD3JXHeGQUqxLtZrQYngSlb/RVqhsxuAhPnbJodPXyakzqrxbsBX54ZOZnkduxKFnqqEqxgFte+UjmZvxgyRPx4BrxzUnZY6zEH3qh9n8tzDm6J6oEdyVURXIES26lIEca5BZ7+YyHgG87YKQ='
os.environ['KIS_DEMO_ACCOUNT'] = '50157423-01'

from ai_trading_system.utils.kis_api import KisAPIEnhanced

def final_buy_test():
    """최종 매수 테스트"""
    print("=" * 60)
    print("🎯 최종 매수 테스트")
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
    
    # 1. 계좌 잔고
    print("\n1️⃣ 계좌 잔고")
    print("-" * 40)
    cash = api.get_available_cash()
    print(f"가용 현금: {cash:,.0f}원")
    
    # 2. 저가 종목 선택 - KODEX 200선물인버스2X (252670)
    test_stock = {
        'code': '252670',
        'name': 'KODEX 200선물인버스2X',
        'price': 748
    }
    
    print(f"\n2️⃣ 테스트 종목")
    print("-" * 40)
    print(f"종목명: {test_stock['name']}")
    print(f"종목코드: {test_stock['code']}")
    print(f"현재가: {test_stock['price']:,}원")
    
    # 3. 현재가 재확인
    print("\n3️⃣ 현재가 확인")
    print("-" * 40)
    price_info = api.get_stock_price(test_stock['code'])
    if price_info and price_info.get('rt_cd') == '0':
        output = price_info.get('output', {})
        current_price = int(output.get('stck_prpr', 0))
        print(f"실시간 현재가: {current_price:,}원")
        print(f"전일대비: {output.get('prdy_vrss', '')}원 ({output.get('prdy_ctrt', '')}%)")
    else:
        current_price = test_stock['price']
    
    # 4. 매수 주문
    print("\n4️⃣ 매수 주문")
    print("-" * 40)
    print(f"매수 수량: 1주")
    print(f"예상 금액: {current_price:,}원")
    print(f"주문 유형: 시장가")
    
    buy_result = api.buy_stock(
        stock_code=test_stock['code'],
        quantity=1,
        order_type="03"  # 시장가
    )
    
    print(f"\n매수 응답:")
    if buy_result:
        print(f"결과코드: {buy_result.get('rt_cd')}")
        print(f"메시지: {buy_result.get('msg1')}")
        
        if buy_result.get('rt_cd') == '0':
            output = buy_result.get('output', {})
            print("\n✅ 매수 주문 성공!")
            print(f"주문번호: {output.get('ODNO', 'N/A')}")
            print(f"주문시각: {output.get('ORD_TMD', 'N/A')}")
            
            # 5초 대기
            print("\n⏳ 5초 대기...")
            time.sleep(5)
            
            # 5. 보유 확인
            print("\n5️⃣ 보유 종목 확인")
            print("-" * 40)
            holdings = api.get_holding_stocks()
            print(f"보유 종목 수: {len(holdings)}개")
            
            for holding in holdings:
                if holding['stock_code'] == test_stock['code']:
                    print(f"\n✅ 매수 확인!")
                    print(f"종목: {holding['stock_name']}")
                    print(f"수량: {holding['quantity']}주")
                    print(f"평균단가: {holding['avg_price']:,}원")
                    print(f"평가금액: {holding['eval_amt']:,}원")
                    print(f"수익률: {holding['profit_rate']:.2f}%")
                    
                    # 6. 매도 테스트
                    print("\n6️⃣ 매도 테스트")
                    print("-" * 40)
                    
                    sell_result = api.sell_stock(
                        stock_code=holding['stock_code'],
                        quantity=holding['quantity'],
                        order_type="03"  # 시장가
                    )
                    
                    if sell_result and sell_result.get('rt_cd') == '0':
                        print("✅ 매도 주문 성공!")
                        print(f"주문번호: {sell_result.get('output', {}).get('ODNO', 'N/A')}")
                    else:
                        print(f"❌ 매도 실패: {sell_result}")
                    
                    break
        else:
            print("\n❌ 매수 실패")
            print(f"상세 메시지: {buy_result.get('msg2', '')}")
            
            # output 내용 확인
            if 'output' in buy_result:
                print("\n출력 정보:")
                output = buy_result['output']
                if isinstance(output, dict):
                    for key, value in output.items():
                        print(f"  {key}: {value}")
    else:
        print("❌ 응답 없음")
    
    # 7. 최종 잔고
    print("\n7️⃣ 최종 상태")
    print("-" * 40)
    final_cash = api.get_available_cash()
    print(f"최종 가용현금: {final_cash:,.0f}원")
    
    # 계좌 정보가 0원인 경우 확인
    if cash == 0 and final_cash == 0:
        print("\n⚠️ 모의투자 계좌 잔고가 0원입니다.")
        print("한국투자증권 HTS/MTS에서 모의투자 계좌에 가상머니를 충전해주세요.")
        print("보통 1억원 정도의 가상머니로 시작합니다.")

if __name__ == "__main__":
    final_buy_test()