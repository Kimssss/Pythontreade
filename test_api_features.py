#!/usr/bin/env python3
"""
한국투자증권 API 모의투자 기능 점검
"""
import os
import sys
import json
import asyncio
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_trading_system.utils.kis_api import KisAPIEnhanced
from ai_trading_system.config.settings import KIS_CONFIG

def test_kis_api():
    """KIS API 기능 테스트"""
    print("=" * 60)
    print("🧪 한국투자증권 API 모의투자 기능 점검")
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 모의투자 계정으로 초기화
    demo_config = KIS_CONFIG['demo']
    api = KisAPIEnhanced(
        demo_config['appkey'],
        demo_config['appsecret'],
        demo_config['account'],
        is_real=False,
        min_request_interval=0.5
    )
    
    # 캐시된 토큰 강제 로드
    import pickle
    try:
        with open('cache/token_demo_PSpRavS44k.pkl', 'rb') as f:
            cached = pickle.load(f)
            api.access_token = cached['access_token']
            api.token_expire_time = cached['token_expire_time']
            print("✅ 캐시된 토큰 로드 성공")
    except:
        pass
    
    # 테스트 결과 저장
    results = {
        '토큰발급': False,
        '계좌잔고조회': False,
        '보유종목조회': False,
        '거래량순위조회': False,
        '현재가조회': False,
        '일봉데이터조회': False,
        '해외주식API초기화': False,
        '해외주식현재가': False,
        '해외주식잔고': False
    }
    
    try:
        # 1. 토큰 발급
        print("\n1️⃣ 토큰 발급 테스트")
        print("-" * 40)
        if api.access_token:
            print("✅ 캐시된 토큰 사용")
            results['토큰발급'] = True
        elif api.get_access_token():
            print("✅ 신규 토큰 발급 성공")
            results['토큰발급'] = True
        else:
            print("❌ 토큰 발급 실패")
        
        # 2. 계좌 잔고 조회
        print("\n2️⃣ 계좌 잔고 조회")
        print("-" * 40)
        cash = api.get_available_cash()
        print(f"가용 현금: {cash:,.0f}원")
        if cash >= 0:
            results['계좌잔고조회'] = True
            print("✅ 계좌 잔고 조회 성공")
        
        # 3. 보유 종목 조회
        print("\n3️⃣ 보유 종목 조회")
        print("-" * 40)
        holdings = api.get_holding_stocks()
        print(f"보유 종목 수: {len(holdings)}개")
        results['보유종목조회'] = True
        if holdings:
            for stock in holdings[:5]:  # 상위 5개만
                print(f"  - {stock['stock_name']}: {stock['quantity']}주")
        else:
            print("  보유 종목 없음")
        print("✅ 보유 종목 조회 성공")
        
        # 4. 거래량 순위 조회
        print("\n4️⃣ 거래량 순위 조회")
        print("-" * 40)
        volume_ranks = api.get_volume_rank()
        if volume_ranks:
            print(f"거래량 상위 종목 수: {len(volume_ranks)}개")
            results['거래량순위조회'] = True
            for i, stock in enumerate(volume_ranks[:5], 1):
                print(f"  {i}. {stock['name']} ({stock['code']}): {stock['volume']:,}주")
            print("✅ 거래량 순위 조회 성공")
        else:
            print("❌ 거래량 순위 조회 실패")
        
        # 5. 현재가 조회 (삼성전자)
        print("\n5️⃣ 현재가 조회 (삼성전자)")
        print("-" * 40)
        price_info = api.get_stock_price('005930')
        if price_info and price_info.get('rt_cd') == '0':
            output = price_info.get('output', {})
            print(f"종목명: 삼성전자")
            print(f"현재가: {output.get('stck_prpr', 'N/A'):,}원")
            print(f"전일대비: {output.get('prdy_vrss', 'N/A')}원")
            print(f"등락률: {output.get('prdy_ctrt', 'N/A')}%")
            results['현재가조회'] = True
            print("✅ 현재가 조회 성공")
        else:
            print("❌ 현재가 조회 실패")
        
        # 6. 일봉 데이터 조회
        print("\n6️⃣ 일봉 데이터 조회 (삼성전자)")
        print("-" * 40)
        daily_price = api.get_daily_price('005930', count=5)
        if daily_price and daily_price.get('rt_cd') == '0':
            output = daily_price.get('output', [])
            print(f"최근 {len(output)}일 데이터:")
            for day in output[:5]:
                print(f"  {day['stck_bsop_date']}: {int(day['stck_clpr']):,}원")
            results['일봉데이터조회'] = True
            print("✅ 일봉 데이터 조회 성공")
        else:
            print("❌ 일봉 데이터 조회 실패")
        
        # 7. 해외주식 API 초기화
        print("\n7️⃣ 해외주식 API 초기화")
        print("-" * 40)
        try:
            api.initialize_overseas_api()
            results['해외주식API초기화'] = True
            print("✅ 해외주식 API 초기화 성공")
        except Exception as e:
            print(f"❌ 해외주식 API 초기화 실패: {e}")
        
        # 8. 해외주식 현재가 (AAPL)
        if results['해외주식API초기화']:
            print("\n8️⃣ 해외주식 현재가 조회 (AAPL)")
            print("-" * 40)
            try:
                aapl_price = api.overseas.get_overseas_price('NASD', 'AAPL')
                if aapl_price:
                    print(f"종목: Apple Inc.")
                    print(f"현재가: ${aapl_price['current_price']}")
                    print(f"변동률: {aapl_price['change_rate']}%")
                    print(f"거래량: {aapl_price['volume']:,}")
                    results['해외주식현재가'] = True
                    print("✅ 해외주식 현재가 조회 성공")
                else:
                    print("❌ 해외주식 현재가 조회 실패")
            except Exception as e:
                print(f"❌ 해외주식 현재가 조회 오류: {e}")
        
        # 9. 해외주식 잔고
        if results['해외주식API초기화']:
            print("\n9️⃣ 해외주식 잔고 조회")
            print("-" * 40)
            try:
                overseas_balance = api.overseas.get_overseas_balance()
                if overseas_balance:
                    print(f"USD 잔고: ${overseas_balance.get('foreign_currency_amount', 0):,.2f}")
                    print(f"보유 종목: {len(overseas_balance.get('holdings', []))}개")
                    results['해외주식잔고'] = True
                    print("✅ 해외주식 잔고 조회 성공")
                else:
                    print("❌ 해외주식 잔고 조회 실패")
            except Exception as e:
                print(f"❌ 해외주식 잔고 조회 오류: {e}")
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 테스트 결과 요약")
        print("=" * 60)
        
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        for func, success in results.items():
            status = "✅" if success else "❌"
            print(f"{status} {func}")
        
        print(f"\n총 {total_count}개 중 {success_count}개 성공 ({success_count/total_count*100:.1f}%)")
        
        # 시장 상태 확인
        print("\n" + "=" * 60)
        print("🕐 현재 거래 가능 시장")
        print("=" * 60)
        
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        
        # 한국 시장
        if 9 <= hour < 15 or (hour == 15 and minute <= 30):
            print("🇰🇷 한국 시장: 거래 가능 ✅")
        else:
            print("🇰🇷 한국 시장: 마감 ❌")
        
        # 미국 시장
        if (hour >= 22 and minute >= 30) or hour >= 23 or hour < 6:
            print("🇺🇸 미국 시장: 거래 가능 ✅")
        else:
            print("🇺🇸 미국 시장: 마감 ❌")
        
        print("\n✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_kis_api()