#!/usr/bin/env python3
"""
KIS API 수정 및 검증 테스트
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리의 .env 파일 로드
project_root = Path(__file__).parent
load_dotenv(project_root / '.env')

# Python 경로에 추가
sys.path.insert(0, str(project_root / 'ai_trading_system'))

# 필요한 모듈만 import
from utils.kis_api import KisAPIEnhanced


def print_section(title):
    """섹션 구분 출력"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_api_methods():
    """KIS API 메소드 테스트 및 문제 해결"""
    
    print_section("KIS API 테스트 및 문제 해결")
    
    # 환경 변수 확인
    demo_appkey = os.getenv('DEMO_APPKEY')
    demo_appsecret = os.getenv('DEMO_APPSECRET')
    demo_account = os.getenv('DEMO_ACCOUNT_NO')
    
    if not all([demo_appkey, demo_appsecret, demo_account]):
        print("❌ 환경 변수가 설정되지 않았습니다.")
        return
    
    print(f"✅ 환경 변수 로드 성공")
    print(f"   - AppKey: {demo_appkey[:10]}...")
    print(f"   - Account: {demo_account}")
    
    # API 인스턴스 생성
    api = KisAPIEnhanced(
        demo_appkey,
        demo_appsecret,
        demo_account,
        is_real=False,
        min_request_interval=0.5
    )
    
    print("\n1. 토큰 발급")
    if not api.get_access_token():
        print("❌ 토큰 발급 실패")
        return
    print("✅ 토큰 발급 성공")
    
    print("\n2. 주요 API 메소드 테스트")
    
    # 테스트할 메소드 목록
    test_cases = [
        {
            'name': 'get_balance',
            'method': api.get_balance,
            'args': [],
            'description': '계좌 잔고 조회'
        },
        {
            'name': 'get_available_cash',
            'method': api.get_available_cash,
            'args': [],
            'description': '가용 현금 조회'
        },
        {
            'name': 'get_holding_stocks',
            'method': api.get_holding_stocks,
            'args': [],
            'description': '보유 종목 조회'
        },
        {
            'name': 'get_volume_rank',
            'method': api.get_volume_rank,
            'args': [],
            'description': '거래량 순위 조회'
        },
        {
            'name': 'get_top_volume_stocks',
            'method': api.get_top_volume_stocks,
            'args': [],
            'kwargs': {'count': 5},
            'description': '거래량 상위 종목 조회'
        },
        {
            'name': 'get_stock_price',
            'method': api.get_stock_price,
            'args': ['005930'],
            'description': '삼성전자 현재가 조회'
        },
        {
            'name': 'get_daily_price',
            'method': api.get_daily_price,
            'args': ['005930', 10],
            'description': '삼성전자 일봉 조회'
        }
    ]
    
    success_count = 0
    fail_count = 0
    
    for test in test_cases:
        print(f"\n[{test['name']}] {test['description']}")
        try:
            # 메소드 호출
            if 'kwargs' in test:
                result = test['method'](*test['args'], **test['kwargs'])
            else:
                result = test['method'](*test['args'])
            
            # 결과 검증
            if result is None:
                print(f"   ❌ None 반환")
                fail_count += 1
            elif isinstance(result, dict):
                rt_cd = result.get('rt_cd', 'N/A')
                msg = result.get('msg1', '')
                if rt_cd == '0':
                    print(f"   ✅ 성공 (rt_cd: {rt_cd})")
                    success_count += 1
                    
                    # 추가 정보 출력
                    if test['name'] == 'get_available_cash':
                        print(f"      가용 현금: {result:,.0f}원")
                    elif test['name'] == 'get_holding_stocks':
                        print(f"      보유 종목: {len(result)}개")
                    elif test['name'] in ['get_volume_rank', 'get_top_volume_stocks']:
                        stocks = result.get('output', [])
                        print(f"      조회된 종목: {len(stocks)}개")
                        if stocks:
                            top_stock = stocks[0]
                            print(f"      1위: {top_stock.get('hts_kor_isnm', '')} ({top_stock.get('mksc_shrn_iscd', '')})")
                else:
                    print(f"   ⚠️ 실패 (rt_cd: {rt_cd}, msg: {msg})")
                    fail_count += 1
            elif isinstance(result, (list, int, float)):
                print(f"   ✅ 성공 (type: {type(result).__name__})")
                success_count += 1
                if isinstance(result, (int, float)):
                    print(f"      값: {result:,.0f}")
                elif isinstance(result, list):
                    print(f"      개수: {len(result)}개")
            else:
                print(f"   ⚠️ 예상치 못한 타입: {type(result)}")
                fail_count += 1
                
        except Exception as e:
            print(f"   ❌ 오류 발생: {str(e)}")
            fail_count += 1
    
    # 최종 결과
    print_section("테스트 결과")
    print(f"총 테스트: {len(test_cases)}개")
    print(f"성공: {success_count}개")
    print(f"실패: {fail_count}개")
    print(f"성공률: {success_count/len(test_cases)*100:.1f}%")
    
    if fail_count == 0:
        print("\n✅ 모든 API 메소드가 정상적으로 작동합니다!")
    else:
        print("\n⚠️ 일부 API 메소드에 문제가 있습니다.")
    
    # API 메소드 목록 확인
    print_section("사용 가능한 API 메소드")
    methods = [method for method in dir(api) if not method.startswith('_') and callable(getattr(api, method))]
    for i, method in enumerate(methods[:20], 1):  # 상위 20개만
        print(f"{i:2d}. {method}")
    
    if len(methods) > 20:
        print(f"... 외 {len(methods)-20}개")


if __name__ == "__main__":
    test_api_methods()