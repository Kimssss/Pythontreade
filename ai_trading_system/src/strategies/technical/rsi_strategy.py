#!/usr/bin/env python3
"""
RSI 전략
과매수/과매도 구간 기반 거래
"""

import pandas as pd
import numpy as np
from typing import List
import logging

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from ai_trading_system.src.strategies.base_strategy import BaseStrategy
from ai_trading_system.src.core.events import SignalEvent

logger = logging.getLogger('rsi_strategy')

class RSIStrategy(BaseStrategy):
    """RSI 전략"""
    
    def __init__(self, symbols: List[str], period: int = 14, overbought: float = 70, oversold: float = 30):
        """초기화
        
        Args:
            symbols: 대상 종목
            period: RSI 계산 기간
            overbought: 과매수 기준선
            oversold: 과매도 기준선
        """
        super().__init__("RSI", symbols)
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
        
        # 이전 RSI 저장
        self.prev_rsi = {symbol: None for symbol in symbols}
    
    def calculate_signals(self, data: pd.DataFrame) -> List[SignalEvent]:
        """거래 신호 계산"""
        signals = []
        
        if len(data) < self.period + 1:
            return signals
        
        for symbol in self.symbols:
            try:
                # 종목별 데이터 확인
                close_col = f"{symbol}_close" if f"{symbol}_close" in data.columns else "close"
                if close_col not in data.columns:
                    continue
                
                close = data[close_col].dropna()
                if len(close) < self.period + 1:
                    continue
                
                # RSI 계산
                rsi = self.calculate_rsi(close, self.period)
                
                if len(rsi) >= 2:
                    prev_rsi = rsi.iloc[-2]
                    curr_rsi = rsi.iloc[-1]
                    
                    # 과매도에서 반등 (매수 신호)
                    if prev_rsi < self.oversold and curr_rsi >= self.oversold:
                        signals.append(SignalEvent(
                            symbol=symbol,
                            signal_type="LONG",
                            strength=min(1.0, (self.oversold - prev_rsi) / 10),
                            strategy_name=self.name
                        ))
                    
                    # 과매수에서 하락 (매도 신호)
                    elif prev_rsi > self.overbought and curr_rsi <= self.overbought:
                        if self.get_position(symbol) > 0:
                            signals.append(SignalEvent(
                                symbol=symbol,
                                signal_type="EXIT",
                                strength=min(1.0, (prev_rsi - self.overbought) / 10),
                                strategy_name=self.name
                            ))
                    
                    self.prev_rsi[symbol] = curr_rsi
                    
            except Exception as e:
                logger.error(f"RSI 신호 계산 오류 ({symbol}): {e}")
        
        return signals