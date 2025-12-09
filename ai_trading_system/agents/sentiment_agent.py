#!/usr/bin/env python3
"""
감성 분석 에이전트 (앙상블 시스템 통합)
뉴스 감성 기반 매매 신호 생성
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from analysis.sentiment_analyzer import SentimentAgent as CoreSentimentAgent

logger = logging.getLogger('ai_trading.agents.sentiment')


class SentimentAgent:
    """감성 분석 에이전트 - 앙상블 시스템용"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.core_agent = CoreSentimentAgent()
        
        # 설정
        self.weight = self.config.get('weight', 0.15)  # 앙상블 가중치
        self.min_confidence = self.config.get('min_confidence', 0.3)
        self.signal_threshold = self.config.get('signal_threshold', 0.4)
        
        # 상태 추적
        self.last_signals = {}
        self.signal_history = []
        
        logger.info("Sentiment Agent initialized for ensemble system")
    
    async def analyze(self, stock_code: str, market_data: pd.DataFrame) -> Dict:
        """감성 분석 수행"""
        try:
            current_price = market_data['close'].iloc[-1] if not market_data.empty else 0.0
            
            # 핵심 감성 분석 수행
            sentiment_signal = await self.core_agent.get_trading_signal(stock_code, current_price)
            
            # 시장 데이터와 결합한 분석
            enhanced_signal = self._enhance_with_market_data(sentiment_signal, market_data)
            
            # 신호 히스토리 업데이트
            self._update_signal_history(stock_code, enhanced_signal)
            
            return enhanced_signal
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed for {stock_code}: {e}")
            return self._get_default_signal()
    
    def _enhance_with_market_data(self, sentiment_signal: Dict, market_data: pd.DataFrame) -> Dict:
        """시장 데이터로 감성 신호 강화"""
        try:
            if market_data.empty:
                return sentiment_signal
            
            # 기본 감성 신호
            base_action = sentiment_signal.get('action', 'hold')
            base_confidence = sentiment_signal.get('confidence', 0.0)
            sentiment_score = sentiment_signal.get('sentiment_score', 0.0)
            
            # 시장 데이터 기반 보정
            price_momentum = self._calculate_price_momentum(market_data)
            volume_confirmation = self._check_volume_confirmation(market_data)
            volatility_factor = self._calculate_volatility_factor(market_data)
            
            # 신호 강도 조정
            adjusted_confidence = base_confidence
            
            # 가격 모멘텀과 감성이 일치하는 경우 신뢰도 증가
            if (sentiment_score > 0 and price_momentum > 0) or (sentiment_score < 0 and price_momentum < 0):
                adjusted_confidence *= 1.2
            
            # 거래량 확인
            if volume_confirmation:
                adjusted_confidence *= 1.1
            
            # 변동성이 높으면 신뢰도 감소
            adjusted_confidence *= (1.0 - volatility_factor * 0.3)
            
            # 최종 조정
            adjusted_confidence = max(0.0, min(1.0, adjusted_confidence))
            
            # 최종 액션 결정
            final_action = base_action
            if adjusted_confidence < self.min_confidence:
                final_action = 'hold'
            
            return {
                'action': final_action,
                'confidence': adjusted_confidence,
                'sentiment_score': sentiment_score,
                'market_sentiment': sentiment_signal.get('market_sentiment', {}),
                'stock_sentiment': sentiment_signal.get('stock_sentiment', {}),
                'market_factors': {
                    'price_momentum': price_momentum,
                    'volume_confirmation': volume_confirmation,
                    'volatility_factor': volatility_factor
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Signal enhancement failed: {e}")
            return sentiment_signal
    
    def _calculate_price_momentum(self, market_data: pd.DataFrame) -> float:
        """가격 모멘텀 계산"""
        try:
            if len(market_data) < 5:
                return 0.0
            
            # 최근 5일 평균 대비 현재 가격
            recent_avg = market_data['close'].tail(5).mean()
            current_price = market_data['close'].iloc[-1]
            
            momentum = (current_price - recent_avg) / recent_avg
            return np.clip(momentum * 10, -1.0, 1.0)  # -1 ~ 1 범위로 정규화
            
        except Exception:
            return 0.0
    
    def _check_volume_confirmation(self, market_data: pd.DataFrame) -> bool:
        """거래량 확인"""
        try:
            if len(market_data) < 10:
                return False
            
            # 최근 거래량이 평균 대비 높은지 확인
            recent_volume = market_data['volume'].iloc[-1]
            avg_volume = market_data['volume'].tail(10).mean()
            
            return recent_volume > avg_volume * 1.2
            
        except Exception:
            return False
    
    def _calculate_volatility_factor(self, market_data: pd.DataFrame) -> float:
        """변동성 팩터 계산"""
        try:
            if len(market_data) < 10:
                return 0.0
            
            # 최근 10일 수익률 변동성
            returns = market_data['close'].tail(10).pct_change().dropna()
            volatility = returns.std()
            
            # 0 ~ 1 범위로 정규화 (높은 변동성 = 1에 가까움)
            return min(volatility * 20, 1.0)
            
        except Exception:
            return 0.0
    
    def _update_signal_history(self, stock_code: str, signal: Dict):
        """신호 히스토리 업데이트"""
        try:
            self.last_signals[stock_code] = signal
            
            # 히스토리 저장 (최근 100개만)
            self.signal_history.append({
                'stock_code': stock_code,
                'timestamp': datetime.now(),
                'action': signal['action'],
                'confidence': signal['confidence'],
                'sentiment_score': signal['sentiment_score']
            })
            
            if len(self.signal_history) > 100:
                self.signal_history = self.signal_history[-100:]
                
        except Exception as e:
            logger.error(f"Signal history update failed: {e}")
    
    def _get_default_signal(self) -> Dict:
        """기본 신호 반환"""
        return {
            'action': 'hold',
            'confidence': 0.0,
            'sentiment_score': 0.0,
            'market_sentiment': {},
            'stock_sentiment': {},
            'market_factors': {},
            'timestamp': datetime.now().isoformat()
        }
    
    def get_signal_summary(self) -> Dict:
        """신호 요약 정보"""
        try:
            if not self.signal_history:
                return {'총_신호수': 0, '평균_신뢰도': 0.0, '액션_분포': {}}
            
            recent_signals = self.signal_history[-20:]  # 최근 20개
            
            actions = [s['action'] for s in recent_signals]
            confidences = [s['confidence'] for s in recent_signals]
            
            action_counts = {}
            for action in actions:
                action_counts[action] = action_counts.get(action, 0) + 1
            
            return {
                '총_신호수': len(self.signal_history),
                '최근_신호수': len(recent_signals),
                '평균_신뢰도': np.mean(confidences) if confidences else 0.0,
                '액션_분포': action_counts,
                '마지막_업데이트': self.signal_history[-1]['timestamp'].isoformat() if self.signal_history else None
            }
            
        except Exception as e:
            logger.error(f"Signal summary failed: {e}")
            return {'오류': str(e)}
    
    async def batch_analyze(self, stock_codes: List[str], market_data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """여러 종목 일괄 분석"""
        results = {}
        
        try:
            # 동시 분석 (최대 5개씩)
            tasks = []
            for stock_code in stock_codes[:5]:  # 성능을 위해 5개로 제한
                market_data = market_data_dict.get(stock_code, pd.DataFrame())
                task = self.analyze(stock_code, market_data)
                tasks.append((stock_code, task))
            
            # 결과 수집
            for stock_code, task in tasks:
                try:
                    result = await task
                    results[stock_code] = result
                except Exception as e:
                    logger.error(f"Batch analysis failed for {stock_code}: {e}")
                    results[stock_code] = self._get_default_signal()
            
            logger.info(f"Batch sentiment analysis completed: {len(results)} stocks")
            return results
            
        except Exception as e:
            logger.error(f"Batch sentiment analysis failed: {e}")
            return {}


# 감성 에이전트 팩토리
def create_sentiment_agent(config: Dict = None) -> SentimentAgent:
    """감성 에이전트 생성"""
    return SentimentAgent(config)


if __name__ == "__main__":
    async def test_sentiment_agent():
        """감성 에이전트 테스트"""
        print("🤖 감성 에이전트 테스트 시작")
        
        # 테스트 설정
        config = {
            'weight': 0.15,
            'min_confidence': 0.3,
            'signal_threshold': 0.4
        }
        
        # 에이전트 생성
        agent = SentimentAgent(config)
        
        # 테스트 데이터 생성
        test_data = pd.DataFrame({
            'close': [75000, 75500, 76000, 75800, 76200],
            'volume': [1000000, 1200000, 900000, 1100000, 1300000]
        })
        
        # 단일 종목 분석
        print("\n📊 단일 종목 감성 분석:")
        result = await agent.analyze("005930", test_data)  # 삼성전자
        print(f"액션: {result['action']}")
        print(f"신뢰도: {result['confidence']:.3f}")
        print(f"감성점수: {result['sentiment_score']:.3f}")
        
        # 배치 분석
        print("\n📊 배치 감성 분석:")
        stock_codes = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
        market_data_dict = {code: test_data for code in stock_codes}
        
        batch_results = await agent.batch_analyze(stock_codes, market_data_dict)
        
        for stock_code, result in batch_results.items():
            print(f"{stock_code}: {result['action']} (신뢰도: {result['confidence']:.3f})")
        
        # 신호 요약
        print("\n📈 신호 요약:")
        summary = agent.get_signal_summary()
        for key, value in summary.items():
            print(f"{key}: {value}")
        
        print("\n✅ 감성 에이전트 테스트 완료")
    
    # 테스트 실행
    asyncio.run(test_sentiment_agent())