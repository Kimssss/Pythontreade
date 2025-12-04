#!/usr/bin/env python3
"""
팩터 분석 에이전트 - 백테스팅용 단순화 버전
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger('factor_agent')

class FactorAgent:
    """팩터 분석 에이전트"""
    
    def __init__(self):
        self.name = "FactorAgent"
        
    async def analyze_stock(self, stock_info: Dict, price_data: pd.DataFrame) -> Dict[str, Any]:
        """주식 팩터 분석
        
        Args:
            stock_info: 주식 정보
            price_data: OHLCV 데이터
            
        Returns:
            분석 결과 딕셔너리
        """
        try:
            if len(price_data) < 10:
                return {'신호: 0, 'confidence': 0}
                
            # 가격 및 거래량 팩터
            current_price = price_data.iloc[-1]['close']
            volume = price_data.iloc[-1]['volume']
            
            # 모멘텀 팩터 (단순화)
            momentum_factor = self._calculate_momentum(price_data)
            
            # 볼륨 팩터
            volume_factor = self._calculate_volume_factor(price_data)
            
            # 가격 팩터 (시가총액 기준)
            price_factor = self._calculate_price_factor(stock_info)
            
            # 변동성 팩터
            volatility_factor = self._calculate_volatility_factor(price_data)
            
            # 신호 통합 (가중평균)
            signal = (
                momentum_factor * 0.4 +
                volume_factor * 0.3 +
                price_factor * 0.2 +
                volatility_factor * 0.1
            )
            
            # 신호 정규화
            signal = max(-1, min(1, signal))
            
            return {
                '신호: signal,
                'confidence': abs(signal),
                'factors': {
                    'momentum': momentum_factor,
                    'volume': volume_factor,
                    'price': price_factor,
                    'volatility': volatility_factor
                }
            }
            
        except Exception as e:
            logger.error(f"팩터 분석 중 오류: {e}")
            return {'신호: 0, 'confidence': 0}
            
    def _calculate_momentum(self, price_data: pd.DataFrame) -> float:
        """모멘텀 팩터 계산"""
        if len(price_data) < 10:
            return 0
            
        closes = price_data['close'].values
        
        # 단기 모멘텀 (5일)
        short_momentum = (closes[-1] - closes[-6]) / closes[-6] if len(closes) > 5 else 0
        
        # 중기 모멘텀 (20일)
        long_momentum = (closes[-1] - closes[-21]) / closes[-21] if len(closes) > 20 else 0
        
        # 가중 모멘텀
        momentum = short_momentum * 0.6 + long_momentum * 0.4
        
        # 정규화 (-1 ~ 1)
        return max(-1, min(1, momentum * 10))  # 10배 확대
        
    def _calculate_volume_factor(self, price_data: pd.DataFrame) -> float:
        """거래량 팩터 계산"""
        if len(price_data) < 10:
            return 0
            
        volumes = price_data['volume'].values
        
        # 평균 거래량 대비 현재 거래량
        avg_volume = np.mean(volumes[-10:])
        current_volume = volumes[-1]
        
        if avg_volume == 0:
            return 0
            
        volume_ratio = current_volume / avg_volume
        
        # 거래량 증가 시 긍정적 신호
        if volume_ratio > 1.5:
            return 0.5
        elif volume_ratio > 1.2:
            return 0.3
        elif volume_ratio < 0.5:
            return -0.3
        else:
            return 0
            
    def _calculate_price_factor(self, stock_info: Dict) -> float:
        """가격 팩터 계산"""
        try:
            market_cap = stock_info.get('market_cap', 0)
            price = stock_info.get('price', 0)
            
            # 시가총액 기준 팩터 (대형주 선호)
            if market_cap > 1000000:  # 1조원 이상
                cap_factor = 0.3
            elif market_cap > 100000:  # 1000억원 이상
                cap_factor = 0.1
            else:
                cap_factor = -0.1
                
            # 가격 팩터 (적정 가격대 선호)
            if 10000 <= price <= 100000:  # 1만원 ~ 10만원
                price_factor = 0.2
            else:
                price_factor = -0.1
                
            return cap_factor + price_factor
            
        except:
            return 0
            
    def _calculate_volatility_factor(self, price_data: pd.DataFrame) -> float:
        """변동성 팩터 계산"""
        if len(price_data) < 10:
            return 0
            
        closes = price_data['close'].values
        returns = np.diff(closes) / closes[:-1]
        
        volatility = np.std(returns)
        
        # 적절한 변동성 선호 (너무 높거나 낮으면 불리)
        if 0.01 <= volatility <= 0.03:  # 1%~3% 일간 변동성
            return 0.2
        elif volatility > 0.05:  # 5% 이상 고변동성
            return -0.3
        else:
            return 0