#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from ai_trading_system.utils.kis_api import KisAPIEnhanced

def test_orders():
    print("=" * 60)
    print("주문 테스트 (시장시간 고려)")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 현재 시간 확인
    now = datetime.now()
    is_korean_market = 9 <= now.hour < 15.5 and now.weekday() < 5
    is_us_market = ((now.hour >= 22.5) or (now.hour < 5)) and now.weekday() < 5
    
    print(f"현재 시각: {now.hour}시 {now.minute}분")
    print(f"요일: {['월','화','수','목','금','토','일'][now.weekday()]}요일")
    print(f"한국 시장: {'🟢 거래가능' if is_korean_market else '🔴 마감'}")
    print(f"미국 시장: {'🟢 거래가능' if is_us_market else '🔴 마감'}")
    
    # API 초기화
    api = KisAPIEnhanced(
        appkey=os.environ.get('DEMO_APPKEY'),
        appsecret=os.environ.get('DEMO_APPSECRET'),
        account_no=os.environ.get('DEMO_ACCOUNT_NO'),
        is_real=False,
        min_request_interval=0.5
    )
    
    if api.get_access_token():
        print("✅ 토큰 발급 성공")
    else:
        print("❌ 토큰 발급 실패")
        return
    
    # 시장 시간에 따른 테스트
    if is_korean_market:
        print("\n📈 한국 시장 거래 시간 - 실시간 주문 테스트")
        test_korean_order(api)
    elif is_us_market:
        print("\n🇺🇸 미국 시장 거래 시간 - 해외주식 테스트")  
        test_us_order(api)
    else:
        print("\n🌙 장외 시간 - 예약 주문 또는 조건부 주문 테스트")
        test_after_hours_order(api)

def test_korean_order(api):
    """한국 시장 거래시간 주문"""
    print("-" * 40)
    
    # 저가주 찾기
    volume_data = api.get_volume_rank(market="ALL")
    if isinstance(volume_data, dict) and 'output' in volume_data:
        stocks = volume_data['output']
        
        for stock in stocks[:10]:
            price = int(stock.get('stck_prpr', 0))
            if 1000 <= price <= 10000:
                test_stock = {
                    'code': stock['mksc_shrn_iscd'],
                    'name': stock['hts_kor_isnm'], 
                    'price': price
                }
                break
        
        print(f"테스트 종목: {test_stock['name']} ({test_stock['code']})")
        print(f"현재가: {test_stock['price']:,}원")
        
        # 시장가 주문
        result = api.buy_stock(
            stock_code=test_stock['code'],
            quantity=1,
            order_type="03"  # 시장가
        )
        
        if result and result.get('rt_cd') == '0':
            print("✅ 시장가 매수 성공!")
            return True
        else:
            print(f"❌ 시장가 실패: {result.get('msg1') if result else 'No response'}")
            
            # 지정가로 시도
            result2 = api.buy_stock(
                stock_code=test_stock['code'],
                quantity=1, 
                order_type="01",  # 지정가
                price=test_stock['price'] + 10  # 현재가보다 10원 높게
            )
            
            if result2 and result2.get('rt_cd') == '0':
                print("✅ 지정가 매수 성공!")
                return True
            else:
                print(f"❌ 지정가도 실패: {result2.get('msg1') if result2 else 'No response'}")
    
    return False

def test_us_order(api):
    """미국 시장 거래시간 주문"""
    print("-" * 40)
    
    # 해외주식 API 초기화
    api.initialize_overseas_api()
    
    # AAPL 현재가 확인
    aapl_data = api.overseas.get_overseas_price('NASD', 'AAPL')
    if aapl_data:
        print(f"AAPL 현재가: ${aapl_data['current_price']}")
        
        # 해외주식 매수 시도
        result = api.overseas.buy_overseas_stock(
            exchange='NASD',
            symbol='AAPL',
            quantity=1,
            order_type='00'  # 시장가
        )
        
        if result and result.get('rt_cd') == '0':
            print("✅ 해외주식 매수 성공!")
            return True
        else:
            print(f"❌ 해외주식 매수 실패: {result.get('msg1') if result else 'No response'}")
    
    return False

def test_after_hours_order(api):
    """장외시간 주문 테스트"""
    print("-" * 40)
    print("장외시간에는 다음이 가능할 수 있습니다:")
    print("1. 예약주문 (다음 거래일)")
    print("2. 조건부주문")
    print("3. 계좌 조회 및 분석")
    
    # 계좌 상태만 확인
    cash = api.get_available_cash()
    holdings = api.get_holding_stocks()
    
    print(f"\n현재 계좌 상태:")
    print(f"가용현금: {cash:,.0f}원")
    print(f"보유종목: {len(holdings)}개")
    
    for holding in holdings:
        print(f"  - {holding['stock_name']}: {holding['quantity']}주")
        print(f"    평가금액: {holding['eval_amt']:,}원")
        print(f"    수익률: {holding['profit_rate']:.2f}%")
    
    return True

if __name__ == "__main__":
    test_orders()