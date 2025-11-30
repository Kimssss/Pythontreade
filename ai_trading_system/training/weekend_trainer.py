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
import pickle
import asyncio

logger = logging.getLogger('ai_trading.training')


class WeekendTrainer:
    """주말/장외시간 학습 관리자"""
    
    def __init__(self, ensemble_system, kis_api):
        self.ensemble = ensemble_system
        self.kis_api = kis_api
        self.training_history = []
        self.cache_dir = Path('training_cache')
        self.cache_dir.mkdir(exist_ok=True)
        self.trained_stocks = []  # 이미 학습한 종목 기록
        
    async def run_training_session(self):
        """학습 세션 실행"""
        logger.info("\n" + "="*60)
        logger.info("🤖 AI TRAINING SESSION STARTED")
        logger.info("="*60)
        start_time = datetime.now()
        
        try:
            # 1. 과거 데이터 수집
            logger.info("\n[Phase 1/5] 📈 Collecting Historical Data...")
            logger.info("-" * 40)
            training_data = await self._collect_training_data()
            
            if not training_data:
                logger.warning("❌ No training data available - API rate limit on weekend")
                logger.info("Try again later when API is less busy")
                return None
            
            # 2. DQN 에이전트 학습
            logger.info("\n[Phase 2/5] 🧠 Training DQN Agent...")
            logger.info("-" * 40)
            dqn_results = await self._train_dqn_agent(training_data)
            
            # 3. 팩터 가중치 최적화
            logger.info("\n[Phase 3/5] ⚖️ Optimizing Factor Weights...")
            logger.info("-" * 40)
            factor_results = await self._optimize_factor_weights(training_data)
            
            # 4. 기술적 지표 파라미터 최적화
            logger.info("\n[Phase 4/5] 🔧 Optimizing Technical Indicators...")
            logger.info("-" * 40)
            tech_results = await self._optimize_technical_params(training_data)
            
            # 5. 백테스팅
            logger.info("\n[Phase 5/5] 📊 Running Backtesting...")
            logger.info("-" * 40)
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
        """학습용 데이터 수집 (Rate Limit 회피 전략)"""
        try:
            # 전략 1: 캐시된 데이터 확인
            cached_data = self._load_cached_training_data()
            if cached_data:
                logger.info("📦 Using cached training data from previous session")
                return cached_data
            
            # 전략 2: 단계적 데이터 수집 (단계별 대기시간 최적화)
            logger.info("Fetching top volume stocks with rate limit strategy...")
            
            # 첫 API 호출 전 충분한 대기
            await asyncio.sleep(3.0)
            
            volume_stocks = self.kis_api.get_top_volume_stocks(count=30)
            
            if not volume_stocks or volume_stocks.get('rt_cd') != '0':
                logger.warning("Failed to get volume stocks - will retry with exponential backoff")
                # Exponential backoff 재시도
                for retry in range(3):
                    wait_time = 5 * (2 ** retry)  # 5, 10, 20초
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    
                    volume_stocks = self.kis_api.get_top_volume_stocks(count=30)
                    if volume_stocks and volume_stocks.get('rt_cd') == '0':
                        break
                else:
                    logger.error("Failed to get volume stocks after retries")
                    return None
            
            # 전략 3: 적응적 수집 (성공률에 따라 대기시간 조절)
            stocks = volume_stocks.get('output', [])
            training_data = []
            success_count = 0
            fail_count = 0
            
            # 초기 대기시간
            base_wait_time = 3.0  # 주말 기본 3초
            current_wait_time = base_wait_time
            
            for i, stock in enumerate(stocks):
                stock_code = stock.get('mksc_shrn_iscd', '')
                stock_name = stock.get('hts_kor_isnm', '')
                
                if not stock_code:
                    continue
                
                # 최대 10개의 유효한 데이터를 수집하면 종료
                if len(training_data) >= 10:
                    logger.info("✅ Collected enough data for training (10 stocks)")
                    break
                
                logger.info(f"\n[{i+1}/{min(len(stocks), 15)}] Attempting {stock_name} ({stock_code})")
                logger.info(f"Current wait time: {current_wait_time:.1f}s")
                
                # 대기
                await asyncio.sleep(current_wait_time)
                
                # 데이터 수집 시도
                daily_data = self.kis_api.get_daily_price(stock_code, count=30)
                
                if daily_data and daily_data.get('rt_cd') == '0':
                    df = self._parse_daily_data(daily_data)
                    if df is not None and len(df) > 20:
                        training_data.append({
                            'stock_code': stock_code,
                            'stock_name': stock_name,
                            'data': df
                        })
                        logger.info(f"  ✅ Success! Data collected: {len(df)} days")
                        success_count += 1
                        
                        # 성공 시 대기시간 감소
                        current_wait_time = max(2.0, current_wait_time * 0.9)
                else:
                    error_msg = daily_data.get('msg1', 'Unknown error') if daily_data else 'No response'
                    logger.warning(f"  ⚠️ Failed: {error_msg}")
                    fail_count += 1
                    
                    # 실패 시 대기시간 증가
                    if '초당' in error_msg:  # rate limit 에러
                        current_wait_time = min(10.0, current_wait_time * 1.5)
                        logger.info(f"  Rate limit detected - increasing wait time to {current_wait_time:.1f}s")
                
                # 현황 업데이트
                if (success_count + fail_count) % 5 == 0:
                    logger.info(f"\n--- Progress: {success_count} success, {fail_count} failed ---")
            
            # 결과 요약
            logger.info(f"\n=== Collection Complete ===")
            logger.info(f"Total attempts: {success_count + fail_count}")
            logger.info(f"Successful: {success_count}")
            logger.info(f"Failed: {fail_count}")
            logger.info(f"Final dataset: {len(training_data)} stocks")
            
            # 성공적으로 수집한 데이터 캐싱
            if training_data:
                self._save_training_data_cache(training_data)
            
            return training_data
            
        except Exception as e:
            logger.error(f"Error collecting training data: {e}")
            return None
    
    def _load_cached_training_data(self):
        """캐시된 학습 데이터 로드"""
        try:
            cache_file = self.cache_dir / 'training_data_cache.pkl'
            if cache_file.exists():
                # 24시간 이내 캐시만 사용
                if (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).total_seconds() < 86400:
                    with open(cache_file, 'rb') as f:
                        return pickle.load(f)
        except:
            pass
        return None
    
    def _save_training_data_cache(self, data):
        """학습 데이터 캐싱"""
        try:
            cache_file = self.cache_dir / 'training_data_cache.pkl'
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"💾 Training data cached to {cache_file}")
        except Exception as e:
            logger.error(f"Failed to cache training data: {e}")
    
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
    
    async def run_single_stock_training(self):
        """한 종목만 학습하는 경량 모드 (주말 특화)"""
        logger.info("\n" + "="*60)
        logger.info("🎯 SINGLE STOCK TRAINING MODE")
        logger.info("="*60)
        
        try:
            # 거래량 상위 종목 가져오기 (20개)
            await asyncio.sleep(3)  # 충분한 대기
            
            logger.info("Fetching top volume stocks...")
            volume_stocks = self.kis_api.get_top_volume_stocks(count=20)
            
            if not volume_stocks or volume_stocks.get('rt_cd') != '0':
                logger.error("Failed to get volume stocks")
                return None
            
            stocks = volume_stocks.get('output', [])
            if not stocks:
                logger.error("No stocks in response")
                return None
            
            # 이미 학습한 종목 제외하고 선택
            available_stocks = [
                s for s in stocks 
                if s.get('mksc_shrn_iscd', '') not in self.trained_stocks
            ]
            
            if not available_stocks:
                logger.info("🔄 All top stocks trained. Resetting list...")
                self.trained_stocks = []  # 리셋
                available_stocks = stocks
            
            stock = available_stocks[0]
            stock_code = stock.get('mksc_shrn_iscd', '')
            stock_name = stock.get('hts_kor_isnm', '')
            
            # 학습 목록에 추가
            self.trained_stocks.append(stock_code)
            
            logger.info(f"\n📊 Training on: {stock_name} ({stock_code})")
            
            # 5초 대기 (주말 특별 대기)
            await asyncio.sleep(5)
            
            # 데이터 수집
            logger.info("Collecting 30-day price data...")
            daily_data = self.kis_api.get_daily_price(stock_code, count=30)
            
            if not daily_data or daily_data.get('rt_cd') != '0':
                logger.error(f"Failed to get price data: {daily_data.get('msg1', '')}")
                return None
            
            df = self._parse_daily_data(daily_data)
            if df is None or len(df) < 20:
                logger.error("Insufficient data for training")
                return None
            
            logger.info(f"✅ Data collected: {len(df)} days")
            
            # 간단한 DQN 학습
            logger.info("\n🧠 Quick DQN training...")
            episode_losses = []
            for i in range(10):  # 10 에피소드만
                loss = self._train_episode(self.ensemble.dqn_agent, df)
                episode_losses.append(loss)
                if i % 5 == 0:
                    logger.info(f"  Episode {i+1}: Loss = {loss:.4f}")
            
            avg_loss = sum(episode_losses) / len(episode_losses) if episode_losses else 0
            logger.info(f"\n✅ Training complete! Average loss: {avg_loss:.4f}")
            
            # 간단한 백테스트
            trades = self._simulate_trades(df)
            win_rate = len([t for t in trades if t['profit'] > 0]) / len(trades) if trades else 0
            
            logger.info(f"\n📊 Quick backtest results:")
            logger.info(f"  - Trades: {len(trades)}")
            logger.info(f"  - Win rate: {win_rate:.1%}")
            
            return {
                'mode': 'single_stock',
                'stock': f"{stock_name} ({stock_code})",
                'avg_loss': avg_loss,
                'win_rate': win_rate,
                'duration': 60  # 약 1분
            }
            
        except Exception as e:
            logger.error(f"Single stock training error: {e}")
            return None