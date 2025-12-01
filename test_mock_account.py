#!/usr/bin/env python3
"""
모의투자 계좌 설정 확인 및 테스트
"""
import os
import sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

os.environ['KIS_DEMO_APPKEY'] = 'PSpRavS44ke8s1UZ8sn8VuOiXIXEE2QcMj2I'
os.environ['KIS_DEMO_APPSECRET'] = 'acvrN9QSZYfam2V2rAEyFsUisSv1dyDo8kXD3JXHeGQUqxLtZrQYngSlb/RVqhsxuAhPnbJodPXyakzqrxbsBX54ZOZnkduxKFnqqEqxgFte+UjmZvxgyRPx4BrxzUnZY6zEH3qh9n8tzDm6J6oEdyVURXIES26lIEca5BZ7+YyHgG87YKQ='
os.environ['KIS_DEMO_ACCOUNT'] = '50144239-01'

from ai_trading_system.utils.kis_api import KisAPIEnhanced

def test_mock_account():
    """모의투자 계좌 테스트"""
    print("=" * 60)
    print("🏦 모의투자 계좌 확인")
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
    
    # 토큰 발급
    print("\n1️⃣ 토큰 발급")
    print("-" * 40)
    
    if api.get_access_token():
        print("✅ 토큰 발급 성공!")
        print(f"토큰: {api.access_token[:20]}...")
    else:
        print("❌ 토큰 발급 실패")
        return
    
    # 계좌 잔고 상세 조회
    print("\n2️⃣ 계좌 잔고 상세")
    print("-" * 40)
    
    balance = api.get_balance()
    if balance and balance.get('rt_cd') == '0':
        output2 = balance.get('output2', [])
        if output2:
            data = output2[0]
            print(f"예수금총금액: {int(data.get('dnca_tot_amt', 0)):,}원")
            print(f"익일정산금액: {int(data.get('nxdy_excc_amt', 0)):,}원")
            print(f"주문가능현금: {int(data.get('ord_psbl_cash', 0)):,}원")
            print(f"출금가능금액: {int(data.get('prvs_rcdl_excc_amt', 0)):,}원")
            print(f"대용금액: {int(data.get('sma_evlu_amt', 0)):,}원")
            print(f"수표금액: {int(data.get('bfdy_cprs_amt', 0)):,}원")
            # 대출 관련 필드는 문자열일 수 있으므로 제외
            
            # output1도 확인
            output1 = balance.get('output1', [])
            if output1:
                print("\n보유 종목:")
                for stock in output1[:5]:  # 최대 5개만 표시
                    print(f"  - {stock.get('prdt_name')} ({stock.get('pdno')})")
                    print(f"    수량: {stock.get('hldg_qty')}주")
                    print(f"    평가금액: {int(stock.get('evlu_amt', 0)):,}원")
    else:
        print(f"❌ 잔고 조회 실패: {balance}")
    
    # 계좌 종류 확인
    print("\n3️⃣ 계좌 정보")
    print("-" * 40)
    print(f"API URL: {api.base_url}")
    print(f"모의투자 여부: {'예' if not api.is_real else '아니오'}")
    
    # 간단한 종목 조회로 API 동작 확인
    print("\n4️⃣ API 동작 확인 (삼성전자 조회)")
    print("-" * 40)
    
    price = api.get_stock_price('005930')
    if price and price.get('rt_cd') == '0':
        output = price.get('output', {})
        print(f"종목명: 삼성전자")
        print(f"현재가: {output.get('stck_prpr', 'N/A')}원")
        print(f"전일대비: {output.get('prdy_ctrt', 'N/A')}%")
        print("✅ API 정상 동작 확인")
    else:
        print("❌ 종목 조회 실패")
    
    # 모의투자 주문 가능 여부 테스트
    print("\n5️⃣ 모의투자 주문 가능 여부")
    print("-" * 40)
    
    # ETF로 시도 (보통 모의투자에서 가능)
    test_result = api.buy_stock(
        stock_code='069500',  # KODEX 200
        quantity=1,
        order_type="01",  # 지정가
        price=43000  # 대략적인 가격
    )
    
    if test_result:
        rt_cd = test_result.get('rt_cd')
        msg1 = test_result.get('msg1')
        
        print(f"응답코드: {rt_cd}")
        print(f"메시지: {msg1}")
        
        if rt_cd == '0':
            print("✅ 모의투자 주문 가능!")
            # 주문 취소
            output = test_result.get('output', {})
            if output.get('ODNO'):
                print(f"주문번호: {output['ODNO']} (테스트 완료)")
        elif '모의투자 주문이 불가한 계좌' in msg1:
            print("\n⚠️ 이 계좌는 모의투자 주문이 불가능합니다.")
            print("해결 방법:")
            print("1. 한국투자증권 홈페이지/앱에 로그인")
            print("2. 모의투자 메뉴로 이동")
            print("3. 모의투자 참가 신청")
            print("4. 가상머니 충전 (보통 1억원)")
            print("5. 모의투자 약관 동의")
        elif '주문가능현금이 부족합니다' in msg1:
            print("\n⚠️ 모의투자 계좌에 가상머니가 없습니다.")
            print("한국투자증권에서 가상머니를 충전하세요.")
        else:
            print(f"\n❓ 기타 오류: {msg1}")
    
    print("\n✅ 계좌 확인 완료")
    
    # 현재 시장 상태 확인
    print("\n6️⃣ 시장 상태")
    print("-" * 40)
    now = datetime.now()
    print(f"현재 시간: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"요일: {['월','화','수','목','금','토','일'][now.weekday()]}요일")
    
    if now.weekday() >= 5:
        print("🔴 주말 - 모든 시장 마감")
    else:
        if 9 <= now.hour < 15.5:
            print("🟢 한국 시장 거래 가능")
        elif (now.hour >= 22.5) or (now.hour < 5):
            print("🟢 미국 시장 거래 가능")
        else:
            print("🔴 현재 거래 시간이 아닙니다")

if __name__ == "__main__":
    test_mock_account()