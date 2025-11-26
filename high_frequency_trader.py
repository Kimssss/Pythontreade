#!/usr/bin/env python3
"""
고빈도 거래 전략 (High Frequency Trading)
- 마이크로초 단위 거래
- 호가창 분석
- 시장 미시구조 활용
"""

import time
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import threading
import queue
from dataclasses import dataclass
import logging

from kis_api_enhanced import KisAPIEnhanced as KisAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class OrderBookSnapshot:
    """호가창 스냅샷"""
    timestamp: datetime
    stock_code: str
    bid_prices: List[int]
    bid_quantities: List[int]
    ask_prices: List[int]
    ask_quantities: List[int]
    last_price: int
    volume: int

@dataclass
class TradeSignal:
    """거래 신호"""
    timestamp: datetime
    stock_code: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    expected_profit: float
    risk_level: float

class OrderBookAnalyzer:
    """
    호가창 분석기
    - 호가 불균형 탐지
    - 스프레드 분석
    - 거래량 패턴 분석
    """
    
    def __init__(self):
        self.order_book_history = []
        self.max_history_size = 100
        
    def analyze_order_book(self, order_book: OrderBookSnapshot) -> Dict[str, float]:
        """호가창 분석 수행"""
        analysis = {}
        
        # 1. 호가 불균형 (Order Book Imbalance)
        bid_volume = sum(order_book.bid_quantities[:5])  # 상위 5호가
        ask_volume = sum(order_book.ask_quantities[:5])
        total_volume = bid_volume + ask_volume
        
        if total_volume > 0:
            analysis['bid_ask_imbalance'] = (bid_volume - ask_volume) / total_volume
        else:
            analysis['bid_ask_imbalance'] = 0
        
        # 2. 스프레드 분석
        if order_book.bid_prices and order_book.ask_prices:
            best_bid = max(order_book.bid_prices)
            best_ask = min(order_book.ask_prices)
            analysis['spread'] = best_ask - best_bid
            analysis['spread_pct'] = (best_ask - best_bid) / best_bid if best_bid > 0 else 0
        else:
            analysis['spread'] = 0
            analysis['spread_pct'] = 0
        
        # 3. 호가 깊이 (Market Depth)
        analysis['bid_depth'] = len([p for p in order_book.bid_prices if p > 0])
        analysis['ask_depth'] = len([p for p in order_book.ask_prices if p > 0])
        
        # 4. 가격 압력 (Price Pressure)
        if len(self.order_book_history) > 1:
            prev_book = self.order_book_history[-1]
            
            # 상위 호가 변화량 분석
            bid_pressure = 0
            ask_pressure = 0
            
            for i in range(min(3, len(order_book.bid_quantities))):
                if i < len(prev_book.bid_quantities):
                    bid_pressure += order_book.bid_quantities[i] - prev_book.bid_quantities[i]
            
            for i in range(min(3, len(order_book.ask_quantities))):
                if i < len(prev_book.ask_quantities):
                    ask_pressure += order_book.ask_quantities[i] - prev_book.ask_quantities[i]
            
            analysis['bid_pressure'] = bid_pressure
            analysis['ask_pressure'] = ask_pressure
        else:
            analysis['bid_pressure'] = 0
            analysis['ask_pressure'] = 0
        
        # 5. 거래 모멘텀
        if len(self.order_book_history) >= 5:
            recent_volumes = [book.volume for book in self.order_book_history[-5:]]
            analysis['volume_momentum'] = (recent_volumes[-1] - recent_volumes[0]) / len(recent_volumes)
        else:
            analysis['volume_momentum'] = 0
        
        # 히스토리에 추가
        self.order_book_history.append(order_book)
        if len(self.order_book_history) > self.max_history_size:
            self.order_book_history.pop(0)
        
        return analysis
    
    def detect_liquidity_events(self, analysis: Dict[str, float]) -> List[str]:
        """유동성 이벤트 탐지"""
        events = []
        
        # 대량 호가 불균형
        if abs(analysis['bid_ask_imbalance']) > 0.7:
            direction = "매수" if analysis['bid_ask_imbalance'] > 0 else "매도"
            events.append(f"대량_{direction}_호가_불균형")
        
        # 스프레드 확대
        if analysis['spread_pct'] > 0.005:  # 0.5% 이상
            events.append("스프레드_확대")
        
        # 급격한 거래량 증가
        if analysis['volume_momentum'] > 1000:
            events.append("거래량_급증")
        
        # 호가 깊이 감소 (유동성 부족)
        if analysis['bid_depth'] + analysis['ask_depth'] < 5:
            events.append("유동성_부족")
        
        return events

