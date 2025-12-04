#!/usr/bin/env python3
"""
빠른 백테스팅 데모 - 시뮬레이션 데이터 사용
"""

import numpy as np
from datetime import datetime, timedelta
import time

class QuickBacktest:
    """빠른 백테스트 데모"""
    
    def __init__(self, initial_capital=10000000, days=30):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.days = days
        self.portfolio_values = []
        self.trades = []
        
    def run(self):
        """백테스트 실행"""
        print("🚀 빠른 백테스팅 데모 시작!")
        print("=" * 50)
        print(f"💰 초기 자본: {self.initial_capital:,}원")
        print(f"📅 시뮬레이션 기간: {self.days}일")
        print("=" * 50)
        
        print(f"\n📈 일별 진행 상황:")
        print("-" * 70)
        
        for day in range(1, self.days + 1):
            # 시뮬레이션 수익률 (랜덤)
            daily_return = np.random.normal(0.002, 0.02)  # 평균 0.2%, 변동성 2%
            
            # 포트폴리오 가치 업데이트
            old_value = self.current_capital
            self.current_capital *= (1 + daily_return)
            change = self.current_capital - old_value
            
            # 기록
            self.portfolio_values.append(self.current_capital)
            
            # 거래 시뮬레이션 (5일마다)
            if day % 5 == 0:
                self.trades.append({
                    'day': day,
                    'action': 'rebalance',
                    'value': self.current_capital
                })
                
            # 진행 상황 표시 (3일마다)
            if day % 3 == 0:
                total_return = (self.current_capital - self.initial_capital) / self.initial_capital * 100
                date_str = (datetime.now() - timedelta(days=self.days-day)).strftime('%Y-%m-%d')
                
                print(f"Day {day:2d} | {date_str} | "
                      f"수익률: {total_return:+6.2f}% | "
                      f"자산: {self.current_capital:10,.0f}원 | "
                      f"일변동: {change:+8,.0f}원")
                      
            # 시뮬레이션 딜레이
            time.sleep(0.1)
            
        # 최종 결과
        self._show_results()
        
    def _show_results(self):
        """결과 표시"""
        final_return = (self.current_capital - self.initial_capital) / self.initial_capital * 100
        profit_loss = self.current_capital - self.initial_capital
        
        print("\n" + "=" * 50)
        print("🎯 백테스트 완료!")
        print("=" * 50)
        
        print(f"💰 수익성 지표:")
        print(f"   초기 자본: {self.initial_capital:,}원")
        print(f"   최종 자산: {self.current_capital:,.0f}원")
        print(f"   총 손익: {profit_loss:+,.0f}원")
        print(f"   총 수익률: {final_return:+.2f}%")
        print(f"   연간환산: {final_return * 365 / self.days:+.2f}%")
        
        # 변동성 계산
        if len(self.portfolio_values) > 1:
            returns = np.diff(self.portfolio_values) / self.portfolio_values[:-1]
            volatility = np.std(returns) * np.sqrt(252) * 100  # 연간 변동성
            
            print(f"\n📉 위험 지표:")
            print(f"   변동성: {volatility:.2f}%")
            print(f"   샤프비율: {(final_return * 365 / self.days) / volatility:.2f}" if volatility > 0 else "   샤프비율: N/A")
        
        print(f"\n🔄 거래 지표:")
        print(f"   리밸런싱: {len(self.trades)}회")
        print(f"   거래일: {self.days}일")
        
        # 성과 평가
        print(f"\n🏆 성과 평가:")
        if final_return > 10:
            print(f"   🎉 우수한 성과! (+{final_return:.1f}%)")
        elif final_return > 5:
            print(f"   👍 양호한 성과! (+{final_return:.1f}%)")
        elif final_return > 0:
            print(f"   📈 수익 달성! (+{final_return:.1f}%)")
        elif final_return > -5:
            print(f"   📉 소폭 손실 ({final_return:.1f}%)")
        else:
            print(f"   ⚠️  큰 손실 주의 ({final_return:.1f}%)")

if __name__ == "__main__":
    # 빠른 데모 실행
    backtest = QuickBacktest(initial_capital=10000000, days=30)
    backtest.run()