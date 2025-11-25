#!/usr/bin/env python3
"""
미국주식 API 토큰 문제 해결 및 테스트
"""

import requests
import json
import time
from config import Config

def test_token_methods():
    """다양한 토큰 발급 방식 테스트"""
    print("🔑 미국주식 API 토큰 발급 방식 테스트")
    print("=" * 50)
    
    demo_info = Config.get_account_info('demo')
    
    # 방법 1: 기존 방식
    print("1️⃣ 기존 토큰 발급 방식...")
    try:
        url1 = "https://openapivts.koreainvestment.com:29443/oauth2/tokenP"
        headers1 = {"content-type": "application/json"}
        body1 = {
            "grant_type": "client_credentials",
            "appkey": demo_info['appkey'],
            "appsecret": demo_info['appsecret']
        }
        
        response1 = requests.post(url1, headers=headers1, json=body1)
        print(f"   상태코드: {response1.status_code}")
        
        if response1.status_code == 200:
            token1 = response1.json().get('access_token')
            print(f"   토큰: {token1[:30]}...")
            
            # 즉시 미국주식 API 테스트
            test_us_api_with_token(token1, demo_info, "기존방식")
        else:
            print(f"   실패: {response1.text}")
            
    except Exception as e:
        print(f"   오류: {e}")
    
    print("\n" + "-" * 50)
    
    # 방법 2: Approval 타입 토큰
    print("2️⃣ Approval 토큰 발급 방식...")
    try:
        url2 = "https://openapivts.koreainvestment.com:29443/oauth2/Approval"
        headers2 = {
            "content-type": "application/json; charset=utf-8"
        }
        body2 = {
            "grant_type": "client_credentials",
            "appkey": demo_info['appkey'],
            "secretkey": demo_info['appsecret']  # secretkey로 변경
        }
        
        response2 = requests.post(url2, headers=headers2, json=body2)
        print(f"   상태코드: {response2.status_code}")
        
        if response2.status_code == 200:
            result2 = response2.json()
            approval_key = result2.get('approval_key')
            print(f"   Approval Key: {approval_key[:30] if approval_key else 'None'}...")
            
            # approval_key로 미국주식 API 테스트
            if approval_key:
                test_us_api_with_approval(approval_key, demo_info, "Approval방식")
        else:
            print(f"   실패: {response2.text}")
            
    except Exception as e:
        print(f"   오류: {e}")
    
    print("\n" + "-" * 50)
    
    # 방법 3: 해외주식 전용 엔드포인트 확인
    print("3️⃣ 해외주식 전용 토큰 엔드포인트 탐색...")
    
    test_endpoints = [
        "https://openapivts.koreainvestment.com:29443/oauth2/tokenP",
        "https://openapivts.koreainvestment.com:29443/oauth2/token", 
        "https://openapivts.koreainvestment.com:29443/uapi/overseas-stock/oauth2/token"
    ]
    
    for endpoint in test_endpoints:
        try:
            print(f"\n   🔗 테스트: {endpoint}")
            headers = {"content-type": "application/json"}
            body = {
                "grant_type": "client_credentials",
                "appkey": demo_info['appkey'],
                "appsecret": demo_info['appsecret']
            }
            
            response = requests.post(endpoint, headers=headers, json=body, timeout=10)
            print(f"   상태코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                token = result.get('access_token')
                if token:
                    print(f"   ✅ 토큰 발급 성공: {token[:20]}...")
                    # 즉시 테스트
                    test_us_api_with_token(token, demo_info, f"엔드포인트_{endpoint.split('/')[-1]}")
            else:
                print(f"   응답: {response.text[:100]}")
                
        except Exception as e:
            print(f"   오류: {e}")

def test_us_api_with_token(token, demo_info, method_name):
    """토큰으로 미국주식 API 테스트"""
    print(f"\n   🇺🇸 {method_name} 토큰으로 미국주식 API 테스트:")
    
    try:
        url = "https://openapivts.koreainvestment.com:29443/uapi/overseas-price/v1/quotations/price"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey": demo_info['appkey'],
            "appsecret": demo_info['appsecret'],
            "tr_id": "HHDFS00000300"
        }
        
        params = {
            "AUTH": "",
            "EXCD": "NAS",
            "SYMB": "AAPL"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"   📡 응답코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            rt_cd = result.get('rt_cd')
            msg = result.get('msg1', '')
            
            print(f"   📊 rt_cd: {rt_cd}, 메시지: {msg}")
            
            if rt_cd == '0':
                output = result.get('output', {})
                price = output.get('last', 'N/A')
                print(f"   🍎 애플 현재가: ${price}")
                print(f"   ✅ {method_name} 성공!")
                return True
            else:
                print(f"   ❌ API 오류: {msg}")
        else:
            error_text = response.text
            print(f"   ❌ HTTP 오류: {error_text[:200]}")
            
    except Exception as e:
        print(f"   ❌ 테스트 오류: {e}")
    
    return False

def test_us_api_with_approval(approval_key, demo_info, method_name):
    """Approval Key로 미국주식 API 테스트"""
    print(f"\n   🇺🇸 {method_name} 키로 미국주식 API 테스트:")
    
    try:
        url = "https://openapivts.koreainvestment.com:29443/uapi/overseas-price/v1/quotations/price"
        
        headers = {
            "content-type": "application/json; charset=utf-8", 
            "appkey": demo_info['appkey'],
            "appsecret": demo_info['appsecret'],
            "tr_id": "HHDFS00000300"
        }
        
        # Approval 방식에서는 다른 헤더 사용 가능
        if approval_key:
            headers["approval_key"] = approval_key
            # 또는 headers["authorization"] = f"Bearer {approval_key}"
        
        params = {
            "AUTH": "",
            "EXCD": "NAS", 
            "SYMB": "AAPL"
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"   📡 응답코드: {response.status_code}")
        print(f"   📄 응답: {response.text[:200]}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"   ❌ 테스트 오류: {e}")
        return False

if __name__ == "__main__":
    test_token_methods()