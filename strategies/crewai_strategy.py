"""
전략 2: Ollama + CrewAI 멀티 에이전트 전략

참조: https://twentytwentyone.tistory.com/361

[시스템 구조]
데이터 수집 (인터넷) → AI 분석 (온디바이스) → 매매 실행 (인터넷)

[에이전트 구성]
1. Data Analyst Agent: 기술적 지표 분석
2. News Sentiment Agent: 뉴스 감성 분석
3. Trading Decision Agent: 최종 매매 결정

[종목 선정]
- 보유 종목: 필수 분석 (매도 신호)
- 거래량 상위 50개: 매수 후보 탐색
"""

import time
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from indicators.technical import TechnicalIndicators
from crawlers.naver_news_crawler import NaverNewsCrawler

# CrewAI 사용 가능 여부
CREWAI_AVAILABLE = False
try:
    from crewai import Agent, Task, Crew, Process
    from langchain_ollama import ChatOllama
    CREWAI_AVAILABLE = True
except ImportError:
    pass


class CrewAIStrategy:
    """Ollama + CrewAI 멀티 에이전트 전략"""

    def __init__(self, api, config: Dict = None):
        """
        초기화

        Args:
            api: KisAPI 인스턴스
            config: 전략 설정
        """
        self.api = api
        self.indicators = TechnicalIndicators()
        self.news_crawler = NaverNewsCrawler()

        # 기본 설정
        default_config = {
            # 종목 선정
            'scan_count': 50,            # 거래량 상위 스캔 수
            'min_price': 1000,           # 최소 주가
            'max_price': 500000,         # 최대 주가
            'min_volume_ratio': 2.0,     # 최소 거래량 비율
            'min_change_rate': 1.0,      # 최소 등락률
            'max_change_rate': 8.0,      # 최대 등락률

            # 매수 조건
            'buy_score_min': 60,         # 최소 종합점수
            'rsi_min': 40,               # RSI 하한
            'rsi_max': 70,               # RSI 상한

            # 매도 조건
            'take_profit': 5.0,          # 익절 %
            'stop_loss': -3.0,           # 손절 %
            'max_hold_days': 3,          # 최대 보유일
            'sell_rsi_max': 75,          # 매도 RSI 상한

            # 자금 관리
            'max_stocks': 5,             # 최대 보유 종목
            'position_ratio': 0.2,       # 종목당 투자 비율
            'max_buy_per_day': 3,        # 일일 매수 한도

            # Ollama 설정
            'ollama_model': 'llama3.2',  # 사용 모델
            'use_ollama': True,          # Ollama 사용 여부
        }

        self.config = {**default_config, **(config or {})}

        # 거래 기록
        self.trade_history = []
        self.daily_buy_count = 0
        self.last_trade_date = None
        self.buy_dates = {}

        # CrewAI 초기화
        self.crewai_available = False
        self.llm = None
        self.agents = {}

        if self.config['use_ollama']:
            self._init_crewai()

    def _init_crewai(self):
        """CrewAI 및 Ollama 초기화"""
        if not CREWAI_AVAILABLE:
            print("⚠️  CrewAI 패키지 미설치. 규칙 기반으로 동작합니다.")
            print("   설치: pip install crewai langchain-ollama")
            return

        # Ollama 실행 확인
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                print("⚠️  Ollama가 실행되지 않았습니다.")
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            print("⚠️  Ollama를 찾을 수 없습니다.")
            print("   설치: https://ollama.ai")
            return

        # LLM 설정
        try:
            self.llm = ChatOllama(
                model=self.config['ollama_model'],
                temperature=0.3
            )

            # Agent 1: Data Analyst
            self.agents['data_analyst'] = Agent(
                role='주식 기술적 분석가',
                goal='기술적 지표를 분석하여 추세와 매매 타이밍을 판단',
                backstory='''당신은 10년 경력의 기술적 분석 전문가입니다.
                이동평균선, RSI, MACD, 거래량을 정확하게 해석하며,
                차트 패턴을 통해 매수/매도 시점을 판단합니다.
                답변은 반드시 한국어로 합니다.''',
                llm=self.llm,
                verbose=False,
                allow_delegation=False
            )

            # Agent 2: News Sentiment Analyst
            self.agents['sentiment_analyst'] = Agent(
                role='뉴스 감성 분석가',
                goal='뉴스와 시장 심리를 분석하여 투자 판단에 반영',
                backstory='''당신은 금융 뉴스 분석 전문가입니다.
                뉴스 헤드라인에서 호재/악재를 판단하고,
                시장 심리가 주가에 미치는 영향을 분석합니다.
                답변은 반드시 한국어로 합니다.''',
                llm=self.llm,
                verbose=False,
                allow_delegation=False
            )

            # Agent 3: Trading Decision Maker
            self.agents['decision_maker'] = Agent(
                role='매매 결정자',
                goal='기술적 분석과 감성 분석을 종합하여 최종 매매 결정',
                backstory='''당신은 퀀트 트레이딩 전문가입니다.
                여러 분석을 종합하여 명확한 매수/매도/관망 결정을 내립니다.
                리스크 관리를 중시하며, 확실한 기회에만 매매합니다.
                답변은 반드시 정해진 형식으로 합니다.''',
                llm=self.llm,
                verbose=False,
                allow_delegation=False
            )

            self.crewai_available = True
            print(f"✅ CrewAI 초기화 완료 (모델: {self.config['ollama_model']})")
            print("   에이전트: Data Analyst, Sentiment Analyst, Decision Maker")

        except Exception as e:
            print(f"⚠️  CrewAI 초기화 실패: {e}")

    def reset_daily_count(self):
        """일일 카운터 리셋"""
        today = datetime.now().date()
        if self.last_trade_date != today:
            self.daily_buy_count = 0
            self.last_trade_date = today

    def get_candidate_stocks(self) -> List[Dict]:
        """
        매수 후보 종목 조회 (거래량 상위 50개)

        Returns:
            후보 종목 리스트
        """
        candidates = []
        scan_per_market = self.config['scan_count'] // 2  # 코스피/코스닥 각 25개

        print(f"📊 거래량 상위 {self.config['scan_count']}개 종목 스캔 중...")

        for market in ['J', 'Q']:  # J: 코스피, Q: 코스닥
            volume_data = self.api.get_volume_rank(market)

            if not volume_data or volume_data.get('rt_cd') != '0':
                continue

            stocks = volume_data.get('output', [])

            for stock in stocks[:scan_per_market]:
                try:
                    code = stock.get('mksc_shrn_iscd', '')
                    name = stock.get('hts_kor_isnm', '')
                    price = int(stock.get('stck_prpr', 0))
                    change_rate = float(stock.get('prdy_ctrt', 0))
                    volume = int(stock.get('acml_vol', 0))

                    # 기본 필터링
                    if not code or price == 0:
                        continue

                    # 가격 필터
                    if not (self.config['min_price'] <= price <= self.config['max_price']):
                        continue

                    # 등락률 필터
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

        print(f"   → 1차 필터 통과: {len(candidates)}개")
        return candidates

    def analyze_technical(self, stock_code: str) -> Dict:
        """
        기술적 분석

        Args:
            stock_code: 종목코드

        Returns:
            기술적 분석 결과
        """
        result = {
            'code': stock_code,
            'score': 0,
            'signal': 'HOLD',
            'indicators': {},
            'reasons': []
        }

        # 일별 시세 조회
        daily_data = self.api.get_daily_price(stock_code)
        if not daily_data or daily_data.get('rt_cd') != '0':
            result['error'] = '시세 조회 실패'
            return result

        output = daily_data.get('output', [])
        if len(output) < 21:
            result['error'] = '데이터 부족'
            return result

        # 데이터 추출
        prices = []
        volumes = []
        for item in reversed(output[:21]):
            try:
                prices.append(float(item.get('stck_clpr', 0)))
                volumes.append(int(item.get('acml_vol', 0)))
            except (ValueError, TypeError):
                continue

        if len(prices) < 21:
            result['error'] = '데이터 변환 실패'
            return result

        # 기술적 지표 계산
        analysis = self.indicators.analyze_stock(prices, volumes)
        result['indicators'] = analysis

        score = 50  # 기본 점수
        reasons = []

        # 1. 이동평균선 분석 (+/- 15점)
        if analysis.get('price_above_ma5'):
            score += 10
            reasons.append("MA5 상회")
        else:
            score -= 10

        if analysis.get('price_above_ma20'):
            score += 5
            reasons.append("MA20 상회")

        # 2. RSI 분석 (+/- 15점)
        rsi = analysis.get('rsi', 50)
        if self.config['rsi_min'] <= rsi <= self.config['rsi_max']:
            score += 15
            reasons.append(f"RSI 적정({rsi:.0f})")
        elif rsi > self.config['rsi_max']:
            score -= 15
            reasons.append(f"RSI 과매수({rsi:.0f})")
        elif rsi < self.config['rsi_min']:
            score += 5
            reasons.append(f"RSI 과매도({rsi:.0f})")

        # 3. 거래량 분석 (+/- 10점)
        volume_ratio = analysis.get('volume_ratio', 1)
        if volume_ratio >= self.config['min_volume_ratio']:
            score += 10
            reasons.append(f"거래량 급등({volume_ratio:.1f}배)")
        elif volume_ratio < 0.5:
            score -= 5
            reasons.append("거래량 부족")

        # 4. 추세 분석 (+/- 10점)
        if len(prices) >= 5:
            trend = (prices[-1] - prices[-5]) / prices[-5] * 100
            if trend > 3:
                score += 10
                reasons.append(f"상승추세(+{trend:.1f}%)")
            elif trend < -3:
                score -= 10
                reasons.append(f"하락추세({trend:.1f}%)")

        result['score'] = max(0, min(100, score))
        result['reasons'] = reasons
        result['prices'] = prices
        result['volumes'] = volumes

        if score >= 70:
            result['signal'] = 'BUY'
        elif score <= 30:
            result['signal'] = 'SELL'
        else:
            result['signal'] = 'HOLD'

        return result

    def analyze_sentiment(self, stock_code: str) -> Dict:
        """
        뉴스 감성 분석

        Args:
            stock_code: 종목코드

        Returns:
            감성 분석 결과
        """
        sentiment_data = self.news_crawler.get_stock_sentiment(stock_code, 10)

        result = {
            'code': stock_code,
            'score': sentiment_data['sentiment']['score'],
            'label': sentiment_data['sentiment']['label'],
            'positive_ratio': sentiment_data['sentiment']['positive_ratio'],
            'negative_ratio': sentiment_data['sentiment']['negative_ratio'],
            'news_count': sentiment_data['news_count'],
            'positive_news': sentiment_data.get('positive_news', []),
            'negative_news': sentiment_data.get('negative_news', [])
        }

        return result

    def analyze_with_crewai(self, stock_code: str, stock_name: str,
                           tech_result: Dict, sentiment_result: Dict) -> Dict:
        """
        CrewAI 멀티 에이전트 분석

        Args:
            stock_code: 종목코드
            stock_name: 종목명
            tech_result: 기술적 분석 결과
            sentiment_result: 감성 분석 결과

        Returns:
            최종 분석 결과
        """
        if not self.crewai_available:
            return self._decide_without_crewai(tech_result, sentiment_result)

        # 데이터 요약
        indicators = tech_result.get('indicators', {})
        data_summary = f"""
## 종목: {stock_name} ({stock_code})

## 기술적 분석 결과
- 기술 점수: {tech_result.get('score', 0)}점
- MA5 상회: {indicators.get('price_above_ma5', False)}
- MA20 상회: {indicators.get('price_above_ma20', False)}
- RSI: {indicators.get('rsi', 'N/A')}
- 거래량 비율: {indicators.get('volume_ratio', 'N/A')}배
- 분석: {', '.join(tech_result.get('reasons', []))}

## 뉴스 감성 분석 결과
- 감성 점수: {sentiment_result.get('score', 0)}점
- 감성 라벨: {sentiment_result.get('label', 'NEUTRAL')}
- 긍정 뉴스 비율: {sentiment_result.get('positive_ratio', 0)}%
- 부정 뉴스 비율: {sentiment_result.get('negative_ratio', 0)}%
- 긍정 뉴스: {sentiment_result.get('positive_news', [])}
- 부정 뉴스: {sentiment_result.get('negative_news', [])}
"""

        try:
            # Task: 최종 매매 결정
            decision_task = Task(
                description=f"""다음 분석 결과를 종합하여 매매 결정을 내리세요:
{data_summary}

기술 점수(60%)와 감성 점수(40%)를 종합하여 판단하세요.
반드시 다음 형식으로만 답변하세요:

SIGNAL: [BUY 또는 SELL 또는 HOLD]
CONFIDENCE: [0-100 숫자]
REASON: [결정 이유 1문장]""",
                expected_output="SIGNAL, CONFIDENCE, REASON 형식의 매매 결정",
                agent=self.agents['decision_maker']
            )

            crew = Crew(
                agents=[self.agents['decision_maker']],
                tasks=[decision_task],
                process=Process.sequential,
                verbose=False
            )

            crew_result = crew.kickoff()
            return self._parse_crewai_result(str(crew_result), tech_result, sentiment_result)

        except Exception as e:
            print(f"⚠️  CrewAI 분석 오류: {e}")
            return self._decide_without_crewai(tech_result, sentiment_result)

    def _parse_crewai_result(self, result_text: str, tech_result: Dict, sentiment_result: Dict) -> Dict:
        """CrewAI 결과 파싱"""
        output = {
            'signal': 'HOLD',
            'confidence': 50,
            'reason': '',
            'source': 'crewai'
        }

        for line in result_text.split('\n'):
            line = line.strip()
            if 'SIGNAL:' in line.upper():
                signal = line.split(':')[-1].strip().upper()
                if signal in ['BUY', 'SELL', 'HOLD']:
                    output['signal'] = signal
            elif 'CONFIDENCE:' in line.upper():
                try:
                    conf = int(''.join(filter(str.isdigit, line.split(':')[-1])))
                    output['confidence'] = max(0, min(100, conf))
                except ValueError:
                    pass
            elif 'REASON:' in line.upper():
                output['reason'] = line.split(':', 1)[-1].strip()

        output['tech_score'] = tech_result.get('score', 0)
        output['sentiment_score'] = sentiment_result.get('score', 0)

        return output

    def _decide_without_crewai(self, tech_result: Dict, sentiment_result: Dict) -> Dict:
        """CrewAI 없이 규칙 기반 결정"""
        tech_score = tech_result.get('score', 50)
        sentiment_score = sentiment_result.get('score', 0)

        # 종합 점수 (기술 60% + 감성 40%)
        # 감성 점수는 -100~100이므로 0~100으로 변환
        normalized_sentiment = (sentiment_score + 100) / 2
        total_score = tech_score * 0.6 + normalized_sentiment * 0.4

        if total_score >= self.config['buy_score_min']:
            signal = 'BUY'
        elif total_score <= 30:
            signal = 'SELL'
        else:
            signal = 'HOLD'

        return {
            'signal': signal,
            'confidence': int(total_score),
            'reason': f"기술({tech_score:.0f}) + 감성({sentiment_score:.0f}) = {total_score:.0f}",
            'tech_score': tech_score,
            'sentiment_score': sentiment_score,
            'total_score': total_score,
            'source': 'rules'
        }

    def check_sell_signals(self, holdings: List[Dict]) -> List[Dict]:
        """
        보유 종목 매도 신호 확인 (필수)

        Args:
            holdings: 보유 종목 리스트

        Returns:
            매도 대상 리스트
        """
        sell_targets = []

        for stock in holdings:
            code = stock['stock_code']
            name = stock['stock_name']
            profit_rate = stock['profit_rate']

            sell_reason = None

            # 1. 익절
            if profit_rate >= self.config['take_profit']:
                sell_reason = f"익절 (+{profit_rate:.2f}%)"

            # 2. 손절
            elif profit_rate <= self.config['stop_loss']:
                sell_reason = f"손절 ({profit_rate:.2f}%)"

            # 3. 보유 기간 초과
            elif code in self.buy_dates:
                hold_days = (datetime.now() - self.buy_dates[code]).days
                if hold_days >= self.config['max_hold_days']:
                    sell_reason = f"보유기간 초과 ({hold_days}일)"

            # 4. 기술적 매도 신호
            if not sell_reason:
                tech_result = self.analyze_technical(code)
                rsi = tech_result.get('indicators', {}).get('rsi', 50)

                if rsi > self.config['sell_rsi_max']:
                    sell_reason = f"RSI 과매수 ({rsi:.0f})"
                elif not tech_result.get('indicators', {}).get('price_above_ma5', True):
                    if profit_rate < 0:
                        sell_reason = f"MA5 이탈 + 손실 ({profit_rate:.2f}%)"

            # 5. 뉴스 악재
            if not sell_reason:
                sentiment = self.analyze_sentiment(code)
                if sentiment.get('negative_ratio', 0) > 60:
                    sell_reason = f"뉴스 악재 (부정 {sentiment['negative_ratio']:.0f}%)"

            if sell_reason:
                sell_targets.append({
                    'code': code,
                    'name': name,
                    'quantity': stock['quantity'],
                    'buy_price': stock['buy_price'],
                    'current_price': stock['current_price'],
                    'profit_rate': profit_rate,
                    'reason': sell_reason
                })

        return sell_targets

    def execute_buy(self, stock: Dict, quantity: int) -> Tuple[bool, str]:
        """매수 실행"""
        code = stock['code']
        name = stock.get('name', code)
        price = stock.get('price', 0)

        result = self.api.buy_stock(code, quantity, order_type="03")

        if result and result.get('rt_cd') == '0':
            order_no = result.get('output', {}).get('ODNO', 'N/A')
            self.buy_dates[code] = datetime.now()
            self.daily_buy_count += 1

            self.trade_history.append({
                'type': 'BUY',
                'strategy': 'crewai',
                'code': code,
                'name': name,
                'quantity': quantity,
                'price': price,
                'order_no': order_no,
                'timestamp': datetime.now().isoformat()
            })

            return True, f"매수 성공: {name} {quantity}주 @{price:,}원"
        else:
            msg = result.get('msg1', 'Unknown error') if result else '주문 실패'
            return False, f"매수 실패: {name} - {msg}"

    def execute_sell(self, stock: Dict) -> Tuple[bool, str]:
        """매도 실행"""
        code = stock['code']
        name = stock['name']
        quantity = stock['quantity']
        reason = stock['reason']

        result = self.api.sell_stock(code, quantity, order_type="03")

        if result and result.get('rt_cd') == '0':
            order_no = result.get('output', {}).get('ODNO', 'N/A')

            if code in self.buy_dates:
                del self.buy_dates[code]

            self.trade_history.append({
                'type': 'SELL',
                'strategy': 'crewai',
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

    def calculate_buy_quantity(self, price: int, available_cash: int) -> int:
        """매수 수량 계산"""
        invest_amount = int(available_cash * self.config['position_ratio'])
        quantity = invest_amount // price
        return max(0, quantity)

    def run_once(self) -> Dict:
        """
        전략 1회 실행

        Returns:
            실행 결과
        """
        result = {
            'timestamp': datetime.now().isoformat(),
            'strategy': 'crewai',
            'sells': [],
            'buys': [],
            'errors': []
        }

        self.reset_daily_count()

        # ========================================
        # 1단계: 보유 종목 매도 분석 (필수)
        # ========================================
        print("\n" + "=" * 50)
        print("📊 [CrewAI 전략] 보유 종목 분석 중...")
        print("=" * 50)

        holdings = self.api.get_holding_stocks()

        if holdings:
            print(f"   보유 종목: {len(holdings)}개")
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
        else:
            print("   보유 종목 없음")

        # ========================================
        # 2단계: 매수 가능 여부 확인
        # ========================================
        current_holdings = len(self.api.get_holding_stocks())
        available_cash = self.api.get_available_cash()

        can_buy = (
            current_holdings < self.config['max_stocks'] and
            self.daily_buy_count < self.config['max_buy_per_day'] and
            available_cash > self.config['min_price'] * 10
        )

        if not can_buy:
            reasons = []
            if current_holdings >= self.config['max_stocks']:
                reasons.append(f"보유한도({self.config['max_stocks']}개)")
            if self.daily_buy_count >= self.config['max_buy_per_day']:
                reasons.append(f"일일한도({self.config['max_buy_per_day']}회)")
            if available_cash <= self.config['min_price'] * 10:
                reasons.append("현금부족")
            print(f"\n⏸️  매수 중단: {', '.join(reasons)}")
            return result

        # ========================================
        # 3단계: 거래량 상위 50개 스캔
        # ========================================
        print("\n" + "-" * 50)
        print("🔍 매수 후보 종목 분석 중...")
        print("-" * 50)

        candidates = self.get_candidate_stocks()

        # 이미 보유 중인 종목 제외
        holding_codes = [h['stock_code'] for h in holdings]
        candidates = [c for c in candidates if c['code'] not in holding_codes]

        # ========================================
        # 4단계: CrewAI 분석 (상위 10개)
        # ========================================
        analyzed = 0
        for candidate in candidates[:10]:
            if self.daily_buy_count >= self.config['max_buy_per_day']:
                break
            if current_holdings >= self.config['max_stocks']:
                break

            code = candidate['code']
            name = candidate['name']

            print(f"\n   분석 중: {name} ({code})")

            # 기술적 분석
            tech_result = self.analyze_technical(code)
            if tech_result.get('error'):
                print(f"      ⏭️  {tech_result['error']}")
                continue

            # 감성 분석
            sentiment_result = self.analyze_sentiment(code)

            # CrewAI 최종 결정
            decision = self.analyze_with_crewai(code, name, tech_result, sentiment_result)

            print(f"      기술: {tech_result.get('score', 0)}점, 감성: {sentiment_result.get('score', 0)}점")
            print(f"      결정: {decision['signal']} ({decision['confidence']}%)")

            if decision['signal'] == 'BUY' and decision['confidence'] >= self.config['buy_score_min']:
                quantity = self.calculate_buy_quantity(candidate['price'], available_cash)

                if quantity > 0:
                    candidate['decision'] = decision
                    success, msg = self.execute_buy(candidate, quantity)

                    if success:
                        result['buys'].append(msg)
                        print(f"      ✅ {msg}")
                        current_holdings += 1
                        available_cash = self.api.get_available_cash()
                    else:
                        result['errors'].append(msg)
                        print(f"      ❌ {msg}")

                    time.sleep(0.5)

            analyzed += 1
            time.sleep(0.3)

        print(f"\n   분석 완료: {analyzed}개 종목")

        return result

    def get_status(self) -> Dict:
        """현재 상태 조회"""
        holdings = self.api.get_holding_stocks()
        available_cash = self.api.get_available_cash()

        return {
            'strategy': 'crewai',
            'crewai_available': self.crewai_available,
            'ollama_model': self.config['ollama_model'],
            'holdings_count': len(holdings),
            'holdings': holdings,
            'available_cash': available_cash,
            'daily_buy_count': self.daily_buy_count,
            'config': self.config,
            'trade_history': self.trade_history[-10:]
        }
