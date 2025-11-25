"""
Ollama 기반 주식 패턴 분석기

온디바이스 AI(Ollama)를 활용한 가격 패턴 분석
- 인터넷 없이 로컬에서 실행
- 수집된 데이터를 기반으로 분석
- 변동성 돌파 전략의 보조 필터로 활용

[필요 환경]
- Ollama 설치: https://ollama.ai
- 모델 다운로드: ollama pull llama3.2 (또는 EEVE-Korean-10.8B)

[사용법]
analyzer = OllamaAnalyzer()
result = analyzer.analyze_stock(price_data, volume_data, indicators)
"""

import json
import subprocess
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class OllamaAnalyzer:
    """Ollama 기반 주식 분석기"""

    def __init__(self, model: str = "llama3.2", timeout: int = 30):
        """
        초기화

        Args:
            model: Ollama 모델명 (llama3.2, mistral, EEVE-Korean-10.8B 등)
            timeout: 응답 대기 시간 (초)
        """
        self.model = model
        self.timeout = timeout
        self.is_available = self._check_ollama()

    def _check_ollama(self) -> bool:
        """Ollama 설치 및 실행 확인"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print(f"✅ Ollama 사용 가능 (모델: {self.model})")
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        print("⚠️  Ollama를 찾을 수 없습니다. 규칙 기반 분석으로 대체됩니다.")
        print("   Ollama 설치: https://ollama.ai")
        return False

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Ollama API 호출

        Args:
            prompt: 프롬프트

        Returns:
            응답 텍스트
        """
        if not self.is_available:
            return None

        try:
            result = subprocess.run(
                ["ollama", "run", self.model, prompt],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except subprocess.TimeoutExpired:
            print(f"⚠️  Ollama 응답 시간 초과 ({self.timeout}초)")
        except Exception as e:
            print(f"⚠️  Ollama 호출 오류: {e}")

        return None

    def analyze_price_pattern(
        self,
        prices: List[float],
        volumes: List[int],
        indicators: Dict
    ) -> Dict:
        """
        가격 패턴 분석

        Args:
            prices: 최근 N일 종가 리스트 (오래된 순)
            volumes: 최근 N일 거래량 리스트
            indicators: 기술적 지표 {'ma5': x, 'ma20': x, 'rsi': x, ...}

        Returns:
            분석 결과 {
                'signal': 'BUY' | 'SELL' | 'HOLD',
                'confidence': 0-100,
                'reason': '분석 이유',
                'pattern': '감지된 패턴'
            }
        """
        # Ollama 사용 가능하면 AI 분석
        if self.is_available:
            return self._analyze_with_ollama(prices, volumes, indicators)

        # 아니면 규칙 기반 분석
        return self._analyze_with_rules(prices, volumes, indicators)

    def _analyze_with_ollama(
        self,
        prices: List[float],
        volumes: List[int],
        indicators: Dict
    ) -> Dict:
        """Ollama를 이용한 AI 분석"""

        # 최근 데이터 요약
        recent_prices = prices[-10:] if len(prices) >= 10 else prices
        recent_volumes = volumes[-10:] if len(volumes) >= 10 else volumes

        # 변화율 계산
        price_changes = []
        for i in range(1, len(recent_prices)):
            change = (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1] * 100
            price_changes.append(round(change, 2))

        # 프롬프트 구성
        prompt = f"""당신은 주식 기술적 분석 전문가입니다. 다음 데이터를 분석하고 매매 신호를 판단해주세요.

## 가격 데이터 (최근 10일)
- 종가: {recent_prices}
- 일별 변화율(%): {price_changes}

## 거래량 데이터
- 최근 거래량: {recent_volumes}
- 평균 대비: {indicators.get('volume_ratio', 'N/A')}배

## 기술적 지표
- 현재가: {prices[-1] if prices else 'N/A'}
- 5일 이동평균: {indicators.get('ma5', 'N/A')}
- 20일 이동평균: {indicators.get('ma20', 'N/A')}
- RSI(14): {indicators.get('rsi', 'N/A')}
- 현재가 > MA5: {indicators.get('price_above_ma5', 'N/A')}
- 현재가 > MA20: {indicators.get('price_above_ma20', 'N/A')}

## 분석 요청
위 데이터를 기반으로 다음 형식으로 답변해주세요:

SIGNAL: [BUY/SELL/HOLD 중 하나]
CONFIDENCE: [0-100 사이 숫자]
PATTERN: [감지된 패턴 이름, 예: 상승추세, 박스권, 하락추세, 쌍바닥 등]
REASON: [간단한 이유 1-2문장]

답변:"""

        response = self._call_ollama(prompt)

        if response:
            return self._parse_ollama_response(response)

        # 실패 시 규칙 기반으로 대체
        return self._analyze_with_rules(prices, volumes, indicators)

    def _parse_ollama_response(self, response: str) -> Dict:
        """Ollama 응답 파싱"""
        result = {
            'signal': 'HOLD',
            'confidence': 50,
            'pattern': '분석 중',
            'reason': '',
            'source': 'ollama'
        }

        lines = response.strip().split('\n')

        for line in lines:
            line = line.strip()

            if line.startswith('SIGNAL:'):
                signal = line.replace('SIGNAL:', '').strip().upper()
                if signal in ['BUY', 'SELL', 'HOLD']:
                    result['signal'] = signal

            elif line.startswith('CONFIDENCE:'):
                try:
                    conf = int(line.replace('CONFIDENCE:', '').strip().split()[0])
                    result['confidence'] = max(0, min(100, conf))
                except ValueError:
                    pass

            elif line.startswith('PATTERN:'):
                result['pattern'] = line.replace('PATTERN:', '').strip()

            elif line.startswith('REASON:'):
                result['reason'] = line.replace('REASON:', '').strip()

        return result

    def _analyze_with_rules(
        self,
        prices: List[float],
        volumes: List[int],
        indicators: Dict
    ) -> Dict:
        """규칙 기반 분석 (Ollama 대체)"""

        result = {
            'signal': 'HOLD',
            'confidence': 50,
            'pattern': '',
            'reason': '',
            'source': 'rules'
        }

        if len(prices) < 5:
            result['reason'] = '데이터 부족'
            return result

        # 점수 계산
        score = 0
        reasons = []

        # 1. 추세 분석 (최근 5일)
        recent_trend = (prices[-1] - prices[-5]) / prices[-5] * 100

        if recent_trend > 3:
            score += 2
            reasons.append(f"상승추세 (+{recent_trend:.1f}%)")
        elif recent_trend < -3:
            score -= 2
            reasons.append(f"하락추세 ({recent_trend:.1f}%)")

        # 2. 이동평균 분석
        if indicators.get('price_above_ma5'):
            score += 1
            reasons.append("MA5 상회")
        else:
            score -= 1

        if indicators.get('price_above_ma20'):
            score += 1
            reasons.append("MA20 상회")

        # 3. RSI 분석
        rsi = indicators.get('rsi')
        if rsi:
            if 50 <= rsi <= 70:
                score += 1
                reasons.append(f"RSI 적정({rsi:.0f})")
            elif rsi > 70:
                score -= 1
                reasons.append(f"RSI 과매수({rsi:.0f})")
            elif rsi < 30:
                score += 1
                reasons.append(f"RSI 과매도({rsi:.0f})")

        # 4. 거래량 분석
        volume_ratio = indicators.get('volume_ratio', 1)
        if volume_ratio >= 2:
            score += 1
            reasons.append(f"거래량 급등({volume_ratio:.1f}배)")

        # 5. 패턴 감지
        pattern = self._detect_pattern(prices)
        if pattern:
            result['pattern'] = pattern
            if pattern in ['상승추세', '쌍바닥', '골든크로스']:
                score += 1
            elif pattern in ['하락추세', '쌍봉', '데드크로스']:
                score -= 1

        # 신호 결정
        if score >= 3:
            result['signal'] = 'BUY'
            result['confidence'] = min(50 + score * 10, 90)
        elif score <= -2:
            result['signal'] = 'SELL'
            result['confidence'] = min(50 + abs(score) * 10, 90)
        else:
            result['signal'] = 'HOLD'
            result['confidence'] = 50

        result['reason'] = ', '.join(reasons) if reasons else '특별한 신호 없음'

        return result

    def _detect_pattern(self, prices: List[float]) -> str:
        """간단한 패턴 감지"""
        if len(prices) < 10:
            return ''

        # 최근 10일 데이터
        recent = prices[-10:]

        # 상승/하락 추세
        up_days = sum(1 for i in range(1, len(recent)) if recent[i] > recent[i-1])

        if up_days >= 7:
            return '강한 상승추세'
        elif up_days >= 5:
            return '상승추세'
        elif up_days <= 3:
            return '하락추세'

        # 박스권 (변동폭 5% 이내)
        high = max(recent)
        low = min(recent)
        range_pct = (high - low) / low * 100

        if range_pct < 5:
            return '박스권'

        return '변동성 구간'

    def get_trading_recommendation(
        self,
        stock_code: str,
        stock_name: str,
        current_price: float,
        analysis_result: Dict,
        strategy_signal: bool
    ) -> Dict:
        """
        최종 매매 추천

        Args:
            stock_code: 종목코드
            stock_name: 종목명
            current_price: 현재가
            analysis_result: 패턴 분석 결과
            strategy_signal: 기본 전략 신호 (True=매수, False=대기)

        Returns:
            최종 추천 결과
        """
        ai_signal = analysis_result.get('signal', 'HOLD')
        ai_confidence = analysis_result.get('confidence', 50)

        # 최종 점수 계산
        final_score = 0

        # 기본 전략 신호 (가중치 60%)
        if strategy_signal:
            final_score += 60

        # AI 분석 (가중치 40%)
        if ai_signal == 'BUY':
            final_score += int(40 * ai_confidence / 100)
        elif ai_signal == 'SELL':
            final_score -= int(40 * ai_confidence / 100)

        # 최종 추천
        if final_score >= 70:
            recommendation = 'STRONG_BUY'
            action = '적극 매수 추천'
        elif final_score >= 50:
            recommendation = 'BUY'
            action = '매수 고려'
        elif final_score >= 30:
            recommendation = 'HOLD'
            action = '관망'
        else:
            recommendation = 'AVOID'
            action = '매수 보류'

        return {
            'code': stock_code,
            'name': stock_name,
            'price': current_price,
            'recommendation': recommendation,
            'action': action,
            'score': final_score,
            'strategy_signal': strategy_signal,
            'ai_signal': ai_signal,
            'ai_confidence': ai_confidence,
            'pattern': analysis_result.get('pattern', ''),
            'reason': analysis_result.get('reason', ''),
            'timestamp': datetime.now().isoformat()
        }


class OllamaCrewAnalyzer:
    """
    CrewAI 스타일 멀티 에이전트 분석기

    여러 분석 관점을 가진 에이전트가 협력하여 분석
    (Ollama 없이도 규칙 기반으로 동작)
    """

    def __init__(self, model: str = "llama3.2"):
        self.model = model
        self.base_analyzer = OllamaAnalyzer(model)

    def analyze_with_crew(
        self,
        prices: List[float],
        volumes: List[int],
        indicators: Dict
    ) -> Dict:
        """
        멀티 에이전트 분석

        3명의 가상 분석가가 각각의 관점에서 분석:
        1. 추세 분석가: 가격 추세 분석
        2. 모멘텀 분석가: RSI, 거래량 분석
        3. 리스크 분석가: 변동성, 리스크 평가
        """

        # Agent 1: 추세 분석
        trend_analysis = self._analyze_trend(prices)

        # Agent 2: 모멘텀 분석
        momentum_analysis = self._analyze_momentum(prices, volumes, indicators)

        # Agent 3: 리스크 분석
        risk_analysis = self._analyze_risk(prices, indicators)

        # 최종 종합 (투표 방식)
        votes = {
            'BUY': 0,
            'SELL': 0,
            'HOLD': 0
        }

        for analysis in [trend_analysis, momentum_analysis, risk_analysis]:
            signal = analysis.get('signal', 'HOLD')
            confidence = analysis.get('confidence', 50) / 100
            votes[signal] += confidence

        # 가장 많은 표를 받은 신호
        final_signal = max(votes, key=votes.get)
        total_votes = sum(votes.values())
        final_confidence = int(votes[final_signal] / total_votes * 100) if total_votes > 0 else 50

        return {
            'signal': final_signal,
            'confidence': final_confidence,
            'trend': trend_analysis,
            'momentum': momentum_analysis,
            'risk': risk_analysis,
            'votes': votes,
            'source': 'crew'
        }

    def _analyze_trend(self, prices: List[float]) -> Dict:
        """추세 분석"""
        if len(prices) < 10:
            return {'signal': 'HOLD', 'confidence': 50, 'note': '데이터 부족'}

        # 단기 추세 (5일)
        short_trend = (prices[-1] - prices[-5]) / prices[-5] * 100

        # 중기 추세 (10일)
        mid_trend = (prices[-1] - prices[-10]) / prices[-10] * 100

        if short_trend > 2 and mid_trend > 3:
            return {'signal': 'BUY', 'confidence': 70, 'note': f'상승추세 (단기 +{short_trend:.1f}%, 중기 +{mid_trend:.1f}%)'}
        elif short_trend < -2 and mid_trend < -3:
            return {'signal': 'SELL', 'confidence': 70, 'note': f'하락추세 (단기 {short_trend:.1f}%, 중기 {mid_trend:.1f}%)'}
        else:
            return {'signal': 'HOLD', 'confidence': 50, 'note': '횡보 구간'}

    def _analyze_momentum(self, prices: List[float], volumes: List[int], indicators: Dict) -> Dict:
        """모멘텀 분석"""
        rsi = indicators.get('rsi', 50)
        volume_ratio = indicators.get('volume_ratio', 1)

        score = 50  # 기본 점수

        if 50 <= rsi <= 70:
            score += 15
        elif rsi > 70:
            score -= 20
        elif rsi < 30:
            score += 10

        if volume_ratio >= 2:
            score += 15
        elif volume_ratio >= 1.5:
            score += 10

        if score >= 65:
            return {'signal': 'BUY', 'confidence': score, 'note': f'모멘텀 양호 (RSI: {rsi:.0f}, 거래량: {volume_ratio:.1f}배)'}
        elif score <= 35:
            return {'signal': 'SELL', 'confidence': 100 - score, 'note': f'모멘텀 약화'}
        else:
            return {'signal': 'HOLD', 'confidence': 50, 'note': '모멘텀 중립'}

    def _analyze_risk(self, prices: List[float], indicators: Dict) -> Dict:
        """리스크 분석"""
        if len(prices) < 10:
            return {'signal': 'HOLD', 'confidence': 50, 'note': '데이터 부족'}

        # 변동성 계산 (표준편차 기반)
        recent = prices[-10:]
        avg = sum(recent) / len(recent)
        variance = sum((p - avg) ** 2 for p in recent) / len(recent)
        volatility = (variance ** 0.5) / avg * 100  # 변동성 %

        # 최대 낙폭
        max_price = max(recent)
        current = prices[-1]
        drawdown = (max_price - current) / max_price * 100

        if volatility < 3 and drawdown < 5:
            return {'signal': 'BUY', 'confidence': 60, 'note': f'리스크 낮음 (변동성: {volatility:.1f}%)'}
        elif volatility > 10 or drawdown > 10:
            return {'signal': 'SELL', 'confidence': 60, 'note': f'리스크 높음 (변동성: {volatility:.1f}%, 낙폭: {drawdown:.1f}%)'}
        else:
            return {'signal': 'HOLD', 'confidence': 50, 'note': f'리스크 보통'}
