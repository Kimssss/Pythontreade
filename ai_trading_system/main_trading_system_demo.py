"""
AI 자동매매 시스템 - 데모 테스트 버전
API 없이 시뮬레이션으로 작동
"""
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional
import json
import os
import random

# 시스템 모듈
try:
    from .models.ensemble_system import MultiAgentEnsemble
    from .strategies.stock_screener import StockScreener
    from .utils.risk_manager import RiskManager
    from .utils.technical_indicators import TechnicalIndicators
    from .config.settings import (
        TRADING_CONFIG, DATA_CONFIG, 
        LOGGING_CONFIG, SCREENING_CONFIG
    )
except ImportError:
    from models.ensemble_system import MultiAgentEnsemble
    from strategies.stock_screener import StockScreener
    from utils.risk_manager import RiskManager
    from utils.technical_indicators import TechnicalIndicators
    from config.settings import (
        TRADING_CONFIG, DATA_CONFIG, 
        LOGGING_CONFIG, SCREENING_CONFIG
    )

# 로깅 설정
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('ai_trading')


class MockKisAPI:
    """모의 KIS API"""
    def __init__(self):
        self.token = "DEMO_TOKEN_123"
        self.holdings = {}
        self.cash_balance = 10000000  # 천만원 시작
        logger.info("Mock KIS API initialized for demo mode")
    
    def get_access_token(self):
        return True
    
    def get_available_cash(self):
        return self.cash_balance
    
    def get_holding_stocks(self):
        holdings = []
        for code, data in self.holdings.items():
            holdings.append({
                'stock_code': code,
                'stock_name': data['name'],
                'quantity': data['quantity'],
                'avg_price': data['avg_price'],
                'current_price': data['current_price'],
                'eval_amt': data['quantity'] * data['current_price'],
                'profit_loss': (data['current_price'] - data['avg_price']) * data['quantity'],
                'profit_rate': ((data['current_price'] / data['avg_price']) - 1) * 100
            })
        return holdings
    
    def get_daily_price(self, stock_code, count=60):
        # 모의 일봉 데이터 생성
        base_price = 50000 + random.randint(-20000, 20000)
        dates = pd.date_range(end=datetime.now(), periods=count).strftime('%Y%m%d').tolist()
        
        output = []
        for i, date in enumerate(dates):
            price = base_price + random.randint(-2000, 2000)
            output.append({
                'stck_bsop_date': date,
                'stck_oprc': str(price),
                'stck_hgpr': str(price + random.randint(0, 1000)),
                'stck_lwpr': str(price - random.randint(0, 1000)),
                'stck_clpr': str(price + random.randint(-500, 500)),
                'acml_vol': str(random.randint(100000, 1000000))
            })
        
        return {'rt_cd': '0', 'output': output}
    
    def buy_stock(self, stock_code, quantity, order_type="03"):
        """매수 주문"""
        price = 50000 + random.randint(-20000, 20000)
        total_cost = price * quantity
        
        if self.cash_balance >= total_cost:
            self.cash_balance -= total_cost
            
            if stock_code not in self.holdings:
                self.holdings[stock_code] = {
                    'name': f'종목{stock_code[-3:]}',
                    'quantity': 0,
                    'avg_price': 0,
                    'current_price': price
                }
            
            # 평균단가 계산
            holding = self.holdings[stock_code]
            total_qty = holding['quantity'] + quantity
            total_value = (holding['quantity'] * holding['avg_price']) + total_cost
            holding['avg_price'] = total_value / total_qty if total_qty > 0 else price
            holding['quantity'] = total_qty
            
            logger.info(f"✅ DEMO BUY: {stock_code} x{quantity} @ {price:,.0f} KRW")
            return {'rt_cd': '0', 'output': {'odno': f'DEMO{random.randint(1000, 9999)}'}}
        else:
            logger.error(f"Insufficient cash: Need {total_cost:,.0f}, Have {self.cash_balance:,.0f}")
            return {'rt_cd': '1', 'msg': 'Insufficient cash'}
    
    def sell_stock(self, stock_code, quantity, order_type="03"):
        """매도 주문"""
        if stock_code in self.holdings:
            holding = self.holdings[stock_code]
            if holding['quantity'] >= quantity:
                price = holding['current_price']
                total_value = price * quantity
                
                self.cash_balance += total_value
                holding['quantity'] -= quantity
                
                if holding['quantity'] == 0:
                    del self.holdings[stock_code]
                
                logger.info(f"✅ DEMO SELL: {stock_code} x{quantity} @ {price:,.0f} KRW")
                return {'rt_cd': '0', 'output': {'odno': f'DEMO{random.randint(1000, 9999)}'}}
        
        return {'rt_cd': '1', 'msg': 'No holdings'}


