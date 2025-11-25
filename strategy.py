"""
기술적 분석 전략 모듈
- RSI (Relative Strength Index)
- 이동평균선 (Moving Average)
- 볼린저 밴드 (Bollinger Bands)
- MACD
"""

from typing import List, Dict, Tuple, Optional


class TechnicalAnalysis:
    """기술적 분석 클래스"""

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """
        RSI (상대강도지수) 계산

        Args:
            prices: 종가 리스트 (최신 데이터가 앞에 있어야 함)
            period: RSI 기간 (기본값 14)

        Returns:
            RSI 값 (0-100)
        """
        if len(prices) < period + 1:
            return None

        # 가격 변화 계산 (최신순 -> 과거순으로 되어 있으므로 reverse)
        prices = list(reversed(prices[:period + 1]))

        gains = []
        losses = []

        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    @staticmethod
    def calculate_ma(prices: List[float], period: int) -> Optional[float]:
        """
        단순 이동평균 계산

        Args:
            prices: 종가 리스트
            period: 이동평균 기간

        Returns:
            이동평균 값
        """
        if len(prices) < period:
            return None

        return round(sum(prices[:period]) / period, 2)

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> Optional[float]:
        """
        지수 이동평균 계산

        Args:
            prices: 종가 리스트 (최신 데이터가 앞에 있어야 함)
            period: EMA 기간

        Returns:
            EMA 값
        """
        if len(prices) < period:
            return None

        # 과거순으로 정렬
        prices = list(reversed(prices[:period * 2]))

        multiplier = 2 / (period + 1)
        ema = sum(prices[:period]) / period  # 첫 SMA

        for price in prices[period:]:
            ema = (price - ema) * multiplier + ema

        return round(ema, 2)

    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Optional[Dict]:
        """
        볼린저 밴드 계산

        Args:
            prices: 종가 리스트
            period: 기간 (기본값 20)
            std_dev: 표준편차 배수 (기본값 2)

        Returns:
            {'upper': 상단밴드, 'middle': 중심선, 'lower': 하단밴드}
        """
        if len(prices) < period:
            return None

        prices_subset = prices[:period]
        middle = sum(prices_subset) / period

        # 표준편차 계산
        variance = sum((p - middle) ** 2 for p in prices_subset) / period
        std = variance ** 0.5

        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)

        return {
            'upper': round(upper, 2),
            'middle': round(middle, 2),
            'lower': round(lower, 2)
        }

    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Dict]:
        """
        MACD 계산

        Args:
            prices: 종가 리스트
            fast: 빠른 EMA 기간 (기본값 12)
            slow: 느린 EMA 기간 (기본값 26)
            signal: 시그널 기간 (기본값 9)

        Returns:
            {'macd': MACD선, 'signal': 시그널선, 'histogram': 히스토그램}
        """
        if len(prices) < slow + signal:
            return None

        # EMA 계산을 위한 내부 함수
        def calc_ema(data: List[float], period: int) -> List[float]:
            ema_list = []
            multiplier = 2 / (period + 1)
            ema = sum(data[:period]) / period
            ema_list.append(ema)

            for price in data[period:]:
                ema = (price - ema) * multiplier + ema
                ema_list.append(ema)

            return ema_list

        # 과거순으로 정렬
        reversed_prices = list(reversed(prices))

        fast_ema = calc_ema(reversed_prices, fast)
        slow_ema = calc_ema(reversed_prices, slow)

        # MACD 라인 계산
        macd_line = []
        for i in range(len(slow_ema)):
            fast_idx = i + (slow - fast)
            if fast_idx < len(fast_ema):
                macd_line.append(fast_ema[fast_idx] - slow_ema[i])

        if len(macd_line) < signal:
            return None

        # 시그널 라인 계산
        signal_ema = calc_ema(macd_line, signal)

        current_macd = macd_line[-1]
        current_signal = signal_ema[-1]
        histogram = current_macd - current_signal

        return {
            'macd': round(current_macd, 2),
            'signal': round(current_signal, 2),
            'histogram': round(histogram, 2)
        }


