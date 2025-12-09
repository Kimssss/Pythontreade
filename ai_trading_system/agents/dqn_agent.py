#!/usr/bin/env python3
"""
DQN 에이전트 - 백테스팅용 단순화 버전
"""

import numpy as np
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger('dqn_agent')

class DQNAgent:
    """DQN 에이전트 (백테스팅용 단순화 버전)"""
    
    def __init__(self, state_dim: int = 50, action_dim: int = 3, lr: float = 0.001):
        """
        Args:
            state_dim: 상태 공간 차원
            action_dim: 행동 공간 차원 (0: 매도, 1: 보유, 2: 매수)
            lr: 학습률
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.lr = lr
        self.name = "DQNAgent"
        
        # 단순한 가중치 (실제 신경망 대신)
        self.weights = np.random.randn(state_dim) * 0.1
        
    async def predict(self, state: np.ndarray) -> int:
        """행동 예측
        
        Args:
            state: 상태 벡터
            
        Returns:
            행동 (0: 매도, 1: 보유, 2: 매수)
        """
        try:
            if len(state) != self.state_dim:
                # 상태 차원 맞춤
                if len(state) < self.state_dim:
                    state = np.pad(state, (0, self.state_dim - len(state)))
                else:
                    state = state[:self.state_dim]
                    
            # 단순 선형 결합
            score = np.dot(state, self.weights)
            
            # 행동 결정
            if score > 0.5:
                return 2  # 매수
            elif score < -0.5:
                return 0  # 매도
            else:
                return 1  # 보유
                
        except Exception as e:
            logger.error(f"DQN 예측 중 오류: {e}")
            return 1  # 기본값: 보유
            
    def get_signal(self, action: int) -> float:
        """행동을 신호로 변환
        
        Args:
            action: DQN 행동
            
        Returns:
            신호 값 (-1 ~ 1)
        """
        if action == 0:  # 매도
            return -0.8
        elif action == 2:  # 매수
            return 0.8
        else:  # 보유
            return 0
            
    async def analyze_stock(self, price_data, additional_features=None) -> Dict[str, Any]:
        """주식 분석 (다른 에이전트와 인터페이스 통일)
        
        Args:
            price_data: 가격 데이터
            additional_features: 추가 특성
            
        Returns:
            분석 결과
        """
        try:
            # 가격 데이터에서 특성 추출
            state = self._extract_features(price_data, additional_features)
            
            # 행동 예측
            action = await self.predict(state)
            
            # 신호 변환
            signal = self.get_signal(action)
            
            return {
                '신호': signal,
                'confidence': abs(signal),
                'action': action,
                'state_dim': len(state)
            }
            
        except Exception as e:
            logger.error(f"DQN 분석 중 오류: {e}")
            return {'신호': 0, 'confidence': 0, 'action': 1}
            
    def _extract_features(self, price_data, additional_features=None) -> np.ndarray:
        """가격 데이터에서 특성 추출"""
        try:
            features = []
            
            if hasattr(price_data, 'values'):
                # DataFrame인 경우
                closes = price_data['close'].values if 'close' in price_data.columns else price_data.iloc[:, -1].values
            else:
                # 배열인 경우
                closes = np.array(price_data)
                
            # 기본 특성
            if len(closes) > 0:
                # 가격 변화율
                if len(closes) > 1:
                    returns = np.diff(closes) / closes[:-1]
                    features.extend(returns[-10:].tolist() if len(returns) >= 10 else returns.tolist())
                
                # 이동평균
                if len(closes) >= 5:
                    sma_5 = np.mean(closes[-5:])
                    features.append(sma_5 / closes[-1] - 1)
                
                if len(closes) >= 20:
                    sma_20 = np.mean(closes[-20:])
                    features.append(sma_20 / closes[-1] - 1)
                
                # 변동성
                if len(closes) > 1:
                    volatility = np.std(closes[-min(20, len(closes)):])
                    features.append(volatility / closes[-1])
                    
            # 추가 특성
            if additional_features:
                if isinstance(additional_features, (list, np.ndarray)):
                    features.extend(additional_features)
                    
            # 크기 조정
            while len(features) < self.state_dim:
                features.append(0)
                
            return np.array(features[:self.state_dim])
            
        except Exception as e:
            logger.error(f"특성 추출 중 오류: {e}")
            return np.zeros(self.state_dim)