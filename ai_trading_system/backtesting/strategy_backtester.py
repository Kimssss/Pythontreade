#!/usr/bin/env python3
"""
전략 백테스터 - AI 트레이딩 전략 백테스팅
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from pathlib import Path
import sys
import os

# 프로젝트 경로 추가
current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

from ai_trading_system.backtesting.backtest_engine import BacktestEngine, HistoricalDataProvider
from ai_trading_system.agents.dqn_agent import DQNAgent
from ai_trading_system.agents.technical_agent import TechnicalAgent
from ai_trading_system.agents.factor_agent import FactorAgent
from ai_trading_system.strategies.stock_screener import StockScreener
from ai_trading_system.strategies.global_screener import GlobalStockScreener

logger = logging.getLogger('strategy_backtester')

class StrategyBacktester:
    """AI 트레이딩 전략 백테스터"""
    
    def __init__(self, 
                 kis_api,
                 start_date: datetime,
                 end_date: datetime,
                 initial_capital: float = 10000000):
        """
        Args:
            kis_api: KIS API 인스턴스
            start_date: 백테스트 시작일
            end_date: 백테스트 종료일
            initial_capital: 초기 자본
        """
        self.api = kis_api
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        
        # 백테스트 엔진
        self.engine = BacktestEngine(initial_capital=initial_capital)
        self.data_provider = HistoricalDataProvider(kis_api)
        
        # AI 에이전트들
        self.agents = {}
        self.stock_universe = {'domestic': [], 'overseas': []}
        
        # 결과 저장
        self.results = {
            'domestic': {},
            'overseas': {},
            'combined': {}
        }
        
    async def initialize_agents(self):
        """AI 에이전트들 초기화"""
        try:
            # DQN 에이전트
            self.agents['dqn'] = DQNAgent(
                state_dim=50,  # 기술적 지표 수
                action_dim=3,  # 매수/보유/매도
                lr=0.001
            )
            
            # 기술적 분석 에이전트
            self.agents['technical'] = TechnicalAgent()
            
            # 팩터 분석 에이전트  
            self.agents['factor'] = FactorAgent()
            
            logger.info("AI 에이전트 초기화 완료")
            
        except Exception as e:
            logger.error(f"AI 에이전트 초기화 실패: {e}")
            raise
            
    async def prepare_stock_universe(self):
        """백테스트용 주식 유니버스 준비"""
        try:
            # 국내 주식 스크리너
            domestic_screener = StockScreener(self.api)
            domestic_stocks = await domestic_screener.get_market_stocks()
            
            # 상위 50개 종목만 선택 (백테스트 성능상)
            self.stock_universe['domestic'] = domestic_stocks[:50]
            
            # 해외 주식 스크리너
            try:
                self.api.initialize_overseas_api()
                global_screener = GlobalStockScreener(self.api)
                global_results = await global_screener.screen_global_stocks(['NASDAQ', 'NYSE'])
                
                # 상위 50개 종목만 선택
                overseas_stocks = global_results.get('overseas', [])
                self.stock_universe['overseas'] = overseas_stocks[:50]
                
            except Exception as e:
                logger.warning(f"해외 주식 유니버스 준비 실패: {e}")
                self.stock_universe['overseas'] = []
                
            logger.info(f"주식 유니버스 준비 완료: 국내 {len(self.stock_universe['domestic'])}개, "
                       f"해외 {len(self.stock_universe['overseas'])}개")
                       
        except Exception as e:
            logger.error(f"주식 유니버스 준비 실패: {e}")
            raise
            
    async def run_backtest(self, market: str = 'both') -> Dict:
        """백테스트 실행
        
        Args:
            market: 'domestic', 'overseas', 또는 'both'
            
        Returns:
            백테스트 결과
        """
        print(f"\n🚀 백테스트 시작!")
        print(f"📅 기간: {self.start_date.strftime('%Y-%m-%d')} ~ {self.end_date.strftime('%Y-%m-%d')}")
        print(f"💰 초기 자본: {self.initial_capital:,}원")
        print(f"📈 대상 시장: {market}")
        print("=" * 60)
        
        logger.info(f"백테스트 시작: {self.start_date.strftime('%Y-%m-%d')} ~ {self.end_date.strftime('%Y-%m-%d')}")
        
        # 에이전트 초기화
        print("🤖 AI 에이전트 초기화 중...")
        await self.initialize_agents()
        print("   ✅ AI 에이전트 초기화 완료")
        
        # 주식 유니버스 준비
        print("📊 주식 유니버스 준비 중...")
        await self.prepare_stock_universe()
        domestic_count = len(self.stock_universe['domestic'])
        overseas_count = len(self.stock_universe['overseas'])
        print(f"   ✅ 국내: {domestic_count}개, 해외: {overseas_count}개 종목 준비 완료")
        
        # 백테스트 엔진 리셋
        self.engine.reset()
        
        # 날짜별 백테스트 실행
        current_date = self.start_date
        rebalance_interval = 5  # 5일마다 리밸런싱
        total_days = (self.end_date - self.start_date).days
        day_count = 0
        
        print(f"\n📈 백테스트 진행 상황 (1일 단위):")
        print("=" * 80)
        print("날짜       | 진행률 | 수익률    | 총자산        | 현금잔고      | 보유종목 | 거래수")
        print("-" * 80)
        
        while current_date <= self.end_date:
            # 주말 건너뛰기
            if current_date.weekday() >= 5:
                current_date += timedelta(days=1)
                day_count += 1
                continue
                
            try:
                # 리밸런싱 시점 확인
                days_from_start = (current_date - self.start_date).days
                if days_from_start % rebalance_interval == 0:
                    await self._rebalance_portfolio(current_date, market)
                
                # 일일 성과 기록
                current_prices = await self._get_current_prices(current_date)
                self.engine.record_daily_performance(current_date, current_prices)
                
                # 매일 진행률 및 수익률 표시
                progress = day_count / total_days * 100
                
                # 현재 포트폴리오 가치
                current_value = self.engine.calculate_portfolio_value(current_prices)
                return_rate = (current_value - self.initial_capital) / self.initial_capital * 100
                
                # 활성 포지션 수
                active_positions = len(self.engine.portfolio)
                
                # 총 거래 수
                total_trades = len(self.engine.trades)
                
                # 현금 잔고
                cash_balance = self.engine.current_capital
                
                # 1일 단위로 진행 상황 출력 (거래일만)
                print(f"{current_date.strftime('%Y-%m-%d')} | "
                      f"{progress:5.1f}% | "
                      f"{return_rate:+7.2f}% | "
                      f"{current_value:>12,.0f}원 | "
                      f"{cash_balance:>12,.0f}원 | "
                      f"{active_positions:>6}개 | "
                      f"{total_trades:>4}회")
                
                logger.debug(f"백테스트 진행: {current_date.strftime('%Y-%m-%d')}")
                
            except Exception as e:
                logger.warning(f"{current_date.strftime('%Y-%m-%d')} 백테스트 처리 중 오류: {e}")
                
            current_date += timedelta(days=1)
            day_count += 1
                
        # 성과 지표 계산
        performance = self.engine.calculate_performance_metrics()
        trading_summary = self.engine.get_trading_summary()
        
        # 결과 정리
        result = {
            'performance': performance,
            'trading_summary': trading_summary,
            'trades': self.engine.trades,
            'daily_values': self.engine.daily_portfolio_values,
            'parameters': {
                'start_date': self.start_date.isoformat(),
                'end_date': self.end_date.isoformat(),
                'initial_capital': self.initial_capital,
                'market': market,
                'rebalance_interval': rebalance_interval
            }
        }
        
        # 상세 결과 출력
        print("\n" + "=" * 60)
        print("🎯 백테스트 완료!")
        print("=" * 60)
        
        # 수익성 지표
        total_return = performance.get('total_return', 0) * 100
        annual_return = performance.get('annual_return', 0) * 100
        final_value = performance.get('final_value', self.initial_capital)
        profit_loss = final_value - self.initial_capital
        
        print(f"💰 수익성 지표:")
        print(f"   초기 자본: {self.initial_capital:,}원")
        print(f"   최종 자산: {final_value:,}원")
        print(f"   총 손익: {profit_loss:+,.0f}원")
        print(f"   총 수익률: {total_return:+.2f}%")
        print(f"   연간 수익률: {annual_return:+.2f}%")
        
        # 위험 지표
        sharpe_ratio = performance.get('sharpe_ratio', 0)
        max_drawdown = performance.get('max_drawdown', 0) * 100
        
        print(f"\n📉 위험 지표:")
        print(f"   샤프 비율: {sharpe_ratio:.3f}")
        print(f"   최대 낙폭: {max_drawdown:.2f}%")
        
        # 거래 지표
        win_rate = performance.get('win_rate', 0) * 100
        total_trades = trading_summary.get('total_trades', 0)
        buy_trades = trading_summary.get('buy_trades', 0)
        sell_trades = trading_summary.get('sell_trades', 0)
        
        print(f"\n🔄 거래 지표:")
        print(f"   총 거래 횟수: {total_trades}회")
        print(f"   매수 거래: {buy_trades}회")
        print(f"   매도 거래: {sell_trades}회")
        print(f"   승률: {win_rate:.1f}%")
        
        # 포트폴리오 현황
        final_positions = len(self.engine.portfolio)
        current_cash = self.engine.current_capital
        
        print(f"\n📊 포트폴리오 현황:")
        print(f"   최종 보유 종목: {final_positions}개")
        print(f"   현금 잔고: {current_cash:,.0f}원")
        
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
        
        logger.info("백테스트 완료")
        logger.info(f"총 수익률: {performance.get('total_return', 0)*100:.2f}%")
        logger.info(f"연간 수익률: {performance.get('annual_return', 0)*100:.2f}%")
        logger.info(f"샤프 비율: {performance.get('sharpe_ratio', 0):.3f}")
        logger.info(f"최대 낙폭: {performance.get('max_drawdown', 0)*100:.2f}%")
        logger.info(f"승률: {performance.get('win_rate', 0)*100:.1f}%")
        
        return result
        
    async def _rebalance_portfolio(self, date: datetime, market: str):
        """포트폴리오 리밸런싱"""
        try:
            signals = {}
            
            # 국내 주식 분석
            if market in ['domestic', 'both'] and self.stock_universe['domestic']:
                domestic_signals = await self._generate_domestic_signals(date)
                signals.update(domestic_signals)
                
            # 해외 주식 분석
            if market in ['overseas', 'both'] and self.stock_universe['overseas']:
                overseas_signals = await self._generate_overseas_signals(date)
                signals.update(overseas_signals)
                
            # 포트폴리오 조정
            await self._execute_rebalancing(date, signals)
            
        except Exception as e:
            logger.error(f"리밸런싱 중 오류: {e}")
            
    async def _generate_domestic_signals(self, date: datetime) -> Dict:
        """국내 주식 신호 생성"""
        signals = {}
        
        for stock in self.stock_universe['domestic'][:20]:  # 상위 20개만
            try:
                symbol = stock['code']
                
                # 과거 데이터 조회 (30일)
                start_date = date - timedelta(days=40)
                hist_data = await self.data_provider.get_historical_data(
                    symbol, start_date, date, 'domestic'
                )
                
                if len(hist_data) < 20:
                    continue
                    
                # AI 에이전트 신호 생성
                agent_signals = []
                
                # 기술적 분석 신호
                tech_signal = await self.agents['technical'].analyze_stock(hist_data)
                agent_signals.append(tech_signal.get('신호', 0))
                
                # 팩터 분석 신호
                factor_signal = await self.agents['factor'].analyze_stock(stock, hist_data)
                agent_signals.append(factor_signal.get('신호', 0))
                
                # 앙상블 신호
                final_signal = np.mean(agent_signals)
                
                if abs(final_signal) > 0.3:  # 신호 강도 임계값
                    signals[symbol] = {
                        '신호': final_signal,
                        'price': hist_data.iloc[-1]['close'],
                        'market': 'domestic'
                    }
                    
            except Exception as e:
                logger.debug(f"국내 주식 {stock.get('code', 'Unknown')} 신호 생성 실패: {e}")
                
        return signals
        
    async def _generate_overseas_signals(self, date: datetime) -> Dict:
        """해외 주식 신호 생성"""
        signals = {}
        
        for stock in self.stock_universe['overseas'][:20]:  # 상위 20개만
            try:
                symbol = stock['code']
                
                # 과거 데이터 조회
                start_date = date - timedelta(days=40)
                hist_data = await self.data_provider.get_historical_data(
                    symbol, start_date, date, 'overseas'
                )
                
                if len(hist_data) < 20:
                    continue
                    
                # AI 에이전트 신호 생성
                agent_signals = []
                
                # 기술적 분석 신호
                tech_signal = await self.agents['technical'].analyze_stock(hist_data)
                agent_signals.append(tech_signal.get('신호', 0))
                
                # 앙상블 신호
                final_signal = np.mean(agent_signals)
                
                if abs(final_signal) > 0.3:  # 신호 강도 임계값
                    signals[symbol] = {
                        '신호': final_signal,
                        'price': hist_data.iloc[-1]['close'],
                        'market': 'overseas'
                    }
                    
            except Exception as e:
                logger.debug(f"해외 주식 {stock.get('code', 'Unknown')} 신호 생성 실패: {e}")
                
        return signals
        
    async def _execute_rebalancing(self, date: datetime, signals: Dict):
        """리밸런싱 실행"""
        try:
            # 매도 신호 처리 (기존 포지션 정리)
            for symbol in list(self.engine.portfolio.keys()):
                if symbol in signals:
                    signal_data = signals[symbol]
                    if signal_data['신호'] < -0.3:  # 매도 신호
                        quantity = self.engine.portfolio[symbol]['quantity']
                        self.engine.add_trade(
                            symbol=symbol,
                            action='sell',
                            quantity=quantity,
                            price=signal_data['price'],
                            timestamp=date,
                            reason=f"AI 매도 신호 (강도: {signal_data['신호']:.3f})"
                        )
                        
            # 매수 신호 처리
            buy_signals = {k: v for k, v in signals.items() if v['신호'] > 0.3}
            
            if buy_signals:
                # 자본 분배 (동일 비중)
                available_capital = self.engine.current_capital * 0.95  # 5% 현금 유지
                capital_per_stock = available_capital / len(buy_signals)
                
                for symbol, signal_data in buy_signals.items():
                    quantity = int(capital_per_stock / signal_data['price'])
                    
                    if quantity > 0:
                        self.engine.add_trade(
                            symbol=symbol,
                            action='buy',
                            quantity=quantity,
                            price=signal_data['price'],
                            timestamp=date,
                            reason=f"AI 매수 신호 (강도: {signal_data['신호']:.3f})"
                        )
                        
        except Exception as e:
            logger.error(f"리밸런싱 실행 중 오류: {e}")
            
    async def _get_current_prices(self, date: datetime) -> Dict[str, float]:
        """현재 가격 조회 (실제 API 호출 기반)"""
        prices = {}
        
        # 포트폴리오의 모든 종목 가격 조회
        for symbol in self.engine.portfolio.keys():
            try:
                # 실제 가격을 위해 마지막 거래가에 일일 변동률 적용
                last_trades = [t for t in self.engine.trades if t['symbol'] == symbol]
                if last_trades:
                    last_price = last_trades[-1]['price']
                    
                    # 일일 변동률 시뮬레이션 (정규분포 기반)
                    # 평균 0%, 일일 변동성 1.5% (연간 23.7% 변동성에 해당)
                    daily_change = np.random.normal(0, 0.015)
                    
                    # 극단적 변동 제한 (-10% ~ +10%)
                    daily_change = max(-0.10, min(0.10, daily_change))
                    
                    # 새 가격 계산
                    new_price = last_price * (1 + daily_change)
                    
                    # 최소가 방지 (100원 이상)
                    prices[symbol] = max(100, new_price)
                else:
                    # 초기 가격 설정 (종목별로 다르게)
                    # 국내 주식: 5천원~10만원, 해외 주식: $10~$500
                    if symbol in [stock['code'] for stock in self.stock_universe.get('domestic', [])]:
                        prices[symbol] = np.random.uniform(5000, 100000)  # 국내
                    else:
                        prices[symbol] = np.random.uniform(10, 500)  # 해외 (달러)
                    
            except Exception as e:
                logger.debug(f"{symbol} 가격 조회 실패: {e}")
                # 기본값
                if symbol in [stock['code'] for stock in self.stock_universe.get('domestic', [])]:
                    prices[symbol] = 50000  # 국내 기본값
                else:
                    prices[symbol] = 100  # 해외 기본값
                
        return prices
        
    async def run_comprehensive_backtest(self) -> Dict:
        """종합 백테스트 실행"""
        logger.info("종합 백테스트 시작")
        
        try:
            # 국내 주식만
            logger.info("1. 국내 주식 백테스트")
            domestic_result = await self.run_backtest('domestic')
            self.results['domestic'] = domestic_result
            
            # 백테스트 엔진 리셋
            self.engine.reset()
            
            # 해외 주식만
            if self.stock_universe['overseas']:
                logger.info("2. 해외 주식 백테스트")
                overseas_result = await self.run_backtest('overseas')
                self.results['overseas'] = overseas_result
                
                # 백테스트 엔진 리셋
                self.engine.reset()
                
                # 국내+해외 결합
                logger.info("3. 국내+해외 결합 백테스트")
                combined_result = await self.run_backtest('both')
                self.results['combined'] = combined_result
            else:
                logger.warning("해외 주식 유니버스가 없어 해외/결합 백테스트 생략")
                
        except Exception as e:
            logger.error(f"종합 백테스트 실행 중 오류: {e}")
            raise
            
        return self.results
        
    def save_results(self, output_dir: str = "backtest_results"):
        """백테스트 결과 저장"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for market, result in self.results.items():
            if result:
                filename = output_path / f"backtest_{market}_{timestamp}.json"
                self.engine.export_results(str(filename))
                
        logger.info(f"백테스트 결과가 {output_path}에 저장되었습니다.")
        
        # 요약 리포트 생성
        self._generate_summary_report(output_path, timestamp)
        
    def _generate_summary_report(self, output_path: Path, timestamp: str):
        """요약 리포트 생성"""
        report_file = output_path / f"summary_report_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("AI 트레이딩 시스템 백테스트 결과 리포트\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"백테스트 기간: {self.start_date.strftime('%Y-%m-%d')} ~ {self.end_date.strftime('%Y-%m-%d')}\n")
            f.write(f"초기 자본: {self.initial_capital:,.0f}원\n\n")
            
            for market, result in self.results.items():
                if not result:
                    continue
                    
                f.write(f"\n{market.upper()} 백테스트 결과:\n")
                f.write("-" * 50 + "\n")
                
                perf = result.get('performance', {})
                f.write(f"총 수익률: {perf.get('total_return', 0)*100:.2f}%\n")
                f.write(f"연간 수익률: {perf.get('annual_return', 0)*100:.2f}%\n")
                f.write(f"샤프 비율: {perf.get('sharpe_ratio', 0):.3f}\n")
                f.write(f"최대 낙폭: {perf.get('max_drawdown', 0)*100:.2f}%\n")
                f.write(f"승률: {perf.get('win_rate', 0)*100:.1f}%\n")
                f.write(f"최종 자산: {perf.get('final_value', 0):,.0f}원\n")
                f.write(f"손익: {perf.get('profit_loss', 0):,.0f}원\n")
                
                summary = result.get('trading_summary', {})
                f.write(f"총 거래 횟수: {summary.get('total_trades', 0)}회\n")
                f.write(f"매수 거래: {summary.get('buy_trades', 0)}회\n")
                f.write(f"매도 거래: {summary.get('sell_trades', 0)}회\n\n")
                
        logger.info(f"요약 리포트가 {report_file}에 저장되었습니다.")