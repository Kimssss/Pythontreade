#!/usr/bin/env python3
"""
기술적 분석 에이전트 - 백테스팅용 단순화 버전
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger('technical_agent')

class TechnicalAgent:
    """기술적 분석 에이전트"""
    
    def __init__(self):
        self.name = "TechnicalAgent"
        
    async def analyze_stock(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """주식 기술적 분석
        
        Args:
            price_data: OHLCV 데이터
            
        Returns:
            분석 결과 딕셔너리
        """
        try:
            if len(price_data) < 20:
                return {'신호': 0, 'confidence': 0}
                
            closes = price_data['close'].values
            
            # 단순 이동평균
            sma_5 = np.mean(closes[-5:])
            sma_20 = np.mean(closes[-20:])
            
            # RSI 계산 (단순화)
            rsi = self._calculate_rsi(closes, 14)
            
            # MACD 계산 (단순화)
            macd_signal = self._calculate_macd_signal(closes)
            
            # 신호 생성
            signal = 0
            
            # 이동평균 신호
            if sma_5 > sma_20:
                signal += 0.3
            else:
                signal -= 0.3
                
            # RSI 신호
            if rsi < 30:  # 과매도
                signal += 0.4
            elif rsi > 70:  # 과매수
                signal -= 0.4
                
            # MACD 신호
            signal += macd_signal * 0.3
            
            # 신호 정규화 (-1 ~ 1)
            signal = max(-1, min(1, signal))
            
            return {
                '신호': signal,
                'confidence': abs(signal),
                'indicators': {
                    'sma_5': sma_5,
                    'sma_20': sma_20,
                    'rsi': rsi,
                    'macd_signal': macd_signal
                }
            }
            
        except Exception as e:
            logger.error(f"기술적 분석 중 오류: {e}")
            return {'신호': 0, 'confidence': 0}
            
    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """RSI 계산"""
        if len(prices) < period + 1:
            return 50
            
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100
            
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
        
    def _calculate_macd_signal(self, prices: np.ndarray) -> float:
        """MACD 신호 계산 (단순화)"""
        if len(prices) < 26:
            return 0
            
        ema_12 = self._ema(prices, 12)
        ema_26 = self._ema(prices, 26)
        
        macd = ema_12 - ema_26
        
        # 단순 MACD 신호 (0 위/아래)
        return 1 if macd > 0 else -1
        
    def _ema(self, prices: np.ndarray, period: int) -> float:
        """지수 이동평균 계산"""
        if len(prices) < period:
            return np.mean(prices)
            
        alpha = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = alpha * price + (1 - alpha) * ema
            
        return ema