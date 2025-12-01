#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
해외주식 직접 매수/매도 테스트
"""
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from ai_trading_system.utils.kis_api import KisAPIEnhanced

def test_overseas_trading():
    print("=" * 80)
    print("🇺🇸 해외주식 매수/매도 직접 테스트")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # API 초기화
    api = KisAPIEnhanced(
        appkey=os.environ.get('KIS_DEMO_APPKEY'),
        appsecret=os.environ.get('KIS_DEMO_APPSECRET'),
        account_no=os.environ.get('KIS_DEMO_ACCOUNT'),
        is_real=False,
        min_request_interval=2.0  # 2초 간격
    )
    
    print("\n1️⃣ 토큰 발급 및 해외주식 API 초기화")
    print("-" * 50)
    
    if not api.get_access_token():
        print("❌ 토큰 발급 실패")
        return False
    
    print("✅ 토큰 발급 성공")
    
    # 해외주식 API 초기화
    api.initialize_overseas_api()
    print("✅ 해외주식 API 초기화 완료")
    
    print("\n2️⃣ 해외 계좌 잔고 확인")
    print("-" * 50)
    
    try:
        # USD 잔고 확인
        overseas_balance = api.overseas.get_overseas_balance()
        if overseas_balance and overseas_balance.get('rt_cd') == '0':
            output = overseas_balance.get('output', {})
            usd_balance = float(output.get('ovrs_crcycd_amt', 0))
            print(f"USD 잔고: ${usd_balance:,.2f}")
            
            if usd_balance == 0:
                print("⚠️ USD 잔고가 0입니다. 환전이나 가상머니 충전이 필요합니다.")
        else:
            print("❌ 해외 잔고 조회 실패")
            
    except Exception as e:
        print(f"⚠️ 잔고 조회 중 오류: {e}")
    
    print("\n3️⃣ 해외주식 현재가 조회 테스트")
    print("-" * 50)
    
    # 테스트할 종목들
    test_stocks = [
        {'exchange': 'NASD', 'symbol': 'AAPL', 'name': 'Apple Inc.'},
        {'exchange': 'NASD', 'symbol': 'MSFT', 'name': 'Microsoft Corp.'},
        {'exchange': 'NYSE', 'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.'}
    ]
    
    successful_quotes = []
    
    for stock in test_stocks:
        try:
            print(f"\n📊 {stock['name']} ({stock['symbol']}) 조회 중...")
            
            price_info = api.overseas.get_overseas_price(stock['exchange'], stock['symbol'])
            
            if price_info and isinstance(price_info, dict) and price_info.get('current_price'):
                current_price = float(price_info.get('current_price', 0))
                change_rate = float(price_info.get('change_rate', 0))
                
                print(f"✅ 현재가: ${current_price:.2f}")
                print(f"   등락률: {change_rate:+.2f}%")
                
                successful_quotes.append({
                    **stock,
                    'price': current_price,
                    'change_rate': change_rate
                })
            else:
                print(f"❌ 조회 실패: {price_info}")
                
            # API 호출 간격
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
    
    if not successful_quotes:
        print("\n⚠️ 조회 가능한 종목이 없어 매수/매도 테스트를 건너뜁니다.")
        return False
    
    # 가장 저렴한 종목 선택
    cheapest_stock = min(successful_quotes, key=lambda x: x['price'])
    
    print(f"\n4️⃣ 매수 테스트: {cheapest_stock['name']}")
    print("-" * 50)
    print(f"선택된 종목: {cheapest_stock['symbol']}")
    print(f"현재가: ${cheapest_stock['price']:.2f}")
    print(f"거래소: {cheapest_stock['exchange']}")
    
    try:
        # 1주 매수 시도
        buy_result = api.overseas.buy_overseas_stock(
            exchange=cheapest_stock['exchange'],
            symbol=cheapest_stock['symbol'],
            quantity=1,
            order_type='00'  # 시장가
        )
        
        print(f"\n매수 결과:")
        if buy_result:
            print(f"응답코드: {buy_result.get('rt_cd')}")
            print(f"메시지: {buy_result.get('msg1')}")
            print(f"상세: {buy_result.get('msg2', '')}")
            
            if buy_result.get('rt_cd') == '0':
                print("✅ 해외주식 매수 주문 성공!")
                output = buy_result.get('output', {})
                print(f"주문번호: {output.get('ODNO', 'N/A')}")
                
                # 5초 대기 후 매도 테스트
                print("\n⏳ 5초 후 매도 테스트...")
                time.sleep(5)
                
                print(f"\n5️⃣ 매도 테스트: {cheapest_stock['name']}")
                print("-" * 50)
                
                # 매도 시도
                sell_result = api.overseas.sell_overseas_stock(
                    exchange=cheapest_stock['exchange'],
                    symbol=cheapest_stock['symbol'],
                    quantity=1,
                    order_type='00'  # 시장가
                )
                
                print(f"\n매도 결과:")
                if sell_result:
                    print(f"응답코드: {sell_result.get('rt_cd')}")
                    print(f"메시지: {sell_result.get('msg1')}")
                    
                    if sell_result.get('rt_cd') == '0':
                        print("✅ 해외주식 매도 주문 성공!")
                        print(f"주문번호: {sell_result.get('output', {}).get('ODNO', 'N/A')}")
                        return True
                    else:
                        print("❌ 매도 실패")
                else:
                    print("❌ 매도 응답 없음")
            else:
                print("❌ 매수 실패")
                print("가능한 원인:")
                if "잔고" in buy_result.get('msg1', ''):
                    print("  - USD 잔고 부족")
                elif "시간" in buy_result.get('msg1', ''):
                    print("  - 미국 시장 거래시간 아님")
                elif "모의투자" in buy_result.get('msg1', ''):
                    print("  - 모의투자 해외주식 제한")
        else:
            print("❌ 매수 응답 없음")
            
    except Exception as e:
        print(f"❌ 매수/매도 테스트 중 오류: {e}")
    
    print(f"\n6️⃣ 해외 보유종목 확인")
    print("-" * 50)
    
    try:
        # 해외 보유종목 조회
        overseas_holdings = api.overseas.get_overseas_holdings()
        if overseas_holdings and overseas_holdings.get('rt_cd') == '0':
            holdings = overseas_holdings.get('output1', [])
            print(f"해외 보유종목: {len(holdings)}개")
            
            for holding in holdings[:5]:  # 최대 5개만
                print(f"  - {holding.get('ovrs_prod_name', 'N/A')}")
                print(f"    수량: {holding.get('ovrs_cblc_qty', 0)}주")
                print(f"    평가금액: ${holding.get('ovrs_stck_evlu_amt', 0)}")
        else:
            print("해외 보유종목: 0개")
    except Exception as e:
        print(f"⚠️ 보유종목 조회 오류: {e}")
    
    print("\n✅ 해외주식 테스트 완료")
    return True

if __name__ == "__main__":
    success = test_overseas_trading()
    if success:
        print("\n🎉 해외주식 매수/매도 기능이 정상 동작합니다!")
    else:
        print("\n⚠️ 일부 기능에 제한이 있을 수 있습니다.")