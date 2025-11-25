"""
모멘텀 + 거래량 전략 (Strategy 1)

[종목선택]
- 거래량 상위 종목 필터
- 등락률 +2% ~ +8% 범위
- 거래량 200% 이상 급등

[매수조건]
- 5일 이동평균선 위에서 거래
- RSI 50 이상
- 거래량 급등

[매도조건]
- 익절: +5% 도달
- 손절: -3% 도달
- 보유 기간 3일 초과 시 청산
"""

import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from indicators.technical import TechnicalIndicators


class MomentumVolumeStrategy:
    """모멘텀 + 거래량 기반 자동매매 전략"""

    def __init__(self, api, config: Dict = None):
        """
        초기화

        Args:
            api: KisAPI 인스턴스
            config: 전략 설정
        """
        self.api = api
        self.indicators = TechnicalIndicators()

        # 기본 설정
        default_config = {
            # 종목 선택 조건
            'min_price': 1000,           # 최소 주가 (1,000원)
            'max_price': 500000,         # 최대 주가 (50만원)
            'min_volume_ratio': 2.0,     # 최소 거래량 비율 (평균 대비 200%)
            'min_change_rate': 2.0,      # 최소 등락률 (+2%)
            'max_change_rate': 8.0,      # 최대 등락률 (+8%)

            # 매수 조건
            'buy_rsi_min': 50,           # 최소 RSI
            'buy_rsi_max': 70,           # 최대 RSI (과매수 제외)

            # 매도 조건 (손익)
            'take_profit': 5.0,          # 익절 기준 (+5%)
            'stop_loss': -3.0,           # 손절 기준 (-3%)
            'max_hold_days': 3,          # 최대 보유 기간 (일)

            # 자금 관리
            'max_stocks': 5,             # 최대 보유 종목 수
            'position_ratio': 0.2,       # 종목당 투자 비율 (20%)
            'max_buy_per_day': 3,        # 일일 최대 매수 횟수
        }

        self.config = {**default_config, **(config or {})}

        # 거래 기록
        self.trade_history = []
        self.daily_buy_count = 0
        self.last_trade_date = None

        # 보유 종목 매수 정보 (매수일 기록용)
        self.buy_dates = {}

    def reset_daily_count(self):
        """일일 카운터 리셋"""
        today = datetime.now().date()
        if self.last_trade_date != today:
            self.daily_buy_count = 0
            self.last_trade_date = today

    def get_candidate_stocks(self) -> List[Dict]:
        """
        매수 후보 종목 조회

        Returns:
            후보 종목 리스트
        """
        candidates = []

        # 1. 거래량 상위 종목 조회 (코스피 + 코스닥)
        print("📊 거래량 상위 종목 스캔 중...")

        for market in ['J', 'Q']:  # J: 코스피, Q: 코스닥
            volume_data = self.api.get_volume_rank(market)

            if not volume_data or volume_data.get('rt_cd') != '0':
                continue

            stocks = volume_data.get('output', [])

            for stock in stocks[:30]:  # 상위 30종목만 확인
                try:
                    code = stock.get('mksc_shrn_iscd', '')  # 종목코드
                    name = stock.get('hts_kor_isnm', '')    # 종목명
                    price = int(stock.get('stck_prpr', 0))  # 현재가
                    change_rate = float(stock.get('prdy_ctrt', 0))  # 등락률
                    volume = int(stock.get('acml_vol', 0))  # 거래량

                    # 기본 필터링
                    if not code or price == 0:
                        continue

                    # 가격 필터
                    if not (self.config['min_price'] <= price <= self.config['max_price']):
                        continue

                    # 등락률 필터 (상승 종목만)
                    if not (self.config['min_change_rate'] <= change_rate <= self.config['max_change_rate']):
                        continue

                    candidates.append({
                        'code': code,
                        'name': name,
                        'price': price,
                        'change_rate': change_rate,
                        'volume': volume,
                        'market': 'KOSPI' if market == 'J' else 'KOSDAQ'
                    })

                except (ValueError, TypeError):
                    continue

        print(f"   → {len(candidates)}개 후보 종목 발견")
        return candidates

    def analyze_stock(self, stock_code: str) -> Dict:
        """
        종목 상세 분석

        Args:
            stock_code: 종목코드

        Returns:
            분석 결과
        """
        result = {
            'code': stock_code,
            'is_buy_signal': False,
            'reason': '',
            'indicators': {}
        }

        # 일별 시세 조회
        daily_data = self.api.get_daily_price(stock_code)

        if not daily_data or daily_data.get('rt_cd') != '0':
            result['reason'] = '일별 시세 조회 실패'
            return result

        output = daily_data.get('output', [])

        if len(output) < 21:
            result['reason'] = '데이터 부족'
            return result

        # 가격/거래량 데이터 추출 (최신 데이터가 마지막으로)
        prices = []
        volumes = []

        for item in reversed(output[:21]):
            try:
                prices.append(float(item.get('stck_clpr', 0)))
                volumes.append(int(item.get('acml_vol', 0)))
            except (ValueError, TypeError):
                continue

        if len(prices) < 21:
            result['reason'] = '데이터 변환 실패'
            return result

        # 기술적 지표 계산
        analysis = self.indicators.analyze_stock(prices, volumes)
        result['indicators'] = analysis

        current_price = prices[-1]

        # 매수 조건 검사
        buy_signals = []

        # 1. 5일 이동평균선 위에서 거래
        if analysis['price_above_ma5']:
            buy_signals.append('MA5 상회')
        else:
            result['reason'] = '5일선 아래'
            return result

        # 2. RSI 조건 (50-70 구간)
        rsi = analysis.get('rsi')
        if rsi:
            if self.config['buy_rsi_min'] <= rsi <= self.config['buy_rsi_max']:
                buy_signals.append(f'RSI {rsi}')
            else:
                result['reason'] = f'RSI 조건 미충족 ({rsi})'
                return result

        # 3. 거래량 급등 확인
        volume_ratio = analysis.get('volume_ratio')
        if volume_ratio and volume_ratio >= self.config['min_volume_ratio']:
            buy_signals.append(f'거래량 {volume_ratio}배')
        else:
            result['reason'] = f'거래량 부족 ({volume_ratio}배)'
            return result

        # 모든 조건 충족
        result['is_buy_signal'] = True
        result['reason'] = ', '.join(buy_signals)
        result['current_price'] = current_price

        return result

    def check_sell_signals(self, holdings: List[Dict]) -> List[Dict]:
        """
        보유 종목 매도 신호 확인

        Args:
            holdings: 보유 종목 리스트

        Returns:
            매도 대상 리스트
        """
        sell_targets = []

        for stock in holdings:
            code = stock['stock_code']
            name = stock['stock_name']
            quantity = stock['quantity']
            buy_price = stock['buy_price']
            current_price = stock['current_price']
            profit_rate = stock['profit_rate']

            sell_reason = None

            # 1. 익절 조건
            if profit_rate >= self.config['take_profit']:
                sell_reason = f"익절 (+{profit_rate:.2f}%)"

            # 2. 손절 조건
            elif profit_rate <= self.config['stop_loss']:
                sell_reason = f"손절 ({profit_rate:.2f}%)"

            # 3. 보유 기간 초과
            elif code in self.buy_dates:
                buy_date = self.buy_dates[code]
                hold_days = (datetime.now() - buy_date).days
                if hold_days >= self.config['max_hold_days']:
                    sell_reason = f"보유기간 초과 ({hold_days}일)"

            # 4. 기술적 매도 신호 (RSI 과매수 + 하락 전환)
            if not sell_reason:
                daily_data = self.api.get_daily_price(code)
                if daily_data and daily_data.get('rt_cd') == '0':
                    output = daily_data.get('output', [])
                    if len(output) >= 15:
                        prices = [float(item.get('stck_clpr', 0)) for item in reversed(output[:15])]
                        rsi = self.indicators.calculate_rsi(prices, 14)

                        if rsi and rsi > 70 and prices[-1] < prices[-2]:
                            sell_reason = f"RSI 과매수 ({rsi:.1f}) + 하락"

            if sell_reason:
                sell_targets.append({
                    'code': code,
                    'name': name,
                    'quantity': quantity,
                    'buy_price': buy_price,
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
        # 종목당 투자 금액 계산
        invest_amount = int(available_cash * self.config['position_ratio'])

        # 매수 수량 계산
        quantity = invest_amount // price

        return max(0, quantity)

    def execute_buy(self, stock: Dict, quantity: int) -> Tuple[bool, str]:
        """
        매수 실행

        Args:
            stock: 종목 정보
            quantity: 매수 수량

        Returns:
            (성공여부, 메시지)
        """
        code = stock['code']
        name = stock.get('name', code)
        price = stock.get('current_price', stock.get('price', 0))

        result = self.api.buy_stock(code, quantity, order_type="03")  # 시장가

        if result and result.get('rt_cd') == '0':
            order_no = result.get('output', {}).get('ODNO', 'N/A')

            # 매수 기록
            self.buy_dates[code] = datetime.now()
            self.daily_buy_count += 1

            self.trade_history.append({
                'type': 'BUY',
                'code': code,
                'name': name,
                'quantity': quantity,
                'price': price,
                'order_no': order_no,
                'timestamp': datetime.now().isoformat()
            })

            return True, f"매수 성공: {name} {quantity}주 (주문번호: {order_no})"
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

            # 매수일 기록 삭제
            if code in self.buy_dates:
                del self.buy_dates[code]

            self.trade_history.append({
                'type': 'SELL',
                'code': code,
                'name': name,
                'quantity': quantity,
                'profit_rate': stock.get('profit_rate', 0),
                'reason': reason,
                'order_no': order_no,
                'timestamp': datetime.now().isoformat()
            })

            return True, f"매도 성공: {name} {quantity}주 - {reason} (주문번호: {order_no})"
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
            'sells': [],
            'buys': [],
            'errors': []
        }

        self.reset_daily_count()

        # 1. 보유 종목 매도 검사
        print("\n🔍 보유 종목 매도 신호 확인 중...")
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
                time.sleep(0.5)  # API 호출 간격

        # 2. 매수 조건 확인
        current_holdings = len(self.api.get_holding_stocks())
        available_cash = self.api.get_available_cash()

        can_buy = (
            current_holdings < self.config['max_stocks'] and
            self.daily_buy_count < self.config['max_buy_per_day'] and
            available_cash > self.config['min_price'] * 10
        )

        if can_buy:
            print("\n🔍 매수 후보 종목 분석 중...")
            candidates = self.get_candidate_stocks()

            # 이미 보유 중인 종목 제외
            holding_codes = [h['stock_code'] for h in holdings]
            candidates = [c for c in candidates if c['code'] not in holding_codes]

            for candidate in candidates[:10]:  # 상위 10개만 상세 분석
                if self.daily_buy_count >= self.config['max_buy_per_day']:
                    break
                if current_holdings >= self.config['max_stocks']:
                    break

                analysis = self.analyze_stock(candidate['code'])

                if analysis['is_buy_signal']:
                    price = analysis.get('current_price', candidate['price'])
                    quantity = self.calculate_buy_quantity(price, available_cash)

                    if quantity > 0:
                        candidate['current_price'] = price
                        success, msg = self.execute_buy(candidate, quantity)

                        if success:
                            result['buys'].append(msg)
                            print(f"   ✅ {msg}")
                            current_holdings += 1
                            available_cash = self.api.get_available_cash()
                        else:
                            result['errors'].append(msg)
                            print(f"   ❌ {msg}")

                        time.sleep(0.5)
                else:
                    print(f"   ⏭️  {candidate['name']}: {analysis['reason']}")

                time.sleep(0.3)  # API 호출 간격
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
        """
        현재 상태 조회

        Returns:
            상태 정보
        """
        holdings = self.api.get_holding_stocks()
        available_cash = self.api.get_available_cash()

        return {
            'holdings_count': len(holdings),
            'holdings': holdings,
            'available_cash': available_cash,
            'daily_buy_count': self.daily_buy_count,
            'config': self.config,
            'trade_history': self.trade_history[-10:]  # 최근 10건
        }
