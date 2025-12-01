"""
멀티 에이전트 앙상블 시스템
DQN, 팩터, 기술적 분석 에이전트 통합
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

try:
    from .dqn_agent import DQNAgent
    from ..strategies.stock_screener import StockScreener
    from ..utils.technical_indicators import TechnicalIndicators
    from ..utils.kis_api import KisAPIEnhanced
    from ..config.settings import MODEL_CONFIG, TRADING_CONFIG
except ImportError:
    from models.dqn_agent import DQNAgent
    from strategies.stock_screener import StockScreener
    from utils.technical_indicators import TechnicalIndicators
    from utils.kis_api import KisAPIEnhanced
    from config.settings import MODEL_CONFIG, TRADING_CONFIG

logger = logging.getLogger('ai_trading.ensemble')


class TechnicalAnalysisAgent:
    """기술적 분석 에이전트"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
        
    def analyze(self, price_data: pd.DataFrame) -> Dict:
        """기술적 분석 수행"""
        # 기술적 지표 계산
        df = self.indicators.calculate_all_indicators(price_data)
        
        # 신호 생성
        signals = self.indicators.generate_signals(df)
        
        # 최신 신호 가져오기
        latest_signal = signals.iloc[-1] if len(signals) > 0 else None
        
        if latest_signal is None:
            return {'action': 2, 'confidence': 0.5}  # 기본값: 관망
        
        # 신호를 행동으로 변환
        if latest_signal['final_signal'] == 1:
            action = 0  # 매수
        elif latest_signal['final_signal'] == -1:
            action = 1  # 매도
        else:
            action = 2  # 관망
        
        # 신뢰도 계산
        confidence = abs(latest_signal['composite_signal'])
        confidence = min(max(confidence, 0), 1)  # 0~1 범위로 제한
        
        return {
            'action': action,
            'confidence': confidence,
            'signals': {
                'ma_cross': latest_signal['MA_cross'],
                'rsi': latest_signal['RSI_signal'],
                'macd': latest_signal['MACD_signal'],
                'bb': latest_signal['BB_signal'],
                'stoch': latest_signal['Stoch_signal'],
                'volume': latest_signal['Volume_signal']
            }
        }


class FactorInvestingAgent:
    """팩터 투자 에이전트"""
    
    def __init__(self, stock_screener: StockScreener):
        self.screener = stock_screener
        
    async def analyze(self, stock_code: str, market_data: Dict) -> Dict:
        """팩터 분석 수행"""
        # 종목 상세 정보 조회
        stock_details = await self.screener.get_stock_details(stock_code)
        
        if not stock_details:
            return {'action': 2, 'confidence': 0.5}
        
        # 팩터 점수 계산
        df = pd.DataFrame([market_data])
        # 기술적 지표만으로 분석 (재무 데이터는 실제 API 연동 필요)
        df = self.screener.calculate_factor_scores(df)
        
        # 점수 기반 행동 결정
        total_score = df.iloc[0]['total_score'] if 'total_score' in df.columns else 0.5
        
        if total_score >= 0.7:
            action = 0  # 매수
        elif total_score <= 0.3:
            action = 1  # 매도
        else:
            action = 2  # 관망
        
        return {
            'action': action,
            'confidence': abs(total_score - 0.5) * 2,  # 0.5에서 멀수록 높은 신뢰도
            'factor_scores': {
                'value': df.iloc[0].get('value_score', 0),
                'quality': df.iloc[0].get('quality_score', 0),
                'momentum': df.iloc[0].get('momentum_score', 0),
                'growth': df.iloc[0].get('growth_score', 0),
                'total': total_score
            }
        }


