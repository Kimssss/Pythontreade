#!/usr/bin/env python3
"""
글로벌 트레이딩 시스템 테스트
"""
import os
import sys
import asyncio
from datetime import datetime

# 프로젝트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 환경변수 설정
os.environ['TRADING_MODE'] = 'demo'
os.environ['GLOBAL_TRADING_MODE'] = 'both'  # 한국/미국 둘 다

async def test_trading_system():
    """트레이딩 시스템 테스트"""
    print("=" * 60)
    print("🌐 글로벌 트레이딩 시스템 테스트")
    print("=" * 60)
    
    try:
        from ai_trading_system.main_trading_system import AITradingSystem
        
        # 시스템 초기화
        print("\n1️⃣ 시스템 초기화 중...")
        system = AITradingSystem(mode='demo')
        
        # 초기화
        print("\n2️⃣ API 연결 및 토큰 발급...")
        await system.initialize()
        
        # 현재 활성 시장 확인
        print("\n3️⃣ 현재 활성 시장 확인...")
        active_markets = system.get_active_markets()
        print(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"활성 시장: {active_markets}")
        
        # 한국 시장 활성 여부
        if active_markets['korean']:
            print("✅ 한국 시장 거래 가능 (09:00-15:30)")
        else:
            print("❌ 한국 시장 마감")
            
        # 미국 시장 활성 여부
        if active_markets['us']:
            print("✅ 미국 시장 거래 가능 (22:30-05:00 또는 23:30-06:00)")
        else:
            print("❌ 미국 시장 마감")
        
        # 활성 시장이 있으면 거래 사이클 실행
        if any(active_markets.values()):
            print("\n4️⃣ 트레이딩 사이클 실행...")
            await system.run_trading_cycle()
            print("✅ 트레이딩 사이클 완료")
        else:
            print("\n⚠️ 현재 거래 가능한 시장이 없습니다")
            
            # 해외주식 API 테스트
            print("\n5️⃣ 미국 주식 API 테스트 (시장 마감 중이어도 테스트)")
            if hasattr(system.kis_api, 'overseas') and system.kis_api.overseas:
                # AAPL 현재가 조회
                print("\n📊 AAPL 현재가 조회...")
                price_info = system.kis_api.overseas.get_overseas_price('NASD', 'AAPL')
                if price_info:
                    print(f"AAPL 현재가: ${price_info['current_price']}")
                    print(f"변동률: {price_info['change_rate']}%")
                else:
                    print("❌ AAPL 현재가 조회 실패")
                    
                # 해외주식 잔고 조회
                print("\n💰 해외주식 잔고 조회...")
                balance = system.kis_api.overseas.get_overseas_balance()
                if balance:
                    print(f"USD 잔고: ${balance.get('foreign_currency_amount', 0):,.2f}")
                    print(f"보유 종목 수: {len(balance.get('holdings', []))}")
                else:
                    print("❌ 해외주식 잔고 조회 실패")
            else:
                print("❌ 해외주식 API가 초기화되지 않았습니다")
        
        print("\n✅ 테스트 완료!")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_trading_system())