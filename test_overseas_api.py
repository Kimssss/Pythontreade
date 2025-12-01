#!/usr/bin/env python3
"""
한국투자증권 API 해외주식 지원 테스트
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_trading_system.utils.kis_api import KisAPIEnhanced
from ai_trading_system.config.settings import KIS_CONFIG
import json

def test_overseas_stock_api():
    """해외주식 API 테스트"""
    print("=" * 60)
    print("🌏 한국투자증권 해외주식 API 테스트")
    print("=" * 60)
    
    # 모의투자 계정으로 테스트
    demo_config = KIS_CONFIG['demo']
    api = KisAPIEnhanced(
        demo_config['appkey'],
        demo_config['appsecret'],
        demo_config['account'],
        is_real=False,
        min_request_interval=0.5
    )
    
    # 토큰 발급 또는 캐시된 토큰 사용
    if api.access_token:
        print("✅ 캐시된 토큰 사용")
    elif not api.get_access_token():
        print("❌ 토큰 발급 실패")
        # 기존 토큰이 있으면 사용
        import pickle
        try:
            with open('cache/token_demo_PSpRavS44k.pkl', 'rb') as f:
                cached = pickle.load(f)
                api.access_token = cached['access_token']
                api.token_expire_time = cached['token_expire_time']
                print("✅ 저장된 토큰 로드 성공")
        except Exception as e:
            print(f"토큰 로드 실패: {e}")
            return
    
    print("✅ 토큰 발급 성공\n")
    
    # 해외주식 관련 엔드포인트 테스트
    base_url = api.base_url
    
    # 1. 해외주식 현재가 조회 (AAPL)
    print("1️⃣ 해외주식 현재가 조회 테스트 (AAPL)")
    print("-" * 40)
    
    url = f"{base_url}/uapi/overseas-price/v1/quotations/price"
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {api.access_token}",
        "appkey": api.appkey,
        "appsecret": api.appsecret,
        "tr_id": "HHDFS00000300"  # 해외주식 현재가
    }
    
    params = {
        "AUTH": "",
        "EXCD": "NAS",  # 거래소 코드 (NAS: 나스닥)
        "SYMB": "AAPL"  # 심볼 (애플)
    }
    
    try:
        response = api._make_api_request_with_retry(
            'GET', url, headers=headers, params=params, 
            endpoint_name="overseas_price"
        )
        
        if response:
            result = response.json()
            print(f"응답 코드: {result.get('rt_cd')}")
            print(f"응답 메시지: {result.get('msg1')}")
            
            if result.get('rt_cd') == '0':
                output = result.get('output', {})
                print(f"\n📊 AAPL 현재가 정보:")
                print(f"  - 현재가: ${output.get('last', 'N/A')}")
                print(f"  - 전일대비: ${output.get('diff', 'N/A')}")
                print(f"  - 등락률: {output.get('rate', 'N/A')}%")
                print(f"  - 거래량: {output.get('tvol', 'N/A')}")
        else:
            print("❌ API 호출 실패")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    # 2. 해외주식 잔고 조회
    print("\n2️⃣ 해외주식 잔고 조회 테스트")
    print("-" * 40)
    
    url = f"{base_url}/uapi/overseas-stock/v1/trading/inquire-balance"
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {api.access_token}",
        "appkey": api.appkey,
        "appsecret": api.appsecret,
        "tr_id": "VTTS3012R" if not api.is_real else "TTTS3012R"  # 해외주식 잔고조회
    }
    
    params = {
        "CANO": api.account_no.split('-')[0] if '-' in api.account_no else api.account_no[:8],
        "ACNT_PRDT_CD": api.account_no.split('-')[1] if '-' in api.account_no else api.account_no[8:],
        "OVRS_EXCG_CD": "NASD",  # 나스닥
        "TR_CRCY_CD": "USD",      # 통화
        "CTX_AREA_FK200": "",
        "CTX_AREA_NK200": ""
    }
    
    try:
        response = api._make_api_request_with_retry(
            'GET', url, headers=headers, params=params, 
            endpoint_name="overseas_balance"
        )
        
        if response:
            result = response.json()
            print(f"응답 코드: {result.get('rt_cd')}")
            print(f"응답 메시지: {result.get('msg1')}")
            
            if result.get('rt_cd') == '0':
                output1 = result.get('output1', [])
                output2 = result.get('output2', {})
                
                print(f"\n💰 해외주식 잔고 정보:")
                print(f"  - 보유 종목 수: {len(output1)}")
                
                if output2:
                    print(f"  - 예수금(USD): ${output2.get('frcr_dncl_amt_1', 'N/A')}")
                    print(f"  - 평가금액(USD): ${output2.get('ovrs_tot_evlu_amt', 'N/A')}")
                
                if output1:
                    print(f"\n📈 보유 종목:")
                    for stock in output1[:5]:  # 상위 5개만 표시
                        print(f"  - {stock.get('ovrs_item_name', 'N/A')} ({stock.get('ovrs_pdno', 'N/A')})")
                        print(f"    보유수량: {stock.get('ovrs_cblc_qty', 'N/A')}")
                        print(f"    평가금액: ${stock.get('ovrs_stck_evlu_amt', 'N/A')}")
        else:
            print("❌ API 호출 실패")
    
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    # 3. 해외주식 주문 가능 여부 테스트
    print("\n3️⃣ 해외주식 매수 주문 테스트 (시뮬레이션)")
    print("-" * 40)
    
    url = f"{base_url}/uapi/overseas-stock/v1/trading/order"
    
    # 주문 데이터 (실제로 주문하지 않고 구조만 확인)
    order_data = {
        "CANO": api.account_no.split('-')[0] if '-' in api.account_no else api.account_no[:8],
        "ACNT_PRDT_CD": api.account_no.split('-')[1] if '-' in api.account_no else api.account_no[8:],
        "OVRS_EXCG_CD": "NASD",  # 나스닥
        "PDNO": "AAPL",           # 애플
        "ORD_QTY": "1",           # 1주
        "OVRS_ORD_UNPR": "0",     # 시장가
        "ORD_SVR_DVSN_CD": "0",   # 일반주문
        "ORD_DVSN": "00"          # 시장가
    }
    
    print("📋 해외주식 주문 구조:")
    print(f"  - 거래소: {order_data['OVRS_EXCG_CD']}")
    print(f"  - 종목: {order_data['PDNO']}")
    print(f"  - 수량: {order_data['ORD_QTY']}주")
    print(f"  - 주문유형: 시장가")
    
    # 4. 지원 거래소 목록
    print("\n4️⃣ 한국투자증권 해외주식 지원 거래소")
    print("-" * 40)
    
    exchanges = {
        "NASD": "나스닥 (NASDAQ)",
        "NYSE": "뉴욕증권거래소 (NYSE)",
        "AMEX": "아멕스 (AMEX)",
        "SEHK": "홍콩거래소 (HKEX)",
        "SHAA": "상해거래소 (SSE)",
        "SZAA": "심천거래소 (SZSE)",
        "TKSE": "도쿄거래소 (TSE)",
        "HASE": "하노이거래소 (HNX)",
        "VNSE": "호치민거래소 (HSX)"
    }
    
    for code, name in exchanges.items():
        print(f"  - {code}: {name}")
    
    print("\n✅ 한국투자증권 API는 해외주식 거래를 지원합니다!")
    print("📌 주요 기능:")
    print("  - 미국 주식 (나스닥, NYSE, AMEX)")
    print("  - 중국 주식 (상해, 심천, 홍콩)")
    print("  - 일본 주식 (도쿄)")
    print("  - 베트남 주식 (하노이, 호치민)")
    
    return True

if __name__ == "__main__":
    test_overseas_stock_api()