#!/usr/bin/env python3
"""
AI 자동매매 시스템 메인 모듈
- DQN 강화학습 기반 트레이딩
- AutoML 하이퍼파라미터 최적화
- 실시간 모니터링 및 자동 재훈련
"""

import sys
import os
import traceback
from pathlib import Path

# 자동 패키지 설치
try:
    from auto_install import check_and_install_requirements, auto_install_on_import
    
    # 시스템 시작 시 모든 의존성 확인
    print("🔧 의존성 패키지 확인 중...")
    if not check_and_install_requirements():
        print("❌ 패키지 설치 실패. 시스템을 종료합니다.")
        sys.exit(1)
    print("✅ 의존성 확인 완료\n")
    
except ImportError as e:
    print(f"⚠️ 자동 설치 모듈 로드 실패: {e}")
    print("수동으로 필요한 패키지들을 설치해주세요.")

# 이제 안전하게 다른 모듈들을 임포트
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Tuple, Optional
import threading
import time

# 로컬 모듈
from kis_api import KisAPI
from config import Config

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_trading.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class TradingEnvironment:
    """
    강화학습을 위한 트레이딩 환경 (OpenAI Gym 스타일)
    """
    
    def __init__(self, kis_api: KisAPI, stocks: List[str], initial_balance: float = 1000000):
        self.kis_api = kis_api
        self.stocks = stocks  # 거래할 종목 리스트
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.positions = {stock: 0 for stock in stocks}  # 각 종목별 보유 수량
        self.prices = {stock: 0 for stock in stocks}     # 각 종목별 현재가
        self.price_history = {stock: [] for stock in stocks}  # 가격 이력
        self.step_count = 0
        self.max_steps = 1000
        
        # 상태 공간 차원: 각 종목별 (가격 변화율, RSI, 이동평균, 거래량) + 보유 현금 비율 + 포지션
        self.observation_space_size = len(stocks) * 4 + 1 + len(stocks)
        # 액션 공간: 각 종목에 대해 (매수, 보유, 매도)
        self.action_space_size = 3 ** len(stocks)
        
    def reset(self):
        """환경 리셋"""
        self.current_balance = self.initial_balance
        self.positions = {stock: 0 for stock in self.stocks}
        self.step_count = 0
        
        # 현재 가격 정보 가져오기
        self._update_market_data()
        return self._get_state()
    
    def _update_market_data(self):
        """시장 데이터 업데이트"""
        for stock in self.stocks:
            try:
                price_data = self.kis_api.get_stock_price(stock)
                if price_data and price_data.get('rt_cd') == '0':
                    current_price = int(price_data['output']['stck_prpr'])
                    self.prices[stock] = current_price
                    self.price_history[stock].append(current_price)
                    
                    # 최근 30개 가격만 유지
                    if len(self.price_history[stock]) > 30:
                        self.price_history[stock] = self.price_history[stock][-30:]
                else:
                    logger.warning(f"{stock} 가격 정보 조회 실패")
            except Exception as e:
                logger.error(f"{stock} 가격 조회 중 오류: {e}")
    
    def _calculate_technical_indicators(self, stock: str) -> Dict[str, float]:
        """기술적 지표 계산"""
        prices = self.price_history[stock]
        if len(prices) < 10:
            return {'price_change': 0, 'rsi': 50, 'ma_ratio': 1, 'volume_ma': 1}
        
        # 가격 변화율
        price_change = (prices[-1] - prices[-2]) / prices[-2] if len(prices) >= 2 else 0
        
        # RSI 계산 (단순화된 버전)
        gains = []
        losses = []
        for i in range(1, min(len(prices), 15)):
            change = prices[i] - prices[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = np.mean(gains) if gains else 0
        avg_loss = np.mean(losses) if losses else 0.001  # 0으로 나누기 방지
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        # 이동평균 비율
        ma_5 = np.mean(prices[-5:]) if len(prices) >= 5 else prices[-1]
        ma_ratio = prices[-1] / ma_5
        
        return {
            'price_change': price_change,
            'rsi': rsi,
            'ma_ratio': ma_ratio,
            'volume_ma': 1.0  # 거래량 정보는 추후 추가
        }
    
    def _get_state(self) -> np.ndarray:
        """현재 상태 벡터 생성"""
        state = []
        
        # 각 종목별 기술적 지표
        for stock in self.stocks:
            indicators = self._calculate_technical_indicators(stock)
            state.extend([
                indicators['price_change'],
                indicators['rsi'] / 100,  # 0-1 정규화
                indicators['ma_ratio'] - 1,  # 중심화
                indicators['volume_ma']
            ])
        
        # 현금 비율
        total_value = self._calculate_portfolio_value()
        cash_ratio = self.current_balance / total_value if total_value > 0 else 1
        state.append(cash_ratio)
        
        # 각 종목별 포지션 비율
        for stock in self.stocks:
            position_value = self.positions[stock] * self.prices[stock]
            position_ratio = position_value / total_value if total_value > 0 else 0
            state.append(position_ratio)
        
        return np.array(state, dtype=np.float32)
    
    def _calculate_portfolio_value(self) -> float:
        """포트폴리오 총 가치 계산"""
        total_value = self.current_balance
        for stock in self.stocks:
            total_value += self.positions[stock] * self.prices[stock]
        return total_value
    
    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict]:
        """액션 실행"""
        self.step_count += 1
        
        # 액션을 각 종목별 행동으로 분해
        actions = self._decode_action(action)
        
        # 포트폴리오 이전 가치
        prev_value = self._calculate_portfolio_value()
        
        # 시장 데이터 업데이트
        self._update_market_data()
        
        # 각 종목에 대해 액션 실행
        for i, stock in enumerate(self.stocks):
            stock_action = actions[i]  # 0: 매도, 1: 보유, 2: 매수
            
            if stock_action == 2:  # 매수
                self._execute_buy(stock)
            elif stock_action == 0:  # 매도
                self._execute_sell(stock)
            # 1: 보유 (아무 작업 안함)
        
        # 새로운 포트폴리오 가치
        new_value = self._calculate_portfolio_value()
        
        # 보상 계산 (일일 수익률)
        reward = (new_value - prev_value) / prev_value if prev_value > 0 else 0
        
        # 에피소드 종료 조건
        done = (self.step_count >= self.max_steps) or (new_value < self.initial_balance * 0.5)
        
        info = {
            'portfolio_value': new_value,
            'cash': self.current_balance,
            'positions': self.positions.copy(),
            'step': self.step_count
        }
        
        return self._get_state(), reward, done, info
    
    def _decode_action(self, action: int) -> List[int]:
        """통합 액션을 각 종목별 액션으로 분해"""
        actions = []
        for i in range(len(self.stocks)):
            actions.append(action % 3)
            action //= 3
        return actions
    
    def _execute_buy(self, stock: str):
        """매수 실행 (포트폴리오의 10% 금액으로)"""
        try:
            total_value = self._calculate_portfolio_value()
            buy_amount = total_value * 0.1  # 10% 매수
            
            if buy_amount > self.current_balance:
                buy_amount = self.current_balance * 0.9  # 현금의 90%
            
            if buy_amount > self.prices[stock]:  # 최소 1주는 살 수 있는 금액
                quantity = int(buy_amount / self.prices[stock])
                cost = quantity * self.prices[stock]
                
                if cost <= self.current_balance:
                    self.positions[stock] += quantity
                    self.current_balance -= cost
                    logger.info(f"매수: {stock} {quantity}주 @ {self.prices[stock]}원")
        
        except Exception as e:
            logger.error(f"매수 실행 중 오류 ({stock}): {e}")
    
    def _execute_sell(self, stock: str):
        """매도 실행 (보유 수량의 50%)"""
        try:
            if self.positions[stock] > 0:
                sell_quantity = max(1, self.positions[stock] // 2)  # 최소 1주
                if sell_quantity <= self.positions[stock]:
                    revenue = sell_quantity * self.prices[stock]
                    self.positions[stock] -= sell_quantity
                    self.current_balance += revenue
                    logger.info(f"매도: {stock} {sell_quantity}주 @ {self.prices[stock]}원")
        
        except Exception as e:
            logger.error(f"매도 실행 중 오류 ({stock}): {e}")

class DQNAgent:
    """
    Deep Q-Network 에이전트
    """
    
    def __init__(self, state_size: int, action_size: int, learning_rate: float = 0.001):
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.epsilon = 1.0  # 탐험율
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01
        self.memory = []
        self.memory_size = 10000
        self.batch_size = 32
        self.gamma = 0.95  # 할인률
        
        # 신경망 모델 구축
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()
    
    def _build_model(self):
        """DQN 모델 구축"""
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(128, activation='relu', input_shape=(self.state_size,)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(self.action_size, activation='linear')
        ])
        
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse'
        )
        return model
    
    def update_target_model(self):
        """타겟 모델 업데이트"""
        self.target_model.set_weights(self.model.get_weights())
    
    def remember(self, state, action, reward, next_state, done):
        """경험 저장"""
        self.memory.append((state, action, reward, next_state, done))
        if len(self.memory) > self.memory_size:
            self.memory.pop(0)
    
    def act(self, state, training=True):
        """액션 선택 (epsilon-greedy)"""
        if training and np.random.random() <= self.epsilon:
            return np.random.choice(self.action_size)
        
        q_values = self.model.predict(state.reshape(1, -1), verbose=0)
        return np.argmax(q_values[0])
    
    def replay(self):
        """경험 재생 학습"""
        if len(self.memory) < self.batch_size:
            return
        
        batch = np.random.choice(len(self.memory), self.batch_size, replace=False)
        states = np.array([self.memory[i][0] for i in batch])
        actions = np.array([self.memory[i][1] for i in batch])
        rewards = np.array([self.memory[i][2] for i in batch])
        next_states = np.array([self.memory[i][3] for i in batch])
        dones = np.array([self.memory[i][4] for i in batch])
        
        current_q_values = self.model.predict(states, verbose=0)
        next_q_values = self.target_model.predict(next_states, verbose=0)
        
        targets = current_q_values.copy()
        
        for i in range(self.batch_size):
            if dones[i]:
                targets[i][actions[i]] = rewards[i]
            else:
                targets[i][actions[i]] = rewards[i] + self.gamma * np.max(next_q_values[i])
        
        self.model.fit(states, targets, epochs=1, verbose=0)
        
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def save_model(self, filepath: str):
        """모델 저장"""
        self.model.save(filepath)
        logger.info(f"모델 저장: {filepath}")
    
    def load_model(self, filepath: str):
        """모델 로드"""
        if os.path.exists(filepath):
            self.model = tf.keras.models.load_model(filepath)
            self.update_target_model()
            logger.info(f"모델 로드: {filepath}")
            return True
        return False