class TradingStrategy:
    """매매 전략 클래스"""

    def __init__(self, style: str = "neutral"):
        """
        Args:
            style: 투자 성향 (conservative, neutral, aggressive)
        """
        self.style = style
        self.ta = TechnicalAnalysis()

        # 성향별 파라미터 설정
        self.params = self._get_style_params()

    def _get_style_params(self) -> Dict:
        """투자 성향별 파라미터"""
        params = {
            "conservative": {  # 보수적
                "rsi_buy": 25,
                "rsi_sell": 75,
                "stop_loss": -0.03,  # -3%
                "take_profit": 0.07,  # +7%
                "ma_short": 5,
                "ma_long": 20,
                "position_size": 0.08,  # 종목당 8%
                "max_positions": 5
            },
            "neutral": {  # 중립
                "rsi_buy": 30,
                "rsi_sell": 70,
                "stop_loss": -0.05,  # -5%
                "take_profit": 0.10,  # +10%
                "ma_short": 5,
                "ma_long": 20,
                "position_size": 0.10,  # 종목당 10%
                "max_positions": 5
            },
            "aggressive": {  # 공격적
                "rsi_buy": 35,
                "rsi_sell": 65,
                "stop_loss": -0.07,  # -7%
                "take_profit": 0.15,  # +15%
                "ma_short": 5,
                "ma_long": 20,
                "position_size": 0.15,  # 종목당 15%
                "max_positions": 7
            }
        }
        return params.get(self.style, params["neutral"])

    def analyze(self, prices: List[float], current_price: float) -> Dict:
        """
        종합 기술적 분석

        Args:
            prices: 일봉 종가 리스트 (최신 데이터가 앞)
            current_price: 현재가

        Returns:
            분석 결과 딕셔너리
        """
        result = {
            "current_price": current_price,
            "rsi": None,
            "ma_short": None,
            "ma_long": None,
            "bollinger": None,
            "macd": None,
            "signals": [],
            "recommendation": "HOLD",
            "score": 0
        }

        # RSI 계산
        rsi = self.ta.calculate_rsi(prices)
        result["rsi"] = rsi

        # 이동평균 계산
        ma_short = self.ta.calculate_ma(prices, self.params["ma_short"])
        ma_long = self.ta.calculate_ma(prices, self.params["ma_long"])
        result["ma_short"] = ma_short
        result["ma_long"] = ma_long

        # 볼린저 밴드
        bollinger = self.ta.calculate_bollinger_bands(prices)
        result["bollinger"] = bollinger

        # MACD
        macd = self.ta.calculate_macd(prices)
        result["macd"] = macd

        # 시그널 분석
        score = 0

        # RSI 시그널
        if rsi is not None:
            if rsi < self.params["rsi_buy"]:
                result["signals"].append(f"RSI 과매도({rsi})")
                score += 2
            elif rsi > self.params["rsi_sell"]:
                result["signals"].append(f"RSI 과매수({rsi})")
                score -= 2

        # 이동평균 시그널
        if ma_short and ma_long:
            if ma_short > ma_long:
                result["signals"].append("이평선 정배열(골든크로스)")
                score += 1
            else:
                result["signals"].append("이평선 역배열(데드크로스)")
                score -= 1

            # 현재가 위치
            if current_price > ma_short:
                result["signals"].append("현재가 > 단기이평")
                score += 0.5
            if current_price > ma_long:
                result["signals"].append("현재가 > 장기이평")
                score += 0.5

        # 볼린저 밴드 시그널
        if bollinger:
            if current_price <= bollinger["lower"]:
                result["signals"].append("볼린저 하단 터치")
                score += 2
            elif current_price >= bollinger["upper"]:
                result["signals"].append("볼린저 상단 터치")
                score -= 2

        # MACD 시그널
        if macd:
            if macd["histogram"] > 0:
                result["signals"].append("MACD 상승 추세")
                score += 1
            else:
                result["signals"].append("MACD 하락 추세")
                score -= 1

        result["score"] = score

        # 최종 추천
        if score >= 3:
            result["recommendation"] = "STRONG_BUY"
        elif score >= 1.5:
            result["recommendation"] = "BUY"
        elif score <= -3:
            result["recommendation"] = "STRONG_SELL"
        elif score <= -1.5:
            result["recommendation"] = "SELL"
        else:
            result["recommendation"] = "HOLD"

        return result

    def should_buy(self, analysis: Dict) -> bool:
        """매수 여부 판단"""
        return analysis["recommendation"] in ["BUY", "STRONG_BUY"]

    def should_sell(self, analysis: Dict) -> bool:
        """매도 여부 판단"""
        return analysis["recommendation"] in ["SELL", "STRONG_SELL"]

    def check_stop_loss(self, buy_price: float, current_price: float) -> bool:
        """손절 확인"""
        change = (current_price - buy_price) / buy_price
        return change <= self.params["stop_loss"]

    def check_take_profit(self, buy_price: float, current_price: float) -> bool:
        """익절 확인"""
        change = (current_price - buy_price) / buy_price
        return change >= self.params["take_profit"]

    def calculate_position_size(self, total_capital: float, current_price: float) -> int:
        """
        매수 수량 계산

        Args:
            total_capital: 총 투자금
            current_price: 현재가

        Returns:
            매수 수량
        """
        position_amount = total_capital * self.params["position_size"]
        quantity = int(position_amount / current_price)
        return max(1, quantity)


if __name__ == "__main__":
    # 테스트
    test_prices = [50000, 49500, 49000, 48500, 48000, 47500, 47000, 46500,
                   46000, 45500, 45000, 44500, 44000, 43500, 43000, 42500,
                   42000, 41500, 41000, 40500, 40000, 39500, 39000, 38500,
                   38000, 37500, 37000, 36500, 36000, 35500]

    strategy = TradingStrategy(style="neutral")
    analysis = strategy.analyze(test_prices, 50000)

    print("=== 기술적 분석 결과 ===")
    print(f"현재가: {analysis['current_price']:,}원")
    print(f"RSI: {analysis['rsi']}")
    print(f"단기이평({strategy.params['ma_short']}일): {analysis['ma_short']}")
    print(f"장기이평({strategy.params['ma_long']}일): {analysis['ma_long']}")
    print(f"볼린저밴드: {analysis['bollinger']}")
    print(f"MACD: {analysis['macd']}")
    print(f"\n시그널: {analysis['signals']}")
    print(f"점수: {analysis['score']}")
    print(f"추천: {analysis['recommendation']}")
