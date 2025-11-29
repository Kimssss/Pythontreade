"""
AI 자동매매 시스템 메인 실행 모듈
블로그 분석 기반 통합 시스템
"""
import asyncio
import logging
import logging.config
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Optional
import json
import os

# 시스템 모듈
try:
    from .models.ensemble_system import MultiAgentEnsemble
    from .strategies.stock_screener import StockScreener
    from .utils.kis_api import KisAPIEnhanced
    from .utils.risk_manager import RiskManager
    from .utils.technical_indicators import TechnicalIndicators
    from .config.settings import (
        KIS_CONFIG, TRADING_CONFIG, DATA_CONFIG, 
        LOGGING_CONFIG, SCREENING_CONFIG
    )
except ImportError:
    from models.ensemble_system import MultiAgentEnsemble
    from strategies.stock_screener import StockScreener
    from utils.kis_api import KisAPIEnhanced
    from utils.risk_manager import RiskManager
    from utils.technical_indicators import TechnicalIndicators
    from config.settings import (
        KIS_CONFIG, TRADING_CONFIG, DATA_CONFIG, 
        LOGGING_CONFIG, SCREENING_CONFIG
    )

# 로깅 설정
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('ai_trading')


class AITradingSystem:
    """AI 자동매매 통합 시스템"""
    
    def __init__(self, mode: str = 'demo'):
        """
        Args:
            mode: 'demo' (모의투자) 또는 'real' (실전투자)
        """
        self.mode = mode
        logger.info(f"Initializing AI Trading System in {mode} mode")
        
        # KIS API 초기화
        config = KIS_CONFIG[mode]
        self.kis_api = KisAPIEnhanced(
            appkey=config['appkey'],
            appsecret=config['appsecret'],
            account_no=config['account'],
            is_real=config['is_real']
        )
        
        # 컴포넌트 초기화
        self.ensemble = MultiAgentEnsemble(self.kis_api)
        self.screener = StockScreener(self.kis_api)
        self.risk_manager = RiskManager()
        self.indicators = TechnicalIndicators()
        
        # 포트폴리오 상태
        self.portfolio = {}
        self.cash_balance = 0
        self.total_value = 0
        
        # 거래 히스토리
        self.trade_history = []
        self.performance_history = []
        
        # 실행 상태
        self.is_running = False
        
        logger.info("AI Trading System initialized successfully")
    
    async def initialize(self):
        """시스템 초기화 및 토큰 발급"""
        logger.info("Getting access token...")
        if not self.kis_api.get_access_token():
            raise Exception("Failed to get access token")
        
        # 계좌 정보 조회
        await self.update_portfolio_status()
        logger.info(f"Initial portfolio value: {self.total_value:,.0f} KRW")
    
    async def update_portfolio_status(self):
        """포트폴리오 상태 업데이트"""
        try:
            # 현금 잔고 조회
            self.cash_balance = self.kis_api.get_available_cash()
            
            # 보유 종목 조회
            holdings = self.kis_api.get_holding_stocks()
            
            self.portfolio = {}
            portfolio_value = self.cash_balance
            
            for holding in holdings:
                self.portfolio[holding['stock_code']] = {
                    'name': holding['stock_name'],
                    'quantity': holding['quantity'],
                    'avg_price': holding['avg_price'],
                    'current_price': holding['current_price'],
                    'value': holding['eval_amt'],
                    'profit_loss': holding['profit_loss'],
                    'profit_rate': holding['profit_rate']
                }
                portfolio_value += holding['eval_amt']
            
            self.total_value = portfolio_value
            
        except Exception as e:
            logger.error(f"Error updating portfolio status: {e}")
            # 주말이나 장외시간일 경우 기본값 사용
            logger.info("Using default values for weekend/after-hours")
            if self.cash_balance is None:
                self.cash_balance = 0
            if self.total_value is None:
                self.total_value = 0
    
    async def run_trading_cycle(self):
        """메인 트레이딩 사이클"""
        logger.info("=== Starting Trading Cycle ===")
        
        try:
            # 1. 시장 상태 분석
            market_condition = await self.analyze_market_condition()
            logger.info(f"Market condition: {market_condition}")
            
            # 2. 종목 스크리닝
            candidates = await self.screener.screen_stocks(market_condition)
            logger.info(f"Screened {len(candidates)} candidate stocks")
            
            # 3. 포트폴리오 업데이트
            await self.update_portfolio_status()
            
            # 4. 각 종목별 신호 생성 및 거래 결정
            signals = []
            for stock in candidates[:10]:  # 상위 10개 종목만 분석
                signal = await self.analyze_stock_and_generate_signal(stock)
                if signal and signal['confidence'] >= TRADING_CONFIG['min_confidence']:
                    signals.append(signal)
            
            logger.info(f"Generated {len(signals)} trading signals")
            
            # 5. 리스크 필터링
            filtered_signals = self.filter_signals_by_risk(signals)
            logger.info(f"After risk filtering: {len(filtered_signals)} signals")
            
            # 6. 주문 실행
            executed_trades = await self.execute_trades(filtered_signals)
            logger.info(f"Executed {len(executed_trades)} trades")
            
            # 7. 포트폴리오 리밸런싱 체크
            if self.should_rebalance():
                await self.rebalance_portfolio()
            
            # 8. 성과 기록
            self.record_performance()
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}", exc_info=True)
    
    async def analyze_market_condition(self) -> str:
        """시장 상태 분석"""
        try:
            # KOSPI 지수 데이터로 시장 분석 (실제로는 별도 API 필요)
            # 여기서는 간단한 로직으로 구현
            top_stocks = await self.screener.get_market_stocks()
            
            if not top_stocks:
                return 'normal'
            
            # 상승/하락 종목 비율 계산
            up_count = sum(1 for s in top_stocks if s['change_rate'] > 0)
            down_count = len(top_stocks) - up_count
            
            up_ratio = up_count / len(top_stocks) if len(top_stocks) > 0 else 0.5
            
            if up_ratio > 0.7:
                return 'bull'
            elif up_ratio < 0.3:
                return 'bear'
            else:
                return 'normal'
                
        except Exception as e:
            logger.error(f"Error analyzing market condition: {e}")
            return 'normal'
    
    async def analyze_stock_and_generate_signal(self, stock: Dict) -> Optional[Dict]:
        """개별 종목 분석 및 신호 생성"""
        try:
            stock_code = stock['code']
            
            # 일봉 데이터 조회
            daily_data = self.kis_api.get_daily_price(stock_code, count=60)
            if not daily_data or daily_data.get('rt_cd') != '0':
                return None
            
            # DataFrame 변환
            df_data = []
            for item in daily_data.get('output', []):
                df_data.append({
                    'date': item['stck_bsop_date'],
                    'open': float(item['stck_oprc']),
                    'high': float(item['stck_hgpr']),
                    'low': float(item['stck_lwpr']),
                    'close': float(item['stck_clpr']),
                    'volume': int(item['acml_vol'])
                })
            
            if len(df_data) < 30:
                return None
            
            df = pd.DataFrame(df_data).sort_values('date')
            df.set_index('date', inplace=True)
            
            # 현재 포지션 확인
            current_position = 1 if stock_code in self.portfolio else 0
            
            # 앙상블 신호 생성
            signal = await self.ensemble.generate_signal(
                stock_code, df, current_position
            )
            
            # 추가 정보
            signal['stock_name'] = stock['name']
            signal['current_price'] = stock['price']
            signal['market_cap'] = stock.get('market_cap', 0)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error analyzing stock {stock['code']}: {e}")
            return None
    
    def filter_signals_by_risk(self, signals: List[Dict]) -> List[Dict]:
        """리스크 기준으로 신호 필터링"""
        filtered = []
        
        # 포트폴리오 리스크 메트릭 계산
        portfolio_returns = self.calculate_portfolio_returns()
        current_leverage = self.risk_manager.adjust_leverage_by_risk(portfolio_returns)
        
        for signal in signals:
            # 매수 신호만 처리 (매도는 별도 로직)
            if signal['action'] != 0:  # 0: Buy
                continue
            
            # 가상 포지션으로 리스크 체크
            position_value = self.total_value * TRADING_CONFIG['max_position_size']
            position_value *= current_leverage  # 레버리지 적용
            
            mock_position = {
                'code': signal['stock_code'],
                'value': position_value
            }
            
            # 리스크 한도 체크
            approved, reason = self.risk_manager.check_risk_limits(
                {'portfolio': self.portfolio, 'returns': portfolio_returns},
                mock_position
            )
            
            if approved:
                signal['position_size'] = self.risk_manager.calculate_position_size(
                    signal['confidence'],
                    self.total_value,
                    signal['current_price'],
                    0.02  # 기본 변동성 (실제로는 계산 필요)
                )
                
                if signal['position_size'] > 0:
                    filtered.append(signal)
            else:
                logger.info(f"Signal filtered for {signal['stock_code']}: {reason}")
        
        return filtered
    
    async def execute_trades(self, signals: List[Dict]) -> List[Dict]:
        """거래 실행"""
        executed = []
        
        for signal in signals:
            try:
                stock_code = signal['stock_code']
                quantity = signal['position_size']
                
                if signal['action'] == 0:  # Buy
                    # 주문 가능 금액 체크
                    required_amount = signal['current_price'] * quantity
                    if required_amount > self.cash_balance:
                        logger.warning(f"Insufficient cash for {stock_code}")
                        continue
                    
                    # 매수 주문
                    result = self.kis_api.buy_stock(
                        stock_code, 
                        quantity,
                        order_type="03"  # 시장가
                    )
                    
                    if result and result.get('rt_cd') == '0':
                        trade = {
                            'timestamp': datetime.now(),
                            'stock_code': stock_code,
                            'stock_name': signal['stock_name'],
                            'action': 'BUY',
                            'quantity': quantity,
                            'price': signal['current_price'],
                            'signal': signal,
                            'order_no': result.get('output', {}).get('odno')
                        }
                        
                        executed.append(trade)
                        self.trade_history.append(trade)
                        
                        logger.info(f"Executed BUY: {stock_code} x{quantity}")
                        
                        # 잔고 업데이트
                        self.cash_balance -= required_amount
                
                elif signal['action'] == 1:  # Sell
                    if stock_code in self.portfolio:
                        holding = self.portfolio[stock_code]
                        
                        # 매도 주문
                        result = self.kis_api.sell_stock(
                            stock_code,
                            holding['quantity'],
                            order_type="03"
                        )
                        
                        if result and result.get('rt_cd') == '0':
                            trade = {
                                'timestamp': datetime.now(),
                                'stock_code': stock_code,
                                'stock_name': signal['stock_name'],
                                'action': 'SELL',
                                'quantity': holding['quantity'],
                                'price': signal['current_price'],
                                'signal': signal,
                                'order_no': result.get('output', {}).get('odno')
                            }
                            
                            executed.append(trade)
                            self.trade_history.append(trade)
                            
                            logger.info(f"Executed SELL: {stock_code} x{holding['quantity']}")
                
                # API 호출 간격
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error executing trade for {signal['stock_code']}: {e}")
        
        return executed
    
    def calculate_portfolio_returns(self) -> pd.Series:
        """포트폴리오 수익률 계산"""
        if len(self.performance_history) < 2:
            return pd.Series()
        
        values = [p['total_value'] for p in self.performance_history]
        returns = pd.Series(values).pct_change().dropna()
        
        return returns
    
    def should_rebalance(self) -> bool:
        """리밸런싱 필요 여부 확인"""
        if not self.portfolio:
            return False
        
        # 월 1회 리밸런싱 (매월 첫 거래일)
        if len(self.trade_history) > 0:
            last_rebalance = self.trade_history[-1]['timestamp']
            if (datetime.now() - last_rebalance).days < 30:
                return False
        
        return True
    
    async def rebalance_portfolio(self):
        """포트폴리오 리밸런싱"""
        logger.info("Starting portfolio rebalancing...")
        
        try:
            # 현재 보유 종목 재평가
            for stock_code in list(self.portfolio.keys()):
                # 종목 재분석
                stock_info = await self.screener.get_stock_details(stock_code)
                if not stock_info:
                    continue
                
                # 매도 여부 결정
                df = pd.DataFrame([{
                    'close': stock_info['current_price'],
                    'volume': stock_info['volume']
                }])
                
                signal = await self.ensemble.generate_signal(stock_code, df, 1)
                
                if signal['action'] == 1:  # Sell signal
                    await self.execute_trades([signal])
            
            logger.info("Portfolio rebalancing completed")
            
        except Exception as e:
            logger.error(f"Error during rebalancing: {e}")
    
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
        
        # 리스크 메트릭
        returns = self.calculate_portfolio_returns()
        if len(returns) > 0:
            risk_metrics = self.risk_manager.get_risk_metrics(
                pd.DataFrame({'value': [p['total_value'] 
                            for p in self.performance_history + [performance]]})
            )
            performance.update(risk_metrics)
        
        self.performance_history.append(performance)
        
        # 최근 1000개만 유지
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
        
        logger.info(f"Performance: Value={performance['total_value']:,.0f}, "
                   f"Return={performance['daily_return']:.2%}")
    
    async def run(self):
        """메인 실행 루프"""
        logger.info("Starting AI Trading System...")
        
        try:
            # 초기화
            await self.initialize()
            
            self.is_running = True
            
            while self.is_running:
                try:
                    # 장 시간 체크 (9:00 ~ 15:30)
                    now = datetime.now()
                    if now.weekday() < 5:  # 평일
                        if 9 <= now.hour < 15 or (now.hour == 15 and now.minute < 30):
                            # 트레이딩 사이클 실행
                            await self.run_trading_cycle()
                            
                            # 다음 사이클까지 대기 (5분)
                            await asyncio.sleep(300)
                        else:
                            # 장 마감 후 일일 정산
                            if now.hour == 15 and now.minute == 30:
                                await self.daily_settlement()
                            
                            # 장외 시간 대기
                            logger.info("Market closed. Waiting...")
                            await asyncio.sleep(3600)  # 1시간 대기
                    else:
                        # 주말 대기
                        logger.info("Weekend. Waiting...")
                        await asyncio.sleep(3600)  # 1시간 대기
                        
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}", exc_info=True)
                    await asyncio.sleep(60)  # 1분 후 재시도
                    
        finally:
            self.is_running = False
            await self.cleanup()
    
    async def daily_settlement(self):
        """일일 정산 및 학습"""
        logger.info("=== Daily Settlement ===")
        
        try:
            # 일일 성과 요약
            daily_trades = [t for t in self.trade_history 
                          if t['timestamp'].date() == datetime.now().date()]
            
            logger.info(f"Today's trades: {len(daily_trades)}")
            logger.info(f"Portfolio value: {self.total_value:,.0f} KRW")
            
            # 리스크 메트릭 출력
            returns = self.calculate_portfolio_returns()
            if len(returns) > 0:
                metrics = self.risk_manager.get_risk_metrics(
                    pd.DataFrame({'value': [p['total_value'] 
                                for p in self.performance_history]})
                )
                
                logger.info(f"Risk metrics: VaR={metrics['var_95']:.2%}, "
                          f"Sharpe={metrics['sharpe_ratio']:.2f}")
            
            # 성과 저장
            self.save_performance_data()
            
            # DQN 모델 학습 (강화학습)
            # 실제 구현시 추가 필요
            
        except Exception as e:
            logger.error(f"Error in daily settlement: {e}")
    
    def save_performance_data(self):
        """성과 데이터 저장"""
        try:
            # 성과 히스토리 저장
            performance_file = f"performance_{self.mode}_{datetime.now().strftime('%Y%m')}.json"
            with open(performance_file, 'w') as f:
                json.dump(self.performance_history, f, default=str, indent=2)
            
            # 거래 히스토리 저장
            trades_file = f"trades_{self.mode}_{datetime.now().strftime('%Y%m')}.json"
            with open(trades_file, 'w') as f:
                json.dump(self.trade_history, f, default=str, indent=2)
            
            logger.info("Performance data saved")
            
        except Exception as e:
            logger.error(f"Error saving performance data: {e}")
    
    async def cleanup(self):
        """시스템 정리"""
        logger.info("Cleaning up...")
        
        # 성과 데이터 저장
        self.save_performance_data()
        
        # DQN 모델 저장
        model_file = f"models/dqn_model_{self.mode}_{datetime.now().strftime('%Y%m%d')}.pt"
        self.ensemble.dqn_agent.save_model(model_file)
        
        logger.info("AI Trading System stopped")


async def main():
    """메인 실행 함수"""
    # 환경 변수 체크
    mode = os.environ.get('TRADING_MODE', 'demo')
    
    # 필수 환경 변수 확인
    required_vars = [
        f'KIS_{mode.upper()}_APPKEY',
        f'KIS_{mode.upper()}_APPSECRET',
        f'KIS_{mode.upper()}_ACCOUNT'
    ]
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        return
    
    # 시스템 실행
    system = AITradingSystem(mode=mode)
    await system.run()


if __name__ == "__main__":
    asyncio.run(main())