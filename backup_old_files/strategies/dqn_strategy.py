"""
강화학습(DQN) 기반 자동 전략 학습
참조: https://twentytwentyone.tistory.com/1873

[주요 특징]
- Deep Q-Network를 사용한 자동 전략 학습
- 시장 상태를 학습하여 최적의 행동 선택
- 경험 재생(Experience Replay)으로 안정적 학습
- 자동으로 투자 전략 개선
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
from collections import deque
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from indicators.technical import TechnicalIndicators


class DQN(nn.Module):
    """Deep Q-Network 모델"""
    
    def __init__(self, state_size: int, action_size: int, hidden_size: int = 128):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(state_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.fc3 = nn.Linear(hidden_size, hidden_size)
        self.fc4 = nn.Linear(hidden_size, action_size)
        self.dropout = nn.Dropout(0.2)
        
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)
        x = torch.relu(self.fc2(x))
        x = self.dropout(x)
        x = torch.relu(self.fc3(x))
        x = self.fc4(x)
        return x


class DQNAgent:
    """DQN 에이전트"""
    
    def __init__(self, state_size: int, action_size: int = 3):  # 매수, 매도, 홀드
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=10000)
        self.epsilon = 1.0  # 탐험 확률
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.gamma = 0.95  # 할인 계수
        self.learning_rate = 0.001
        
        # 신경망
        self.q_network = DQN(state_size, action_size)
        self.target_network = DQN(state_size, action_size)
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=self.learning_rate)
        
        self.update_target_network()
        
    def update_target_network(self):
        """타겟 네트워크 업데이트"""
        self.target_network.load_state_dict(self.q_network.state_dict())
        
    def remember(self, state, action, reward, next_state, done):
        """경험 저장"""
        self.memory.append((state, action, reward, next_state, done))
        
    def act(self, state):
        """행동 선택 (ε-greedy)"""
        if random.random() <= self.epsilon:
            return random.randrange(self.action_size)
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        q_values = self.q_network(state_tensor)
        return np.argmax(q_values.detach().numpy())
        
    def replay(self, batch_size: int = 32):
        """경험 재생으로 학습"""
        if len(self.memory) < batch_size:
            return
            
        batch = random.sample(self.memory, batch_size)
        states = torch.FloatTensor([e[0] for e in batch])
        actions = torch.LongTensor([e[1] for e in batch])
        rewards = torch.FloatTensor([e[2] for e in batch])
        next_states = torch.FloatTensor([e[3] for e in batch])
        dones = torch.FloatTensor([e[4] for e in batch])
        
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        next_q_values = self.target_network(next_states).max(1)[0].detach()
        target_q_values = rewards + (self.gamma * next_q_values * (1 - dones))
        
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # 엡실론 감소
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay


class DQNStrategy:
    """강화학습 기반 자동 전략"""
    
    def __init__(self, api, config: Dict = None):
        self.api = api
        self.indicators = TechnicalIndicators()
        
        # 기본 설정
        default_config = {
            'state_size': 20,           # 상태 벡터 크기
            'lookback_period': 20,      # 과거 데이터 기간
            'initial_balance': 10000000,  # 초기 자금
            'position_size': 0.2,       # 포지션 크기
            'min_price': 5000,
            'max_price': 500000,
            'max_stocks': 5,
            'learning_episodes': 100,   # 학습 에피소드
            'train_interval': 1000,     # 학습 주기
        }
        
        self.config = {**default_config, **(config or {})}
        
        # DQN 에이전트 초기화
        self.agent = DQNAgent(self.config['state_size'])
        
        # 거래 기록
        self.trade_history = []
        self.portfolio = {}
        self.balance = self.config['initial_balance']
        self.total_trades = 0
        self.winning_trades = 0
        
        # 학습 데이터
        self.state_buffer = deque(maxlen=self.config['lookback_period'])
        
    def extract_features(self, stock_data: List[Dict]) -> np.ndarray:
        """시장 데이터에서 특징 추출"""
        if len(stock_data) < self.config['lookback_period']:
            return None
            
        # 가격 데이터
        prices = [float(d.get('stck_clpr', 0)) for d in stock_data]
        volumes = [int(d.get('acml_vol', 0)) for d in stock_data]
        
        if not prices or len(prices) < self.config['lookback_period']:
            return None
            
        # 기술적 지표 계산
        analysis = self.indicators.analyze_stock(prices, volumes)
        
        # 특징 벡터 구성
        features = []
        
        # 가격 변화율
        returns = [(prices[i] - prices[i-1]) / prices[i-1] if prices[i-1] > 0 else 0 
                  for i in range(1, len(prices))]
        features.extend(returns[-5:])  # 최근 5일 수익률
        
        # 기술적 지표
        features.append(analysis.get('rsi', 50) / 100)  # RSI 정규화
        features.append(1.0 if analysis.get('price_above_ma5', False) else 0.0)
        features.append(1.0 if analysis.get('price_above_ma20', False) else 0.0)
        features.append(min(analysis.get('volume_ratio', 1.0) / 5, 1.0))  # 거래량 비율
        
        # 볼린저 밴드 위치
        current_price = prices[-1]
        ma20 = np.mean(prices[-20:])
        std20 = np.std(prices[-20:])
        bb_position = (current_price - ma20) / (2 * std20 + 1e-10)
        features.append(np.clip(bb_position, -1, 1))
        
        # 모멘텀
        momentum_5 = (prices[-1] - prices[-6]) / prices[-6] if len(prices) > 5 and prices[-6] > 0 else 0
        momentum_20 = (prices[-1] - prices[-21]) / prices[-21] if len(prices) > 20 and prices[-21] > 0 else 0
        features.append(np.clip(momentum_5, -0.2, 0.2))
        features.append(np.clip(momentum_20, -0.3, 0.3))
        
        # 패딩으로 고정 크기 맞추기
        while len(features) < self.config['state_size']:
            features.append(0.0)
            
        return np.array(features[:self.config['state_size']])
    
    def calculate_reward(self, action: int, price_change: float, 
                        holding_position: bool) -> float:
        """보상 계산"""
        reward = 0.0
        
        if action == 0:  # 매수
            if not holding_position and price_change > 0:
                reward = price_change * 10  # 좋은 매수 타이밍
            elif not holding_position and price_change < 0:
                reward = price_change * 5  # 나쁜 매수 타이밍
            elif holding_position:
                reward = -0.1  # 이미 보유 중인데 매수 시도
                
        elif action == 1:  # 매도
            if holding_position and price_change < 0:
                reward = -price_change * 10  # 좋은 매도 타이밍 (손실 회피)
            elif holding_position and price_change > 0:
                reward = price_change * 5  # 수익 실현
            elif not holding_position:
                reward = -0.1  # 보유하지 않은데 매도 시도
                
        else:  # 홀드
            reward = -0.01  # 작은 페널티 (거래 촉진)
            
        return reward
    
    def get_action_name(self, action: int) -> str:
        """행동 이름 반환"""
        actions = {0: "BUY", 1: "SELL", 2: "HOLD"}
        return actions.get(action, "UNKNOWN")
    
    def train_on_historical_data(self, stock_code: str, days: int = 100):
        """과거 데이터로 학습"""
        print(f"\n🧠 {stock_code} 종목으로 DQN 학습 시작...")
        
        # 과거 데이터 조회
        daily_data = self.api.get_daily_price(stock_code, days=days)
        if not daily_data or daily_data.get('rt_cd') != '0':
            print("❌ 데이터 조회 실패")
            return
            
        stock_data = daily_data.get('output', [])
        if len(stock_data) < self.config['lookback_period'] + 1:
            print("❌ 데이터 부족")
            return
            
        # 에피소드별 학습
        for episode in range(self.config['learning_episodes']):
            episode_reward = 0
            holding = False
            
            for i in range(self.config['lookback_period'], len(stock_data) - 1):
                # 현재 상태
                state = self.extract_features(stock_data[:i+1])
                if state is None:
                    continue
                    
                # 행동 선택
                action = self.agent.act(state)
                
                # 다음 가격
                current_price = float(stock_data[i]['stck_clpr'])
                next_price = float(stock_data[i+1]['stck_clpr'])
                price_change = (next_price - current_price) / current_price
                
                # 보상 계산
                reward = self.calculate_reward(action, price_change, holding)
                episode_reward += reward
                
                # 포지션 업데이트
                if action == 0 and not holding:  # 매수
                    holding = True
                elif action == 1 and holding:  # 매도
                    holding = False
                
                # 다음 상태
                next_state = self.extract_features(stock_data[:i+2])
                done = (i == len(stock_data) - 2)
                
                if next_state is not None:
                    # 경험 저장
                    self.agent.remember(state, action, reward, next_state, done)
                    
                # 학습
                if len(self.agent.memory) > 32:
                    self.agent.replay(32)
                    
            # 타겟 네트워크 업데이트
            if episode % 10 == 0:
                self.agent.update_target_network()
                
            if episode % 20 == 0:
                print(f"   에피소드 {episode}: 총 보상 = {episode_reward:.2f}, ε = {self.agent.epsilon:.3f}")
                
        print("✅ DQN 학습 완료!")
    
    def analyze_stock(self, stock_code: str) -> Dict:
        """DQN으로 종목 분석"""
        # 최근 데이터 조회
        daily_data = self.api.get_daily_price(stock_code)
        if not daily_data or daily_data.get('rt_cd') != '0':
            return {'signal': 'HOLD', 'confidence': 0, 'reason': '데이터 조회 실패'}
            
        stock_data = daily_data.get('output', [])
        if len(stock_data) < self.config['lookback_period']:
            return {'signal': 'HOLD', 'confidence': 0, 'reason': '데이터 부족'}
            
        # 현재 상태 추출
        state = self.extract_features(stock_data[:self.config['lookback_period']+1])
        if state is None:
            return {'signal': 'HOLD', 'confidence': 0, 'reason': '특징 추출 실패'}
            
        # Q값 계산
        state_tensor = torch.FloatTensor(state).unsqueeze(0)
        with torch.no_grad():
            q_values = self.agent.q_network(state_tensor).squeeze().numpy()
            
        # 최적 행동 선택
        action = np.argmax(q_values)
        confidence = abs(q_values[action] - np.mean(q_values)) * 100
        confidence = min(100, max(0, confidence))
        
        # 신호 생성
        signal = self.get_action_name(action)
        
        # 이유 생성
        if action == 0:
            reason = f"DQN 모델이 매수 신호 감지 (Q값: {q_values[0]:.2f})"
        elif action == 1:
            reason = f"DQN 모델이 매도 신호 감지 (Q값: {q_values[1]:.2f})"
        else:
            reason = f"DQN 모델이 관망 권고 (Q값: {q_values[2]:.2f})"
            
        return {
            'signal': signal,
            'confidence': int(confidence),
            'reason': reason,
            'q_values': q_values.tolist(),
            'epsilon': self.agent.epsilon
        }
    
    def run_once(self) -> Dict:
        """전략 1회 실행"""
        result = {
            'timestamp': datetime.now().isoformat(),
            'strategy': 'dqn',
            'buys': [],
            'sells': [],
            'analysis': [],
            'errors': []
        }
        
        # 보유 종목 확인
        holdings = self.api.get_holding_stocks()
        holding_codes = [h['stock_code'] for h in holdings] if holdings else []
        
        # 거래량 상위 종목 조회
        volume_stocks = []
        for market in ['J', 'Q']:  # KOSPI, KOSDAQ
            volume_data = self.api.get_volume_rank(market)
            if volume_data and volume_data.get('rt_cd') == '0':
                stocks = volume_data.get('output', [])[:10]
                for stock in stocks:
                    try:
                        code = stock.get('mksc_shrn_iscd', '')
                        name = stock.get('hts_kor_isnm', '')
                        price = int(stock.get('stck_prpr', 0))
                        
                        if code and self.config['min_price'] <= price <= self.config['max_price']:
                            volume_stocks.append({
                                'code': code,
                                'name': name,
                                'price': price
                            })
                    except (ValueError, TypeError):
                        continue
        
        # DQN으로 각 종목 분석
        analyzed_count = 0
        for stock in volume_stocks[:20]:  # 상위 20개만
            if analyzed_count >= 5:  # 최대 5개 분석
                break
                
            code = stock['code']
            name = stock['name']
            
            # 이미 보유 중이면 스킵
            if code in holding_codes:
                continue
                
            print(f"\n🤖 DQN 분석: {name} ({code})")
            
            # DQN 분석
            analysis = self.analyze_stock(code)
            result['analysis'].append({
                'code': code,
                'name': name,
                **analysis
            })
            
            # 매수 신호이고 신뢰도가 높으면 매수
            if analysis['signal'] == 'BUY' and analysis['confidence'] >= 60:
                # 매수 수량 계산
                available_cash = self.api.get_available_cash()
                max_investment = int(available_cash * self.config['position_size'])
                quantity = max_investment // stock['price']
                
                if quantity > 0:
                    print(f"   → 매수 실행: {quantity}주")
                    result['buys'].append({
                        'code': code,
                        'name': name,
                        'quantity': quantity,
                        'price': stock['price'],
                        'confidence': analysis['confidence'],
                        'reason': analysis['reason']
                    })
                
            analyzed_count += 1
        
        # 보유 종목 매도 검토
        for holding in holdings:
            code = holding['stock_code']
            name = holding['stock_name']
            
            analysis = self.analyze_stock(code)
            
            if analysis['signal'] == 'SELL' and analysis['confidence'] >= 60:
                print(f"\n💰 매도 신호: {name} ({code})")
                result['sells'].append({
                    'code': code,
                    'name': name,
                    'quantity': holding['quantity'],
                    'confidence': analysis['confidence'],
                    'reason': analysis['reason']
                })
        
        # 학습 (주기적으로)
        self.total_trades += 1
        if self.total_trades % self.config['train_interval'] == 0:
            print("\n🧠 모델 재학습 중...")
            # 최근 거래가 활발한 종목으로 재학습
            if volume_stocks:
                self.train_on_historical_data(volume_stocks[0]['code'])
        
        return result
    
    def get_status(self) -> Dict:
        """현재 상태 조회"""
        return {
            'strategy': 'dqn',
            'epsilon': self.agent.epsilon,
            'memory_size': len(self.agent.memory),
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
            'balance': self.balance,
            'portfolio': self.portfolio,
            'config': self.config
        }