class MicrostructureStrategy:
    """
    시장 미시구조 기반 고빈도 거래 전략
    """
    
    def __init__(self):
        self.position_limit = 1000  # 최대 포지션 (주)
        self.risk_limit = 0.001     # 최대 리스크 (0.1%)
        self.min_profit_threshold = 0.0005  # 최소 수익 기준 (0.05%)
        
    def generate_signal(self, 
                       stock_code: str,
                       order_book_analysis: Dict[str, float],
                       current_price: float,
                       events: List[str]) -> Optional[TradeSignal]:
        """거래 신호 생성"""
        
        signal_strength = 0
        signal_type = "HOLD"
        
        # 1. 호가 불균형 기반 신호
        imbalance = order_book_analysis['bid_ask_imbalance']
        if imbalance > 0.3:  # 매수 우세
            signal_strength += imbalance * 0.4
            signal_type = "BUY"
        elif imbalance < -0.3:  # 매도 우세
            signal_strength += abs(imbalance) * 0.4
            signal_type = "SELL"
        
        # 2. 스프레드 기반 신호 (스프레드가 좁을 때 거래)
        spread_pct = order_book_analysis['spread_pct']
        if spread_pct < 0.002:  # 0.2% 미만
            signal_strength += 0.3
        
        # 3. 거래량 모멘텀
        volume_momentum = order_book_analysis['volume_momentum']
        if volume_momentum > 500:
            signal_strength += 0.2
        
        # 4. 이벤트 기반 가중치
        for event in events:
            if "대량_매수_호가_불균형" in event and signal_type != "SELL":
                signal_strength += 0.3
                signal_type = "BUY"
            elif "대량_매도_호가_불균형" in event and signal_type != "BUY":
                signal_strength += 0.3
                signal_type = "SELL"
            elif "거래량_급증" in event:
                signal_strength += 0.2
        
        # 신호 강도가 임계값 이상일 때만 거래
        if signal_strength > 0.5 and signal_type != "HOLD":
            
            # 예상 수익 계산 (매우 보수적)
            expected_profit = signal_strength * self.min_profit_threshold
            
            # 리스크 레벨 계산
            risk_level = spread_pct + (1 - signal_strength) * 0.001
            
            return TradeSignal(
                timestamp=datetime.now(),
                stock_code=stock_code,
                signal_type=signal_type,
                confidence=signal_strength,
                expected_profit=expected_profit,
                risk_level=risk_level
            )
        
        return None
    
    def calculate_position_size(self, signal: TradeSignal, available_cash: float, current_price: float) -> int:
        """포지션 크기 계산"""
        if signal.risk_level <= 0:
            return 0
        
        # Kelly Criterion 기반 사이징 (매우 보수적)
        win_prob = signal.confidence
        win_loss_ratio = signal.expected_profit / signal.risk_level
        
        kelly_fraction = (win_prob * win_loss_ratio - (1 - win_prob)) / win_loss_ratio
        kelly_fraction = max(0, min(0.1, kelly_fraction))  # 최대 10%로 제한
        
        max_position_value = available_cash * kelly_fraction
        quantity = int(max_position_value / current_price)
        
        # 절대 포지션 제한
        return min(quantity, self.position_limit)

