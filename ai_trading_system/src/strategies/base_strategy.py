#!/usr/bin/env python3
"""
기본 전략 추상 클래스
모든 거래 전략의 기본 인터페이스
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import pandas as pd
import numpy as np
import logging

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ai_trading_system.src.core.events import SignalEvent

logger = logging.getLogger('strategy')

class BaseStrategy(ABC):
    """기본 전략 클래스"""
    
    def __init__(self, name: str, symbols: List[str]):
        """초기화
        
        Args:
            name: 전략 이름
            symbols: 대상 종목 리스트
        """
        self.name = name
        self.symbols = symbols
        self.positions = {symbol: 0 for symbol in symbols}  # 현재 포지션
        self.is_active = True
        
        logger.info(f"전략 초기화: {name}, 대상 종목: {symbols}")
    
    @abstractmethod
    def calculate_signals(self, data: pd.DataFrame) -> List[SignalEvent]:
        """거래 신호 계산
        
        Args:
            data: 시장 데이터
            
        Returns:
            거래 신호 리스트
        """
        raise NotImplementedError("calculate_signals 메서드를 구현해야 합니다")
    
    def update_position(self, symbol: str, quantity: int):
        """포지션 업데이트
        
        Args:
            symbol: 종목 코드
            quantity: 수량 변화 (양수: 매수, 음수: 매도)
        """
        if symbol in self.positions:
            self.positions[symbol] += quantity
            logger.debug(f"포지션 업데이트: {symbol} {self.positions[symbol]}")
    
    def get_position(self, symbol: str) -> int:
        """현재 포지션 조회
        
        Args:
            symbol: 종목 코드
            
        Returns:
            현재 포지션 수량
        """
        return self.positions.get(symbol, 0)
    
    def activate(self):
        """전략 활성화"""
        self.is_active = True
        logger.info(f"전략 활성화: {self.name}")
    
    def deactivate(self):
        """전략 비활성화"""
        self.is_active = False
        logger.info(f"전략 비활성화: {self.name}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """성과 지표 계산"""
        return {
            'strategy_name': self.name,
            'symbols': self.symbols,
            'positions': self.positions.copy(),
            'is_active': self.is_active
        }

    @staticmethod
    def calculate_sma(prices: pd.Series, window: int) -> pd.Series:
        """단순이동평균 계산"""
        return prices.rolling(window=window).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, window: int) -> pd.Series:
        """지수이동평균 계산"""
        return prices.ewm(span=window, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
        """RSI 계산"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: float = 2.0) -> Dict[str, pd.Series]:
        """볼린저 밴드 계산"""
        sma = prices.rolling(window=window).mean()
        std = prices.rolling(window=window).std()
        
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        
        return {
            'upper': upper,
            'middle': sma,
            'lower': lower
        }