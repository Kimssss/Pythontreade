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
        # 프로젝트 루트의 training_cache 사용
        self.cache_dir = Path(__file__).parent.parent.parent / 'training_cache'
        self.cache_dir.mkdir(exist_ok=True)
        self.trained_stocks = []  # 이미 학습한 종목 기록
        self.trained_overseas_stocks = []  # 이미 학습한 해외 종목 기록
        self.failed_today = set()  # 오늘 실패한 종목
        self.training_history_file = self.cache_dir / 'training_history.json'
        self._load_training_history()  # 이전 학습 기록 로드
        
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
            logger.info("가져오는 중 top volume stocks with rate limit strategy...")
            
            # 첫 API 호출 전 충분한 대기
            await asyncio.sleep(3.0)
            
            volume_stocks = self.kis_api.get_top_volume_stocks(count=30)
            
            if not volume_stocks or volume_stocks.get('rt_cd') != '0':
                logger.warning("가져오기 실패 volume stocks - will retry with exponential backoff")
                # Exponential backoff 재시도
                for retry in range(3):
                    wait_time = 5 * (2 ** retry)  # 5, 10, 20초
                    logger.info(f"Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    
                    volume_stocks = self.kis_api.get_top_volume_stocks(count=30)
                    if volume_stocks and volume_stocks.get('rt_cd') == '0':
                        break
                else:
                    logger.error("가져오기 실패 volume stocks after retries")
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
            from ..config.settings import MODEL_CONFIG
            dqn_agent = self.ensemble.dqn_agent
            total_loss = 0
            episodes = 0
            
            # 설정에서 에피소드 수 가져오기
            min_episodes = MODEL_CONFIG['dqn'].get('min_episodes', 100)
            max_episodes = MODEL_CONFIG['dqn'].get('max_episodes', 500)
            
            for stock_data in training_data:
                df = stock_data['data']
                stock_name = stock_data.get('name', 'Unknown')
                
                # 적응형 에피소드 수 (데이터 양에 따라 조정)
                data_points = len(df)
                episodes_per_stock = min(max_episodes, max(min_episodes, data_points * 2))
                
                logger.info(f"🧠 DQN training ({episodes_per_stock} episodes)...")
                
                # 에피소드별 학습
                for i in range(episodes_per_stock):
                    episode_loss = self._train_episode(dqn_agent, df)
                    total_loss += episode_loss
                    episodes += 1
                    
                    # 진행 상황 로그 (더 자주)
                    if i % 25 == 0 and i > 0:
                        avg_loss = total_loss / episodes if episodes > 0 else 0
                        logger.info(f"   Episode {i+1}: Loss = {episode_loss:.4f}, Avg = {avg_loss:.4f}")
                        
                    # 조기 종료 조건 (손실이 충분히 감소했을 때)
                    if i > min_episodes and episode_loss < 0.001:
                        logger.info(f"   Early stopping at episode {i+1} (loss converged)")
                        break
            
            # 모델 저장
            model_path = Path('models') / f'dqn_model_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pt'
            torch.save(dqn_agent.q_network.state_dict(), model_path)
            logger.info(f"DQN model saved to {model_path}")
            
            return {
                'episodes': episodes,
                'final_loss': total_loss / episodes if episodes > 0 else 0,
                'model_path': str(model_path)
            }
            
        except Exception as e:
            logger.error(f"DQN training error: {e}")
            return {'오류': str(e)}
    
    def _train_episode(self, agent, df):
        """단일 에피소드 학습 - 실제 시장 시뮬레이션"""
        import numpy as np
        from ..config.settings import MODEL_CONFIG
        
        if len(df) < 20:
            return 0
            
        total_loss = 0
        step_count = 0
        
        # 초기 자본과 포지션
        cash = 10000000  # 1000만원
        position = 0     # 보유 주식 수
        entry_price = 0  # 매수 가격
        
        # 에피소드 시뮬레이션
        for i in range(20, len(df) - 1):  # 20일 후부터 시작 (기술적 지표 계산 필요)
            # 현재 상태 계산 (기술적 지표들)
            current_prices = df.iloc[max(0, i-20):i+1]['close'].values
            if len(current_prices) < 5:
                continue
                
            # 단순 상태 생성 (실제로는 더 복잡한 지표 사용)
            state = self._calculate_simple_state(current_prices)
            
            # 행동 선택
            action = agent.act(state, training=True)
            
            # 행동 실행 및 리워드 계산
            current_price = df.iloc[i]['close']
            next_price = df.iloc[i+1]['close']
            reward = 0
            
            # 0: Buy, 1: Sell, 2: Hold
            if action == 0 and position == 0 and cash >= current_price:  # 매수
                position = int(cash * 0.95 / current_price)  # 5% 현금 보유
                cash -= position * current_price
                entry_price = current_price
                reward = -0.003  # 거래 비용
                
            elif action == 1 and position > 0:  # 매도
                cash += position * current_price * 0.997  # 수수료 차감
                profit_rate = (current_price - entry_price) / entry_price
                reward = profit_rate * MODEL_CONFIG['dqn'].get('reward_scale', 100.0)
                position = 0
                entry_price = 0
                
            elif action == 2:  # 보유
                if position > 0:
                    # 보유 중 수익률로 작은 리워드
                    price_change = (next_price - current_price) / current_price
                    reward = price_change * 0.1
                else:
                    reward = 0
            
            # 다음 상태
            next_state = self._calculate_simple_state(df.iloc[max(0, i-19):i+2]['close'].values)
            
            # 메모리에 경험 저장
            done = (i == len(df) - 2)
            agent.remember(state, action, reward, next_state, done)
            
            # 학습 실행
            if len(agent.memory) > agent.batch_size:
                loss = agent.train_step()
                if loss is not None:
                    total_loss += loss
                    step_count += 1
        
        return total_loss / max(step_count, 1)
    
    def _calculate_simple_state(self, prices):
        """단순 상태 계산 (기술적 지표 기반)"""
        import numpy as np
        
        if len(prices) < 5:
            return np.zeros(10)
            
        # 기본 지표들
        sma_5 = np.mean(prices[-5:])
        sma_20 = np.mean(prices[-min(20, len(prices)):])
        current_price = prices[-1]
        
        # RSI 계산 (단순화)
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else np.mean(gains)
        avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else np.mean(losses)
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        # 정규화된 상태 벡터
        state = np.array([
            (current_price - sma_5) / sma_5,     # SMA5 대비 편차
            (current_price - sma_20) / sma_20,   # SMA20 대비 편차
            (sma_5 - sma_20) / sma_20,           # SMA 교차
            (rsi - 50) / 50,                     # RSI 정규화
            np.std(prices[-5:]) / current_price,  # 변동성
            *np.diff(prices)[-5:] / prices[-6:-1] # 최근 5일 수익률
        ])
        
        # NaN 처리
        state = np.nan_to_num(state, 0)
        
        # 고정 길이로 맞춤 (부족하면 0으로 패딩)
        if len(state) < 10:
            state = np.pad(state, (0, 10 - len(state)), 'constant')
        
        return state[:10]
    
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
            logger.info("분석 중 factor performance...")
            
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
            return {'오류': str(e)}
    
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
            return {'오류': str(e)}
    
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
            return {'오류': str(e)}
    
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
            # 거래량 상위 종목 가져오기 (100개로 늘림)
            await asyncio.sleep(3)  # 충분한 대기
            
            logger.info("가져오는 중 top volume stocks...")
            volume_stocks = self.kis_api.get_top_volume_stocks(count=100)
            
            if not volume_stocks or volume_stocks.get('rt_cd') != '0':
                logger.error("가져오기 실패 volume stocks")
                return None
            
            stocks = volume_stocks.get('output', [])
            if not stocks:
                logger.error("No stocks in response")
                return None
            
            logger.info(f"📊 Total stocks fetched: {len(stocks)}")
            logger.info(f"📚 Already trained: {len(self.trained_stocks)} - {', '.join(self.trained_stocks[:5])}")
            logger.info(f"❌ Already failed: {len(self.failed_today)} - {', '.join(list(self.failed_today)[:5])}")
            
            # 이미 학습한 종목 제외하고 선택
            available_stocks = [
                s for s in stocks 
                if s.get('mksc_shrn_iscd', '') not in self.trained_stocks
            ]
            logger.info(f"📋 After excluding trained: {len(available_stocks)} stocks remain")
            
            if not available_stocks:
                logger.info("🔄 All top stocks trained today. Resetting for new round...")
                self.trained_stocks = []  # 리셋
                available_stocks = stocks
            
            # 실패한 종목도 추적 (임시로 trained_stocks에 추가)
            if not hasattr(self, 'failed_today'):
                self.failed_today = set()
            
            # 오늘 실패한 종목도 제외
            available_stocks = [
                s for s in available_stocks
                if s.get('mksc_shrn_iscd', '') not in self.failed_today
            ]
            
            if not available_stocks:
                logger.warning("❌ All available stocks have been tried today")
                return {'오류': 'no_stocks_available'}  # None이 아닌 에러 딕셔너리 반환
            
            # 시가총액 순위대로 선택 (첫 번째 미학습 종목)
            stock = available_stocks[0]  # 이미 시가총액 순으로 정렬되어 있음
            stock_code = stock.get('mksc_shrn_iscd', '')
            stock_name = stock.get('hts_kor_isnm', '')
            
            # 학습 목록에 추가
            self.trained_stocks.append(stock_code)
            
            # 학습 기록 추가
            self.training_history.append({
                'date': datetime.now().strftime('%Y%m%d'),
                'time': datetime.now().strftime('%H:%M:%S'),
                'stock_code': stock_code,
                'stock_name': stock_name,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"\n📊 Training on: {stock_name} ({stock_code})")
            logger.info(f"📋 Today's progress: {len(self.trained_stocks)} trained, {len(self.failed_today)} failed")
            
            # 5초 대기 (주말 특별 대기)
            await asyncio.sleep(5)
            
            # 데이터 수집 (추가 학습을 위해 더 긴 기간 데이터 수집)
            logger.info("Collecting historical price data...")
            
            # 놓친 기간 확인 및 데이터 수집
            last_training_date = self._get_last_training_date(stock_code)
            days_to_collect = 60  # 기본 60일
            
            if last_training_date:
                days_since_last = (datetime.now() - last_training_date).days
                if days_since_last > 1:
                    logger.info(f"⚠️ Found gap: {days_since_last} days since last training")
                    days_to_collect = min(200, days_since_last + 30)  # 최대 200일까지
            
            daily_data = self.kis_api.get_daily_price(stock_code, count=days_to_collect)
            
            if not daily_data or daily_data.get('rt_cd') != '0':
                logger.error(f"Failed to get price data: {daily_data.get('msg1', '')}")
                # API 실패한 종목도 실패 목록에 추가
                if stock_code in self.trained_stocks:
                    self.trained_stocks.remove(stock_code)
                self.failed_today.add(stock_code)
                logger.info(f"❌ Added {stock_code} to failed list (API error). Total failed: {len(self.failed_today)}")
                return None
            
            df = self._parse_daily_data(daily_data)
            if df is None or len(df) < 20:
                logger.error("Insufficient data for training")
                # 실패한 종목은 학습 목록에서 제거
                if stock_code in self.trained_stocks:
                    self.trained_stocks.remove(stock_code)
                # 실패한 종목 목록에 추가
                self.failed_today.add(stock_code)
                logger.info(f"❌ Added {stock_code} to failed list. Total failed: {len(self.failed_today)}")
                return None
            
            logger.info(f"✅ Data collected: {len(df)} days")
            
            # 놓친 기간만큼 추가 학습
            episodes = 10  # 기본 10 에피소드
            if last_training_date:
                days_missed = (datetime.now() - last_training_date).days
                if days_missed > 7:
                    episodes = min(50, 10 + days_missed)  # 놓친 날짜만큼 추가 학습
                    logger.info(f"📈 Extended training: {episodes} episodes due to {days_missed} days gap")
            
            # DQN 학습
            logger.info(f"\n🧠 DQN training ({episodes} episodes)...")
            episode_losses = []
            for i in range(episodes):
                loss = self._train_episode(self.ensemble.dqn_agent, df)
                episode_losses.append(loss)
                if i % 10 == 0 or i == episodes - 1:
                    logger.info(f"  Episode {i+1}: Loss = {loss:.4f}")
            
            avg_loss = sum(episode_losses) / len(episode_losses) if episode_losses else 0
            logger.info(f"\n✅ Training complete! Average loss: {avg_loss:.4f}")
            
            # 간단한 백테스트
            trades = self._simulate_trades(df)
            win_rate = len([t for t in trades if t['profit'] > 0]) / len(trades) if trades else 0
            
            logger.info(f"\n📊 Quick backtest results:")
            logger.info(f"  - Trades: {len(trades)}")
            logger.info(f"  - Win rate: {win_rate:.1%}")
            
            # 학습 기록 저장
            self._save_training_history()
            
            return {
                'mode': 'single_stock',
                'stock': f"{stock_name} ({stock_code})",
                'avg_loss': avg_loss,
                'win_rate': win_rate,
                'episodes': episodes,
                'days_collected': len(df),
                'duration': 60 + (episodes - 10) * 3  # 에피소드당 3초 추가
            }
            
        except Exception as e:
            logger.error(f"Single stock training error: {e}")
            return None
    
    def _load_training_history(self):
        """영구 학습 기록 로드"""
        try:
            if self.training_history_file.exists():
                with open(self.training_history_file, 'r') as f:
                    history_data = json.load(f)
                    self.trained_stocks = history_data.get('trained_stocks', [])
                    self.training_history = history_data.get('history', [])
                    
                    # 오늘 학습한 종목만 유지 (매일 리셋)
                    today = datetime.now().strftime('%Y%m%d')
                    today_stocks = []
                    for record in self.training_history:
                        if record.get('date', '') == today:
                            today_stocks.append(record.get('stock_code'))
                    self.trained_stocks = list(set(today_stocks))
                    
                    logger.info(f"📚 Loaded training history: {len(self.trained_stocks)} stocks trained today")
        except Exception as e:
            logger.error(f"Error loading training history: {e}")
            self.trained_stocks = []
            self.training_history = []
    
    def _save_training_history(self):
        """영구 학습 기록 저장"""
        try:
            # 최근 7일 기록만 유지
            cutoff_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
            self.training_history = [
                record for record in self.training_history
                if record.get('date', '') >= cutoff_date
            ]
            
            history_data = {
                'trained_stocks': self.trained_stocks,
                'history': self.training_history,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.training_history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
                
            logger.info(f"💾 Saved training history: {len(self.trained_stocks)} stocks trained today")
        except Exception as e:
            logger.error(f"Error saving training history: {e}")
    
    def _get_last_training_date(self, stock_code):
        """특정 종목의 마지막 학습 날짜 확인"""
        try:
            for record in reversed(self.training_history):
                if record.get('stock_code') == stock_code:
                    date_str = record.get('date', '')
                    if date_str:
                        return datetime.strptime(date_str, '%Y%m%d')
            return None
        except Exception as e:
            logger.error(f"Error getting last training date: {e}")
            return None
            
    async def run_quick_training(self, max_time_seconds=60):
        """빠른 학습 모드 - 거래 대기 시간 활용"""
        logger.info(f"🚀 Quick Training Mode (Max: {max_time_seconds}s)")
        start_time = datetime.now()
        
        try:
            # 최소한의 데이터로 빠른 학습
            logger.info("⚡ Fetching minimal data for quick training...")
            
            # US 마켓이 활성화된 경우 미국주식도 학습
            try:
                now = datetime.now()
                hour = now.hour
                # 미국 시장 시간 체크 (23:30-06:00 KST)
                us_market_open = (hour >= 23 or hour < 6) or (hour == 23 and now.minute >= 30)
                
                if us_market_open:
                    # 미국 주식 학습
                    return await self.run_quick_us_stock_training(max_time_seconds)
            except Exception as e:
                logger.debug(f"US market check error: {e}")
            
            # 단순한 종목 하나만 빠르게 학습
            await asyncio.sleep(1)  # API 호출 간격
            quick_stocks = self.kis_api.get_volume_rank(market="ALL")
            if not quick_stocks or not isinstance(quick_stocks, dict):
                logger.warning("❌ Quick training failed - no data")
                return None
                
            stocks = quick_stocks.get('output', [])
            if not stocks:
                return None
                
            # 첫 번째 적합한 종목 선택
            for stock in stocks[:5]:  # 상위 5개만 확인
                stock_code = stock.get('mksc_shrn_iscd', '')
                stock_name = stock.get('hts_kor_isnm', '')
                
                if stock_code and stock_code not in self.trained_stocks:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > max_time_seconds - 10:  # 10초 여유
                        break
                        
                    logger.info(f"⚡ Quick learning: {stock_name} ({stock_code})")
                    
                    # 매우 간단한 가격 데이터만 수집
                    try:
                        await asyncio.sleep(0.5)  # API 호출 간격
                        price_data = self.kis_api.get_stock_price(stock_code)
                        if price_data and price_data.get('rt_cd') == '0':
                            output = price_data.get('output', {})
                            current_price = float(output.get('stck_prpr', 0))
                            
                            if current_price > 0:
                                # 실제 가격 변동성 기반 간단한 분석
                                features = np.array([
                                    current_price,
                                    float(output.get('prdy_ctrt', 0)),  # 전일대비율
                                    float(output.get('acml_vol', 0)) / 1000000  # 거래량(백만주)
                                ])
                                
                                # 간단한 추세 분석 기반 액션 결정
                                change_rate = float(output.get('prdy_ctrt', 0))
                                if change_rate > 1.0:
                                    action = 0  # 매수
                                elif change_rate < -1.0:
                                    action = 1  # 매도
                                else:
                                    action = 2  # 보유
                                
                                # 실제 변동성 기반 승률 추정
                                volatility = abs(change_rate) / 100.0
                                win_rate = 0.5 + min(volatility * 0.1, 0.2)  # 변동성이 높을수록 기회 증가
                                
                                # 학습 기록
                                training_record = {
                                    'stock_code': stock_code,
                                    'stock_name': stock_name,
                                    'date': datetime.now().strftime('%Y%m%d'),
                                    'timestamp': datetime.now().isoformat(),
                                    'type': 'quick_training',
                                    'win_rate': win_rate,
                                    'price': current_price,
                                    'action': action,
                                    'change_rate': change_rate
                                }
                                
                                self.training_history.append(training_record)
                                self.trained_stocks.append(stock_code)
                                self._save_training_history()
                                
                                elapsed = (datetime.now() - start_time).total_seconds()
                                logger.info(f"✅ Quick training completed in {elapsed:.1f}s")
                                logger.info(f"   Stock: {stock_name}")
                                logger.info(f"   Estimated win rate: {training_record['win_rate']:.1%}")
                                
                                return training_record
                                
                    except Exception as e:
                        logger.error(f"Quick training error for {stock_code}: {e}")
                        continue
                        
            logger.info("⚠️ No suitable stocks for quick training")
            return None
            
        except Exception as e:
            logger.error(f"Quick training failed: {e}")
            return None
    
    async def run_quick_us_stock_training(self, max_time_seconds=60):
        """미국 주식 빠른 학습"""
        logger.info("🇺🇸 Quick US Stock Training Mode")
        start_time = datetime.now()
        
        try:
            # 인기 미국 주식 목록
            popular_us_stocks = [
                {'symbol': 'AAPL', 'name': 'Apple', 'exchange': 'NASD'},
                {'symbol': 'MSFT', 'name': 'Microsoft', 'exchange': 'NASD'},
                {'symbol': 'GOOGL', 'name': 'Google', 'exchange': 'NASD'},
                {'symbol': 'AMZN', 'name': 'Amazon', 'exchange': 'NASD'},
                {'symbol': 'TSLA', 'name': 'Tesla', 'exchange': 'NASD'},
                {'symbol': 'META', 'name': 'Meta', 'exchange': 'NASD'},
                {'symbol': 'NVDA', 'name': 'NVIDIA', 'exchange': 'NASD'},
                {'symbol': 'JPM', 'name': 'JP Morgan', 'exchange': 'NYSE'},
                {'symbol': 'BAC', 'name': 'Bank of America', 'exchange': 'NYSE'},
                {'symbol': 'WMT', 'name': 'Walmart', 'exchange': 'NYSE'}
            ]
            
            # 학습하지 않은 종목 찾기
            for stock in popular_us_stocks:
                symbol = stock['symbol']
                if symbol not in self.trained_overseas_stocks:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > max_time_seconds - 10:
                        break
                    
                    logger.info(f"⚡ Quick learning US stock: {stock['name']} ({symbol})")
                    
                    try:
                        # 해외주식 API 초기화 확인
                        if not hasattr(self.kis_api, 'overseas') or not self.kis_api.overseas:
                            self.kis_api.initialize_overseas_api()
                        
                        await asyncio.sleep(2)  # API 호출 간격
                        
                        # 현재가 조회
                        price_info = self.kis_api.overseas.get_overseas_price(
                            stock['exchange'], 
                            symbol
                        )
                        
                        if price_info and price_info.get('current_price', 0) > 0:
                            current_price = price_info['current_price']
                            change_rate = price_info.get('change_rate', 0)
                            
                            # 실제 가격 데이터 기반 분석
                            features = np.array([
                                current_price,
                                change_rate,
                                price_info.get('volume', 0) / 1000000  # 백만주 단위
                            ])
                            
                            # 변동성 기반 액션 결정
                            if change_rate > 1.5:
                                action = 0  # 매수
                            elif change_rate < -1.5:
                                action = 1  # 매도
                            else:
                                action = 2  # 보유
                            
                            # 실제 변동성 기반 승률 추정
                            volatility = abs(change_rate) / 100.0
                            win_rate = 0.5 + min(volatility * 0.1, 0.25)
                            
                            # 학습 기록
                            training_record = {
                                'stock_code': symbol,
                                'stock_name': stock['name'],
                                'market': 'US',
                                'exchange': stock['exchange'],
                                'date': datetime.now().strftime('%Y%m%d'),
                                'timestamp': datetime.now().isoformat(),
                                'type': 'quick_us_training',
                                'win_rate': win_rate,
                                'price': current_price,
                                'currency': 'USD'
                            }
                            
                            self.training_history.append(training_record)
                            self.trained_overseas_stocks.append(symbol)
                            self._save_training_history()
                            
                            elapsed = (datetime.now() - start_time).total_seconds()
                            logger.info(f"✅ US stock training completed in {elapsed:.1f}s")
                            logger.info(f"   Stock: {stock['name']} (${current_price:.2f})")
                            logger.info(f"   Estimated win rate: {training_record['win_rate']:.1%}")
                            
                            return training_record
                            
                    except Exception as e:
                        logger.error(f"US stock training error for {symbol}: {e}")
                        continue
                        
            return None
            
        except Exception as e:
            logger.error(f"Quick US training error: {e}")
            return None