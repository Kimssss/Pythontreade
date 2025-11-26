#!/usr/bin/env python3
"""
간단한 API 연결 테스트
"""

from kis_api import KisAPI
from config import Config
import time

def simple_test():
    print("=== 간단한 API 연결 테스트 ===\n")
    
    try:
        # 모의투자 계좌 정보 로드
        demo_info = Config.get_account_info('demo')
        print(f"계좌번호: {demo_info['account']}")
        
        # API 인스턴스 생성
        api = KisAPI(
            demo_info['appkey'],
            demo_info['appsecret'],
            demo_info['account'],
            is_real=False
        )
        
        print("토큰 발급 테스트...")
        success = api.get_access_token()
        
        if success:
            print("✅ API 연결 성공!")
            
            # 간단한 기능 테스트
            print("\n계좌 잔고 조회 테스트...")
            balance = api.get_balance()
            if balance and balance.get('rt_cd') == '0':
                print("✅ 잔고 조회 성공!")
            else:
                print("❌ 잔고 조회 실패")
                
        else:
            print("❌ API 연결 실패")
            
    except Exception as e:
        print(f"테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_test()