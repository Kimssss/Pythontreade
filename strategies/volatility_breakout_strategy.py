"""
변동성 돌파 전략 (Volatility Breakout Strategy)

래리 윌리엄스(Larry Williams)의 변동성 돌파 전략

[핵심 공식]
매수 목표가 = 당일 시가 + (전일 고가 - 전일 저가) × K

[매수 조건]
- 현재가 > 매수 목표가
- 장 시작 후 일정 시간 경과 (노이즈 제거)

[매도 조건]
- 장 마감 전 전량 매도 (당일 청산)
- 손절가 도달 시 즉시 매도

[K값]
- 0.5가 기본값 (0.1~0.9 조절 가능)
- K값이 낮을수록: 진입 쉬움, 리스크 높음, 수익률 높음
- K값이 높을수록: 진입 어려움, 리스크 낮음, 수익률 낮음
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple


class VolatilityBreakoutStrategy:
    """변동성 돌파 전략"""

    def __init__(self, api, config: Dict = None):
        """
        초기화

        Args:
            api: KisAPI 인스턴스
            config: 전략 설정
        """
        self.api = api

        # 기본 설정
        default_config = {
            # K값 설정
            'k_value': 0.5,              # 변동성 돌파 K값 (0.1~0.9)

            # 종목 선택 조건
            'min_price': 1000,           # 최소 주가
            'max_price': 500000,         # 최대 주가
            'min_volume': 100000,        # 최소 거래량

            # 매수 조건
            'buy_start_time': (9, 10),   # 매수 시작 시간 (09:10)
            'buy_end_time': (14, 30),    # 매수 종료 시간 (14:30)

            # 매도 조건
            'sell_time': (15, 15),       # 청산 시간 (15:15)
            'stop_loss': -2.0,           # 손절 기준 (-2%)

            # 자금 관리
            'max_stocks': 3,             # 최대 보유 종목 수
            'position_ratio': 0.3,       # 종목당 투자 비율 (30%)
            'max_buy_per_day': 3,        # 일일 최대 매수 횟수

            # 대상 종목 (빈 리스트면 거래량 상위 종목 자동 선택)
            'target_stocks': [],         # 예: ['005930', '000660']
        }

        self.config = {**default_config, **(config or {})}

        # 거래 기록
        self.trade_history = []
        self.daily_buy_count = 0
        self.last_trade_date = None

        # 당일 매수 정보 (종목별 매수가 저장)
        self.today_positions = {}  # {code: {'buy_price': price, 'quantity': qty, 'target': target}}

        # 전일 데이터 캐시
        self.prev_day_data = {}  # {code: {'high': h, 'low': l, 'open': o}}

    def reset_daily_data(self):
        """일일 데이터 리셋"""
        today = datetime.now().date()
        if self.last_trade_date != today:
            self.daily_buy_count = 0
            self.today_positions = {}
            self.prev_day_data = {}
            self.last_trade_date = today
            print(f"📅 새로운 거래일: {today}")

    def get_previous_day_data(self, stock_code: str) -> Optional[Dict]:
        """
        전일 시세 데이터 조회

        Args:
            stock_code: 종목코드

        Returns:
            전일 데이터 {'high': 고가, 'low': 저가, 'open': 시가, 'close': 종가}
        """
        # 캐시 확인
        if stock_code in self.prev_day_data:
            return self.prev_day_data[stock_code]

        # API로 일별 시세 조회
        daily_data = self.api.get_daily_price(stock_code)

        if not daily_data or daily_data.get('rt_cd') != '0':
            return None

        output = daily_data.get('output', [])

        if len(output) < 2:
            return None

        # output[0]은 당일, output[1]은 전일
        prev_day = output[1]

        try:
            data = {
                'high': int(prev_day.get('stck_hgpr', 0)),    # 전일 고가
                'low': int(prev_day.get('stck_lwpr', 0)),     # 전일 저가
                'open': int(prev_day.get('stck_oprc', 0)),    # 전일 시가
                'close': int(prev_day.get('stck_clpr', 0)),   # 전일 종가
            }

            # 유효성 검사
            if data['high'] > 0 and data['low'] > 0:
                self.prev_day_data[stock_code] = data
                return data

        except (ValueError, TypeError):
            pass

        return None

    def get_today_open_price(self, stock_code: str) -> Optional[int]:
        """
        당일 시가 조회

        Args:
            stock_code: 종목코드

        Returns:
            당일 시가
        """
        daily_data = self.api.get_daily_price(stock_code)

        if not daily_data or daily_data.get('rt_cd') != '0':
            return None

        output = daily_data.get('output', [])

        if not output:
            return None

        # output[0]이 당일
        today = output[0]

        try:
            return int(today.get('stck_oprc', 0))
        except (ValueError, TypeError):
            return None

    def calculate_target_price(self, stock_code: str) -> Optional[Dict]:
        """
        매수 목표가 계산

        Args:
            stock_code: 종목코드

        Returns:
            {
                'target_price': 매수목표가,
                'today_open': 당일시가,
                'prev_range': 전일변동폭,
                'k_value': K값
            }
        """
        # 전일 데이터
        prev_data = self.get_previous_day_data(stock_code)
        if not prev_data:
            return None

        # 당일 시가
        today_open = self.get_today_open_price(stock_code)
        if not today_open:
            return None

        # 변동폭 계산
        prev_range = prev_data['high'] - prev_data['low']

        if prev_range <= 0:
            return None

        # 목표가 계산: 당일시가 + (전일고가 - 전일저가) × K
        k = self.config['k_value']
        target_price = today_open + int(prev_range * k)

        return {
            'target_price': target_price,
            'today_open': today_open,
            'prev_range': prev_range,
            'prev_high': prev_data['high'],
            'prev_low': prev_data['low'],
            'k_value': k
        }

    def get_target_stocks(self) -> List[Dict]:
        """
        매매 대상 종목 조회

        Returns:
            대상 종목 리스트
        """
        # 사용자 지정 종목이 있으면 그것 사용
        if self.config['target_stocks']:
            stocks = []
            for code in self.config['target_stocks']:
                price_info = self.api.get_stock_price(code)
                if price_info and price_info.get('rt_cd') == '0':
                    output = price_info.get('output', {})
                    stocks.append({
                        'code': code,
                        'name': output.get('prdt_name', code),
                        'price': int(output.get('stck_prpr', 0)),
                        'volume': int(output.get('acml_vol', 0))
                    })
            return stocks

        # 거래량 상위 종목에서 선택
        candidates = []

        for market in ['J', 'Q']:  # 코스피, 코스닥
            volume_data = self.api.get_volume_rank(market)

            if not volume_data or volume_data.get('rt_cd') != '0':
                continue

            stocks = volume_data.get('output', [])

            for stock in stocks[:20]:
                try:
                    code = stock.get('mksc_shrn_iscd', '')
                    name = stock.get('hts_kor_isnm', '')
                    price = int(stock.get('stck_prpr', 0))
                    volume = int(stock.get('acml_vol', 0))

                    # 가격 필터
                    if not (self.config['min_price'] <= price <= self.config['max_price']):
                        continue

                    # 거래량 필터
                    if volume < self.config['min_volume']:
                        continue

                    candidates.append({
                        'code': code,
                        'name': name,
                        'price': price,
                        'volume': volume,
                        'market': 'KOSPI' if market == 'J' else 'KOSDAQ'
                    })

                except (ValueError, TypeError):
                    continue

        # 거래량 순 정렬
        candidates.sort(key=lambda x: x['volume'], reverse=True)

        return candidates[:10]  # 상위 10개

    def check_buy_signal(self, stock: Dict) -> Optional[Dict]:
        """
        매수 신호 확인

        Args:
            stock: 종목 정보

        Returns:
            매수 신호 정보 또는 None
        """
        code = stock['code']
        current_price = stock['price']

        # 목표가 계산
        target_info = self.calculate_target_price(code)

        if not target_info:
            return None

        target_price = target_info['target_price']

        # 매수 조건: 현재가 > 목표가
        if current_price > target_price:
            return {
                'code': code,
                'name': stock.get('name', code),
                'current_price': current_price,
                'target_price': target_price,
                'today_open': target_info['today_open'],
                'prev_range': target_info['prev_range'],
                'k_value': target_info['k_value'],
                'breakout_rate': (current_price - target_price) / target_price * 100
            }

        return None

    def is_buy_time(self) -> bool:
        """매수 가능 시간 확인"""
        now = datetime.now()
        current_time = (now.hour, now.minute)

        return (self.config['buy_start_time'] <= current_time <= self.config['buy_end_time'])

    def is_sell_time(self) -> bool:
        """청산 시간 확인"""
        now = datetime.now()
        current_time = (now.hour, now.minute)

        return current_time >= self.config['sell_time']

    def check_sell_signals(self, holdings: List[Dict]) -> List[Dict]:
        """
        매도 신호 확인

        Args:
            holdings: 보유 종목 리스트

        Returns:
            매도 대상 리스트
        """
        sell_targets = []
        is_closing_time = self.is_sell_time()

        for stock in holdings:
            code = stock['stock_code']
            current_price = stock['current_price']
            profit_rate = stock['profit_rate']

            sell_reason = None

            # 1. 청산 시간 (15:15 이후)
            if is_closing_time:
                sell_reason = f"장 마감 청산 ({profit_rate:+.2f}%)"

            # 2. 손절
            elif profit_rate <= self.config['stop_loss']:
                sell_reason = f"손절 ({profit_rate:.2f}%)"

            if sell_reason:
                sell_targets.append({
                    'code': code,
                    'name': stock['stock_name'],
                    'quantity': stock['quantity'],
                    'buy_price': stock['buy_price'],
                    'current_price': current_price,
                    'profit_rate': profit_rate,
                    'reason': sell_reason
                })

        return sell_targets

    def calculate_buy_quantity(self, price: int, available_cash: int) -> int:
        """
        매수 수량 계산

        Args:
            price: 주가
            available_cash: 가용 현금

        Returns:
            매수 수량
        """
        invest_amount = int(available_cash * self.config['position_ratio'])
        quantity = invest_amount // price

        return max(0, quantity)

    def execute_buy(self, signal: Dict, quantity: int) -> Tuple[bool, str]:
        """
        매수 실행

        Args:
            signal: 매수 신호 정보
            quantity: 매수 수량

        Returns:
            (성공여부, 메시지)
        """
        code = signal['code']
        name = signal['name']
        price = signal['current_price']

        result = self.api.buy_stock(code, quantity, order_type="03")  # 시장가

        if result and result.get('rt_cd') == '0':
            order_no = result.get('output', {}).get('ODNO', 'N/A')

            # 포지션 기록
            self.today_positions[code] = {
                'buy_price': price,
                'quantity': quantity,
                'target_price': signal['target_price'],
                'buy_time': datetime.now()
            }

            self.daily_buy_count += 1

            self.trade_history.append({
                'type': 'BUY',
                'strategy': 'volatility_breakout',
                'code': code,
                'name': name,
                'quantity': quantity,
                'price': price,
                'target_price': signal['target_price'],
                'k_value': signal['k_value'],
                'order_no': order_no,
                'timestamp': datetime.now().isoformat()
            })

            return True, f"매수 성공: {name} {quantity}주 @{price:,}원 (목표가: {signal['target_price']:,}원)"
        else:
            msg = result.get('msg1', 'Unknown error') if result else '주문 실패'
            return False, f"매수 실패: {name} - {msg}"

    def execute_sell(self, stock: Dict) -> Tuple[bool, str]:
        """
        매도 실행

        Args:
            stock: 매도 대상 정보

        Returns:
            (성공여부, 메시지)
        """
        code = stock['code']
        name = stock['name']
        quantity = stock['quantity']
        reason = stock['reason']

        result = self.api.sell_stock(code, quantity, order_type="03")  # 시장가

        if result and result.get('rt_cd') == '0':
            order_no = result.get('output', {}).get('ODNO', 'N/A')

            # 포지션 기록 삭제
            if code in self.today_positions:
                del self.today_positions[code]

            self.trade_history.append({
                'type': 'SELL',
                'strategy': 'volatility_breakout',
                'code': code,
                'name': name,
                'quantity': quantity,
                'profit_rate': stock.get('profit_rate', 0),
                'reason': reason,
                'order_no': order_no,
                'timestamp': datetime.now().isoformat()
            })

            return True, f"매도 성공: {name} {quantity}주 - {reason}"
        else:
            msg = result.get('msg1', 'Unknown error') if result else '주문 실패'
            return False, f"매도 실패: {name} - {msg}"

    def run_once(self) -> Dict:
        """
        전략 1회 실행

        Returns:
            실행 결과
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'strategy': 'volatility_breakout',
            'sells': [],
            'buys': [],
            'errors': []
        }

        self.reset_daily_data()

        # 1. 보유 종목 매도 검사 (청산/손절)
        print("\n🔍 [변동성 돌파] 보유 종목 확인 중...")
        holdings = self.api.get_holding_stocks()

        if holdings:
            sell_targets = self.check_sell_signals(holdings)

            for target in sell_targets:
                success, msg = self.execute_sell(target)
                if success:
                    result['sells'].append(msg)
                    print(f"   ✅ {msg}")
                else:
                    result['errors'].append(msg)
                    print(f"   ❌ {msg}")
                time.sleep(0.5)

        # 2. 매수 시간 확인
        if not self.is_buy_time():
            now = datetime.now()
            print(f"\n⏰ 매수 시간 외 ({now.strftime('%H:%M')})")
            print(f"   매수 가능 시간: {self.config['buy_start_time'][0]:02d}:{self.config['buy_start_time'][1]:02d} ~ {self.config['buy_end_time'][0]:02d}:{self.config['buy_end_time'][1]:02d}")
            return result

        # 3. 매수 조건 확인
        current_holdings = len(self.api.get_holding_stocks())
        available_cash = self.api.get_available_cash()

        can_buy = (
            current_holdings < self.config['max_stocks'] and
            self.daily_buy_count < self.config['max_buy_per_day'] and
            available_cash > self.config['min_price'] * 10
        )

        if can_buy:
            print("\n🔍 [변동성 돌파] 매수 신호 탐색 중...")
            targets = self.get_target_stocks()

            # 이미 보유 중인 종목 제외
            holding_codes = [h['stock_code'] for h in holdings]
            targets = [t for t in targets if t['code'] not in holding_codes]

            for stock in targets:
                if self.daily_buy_count >= self.config['max_buy_per_day']:
                    break
                if current_holdings >= self.config['max_stocks']:
                    break

                signal = self.check_buy_signal(stock)

                if signal:
                    print(f"\n   📈 돌파 감지: {signal['name']}")
                    print(f"      현재가: {signal['current_price']:,}원 > 목표가: {signal['target_price']:,}원")
                    print(f"      돌파율: +{signal['breakout_rate']:.2f}%")

                    quantity = self.calculate_buy_quantity(signal['current_price'], available_cash)

                    if quantity > 0:
                        success, msg = self.execute_buy(signal, quantity)

                        if success:
                            result['buys'].append(msg)
                            print(f"   ✅ {msg}")
                            current_holdings += 1
                            available_cash = self.api.get_available_cash()
                        else:
                            result['errors'].append(msg)
                            print(f"   ❌ {msg}")

                        time.sleep(0.5)

                time.sleep(0.3)
        else:
            reasons = []
            if current_holdings >= self.config['max_stocks']:
                reasons.append(f"보유종목 한도({self.config['max_stocks']}개)")
            if self.daily_buy_count >= self.config['max_buy_per_day']:
                reasons.append(f"일일 매수 한도({self.config['max_buy_per_day']}회)")
            if available_cash <= self.config['min_price'] * 10:
                reasons.append("가용 현금 부족")

            print(f"\n⏸️  매수 중단: {', '.join(reasons)}")

        return result

    def get_status(self) -> Dict:
        """현재 상태 조회"""
        holdings = self.api.get_holding_stocks()
        available_cash = self.api.get_available_cash()

        return {
            'strategy': 'volatility_breakout',
            'k_value': self.config['k_value'],
            'holdings_count': len(holdings),
            'holdings': holdings,
            'available_cash': available_cash,
            'daily_buy_count': self.daily_buy_count,
            'today_positions': self.today_positions,
            'config': self.config,
            'trade_history': self.trade_history[-10:]
        }
