"""
CrewAI 기반 멀티 에이전트 주식 분석 시스템

블로그 참조: https://twentytwentyone.tistory.com/361

[에이전트 구성]
1. Data Analyst Agent: 주식 데이터 분석, 기술적 지표 해석
2. News Sentiment Agent: 뉴스 감성 분석
3. Trading Decision Agent: 최종 매매 결정

[워크플로우]
데이터 수집 → 기술적 분석 → 감성 분석 → 매매 결정

[필요 패키지]
pip install crewai crewai-tools langchain-ollama
"""

import subprocess
import json
from typing import Dict, List, Optional
from datetime import datetime

# CrewAI 사용 가능 여부 체크
CREWAI_AVAILABLE = False
try:
    from crewai import Agent, Task, Crew, Process
    from langchain_ollama import ChatOllama
    CREWAI_AVAILABLE = True
except ImportError:
    pass


class CrewAIStockAnalyzer:
    """
    CrewAI 기반 멀티 에이전트 주식 분석기

    3개의 에이전트가 협력하여 주식 분석:
    - Data Analyst: 기술적 분석
    - Sentiment Analyst: 뉴스/시장 감성 분석
    - Trading Strategist: 최종 매매 결정
    """

    def __init__(self, model: str = "llama3.2"):
        """
        초기화

        Args:
            model: Ollama 모델명
        """
        self.model = model
        self.is_available = self._check_availability()

        if self.is_available:
            self._init_agents()
        else:
            print("⚠️  CrewAI를 사용할 수 없습니다. 규칙 기반 분석으로 대체됩니다.")
            print("   설치: pip install crewai crewai-tools langchain-ollama")

    def _check_availability(self) -> bool:
        """CrewAI 및 Ollama 사용 가능 여부 확인"""
        if not CREWAI_AVAILABLE:
            return False

        # Ollama 실행 확인
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ CrewAI + Ollama 사용 가능 (모델: {self.model})")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        return False

    def _init_agents(self):
        """CrewAI 에이전트 초기화"""
        # LLM 설정
        self.llm = ChatOllama(model=self.model, temperature=0.3)

        # 1. Data Analyst Agent (기술적 분석가)
        self.data_analyst = Agent(
            role='주식 데이터 분석가',
            goal='주식의 기술적 지표를 분석하여 추세와 매매 타이밍을 판단',
            backstory='''당신은 10년 경력의 기술적 분석 전문가입니다.
            이동평균선, RSI, MACD, 거래량 등의 지표를 정확하게 해석하며,
            차트 패턴을 통해 매수/매도 시점을 판단합니다.''',
            llm=self.llm,
            verbose=False,
            allow_delegation=False
        )

        # 2. Sentiment Analyst Agent (감성 분석가)
        self.sentiment_analyst = Agent(
            role='시장 감성 분석가',
            goal='시장 상황과 투자 심리를 분석하여 리스크를 평가',
            backstory='''당신은 시장 심리 분석 전문가입니다.
            거래량 변화, 시장 변동성, 투자자 동향을 분석하여
            현재 시장의 공포/탐욕 수준을 판단합니다.''',
            llm=self.llm,
            verbose=False,
            allow_delegation=False
        )

        # 3. Trading Strategist Agent (매매 전략가)
        self.trading_strategist = Agent(
            role='매매 전략가',
            goal='기술적 분석과 감성 분석을 종합하여 최종 매매 결정',
            backstory='''당신은 퀀트 트레이딩 전문가입니다.
            여러 분석 결과를 종합하여 리스크 대비 수익률을 계산하고,
            명확한 매수/매도/관망 결정을 내립니다.''',
            llm=self.llm,
            verbose=False,
            allow_delegation=False
        )

        print("   에이전트 초기화 완료: Data Analyst, Sentiment Analyst, Trading Strategist")

    def analyze_stock(
        self,
        stock_code: str,
        stock_name: str,
        current_price: float,
        prices: List[float],
        volumes: List[int],
        indicators: Dict
    ) -> Dict:
        """
        멀티 에이전트 주식 분석 실행

        Args:
            stock_code: 종목코드
            stock_name: 종목명
            current_price: 현재가
            prices: 최근 N일 종가 리스트
            volumes: 최근 N일 거래량 리스트
            indicators: 기술적 지표 딕셔너리

        Returns:
            분석 결과 딕셔너리
        """
        if not self.is_available:
            return self._analyze_with_rules(
                stock_code, stock_name, current_price,
                prices, volumes, indicators
            )

        return self._analyze_with_crewai(
            stock_code, stock_name, current_price,
            prices, volumes, indicators
        )

    def _analyze_with_crewai(
        self,
        stock_code: str,
        stock_name: str,
        current_price: float,
        prices: List[float],
        volumes: List[int],
        indicators: Dict
    ) -> Dict:
        """CrewAI 멀티 에이전트 분석"""

        # 데이터 요약 생성
        price_changes = []
        for i in range(1, min(len(prices), 6)):
            change = (prices[-i] - prices[-i-1]) / prices[-i-1] * 100
            price_changes.append(round(change, 2))

        data_summary = f"""
## 종목 정보
- 종목: {stock_name} ({stock_code})
- 현재가: {current_price:,.0f}원

## 가격 데이터 (최근 5일 변화율)
{price_changes}

## 기술적 지표
- 5일 이동평균: {indicators.get('ma5', 'N/A')}
- 20일 이동평균: {indicators.get('ma20', 'N/A')}
- RSI(14): {indicators.get('rsi', 'N/A')}
- 거래량 비율 (평균 대비): {indicators.get('volume_ratio', 'N/A')}배
- 현재가 > MA5: {indicators.get('price_above_ma5', 'N/A')}
- 현재가 > MA20: {indicators.get('price_above_ma20', 'N/A')}
"""

        # Task 1: 기술적 분석
        technical_task = Task(
            description=f"""다음 주식 데이터를 기술적으로 분석하세요:
{data_summary}

분석 항목:
1. 추세 방향 (상승/하락/횡보)
2. 이동평균선 배열 상태
3. RSI 과매수/과매도 여부
4. 거래량 이상 여부
5. 매수/매도/관망 중 추천""",
            expected_output="기술적 분석 결과와 추천 (BUY/SELL/HOLD)",
            agent=self.data_analyst
        )

        # Task 2: 감성/리스크 분석
        sentiment_task = Task(
            description=f"""다음 주식의 시장 심리와 리스크를 분석하세요:
{data_summary}

분석 항목:
1. 거래량 변화로 본 투자자 관심도
2. 변동성 수준
3. 현재 리스크 레벨 (상/중/하)
4. 매수 시 주의사항""",
            expected_output="리스크 분석 결과",
            agent=self.sentiment_analyst
        )

        # Task 3: 최종 매매 결정
        decision_task = Task(
            description=f"""기술적 분석과 감성 분석 결과를 종합하여 최종 매매 결정을 내리세요.

반드시 다음 형식으로 답변하세요:
SIGNAL: [BUY 또는 SELL 또는 HOLD]
CONFIDENCE: [0-100 사이 숫자]
REASON: [결정 이유 1-2문장]""",
            expected_output="최종 매매 결정 (SIGNAL, CONFIDENCE, REASON)",
            agent=self.trading_strategist,
            context=[technical_task, sentiment_task]
        )

        # Crew 실행
        crew = Crew(
            agents=[self.data_analyst, self.sentiment_analyst, self.trading_strategist],
            tasks=[technical_task, sentiment_task, decision_task],
            process=Process.sequential,
            verbose=False
        )

        try:
            result = crew.kickoff()
            return self._parse_crew_result(result, stock_code, stock_name, current_price)
        except Exception as e:
            print(f"⚠️  CrewAI 실행 오류: {e}")
            return self._analyze_with_rules(
                stock_code, stock_name, current_price,
                prices, volumes, indicators
            )

    def _parse_crew_result(
        self,
        result,
        stock_code: str,
        stock_name: str,
        current_price: float
    ) -> Dict:
        """CrewAI 결과 파싱"""
        output = {
            'code': stock_code,
            'name': stock_name,
            'price': current_price,
            'signal': 'HOLD',
            'confidence': 50,
            'reason': '',
            'source': 'crewai',
            'timestamp': datetime.now().isoformat()
        }

        # 결과 텍스트 파싱
        result_text = str(result)

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

        return output

    def _analyze_with_rules(
        self,
        stock_code: str,
        stock_name: str,
        current_price: float,
        prices: List[float],
        volumes: List[int],
        indicators: Dict
    ) -> Dict:
        """규칙 기반 분석 (CrewAI 대체)"""

        output = {
            'code': stock_code,
            'name': stock_name,
            'price': current_price,
            'signal': 'HOLD',
            'confidence': 50,
            'reason': '',
            'source': 'rules',
            'timestamp': datetime.now().isoformat()
        }

        if len(prices) < 5:
            output['reason'] = '데이터 부족'
            return output

        # === Agent 1: 기술적 분석 (Data Analyst) ===
        tech_score = 0
        tech_reasons = []

        # 추세 분석
        trend = (prices[-1] - prices[-5]) / prices[-5] * 100
        if trend > 3:
            tech_score += 20
            tech_reasons.append(f"상승추세(+{trend:.1f}%)")
        elif trend < -3:
            tech_score -= 20
            tech_reasons.append(f"하락추세({trend:.1f}%)")

        # 이동평균 분석
        if indicators.get('price_above_ma5'):
            tech_score += 15
            tech_reasons.append("MA5↑")
        if indicators.get('price_above_ma20'):
            tech_score += 10
            tech_reasons.append("MA20↑")

        # RSI 분석
        rsi = indicators.get('rsi', 50)
        if 50 <= rsi <= 70:
            tech_score += 15
            tech_reasons.append(f"RSI적정({rsi:.0f})")
        elif rsi > 70:
            tech_score -= 15
            tech_reasons.append(f"RSI과매수({rsi:.0f})")
        elif rsi < 30:
            tech_score += 10
            tech_reasons.append(f"RSI과매도({rsi:.0f})")

        # === Agent 2: 감성/리스크 분석 (Sentiment Analyst) ===
        sentiment_score = 0

        # 거래량 분석
        volume_ratio = indicators.get('volume_ratio', 1)
        if volume_ratio >= 2.0:
            sentiment_score += 15
            tech_reasons.append(f"거래량급등({volume_ratio:.1f}x)")
        elif volume_ratio >= 1.5:
            sentiment_score += 10

        # 변동성 분석 (최근 5일)
        if len(prices) >= 5:
            recent = prices[-5:]
            volatility = (max(recent) - min(recent)) / min(recent) * 100
            if volatility > 10:
                sentiment_score -= 10  # 고변동성 = 리스크
            elif volatility < 3:
                sentiment_score += 5   # 저변동성 = 안정

        # === Agent 3: 최종 결정 (Trading Strategist) ===
        total_score = tech_score + sentiment_score

        if total_score >= 30:
            output['signal'] = 'BUY'
            output['confidence'] = min(50 + total_score, 90)
        elif total_score <= -20:
            output['signal'] = 'SELL'
            output['confidence'] = min(50 + abs(total_score), 90)
        else:
            output['signal'] = 'HOLD'
            output['confidence'] = 50

        output['reason'] = ', '.join(tech_reasons) if tech_reasons else '특별한 신호 없음'
        output['tech_score'] = tech_score
        output['sentiment_score'] = sentiment_score
        output['total_score'] = total_score

        return output


