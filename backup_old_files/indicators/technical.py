"""
기술적 지표 계산 모듈
- 이동평균 (MA)
- RSI (Relative Strength Index)
- 거래량 분석
"""

from typing import List, Dict, Optional
from collections import deque


class TechnicalIndicators:
    """기술적 지표 계산 클래스"""

    @staticmethod
    def calculate_ma(prices: List[float], period: int) -> Optional[float]:
        """
        이동평균 계산

        Args:
            prices: 가격 리스트 (최신 데이터가 마지막)
            period: 이동평균 기간

        Returns:
            이동평균 값 또는 None
        """
        if len(prices) < period:
            return None

        return sum(prices[-period:]) / period

    @staticmethod
    def calculate_ma_list(prices: List[float], period: int) -> List[Optional[float]]:
        """
        이동평균 리스트 계산

        Args:
            prices: 가격 리스트
            period: 이동평균 기간

        Returns:
            이동평균 리스트
        """
        result = []
        for i in range(len(prices)):
            if i < period - 1:
                result.append(None)
            else:
                ma = sum(prices[i-period+1:i+1]) / period
                result.append(ma)
        return result

    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """
        RSI (Relative Strength Index) 계산

        Args:
            prices: 가격 리스트 (최소 period+1개 필요)
            period: RSI 계산 기간 (기본 14)

        Returns:
            RSI 값 (0-100) 또는 None
        """
        if len(prices) < period + 1:
            return None

        # 가격 변화 계산
        changes = []
        for i in range(1, len(prices)):
            changes.append(prices[i] - prices[i-1])

        # 최근 period 기간의 변화만 사용
        recent_changes = changes[-(period):]

        # 상승/하락 분리
        gains = [c if c > 0 else 0 for c in recent_changes]
        losses = [-c if c < 0 else 0 for c in recent_changes]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    @staticmethod
    def calculate_volume_ratio(volumes: List[int], period: int = 20) -> Optional[float]:
        """
        거래량 비율 계산 (현재 거래량 / 평균 거래량)

        Args:
            volumes: 거래량 리스트 (최신 데이터가 마지막)
            period: 평균 계산 기간

        Returns:
            거래량 비율 (1.0 = 평균, 2.0 = 평균의 2배)
        """
        if len(volumes) < period + 1:
            return None

        # 과거 period일 평균 거래량 (오늘 제외)
        avg_volume = sum(volumes[-(period+1):-1]) / period

        if avg_volume == 0:
            return None

        current_volume = volumes[-1]
        return round(current_volume / avg_volume, 2)

    @staticmethod
    def calculate_price_change_rate(prices: List[float], period: int = 5) -> Optional[float]:
        """
        가격 변화율 계산 (모멘텀)

        Args:
            prices: 가격 리스트
            period: 비교 기간

        Returns:
            변화율 (%)
        """
        if len(prices) < period + 1:
            return None

        old_price = prices[-(period+1)]
        current_price = prices[-1]

        if old_price == 0:
            return None

        change_rate = ((current_price - old_price) / old_price) * 100
        return round(change_rate, 2)

    @staticmethod
    def is_golden_cross(short_ma_list: List[float], long_ma_list: List[float]) -> bool:
        """
        골든크로스 확인 (단기 MA가 장기 MA를 상향돌파)

        Args:
            short_ma_list: 단기 이동평균 리스트
            long_ma_list: 장기 이동평균 리스트

        Returns:
            골든크로스 발생 여부
        """
        if len(short_ma_list) < 2 or len(long_ma_list) < 2:
            return False

        # 이전: 단기 < 장기, 현재: 단기 > 장기
        prev_short = short_ma_list[-2]
        prev_long = long_ma_list[-2]
        curr_short = short_ma_list[-1]
        curr_long = long_ma_list[-1]

        if None in [prev_short, prev_long, curr_short, curr_long]:
            return False

        return prev_short <= prev_long and curr_short > curr_long

    @staticmethod
    def is_dead_cross(short_ma_list: List[float], long_ma_list: List[float]) -> bool:
        """
        데드크로스 확인 (단기 MA가 장기 MA를 하향돌파)

        Args:
            short_ma_list: 단기 이동평균 리스트
            long_ma_list: 장기 이동평균 리스트

        Returns:
            데드크로스 발생 여부
        """
        if len(short_ma_list) < 2 or len(long_ma_list) < 2:
            return False

        prev_short = short_ma_list[-2]
        prev_long = long_ma_list[-2]
        curr_short = short_ma_list[-1]
        curr_long = long_ma_list[-1]

        if None in [prev_short, prev_long, curr_short, curr_long]:
            return False

        return prev_short >= prev_long and curr_short < curr_long

    @staticmethod
    def analyze_stock(prices: List[float], volumes: List[int]) -> Dict:
        """
        종목 종합 분석

        Args:
            prices: 가격 리스트 (최소 21일치)
            volumes: 거래량 리스트

        Returns:
            분석 결과 딕셔너리
        """
        result = {
            'ma5': None,
            'ma20': None,
            'rsi': None,
            'volume_ratio': None,
            'momentum_5d': None,
            'price_above_ma5': None,
            'price_above_ma20': None,
        }

        if len(prices) >= 5:
            result['ma5'] = TechnicalIndicators.calculate_ma(prices, 5)
            if result['ma5']:
                result['price_above_ma5'] = prices[-1] > result['ma5']

        if len(prices) >= 20:
            result['ma20'] = TechnicalIndicators.calculate_ma(prices, 20)
            if result['ma20']:
                result['price_above_ma20'] = prices[-1] > result['ma20']

        if len(prices) >= 15:
            result['rsi'] = TechnicalIndicators.calculate_rsi(prices, 14)

        if len(volumes) >= 21:
            result['volume_ratio'] = TechnicalIndicators.calculate_volume_ratio(volumes, 20)

        if len(prices) >= 6:
            result['momentum_5d'] = TechnicalIndicators.calculate_price_change_rate(prices, 5)

        return result