class HighFrequencyTrader:
    """
    고빈도 거래 시스템
    """
    
    def __init__(self, kis_api: KisAPI, target_stocks: List[str]):
        self.kis_api = kis_api
        self.target_stocks = target_stocks
        
        self.order_book_analyzer = OrderBookAnalyzer()
        self.strategy = MicrostructureStrategy()
        
        # 실시간 데이터 큐
        self.data_queue = queue.Queue(maxsize=1000)
        self.is_running = False
        
        # 포지션 추적
        self.positions = {stock: 0 for stock in target_stocks}
        self.last_trade_time = {stock: None for stock in target_stocks}
        
        # 최소 거래 간격 (초)
        self.min_trade_interval = 1
        
    def get_order_book_snapshot(self, stock_code: str) -> Optional[OrderBookSnapshot]:
        """호가창 스냅샷 가져오기"""
        try:
            # 한국투자증권 API로 호가 정보 조회
            orderbook_data = self.kis_api.get_orderbook(stock_code)
            if not orderbook_data or orderbook_data.get('rt_cd') != '0':
                return None
            
            output = orderbook_data['output']
            
            # 매수/매도 호가 파싱
            bid_prices = []
            bid_quantities = []
            ask_prices = []
            ask_quantities = []
            
            for i in range(1, 11):  # 10호가
                # 매수 호가
                bid_price = int(output.get(f'bidp{i:02d}', 0))
                bid_qty = int(output.get(f'bidp_rsqn{i:02d}', 0))
                if bid_price > 0:
                    bid_prices.append(bid_price)
                    bid_quantities.append(bid_qty)
                
                # 매도 호가
                ask_price = int(output.get(f'askp{i:02d}', 0))
                ask_qty = int(output.get(f'askp_rsqn{i:02d}', 0))
                if ask_price > 0:
                    ask_prices.append(ask_price)
                    ask_quantities.append(ask_qty)
            
            return OrderBookSnapshot(
                timestamp=datetime.now(),
                stock_code=stock_code,
                bid_prices=bid_prices,
                bid_quantities=bid_quantities,
                ask_prices=ask_prices,
                ask_quantities=ask_quantities,
                last_price=int(output.get('last_price', 0)),
                volume=int(output.get('total_volume', 0))
            )
            
        except Exception as e:
            logger.error(f"호가창 조회 오류 ({stock_code}): {e}")
            return None
    
    def process_market_data(self, stock_code: str):
        """시장 데이터 처리 및 거래 결정"""
        try:
            # 호가창 스냅샷 가져오기
            order_book = self.get_order_book_snapshot(stock_code)
            if not order_book:
                return
            
            # 호가창 분석
            analysis = self.order_book_analyzer.analyze_order_book(order_book)
            events = self.order_book_analyzer.detect_liquidity_events(analysis)
            
            # 거래 신호 생성
            signal = self.strategy.generate_signal(
                stock_code, analysis, order_book.last_price, events
            )
            
            if signal:
                logger.info(f"신호 생성: {stock_code} {signal.signal_type} "
                          f"(신뢰도: {signal.confidence:.3f})")
                
                # 거래 실행
                self.execute_trade(signal, order_book.last_price)
            
        except Exception as e:
            logger.error(f"시장 데이터 처리 오류 ({stock_code}): {e}")
    
    def execute_trade(self, signal: TradeSignal, current_price: float):
        """거래 실행"""
        stock_code = signal.stock_code
        
        # 최소 거래 간격 체크
        if (self.last_trade_time[stock_code] and 
            (datetime.now() - self.last_trade_time[stock_code]).seconds < self.min_trade_interval):
            return
        
        try:
            # 사용 가능 현금 조회
            available_cash = self.kis_api.get_available_cash()
            if available_cash <= 0:
                return
            
            # 포지션 크기 계산
            quantity = self.strategy.calculate_position_size(signal, available_cash, current_price)
            
            if quantity <= 0:
                return
            
            # 거래 실행
            if signal.signal_type == "BUY":
                # 현재 포지션이 너무 크면 매수 제한
                if self.positions[stock_code] > self.strategy.position_limit:
                    return
                
                result = self.kis_api.buy_stock(stock_code, quantity, order_type="03")  # 시장가
                if result and result.get('rt_cd') == '0':
                    self.positions[stock_code] += quantity
                    self.last_trade_time[stock_code] = datetime.now()
                    logger.info(f"매수 실행: {stock_code} {quantity}주 @ {current_price:,}원")
            
            elif signal.signal_type == "SELL":
                # 매도할 수량 확인
                sell_quantity = min(quantity, max(0, self.positions[stock_code]))
                if sell_quantity <= 0:
                    return
                
                result = self.kis_api.sell_stock(stock_code, sell_quantity, order_type="03")
                if result and result.get('rt_cd') == '0':
                    self.positions[stock_code] -= sell_quantity
                    self.last_trade_time[stock_code] = datetime.now()
                    logger.info(f"매도 실행: {stock_code} {sell_quantity}주 @ {current_price:,}원")
            
        except Exception as e:
            logger.error(f"거래 실행 오류 ({stock_code}): {e}")
    
    def start_trading(self, update_interval: float = 0.5):
        """고빈도 거래 시작"""
        logger.info("고빈도 거래 시작")
        logger.info(f"대상 종목: {self.target_stocks}")
        logger.info(f"업데이트 간격: {update_interval}초")
        
        self.is_running = True
        
        try:
            while self.is_running:
                start_time = time.time()
                
                # 각 종목에 대해 병렬 처리
                threads = []
                for stock_code in self.target_stocks:
                    thread = threading.Thread(
                        target=self.process_market_data,
                        args=(stock_code,)
                    )
                    thread.start()
                    threads.append(thread)
                
                # 모든 스레드 완료 대기
                for thread in threads:
                    thread.join(timeout=update_interval/2)
                
                # 주기 조절
                elapsed = time.time() - start_time
                if elapsed < update_interval:
                    time.sleep(update_interval - elapsed)
                
        except KeyboardInterrupt:
            logger.info("거래 중단 요청")
        finally:
            self.is_running = False
            logger.info("고빈도 거래 종료")
    
    def stop_trading(self):
        """거래 중단"""
        self.is_running = False
        logger.info("거래 중단")
    
    def get_performance_summary(self) -> Dict[str, float]:
        """성과 요약"""
        total_position_value = 0
        
        for stock_code, position in self.positions.items():
            if position != 0:
                try:
                    price_data = self.kis_api.get_stock_price(stock_code)
                    if price_data and price_data.get('rt_cd') == '0':
                        current_price = int(price_data['output']['stck_prpr'])
                        total_position_value += position * current_price
                except:
                    pass
        
        return {
            'total_positions': len([p for p in self.positions.values() if p != 0]),
            'total_position_value': total_position_value,
            'positions': self.positions.copy()
        }

