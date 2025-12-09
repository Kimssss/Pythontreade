"""
DQN (Deep Q-Network) 강화학습 트레이딩 에이전트
블로그 분석 기반 구현
"""
import numpy as np
import pandas as pd
from collections import deque
import random
import torch
import torch.nn as nn
import torch.optim as optim
import logging
from typing import Dict, List, Tuple, Optional

try:
    from ..config.settings import MODEL_CONFIG
except ImportError:
    from config.settings import MODEL_CONFIG

logger = logging.getLogger('ai_trading.dqn')


class DQNNetwork(nn.Module):
    """DQN 신경망"""
    
    def __init__(self, state_size: int, action_size: int):
        super(DQNNetwork, self).__init__()
        
        self.fc1 = nn.Linear(state_size, 128)
        self.dropout1 = nn.Dropout(0.2)
        self.fc2 = nn.Linear(128, 64)
        self.dropout2 = nn.Dropout(0.2)
        self.fc3 = nn.Linear(64, 32)
        self.fc4 = nn.Linear(32, action_size)
        
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.dropout1(x)
        x = torch.relu(self.fc2(x))
        x = self.dropout2(x)
        x = torch.relu(self.fc3(x))
        x = self.fc4(x)
        return x


class DQNAgent:
    """DQN 트레이딩 에이전트"""
    
    def __init__(self, state_size: int = 31, action_size: int = 3):
        self.state_size = state_size
        self.action_size = action_size
        
        # 하이퍼파라미터
        config = MODEL_CONFIG['dqn']
        self.learning_rate = config['learning_rate']
        self.epsilon = config['epsilon']
        self.epsilon_min = config['epsilon_min']
        self.epsilon_decay = config['epsilon_decay']
        self.gamma = config['gamma']
        self.batch_size = config['batch_size']
        self.memory_size = config['memory_size']
        self.update_target_freq = config['update_target_freq']
        
        # 경험 재생 메모리
        self.memory = deque(maxlen=self.memory_size)
        
        # 신경망
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.q_network = DQNNetwork(state_size, action_size).to(self.device)
        self.target_network = DQNNetwork(state_size, action_size).to(self.device)
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=self.learning_rate)
        
        # 타겟 네트워크 초기화
        self.update_target_network()
        
        # 학습 카운터
        self.train_step = 0
        
        logger.info(f"DQN Agent initialized on {self.device}")
    
    def update_target_network(self):
        """타겟 네트워크 업데이트"""
        self.target_network.load_state_dict(self.q_network.state_dict())
    
    def remember(self, state, action, reward, next_state, done):
        """경험 저장"""
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state: np.ndarray, training: bool = True) -> int:
        """행동 선택
        
        Returns:
            0: 매수 (Buy)
            1: 매도 (Sell)
            2: 관망 (Hold)
        """
        # Epsilon-greedy 정책
        if training and random.random() <= self.epsilon:
            return random.randrange(self.action_size)
        
        # Q값 기반 행동 선택
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.q_network(state_tensor)
        
        return np.argmax(q_values.cpu().numpy()[0])
    
    def replay(self):
        """경험 재생을 통한 학습"""
        if len(self.memory) < self.batch_size:
            return
        
        # 미니배치 샘플링
        batch = random.sample(self.memory, self.batch_size)
        states = torch.FloatTensor([e[0] for e in batch]).to(self.device)
        actions = torch.LongTensor([e[1] for e in batch]).to(self.device)
        rewards = torch.FloatTensor([e[2] for e in batch]).to(self.device)
        next_states = torch.FloatTensor([e[3] for e in batch]).to(self.device)
        dones = torch.FloatTensor([e[4] for e in batch]).to(self.device)
        
        # 현재 Q값
        current_q_values = self.q_network(states).gather(1, actions.unsqueeze(1))
        
        # 타겟 Q값 계산 (Double DQN)
        next_q_values = self.target_network(next_states).max(1)[0].detach()
        target_q_values = rewards + (self.gamma * next_q_values * (1 - dones))
        
        # 손실 계산 및 역전파
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Epsilon 감소
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
        
        # 타겟 네트워크 업데이트
        self.train_step += 1
        if self.train_step % self.update_target_freq == 0:
            self.update_target_network()
        
        return loss.item()
    
    def train_step(self):
        """한 번의 학습 스텝 (weekend_trainer에서 사용)"""
        return self.replay()
    
    def calculate_reward(self, action: int, current_price: float, 
                        next_price: float, position: int) -> float:
        """보상 계산
        
        Args:
            action: 행동 (0: 매수, 1: 매도, 2: 관망)
            current_price: 현재가
            next_price: 다음 가격
            position: 현재 포지션 (0: 미보유, 1: 보유)
        """
        price_change_rate = (next_price - current_price) / current_price
        
        if action == 0:  # 매수
            if position == 0:  # 미보유 → 매수
                return price_change_rate * 100
            else:  # 이미 보유 중
                return -0.1  # 중복 매수 패널티
        
        elif action == 1:  # 매도
            if position == 1:  # 보유 → 매도
                return price_change_rate * 100
            else:  # 미보유인데 매도 시도
                return -0.1  # 공매도 방지 패널티
        
        else:  # 관망
            if position == 1:  # 보유 중 관망
                return price_change_rate * 50  # 절반 보상
            else:
                return 0
    
    def prepare_state(self, price_history: pd.DataFrame, 
                     current_position: int) -> np.ndarray:
        """상태 벡터 준비
        
        Args:
            price_history: 최근 30일 가격 데이터
            current_position: 현재 포지션
        
        Returns:
            31차원 상태 벡터
        """
        # 최근 30일 일별 수익률
        returns = price_history['close'].pct_change().fillna(0).values[-30:]
        
        # 포지션 정보 추가
        state = np.append(returns, current_position)
        
        return state
    
    def get_action_confidence(self, state: np.ndarray) -> Dict[str, float]:
        """각 행동의 신뢰도 계산"""
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            q_values = self.q_network(state_tensor).cpu().numpy()[0]
        
        # Softmax를 통한 확률 계산
        exp_q = np.exp(q_values - np.max(q_values))
        probabilities = exp_q / np.sum(exp_q)
        
        return {
            'buy_confidence': probabilities[0],
            'sell_confidence': probabilities[1],
            'hold_confidence': probabilities[2],
            'action': int(np.argmax(q_values)),
            'max_confidence': float(np.max(probabilities))
        }
    
    def save_model(self, filepath: str):
        """모델 저장"""
        torch.save({
            'q_network_state_dict': self.q_network.state_dict(),
            'target_network_state_dict': self.target_network.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'train_step': self.train_step
        }, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """모델 로드"""
        checkpoint = torch.load(filepath, map_location=self.device)
        
        self.q_network.load_state_dict(checkpoint['q_network_state_dict'])
        self.target_network.load_state_dict(checkpoint['target_network_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint['epsilon']
        self.train_step = checkpoint['train_step']
        
        logger.info(f"Model loaded from {filepath}")
    
    def train_on_batch(self, states: np.ndarray, actions: np.ndarray, 
                      rewards: np.ndarray, next_states: np.ndarray, 
                      dones: np.ndarray) -> float:
        """배치 학습"""
        states_t = torch.FloatTensor(states).to(self.device)
        actions_t = torch.LongTensor(actions).to(self.device)
        rewards_t = torch.FloatTensor(rewards).to(self.device)
        next_states_t = torch.FloatTensor(next_states).to(self.device)
        dones_t = torch.FloatTensor(dones).to(self.device)
        
        # Q값 계산
        current_q_values = self.q_network(states_t).gather(1, actions_t.unsqueeze(1))
        next_q_values = self.target_network(next_states_t).max(1)[0].detach()
        target_q_values = rewards_t + (self.gamma * next_q_values * (1 - dones_t))
        
        # 손실 계산
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        # 역전파
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return loss.item()