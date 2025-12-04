#!/usr/bin/env python3
"""
빠른 백테스팅 - 실제 주식 스크리닝 없이 시뮬레이션 데이터로 빠른 테스트
"""

import numpy as np
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List
import time

class FastBacktestEngine:
    """빠른 백테스트 엔진"""
    
    def __init__(self, initial_capital: float = 10000000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.portfolio = {}  # {symbol: {'quantity': int, 'avg_price': float}}
        self.trades = []
        self.daily_values = []
        
    def add_trade(self, symbol: str, action: str, quantity: int, price: float, date: datetime):
        """거래 추가"""
        cost = quantity * price
        
        if action == 'buy':
            if cost > self.current_capital:
                return False
                
            if symbol in self.portfolio:
                old_qty = self.portfolio[symbol]['quantity']
                old_avg = self.portfolio[symbol]['avg_price']
                new_qty = old_qty + quantity
                new_avg = (old_qty * old_avg + quantity * price) / new_qty
                self.portfolio[symbol] = {'quantity': new_qty, 'avg_price': new_avg}
            else:
                self.portfolio[symbol] = {'quantity': quantity, 'avg_price': price}
                
            self.current_capital -= cost
            
        elif action == 'sell':
            if symbol not in self.portfolio or self.portfolio[symbol]['quantity'] < quantity:
                return False
                
            self.portfolio[symbol]['quantity'] -= quantity
            if self.portfolio[symbol]['quantity'] == 0:
                del self.portfolio[symbol]
                
            self.current_capital += cost
            
        self.trades.append({
            'date': date,
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'price': price,
            'total': cost
        })
        
        return True
        
    def calculate_portfolio_value(self, prices: Dict[str, float]) -> float:
        """포트폴리오 가치 계산"""
        value = self.current_capital
        
        for symbol, position in self.portfolio.items():
            if symbol in prices:
                value += position['quantity'] * prices[symbol]
                
        return value
        
    def record_daily_value(self, date: datetime, prices: Dict[str, float]):
        """일일 포트폴리오 가치 기록"""
        total_value = self.calculate_portfolio_value(prices)
        return_rate = (total_value - self.initial_capital) / self.initial_capital * 100
        
        self.daily_values.append({
            'date': date,
            'total_value': total_value,
            'cash': self.current_capital,
            'return_rate': return_rate,
            'positions': len(self.portfolio),
            'trades': len(self.trades)
        })
        
        return total_value, return_rate

class FastBacktester:
    """빠른 백테스터"""
    
    def __init__(self, start_date: datetime, end_date: datetime, initial_capital: float = 10000000):
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.engine = FastBacktestEngine(initial_capital)
        
        # 가상 주식 유니버스 생성 (10개 종목)
        self.stock_universe = [
            {'symbol': f'STOCK_{i:02d}', 'name': f'테스트주식{i:02d}', 'initial_price': np.random.uniform(10000, 50000)}
            for i in range(1, 11)
        ]
        
        # 가격 히스토리 생성
        self.price_history = self._generate_price_history()
        
    def _generate_price_history(self) -> Dict[str, Dict[datetime, float]]:
        """가격 히스토리 생성"""
        price_history = {}
        
        dates = []
        current_date = self.start_date
        while current_date <= self.end_date:
            if current_date.weekday() < 5:  # 주말 제외
                dates.append(current_date)
            current_date += timedelta(days=1)
            
        for stock in self.stock_universe:
            symbol = stock['symbol']
            initial_price = stock['initial_price']
            
            # 랜덤 워크로 가격 생성
            prices = [initial_price]
            for i in range(1, len(dates)):
                # 일일 수익률 (-3% ~ +3%)
                daily_return = np.random.normal(0, 0.02)
                daily_return = max(-0.03, min(0.03, daily_return))
                
                new_price = prices[-1] * (1 + daily_return)
                new_price = max(1000, new_price)  # 최소 1000원
                prices.append(new_price)
                
            price_history[symbol] = dict(zip(dates, prices))
            
        return price_history
        
    def _generate_trading_signals(self, date: datetime) -> List[Dict]:
        """거래 신호 생성"""
        signals = []
        
        # 랜덤 거래 신호 생성 (20% 확률로 거래)
        for stock in self.stock_universe:
            if np.random.random() < 0.2:  # 20% 확률
                symbol = stock['symbol']
                price = self.price_history[symbol][date]
                
                # 매수/매도 결정
                action = np.random.choice(['buy', 'sell'], p=[0.6, 0.4])
                
                if action == 'buy':
                    # 보유 현금의 10% 정도로 매수
                    max_investment = self.engine.current_capital * 0.1
                    quantity = int(max_investment / price)
                    if quantity > 0:
                        signals.append({
                            'symbol': symbol,
                            'action': 'buy',
                            'quantity': quantity,
                            'price': price
                        })
                        
                elif action == 'sell' and symbol in self.engine.portfolio:
                    # 보유 수량의 50% 매도
                    held_quantity = self.engine.portfolio[symbol]['quantity']
                    quantity = max(1, held_quantity // 2)
                    signals.append({
                        'symbol': symbol,
                        'action': 'sell',
                        'quantity': quantity,
                        'price': price
                    })
                    
        return signals
        
    def run(self):
        """백테스트 실행"""
        print(f"\n🚀 빠른 백테스트 시작!")
        print(f"📅 기간: {self.start_date.strftime('%Y-%m-%d')} ~ {self.end_date.strftime('%Y-%m-%d')}")
        print(f"💰 초기 자본: {self.initial_capital:,}원")
        print(f"📈 대상: 시뮬레이션 주식 {len(self.stock_universe)}개")
        print("=" * 80)
        
        # 진행 상황 표시 간격 설정
        dates = [d for d in self.price_history[self.stock_universe[0]['symbol']].keys()]
        total_days = len(dates)
        
        if total_days <= 30:
            interval_text = "1일 단위"
        elif total_days <= 180:
            interval_text = "주간 단위"
        else:
            interval_text = "월간 단위"
            
        print(f"\n📈 백테스트 진행 상황 ({interval_text}):")
        print("=" * 80)
        print("날짜       | 진행률 | 수익률    | 총자산        | 현금잔고      | 보유종목 | 거래수")
        print("-" * 80)
        
        for i, current_date in enumerate(dates):
            # 현재 날짜의 모든 종목 가격
            current_prices = {symbol: self.price_history[symbol][current_date] 
                            for symbol in [s['symbol'] for s in self.stock_universe]}
            
            # 거래 신호 생성 및 실행 (5일마다)
            if i % 5 == 0:
                signals = self._generate_trading_signals(current_date)
                for signal in signals:
                    self.engine.add_trade(
                        symbol=signal['symbol'],
                        action=signal['action'],
                        quantity=signal['quantity'],
                        price=signal['price'],
                        date=current_date
                    )
            
            # 일일 성과 기록
            total_value, return_rate = self.engine.record_daily_value(current_date, current_prices)
            
            # 진행률 계산
            progress = (i + 1) / total_days * 100
            
            # 진행 상황 출력 (주간 단위 또는 월간 단위)
            show_progress = False
            if total_days <= 30:  # 1개월 이하: 매일
                show_progress = True
                delay = 0.1
            elif total_days <= 180:  # 6개월 이하: 주간
                show_progress = (i % 7 == 0)
                delay = 0.05
            else:  # 6개월 초과: 월간
                show_progress = (i % 30 == 0) or (i == total_days - 1)  # 월말 또는 마지막날
                delay = 0.02
            
            if show_progress:
                print(f"{current_date.strftime('%Y-%m-%d')} | "
                      f"{progress:5.1f}% | "
                      f"{return_rate:+7.2f}% | "
                      f"{total_value:>12,.0f}원 | "
                      f"{self.engine.current_capital:>12,.0f}원 | "
                      f"{len(self.engine.portfolio):>6}개 | "
                      f"{len(self.engine.trades):>4}회")
                      
            # 시각적 효과를 위한 짧은 딜레이
            time.sleep(delay)
            
        # 최종 결과
        self._show_results()
        
    def _show_results(self):
        """최종 결과 표시"""
        if not self.engine.daily_values:
            return
            
        final_data = self.engine.daily_values[-1]
        final_value = final_data['total_value']
        total_return = final_data['return_rate']
        
        # 성과 지표 계산
        returns = [dv['return_rate'] for dv in self.engine.daily_values]
        max_return = max(returns) if returns else 0
        min_return = min(returns) if returns else 0
        
        print("\n" + "=" * 60)
        print("🎯 백테스트 완료!")
        print("=" * 60)
        
        # 연간 수익률 계산
        trading_days = len(self.engine.daily_values)
        if trading_days > 0:
            annual_return = (total_return / 100) * (252 / trading_days) * 100  # 연간 거래일 252일 기준
        else:
            annual_return = 0
            
        print(f"💰 수익성 지표:")
        print(f"   초기 자본: {self.initial_capital:,}원")
        print(f"   최종 자산: {final_value:,.0f}원")
        print(f"   총 손익: {final_value - self.initial_capital:+,.0f}원")
        print(f"   총 수익률: {total_return:+.2f}%")
        print(f"   연간환산 수익률: {annual_return:+.2f}%")
        print(f"   백테스트 기간: {trading_days}일")
        
        print(f"\n📉 위험 지표:")
        print(f"   최고 수익률: {max_return:+.2f}%")
        print(f"   최저 수익률: {min_return:+.2f}%")
        print(f"   변동폭: {max_return - min_return:.2f}%")
        
        print(f"\n🔄 거래 지표:")
        print(f"   총 거래 횟수: {len(self.engine.trades)}회")
        buy_trades = len([t for t in self.engine.trades if t['action'] == 'buy'])
        sell_trades = len([t for t in self.engine.trades if t['action'] == 'sell'])
        print(f"   매수 거래: {buy_trades}회")
        print(f"   매도 거래: {sell_trades}회")
        
        print(f"\n📊 포트폴리오 현황:")
        print(f"   최종 보유 종목: {len(self.engine.portfolio)}개")
        print(f"   현금 잔고: {self.engine.current_capital:,.0f}원")
        
        # 성과 평가
        print(f"\n🏆 성과 평가:")
        if total_return > 10:
            print(f"   🎉 우수한 성과! (+{total_return:.1f}%)")
        elif total_return > 5:
            print(f"   👍 양호한 성과! (+{total_return:.1f}%)")
        elif total_return > 0:
            print(f"   📈 수익 달성! (+{total_return:.1f}%)")
        elif total_return > -5:
            print(f"   📉 소폭 손실 ({total_return:.1f}%)")
        else:
            print(f"   ⚠️  큰 손실 주의 ({total_return:.1f}%)")

def main():
    """메인 함수"""
    import sys
    
    # 명령행 인자나 환경변수로부터 기간 설정 가져오기
    if len(sys.argv) >= 4:
        # 명령행 인자: start_date end_date capital
        try:
            start_date = datetime.strptime(sys.argv[1], '%Y-%m-%d')
            end_date = datetime.strptime(sys.argv[2], '%Y-%m-%d')
            capital = int(sys.argv[3])
        except (ValueError, IndexError):
            # 기본값 설정 (2년)
            end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = end_date - timedelta(days=730)  # 2년
            capital = 10000000
    else:
        # 기본값 설정 (2년)
        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=730)  # 2년
        capital = 10000000
    
    # 백테스터 생성 및 실행
    backtester = FastBacktester(start_date, end_date, initial_capital=capital)
    backtester.run()

if __name__ == "__main__":
    main()