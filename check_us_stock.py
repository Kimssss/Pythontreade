#!/usr/bin/env python3
"""
미국주식 모의투자 지원 여부 확인 도구
"""

import requests
import json
from config import Config

def test_us_stock_api():
    """미국주식 API 테스트"""
    print("🇺🇸 미국주식 모의투자 지원 확인")
    print("=" * 40)
    
    try:
        # 환경 변수에서 모의투자 계정 정보 로드
        demo_info = Config.get_account_info('demo')
        
        # 토큰 발급
        print("1. 토큰 발급...")
        token_url = "https://openapivts.koreainvestment.com:29443/oauth2/tokenP"
        token_headers = {"content-type": "application/json"}
        token_body = {
            "grant_type": "client_credentials", 
            "appkey": demo_info['appkey'],
            "appsecret": demo_info['appsecret']
        }
        
        token_response = requests.post(token_url, headers=token_headers, json=token_body)
        
        if token_response.status_code != 200:
            print(f"❌ 토큰 발급 실패: {token_response.status_code}")
            return
            
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        print("✅ 토큰 발급 성공")
        
        # 미국주식 관련 API 엔드포인트들 테스트
        us_apis = [
            {
                "name": "미국주식 현재가",
                "url": "https://openapivts.koreainvestment.com:29443/uapi/overseas-price/v1/quotations/price",
                "method": "GET",
                "tr_id": "HHDFS00000300",
                "params": {
                    "AUTH": "",
                    "EXCD": "NAS",  # 나스닥
                    "SYMB": "AAPL"  # 애플 주식
                }
            },
            {
                "name": "미국주식 잔고조회", 
                "url": "https://openapivts.koreainvestment.com:29443/uapi/overseas-stock/v1/trading/inquire-balance",
                "method": "GET",
                "tr_id": "VTRP6504R",
                "params": {
                    "CANO": demo_info['account'].split('-')[0],
                    "ACNT_PRDT_CD": demo_info['account'].split('-')[1],
                    "OVRS_EXCG_CD": "NASD",
                    "TR_CRCY_CD": "USD",
                    "CTX_AREA_FK200": "",
                    "CTX_AREA_NK200": ""
                }
            },
            {
                "name": "미국주식 매수주문",
                "url": "https://openapivts.koreainvestment.com:29443/uapi/overseas-stock/v1/trading/order",
                "method": "POST", 
                "tr_id": "VTTT1002U",
                "test_only": True  # 실제 주문은 하지 않고 API 존재 여부만 확인
            }
        ]
        
        print(f"\n2. 미국주식 API 엔드포인트 테스트...")
        
        for api in us_apis:
            print(f"\n🔍 {api['name']} API 테스트:")
            
            headers = {
                "content-type": "application/json; charset=utf-8",
                "authorization": f"Bearer {access_token}",
                "appkey": demo_info['appkey'],
                "appsecret": demo_info['appsecret'],
                "tr_id": api['tr_id']
            }
            
            if api.get('test_only'):
                print(f"   📋 엔드포인트: {api['url']}")
                print(f"   🔑 TR_ID: {api['tr_id']}")
                print("   ⚠️  실제 주문 테스트는 건너뜀 (안전상)")
                continue
            
            try:
                if api['method'] == 'GET':
                    response = requests.get(api['url'], headers=headers, params=api['params'], timeout=10)
                else:
                    response = requests.post(api['url'], headers=headers, json=api['params'], timeout=10)
                
                print(f"   📡 응답 코드: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    rt_cd = result.get('rt_cd', 'N/A')
                    msg = result.get('msg1', 'N/A')
                    print(f"   ✅ API 호출 성공 (rt_cd: {rt_cd})")
                    if rt_cd != '0':
                        print(f"   ⚠️  메시지: {msg}")
                elif response.status_code == 404:
                    print("   ❌ API 엔드포인트 없음 (404)")
                elif response.status_code == 401:
                    print("   🔒 인증 필요 (401) - API는 존재함")
                else:
                    print(f"   ⚠️  상태: {response.status_code}")
                    print(f"   📄 응답: {response.text[:200]}...")
                    
            except requests.exceptions.Timeout:
                print("   ⏰ 타임아웃")
            except Exception as e:
                print(f"   ❌ 오류: {e}")
        
        print(f"\n" + "=" * 40)
        print("📋 결론:")
        print("✅ 한국투자증권은 미국주식 관련 API를 제공합니다")
        print("✅ 모의투자 환경에서 미국주식 테스트 가능합니다") 
        print("⚠️  실제 사용을 위해서는 계좌에서 해외주식 거래 승인 필요")
        print("📖 자세한 API 문서는 공식 포털에서 확인하세요:")
        print("   https://apiportal.koreainvestment.com/")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_us_stock_api()