def main():
    """메인 실행 함수"""
    print("🚀 고빈도 거래 시스템 v1.0")
    print("=" * 50)
    
    # 주의사항 안내
    print("⚠️ 주의사항:")
    print("- 고빈도 거래는 높은 리스크를 수반합니다")
    print("- 데모 모드에서 충분한 테스트 후 사용하세요")
    print("- 시장 상황에 따라 큰 손실이 발생할 수 있습니다")
    print()
    
    # 사용자 동의 확인
    agreement = input("위험을 이해하고 계속하시겠습니까? (yes/no): ").strip().lower()
    if agreement != 'yes':
        print("시스템을 종료합니다.")
        return
    
    # 모드 선택
    mode = input("모드를 선택하세요 (demo/real): ").strip().lower()
    
    # 대상 종목 설정
    print("\n대상 종목 선택:")
    print("1. 기본 세트 (삼성전자, SK하이닉스, NAVER, 카카오, LG에너지솔루션)")
    print("2. 사용자 정의")
    
    choice = input("선택 (1/2): ").strip()
    
    if choice == "1":
        target_stocks = ['005930', '000660', '035420', '035720', '373220']
    else:
        stock_input = input("종목 코드를 입력하세요 (쉼표로 구분): ")
        target_stocks = [s.strip() for s in stock_input.split(',')]
    
    print(f"\n대상 종목: {target_stocks}")
    
    try:
        # API 초기화
        from config import Config
        account_info = Config.get_account_info('demo' if mode == 'demo' else 'real')
        
        from kis_api_enhanced import KisAPIEnhanced as KisAPI
        kis_api = KisAPI(
            account_info['appkey'],
            account_info['appsecret'], 
            account_info['account'],
            is_real=(mode == 'real')
        )
        
        if not kis_api.get_access_token():
            raise Exception("API 토큰 발급 실패")
        
        # 고빈도 트레이더 초기화
        hft = HighFrequencyTrader(kis_api, target_stocks)
        
        print(f"\n🤖 고빈도 거래 시작 ({mode} 모드)")
        print("중단하려면 Ctrl+C를 눌러주세요")
        
        # 거래 시작
        hft.start_trading(update_interval=0.5)
        
    except KeyboardInterrupt:
        print("\n👋 시스템을 안전하게 종료합니다.")
    except Exception as e:
        logger.error(f"시스템 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
