"""
기술적 지표 계산 모듈
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional


class TechnicalIndicators:
    """기술적 지표 계산 클래스"""
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """단순 이동 평균"""
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """지수 이동 평균"""
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """상대 강도 지수 (RSI)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(prices: pd.Series, 
                      fast_period: int = 12, 
                      slow_period: int = 26, 
                      signal_period: int = 9) -> Dict[str, pd.Series]:
        """MACD (Moving Average Convergence Divergence)"""
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(prices: pd.Series, 
                                 period: int = 20, 
                                 std_dev: float = 2) -> Dict[str, pd.Series]:
        """볼린저 밴드"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'middle': sma,
            'upper': upper_band,
            'lower': lower_band
        }
    
    @staticmethod
    def calculate_stochastic(high: pd.Series, 
                           low: pd.Series, 
                           close: pd.Series,
                           k_period: int = 14,
                           d_period: int = 3) -> Dict[str, pd.Series]:
        """스토캐스틱 오실레이터"""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'k': k_percent,
            'd': d_percent
        }
    
    @staticmethod
    def calculate_atr(high: pd.Series, 
                     low: pd.Series, 
                     close: pd.Series, 
                     period: int = 14) -> pd.Series:
        """Average True Range (변동성 지표)"""
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On Balance Volume (거래량 지표)"""
        obv = pd.Series(index=close.index, dtype='float64')
        obv.iloc[0] = volume.iloc[0]
        
        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """모든 기술적 지표 계산
        
        Args:
            df: OHLCV 데이터프레임 (columns: open, high, low, close, volume)
        
        Returns:
            기술적 지표가 추가된 데이터프레임
        """
        result = df.copy()
        
        # 이동평균
        for period in [5, 20, 60, 120]:
            result[f'SMA{period}'] = TechnicalIndicators.calculate_sma(df['close'], period)
            
        for period in [12, 26]:
            result[f'EMA{period}'] = TechnicalIndicators.calculate_ema(df['close'], period)
        
        # RSI
        result['RSI'] = TechnicalIndicators.calculate_rsi(df['close'])
        
        # MACD
        macd_data = TechnicalIndicators.calculate_macd(df['close'])
        result['MACD'] = macd_data['macd']
        result['MACD_signal'] = macd_data['signal']
        result['MACD_hist'] = macd_data['histogram']
        
        # 볼린저 밴드
        bb_data = TechnicalIndicators.calculate_bollinger_bands(df['close'])
        result['BB_upper'] = bb_data['upper']
        result['BB_middle'] = bb_data['middle']
        result['BB_lower'] = bb_data['lower']
        
        # 스토캐스틱
        stoch_data = TechnicalIndicators.calculate_stochastic(
            df['high'], df['low'], df['close']
        )
        result['Stoch_K'] = stoch_data['k']
        result['Stoch_D'] = stoch_data['d']
        
        # ATR (변동성)
        result['ATR'] = TechnicalIndicators.calculate_atr(
            df['high'], df['low'], df['close']
        )
        
        # OBV (거래량)
        result['OBV'] = TechnicalIndicators.calculate_obv(df['close'], df['volume'])
        
        # 거래량 이동평균
        result['Volume_MA'] = df['volume'].rolling(window=20).mean()
        
        return result
    
    @staticmethod
    def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 기반 매매 신호 생성"""
        signals = pd.DataFrame(index=df.index)
        
        # 이동평균 크로스오버
        signals['MA_cross'] = np.where(
            (df['SMA20'] > df['SMA60']) & 
            (df['SMA20'].shift() <= df['SMA60'].shift()), 1,
            np.where(
                (df['SMA20'] < df['SMA60']) & 
                (df['SMA20'].shift() >= df['SMA60'].shift()), -1, 0
            )
        )
        
        # RSI 신호
        signals['RSI_signal'] = np.where(df['RSI'] < 30, 1,
                                       np.where(df['RSI'] > 70, -1, 0))
        
        # MACD 신호
        signals['MACD_signal'] = np.where(
            (df['MACD'] > df['MACD_signal']) & 
            (df['MACD'].shift() <= df['MACD_signal'].shift()), 1,
            np.where(
                (df['MACD'] < df['MACD_signal']) & 
                (df['MACD'].shift() >= df['MACD_signal'].shift()), -1, 0
            )
        )
        
        # 볼린저 밴드 신호
        signals['BB_signal'] = np.where(df['close'] < df['BB_lower'], 1,
                                      np.where(df['close'] > df['BB_upper'], -1, 0))
        
        # 스토캐스틱 신호
        signals['Stoch_signal'] = np.where(
            (df['Stoch_K'] < 20) & (df['Stoch_D'] < 20), 1,
            np.where(
                (df['Stoch_K'] > 80) & (df['Stoch_D'] > 80), -1, 0
            )
        )
        
        # 거래량 이상 신호
        signals['Volume_signal'] = np.where(
            df['volume'] > df['Volume_MA'] * 1.5, 1, 0
        )
        
        # 종합 신호 (가중 평균)
        weights = {
            'MA_cross': 0.25,
            'RSI_signal': 0.2,
            'MACD_signal': 0.25,
            'BB_signal': 0.15,
            'Stoch_signal': 0.1,
            'Volume_signal': 0.05
        }
        
        signals['composite_signal'] = sum(
            signals[col] * weight for col, weight in weights.items()
        )
        
        # 최종 매매 신호 (-1: 매도, 0: 보유, 1: 매수)
        signals['final_signal'] = np.where(signals['composite_signal'] > 0.5, 1,
                                         np.where(signals['composite_signal'] < -0.5, -1, 0))
        
        return signals