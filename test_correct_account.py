#!/usr/bin/env python3
"""
올바른 계좌번호로 모의투자 테스트
"""
import os
import sys
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 새로운 계정 정보 설정
os.environ['KIS_DEMO_APPKEY'] = 'PSpRavS44ke8s1UZ8sn8VuOiXIXEE2QcMj2I'
os.environ['KIS_DEMO_APPSECRET'] = 'acvrN9QSZYfam2V2rAEyFsUisSv1dyDo8kXD3JXHeGQUqxLtZrQYngSlb/RVqhsxuAhPnbJodPXyakzqrxbsBX54ZOZnkduxKFnqqEqxgFte+UjmZvxgyRPx4BrxzUnZY6zEH3qh9n8tzDm6J6oEdyVURXIES26lIEca5BZ7+YyHgG87YKQ='
os.environ['KIS_DEMO_ACCOUNT'] = '50144239-01'  # 하이픈 추가

from ai_trading_system.utils.kis_api import KisAPIEnhanced

def test_correct_account():
    """올바른 계좌번호로 테스트"""
    print("=" * 60)
    print("🚀 올바른 계좌번호로 모의투자 테스트")
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
    else:
        print("❌ 토큰 발급 실패")
        return
    
    try:
        # 2. 계좌 상태 확인
        print("\n2️⃣ 계좌 상태")
        print("-" * 40)
        
        cash = api.get_available_cash()
        print(f"가용 현금: {cash:,.0f}원")
        
        holdings = api.get_holding_stocks()
        print(f"보유 종목: {len(holdings)}개")
        
        if holdings:
            print("\n현재 보유 종목:")
            for h in holdings:
                print(f"  - {h['stock_name']} ({h['stock_code']}): {h['quantity']}주")
                print(f"    평가금액: {h['eval_amt']:,.0f}원, 수익률: {h['profit_rate']:.2f}%")
        
        # 3. 거래량 상위 종목에서 저가주 찾기
        print("\n3️⃣ 거래량 상위 저가주 찾기")
        print("-" * 40)
        
        volume_data = api.get_volume_rank(market="ALL")
        if isinstance(volume_data, dict) and 'output' in volume_data:
            stocks = volume_data['output']
            
            # 1만원 이하 종목 찾기
            cheap_stocks = []
            for stock in stocks[:30]:
                price = int(stock.get('stck_prpr', 0))
                if 500 <= price <= 10000:
                    cheap_stocks.append({
                        'code': stock['mksc_shrn_iscd'],
                        'name': stock['hts_kor_isnm'],
                        'price': price,
                        'volume': int(stock['acml_vol']),
                        'change_rate': float(stock['prdy_ctrt'])
                    })
            
            if cheap_stocks:
                # 가격 순으로 정렬
                cheap_stocks.sort(key=lambda x: x['price'])
                
                print(f"저가 종목 {len(cheap_stocks)}개 발견:")
                for i, stock in enumerate(cheap_stocks[:5], 1):
                    print(f"{i}. {stock['name']} ({stock['code']}): {stock['price']:,}원")
                
                # 가장 저렴한 종목 선택
                test_stock = cheap_stocks[0]
                
                # 4. 매수 테스트
                print(f"\n4️⃣ 매수 테스트: {test_stock['name']}")
                print("-" * 40)
                print(f"종목코드: {test_stock['code']}")
                print(f"현재가: {test_stock['price']:,}원")
                print(f"매수수량: 1주")
                
                if cash >= test_stock['price']:
                    # 매수 주문
                    buy_result = api.buy_stock(
                        stock_code=test_stock['code'],
                        quantity=1,
                        order_type="03"  # 시장가
                    )
                    
                    if buy_result and buy_result.get('rt_cd') == '0':
                        print("\n✅ 매수 주문 성공!")
                        output = buy_result.get('output', {})
                        print(f"주문번호: {output.get('ODNO', 'N/A')}")
                        print(f"주문시각: {output.get('ORD_TMD', 'N/A')}")
                        
                        # 5초 대기
                        print("\n⏳ 5초 대기...")
                        time.sleep(5)
                        
                        # 5. 보유 확인 및 매도
                        print("\n5️⃣ 매수 확인 및 매도 테스트")
                        print("-" * 40)
                        
                        new_holdings = api.get_holding_stocks()
                        for holding in new_holdings:
                            if holding['stock_code'] == test_stock['code']:
                                print(f"✅ 매수 확인: {holding['stock_name']} {holding['quantity']}주")
                                
                                # 매도 테스트
                                sell_result = api.sell_stock(
                                    stock_code=holding['stock_code'],
                                    quantity=holding['quantity'],
                                    order_type="03"  # 시장가
                                )
                                
                                if sell_result and sell_result.get('rt_cd') == '0':
                                    print("\n✅ 매도 주문 성공!")
                                    print(f"주문번호: {sell_result.get('output', {}).get('ODNO', 'N/A')}")
                                else:
                                    print(f"\n❌ 매도 실패: {sell_result}")
                                break
                    else:
                        print("\n❌ 매수 실패")
                        if buy_result:
                            print(f"오류코드: {buy_result.get('rt_cd')}")
                            print(f"메시지: {buy_result.get('msg1')}")
                            print(f"상세: {buy_result.get('msg2', '')}")
                else:
                    print(f"\n⚠️ 잔고 부족 (필요: {test_stock['price']:,}원, 가용: {cash:,.0f}원)")
        
        # 6. 해외주식 테스트
        print("\n6️⃣ 해외주식 테스트")
        print("-" * 40)
        
        api.initialize_overseas_api()
        
        # AAPL 현재가
        aapl = api.overseas.get_overseas_price('NASD', 'AAPL')
        if aapl:
            print(f"AAPL 현재가: ${aapl['current_price']} ({aapl['change_rate']:+.2f}%)")
        
        # 해외 잔고
        overseas_balance = api.overseas.get_overseas_balance()
        if overseas_balance:
            print(f"USD 잔고: ${overseas_balance.get('foreign_currency_amount', 0):,.2f}")
        
        # 7. 최종 상태
        print("\n7️⃣ 최종 계좌 상태")
        print("-" * 40)
        final_cash = api.get_available_cash()
        print(f"최종 가용현금: {final_cash:,.0f}원")
        
        # 시장 상태 확인
        from ai_trading_system.main_trading_system import AITradingSystem
        system = AITradingSystem(mode='demo')
        markets = system.get_active_markets()
        
        print("\n📊 현재 시장 상태:")
        for market, active in markets.items():
            print(f"  {market.upper()}: {'🟢 거래가능' if active else '🔴 마감'}")
            
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ 테스트 완료!")

if __name__ == "__main__":
    test_correct_account()