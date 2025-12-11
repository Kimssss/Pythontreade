#!/usr/bin/env python3
"""
이벤트 클래스 정의
백테스팅 및 실시간 거래를 위한 이벤트 시스템
"""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional

class EventType(Enum):
    """이벤트 타입"""
    MARKET = "MARKET"      # 시장 데이터 이벤트
    SIGNAL = "SIGNAL"      # 거래 신호 이벤트
    ORDER = "ORDER"        # 주문 이벤트
    FILL = "FILL"         # 체결 이벤트

class Event:
    """기본 이벤트 클래스"""
    def __init__(self, event_type: EventType, timestamp: Optional[datetime] = None):
        self.type = event_type
        self.timestamp = timestamp or datetime.now()

class MarketEvent(Event):
    """시장 데이터 이벤트"""
    def __init__(self, symbol: str, data: Dict[str, Any], timestamp: Optional[datetime] = None):
        super().__init__(EventType.MARKET, timestamp)
        self.symbol = symbol
        self.data = data

class SignalEvent(Event):
    """거래 신호 이벤트"""
    def __init__(self, symbol: str, signal_type: str, strength: float = 1.0, 
                 timestamp: Optional[datetime] = None, strategy_name: str = ""):
        super().__init__(EventType.SIGNAL, timestamp)
        self.symbol = symbol
        self.signal_type = signal_type  # LONG, SHORT, EXIT
        self.strength = strength        # 신호 강도 (0.0 ~ 1.0)
        self.strategy_name = strategy_name

class OrderEvent(Event):
    """주문 이벤트"""
    def __init__(self, symbol: str, order_type: str, quantity: int, 
                 price: Optional[float] = None, timestamp: Optional[datetime] = None):
        super().__init__(EventType.ORDER, timestamp)
        self.symbol = symbol
        self.order_type = order_type    # BUY, SELL
        self.quantity = quantity
        self.price = price              # None이면 시장가

class FillEvent(Event):
    """체결 이벤트"""
    def __init__(self, symbol: str, quantity: int, fill_price: float, 
                 commission: float = 0.0, timestamp: Optional[datetime] = None):
        super().__init__(EventType.FILL, timestamp)
        self.symbol = symbol
        self.quantity = quantity
        self.fill_price = fill_price
        self.commission = commission