def check_crewai_installation() -> Dict:
    """CrewAI 설치 상태 확인"""
    status = {
        'crewai_installed': False,
        'langchain_ollama_installed': False,
        'ollama_running': False,
        'ready': False
    }

    # CrewAI 체크
    try:
        import crewai
        status['crewai_installed'] = True
    except ImportError:
        pass

    # LangChain Ollama 체크
    try:
        import langchain_ollama
        status['langchain_ollama_installed'] = True
    except ImportError:
        pass

    # Ollama 실행 체크
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            status['ollama_running'] = True
    except:
        pass

    status['ready'] = all([
        status['crewai_installed'],
        status['langchain_ollama_installed'],
        status['ollama_running']
    ])

    return status


def install_crewai_packages():
    """CrewAI 패키지 설치"""
    print("📦 CrewAI 패키지 설치 중...")

    packages = [
        'crewai',
        'crewai-tools',
        'langchain-ollama'
    ]

    for package in packages:
        try:
            subprocess.run(
                ['pip', 'install', package],
                check=True,
                capture_output=True
            )
            print(f"   ✅ {package} 설치 완료")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ {package} 설치 실패: {e}")
            return False

    print("\n💡 Ollama 설치도 필요합니다: https://ollama.ai")
    print("   설치 후: ollama pull llama3.2")

    return True
