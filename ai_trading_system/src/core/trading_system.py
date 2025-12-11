#!/usr/bin/env python3
"""
메인 AI 자동매매 시스템
실시간 거래 및 포트폴리오 관리
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import yaml

# 절대 경로 import로 수정
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from ai_trading_system.src.execution.kis_broker import KISBroker
from ai_trading_system.src.strategies.technical.ma_crossover import MACrossoverStrategy
from ai_trading_system.src.strategies.technical.rsi_strategy import RSIStrategy
from ai_trading_system.src.utils.gmail_notifier import GmailNotifier

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_trading_system/logs/trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('trading_system')

class TradingSystem:
    """AI 자동매매 시스템"""
    
    def __init__(self, config_path: str = "ai_trading_system/config/kis_config.yaml", paper_trading: bool = True):
        """초기화
        
        Args:
            config_path: 설정 파일 경로
            paper_trading: 모의투자 여부
        """
        logger.info("=== AI 자동매매 시스템 초기화 ===")
        
        # 설정 로드
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.paper_trading = paper_trading
        self.mode = "모의투자" if paper_trading else "실전투자"
        
        # KIS 브로커 초기화
        logger.info("한국투자증권 API 브로커 초기화...")
        self.broker = KISBroker(config_path, paper_trading)
        
        # 대상 종목
        self.symbols = self.config.get('default_symbols', ['005930', '000660'])
        logger.info(f"대상 종목: {self.symbols}")
        
        # 전략 초기화
        self.strategies = [
            MACrossoverStrategy(self.symbols, fast_period=5, slow_period=20),
            RSIStrategy(self.symbols, period=14, overbought=70, oversold=30)
        ]
        logger.info(f"활성 전략: {[s.name for s in self.strategies]}")
        
        # Gmail 알림
        try:
            self.gmail_notifier = GmailNotifier()
            self.gmail_notifier.notify_trading_start()
        except Exception as e:
            logger.warning(f"Gmail 알림 초기화 실패: {e}")
            self.gmail_notifier = None
        
        # 포트폴리오 상태
        self.portfolio = {}
        self.cash_balance = 0
        self.total_value = 0
        self.last_update = None
        
        # 거래 상태
        self.is_running = False
        self.trade_count_today = 0
        self.last_trade_time = None
        
        logger.info(f"AI 자동매매 시스템 초기화 완료 - {self.mode}")
    
    async def initialize(self):
        """시스템 초기화"""
        logger.info("시스템 데이터 초기화...")
        
        try:
            # 계좌 정보 조회
            await self.update_portfolio()
            
            # 초기 상태 로그
            logger.info(f"초기 포트폴리오 가치: {self.total_value:,.0f}원")
            logger.info(f"현금 잔고: {self.cash_balance:,.0f}원")
            logger.info(f"보유 종목 수: {len(self.portfolio)}개")
            
            self.is_running = True
            
        except Exception as e:
            logger.error(f"시스템 초기화 실패: {e}")
            raise
    
    async def update_portfolio(self):
        """포트폴리오 상태 업데이트"""
        try:
            balance_info = self.broker.get_balance()
            
            if balance_info and balance_info.get('rt_cd') == '0':
                # 현금 잔고
                output2 = balance_info.get('output2', [{}])
                if output2:
                    self.cash_balance = float(output2[0].get('dnca_tot_amt', 0))
                    self.total_value = float(output2[0].get('tot_evlu_amt', 0))
                
                # 보유 종목
                output1 = balance_info.get('output1', [])
                self.portfolio = {}
                
                for holding in output1:
                    if int(holding.get('hldg_qty', 0)) > 0:
                        stock_code = holding['pdno']
                        self.portfolio[stock_code] = {
                            'name': holding['prdt_name'],
                            'quantity': int(holding['hldg_qty']),
                            'avg_price': float(holding['pchs_avg_pric']),
                            'current_price': float(holding['prpr']),
                            'eval_amount': float(holding['evlu_amt']),
                            'profit_rate': float(holding['evlu_pfls_rt'])
                        }
                
                self.last_update = datetime.now()
                logger.info("포트폴리오 상태 업데이트 완료")
                
            else:
                logger.error("계좌 조회 실패")
                
        except Exception as e:
            logger.error(f"포트폴리오 업데이트 오류: {e}")
    
    async def get_market_data(self, symbols: List[str], days: int = 100) -> pd.DataFrame:
        """시장 데이터 수집
        
        Args:
            symbols: 종목 코드 리스트
            days: 조회 일수
            
        Returns:
            통합된 시장 데이터
        """
        all_data = {}
        
        for symbol in symbols:
            try:
                # 일봉 데이터 조회
                daily_data = self.broker.get_daily_price(symbol, count=days)
                
                if daily_data:
                    df = pd.DataFrame(daily_data)
                    df['date'] = pd.to_datetime(df['date'])
                    df = df.set_index('date').sort_index()
                    
                    # 종목별 컬럼명 설정
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        all_data[f"{symbol}_{col}"] = df[col]
                
                # API 호출 간격
                await asyncio.sleep(0.2)
                
            except Exception as e:
                logger.error(f"시장 데이터 조회 오류 ({symbol}): {e}")
        
        if all_data:
            return pd.DataFrame(all_data).fillna(method='ffill').dropna()
        else:
            return pd.DataFrame()
    
    async def analyze_and_trade(self):
        """분석 및 거래 실행"""
        try:
            logger.info("=== 시장 분석 및 거래 신호 생성 ===")
            
            # 시장 데이터 수집
            market_data = await self.get_market_data(self.symbols)
            
            if market_data.empty:
                logger.warning("시장 데이터가 없습니다")
                return
            
            # 전략별 신호 생성
            all_signals = []
            
            for strategy in self.strategies:
                if strategy.is_active:
                    signals = strategy.calculate_signals(market_data)
                    all_signals.extend(signals)
                    logger.info(f"{strategy.name} 전략: {len(signals)}개 신호 생성")
            
            # 신호 통합 및 필터링
            filtered_signals = self.filter_signals(all_signals)
            
            # 거래 실행
            for signal in filtered_signals:
                await self.execute_signal(signal)
                await asyncio.sleep(1)  # 주문 간격
            
            logger.info(f"총 {len(filtered_signals)}개 거래 실행")
            
        except Exception as e:
            logger.error(f"분석 및 거래 실행 오류: {e}")
            if self.gmail_notifier:
                self.gmail_notifier.notify_error(str(e), "거래 실행")
    
    def filter_signals(self, signals: List) -> List:
        """신호 필터링 및 통합
        
        Args:
            signals: 원본 신호 리스트
            
        Returns:
            필터링된 신호 리스트
        """
        if not signals:
            return []
        
        # 종목별 신호 통합
        symbol_signals = {}
        
        for signal in signals:
            symbol = signal.symbol
            if symbol not in symbol_signals:
                symbol_signals[symbol] = []
            symbol_signals[symbol].append(signal)
        
        # 종목별 최종 신호 결정
        final_signals = []
        
        for symbol, sig_list in symbol_signals.items():
            # 매수 신호와 매도 신호 분리
            buy_signals = [s for s in sig_list if s.signal_type == "LONG"]
            sell_signals = [s for s in sig_list if s.signal_type == "EXIT"]
            
            # 신호 강도 합산
            buy_strength = sum(s.strength for s in buy_signals)
            sell_strength = sum(s.strength for s in sell_signals)
            
            # 최종 신호 결정 (임계값: 1.0)
            current_position = self.portfolio.get(symbol, {}).get('quantity', 0)
            
            if buy_strength >= 1.0 and current_position == 0:
                # 매수 신호
                final_signals.append(max(buy_signals, key=lambda s: s.strength))
            elif sell_strength >= 1.0 and current_position > 0:
                # 매도 신호
                final_signals.append(max(sell_signals, key=lambda s: s.strength))
        
        return final_signals
    
    async def execute_signal(self, signal):
        """거래 신호 실행
        
        Args:
            signal: 거래 신호
        """
        try:
            symbol = signal.symbol
            
            # 현재가 조회
            price_info = self.broker.get_stock_price(symbol)
            if not price_info:
                logger.error(f"현재가 조회 실패: {symbol}")
                return
            
            current_price = price_info['current_price']
            current_position = self.portfolio.get(symbol, {}).get('quantity', 0)
            
            if signal.signal_type == "LONG" and current_position == 0:
                # 매수 실행
                position_value = self.total_value * 0.1  # 포트폴리오의 10%
                quantity = int(position_value / current_price)
                
                if quantity > 0 and self.cash_balance >= quantity * current_price * 1.003:
                    result = self.broker.place_order(symbol, quantity, "BUY", order_type="03")
                    
                    if result and result.get('rt_cd') == '0':
                        logger.info(f"✅ 매수 주문 성공: {symbol} {quantity}주 @ {current_price:,}원")
                        self.trade_count_today += 1
                        self.last_trade_time = datetime.now()
                        
                        if self.gmail_notifier:
                            self.gmail_notifier.notify_trade_executed(symbol, "매수", quantity, current_price)
                    else:
                        logger.error(f"❌ 매수 주문 실패: {symbol}")
            
            elif signal.signal_type == "EXIT" and current_position > 0:
                # 매도 실행
                quantity = current_position
                result = self.broker.place_order(symbol, quantity, "SELL", order_type="03")
                
                if result and result.get('rt_cd') == '0':
                    logger.info(f"✅ 매도 주문 성공: {symbol} {quantity}주 @ {current_price:,}원")
                    self.trade_count_today += 1
                    self.last_trade_time = datetime.now()
                    
                    if self.gmail_notifier:
                        self.gmail_notifier.notify_trade_executed(symbol, "매도", quantity, current_price)
                else:
                    logger.error(f"❌ 매도 주문 실패: {symbol}")
        
        except Exception as e:
            logger.error(f"거래 실행 오류 ({signal.symbol}): {e}")
    
    def is_market_open(self) -> bool:
        """장 개장 여부 확인"""
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour
        minute = now.minute
        
        # 평일 09:00 ~ 15:30
        if weekday < 5 and (9 <= hour < 15 or (hour == 15 and minute <= 30)):
            return True
        
        return False
    
    async def send_hourly_status(self):
        """시간별 상태 알림"""
        if self.gmail_notifier:
            try:
                await self.update_portfolio()
                
                market_status = "장중" if self.is_market_open() else "장외시간"
                
                self.gmail_notifier.notify_hourly_status(
                    portfolio_value=self.total_value,
                    positions=len(self.portfolio),
                    trades_today=self.trade_count_today
                )
                
                logger.info(f"시간별 상태 알림 전송 완료 - {market_status}")
                
            except Exception as e:
                logger.error(f"시간별 상태 알림 오류: {e}")
    
    async def run(self):
        """메인 실행 루프"""
        logger.info("🚀 AI 자동매매 시스템 시작")
        
        try:
            # 시스템 초기화
            await self.initialize()
            
            # 시작 알림
            if self.gmail_notifier:
                self.gmail_notifier.notify_market_status("korean", "모니터링 시작")
            
            last_hour = datetime.now().hour
            
            while self.is_running:
                try:
                    current_time = datetime.now()
                    
                    # 시간별 알림
                    if current_time.hour != last_hour:
                        await self.send_hourly_status()
                        last_hour = current_time.hour
                    
                    if self.is_market_open():
                        logger.info(f"📊 장중 거래 - {current_time.strftime('%H:%M:%S')}")
                        
                        # 거래 실행
                        await self.analyze_and_trade()
                        
                        # 5분 대기
                        await asyncio.sleep(300)
                    else:
                        logger.info(f"😴 장외시간 - {current_time.strftime('%H:%M:%S')}")
                        
                        # 포트폴리오 상태만 업데이트
                        await self.update_portfolio()
                        
                        # 30분 대기
                        await asyncio.sleep(1800)
                
                except KeyboardInterrupt:
                    logger.info("사용자 중지 요청")
                    break
                except Exception as e:
                    logger.error(f"메인 루프 오류: {e}")
                    
                    if self.gmail_notifier:
                        self.gmail_notifier.notify_error(str(e), "시스템 오류")
                    
                    # 5분 후 재시도
                    await asyncio.sleep(300)
        
        finally:
            self.is_running = False
            logger.info("AI 자동매매 시스템 종료")