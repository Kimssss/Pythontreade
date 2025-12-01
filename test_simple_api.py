#!/usr/bin/env python3
"""
한국투자증권 API 간단한 테스트
"""
import os
import sys
import json
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 환경변수 직접 설정
os.environ['KIS_DEMO_APPKEY'] = 'PSpRavS44ke8s1UZ8sn8VuOiXIXEE2QcMj2I'
os.environ['KIS_DEMO_APPSECRET'] = 'acvrN9QSZYfam2V2rAEyFsUisSv1dyDo8kXD3JXHeGQUqxLtZrQYngSlb/RVqhsxuAhPnbJodPXyakzqrxbsBX54ZOZnkduxKFnqqEqxgFte+UjmZvxgyRPx4BrxzUnZY6zEH3qh9n8tzDm6J6oEdyVURXIES26lIEca5BZ7+YyHgG87YKQ='
os.environ['KIS_DEMO_ACCOUNT'] = '50144239-01'

from ai_trading_system.utils.kis_api import KisAPIEnhanced

def test_simple():
    """간단한 API 테스트"""
    print("=" * 60)
    print("🧪 한국투자증권 API 간단한 테스트")
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
    
    print(f"계좌번호: {api.account_no}")
    
    # 캐시된 토큰 로드
    import pickle
    try:
        with open('cache/token_demo_PSpRavS44k.pkl', 'rb') as f:
            cached = pickle.load(f)
            api.access_token = cached['access_token']
            api.token_expire_time = cached['token_expire_time']
            print("✅ 캐시된 토큰 로드 성공")
    except:
        print("토큰 캐시 없음")
    
    # 1. 잔고 조회
    print("\n1️⃣ 잔고 조회")
    print("-" * 40)
    try:
        cash = api.get_available_cash()
        print(f"가용 현금: {cash:,.0f}원")
    except Exception as e:
        print(f"오류: {e}")
    
    # 2. 거래량 순위
    print("\n2️⃣ 거래량 순위 (KOSPI)")
    print("-" * 40)
    try:
        stocks = api.get_volume_rank(market="KOSPI")
        if stocks:
            print(f"조회된 종목 수: {len(stocks)}개")
            for i, stock in enumerate(stocks[:5], 1):
                print(f"{i}. {stock['name']} ({stock['code']}): {stock['price']:,}원, 거래량: {stock['volume']:,}")
        else:
            print("거래량 순위 조회 실패")
    except Exception as e:
        print(f"오류: {e}")
    
    # 3. 삼성전자 현재가
    print("\n3️⃣ 삼성전자 현재가")
    print("-" * 40)
    try:
        price_info = api.get_stock_price('005930')
        if price_info and price_info.get('rt_cd') == '0':
            output = price_info.get('output', {})
            print(f"현재가: {int(output.get('stck_prpr', 0)):,}원")
            print(f"전일대비: {output.get('prdy_vrss', 'N/A')}원")
            print(f"등락률: {output.get('prdy_ctrt', 'N/A')}%")
        else:
            print(f"현재가 조회 실패: {price_info}")
    except Exception as e:
        print(f"오류: {e}")
    
    # 4. 매수 가능 테스트
    print("\n4️⃣ 매수 가능 여부 테스트")
    print("-" * 40)
    try:
        # 적당한 가격의 종목 찾기
        if stocks and cash > 0:
            test_stock = None
            for stock in stocks:
                if 5000 <= stock['price'] <= 50000:
                    test_stock = stock
                    break
            
            if test_stock:
                print(f"테스트 종목: {test_stock['name']} ({test_stock['code']})")
                print(f"현재가: {test_stock['price']:,}원")
                
                # 1주만 매수 시도
                print("\n매수 주문 시도 (1주)...")
                result = api.buy_stock(
                    test_stock['code'],
                    quantity=1,
                    order_type="03"  # 시장가
                )
                
                if result:
                    if result.get('rt_cd') == '0':
                        print("✅ 매수 주문 성공!")
                        print(f"주문번호: {result.get('output', {}).get('odno')}")
                    else:
                        print(f"매수 주문 실패: {result.get('msg1')}")
                else:
                    print("매수 주문 응답 없음")
            else:
                print("적절한 테스트 종목을 찾을 수 없음")
        else:
            print("잔고가 없거나 종목 정보가 없어 매수 테스트 불가")
    except Exception as e:
        print(f"매수 테스트 오류: {e}")
    
    # 5. 해외주식 테스트
    print("\n5️⃣ 해외주식 API 테스트")
    print("-" * 40)
    try:
        api.initialize_overseas_api()
        print("✅ 해외주식 API 초기화 성공")
        
        # AAPL 현재가
        print("\nAAPL 현재가 조회...")
        aapl = api.overseas.get_overseas_price('NASD', 'AAPL')
        if aapl:
            print(f"Apple Inc. (AAPL)")
            print(f"현재가: ${aapl['current_price']}")
            print(f"변동률: {aapl['change_rate']}%")
        else:
            print("AAPL 조회 실패")
            
    except Exception as e:
        print(f"해외주식 테스트 오류: {e}")
    
    print("\n✅ 테스트 완료!")

if __name__ == "__main__":
    test_simple()