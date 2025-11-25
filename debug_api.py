import requests
import json
from config import Config

def test_api_connection():
    """API 연결 디버깅"""
    print("=== API 연결 디버깅 ===\n")
    
    try:
        # 환경 변수 확인
        print("1. 환경 변수 확인:")
        demo_info = Config.get_account_info('demo')
        print(f"   App Key: {demo_info['appkey'][:10]}...")
        print(f"   App Secret: {demo_info['appsecret'][:10]}...")
        print(f"   Account: {demo_info['account']}")
        
        # API 요청 테스트
        print("\n2. API 토큰 요청 테스트:")
        url = "https://openapivts.koreainvestment.com:29443/oauth2/tokenP"
        
        headers = {
            "content-type": "application/json"
        }
        
        body = {
            "grant_type": "client_credentials",
            "appkey": demo_info['appkey'],
            "appsecret": demo_info['appsecret']
        }
        
        print(f"   URL: {url}")
        print(f"   Headers: {headers}")
        print(f"   Body: {json.dumps({k: v[:20] + '...' if len(str(v)) > 20 else v for k, v in body.items()}, indent=4)}")
        
        response = requests.post(url, headers=headers, data=json.dumps(body))
        
        print(f"\n3. 응답 정보:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Response: {json.dumps(result, indent=4, ensure_ascii=False)}")
        else:
            print(f"   Error Response: {response.text}")
            
            # 추가 정보
            print(f"\n4. 추가 디버깅 정보:")
            print(f"   Request Headers Sent: {response.request.headers}")
            print(f"   Request Body Sent: {response.request.body}")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

def test_real_api():
    """실전투자 API도 테스트"""
    print("\n=== 실전투자 API 테스트 ===\n")
    
    try:
        real_info = Config.get_account_info('real')
        url = "https://openapi.koreainvestment.com:9443/oauth2/tokenP"
        
        headers = {
            "content-type": "application/json"
        }
        
        body = {
            "grant_type": "client_credentials",
            "appkey": real_info['appkey'],
            "appsecret": real_info['appsecret']
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(body))
        print(f"실전투자 API Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 실전투자 API 정상")
        else:
            print(f"❌ 실전투자 API 오류: {response.text}")
            
    except Exception as e:
        print(f"실전투자 API 테스트 오류: {e}")

if __name__ == "__main__":
    test_api_connection()
    test_real_api()