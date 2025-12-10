#!/usr/bin/env python3
"""
AI 트레이딩 시스템 30분 실제 모니터링 스크립트
"""
import os
import sys
import time
import asyncio
from datetime import datetime, timedelta

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.abspath('.'))

def main():
    """30분 모니터링 실행"""
    print("🚀 AI 트레이딩 시스템 30분 실제 모니터링 시작")
    print("=" * 60)
    
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=30)
    
    print(f"⏰ 시작 시간: {start_time.strftime('%H:%M:%S')}")
    print(f"⏰ 종료 예정: {end_time.strftime('%H:%M:%S')}")
    print("=" * 60)
    
    # 환경변수 설정
    os.environ['KIS_DEMO_APPKEY'] = 'PSTP8BTWgg4loa76mISQPzb2tHvjxtrBUDID'
    os.environ['KIS_DEMO_APPSECRET'] = 'rc+xPU2Ya43Z7MgdiLNknR3QWQMc9yBHj9j4WuK63/XiBvusTUcRVhi3vl8tQdup5yUbRBJJ5+AHv1o3dUgdMdX3Xw5AN09go98Z2+BMeBfF/kaDCw9jHDH1RWhjBi5grVjfBkFArbt3lrP+pFkSdeiJxEPUgx+4nZ9gog744kyo5LEq3hI='
    os.environ['KIS_DEMO_ACCOUNT'] = '50157423-01'
    
    try:
        from ai_trading_system.utils.kis_api import KisAPIEnhanced
        from ai_trading_system.models.ensemble_system import MultiAgentEnsemble
        from ai_trading_system.strategies.stock_screener import StockScreener
        from ai_trading_system.config.settings import KIS_CONFIG, TRADING_CONFIG
        
        print("✅ 모듈 import 성공")
        
        # 기본 컴포넌트 초기화
        kis_api = KisAPIEnhanced(
            appkey=os.environ['KIS_DEMO_APPKEY'],
            appsecret=os.environ['KIS_DEMO_APPSECRET'],
            account_no=os.environ['KIS_DEMO_ACCOUNT']
        )
        ensemble = MultiAgentEnsemble(kis_api)
        screener = StockScreener(kis_api)
        
        print("✅ 시스템 초기화 성공")
        print("\n📊 실시간 모니터링 중...")
        
        cycle = 0
        while datetime.now() < end_time:
            cycle += 1
            current_time = datetime.now()
            remaining = end_time - current_time
            
            print(f"\n[Cycle {cycle}] {current_time.strftime('%H:%M:%S')} - 남은시간: {remaining}")
            
            try:
                # 1. 시장 상태 체크
                print("📊 시장 상태 확인 중...")
                is_market_open = current_time.hour >= 9 and current_time.hour < 16
                print(f"   시장 상태: {'📈 개장 중' if is_market_open else '🌙 장외시간'}")
                
                # 2. 포트폴리오 상태 확인
                print("💼 포트폴리오 잔고 조회 중...")
                balance_info = kis_api.get_balance()
                if balance_info and balance_info.get('rt_cd') == '0':
                    total_balance = balance_info.get('ctx_area_fk100', {}).get('dnca_tot_amt', '0')
                    print(f"   💰 총 잔고: {total_balance:,}원")
                else:
                    print("   ⚠️ 잔고 조회 실패")
                
                # 3. 해외주식 잔고 확인
                try:
                    print("🌍 해외주식 잔고 조회 중...")
                    overseas_balance = kis_api.overseas.get_overseas_balance()
                    if overseas_balance:
                        print(f"   💵 해외주식 잔고: {overseas_balance.get('total_balance', 'N/A')}")
                    else:
                        print("   ⚠️ 해외주식 잔고 조회 실패")
                except Exception as e:
                    print(f"   ❌ 해외주식 잔고 오류: {e}")
                
                # 4. 거래량 상위 종목 확인
                print("📈 거래량 상위 종목 확인 중...")
                volume_stocks = kis_api.get_top_volume_stocks(count=5)
                if volume_stocks and volume_stocks.get('rt_cd') == '0':
                    stocks = volume_stocks.get('output', [])[:3]
                    print("   📊 상위 3종목:")
                    for i, stock in enumerate(stocks, 1):
                        name = stock.get('hts_kor_isnm', '')
                        code = stock.get('mksc_shrn_iscd', '')
                        print(f"      {i}. {name} ({code})")
                else:
                    print("   ⚠️ 거래량 상위 종목 조회 실패")
                
                # 5. DQN 에이전트 상태 확인
                print("🧠 DQN 에이전트 상태 확인 중...")
                dqn_agent = ensemble.dqn_agent
                print(f"   🎯 Epsilon: {dqn_agent.epsilon:.4f}")
                print(f"   💾 메모리 크기: {len(dqn_agent.memory)}")
                print(f"   📊 업데이트 카운트: {dqn_agent.update_count}")
                
                # 6. 간단한 가상 트레이딩 신호 생성 테스트
                if is_market_open and len(stocks) > 0:
                    test_stock = stocks[0]
                    stock_code = test_stock.get('mksc_shrn_iscd', '')
                    stock_name = test_stock.get('hts_kor_isnm', '')
                    
                    print(f"🎯 AI 신호 생성 테스트: {stock_name}")
                    
                    # 현재가 조회
                    price_info = kis_api.get_stock_price(stock_code)
                    if price_info and price_info.get('rt_cd') == '0':
                        current_price = float(price_info.get('output', {}).get('stck_prpr', 0))
                        print(f"   💰 현재가: {current_price:,}원")
                        
                        # AI 신호 생성 시뮬레이션
                        import numpy as np
                        dummy_state = np.random.random(31)  # 31차원 상태 벡터
                        action = dqn_agent.act(dummy_state, training=False)
                        
                        action_names = ['매수', '매도', '보유']
                        print(f"   🤖 AI 신호: {action_names[action]}")
                    else:
                        print(f"   ⚠️ {stock_name} 가격 조회 실패")
                
                print("✅ 모니터링 사이클 완료")
                
            except Exception as e:
                print(f"❌ 모니터링 중 오류 발생: {e}")
                print(f"   오류 타입: {type(e).__name__}")
                import traceback
                print(f"   상세 오류: {traceback.format_exc()}")
            
            # 다음 사이클까지 대기 (3분)
            if datetime.now() < end_time:
                print("⏱️ 다음 사이클까지 3분 대기...")
                time.sleep(180)  # 3분 대기
        
        print("\n" + "=" * 60)
        print("🎯 30분 모니터링 완료!")
        actual_duration = datetime.now() - start_time
        print(f"⏰ 실제 소요 시간: {actual_duration}")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 심각한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)