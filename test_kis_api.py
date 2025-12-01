#!/usr/bin/env python3
"""
한국투자증권 API 테스트 파일
- 주요 기능들을 직접 호출하여 문제점 파악
- 각 API 응답을 자세히 분석
"""

import json
import sys
import os
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리의 .env 파일 로드
project_root = Path(__file__).parent
load_dotenv(project_root / '.env')

# ai_trading_system 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(project_root / 'ai_trading_system'))

from utils.kis_api import KisAPIEnhanced


def print_section(title):
    """섹션 구분 출력"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def print_json(data, indent=2):
    """JSON 데이터를 보기 좋게 출력"""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def test_kis_api():
    """KIS API 주요 기능 테스트"""
    
    # 환경 변수에서 직접 가져오기
    try:
        demo_appkey = os.getenv('DEMO_APPKEY')
        demo_appsecret = os.getenv('DEMO_APPSECRET')
        demo_account = os.getenv('DEMO_ACCOUNT_NO')
        
        if not all([demo_appkey, demo_appsecret, demo_account]):
            print("❌ 환경 변수가 설정되지 않았습니다.")
            print("   필요한 환경 변수:")
            print("   - DEMO_APPKEY")
            print("   - DEMO_APPSECRET")
            print("   - DEMO_ACCOUNT_NO")
            return
            
        print("✅ 환경 변수 로드 성공")
        print(f"   - AppKey: {demo_appkey[:10]}...")
        print(f"   - Account: {demo_account}")
    except Exception as e:
        print(f"❌ 환경 변수 로드 실패: {e}")
        return
    
    # API 인스턴스 생성
    api = KisAPIEnhanced(
        demo_appkey,
        demo_appsecret,
        demo_account,
        is_real=False,
        min_request_interval=0.3  # 300ms 간격
    )
    
    print_section("1. 토큰 발급 테스트")
    
    # 토큰 발급
    try:
        success = api.get_access_token()
        if success:
            print("✅ 토큰 발급 성공")
            print(f"   - 토큰: {api.access_token[:20]}...")
            print(f"   - 만료시간: {api.token_expire_time}")
        else:
            print("❌ 토큰 발급 실패")
            return
    except Exception as e:
        print(f"❌ 토큰 발급 중 오류: {e}")
        return
    
    print_section("2. 잔고 조회 테스트")
    
    try:
        balance = api.get_balance()
        if balance:
            print(f"✅ 잔고 조회 성공 (rt_cd: {balance.get('rt_cd')})")
            print(f"   - 메시지: {balance.get('msg1', '')}")
            
            if balance.get('rt_cd') == '0':
                # output1: 보유종목 정보
                output1 = balance.get('output1', [])
                print(f"   - 보유종목 수: {len(output1)}개")
                
                # output2: 계좌 잔고 정보
                output2 = balance.get('output2', [])
                print(f"   - output2 데이터 개수: {len(output2)}개")
                
                if output2:
                    print("\n   [계좌 잔고 정보 - output2[0]]")
                    for key, value in output2[0].items():
                        if any(keyword in key for keyword in ['cash', 'amt', 'excc']):
                            print(f"     - {key}: {value}")
            else:
                print(f"⚠️ 잔고 조회 실패 응답")
                print_json(balance)
        else:
            print("❌ 잔고 조회 실패 - None 반환")
    except Exception as e:
        print(f"❌ 잔고 조회 중 오류: {e}")
    
    print_section("3. 가용 현금 조회 테스트")
    
    try:
        cash = api.get_available_cash()
        print(f"✅ 가용 현금: {cash:,.0f}원")
    except Exception as e:
        print(f"❌ 가용 현금 조회 중 오류: {e}")
    
    print_section("4. 보유 종목 조회 테스트")
    
    try:
        holdings = api.get_holding_stocks()
        print(f"✅ 보유 종목 수: {len(holdings)}개")
        
        for holding in holdings[:3]:  # 최대 3개만 출력
            print(f"\n   [{holding['stock_name']} ({holding['stock_code']})]")
            print(f"     - 보유수량: {holding['quantity']:,}주")
            print(f"     - 평균단가: {holding['avg_price']:,.0f}원")
            print(f"     - 현재가: {holding['current_price']:,.0f}원")
            print(f"     - 평가금액: {holding['eval_amt']:,.0f}원")
            print(f"     - 손익: {holding['profit_loss']:+,.0f}원 ({holding['profit_rate']:+.2f}%)")
    except Exception as e:
        print(f"❌ 보유 종목 조회 중 오류: {e}")
    
    print_section("5-1. 거래량 순위 조회 테스트 (get_top_volume_stocks)")
    
    try:
        volume_data = api.get_top_volume_stocks(count=10)
        if volume_data:
            print(f"✅ 거래량 순위 조회 성공 (rt_cd: {volume_data.get('rt_cd')})")
            print(f"   - 메시지: {volume_data.get('msg1', '')}")
            
            if volume_data.get('rt_cd') == '0':
                stocks = volume_data.get('output', [])
                print(f"   - 조회된 종목 수: {len(stocks)}개")
                
                # 상위 5개 종목 출력
                for idx, stock in enumerate(stocks[:5], 1):
                    print(f"\n   {idx}. {stock.get('hts_kor_isnm', '')} ({stock.get('mksc_shrn_iscd', '')})")
                    print(f"      - 현재가: {stock.get('stck_prpr', '0'):>10}원")
                    print(f"      - 등락률: {stock.get('prdy_ctrt', '0'):>10}%")
                    print(f"      - 거래량: {stock.get('acml_vol', '0'):>10}주")
                    print(f"      - 거래대금: {stock.get('acml_tr_pbmn', '0'):>10}원")
            else:
                print(f"⚠️ 거래량 순위 조회 실패 응답")
                print_json(volume_data)
        else:
            print("❌ 거래량 순위 조회 실패 - None 반환")
    except Exception as e:
        print(f"❌ 거래량 순위 조회 중 오류: {e}")
    
    print_section("5-2. 거래량 순위 조회 테스트 (get_volume_rank)")
    
    try:
        volume_data = api.get_volume_rank()
        if volume_data:
            print(f"✅ 거래량 순위 조회 성공 (rt_cd: {volume_data.get('rt_cd')})")
            print(f"   - 메시지: {volume_data.get('msg1', '')}")
            
            if volume_data.get('rt_cd') == '0':
                stocks = volume_data.get('output', [])
                print(f"   - 조회된 종목 수: {len(stocks)}개")
                
                # 상위 3개 종목만 간단히 출력
                for idx, stock in enumerate(stocks[:3], 1):
                    print(f"   {idx}. {stock.get('hts_kor_isnm', '')} ({stock.get('mksc_shrn_iscd', '')})")
            else:
                print(f"⚠️ 거래량 순위 조회 실패 응답")
        else:
            print("❌ 거래량 순위 조회 실패 - None 반환")
    except Exception as e:
        print(f"❌ 거래량 순위 조회 중 오류: {e}")
    
    print_section("6. 주식 현재가 조회 테스트 (삼성전자)")
    
    try:
        price_data = api.get_stock_price("005930")
        if price_data:
            print(f"✅ 현재가 조회 성공 (rt_cd: {price_data.get('rt_cd')})")
            
            if price_data.get('rt_cd') == '0':
                output = price_data.get('output', {})
                print(f"\n   [삼성전자 (005930)]")
                print(f"     - 현재가: {output.get('stck_prpr', '0'):>10}원")
                print(f"     - 전일대비: {output.get('prdy_vrss', '0'):>10}원")
                print(f"     - 등락률: {output.get('prdy_ctrt', '0'):>10}%")
                print(f"     - 거래량: {output.get('acml_vol', '0'):>10}주")
        else:
            print("❌ 현재가 조회 실패 - None 반환")
    except Exception as e:
        print(f"❌ 현재가 조회 중 오류: {e}")
    
    print_section("7. 일봉 데이터 조회 테스트 (삼성전자)")
    
    try:
        daily_data = api.get_daily_price("005930", count=5)
        if daily_data:
            print(f"✅ 일봉 데이터 조회 성공 (rt_cd: {daily_data.get('rt_cd')})")
            
            if daily_data.get('rt_cd') == '0':
                candles = daily_data.get('output', [])
                print(f"   - 조회된 일봉 수: {len(candles)}개")
                
                for candle in candles[:3]:
                    date = candle.get('stck_bsop_date', '')
                    print(f"\n   [{date}]")
                    print(f"     - 시가: {candle.get('stck_oprc', '0'):>10}원")
                    print(f"     - 고가: {candle.get('stck_hgpr', '0'):>10}원")
                    print(f"     - 저가: {candle.get('stck_lwpr', '0'):>10}원")
                    print(f"     - 종가: {candle.get('stck_clpr', '0'):>10}원")
                    print(f"     - 거래량: {candle.get('acml_vol', '0'):>10}주")
        else:
            print("❌ 일봉 데이터 조회 실패 - None 반환")
    except Exception as e:
        print(f"❌ 일봉 데이터 조회 중 오류: {e}")
    
    print_section("8. API 로그 파일 확인")
    
    try:
        log_file = Path('logs') / f'api_failures_{datetime.now().strftime("%Y%m%d")}.log'
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"✅ 로그 파일 확인: {len(lines)}개 항목")
                if lines:
                    print("\n   [최근 로그 5개]")
                    for line in lines[-5:]:
                        print(f"     {line.strip()}")
        else:
            print("ℹ️ 오늘 날짜의 로그 파일이 없습니다.")
    except Exception as e:
        print(f"❌ 로그 파일 확인 중 오류: {e}")
    
    print_section("테스트 완료")
    print(f"\n테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    test_kis_api()