class AITradingSystemDemo:
    """AI 자동매매 데모 시스템"""
    
    def __init__(self):
        """데모 모드 초기화"""
        self.mode = 'demo'
        logger.info("Initializing AI Trading System DEMO")
        
        # Mock API 사용
        self.kis_api = MockKisAPI()
        
        # 컴포넌트 초기화
        self.ensemble = MultiAgentEnsemble(self.kis_api)
        self.screener = StockScreener(self.kis_api)
        self.risk_manager = RiskManager()
        self.indicators = TechnicalIndicators()
        
        # 포트폴리오 상태
        self.portfolio = {}
        self.cash_balance = self.kis_api.cash_balance
        self.total_value = self.cash_balance
        
        # 거래 히스토리
        self.trade_history = []
        self.performance_history = []
        
        # 실행 상태
        self.is_running = False
        
        logger.info("AI Trading System DEMO initialized successfully")
    
    async def initialize(self):
        """시스템 초기화"""
        logger.info("=== DEMO System Initialization ===")
        logger.info("Demo mode - Using simulated data")
        await self.update_portfolio_status()
        logger.info(f"Initial portfolio value: {self.total_value:,.0f} KRW")
    
    async def update_portfolio_status(self):
        """포트폴리오 상태 업데이트"""
        logger.info("=== Updating Portfolio Status ===")
        self.cash_balance = self.kis_api.get_available_cash()
        logger.info(f"Cash balance: {self.cash_balance:,.0f} KRW")
        
        holdings = self.kis_api.get_holding_stocks()
        logger.info(f"Found {len(holdings)} holdings")
        
        self.portfolio = {}
        portfolio_value = self.cash_balance
        
        for holding in holdings:
            self.portfolio[holding['stock_code']] = holding
            portfolio_value += holding['eval_amt']
            logger.info(f"  - {holding['stock_name']}: {holding['quantity']}주, "
                      f"평가금액: {holding['eval_amt']:,.0f}원")
        
        self.total_value = portfolio_value
        logger.info(f"Total portfolio value: {self.total_value:,.0f} KRW")
    
    def get_demo_candidates(self) -> List[Dict]:
        """데모용 종목 생성"""
        candidates = []
        for i in range(20):
            candidates.append({
                'code': f'A00{1000+i}',
                'name': f'테스트종목{i+1}',
                'price': 50000 + random.randint(-20000, 20000),
                'change_rate': random.uniform(-5, 5),
                'volume': random.randint(100000, 1000000),
                'market_cap': random.randint(1000, 10000) * 100000000
            })
        return sorted(candidates, key=lambda x: x['volume'], reverse=True)
    
    async def run_trading_cycle(self):
        """메인 트레이딩 사이클"""
        logger.info("\n" + "="*60)
        logger.info("=== Starting DEMO Trading Cycle ===")
        logger.info(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. 데모 종목 가져오기
            candidates = self.get_demo_candidates()
            logger.info(f"Got {len(candidates)} demo stocks")
            
            # 2. 포트폴리오 업데이트
            await self.update_portfolio_status()
            
            # 3. 상위 종목 분석
            signals = []
            for stock in candidates[:5]:  # 상위 5개만
                logger.info(f"\nAnalyzing {stock['name']} ({stock['code']})")
                
                # 간단한 신호 생성 (랜덤)
                if random.random() > 0.3:  # 70% 확률로 신호 생성
                    action = 0 if random.random() > 0.5 else 2  # 매수 또는 관망
                    confidence = random.uniform(0.5, 0.9)
                    
                    signal = {
                        'stock_code': stock['code'],
                        'stock_name': stock['name'],
                        'action': action,
                        'action_name': ['BUY', 'SELL', 'HOLD'][action],
                        'confidence': confidence,
                        'current_price': stock['price']
                    }
                    
                    if action == 0:  # 매수 신호만
                        signals.append(signal)
                        logger.info(f"  → Signal: {signal['action_name']} (confidence: {confidence:.2%})")
            
            logger.info(f"\nGenerated {len(signals)} buy signals")
            
            # 4. 신호 실행
            if signals:
                # 가장 높은 신뢰도 신호 선택
                best_signal = max(signals, key=lambda x: x['confidence'])
                logger.info(f"\nExecuting best signal: {best_signal['stock_name']}")
                
                # 매수 수량 계산 (자산의 10%)
                position_value = self.total_value * 0.1
                quantity = max(1, int(position_value / best_signal['current_price']))
                
                # 매수 실행
                result = self.kis_api.buy_stock(
                    best_signal['stock_code'],
                    quantity,
                    order_type="03"
                )
                
                if result.get('rt_cd') == '0':
                    trade = {
                        'timestamp': datetime.now(),
                        'stock_code': best_signal['stock_code'],
                        'stock_name': best_signal['stock_name'],
                        'action': 'BUY',
                        'quantity': quantity,
                        'price': best_signal['current_price'],
                        'order_no': result.get('output', {}).get('odno')
                    }
                    self.trade_history.append(trade)
                    logger.info(f"✅ Trade executed successfully!")
            else:
                logger.info("No buy signals generated this cycle")
            
            # 5. 매도 체크 (보유 종목)
            if self.portfolio:
                for code, holding in list(self.portfolio.items()):
                    # 랜덤하게 10% 확률로 매도
                    if random.random() > 0.9:
                        logger.info(f"\nSelling {holding['stock_name']}")
                        result = self.kis_api.sell_stock(code, holding['quantity'])
                        
                        if result.get('rt_cd') == '0':
                            trade = {
                                'timestamp': datetime.now(),
                                'stock_code': code,
                                'stock_name': holding['stock_name'],
                                'action': 'SELL',
                                'quantity': holding['quantity'],
                                'price': holding['current_price'],
                                'profit': holding['profit_loss'],
                                'order_no': result.get('output', {}).get('odno')
                            }
                            self.trade_history.append(trade)
            
            # 6. 성과 기록
            self.record_performance()
            
        except Exception as e:
            logger.error(f"Error in demo trading cycle: {e}", exc_info=True)
    
    def record_performance(self):
        """성과 기록"""
        performance = {
            'timestamp': datetime.now(),
            'total_value': self.total_value,
            'cash_balance': self.cash_balance,
            'positions': len(self.portfolio),
            'daily_trades': len([t for t in self.trade_history 
                               if t['timestamp'].date() == datetime.now().date()])
        }
        
        # 수익률 계산
        if len(self.performance_history) > 0:
            prev_value = self.performance_history[-1]['total_value']
            performance['daily_return'] = (self.total_value - prev_value) / prev_value
        else:
            performance['daily_return'] = 0
        
        self.performance_history.append(performance)
        
        logger.info(f"\n📊 Performance Update:")
        logger.info(f"  Total Value: {performance['total_value']:,.0f} KRW")
        logger.info(f"  Daily Return: {performance['daily_return']:.2%}")
        logger.info(f"  Positions: {performance['positions']}")
        logger.info(f"  Today's Trades: {performance['daily_trades']}")
    
    async def run(self):
        """메인 실행 루프"""
        logger.info("\n" + "="*60)
        logger.info("🚀 Starting AI Trading System DEMO...")
        logger.info("="*60)
        
        try:
            # 초기화
            await self.initialize()
            
            self.is_running = True
            cycle_count = 0
            
            while self.is_running:
                try:
                    cycle_count += 1
                    logger.info(f"\n\n{'='*60}")
                    logger.info(f"CYCLE #{cycle_count}")
                    logger.info(f"{'='*60}")
                    
                    # 트레이딩 사이클 실행
                    await self.run_trading_cycle()
                    
                    # 거래 내역 표시
                    if self.trade_history:
                        logger.info("\n📜 Recent Trades:")
                        for trade in self.trade_history[-5:]:
                            logger.info(f"  {trade['timestamp'].strftime('%H:%M:%S')} - "
                                      f"{trade['action']} {trade['stock_name']} "
                                      f"x{trade['quantity']} @ {trade['price']:,.0f}")
                    
                    # 다음 사이클까지 대기
                    logger.info(f"\n⏰ Next cycle in 30 seconds...")
                    await asyncio.sleep(30)
                    
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}", exc_info=True)
                    await asyncio.sleep(10)
                    
        finally:
            self.is_running = False
            await self.cleanup()
    
    async def cleanup(self):
        """시스템 정리"""
        logger.info("\n=== Cleaning up DEMO system ===")
        
        # 최종 성과 표시
        if self.performance_history:
            initial_value = 10000000  # 초기 자본
            final_value = self.total_value
            total_return = (final_value - initial_value) / initial_value
            
            logger.info("\n📈 Final Performance:")
            logger.info(f"  Initial Capital: {initial_value:,.0f} KRW")
            logger.info(f"  Final Value: {final_value:,.0f} KRW")
            logger.info(f"  Total Return: {total_return:.2%}")
            logger.info(f"  Total Trades: {len(self.trade_history)}")
        
        logger.info("AI Trading System DEMO stopped")


async def main():
    """메인 실행 함수"""
    system = AITradingSystemDemo()
    await system.run()


if __name__ == "__main__":
    asyncio.run(main())