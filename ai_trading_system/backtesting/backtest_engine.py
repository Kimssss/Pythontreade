#!/usr/bin/env python3
"""
백테스팅 엔진 - 국내/해외 주식 백테스팅 기능
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import asyncio
import os
from pathlib import Path
import json

# 로거 설정
logger = logging.getLogger('backtest_engine')

class BacktestEngine:
    """백테스팅 엔진"""
    
    def __init__(self, 
                 initial_capital: float = 10000000,  # 초기 자본 (천만원)
                 commission: float = 0.003,  # 수수료 0.3%
                 slippage: float = 0.001):   # 슬리피지 0.1%
        """
        Args:
            initial_capital: 초기 자본
            commission: 거래 수수료 비율
            slippage: 슬리피지 비율
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.reset()
        
    def reset(self):
        """백테스트 상태 초기화"""
        self.current_capital = self.initial_capital
        self.portfolio = {}  # {종목코드: {'quantity': 수량, 'avg_price': 평균가격}}
        self.trades = []
        self.daily_returns = []
        self.daily_portfolio_values = []
        self.performance_metrics = {}
        
    def add_trade(self, symbol: str, action: str, quantity: int, 
                 price: float, timestamp: datetime, reason: str = ""):
        """거래 추가
        
        Args:
            symbol: 종목 코드
            action: 'buy' 또는 'sell'
            quantity: 거래 수량
            price: 거래 가격
            timestamp: 거래 시점
            reason: 거래 이유
        """
        # 수수료와 슬리피지 적용
        if action == 'buy':
            effective_price = price * (1 + self.slippage + self.commission)
            total_cost = quantity * effective_price
            
            if total_cost > self.current_capital:
                logger.warning(f"자본 부족으로 {symbol} 매수 실패: 필요 {total_cost:,.0f}, 보유 {self.current_capital:,.0f}")
                return False
                
            # 포트폴리오 업데이트
            if symbol in self.portfolio:
                old_qty = self.portfolio[symbol]['quantity']
                old_avg = self.portfolio[symbol]['avg_price']
                new_qty = old_qty + quantity
                new_avg = (old_qty * old_avg + quantity * effective_price) / new_qty
                self.portfolio[symbol] = {'quantity': new_qty, 'avg_price': new_avg}
            else:
                self.portfolio[symbol] = {'quantity': quantity, 'avg_price': effective_price}
                
            self.current_capital -= total_cost
            
        elif action == 'sell':
            if symbol not in self.portfolio or self.portfolio[symbol]['quantity'] < quantity:
                logger.warning(f"보유 수량 부족으로 {symbol} 매도 실패")
                return False
                
            effective_price = price * (1 - self.slippage - self.commission)
            total_proceeds = quantity * effective_price
            
            # 포트폴리오 업데이트
            self.portfolio[symbol]['quantity'] -= quantity
            if self.portfolio[symbol]['quantity'] == 0:
                del self.portfolio[symbol]
                
            self.current_capital += total_proceeds
            
        # 거래 기록
        trade_record = {
            'timestamp': timestamp,
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'effective_price': effective_price,
            'total_amount': quantity * effective_price,
            'reason': reason,
            'capital_after': self.current_capital
        }
        
        self.trades.append(trade_record)
        logger.info(f"{action.upper()} {symbol} x{quantity} @ {price:.2f} (효과가격: {effective_price:.2f})")
        
        return True
        
    def calculate_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """현재 포트폴리오 가치 계산
        
        Args:
            current_prices: {종목코드: 현재가격} 딕셔너리
            
        Returns:
            총 포트폴리오 가치
        """
        portfolio_value = self.current_capital
        
        for symbol, position in self.portfolio.items():
            if symbol in current_prices:
                stock_value = position['quantity'] * current_prices[symbol]
                portfolio_value += stock_value
            else:
                # 가격 정보가 없으면 평균 매수가로 계산
                stock_value = position['quantity'] * position['avg_price']
                portfolio_value += stock_value
                
        return portfolio_value
        
    def record_daily_performance(self, date: datetime, current_prices: Dict[str, float]):
        """일일 성과 기록
        
        Args:
            date: 날짜
            current_prices: 현재 주식 가격들
        """
        portfolio_value = self.calculate_portfolio_value(current_prices)
        self.daily_portfolio_values.append({
            'date': date,
            'portfolio_value': portfolio_value,
            'cash': self.current_capital,
            'stock_value': portfolio_value - self.current_capital
        })
        
        # 일일 수익률 계산
        if len(self.daily_portfolio_values) > 1:
            prev_value = self.daily_portfolio_values[-2]['portfolio_value']
            daily_return = (portfolio_value - prev_value) / prev_value
            self.daily_returns.append(daily_return)
            
    def calculate_performance_metrics(self) -> Dict:
        """성과 지표 계산"""
        if not self.daily_portfolio_values:
            return {}
            
        # 기본 수익률
        final_value = self.daily_portfolio_values[-1]['portfolio_value']
        total_return = (final_value - self.initial_capital) / self.initial_capital
        
        # 연간 수익률 (거래일 250일 기준)
        trading_days = len(self.daily_portfolio_values)
        if trading_days > 0:
            annual_return = (1 + total_return) ** (250 / trading_days) - 1
        else:
            annual_return = 0
            
        # 샤프 비율
        if len(self.daily_returns) > 1:
            avg_return = np.mean(self.daily_returns)
            return_std = np.std(self.daily_returns)
            sharpe_ratio = (avg_return / return_std) * np.sqrt(250) if return_std > 0 else 0
        else:
            sharpe_ratio = 0
            
        # 최대 낙폭 (Max Drawdown)
        portfolio_values = [pv['portfolio_value'] for pv in self.daily_portfolio_values]
        peak = np.maximum.accumulate(portfolio_values)
        drawdown = (portfolio_values - peak) / peak
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        
        # 승률 계산
        profitable_trades = len([t for t in self.trades if t['action'] == 'sell' and self._calculate_trade_profit(t) > 0])
        total_sell_trades = len([t for t in self.trades if t['action'] == 'sell'])
        win_rate = profitable_trades / total_sell_trades if total_sell_trades > 0 else 0
        
        self.performance_metrics = {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': len(self.trades),
            'final_value': final_value,
            'initial_capital': self.initial_capital,
            'profit_loss': final_value - self.initial_capital
        }
        
        return self.performance_metrics
        
    def _calculate_trade_profit(self, sell_trade: Dict) -> float:
        """거래별 손익 계산 (매도 거래 기준)"""
        symbol = sell_trade['symbol']
        
        # 매도 거래에 대해 해당 매수 거래 찾기
        buy_trades = [t for t in self.trades if t['symbol'] == symbol and t['action'] == 'buy' 
                     and t['timestamp'] <= sell_trade['timestamp']]
        
        if not buy_trades:
            return 0
            
        # 가장 최근 매수 거래의 가격 사용 (LIFO)
        latest_buy = max(buy_trades, key=lambda t: t['timestamp'])
        avg_buy_price = latest_buy['effective_price']
        
        # 손익 계산 (수수료 포함)
        profit = (sell_trade['effective_price'] - avg_buy_price) * sell_trade['quantity']
        return profit
        
    def get_trading_summary(self) -> Dict:
        """거래 요약 정보"""
        buy_trades = [t for t in self.trades if t['action'] == 'buy']
        sell_trades = [t for t in self.trades if t['action'] == 'sell']
        
        total_buy_amount = sum(t['total_amount'] for t in buy_trades)
        total_sell_amount = sum(t['total_amount'] for t in sell_trades)
        
        return {
            'total_trades': len(self.trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'total_buy_amount': total_buy_amount,
            'total_sell_amount': total_sell_amount,
            'portfolio_positions': len(self.portfolio),
            'current_cash': self.current_capital
        }
        
    def export_results(self, filename: str):
        """백테스트 결과 내보내기"""
        results = {
            'performance_metrics': self.performance_metrics,
            'trading_summary': self.get_trading_summary(),
            'trades': self.trades,
            'daily_portfolio_values': self.daily_portfolio_values,
            'final_portfolio': self.portfolio
        }
        
        # JSON 직렬화 가능하도록 datetime 변환
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj
            
        def recursive_convert(data):
            if isinstance(data, dict):
                return {k: recursive_convert(v) for k, v in data.items()}
            elif isinstance(data, list):
                return [recursive_convert(item) for item in data]
            else:
                return convert_datetime(data)
        
        results = recursive_convert(results)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        logger.info(f"백테스트 결과가 {filename}에 저장되었습니다.")


class HistoricalDataProvider:
    """과거 데이터 제공자 (시뮬레이션용)"""
    
    def __init__(self, kis_api):
        self.api = kis_api
        
    async def get_historical_data(self, symbol: str, start_date: datetime, 
                                 end_date: datetime, market: str = 'domestic') -> pd.DataFrame:
        """과거 데이터 조회
        
        Args:
            symbol: 종목 코드
            start_date: 시작일
            end_date: 종료일
            market: 'domestic' 또는 'overseas'
            
        Returns:
            DataFrame with OHLCV data
        """
        # 실제 구현에서는 KIS API 또는 외부 데이터 소스에서 데이터 조회
        # 여기서는 시뮬레이션 데이터 생성
        return self._generate_simulation_data(symbol, start_date, end_date)
        
    def _generate_simulation_data(self, symbol: str, start_date: datetime, 
                                 end_date: datetime) -> pd.DataFrame:
        """시뮬레이션 데이터 생성"""
        # 간단한 랜덤 워크 기반 가격 데이터 생성
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        dates = dates[dates.weekday < 5]  # 주말 제외
        
        # 기본 가격 (10,000원에서 시작)
        base_price = 10000
        returns = np.random.normal(0.001, 0.02, len(dates))  # 평균 0.1% 수익률, 2% 변동성
        prices = base_price * np.exp(np.cumsum(returns))
        
        # OHLCV 데이터 생성
        data = []
        for i, date in enumerate(dates):
            open_price = prices[i]
            close_price = prices[i] * (1 + np.random.normal(0, 0.005))
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
            volume = int(np.random.uniform(10000, 100000))
            
            data.append({
                'date': date,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            if i < len(dates) - 1:
                prices[i + 1] = close_price
                
        return pd.DataFrame(data)