class AITradingSystem:
    """
    AI 자동매매 시스템 메인 클래스
    """
    
    def __init__(self, mode='demo'):
        self.mode = mode
        self.kis_api = None
        self.trading_env = None
        self.agent = None
        self.is_running = False
        self.stocks = ['005930', '000660', '051910']  # 삼성전자, SK하이닉스, LG화학
        
        # 로그 파일 설정
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        self.performance_log = log_dir / f"performance_{mode}.json"
        self.model_path = f"models/dqn_model_{mode}.keras"
        
        # 모델 디렉토리 생성
        Path("models").mkdir(exist_ok=True)
        
    def initialize(self):
        """시스템 초기화"""
        try:
            # API 초기화
            account_info = Config.get_account_info(self.mode)
            self.kis_api = KisAPI(
                account_info['appkey'],
                account_info['appsecret'], 
                account_info['account'],
                is_real=(self.mode == 'real')
            )
            
            # 토큰 발급
            if not self.kis_api.get_access_token():
                raise Exception("API 토큰 발급 실패")
            
            # 트레이딩 환경 초기화
            self.trading_env = TradingEnvironment(self.kis_api, self.stocks)
            
            # DQN 에이전트 초기화
            self.agent = DQNAgent(
                state_size=self.trading_env.observation_space_size,
                action_size=self.trading_env.action_space_size
            )
            
            # 기존 모델 로드 (있다면)
            self.agent.load_model(self.model_path)
            
            logger.info(f"AI 자동매매 시스템 초기화 완료 ({self.mode} 모드)")
            return True
            
        except Exception as e:
            logger.error(f"시스템 초기화 실패: {e}")
            traceback.print_exc()
            return False
    
    def train_agent(self, episodes=1000):
        """에이전트 훈련"""
        logger.info(f"DQN 에이전트 훈련 시작 (에피소드: {episodes})")
        
        scores = []
        best_score = float('-inf')
        
        for episode in range(episodes):
            state = self.trading_env.reset()
            total_reward = 0
            step = 0
            
            while True:
                action = self.agent.act(state, training=True)
                next_state, reward, done, info = self.trading_env.step(action)
                
                self.agent.remember(state, action, reward, next_state, done)
                state = next_state
                total_reward += reward
                step += 1
                
                if done:
                    break
                
                # 주기적 학습
                if step % 10 == 0:
                    self.agent.replay()
            
            scores.append(total_reward)
            
            # 타겟 모델 업데이트
            if episode % 10 == 0:
                self.agent.update_target_model()
            
            # 성능 로깅
            if episode % 100 == 0:
                avg_score = np.mean(scores[-100:])
                logger.info(f"에피소드 {episode}, 평균 점수: {avg_score:.4f}, 엡실론: {self.agent.epsilon:.4f}")
                
                # 최고 성능 모델 저장
                if avg_score > best_score:
                    best_score = avg_score
                    self.agent.save_model(self.model_path)
        
        logger.info("훈련 완료")
        return scores
    
    def run_live_trading(self):
        """실시간 트레이딩 실행"""
        if not self.initialize():
            return
        
        logger.info("실시간 AI 자동매매 시작")
        self.is_running = True
        
        try:
            while self.is_running:
                # 토큰 갱신 확인
                self.kis_api.refresh_token_if_needed()
                
                # 현재 상태 가져오기
                self.trading_env._update_market_data()
                state = self.trading_env._get_state()
                
                # AI 모델로 액션 결정 (탐험 없이)
                action = self.agent.act(state, training=False)
                
                # 실제 거래 실행은 별도 로직 필요
                self._execute_real_trading(action)
                
                # 성능 기록
                self._log_performance()
                
                # 30분 대기 (실제 운영에서는 조정 가능)
                time.sleep(30 * 60)
                
        except KeyboardInterrupt:
            logger.info("사용자에 의한 트레이딩 중단")
        except Exception as e:
            logger.error(f"트레이딩 실행 중 오류: {e}")
            traceback.print_exc()
        finally:
            self.stop()
    
    def _execute_real_trading(self, action: int):
        """실제 거래 실행 (매우 보수적으로)"""
        try:
            # 실제 잔고 조회
            balance = self.kis_api.get_balance()
            if not balance:
                logger.warning("잔고 조회 실패")
                return
            
            # 보유 종목 확인
            holdings = self.kis_api.get_holding_stocks()
            available_cash = self.kis_api.get_available_cash()
            
            logger.info(f"현재 보유 현금: {available_cash:,}원")
            logger.info(f"보유 종목 수: {len(holdings)}")
            
            # 여기서 실제 매매 로직 구현
            # 안전을 위해 작은 금액으로만 테스트
            
        except Exception as e:
            logger.error(f"실제 거래 실행 중 오류: {e}")
    
    def _log_performance(self):
        """성능 로깅"""
        try:
            performance_data = {
                'timestamp': datetime.now().isoformat(),
                'balance': self.kis_api.get_available_cash(),
                'holdings': self.kis_api.get_holding_stocks(),
                'mode': self.mode
            }
            
            # 파일에 추가
            logs = []
            if self.performance_log.exists():
                with open(self.performance_log, 'r') as f:
                    logs = json.load(f)
            
            logs.append(performance_data)
            
            # 최근 1000개만 유지
            if len(logs) > 1000:
                logs = logs[-1000:]
            
            with open(self.performance_log, 'w') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"성능 로깅 중 오류: {e}")
    
    def stop(self):
        """시스템 중단"""
        self.is_running = False
        logger.info("AI 자동매매 시스템 중단")

def main():
    """메인 함수"""
    print("🤖 AI 자동매매 시스템")
    print("=" * 50)
    
    # 모드 선택
    while True:
        mode = input("모드를 선택하세요 (demo/real/train): ").strip().lower()
        if mode in ['demo', 'real', 'train']:
            break
        print("올바른 모드를 입력하세요: demo, real, train")
    
    system = AITradingSystem(mode='demo' if mode in ['demo', 'train'] else 'real')
    
    try:
        if mode == 'train':
            if system.initialize():
                print("🧠 AI 모델 훈련을 시작합니다...")
                episodes = int(input("훈련 에피소드 수 (기본값: 1000): ") or "1000")
                system.train_agent(episodes)
        else:
            print(f"🚀 실시간 자동매매를 시작합니다 ({mode} 모드)")
            print("중단하려면 Ctrl+C를 눌러주세요")
            system.run_live_trading()
    
    except Exception as e:
        logger.error(f"시스템 실행 중 오류: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()