class MultiAgentEnsemble:
    """멀티 에이전트 앙상블 시스템"""
    
    def __init__(self, kis_api: KisAPIEnhanced):
        self.kis_api = kis_api
        
        # 에이전트 초기화
        self.dqn_agent = DQNAgent()
        self.technical_agent = TechnicalAnalysisAgent()
        self.factor_agent = FactorInvestingAgent(StockScreener(kis_api))
        
        # 가중치
        self.weights = MODEL_CONFIG['ensemble_weights'].copy()
        
        # 성과 추적
        self.agent_performance = {
            'dqn_agent': [],
            'factor_agent': [],
            'technical_agent': []
        }
        
        logger.info("Multi-Agent Ensemble initialized")
    
    async def generate_signal(self, stock_code: str, 
                            price_data: pd.DataFrame,
                            current_position: int = 0) -> Dict:
        """통합 신호 생성
        
        Args:
            stock_code: 종목 코드
            price_data: 가격 데이터 (OHLCV)
            current_position: 현재 포지션 (0: 미보유, 1: 보유)
        
        Returns:
            통합 신호 및 세부 정보
        """
        decisions = {}
        
        # 1. DQN 에이전트 예측
        if len(price_data) >= 30:
            state = self.dqn_agent.prepare_state(price_data, current_position)
            dqn_result = self.dqn_agent.get_action_confidence(state)
            decisions['dqn_agent'] = {
                'action': dqn_result['action'],
                'confidence': dqn_result['max_confidence']
            }
        else:
            decisions['dqn_agent'] = {'action': 2, 'confidence': 0.5}
        
        # 2. 기술적 분석 에이전트
        technical_result = self.technical_agent.analyze(price_data)
        decisions['technical_agent'] = technical_result
        
        # 3. 팩터 투자 에이전트
        market_data = {
            'code': stock_code,
            'price': float(price_data.iloc[-1]['close']),
            'volume': int(price_data.iloc[-1]['volume'])
        }
        factor_result = await self.factor_agent.analyze(stock_code, market_data)
        decisions['factor_agent'] = factor_result
        
        # 4. 앙상블 결정
        final_decision = self._ensemble_decision(decisions)
        
        return {
            'stock_code': stock_code,
            'action': final_decision['action'],
            'action_name': ['BUY', 'SELL', 'HOLD'][final_decision['action']],
            'confidence': final_decision['confidence'],
            'agent_decisions': decisions,
            'weights': self.weights.copy(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _ensemble_decision(self, decisions: Dict) -> Dict:
        """앙상블 의사 결정"""
        # 가중 평균으로 최종 결정
        action_scores = {0: 0, 1: 0, 2: 0}  # Buy, Sell, Hold
        total_weight = 0
        
        for agent_name, decision in decisions.items():
            if agent_name not in self.weights:
                continue
                
            weight = self.weights[agent_name] * decision['confidence']
            action = decision['action']
            
            action_scores[action] += weight
            total_weight += weight
        
        # 정규화
        if total_weight > 0:
            for action in action_scores:
                action_scores[action] /= total_weight
        
        # 최종 행동 선택
        final_action = max(action_scores, key=action_scores.get)
        final_confidence = action_scores[final_action]
        
        return {
            'action': final_action,
            'confidence': final_confidence,
            'action_scores': action_scores
        }
    
    def update_weights(self, agent_name: str, performance: float):
        """에이전트 가중치 업데이트 (성과 기반)"""
        # 성과 기록
        self.agent_performance[agent_name].append(performance)
        
        # 최근 20개 성과만 유지
        if len(self.agent_performance[agent_name]) > 20:
            self.agent_performance[agent_name].pop(0)
        
        # 평균 성과 계산
        avg_performances = {}
        for name, perfs in self.agent_performance.items():
            if perfs:
                avg_performances[name] = np.mean(perfs)
            else:
                avg_performances[name] = 0
        
        # 가중치 재조정
        total_perf = sum(max(p, 0.1) for p in avg_performances.values())
        if total_perf > 0:
            for name in self.weights:
                if name in avg_performances:
                    self.weights[name] = max(avg_performances[name], 0.1) / total_perf
        
        # 가중치 정규화
        weight_sum = sum(self.weights.values())
        for name in self.weights:
            self.weights[name] /= weight_sum
        
        logger.info(f"Updated weights: {self.weights}")
    
    def train_dqn(self, state: np.ndarray, action: int, reward: float,
                  next_state: np.ndarray, done: bool):
        """DQN 에이전트 학습"""
        self.dqn_agent.remember(state, action, reward, next_state, done)
        loss = self.dqn_agent.replay()
        
        if loss is not None:
            logger.debug(f"DQN training loss: {loss:.4f}")
    
    def get_ensemble_stats(self) -> Dict:
        """앙상블 통계 정보"""
        return {
            'current_weights': self.weights.copy(),
            'agent_performance': {
                name: {
                    'mean': np.mean(perfs) if perfs else 0,
                    'std': np.std(perfs) if perfs else 0,
                    'count': len(perfs)
                }
                for name, perfs in self.agent_performance.items()
            },
            'dqn_epsilon': self.dqn_agent.epsilon
        }