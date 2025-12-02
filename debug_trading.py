#!/usr/bin/env python3
"""
Debug script to identify why no trades are executing
"""
import asyncio
import logging
from datetime import datetime
import os
import sys

# 프로젝트 루트 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_trading_system.main_trading_system import AITradingSystem
from ai_trading_system.config.settings import TRADING_CONFIG

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('debug_trading')

async def debug_trading_system():
    """트레이딩 시스템 디버깅"""
    
    # 시스템 초기화
    mode = os.environ.get('TRADING_MODE', 'demo')
    logger.info(f"Starting debug session in {mode} mode")
    
    system = AITradingSystem(mode=mode)
    
    try:
        # 1. 초기화 및 토큰 발급 테스트
        logger.info("\n=== TEST 1: System Initialization ===")
        await system.initialize()
        logger.info(f"Initial cash balance: {system.cash_balance}")
        logger.info(f"Total portfolio value: {system.total_value}")
        
        # 2. 시장 시간 체크
        logger.info("\n=== TEST 2: Market Hours Check ===")
        active_markets = system.get_active_markets()
        logger.info(f"Current time: {datetime.now()}")
        logger.info(f"Active markets: {active_markets}")
        
        # 3. 시장 상태 분석
        logger.info("\n=== TEST 3: Market Condition Analysis ===")
        market_condition = await system.analyze_market_condition()
        logger.info(f"Market condition: {market_condition}")
        
        # 4. 종목 스크리닝
        logger.info("\n=== TEST 4: Stock Screening ===")
        candidates = await system.screener.screen_stocks(market_condition)
        logger.info(f"Found {len(candidates)} candidates")
        if candidates:
            logger.info("Top 5 candidates:")
            for i, stock in enumerate(candidates[:5]):
                logger.info(f"  {i+1}. {stock['name']} ({stock['code']}) - Price: {stock['price']:,.0f}")
        
        # 5. 신호 생성 테스트 (상위 종목)
        if candidates:
            logger.info("\n=== TEST 5: Signal Generation ===")
            test_stock = candidates[0]
            logger.info(f"Testing signal for: {test_stock['name']} ({test_stock['code']})")
            
            signal = await system.analyze_stock_and_generate_signal(test_stock)
            if signal:
                logger.info(f"Signal generated:")
                logger.info(f"  Action: {signal['action_name']}")
                logger.info(f"  Confidence: {signal['confidence']:.2%}")
                logger.info(f"  Agent decisions:")
                for agent, decision in signal['agent_decisions'].items():
                    logger.info(f"    {agent}: Action={decision['action']}, Confidence={decision['confidence']:.2%}")
            else:
                logger.error("Failed to generate signal")
        
        # 6. 리스크 필터 테스트
        logger.info("\n=== TEST 6: Risk Filtering ===")
        logger.info(f"Min confidence threshold: {TRADING_CONFIG['min_confidence']}")
        logger.info(f"Max position size: {TRADING_CONFIG['max_position_size']}")
        logger.info(f"Stop loss rate: {TRADING_CONFIG['stop_loss_rate']}")
        
        # 7. 실제 트레이딩 사이클 1회 실행
        logger.info("\n=== TEST 7: Run One Trading Cycle ===")
        await system.run_trading_cycle()
        
        # 8. 거래 내역 확인
        logger.info("\n=== TEST 8: Trade History ===")
        logger.info(f"Total trades executed: {len(system.trade_history)}")
        if system.trade_history:
            logger.info("Recent trades:")
            for trade in system.trade_history[-5:]:
                logger.info(f"  {trade['timestamp']} - {trade['action']} {trade['stock_name']} x{trade['quantity']}")
        
    except Exception as e:
        logger.error(f"Debug error: {e}", exc_info=True)
    
    logger.info("\n=== DEBUG COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(debug_trading_system())