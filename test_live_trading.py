#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from ai_trading_system.utils.kis_api import KisAPIEnhanced

def test_live_trading():
    print("=" * 60)
    print("실제 모의투자 테스트")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"계좌: {os.environ.get('DEMO_ACCOUNT_NO')}")
    print("=" * 60)
    
    # API 초기화
    api = KisAPIEnhanced(
        appkey=os.environ.get('DEMO_APPKEY'),
        appsecret=os.environ.get('DEMO_APPSECRET'),  
        account_no=os.environ.get('DEMO_ACCOUNT_NO'),
        is_real=False,
        min_request_interval=0.5
    )
    
    # 1. 토큰 발급
    print("\n1. 토큰 발급")
    print("-" * 40)
    if api.get_access_token():
        print(f"✅ 성공: {api.access_token[:20]}...")
    else:
        print("❌ 실패")
        return False
    
    # 2. 계좌 잔고 확인
    print("\n2. 계좌 잔고")
    print("-" * 40)
    cash = api.get_available_cash()
    print(f"가용현금: {cash:,.0f}원")
    
    if cash == 0:
        print("⚠️ 잔고가 0원입니다. 모의투자 가상머니를 충전하세요.")
        return False
    
    # 3. 보유종목 조회
    print("\n3. 보유종목")
    print("-" * 40)
    holdings = api.get_holding_stocks()
    print(f"보유종목: {len(holdings)}개")
    for h in holdings[:3]:  # 최대 3개만 표시
        print(f"  - {h['stock_name']} {h['quantity']}주")
    
    # 4. 저가주 찾기
    print("\n4. 거래 가능 종목 찾기")
    print("-" * 40)
    try:
        volume_data = api.get_volume_rank(market="ALL")
        if isinstance(volume_data, dict) and 'output' in volume_data:
            stocks = volume_data['output']
            
            cheap_stocks = []
            for stock in stocks[:20]:
                price = int(stock.get('stck_prpr', 0))
                if 1000 <= price <= 20000:  # 1천원~2만원 
                    cheap_stocks.append({
                        'code': stock['mksc_shrn_iscd'],
                        'name': stock['hts_kor_isnm'],
                        'price': price
                    })
            
            if cheap_stocks:
                test_stock = cheap_stocks[0]
                print(f"테스트 종목: {test_stock['name']} ({test_stock['code']})")
                print(f"현재가: {test_stock['price']:,}원")
                
                # 5. 매수 테스트
                print("\n5. 매수 테스트")
                print("-" * 40)
                buy_result = api.buy_stock(
                    stock_code=test_stock['code'],
                    quantity=1,
                    order_type="03"  # 시장가
                )
                
                if buy_result:
                    print(f"응답코드: {buy_result.get('rt_cd')}")
                    print(f"메시지: {buy_result.get('msg1')}")
                    
                    if buy_result.get('rt_cd') == '0':
                        print("✅ 매수 성공!")
                        output = buy_result.get('output', {})
                        print(f"주문번호: {output.get('ODNO', 'N/A')}")
                        
                        # 5초 대기
                        print("\n⏳ 5초 대기...")
                        time.sleep(5)
                        
                        # 6. 매도 테스트  
                        print("\n6. 매도 테스트")
                        print("-" * 40)
                        
                        # 보유 확인 후 매도
                        new_holdings = api.get_holding_stocks()
                        for holding in new_holdings:
                            if holding['stock_code'] == test_stock['code']:
                                sell_result = api.sell_stock(
                                    stock_code=holding['stock_code'],
                                    quantity=holding['quantity'],
                                    order_type="03"
                                )
                                
                                if sell_result and sell_result.get('rt_cd') == '0':
                                    print("✅ 매도 성공!")
                                    print(f"주문번호: {sell_result.get('output', {}).get('ODNO', 'N/A')}")
                                else:
                                    print(f"❌ 매도 실패: {sell_result}")
                                break
                        
                        return True
                    else:
                        print("❌ 매수 실패")
                        if "모의투자 주문이 불가한 계좌" in buy_result.get('msg1', ''):
                            print("\n⚠️ 해결방법:")
                            print("1. 한투증권 웹/앱 로그인")
                            print("2. 모의투자 메뉴 접속")  
                            print("3. 참가신청 및 가상머니 충전")
                        return False
            else:
                print("❌ 적절한 테스트 종목을 찾을 수 없습니다")
                return False
                
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    
    print("\n✅ 테스트 완료")
    return True

if __name__ == "__main__":
    success = test_live_trading()
    if success:
        print("\n🎉 모의투자가 정상 작동합니다!")
    else:
        print("\n🚨 모의투자 설정을 확인하세요.")