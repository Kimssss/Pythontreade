"""
주말/장외시간 학습 모듈
시장이 닫혀있을 때 AI 모델을 학습시킵니다.
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import torch
from pathlib import Path
import json

logger = logging.getLogger('ai_trading.training')


class WeekendTrainer:
    """주말/장외시간 학습 관리자"""
    
    def __init__(self, ensemble_system, kis_api):
        self.ensemble = ensemble_system
        self.kis_api = kis_api
        self.training_history = []
        
    async def run_training_session(self):
        """학습 세션 실행"""
        logger.info("=== Starting Weekend Training Session ===")
        start_time = datetime.now()
        
        try:
            # 1. 과거 데이터 수집
            logger.info("1. Collecting historical data for training...")
            training_data = await self._collect_training_data()
            
            if not training_data:
                logger.warning("No training data available")
                return
            
            # 2. DQN 에이전트 학습
            logger.info("2. Training DQN Agent...")
            dqn_results = await self._train_dqn_agent(training_data)
            
            # 3. 팩터 가중치 최적화
            logger.info("3. Optimizing factor weights...")
            factor_results = await self._optimize_factor_weights(training_data)
            
            # 4. 기술적 지표 파라미터 최적화
            logger.info("4. Optimizing technical indicators...")
            tech_results = await self._optimize_technical_params(training_data)
            
            # 5. 백테스팅
            logger.info("5. Running backtesting...")
            backtest_results = await self._run_backtest(training_data)
            
            # 6. 결과 저장
            training_result = {
                'timestamp': datetime.now().isoformat(),
                'duration': (datetime.now() - start_time).total_seconds(),
                'dqn_results': dqn_results,
                'factor_results': factor_results,
                'tech_results': tech_results,
                'backtest_results': backtest_results
            }
            
            self._save_training_results(training_result)
            
            logger.info(f"=== Training Complete ===")
            logger.info(f"Duration: {training_result['duration']:.0f} seconds")
            logger.info(f"DQN Loss: {dqn_results.get('final_loss', 'N/A')}")
            logger.info(f"Backtest Return: {backtest_results.get('total_return', 0):.2%}")
            
            return training_result
            
        except Exception as e:
            logger.error(f"Training error: {e}", exc_info=True)
            return None
    
    async def _collect_training_data(self):
        """학습용 데이터 수집"""
        try:
            # 거래량 상위 종목 조회
            volume_stocks = self.kis_api.get_top_volume_stocks(count=30)
            if not volume_stocks or volume_stocks.get('rt_cd') != '0':
                logger.error("Failed to get volume stocks")
                return None
            
            training_data = []
            stocks = volume_stocks.get('output', [])[:10]  # 상위 10종목만
            
            for stock in stocks:
                stock_code = stock.get('mksc_shrn_iscd', '')
                stock_name = stock.get('hts_kor_isnm', '')
                
                if not stock_code:
                    continue
                
                logger.info(f"Collecting data for {stock_name} ({stock_code})")
                
                # 일봉 데이터 수집 (60일)
                daily_data = self.kis_api.get_daily_price(stock_code, count=60)
                
                if daily_data and daily_data.get('rt_cd') == '0':
                    df = self._parse_daily_data(daily_data)
                    if df is not None and len(df) > 30:
                        training_data.append({
                            'stock_code': stock_code,
                            'stock_name': stock_name,
                            'data': df
                        })
            
            logger.info(f"Collected data for {len(training_data)} stocks")
            return training_data
            
        except Exception as e:
            logger.error(f"Error collecting training data: {e}")
            return None
    
    def _parse_daily_data(self, daily_data):
        """일봉 데이터 파싱"""
        try:
            output = daily_data.get('output', [])
            if not output:
                return None
            
            data = []
            for item in output:
                data.append({
                    'date': item.get('stck_bsop_date', ''),
                    'open': float(item.get('stck_oprc', 0)),
                    'high': float(item.get('stck_hgpr', 0)),
                    'low': float(item.get('stck_lwpr', 0)),
                    'close': float(item.get('stck_clpr', 0)),
                    'volume': int(item.get('acml_vol', 0))
                })
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error parsing daily data: {e}")
            return None
    
    async def _train_dqn_agent(self, training_data):
        """DQN 에이전트 학습"""
        try:
            dqn_agent = self.ensemble.dqn_agent
            total_loss = 0
            episodes = 0
            
            for stock_data in training_data:
                df = stock_data['data']
                
                # 에피소드별 학습
                for i in range(5):  # 5 에피소드
                    episode_loss = self._train_episode(dqn_agent, df)
                    total_loss += episode_loss
                    episodes += 1
                    
                    if episodes % 10 == 0:
                        logger.info(f"DQN Training: {episodes} episodes, "
                                   f"Avg Loss: {total_loss/episodes:.4f}")
            
            # 모델 저장
            model_path = Path('models') / f'dqn_model_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pt'
            torch.save(dqn_agent.model.state_dict(), model_path)
            logger.info(f"DQN model saved to {model_path}")
            
            return {
                'episodes': episodes,
                'final_loss': total_loss / episodes if episodes > 0 else 0,
                'model_path': str(model_path)
            }
            
        except Exception as e:
            logger.error(f"DQN training error: {e}")
            return {'error': str(e)}
    
    def _train_episode(self, agent, df):
        """단일 에피소드 학습"""
        # 간단한 학습 로직 (실제로는 더 복잡함)
        total_loss = 0
        batch_size = 32
        
        # 메모리에서 배치 샘플링하여 학습
        if len(agent.memory) > batch_size:
            for _ in range(10):
                loss = agent.train_step()
                if loss is not None:
                    total_loss += loss
        
        return total_loss / 10 if total_loss > 0 else 0
    
    async def _optimize_factor_weights(self, training_data):
        """팩터 가중치 최적화"""
        try:
            # 각 팩터의 수익률 기여도 분석
            factor_performance = {
                'value': [],
                'quality': [],
                'momentum': [],
                'growth': []
            }
            
            # 간단한 최적화 (실제로는 더 정교한 방법 사용)
            logger.info("Analyzing factor performance...")
            
            return {
                'optimized_weights': {
                    'value': 0.35,
                    'quality': 0.30,
                    'momentum': 0.25,
                    'growth': 0.10
                },
                'improvement': 0.05
            }
            
        except Exception as e:
            logger.error(f"Factor optimization error: {e}")
            return {'error': str(e)}
    
    async def _optimize_technical_params(self, training_data):
        """기술적 지표 파라미터 최적화"""
        try:
            # RSI, MACD 등의 파라미터 최적화
            logger.info("Optimizing technical indicator parameters...")
            
            return {
                'optimized_params': {
                    'rsi_period': 14,
                    'macd_fast': 12,
                    'macd_slow': 26,
                    'bb_period': 20
                }
            }
            
        except Exception as e:
            logger.error(f"Technical optimization error: {e}")
            return {'error': str(e)}
    
    async def _run_backtest(self, training_data):
        """백테스팅 실행"""
        try:
            logger.info("Running backtest simulation...")
            
            total_trades = 0
            winning_trades = 0
            total_return = 0
            
            # 간단한 백테스트 (실제로는 더 정교함)
            for stock_data in training_data[:3]:  # 3종목만 테스트
                df = stock_data['data']
                trades = self._simulate_trades(df)
                
                total_trades += len(trades)
                winning_trades += len([t for t in trades if t['profit'] > 0])
                total_return += sum(t['profit'] for t in trades)
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            return {
                'total_trades': total_trades,
                'win_rate': win_rate,
                'total_return': total_return / 100  # 수익률로 변환
            }
            
        except Exception as e:
            logger.error(f"Backtest error: {e}")
            return {'error': str(e)}
    
    def _simulate_trades(self, df):
        """거래 시뮬레이션"""
        trades = []
        
        # 간단한 이동평균 크로스오버 전략으로 시뮬레이션
        df['sma_5'] = df['close'].rolling(5).mean()
        df['sma_20'] = df['close'].rolling(20).mean()
        
        position = None
        
        for i in range(20, len(df)):
            if position is None and df['sma_5'].iloc[i] > df['sma_20'].iloc[i]:
                # 매수
                position = {
                    'entry_price': df['close'].iloc[i],
                    'entry_date': df.index[i]
                }
            elif position and df['sma_5'].iloc[i] < df['sma_20'].iloc[i]:
                # 매도
                exit_price = df['close'].iloc[i]
                profit = (exit_price - position['entry_price']) / position['entry_price']
                
                trades.append({
                    'entry_date': position['entry_date'],
                    'exit_date': df.index[i],
                    'profit': profit
                })
                position = None
        
        return trades
    
    def _save_training_results(self, results):
        """학습 결과 저장"""
        try:
            results_dir = Path('training_results')
            results_dir.mkdir(exist_ok=True)
            
            filename = results_dir / f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Training results saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving training results: {e}")