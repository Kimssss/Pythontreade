#!/usr/bin/env python3
"""
KIS API 간단한 기능 테스트
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리의 .env 파일 로드
project_root = Path(__file__).parent
load_dotenv(project_root / '.env')

# ai_trading_system 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(project_root / 'ai_trading_system'))

from utils.kis_api import KisAPIEnhanced

def test_simple():
    """간단한 API 테스트"""
    print("KIS API Simple Test")
    print("=" * 50)
    
    # 환경 변수 확인
    demo_appkey = os.getenv('DEMO_APPKEY')
    demo_appsecret = os.getenv('DEMO_APPSECRET')
    demo_account = os.getenv('DEMO_ACCOUNT_NO')
    
    if not all([demo_appkey, demo_appsecret, demo_account]):
        print("❌ 환경 변수가 설정되지 않았습니다.")
        return
    
    print(f"✅ 환경 변수 로드 완료")
    print(f"   AppKey: {demo_appkey[:10]}...")
    print(f"   Account: {demo_account}")
    
    # API 인스턴스 생성
    api = KisAPIEnhanced(
        demo_appkey,
        demo_appsecret,
        demo_account,
        is_real=False,
        min_request_interval=0.5
    )
    
    print("\n1. 토큰 발급 테스트")
    if api.get_access_token():
        print("✅ 토큰 발급 성공")
    else:
        print("❌ 토큰 발급 실패")
        return
    
    print("\n2. get_volume_rank 메소드 테스트")
    try:
        # get_volume_rank 메소드 존재 확인
        if hasattr(api, 'get_volume_rank'):
            print("✅ get_volume_rank 메소드가 존재합니다.")
            
            # 메소드 호출
            result = api.get_volume_rank()
            if result and result.get('rt_cd') == '0':
                stocks = result.get('output', [])
                print(f"✅ 거래량 순위 조회 성공: {len(stocks)}개 종목")
                
                # 상위 3개 종목 출력
                for i, stock in enumerate(stocks[:3], 1):
                    print(f"   {i}. {stock.get('hts_kor_isnm', '')} ({stock.get('mksc_shrn_iscd', '')})")
            else:
                print(f"❌ 거래량 순위 조회 실패: {result.get('msg1', '') if result else 'No response'}")
        else:
            print("❌ get_volume_rank 메소드가 존재하지 않습니다.")
            print("   사용 가능한 메소드:")
            for method in dir(api):
                if not method.startswith('_') and callable(getattr(api, method)):
                    print(f"     - {method}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    print("\n3. get_top_volume_stocks 메소드 테스트")
    try:
        if hasattr(api, 'get_top_volume_stocks'):
            print("✅ get_top_volume_stocks 메소드가 존재합니다.")
            
            # 메소드 호출
            result = api.get_top_volume_stocks(count=5)
            if result and result.get('rt_cd') == '0':
                stocks = result.get('output', [])
                print(f"✅ 거래량 순위 조회 성공: {len(stocks)}개 종목")
            else:
                print(f"❌ 거래량 순위 조회 실패: {result.get('msg1', '') if result else 'No response'}")
        else:
            print("❌ get_top_volume_stocks 메소드가 존재하지 않습니다.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    test_simple()