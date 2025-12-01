#!/usr/bin/env python3
"""
한국투자증권 API 모의투자 전체 기능 테스트 (매수/매도 포함)
"""
import os
import sys
import json
import asyncio
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_trading_system.utils.kis_api import KisAPIEnhanced
from ai_trading_system.config.settings import KIS_CONFIG

async def test_full_trading():
    """전체 트레이딩 기능 테스트"""
    print("=" * 60)
    print("🚀 한국투자증권 API 모의투자 전체 테스트")
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 모의투자 계정으로 초기화
    demo_config = KIS_CONFIG['demo']
    api = KisAPIEnhanced(
        demo_config['appkey'],
        demo_config['appsecret'],
        demo_config['account'],
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
            print("✅ 캐시된 토큰 로드 성공")
    except:
        print("⚠️ 캐시된 토큰 없음, 새로 발급 시도...")
        if not api.get_access_token():
            print("❌ 토큰 발급 실패")
            return
    
    try:
        # 1. 계좌 정보 조회
        print("\n1️⃣ 계좌 정보 조회")
        print("-" * 40)
        
        # 잔고 조회
        cash = api.get_available_cash()
        print(f"💰 가용 현금: {cash:,.0f}원")
        
        # 보유 종목
        holdings = api.get_holding_stocks()
        print(f"📊 보유 종목: {len(holdings)}개")
        if holdings:
            for stock in holdings:
                print(f"  - {stock['stock_name']} ({stock['stock_code']}): {stock['quantity']}주")
                print(f"    평가금액: {stock['eval_amt']:,.0f}원, 수익률: {stock['profit_rate']:.2f}%")
        
        # 2. 한국 주식 테스트
        print("\n2️⃣ 한국 주식 거래 테스트")
        print("-" * 40)
        
        # 거래량 상위 종목 조회
        volume_ranks = api.get_volume_rank(market="KOSPI")
        if volume_ranks and len(volume_ranks) > 0:
            # 테스트할 종목 선택 (거래량 상위 중 적당한 가격대)
            test_stock = None
            for stock in volume_ranks:
                if 10000 <= stock['price'] <= 100000:  # 1만원~10만원 사이
                    test_stock = stock
                    break
            
            if test_stock:
                print(f"\n🎯 테스트 종목: {test_stock['name']} ({test_stock['code']})")
                print(f"   현재가: {test_stock['price']:,}원")
                print(f"   거래량: {test_stock['volume']:,}")
                
                # 매수 가능 수량 계산
                if cash > 0:
                    buy_quantity = min(1, int(cash / test_stock['price'] / 10))  # 최소 1주
                    
                    if buy_quantity > 0:
                        print(f"\n💳 매수 주문 테스트")
                        print(f"   종목: {test_stock['name']}")
                        print(f"   수량: {buy_quantity}주")
                        print(f"   예상 금액: {test_stock['price'] * buy_quantity:,}원")
                        
                        # 매수 주문
                        buy_result = api.buy_stock(
                            test_stock['code'],
                            buy_quantity,
                            order_type="03"  # 시장가
                        )
                        
                        if buy_result and buy_result.get('rt_cd') == '0':
                            print("   ✅ 매수 주문 성공!")
                            order_no = buy_result.get('output', {}).get('odno')
                            print(f"   주문번호: {order_no}")
                            
                            # 3초 대기
                            print("\n⏳ 3초 대기...")
                            time.sleep(3)
                            
                            # 보유 종목 재확인
                            print("\n📋 보유 종목 재확인")
                            new_holdings = api.get_holding_stocks()
                            bought_stock = None
                            for holding in new_holdings:
                                if holding['stock_code'] == test_stock['code']:
                                    bought_stock = holding
                                    print(f"   ✅ 매수 확인: {holding['stock_name']} {holding['quantity']}주")
                                    break
                            
                            # 매도 테스트
                            if bought_stock:
                                print(f"\n💸 매도 주문 테스트")
                                print(f"   종목: {bought_stock['stock_name']}")
                                print(f"   수량: {bought_stock['quantity']}주")
                                
                                sell_result = api.sell_stock(
                                    bought_stock['stock_code'],
                                    bought_stock['quantity'],
                                    order_type="03"  # 시장가
                                )
                                
                                if sell_result and sell_result.get('rt_cd') == '0':
                                    print("   ✅ 매도 주문 성공!")
                                    print(f"   주문번호: {sell_result.get('output', {}).get('odno')}")
                                else:
                                    print(f"   ❌ 매도 실패: {sell_result}")
                        else:
                            print(f"   ❌ 매수 실패: {buy_result}")
                    else:
                        print("   ⚠️ 잔고 부족으로 매수 불가")
                else:
                    print("   ⚠️ 가용 현금이 없어 매수 테스트 불가")
        
        # 3. 해외주식 테스트
        print("\n3️⃣ 해외주식 기능 테스트")
        print("-" * 40)
        
        # 해외주식 API 초기화
        api.initialize_overseas_api()
        print("✅ 해외주식 API 초기화 완료")
        
        # 미국 주식 현재가 조회
        print("\n🇺🇸 미국 주식 현재가 조회")
        test_symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        for symbol in test_symbols:
            price_info = api.overseas.get_overseas_price('NASD', symbol)
            if price_info:
                print(f"\n{symbol}:")
                print(f"  현재가: ${price_info['current_price']}")
                print(f"  변동률: {price_info['change_rate']}%")
                print(f"  거래량: {price_info['volume']:,}")
            else:
                print(f"\n{symbol}: 조회 실패")
        
        # 해외주식 잔고 조회
        print("\n💰 해외주식 잔고 조회")
        overseas_balance = api.overseas.get_overseas_balance()
        if overseas_balance:
            print(f"  USD 잔고: ${overseas_balance.get('foreign_currency_amount', 0):,.2f}")
            print(f"  보유 종목: {len(overseas_balance.get('holdings', []))}개")
            
            holdings = overseas_balance.get('holdings', [])
            if holdings:
                for holding in holdings[:5]:
                    print(f"  - {holding['name']} ({holding['symbol']}): {holding['quantity']}주")
        
        # 4. 시장 상태 확인
        print("\n4️⃣ 현재 거래 가능 시장")
        print("-" * 40)
        
        from ai_trading_system.main_trading_system import AITradingSystem
        system = AITradingSystem(mode='demo')
        active_markets = system.get_active_markets()
        
        print(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        for market, is_active in active_markets.items():
            status = "✅ 거래 가능" if is_active else "❌ 마감"
            emoji = {"korean": "🇰🇷", "us": "🇺🇸"}.get(market, "🌐")
            print(f"{emoji} {market.upper()}: {status}")
        
        print("\n✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_trading())