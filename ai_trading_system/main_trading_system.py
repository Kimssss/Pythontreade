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
    from ai_trading_system.models.ensemble_system import MultiAgentEnsemble
    from ai_trading_system.strategies.stock_screener import StockScreener
    from ai_trading_system.utils.kis_api import KisAPIEnhanced
    from ai_trading_system.utils.risk_manager import RiskManager
    from ai_trading_system.utils.technical_indicators import TechnicalIndicators
    from ai_trading_system.training.weekend_trainer import WeekendTrainer
    from ai_trading_system.mlops.model_manager import AutoMLOpsManager
    from ai_trading_system.agents.sentiment_agent import SentimentAgent
    from ai_trading_system.config.settings import (
        KIS_CONFIG, TRADING_CONFIG, DATA_CONFIG, 
        LOGGING_CONFIG, SCREENING_CONFIG
    )
except ImportError:
    try:
        from .models.ensemble_system import MultiAgentEnsemble
        from .strategies.stock_screener import StockScreener
        from .utils.kis_api import KisAPIEnhanced
        from .utils.risk_manager import RiskManager
        from .utils.technical_indicators import TechnicalIndicators
        from .training.weekend_trainer import WeekendTrainer
        from .mlops.model_manager import AutoMLOpsManager
        from .agents.sentiment_agent import SentimentAgent
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
        from training.weekend_trainer import WeekendTrainer
        from mlops.model_manager import AutoMLOpsManager
        from agents.sentiment_agent import SentimentAgent
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
        logger.info(f"AI 트레이딩 시스템 초기화 중 - {mode} 모드")
        
        # KIS API 초기화
        config = KIS_CONFIG[mode]
        self.kis_api = KisAPIEnhanced(
            appkey=config['appkey'],
            appsecret=config['appsecret'],
            account_no=config['account'],
            is_real=config['is_real'],
            min_request_interval=KIS_CONFIG.get('MIN_REQUEST_INTERVAL', 1.0)
        )
        
        # 컴포넌트 초기화
        self.ensemble = MultiAgentEnsemble(self.kis_api)
        self.screener = StockScreener(self.kis_api)
        self.risk_manager = RiskManager()
        self.indicators = TechnicalIndicators()
        self.trainer = WeekendTrainer(self.ensemble, self.kis_api)
        
        # MLOps 자동화 시스템
        self.mlops_manager = AutoMLOpsManager()
        self.mlops_manager.start_monitoring()
        
        # 감성 분석 에이전트
        self.sentiment_agent = SentimentAgent()
        
        # 백테스트 엔진 (Win Rate 계산용)
        try:
            from ai_trading_system.backtesting.backtest_engine import BacktestEngine
        except ImportError:
            from backtesting.backtest_engine import BacktestEngine
        self.backtest_engine = BacktestEngine(initial_capital=10000000)
        
        # 해외주식 API 초기화
        self.kis_api.initialize_overseas_api()
        
        # 글로벌 스크리너 초기화
        from .strategies.global_screener import GlobalStockScreener
        self.global_screener = GlobalStockScreener(self.kis_api)
        
        # 거래 모드 설정 (국내만, 해외만, 또는 둘 다)
        self.trading_mode = os.environ.get('GLOBAL_TRADING_MODE', 'domestic')  # domestic, overseas, both
        
        # 포트폴리오 상태
        self.portfolio = {}
        self.cash_balance = 0
        self.total_value = 0
        
        # API를 통해서만 데이터 가져오기 - 더미 데이터 사용 금지
        logger.info(f"모드: {mode} - 모든 데이터는 API에서만 가져옵니다")
        
        # 거래 히스토리
        self.trade_history = []
        self.performance_history = []
        
        # 실행 상태
        self.is_running = False
        
        logger.info("AI 트레이딩 시스템 초기화 완료")
    
    async def initialize(self):
        """시스템 초기화 및 토큰 발급"""
        logger.info("=== 시스템 초기화 ===")
        logger.info(f"거래 모드: {self.mode}")
        logger.info("액세스 토큰 발급 중...")
        
        # 토큰 발급 시도 (캐시 우선 사용)
        try:
            # 이미 토큰이 있는지 확인
            if hasattr(self.kis_api, 'access_token') and self.kis_api.access_token:
                logger.info("기존 캐시된 토큰 사용")
                token_result = True
            else:
                token_result = self.kis_api.get_access_token()
            
            if not token_result:
                logger.error("액세스 토큰 발급 실패 - API 인증 정보를 확인하세요")
                raise Exception("Failed to get access token")
        except Exception as e:
            logger.error(f"토큰 발급 오류: {e}")
            raise Exception("Failed to get access token")
        
        logger.info("액세스 토큰 발급 성공")
        
        # 계좌 정보 조회
        logger.info("초기 계좌 정보 조회 중...")
        await self.update_portfolio_status()
        
        logger.info("=== 초기화 완료 ===")
        logger.info(f"초기 포트폴리오 가치: {self.total_value:,.0f}원")
    
    async def update_portfolio_status(self):
        """포트폴리오 상태 업데이트"""
        logger.info("=== 포트폴리오 상태 업데이트 ===")
        try:
            # 현금 잔고 조회
            logger.info("현금 잔고 조회 중...")
            self.cash_balance = self.kis_api.get_available_cash()
            logger.info(f"현금 잔고: {self.cash_balance:,.0f}원")
            
            # 보유 종목 조회
            logger.info("보유 종목 조회 중...")
            holdings = self.kis_api.get_holding_stocks()
            logger.info(f"{len(holdings)}개 보유 종목 발견")
            
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
                logger.info(f"  - {holding['stock_name']}: {holding['quantity']}주, "
                          f"평가금액: {holding['eval_amt']:,.0f}원, "
                          f"수익률: {holding['profit_rate']:.2f}%")
            
            self.total_value = portfolio_value
            # 잔고가 0이면 API에서 반환한 실제 값
            if self.total_value == 0:
                logger.warning("포트폴리오 가치가 0입니다. 이는 API에서 받은 실제 값입니다.")
            
            logger.info(f"총 포트폴리오 가치: {self.total_value:,.0f}원")
            logger.info(f"  - 현금: {self.cash_balance:,.0f}원")
            logger.info(f"  - 주식: {portfolio_value - self.cash_balance:,.0f}원")
            
        except Exception as e:
            logger.error(f"포트폴리오 상태 업데이트 오류: {e}", exc_info=True)
            # 주말이나 장외시간일 경우 기본값 사용
            logger.info("주말/장외시간으로 기본값 사용")
            if self.cash_balance is None:
                self.cash_balance = 0
            if self.total_value is None:
                self.total_value = 0
            
            # API 응답에서 받은 실제 값 사용 (더미 데이터 금지)
            logger.warning(f"API 반환 값 - 현금: {self.cash_balance:,.0f}원, 총액: {self.total_value:,.0f}원")
            
            logger.info(f"기본값 설정 완료 - 현금: {self.cash_balance:,.0f}원, 총액: {self.total_value:,.0f}원")
    
    def get_active_markets(self) -> Dict[str, bool]:
        """현재 거래 가능한 시장 확인"""
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        weekday = now.weekday()
        
        markets = {
            'korean': False,
            'us': False
        }
        
        # 평일만 거래
        if weekday >= 5:  # 토요일(5), 일요일(6)
            return markets
        
        # 한국 시장: 09:00 ~ 15:30
        if 9 <= hour < 15 or (hour == 15 and minute <= 30):
            markets['korean'] = True
            
        # 미국 시장: 23:30 ~ 06:00 (서머타임: 22:30 ~ 05:00)
        # 현재 서머타임 여부는 간단히 구현
        is_dst = 4 <= now.month <= 10  # 대략적인 서머타임 기간
        
        if is_dst:
            if hour >= 22 or hour < 5:
                markets['us'] = True
            elif hour == 22 and minute >= 30:
                markets['us'] = True
        else:
            if hour >= 23 or hour < 6:
                markets['us'] = True
            elif hour == 23 and minute >= 30:
                markets['us'] = True
            
        return markets

    async def run_trading_cycle(self):
        """메인 트레이딩 사이클 - 시간대별 자동 거래"""
        logger.info("=== 거래 사이클 시작 ===")
        
        try:
            # 현재 거래 가능한 시장 확인
            active_markets = self.get_active_markets()
            logger.info(f"활성 시장: {active_markets}")
            
            # 활성 시장이 없으면 스킵
            active_list = [k for k, v in active_markets.items() if v]
            if not active_list:
                logger.info("현재 시간에 활성 시장이 없습니다")
                return
            
            # 1. 시장 상태 분석
            market_condition = await self.analyze_market_condition()
            logger.info(f"시장 상황: {market_condition}")
            
            # 2. 활성 시장에 따른 종목 스크리닝
            if active_markets['korean']:
                await self._trade_korean_stocks(market_condition)
                
            if active_markets['us']:
                await self._trade_us_stocks(market_condition)
            
            # 3. 성과 기록
            self.record_performance()
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}", exc_info=True)
    
    async def _trade_korean_stocks(self, market_condition: str):
        """한국 주식 거래"""
        logger.info("=== Trading Korean Stocks ===")
        
        # 종목 스크리닝
        candidates = await self.screener.screen_stocks(market_condition)
        logger.info(f"Screened {len(candidates)} Korean stocks")
        
        # 포트폴리오 업데이트
        await self.update_portfolio_status()
        
        # 각 종목별 신호 생성 및 거래 결정
        signals = []
        for stock in candidates[:100]:  # 상위 100개 종목 분석
            signal = await self.analyze_stock_and_generate_signal(stock)
            if signal and signal['confidence'] >= TRADING_CONFIG['min_confidence']:
                signals.append(signal)
            # 신뢰도 기준 미달시 제외
        
        logger.info(f"Generated {len(signals)} Korean trading signals")
        
        # 리스크 필터링
        filtered_signals = self.filter_signals_by_risk(signals)
        logger.info(f"After risk filtering: {len(filtered_signals)} signals")
        
        # 주문 실행
        executed_trades = await self.execute_trades(filtered_signals)
        logger.info(f"Executed {len(executed_trades)} Korean trades")
        
        # 거래 완료
    
    async def _trade_us_stocks(self, market_condition: str):
        """미국 주식 거래"""
        logger.info("=== Trading US Stocks ===")
        
        try:
            # 글로벌 스크리너 사용
            results = await self.global_screener.screen_global_stocks(['NASDAQ', 'NYSE'])
            us_candidates = results.get('overseas', [])
            
            logger.info(f"Screened {len(us_candidates)} US stocks")
            
            # 해외 주식 잔고 조회
            overseas_balance = self.kis_api.overseas.get_overseas_balance()
            if overseas_balance:
                logger.info(f"US cash balance: ${overseas_balance.get('foreign_currency_amount', 0):,.2f}")
            else:
                logger.warning("가져오기 실패 overseas balance")
                overseas_balance = {'foreign_currency_amount': 0}
            
            # 신호 생성 및 거래
            for stock in us_candidates[:100]:  # 상위 100개
                try:
                    # 매수 신호인 경우 (보수적 기준 적용)
                    if stock['score'] > 0.65:  # 점수 기준 - 실전용 적정 설정
                        # 적정 수량 계산 (포트폴리오의 10% 이내)
                        available_cash = overseas_balance.get('foreign_currency_amount', 0) if overseas_balance else 0
                        position_size = min(available_cash * 0.1, 10000)  # 최대 $10,000
                        quantity = int(position_size / stock['price'])
                        
                        if quantity > 0:
                            logger.info(f"Buying US stock: {stock['code']} x {quantity} @ ${stock['price']}")
                            
                            # API로 실제 주문 실행 (데모 모드도 실제 API 사용)
                            result = self.kis_api.overseas.buy_overseas_stock(
                                exchange='NASD' if stock['exchange'] == 'NASDAQ' else 'NYSE',
                                symbol=stock['code'],
                                quantity=quantity,
                                order_type='00'  # 시장가
                            )
                            
                            if result and result.get('rt_cd') == '0':
                                logger.info(f"US stock buy order successful: {stock['code']}")
                                
                                # 거래 기록
                                trade = {
                                    'timestamp': datetime.now(),
                                    'stock_code': stock['code'],
                                    'stock_name': stock['name'],
                                    'market': 'US',
                                    'action': 'BUY',
                                    'quantity': quantity,
                                    'price': stock['price'],
                                    'currency': 'USD',
                                    'order_no': result.get('output', {}).get('orno', 'N/A')
                                }
                                self.trade_history.append(trade)
                
                except Exception as e:
                    logger.error(f"Error trading US stock {stock.get('code', 'UNKNOWN')}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in US stock trading: {e}")
    
    async def _execute_demo_test_trade(self, stock: Dict):
        """데모 모드 테스트 거래 실행"""
        try:
            logger.info(f"\n=== DEMO TEST TRADE ===")
            logger.info(f"Stock: {stock['name']} ({stock['code']})")
            logger.info(f"Price: {stock['price']:,.0f} KRW")
            
            # 소량 매수 (1주)
            quantity = 1
            required_amount = stock['price'] * quantity
            
            if self.cash_balance >= required_amount:
                logger.info(f"Buying {quantity} share at {stock['price']:,.0f} KRW")
                
                # 매수 주문
                result = self.kis_api.buy_stock(
                    stock['code'], 
                    quantity,
                    order_type="03"  # 시장가
                )
                
                if result and result.get('rt_cd') == '0':
                    logger.info("\u2705 Demo test trade SUCCESSFUL!")
                    trade = {
                        'timestamp': datetime.now(),
                        'stock_code': stock['code'],
                        'stock_name': stock['name'],
                        'action': 'BUY',
                        'quantity': quantity,
                        'price': stock['price'],
                        'order_no': result.get('output', {}).get('odno', 'DEMO')
                    }
                    self.trade_history.append(trade)
                else:
                    logger.error(f"Demo test trade failed: {result}")
            else:
                logger.warning(f"Insufficient cash for demo test trade. Need: {required_amount:,.0f}, Have: {self.cash_balance:,.0f}")
                
        except Exception as e:
            logger.error(f"Error in demo test trade: {e}")
    
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
            # 매수 및 매도 신호 처리
            if signal['action'] == 0:  # 0: Buy
                pass  # 아래에서 처리
            elif signal['action'] == 1 and signal['stock_code'] in self.portfolio:  # 1: Sell
                # 매도 신호도 필터링 없이 포함
                filtered.append(signal)
                continue
            else:
                continue
            
            # 가상 포지션으로 리스크 체크
            position_value = self.total_value * TRADING_CONFIG['max_position_size']
            position_value *= current_leverage  # 레버리지 적용
            
            mock_position = {
                'code': signal['stock_code'],
                'value': position_value
            }
            
            # 리스크 한도 체크 (모든 모드에서 동일 적용)
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
                            '신호': signal,
                            'order_no': result.get('output', {}).get('odno')
                        }
                        
                        executed.append(trade)
                        self.trade_history.append(trade)
                        
                        # 백테스트 엔진에도 기록 (Win Rate 계산용)
                        self.backtest_engine.add_trade(
                            symbol=stock_code,
                            action='buy',
                            quantity=quantity,
                            price=signal['current_price'],
                            timestamp=datetime.now(),
                            reason=f"AI Signal: {signal.get('confidence', 0):.2f}"
                        )
                        
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
                                '신호': signal,
                                'order_no': result.get('output', {}).get('odno')
                            }
                            
                            executed.append(trade)
                            self.trade_history.append(trade)
                            
                            # 백테스트 엔진에도 기록 (Win Rate 계산용)
                            self.backtest_engine.add_trade(
                                symbol=stock_code,
                                action='sell',
                                quantity=holding['quantity'],
                                price=signal['current_price'],
                                timestamp=datetime.now(),
                                reason=f"AI Signal: {signal.get('confidence', 0):.2f}"
                            )
                            
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
        logger.info("포트폴리오 리밸런싱 시작...")
        
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
        # 백테스트 엔진으로 성과 계산
        if len(self.backtest_engine.trades) > 0:
            self.backtest_engine.calculate_performance_metrics()
            win_rate = self.backtest_engine.performance_metrics.get('win_rate', 0)
            total_trades = self.backtest_engine.performance_metrics.get('total_trades', 0)
        else:
            win_rate = 0
            total_trades = 0
        
        performance = {
            'timestamp': datetime.now(),
            'total_value': self.total_value,
            'cash_balance': self.cash_balance,
            'positions': len(self.portfolio),
            'daily_trades': len([t for t in self.trade_history 
                               if t['timestamp'].date() == datetime.now().date()]),
            'win_rate': win_rate,
            'total_trades': total_trades
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
        
        logger.info(f"📊 성과: 자산={performance['total_value']:,.0f}원, "
                   f"수익률={performance['daily_return']:.2%}, "
                   f"승률={performance['win_rate']:.1%} "
                   f"({performance['total_trades']}거래)")
    
    async def run(self):
        """메인 실행 루프"""
        logger.info("AI 자동매매 시스템 시작...")
        
        try:
            # 초기화
            await self.initialize()
            
            self.is_running = True
            
            while self.is_running:
                try:
                    now = datetime.now()
                    active_markets = self.get_active_markets()
                    active_list = [k for k, v in active_markets.items() if v]
                    
                    if now.weekday() < 5 and active_list:  # 평일이고 활성 시장이 있는 경우
                        # 트레이딩 사이클 실행
                        logger.info(f"\n{'='*60}")
                        logger.info(f"거래 활성 - {now.strftime('%Y-%m-%d %H:%M:%S')}")
                        logger.info(f"활성 시장: {', '.join(active_list).upper()}")
                        
                        # 각 시장의 거래 시간 표시
                        if active_markets['korean']:
                            logger.info("🇰🇷 한국 시장: 09:00-15:30 KST (활성)")
                        if active_markets['us']:
                            logger.info("🇺🇸 미국 시장: 23:30-06:00 KST (활성)")
                            
                        await self.run_trading_cycle()
                        
                        # 다음 사이클까지 대기 (5분) + 학습
                        logger.info("\n[다음 사이클] 다음 거래 사이클까지 5분 대기...")
                        logger.info(f"다음 실행: {(now + timedelta(minutes=5)).strftime('%H:%M:%S')}")
                        
                        # 5분 대기 시간 동안 학습 실행
                        logger.info("\n🧠 [대기 중 학습] 백그라운드 학습 시작...")
                        
                        # 학습을 위한 시간 분할 (총 300초 = 5분)
                        training_start_time = datetime.now()
                        total_wait_time = 300  # 5분
                        
                        while (datetime.now() - training_start_time).total_seconds() < total_wait_time:
                            remaining_time = total_wait_time - (datetime.now() - training_start_time).total_seconds()
                            
                            if remaining_time > 60:  # 1분 이상 남았으면 학습 시도
                                logger.info(f"⏰ 남은 대기시간: {remaining_time:.0f}초 - 빠른 학습 시작...")
                                
                                try:
                                    # 빠른 학습 모드 사용 (최대 60초)
                                    training_result = await self.trainer.run_quick_training(max_time_seconds=min(60, remaining_time - 10))
                                    
                                    if training_result:
                                        logger.info("✅ 빠른 학습 완료!")
                                        logger.info(f"   종목: {training_result['stock_name']}")
                                        logger.info(f"   승률: {training_result['win_rate']:.1%}")
                                    else:
                                        logger.info("⚠️ 빠른 학습 실패, 대체 방법 시도...")
                                        # 실패 시 기존 방식으로 시도
                                        training_result = await self.trainer.run_single_stock_training()
                                        if training_result:
                                            logger.info("✅ 대체 학습 완료!")
                                        
                                except Exception as e:
                                    logger.error(f"대기 중 학습 오류: {e}")
                                
                                # 학습 후 짧은 휴식
                                await asyncio.sleep(10)
                            else:
                                # 남은 시간이 1분 미만이면 그냥 대기
                                logger.info(f"⏰ 남은시간: {remaining_time:.0f}초 - 대기 완료...")
                                await asyncio.sleep(remaining_time)
                                break
                        
                        logger.info("✅ 백그라운드 학습과 함께 대기 완료")
                    else:
                            # 장 마감 후 일일 정산
                            if now.hour == 15 and now.minute == 30:
                                logger.info("\n[장마감] 일일 정산 실행...")
                                await self.daily_settlement()
                            
                            # 장외 시간 대기
                            logger.info(f"\n[장외시간] {now.strftime('%H:%M')} 현재 활성 시장 없음")
                            
                            # 다음 오픈 시간 계산
                            next_open_times = []
                            current_hour = now.hour
                            
                            # 한국 시장
                            if current_hour < 9:
                                next_open_times.append("🇰🇷 한국장: 오늘 09:00")
                            elif current_hour >= 15:
                                next_open_times.append("🇰🇷 한국장: 내일 09:00")
                                
                            # 미국 시장 (서머타임 기준)
                            if 4 <= now.month <= 10:  # 서머타임
                                if current_hour < 22:
                                    next_open_times.append("🇺🇸 미국장: 오늘 22:30")
                                else:
                                    next_open_times.append("🇺🇸 미국장: 현재 활성")
                            else:  # 표준시간
                                if current_hour < 23:
                                    next_open_times.append("🇺🇸 미국장: 오늘 23:30")
                                else:
                                    next_open_times.append("🇺🇸 미국장: 현재 활성")
                                    
                            if next_open_times:
                                logger.info("다음 시장 개장:")
                                for time in next_open_times:
                                    logger.info(f"  {time}")
                            
                            # 장외시간 학습 (15:30 ~ 09:00)
                            # 주식시장 종료 후부터 다음날 시작 전까지 계속 학습
                            logger.info("\n[장외시간 학습] 장 마감 - 학습 시간!")
                            logger.info(f"현재 시간: {now.strftime('%H:%M')}")
                            
                            stocks_trained = 0
                            attempts = 0  # 시도 횟수  
                            max_attempts = 20  # 평일은 더 많이 시도
                            max_stocks_per_hour = 10  # 성공 목표
                            
                            while attempts < max_attempts and stocks_trained < max_stocks_per_hour:
                                attempts += 1
                                logger.info(f"\n[Attempt {attempts}/{max_attempts}] (Success: {stocks_trained}/{max_stocks_per_hour})")
                                
                                try:
                                    # 시간대별 학습 전략
                                    if 18 <= now.hour < 21:
                                        # 저녁 황금시간: 전체 학습 시도
                                        logger.info("🌃 Prime time (18-21): Attempting full training...")
                                        training_result = await self.trainer.run_training_session()
                                        if training_result:
                                            stocks_trained = max_stocks_per_hour  # 전체 학습 성공 시 종료
                                            logger.info("✅ Full training session completed!")
                                        else:
                                            # 실패 시 단일 종목으로
                                            training_result = await self.trainer.run_single_stock_training()
                                            if training_result:
                                                stocks_trained += 1
                                    else:
                                        # 그 외 시간: 단일 종목 학습
                                        logger.info("🌙 Off-peak hours: Single stock training...")
                                        training_result = await self.trainer.run_single_stock_training()
                                        if training_result:
                                            stocks_trained += 1
                                            logger.info("✅ Stock training completed!")
                                            logger.info(f"   Stock: {training_result['stock']}")
                                            logger.info(f"   Win rate: {training_result['win_rate']:.1%}")
                                        else:
                                            # 학습 실패해도 계속 진행
                                            logger.warning("⚠️ Training failed, trying next stock...")
                                        
                                        # 성공/실패 관계없이 다음 종목으로
                                        logger.info("\n➡️ Moving to next stock immediately...")
                                        
                                        # API 호출 간격을 위한 최소 대기
                                        await asyncio.sleep(2)
                                    
                                except Exception as e:
                                    logger.error(f"Training error: {e}")
                                    break
                            
                            logger.info(f"\n📋 Training Summary:")
                            logger.info(f"   - Total attempts: {attempts}")
                            logger.info(f"   - Successful: {stocks_trained}")
                            logger.info(f"   - Failed: {attempts - stocks_trained}")
                            
                            logger.info("Waiting 1 hour...")
                            await asyncio.sleep(3600)  # 1시간 대기
                    
                    # 주말 처리
                    if now.weekday() >= 5:
                        # 주말 대기
                        logger.info("=" * 60)
                        logger.info("WEEKEND MODE - Market is closed")
                        logger.info(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
                        logger.info("Next market open: Monday 09:00")
                        
                        # 주말 활동: 포트폴리오 확인 및 학습
                        logger.info("\n[Weekend Activity] Checking portfolio status...")
                        try:
                            await self.update_portfolio_status()
                            logger.info(f"\n[Portfolio Summary]")
                            logger.info(f"Total Value: {self.total_value:,.0f} KRW")
                            logger.info(f"Cash: {self.cash_balance:,.0f} KRW")
                            logger.info(f"Holdings: {len(self.portfolio)} stocks")
                            
                            # 보유 종목 있으면 표시
                            if self.portfolio:
                                logger.info("\n[Current Holdings]")
                                for code, info in self.portfolio.items():
                                    logger.info(f"- {info['name']}: {info['quantity']}주, "
                                              f"현재가: {info['current_price']:,.0f}원")
                        except Exception as e:
                            logger.warning(f"Weekend portfolio check error: {e}")
                        
                        # 주말엔 계속 학습 (한 종목 끝나면 다음 종목)
                        logger.info("\n[Weekend Training Mode] Continuous learning enabled")
                        logger.info("Will train multiple stocks sequentially...")
                        
                        stocks_trained = 0
                        attempts = 0  # 시도 횟수
                        max_attempts = 10  # 최대 시도 횟수
                        max_stocks_per_hour = 5  # 성공 목표
                        
                        while attempts < max_attempts and stocks_trained < max_stocks_per_hour:
                            attempts += 1
                            logger.info(f"\n[Attempt {attempts}/{max_attempts}] (Success: {stocks_trained}/{max_stocks_per_hour})")
                            
                            try:
                                training_result = await self.trainer.run_single_stock_training()
                                if training_result and 'stock' in training_result:
                                    # 성공적으로 학습 완료
                                    stocks_trained += 1
                                    logger.info("✅ Training completed!")
                                    logger.info(f"   Stock: {training_result['stock']}")
                                    logger.info(f"   Win rate: {training_result['win_rate']:.1%}")
                                elif training_result and training_result.get('오류') == 'no_stocks_available':
                                    # 더 이상 시도할 종목이 없음
                                    logger.warning("⚠️ No more stocks available to train - ending session")
                                    break
                                else:
                                    # 학습 실패해도 계속 진행
                                    logger.warning("⚠️ Training failed, trying next stock...")
                                
                                # 항상 다음 종목으로 이동 (실패해도 카운트는 증가시키지 않음)
                                logger.info("\n➡️ Moving to next stock immediately...")
                                # API 호출 간격을 위한 최소 대기
                                await asyncio.sleep(2)
                            except Exception as e:
                                logger.error(f"Training error: {e}")
                                break
                        
                        logger.info(f"\n📋 Training Summary:")
                        logger.info(f"   - Total attempts: {attempts}")
                        logger.info(f"   - Successful: {stocks_trained}")
                        logger.info(f"   - Failed: {attempts - stocks_trained}")
                        self.last_training_time = datetime.now()
                        
                        # 다음 체크 시간 안내
                        next_check = now + timedelta(hours=1)
                        logger.info(f"\n[Next Check] {next_check.strftime('%H:%M:%S')}")
                        logger.info("Waiting for 1 hour...")
                        logger.info("=" * 60)
                        
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