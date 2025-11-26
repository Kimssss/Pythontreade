#!/usr/bin/env python3
"""
시스템 상태 확인 도구
"""

import requests
import os
from config import Config

def check_environment():
    """환경 설정 확인"""
    print("🔍 환경 설정 확인")
    print("-" * 30)
    
    # .env 파일 존재 확인
    if os.path.exists('.env'):
        print("✅ .env 파일 존재")
    else:
        print("❌ .env 파일 없음")
        return False
    
    # 환경 변수 확인
    try:
        demo_info = Config.get_account_info('demo')
        real_info = Config.get_account_info('real')
        
        print("✅ 모의투자 API 키 로드됨")
        print("✅ 실전투자 API 키 로드됨")
        return True
    except Exception as e:
        print(f"❌ 환경 변수 오류: {e}")
        return False

def check_network():
    """네트워크 연결 확인"""
    print("\n🌐 네트워크 연결 확인")
    print("-" * 30)
    
    test_urls = [
        "https://google.com",
        "https://openapivts.koreainvestment.com:29443",
        "https://openapi.koreainvestment.com:9443"
    ]
    
    for url in test_urls:
        try:
            response = requests.get(url, timeout=5)
            if url == "https://google.com":
                print("✅ 인터넷 연결 정상")
            elif "openapivts" in url:
                print("✅ 모의투자 서버 연결 가능")
            else:
                print("✅ 실전투자 서버 연결 가능")
        except Exception as e:
            if "google" in url:
                print(f"❌ 인터넷 연결 문제: {e}")
                return False
            else:
                print(f"⚠️  {url} 연결 불안정: {e}")
    
    return True

def check_api_status():
    """API 상태 확인"""
    print("\n🔌 API 상태 확인")
    print("-" * 30)
    
    try:
        demo_info = Config.get_account_info('demo')
        
        # 토큰 발급 테스트
        url = "https://openapivts.koreainvestment.com:29443/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": demo_info['appkey'],
            "appsecret": demo_info['appsecret']
        }
        
        response = requests.post(url, headers=headers, json=body, timeout=10)
        
        if response.status_code == 200:
            print("✅ 모의투자 API 토큰 발급 성공")
            return True
        else:
            print(f"❌ 모의투자 API 오류 (상태코드: {response.status_code})")
            print(f"   응답: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API 테스트 중 오류: {e}")
        return False

def check_packages():
    """패키지 설치 확인"""
    print("\n📦 패키지 확인")
    print("-" * 30)
    
    required_packages = ['requests', 'python-dotenv']
    
    for package in required_packages:
        try:
            if package == 'python-dotenv':
                import dotenv
            else:
                __import__(package)
            print(f"✅ {package} 설치됨")
        except ImportError:
            print(f"❌ {package} 설치 필요")
            return False
    
    return True

def main():
    """종합 건강 검진"""
    print("=" * 50)
    print("🏥 한국투자증권 자동매매 시스템 건강 검진")
    print("=" * 50)
    
    checks = [
        check_packages,
        check_environment, 
        check_network,
        check_api_status
    ]
    
    results = []
    for check in checks:
        result = check()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("📋 검진 결과")
    print("=" * 50)
    
    if all(results):
        print("✅ 모든 시스템이 정상입니다!")
        print("🚀 trading_ui.py를 실행할 준비가 되었습니다.")
    else:
        print("❌ 일부 시스템에 문제가 있습니다.")
        print("🔧 위의 오류를 해결한 후 다시 시도하세요.")
        
        print("\n💡 문제 해결 도움말:")
        print("1. 패키지 설치: pip install -r requirements.txt")
        print("2. 환경 설정: .env.example을 참고하여 .env 파일 생성")
        print("3. 네트워크: 방화벽 및 프록시 설정 확인")
        print("4. API 키: 한국투자증권에서 발급받은 키 정보 확인")

if __name__ == "__main__":
    main()