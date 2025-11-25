"""
완전 자동매매 시스템
- 종목 자동 선정
- 매수/매도 자동 실행
- 손절/익절 관리
- 포트폴리오 관리
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from kis_api import KisAPI
from config import Config
from strategy import TradingStrategy
from screener import StockScreener


class AutoTrader:
    """완전 자동매매 시스템"""

    def __init__(self, mode: str = "demo", style: str = "neutral", total_capital: int = 10000000):
        """
        Args:
            mode: 투자 모드 ('demo' 또는 'real')
            style: 투자 성향 ('conservative', 'neutral', 'aggressive')
            total_capital: 총 투자금
        """
        self.mode = mode
        self.style = style
        self.total_capital = total_capital
        self.is_real = (mode == 'real')

        # API 초기화
        account_info = Config.get_account_info(mode)
        self.api = KisAPI(
            account_info['appkey'],
            account_info['appsecret'],
            account_info['account'],
            is_real=self.is_real
        )

        # 전략 및 스크리너
        self.strategy = TradingStrategy(style=style)
        self.screener = StockScreener(self.api, style=style)

        # 포트폴리오 상태
        self.portfolio: Dict[str, Dict] = {}  # {종목코드: {수량, 평균매수가, ...}}
        self.trade_history: List[Dict] = []
        self.daily_trades = 0
        self.max_daily_trades = 10

        # 설정
        self.params = self.strategy.params
        self.portfolio_file = f"portfolio_{mode}.json"

        # 포트폴리오 로드
        self._load_portfolio()

    def _load_portfolio(self):
        """저장된 포트폴리오 로드"""
        try:
            if os.path.exists(self.portfolio_file):
                with open(self.portfolio_file, 'r') as f:
                    data = json.load(f)
                    self.portfolio = data.get('portfolio', {})
                    self.trade_history = data.get('history', [])
                print(f"포트폴리오 로드 완료: {len(self.portfolio)}개 종목")
        except Exception as e:
            print(f"포트폴리오 로드 실패: {e}")

    def _save_portfolio(self):
        """포트폴리오 저장"""
        try:
            data = {
                'portfolio': self.portfolio,
                'history': self.trade_history[-100:],  # 최근 100개만
                'updated': datetime.now().isoformat()
            }
            with open(self.portfolio_file, 'w') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"포트폴리오 저장 실패: {e}")

    def connect(self) -> bool:
        """API 연결"""
        print(f"\n{'='*50}")
        print(f"자동매매 시스템 시작")
        print(f"모드: {'실전투자' if self.is_real else '모의투자'}")
        print(f"성향: {self.style}")
        print(f"투자금: {self.total_capital:,}원")
        print(f"{'='*50}\n")

        if self.api.get_access_token():
            print("API 연결 성공!")
            return True
        else:
            print("API 연결 실패!")
            return False

    def get_available_cash(self) -> int:
        """주문 가능 현금 조회"""
        balance = self.api.get_balance()
        if balance and balance.get('rt_cd') == '0':
            output2 = balance.get('output2', [{}])[0]
            cash = int(output2.get('ord_psbl_cash', 0))
            return cash
        return 0

    def sync_portfolio(self):
        """실제 잔고와 포트폴리오 동기화"""
        print("\n포트폴리오 동기화 중...")
        balance = self.api.get_balance()

        if not balance or balance.get('rt_cd') != '0':
            print("잔고 조회 실패")
            return

        holdings = balance.get('output1', [])
        synced = {}

        for item in holdings:
            code = item.get('pdno', '')
            name = item.get('prdt_name', '')
            quantity = int(item.get('hldg_qty', 0))
            avg_price = float(item.get('pchs_avg_pric', 0))
            current_price = int(item.get('prpr', 0))
            profit_rate = float(item.get('evlu_pfls_rt', 0))

            if quantity > 0:
                synced[code] = {
                    'name': name,
                    'quantity': quantity,
                    'avg_price': avg_price,
                    'current_price': current_price,
                    'profit_rate': profit_rate,
                    'buy_date': self.portfolio.get(code, {}).get('buy_date', datetime.now().isoformat())
                }

        self.portfolio = synced
        self._save_portfolio()
        print(f"동기화 완료: {len(self.portfolio)}개 종목 보유 중")

    def check_sell_signals(self):
        """보유 종목 매도 신호 확인"""
        print("\n=== 매도 신호 확인 ===")

        for code, holding in list(self.portfolio.items()):
            try:
                name = holding['name']
                avg_price = holding['avg_price']
                quantity = holding['quantity']

                # 현재가 조회
                price_data = self.api.get_stock_price(code)
                if not price_data or price_data.get('rt_cd') != '0':
                    continue

                current_price = int(price_data['output'].get('stck_prpr', 0))
                profit_rate = (current_price - avg_price) / avg_price

                print(f"\n{name}({code})")
                print(f"  평균매수가: {avg_price:,.0f}원")
                print(f"  현재가: {current_price:,}원")
                print(f"  수익률: {profit_rate*100:+.2f}%")

                # 손절 확인
                if self.strategy.check_stop_loss(avg_price, current_price):
                    print(f"  => 손절 신호! ({self.params['stop_loss']*100}% 도달)")
                    self._execute_sell(code, name, quantity, current_price, "STOP_LOSS")
                    continue

                # 익절 확인
                if self.strategy.check_take_profit(avg_price, current_price):
                    print(f"  => 익절 신호! ({self.params['take_profit']*100}% 도달)")
                    self._execute_sell(code, name, quantity, current_price, "TAKE_PROFIT")
                    continue

                # 기술적 분석 매도 신호
                analysis = self.screener.analyze_single_stock(code)
                if analysis and self.strategy.should_sell(analysis['analysis']):
                    print(f"  => 기술적 매도 신호!")
                    print(f"     시그널: {', '.join(analysis['analysis']['signals'][:3])}")
                    self._execute_sell(code, name, quantity, current_price, "SIGNAL_SELL")

                time.sleep(0.3)

            except Exception as e:
                print(f"  {code} 매도 확인 실패: {e}")

    def check_buy_signals(self):
        """매수 신호 확인 및 실행"""
        print("\n=== 매수 신호 확인 ===")

        # 현재 보유 종목 수 확인
        current_positions = len(self.portfolio)
        max_positions = self.params['max_positions']

        if current_positions >= max_positions:
            print(f"최대 보유 종목 수 도달 ({current_positions}/{max_positions})")
            return

        # 가용 현금 확인
        available_cash = self.get_available_cash()
        min_buy_amount = self.total_capital * self.params['position_size'] * 0.5

        if available_cash < min_buy_amount:
            print(f"가용 현금 부족: {available_cash:,}원")
            return

        # 매수 후보 스크리닝
        candidates = self.screener.screen_buy_candidates(
            max_candidates=max_positions - current_positions
        )

        # 이미 보유 중인 종목 제외
        candidates = [c for c in candidates if c['code'] not in self.portfolio]

        if not candidates:
            print("매수 후보 없음")
            return

        # 매수 실행
        for candidate in candidates:
            if self.daily_trades >= self.max_daily_trades:
                print("일일 최대 거래 횟수 도달")
                break

            if len(self.portfolio) >= max_positions:
                break

            code = candidate['code']
            name = candidate['name']
            price = candidate['price']

            # 매수 수량 계산
            quantity = self.strategy.calculate_position_size(self.total_capital, price)

            # 가용 현금 재확인
            if price * quantity > available_cash:
                quantity = int(available_cash / price)

            if quantity < 1:
                continue

            self._execute_buy(code, name, quantity, price)
            available_cash -= price * quantity
            time.sleep(1)

    def _execute_buy(self, code: str, name: str, quantity: int, price: int):
        """매수 실행"""
        print(f"\n매수 주문: {name}({code}) {quantity}주 @ {price:,}원")

        if self.is_real:
            confirm = input("실전 매수를 진행하시겠습니까? (y/N): ").strip().lower()
            if confirm != 'y':
                print("매수 취소")
                return

        result = self.api.buy_stock(code, quantity, order_type="03")  # 시장가

        if result and result.get('rt_cd') == '0':
            print(f"  => 매수 주문 성공!")

            self.portfolio[code] = {
                'name': name,
                'quantity': quantity,
                'avg_price': price,
                'current_price': price,
                'profit_rate': 0,
                'buy_date': datetime.now().isoformat()
            }

            self.trade_history.append({
                'type': 'BUY',
                'code': code,
                'name': name,
                'quantity': quantity,
                'price': price,
                'datetime': datetime.now().isoformat()
            })

            self.daily_trades += 1
            self._save_portfolio()
        else:
            error_msg = result.get('msg1', 'Unknown error') if result else 'No response'
            print(f"  => 매수 주문 실패: {error_msg}")

    def _execute_sell(self, code: str, name: str, quantity: int, price: int, reason: str):
        """매도 실행"""
        print(f"\n매도 주문: {name}({code}) {quantity}주 @ {price:,}원 ({reason})")

        if self.is_real:
            confirm = input("실전 매도를 진행하시겠습니까? (y/N): ").strip().lower()
            if confirm != 'y':
                print("매도 취소")
                return

        result = self.api.sell_stock(code, quantity, order_type="03")  # 시장가

        if result and result.get('rt_cd') == '0':
            print(f"  => 매도 주문 성공!")

            # 수익 계산
            if code in self.portfolio:
                buy_price = self.portfolio[code]['avg_price']
                profit = (price - buy_price) * quantity
                profit_rate = (price - buy_price) / buy_price * 100
                print(f"  => 실현 손익: {profit:+,.0f}원 ({profit_rate:+.2f}%)")

                del self.portfolio[code]

            self.trade_history.append({
                'type': 'SELL',
                'code': code,
                'name': name,
                'quantity': quantity,
                'price': price,
                'reason': reason,
                'datetime': datetime.now().isoformat()
            })

            self.daily_trades += 1
            self._save_portfolio()
        else:
            error_msg = result.get('msg1', 'Unknown error') if result else 'No response'
            print(f"  => 매도 주문 실패: {error_msg}")

    def show_status(self):
        """현재 상태 출력"""
        print("\n" + "="*60)
        print("현재 포트폴리오 상태")
        print("="*60)

        self.sync_portfolio()

        if not self.portfolio:
            print("보유 종목 없음")
        else:
            total_value = 0
            total_profit = 0

            for code, holding in self.portfolio.items():
                value = holding['current_price'] * holding['quantity']
                profit = (holding['current_price'] - holding['avg_price']) * holding['quantity']
                total_value += value
                total_profit += profit

                print(f"\n{holding['name']}({code})")
                print(f"  수량: {holding['quantity']}주")
                print(f"  평균매수가: {holding['avg_price']:,.0f}원")
                print(f"  현재가: {holding['current_price']:,}원")
                print(f"  수익률: {holding['profit_rate']:+.2f}%")
                print(f"  평가손익: {profit:+,.0f}원")

            print(f"\n{'='*60}")
            print(f"총 평가금액: {total_value:,}원")
            print(f"총 평가손익: {total_profit:+,.0f}원")

        cash = self.get_available_cash()
        print(f"가용 현금: {cash:,}원")
        print(f"오늘 거래: {self.daily_trades}/{self.max_daily_trades}회")
        print("="*60)

    def run_once(self):
        """한 번 실행 (수동)"""
        if not self.connect():
            return

        self.show_status()
        self.check_sell_signals()
        self.check_buy_signals()
        self.show_status()

    def run_auto(self, interval_minutes: int = 30):
        """자동 실행 (스케줄러)"""
        if not self.connect():
            return

        print(f"\n자동매매 시작 (주기: {interval_minutes}분)")
        print("중지하려면 Ctrl+C를 누르세요.\n")

        try:
            while True:
                now = datetime.now()
                hour = now.hour

                # 장 시간 체크 (09:00 ~ 15:30)
                if 9 <= hour < 16:
                    print(f"\n[{now.strftime('%Y-%m-%d %H:%M:%S')}] 자동매매 실행")

                    # 매일 첫 실행 시 일일 거래 횟수 초기화
                    if hour == 9 and now.minute < interval_minutes:
                        self.daily_trades = 0

                    self.sync_portfolio()
                    self.check_sell_signals()
                    self.check_buy_signals()
                    self.show_status()
                else:
                    print(f"\n[{now.strftime('%H:%M')}] 장 마감 (09:00~15:30 외)")

                print(f"\n다음 실행: {interval_minutes}분 후")
                time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            print("\n\n자동매매 중지")
            self._save_portfolio()


def main():
    """메인 함수"""
    print("="*60)
    print("완전 자동매매 시스템")
    print("="*60)

    # 설정
    print("\n[설정]")
    print("1. 모의투자 (테스트)")
    print("2. 실전투자 (주의!)")
    mode_choice = input("선택 (1/2) [기본값: 1]: ").strip() or "1"
    mode = "real" if mode_choice == "2" else "demo"

    if mode == "real":
        print("\n실전투자 모드를 선택하셨습니다.")
        confirm = input("실제 자금으로 거래됩니다. 계속하시겠습니까? (y/N): ").strip().lower()
        if confirm != 'y':
            mode = "demo"
            print("모의투자 모드로 변경합니다.")

    print("\n[투자 성향]")
    print("1. 보수적 (손절 -3%, 익절 +7%)")
    print("2. 중립 (손절 -5%, 익절 +10%)")
    print("3. 공격적 (손절 -7%, 익절 +15%)")
    style_choice = input("선택 (1/2/3) [기본값: 2]: ").strip() or "2"
    style_map = {"1": "conservative", "2": "neutral", "3": "aggressive"}
    style = style_map.get(style_choice, "neutral")

    capital_input = input("\n투자금 (원) [기본값: 10000000]: ").strip()
    capital = int(capital_input) if capital_input else 10000000

    # 자동매매 시작
    trader = AutoTrader(mode=mode, style=style, total_capital=capital)

    print("\n[실행 모드]")
    print("1. 한 번 실행")
    print("2. 자동 실행 (스케줄러)")
    run_choice = input("선택 (1/2) [기본값: 1]: ").strip() or "1"

    if run_choice == "2":
        interval = input("실행 주기 (분) [기본값: 30]: ").strip()
        interval = int(interval) if interval else 30
        trader.run_auto(interval_minutes=interval)
    else:
        trader.run_once()


if __name__ == "__main__":
    main()
