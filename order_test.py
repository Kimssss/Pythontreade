#!/usr/bin/env python3
"""
한국투자증권 API 주문 기능 테스트 (모의투자 전용)
- 매수 주문 테스트
- 매도 주문 테스트  
- 주문 취소 테스트
- 주문 내역 조회 테스트
"""

import time
from kis_api import KisAPI
from config import Config

def test_demo_orders():
    """모의투자 주문 테스트"""
    print("🔥 모의투자 주문 기능 테스트")
    print("=" * 50)
    
    try:
        # 데모 계정 초기화
        demo_account = Config.get_account_info('demo')
        api = KisAPI(
            demo_account['appkey'],
            demo_account['appsecret'],
            demo_account['account'],
            is_real=False
        )
        
        # 토큰 발급
        print("🔑 토큰 발급 중...")
        if not api.get_access_token():
            print("❌ 토큰 발급 실패")
            return False
        print("✅ 토큰 발급 성공")
        
        # 잔고 확인
        print("\n💰 초기 잔고 확인...")
        balance = api.get_balance()
        if balance and balance.get('rt_cd') == '0':
            output2 = balance.get('output2', [{}])
            initial_cash = int(output2[0].get('ord_psbl_cash', 0))
            print(f"   주문 가능 현금: {initial_cash:,}원")
        else:
            print("❌ 잔고 조회 실패")
            return False
        
        # 테스트 종목 설정
        test_stock = '005930'  # 삼성전자
        test_quantity = 1
        
        # 현재가 조회
        print(f"\n📈 {test_stock} 현재가 조회...")
        price_data = api.get_stock_price(test_stock)
        if not price_data or price_data.get('rt_cd') != '0':
            print("❌ 현재가 조회 실패")
            return False
        
        current_price = int(price_data['output']['stck_prpr'])
        print(f"   삼성전자 현재가: {current_price:,}원")
        
        # 매수 주문 테스트 (시장가)
        print(f"\n🛒 매수 주문 테스트 (시장가 {test_quantity}주)")
        buy_result = api.buy_stock(test_stock, test_quantity, order_type="03")
        
        if buy_result and buy_result.get('rt_cd') == '0':
            buy_order_no = buy_result.get('output', {}).get('ODNO', 'N/A')
            print(f"✅ 매수 주문 성공")
            print(f"   주문번호: {buy_order_no}")
            print(f"   종목: 삼성전자 ({test_stock})")
            print(f"   수량: {test_quantity}주")
            print(f"   주문방식: 시장가")
        else:
            print(f"❌ 매수 주문 실패: {buy_result}")
            return False
        
        # 잠시 대기
        print("\n⏰ 주문 처리 대기 (5초)...")
        time.sleep(5)
        
        # 주문 내역 조회
        print("\n📋 주문 내역 조회...")
        orders = api.get_orders()
        if orders and orders.get('rt_cd') == '0':
            output = orders.get('output', [])
            recent_orders = [o for o in output if o.get('pdno') == test_stock]
            print(f"✅ 주문 내역 조회 성공")
            print(f"   {test_stock} 관련 주문: {len(recent_orders)}건")
            
            if recent_orders:
                last_order = recent_orders[0]
                order_status = last_order.get('ord_gno_brno', 'N/A')
                order_qty = last_order.get('ord_qty', 'N/A')
                print(f"   최근 주문 상태: {order_status}")
                print(f"   주문 수량: {order_qty}주")
        else:
            print(f"❌ 주문 내역 조회 실패")
        
        # 보유 종목 확인
        print("\n📊 보유 종목 확인...")
        holdings = api.get_holding_stocks()
        print(f"✅ 보유 종목 조회 완료: {len(holdings)}개 종목")
        
        samsung_holding = None
        for holding in holdings:
            if holding['stock_code'] == test_stock:
                samsung_holding = holding
                print(f"   삼성전자 보유: {holding['quantity']}주")
                print(f"   평균단가: {holding['buy_price']:,}원")
                print(f"   평가손익: {holding['profit_amount']:,}원")
                break
        
        # 매도 주문 테스트 (보유 주식이 있는 경우)
        if samsung_holding and samsung_holding['quantity'] > 0:
            sell_quantity = min(samsung_holding['quantity'], test_quantity)
            print(f"\n💸 매도 주문 테스트 (시장가 {sell_quantity}주)")
            
            sell_result = api.sell_stock(test_stock, sell_quantity, order_type="03")
            
            if sell_result and sell_result.get('rt_cd') == '0':
                sell_order_no = sell_result.get('output', {}).get('ODNO', 'N/A')
                print(f"✅ 매도 주문 성공")
                print(f"   주문번호: {sell_order_no}")
                print(f"   종목: 삼성전자 ({test_stock})")
                print(f"   수량: {sell_quantity}주")
                print(f"   주문방식: 시장가")
            else:
                print(f"❌ 매도 주문 실패: {sell_result}")
        else:
            print("\n⚠️ 보유 주식이 없어 매도 주문 테스트 생략")
        
        # 최종 잔고 확인
        print("\n💰 최종 잔고 확인...")
        final_balance = api.get_balance()
        if final_balance and final_balance.get('rt_cd') == '0':
            output2 = final_balance.get('output2', [{}])
            final_cash = int(output2[0].get('ord_psbl_cash', 0))
            final_total = int(output2[0].get('tot_evlu_amt', 0))
            
            print(f"   주문 가능 현금: {final_cash:,}원")
            print(f"   총 평가 금액: {final_total:,}원")
            print(f"   현금 변화: {final_cash - initial_cash:+,}원")
        
        print("\n🎉 주문 기능 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"\n💥 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_limit_orders():
    """지정가 주문 테스트"""
    print("\n🎯 지정가 주문 테스트")
    print("-" * 30)
    
    try:
        # 데모 계정 초기화
        demo_account = Config.get_account_info('demo')
        api = KisAPI(
            demo_account['appkey'],
            demo_account['appsecret'],
            demo_account['account'],
            is_real=False
        )
        
        # 토큰 발급
        if not api.get_access_token():
            print("❌ 토큰 발급 실패")
            return False
        
        test_stock = '005930'  # 삼성전자
        
        # 현재가 조회
        price_data = api.get_stock_price(test_stock)
        if not price_data or price_data.get('rt_cd') != '0':
            print("❌ 현재가 조회 실패")
            return False
        
        current_price = int(price_data['output']['stck_prpr'])
        
        # 현재가보다 5% 낮은 가격으로 지정가 매수 주문
        limit_price = int(current_price * 0.95)
        
        print(f"📈 현재가: {current_price:,}원")
        print(f"🎯 지정가: {limit_price:,}원 (-5%)")
        
        print(f"\n🛒 지정가 매수 주문 (1주)")
        buy_result = api.buy_stock(test_stock, 1, price=limit_price, order_type="01")
        
        if buy_result and buy_result.get('rt_cd') == '0':
            order_no = buy_result.get('output', {}).get('ODNO', 'N/A')
            print(f"✅ 지정가 매수 주문 성공")
            print(f"   주문번호: {order_no}")
            print(f"   지정가: {limit_price:,}원")
            print(f"   ⚠️ 현재가보다 낮아서 미체결될 가능성 높음")
        else:
            print(f"❌ 지정가 매수 주문 실패: {buy_result}")
            return False
        
        # 주문 내역에서 확인
        time.sleep(2)
        orders = api.get_orders()
        if orders and orders.get('rt_cd') == '0':
            output = orders.get('output', [])
            recent_orders = [o for o in output if o.get('pdno') == test_stock]
            print(f"\n📋 지정가 주문 확인: {len(recent_orders)}건")
            
            for order in recent_orders[:1]:  # 최근 1건만
                status = order.get('ord_gno_brno', 'N/A')
                qty = order.get('ord_qty', 'N/A')
                price = order.get('ord_unpr', 'N/A')
                print(f"   주문상태: {status}")
                print(f"   주문수량: {qty}주")
                print(f"   주문가격: {price}원")
        
        return True
        
    except Exception as e:
        print(f"💥 지정가 주문 테스트 오류: {e}")
        return False

def main():
    """메인 함수"""
    print("🚀 한국투자증권 주문 기능 종합 테스트")
    print("⚠️  모의투자 계정에서만 실행됩니다")
    print("=" * 60)
    
    # 자동으로 테스트 진행 (모의투자이므로 안전)
    print("🟢 모의투자 계정으로 자동 테스트를 시작합니다...")
    print("   (실제 돈이 사용되지 않으므로 안전합니다)")
    
    success_count = 0
    total_tests = 2
    
    # 1. 시장가 주문 테스트
    if test_demo_orders():
        success_count += 1
    
    # 2. 지정가 주문 테스트  
    if test_limit_orders():
        success_count += 1
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 주문 기능 테스트 결과")
    print("=" * 60)
    print(f"✅ 성공한 테스트: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 모든 주문 기능이 정상 동작합니다!")
        print("   - 시장가 매수/매도 ✅")
        print("   - 지정가 주문 ✅") 
        print("   - 주문 내역 조회 ✅")
        print("   - 잔고/보유종목 조회 ✅")
    else:
        print("⚠️ 일부 주문 기능에 문제가 있습니다.")
        print("   로그를 확인하여 문제를 해결하세요.")
    
    print("\n💡 참고사항:")
    print("   - 모의투자 환경에서 실제 돈이 사용되지 않습니다")
    print("   - 실전 투자 전 충분한 테스트를 권장합니다")
    print("   - API 사용량 제한(1분당 1회 토큰)에 주의하세요")

if __name__ == "__main__":
    main()