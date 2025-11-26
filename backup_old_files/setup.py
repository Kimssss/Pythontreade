#!/usr/bin/env python3
"""
한국투자증권 자동매매 시스템 설치 스크립트
"""

import subprocess
import sys
import os

def install_requirements():
    """필요한 패키지 설치"""
    print("📦 필요한 패키지를 설치합니다...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 패키지 설치 완료!")
    except subprocess.CalledProcessError:
        print("❌ 패키지 설치 실패!")
        return False
    return True

def setup_env_file():
    """환경 설정 파일 생성"""
    if os.path.exists('.env'):
        print("⚠️  .env 파일이 이미 존재합니다.")
        return True
    
    print("📝 환경 설정 파일(.env)을 생성합니다...")
    print("API 키 정보를 입력해주세요:")
    
    # 실전투자 계좌
    print("\n🔴 실전투자 계좌 정보:")
    real_appkey = input("App Key: ").strip()
    real_appsecret = input("App Secret: ").strip()
    real_account = input("계좌번호 (예: 12345678-01): ").strip()
    
    # 모의투자 계좌
    print("\n🟡 모의투자 계좌 정보:")
    demo_appkey = input("App Key: ").strip()
    demo_appsecret = input("App Secret: ").strip()
    demo_account = input("계좌번호 (예: 12345678-01): ").strip()
    
    # .env 파일 생성
    env_content = f"""# 한국투자증권 API 설정
# 실전투자 계좌
REAL_APPKEY={real_appkey}
REAL_APPSECRET={real_appsecret}
REAL_ACCOUNT_NO={real_account}

# 모의투자 계좌
DEMO_APPKEY={demo_appkey}
DEMO_APPSECRET={demo_appsecret}
DEMO_ACCOUNT_NO={demo_account}"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ .env 파일이 생성되었습니다!")
    return True

def main():
    """메인 설치 함수"""
    print("=" * 60)
    print("🏦 한국투자증권 자동매매 시스템 설치")
    print("=" * 60)
    
    # 1. 패키지 설치
    if not install_requirements():
        print("❌ 설치 실패!")
        return
    
    # 2. 환경 설정
    if not setup_env_file():
        print("❌ 환경 설정 실패!")
        return
    
    print("\n" + "=" * 60)
    print("✅ 설치 완료!")
    print("🚀 다음 명령어로 프로그램을 실행하세요:")
    print("   python3 trading_ui.py")
    print("=" * 60)

if __name__ == "__main__":
    main()