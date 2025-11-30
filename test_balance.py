#!/usr/bin/env python3
"""
KIS API 잔고 조회 테스트
주말/장외시간 대응
"""
import os
import time
from datetime import datetime
from dotenv import load_dotenv
from ai_trading_system.utils.kis_api import KisAPIEnhanced

# .env 파일 로드
load_dotenv('ai_trading_system/.env')

def test_balance():
    """계좌 잔고 테스트"""
    # 환경 변수
    appkey = os.getenv('KIS_DEMO_APPKEY')
    appsecret = os.getenv('KIS_DEMO_APPSECRET')
    account = os.getenv('KIS_DEMO_ACCOUNT')
    
    if not all([appkey, appsecret, account]):
        print("❌ API 자격증명이 없습니다. .env 파일을 확인하세요.")
        return
    
    print("=== KIS API Balance Test ===")
    print(f"Time: {datetime.now()}")
    print(f"Account: {account}")
    print(f"Mode: Demo (모의투자)")
    print()
    
    # API 인스턴스 생성 - 주말은 더 긴 간격으로
    api = KisAPIEnhanced(
        appkey, 
        appsecret, 
        account, 
        is_real=False, 
        min_request_interval=2.0  # 주말 2초 간격
    )
    
    # 1. 토큰 발급
    print("1. 토큰 발급 중...")
    if not api.get_access_token():
        print("❌ 토큰 발급 실패")
        return
    print("✅ 토큰 발급 성공")
    print(f"   토큰 만료: {api.token_expire_time}")
    
    # 잠시 대기
    print("\n2초 대기 중...")
    time.sleep(2)
    
    # 2. 계좌 잔고 조회
    print("\n2. 계좌 잔고 조회 중...")
    try:
        balance = api.get_balance()
        
        if not balance:
            print("❌ 잔고 조회 실패 (응답 없음)")
            return
        
        print(f"Response code: {balance.get('rt_cd')}")
        print(f"Message: {balance.get('msg1', '')}")
        
        if balance.get('rt_cd') == '0':
            # 성공
            print("✅ 잔고 조회 성공")
            
            # 현금 정보 (output2)
            output2 = balance.get('output2', [])
            if output2 and len(output2) > 0:
                cash_data = output2[0]
                print("\n=== 💰 현금 잔고 ===")
                print(f"예수금총액: {float(cash_data.get('dnca_tot_amt', 0)):,.0f}원")
                print(f"주문가능현금: {float(cash_data.get('ord_psbl_cash', 0)):,.0f}원")
                print(f"예수금: {float(cash_data.get('prvs_rcdl_excc_amt', 0)):,.0f}원")
                print(f"출금가능금액: {float(cash_data.get('nrcvb_buy_amt', 0)):,.0f}원")
            
            # 보유 주식 (output1)
            output1 = balance.get('output1', [])
            holdings = []
            total_stock_value = 0
            
            for item in output1:
                qty = int(item.get('hldg_qty', 0))
                if qty > 0:
                    eval_amt = float(item.get('evlu_amt', 0))
                    total_stock_value += eval_amt
                    holdings.append({
                        'name': item.get('prdt_name', 'N/A'),
                        'code': item.get('pdno', ''),
                        'qty': qty,
                        'value': eval_amt,
                        'profit': float(item.get('evlu_pfls_amt', 0)),
                        'rate': float(item.get('evlu_pfls_rt', 0))
                    })
            
            if holdings:
                print(f"\n=== 📈 보유 주식 ({len(holdings)}종목) ===")
                for h in holdings[:5]:  # 상위 5개만 표시
                    print(f"{h['name']} ({h['code']})")
                    print(f"  - 수량: {h['qty']}주")
                    print(f"  - 평가금액: {h['value']:,.0f}원")
                    print(f"  - 손익: {h['profit']:,.0f}원 ({h['rate']:.2f}%)")
            else:
                print("\n=== 📈 보유 주식 ===")
                print("보유 주식이 없습니다.")
            
            # 총 자산
            print("\n=== 💼 총 자산 ===")
            cash = float(cash_data.get('ord_psbl_cash', 0)) if output2 else 0
            total = cash + total_stock_value
            print(f"현금: {cash:,.0f}원")
            print(f"주식: {total_stock_value:,.0f}원")
            print(f"총계: {total:,.0f}원")
            
        else:
            # 실패
            print("❌ 잔고 조회 실패")
            print(f"Error code: {balance.get('rt_cd')}")
            print(f"Error msg: {balance.get('msg1', '')}")
            
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_balance()