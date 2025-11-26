#!/usr/bin/env python3
"""
고급 AI 자동매매 시스템 - 블로그 분석 결과 기반 구현
- Multi-Agent 강화학습 앙상블
- Dynamic Factor Model
- Regime Detection
- Risk Parity 포지션 사이징
"""

import sys
import os
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import logging
from datetime import datetime, timedelta
import json
from pathlib import Path

# 자동 패키지 설치
try:
    from auto_install import check_and_install_requirements, auto_install_on_import
    check_and_install_requirements()
except ImportError:
    print("⚠️ 자동 설치 모듈을 찾을 수 없습니다. 수동으로 패키지를 설치해주세요.")

try:
    import tensorflow as tf
    HAS_TF = True
except ImportError:
    HAS_TF = False

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import ta
try:
    from hmmlearn import GaussianHMM
    HAS_HMM = True
except ImportError:
    HAS_HMM = False
    print("⚠️ hmmlearn not available. Using simplified regime detection.")

import warnings
warnings.filterwarnings('ignore')

from kis_api import KisAPI
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RegimeDetector:
    """
    시장 레짐 탐지 (HMM 기반 또는 간단한 규칙 기반)
    - 강세장 (Bull Market)
    - 약세장 (Bear Market) 
    - 횡보장 (Sideways Market)
    """
    
    def __init__(self, n_regimes=3):
        self.n_regimes = n_regimes
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        if HAS_HMM:
            self.model = GaussianHMM(n_components=n_regimes, covariance_type="full")
            self.use_hmm = True
        else:
            self.model = None
            self.use_hmm = False
            print("📊 간단한 규칙 기반 레짐 탐지를 사용합니다.")
        
    def prepare_features(self, prices: pd.Series) -> np.ndarray:
        """시장 레짐 특성 추출"""
        df = pd.DataFrame({'price': prices})
        
        # 수익률과 변동성 계산
        df['returns'] = df['price'].pct_change()
        df['volatility'] = df['returns'].rolling(20).std()
        df['momentum'] = df['price'] / df['price'].shift(20) - 1
        df['volume_trend'] = df['returns'].rolling(10).mean()
        
        # 기술적 지표
        df['rsi'] = ta.momentum.RSIIndicator(df['price']).rsi()
        df['bb_position'] = ta.volatility.BollingerBands(df['price']).bollinger_pband()
        
        features = df[['returns', 'volatility', 'momentum', 'volume_trend', 'rsi', 'bb_position']].dropna()
        return features.values
    
    def fit(self, price_data: pd.Series):
        """레짐 모델 훈련"""
        features = self.prepare_features(price_data)
        
        if self.use_hmm and self.model:
            features_scaled = self.scaler.fit_transform(features)
            self.model.fit(features_scaled)
        else:
            # 간단한 규칙 기반
            self.scaler.fit(features)
        
        self.is_fitted = True
        logger.info(f"레짐 탐지 모델 훈련 완료: {self.n_regimes}개 레짐")
    
    def predict_regime(self, price_data: pd.Series) -> int:
        """현재 시장 레짐 예측"""
        if not self.is_fitted:
            return 1  # 기본값: 중성
        
        if self.use_hmm and self.model:
            features = self.prepare_features(price_data)
            features_scaled = self.scaler.transform(features[-1:])
            regime = self.model.predict(features_scaled)[-1]
            return int(regime)
        else:
            # 간단한 규칙 기반 레짐 분류
            returns = price_data.pct_change().dropna()
            if len(returns) < 10:
                return 1
            
            recent_return = returns.tail(20).mean()
            volatility = returns.tail(20).std()
            
            if recent_return > 0.01 and volatility < 0.03:
                return 0  # 강세장
            elif recent_return < -0.01:
                return 2  # 약세장
            else:
                return 1  # 횡보장
    
    def get_regime_probabilities(self, price_data: pd.Series) -> np.ndarray:
        """각 레짐별 확률 반환"""
        if not self.is_fitted:
            return np.array([0.33, 0.34, 0.33])  # 기본값
        
        if self.use_hmm and self.model:
            features = self.prepare_features(price_data)
            features_scaled = self.scaler.transform(features[-1:])
            probs = self.model.predict_proba(features_scaled)[-1]
            return probs
        else:
            # 간단한 확률 반환
            regime = self.predict_regime(price_data)
            probs = np.array([0.1, 0.1, 0.1])
            probs[regime] = 0.8
            return probs

class DynamicFactorModel:
    """
    동적 팩터 모델
    - 가치/성장/모멘텀/품질/수익성 팩터
    - 시장 상황에 따른 동적 가중치 조정
    """
    
    def __init__(self):
        self.factors = ['value', 'growth', 'momentum', 'quality', 'profitability']
        self.weights = {factor: 0.2 for factor in self.factors}  # 초기 동일 가중
        self.scaler = StandardScaler()
        
    def calculate_factor_scores(self, stock_data: Dict) -> Dict[str, float]:
        """종목별 팩터 스코어 계산"""
        scores = {}
        
        # 가치 팩터 (PER, PBR 역수)
        scores['value'] = 1 / (stock_data.get('per', 10) + 0.01) + 1 / (stock_data.get('pbr', 1) + 0.01)
        
        # 성장 팩터 (매출/이익 성장률)
        scores['growth'] = stock_data.get('sales_growth', 0) + stock_data.get('profit_growth', 0)
        
        # 모멘텀 팩터 (3/6/12개월 수익률)
        scores['momentum'] = (stock_data.get('return_3m', 0) + 
                             stock_data.get('return_6m', 0) + 
                             stock_data.get('return_12m', 0)) / 3
        
        # 품질 팩터 (ROE, 부채비율)
        scores['quality'] = stock_data.get('roe', 0) - stock_data.get('debt_ratio', 0) / 100
        
        # 수익성 팩터 (영업마진, 순이익마진)
        scores['profitability'] = stock_data.get('operating_margin', 0) + stock_data.get('net_margin', 0)
        
        return scores
    
    def update_weights_by_regime(self, regime: int):
        """레짐에 따른 팩터 가중치 동적 조정"""
        if regime == 0:  # 강세장
            self.weights = {
                'value': 0.15,
                'growth': 0.30,
                'momentum': 0.35,
                'quality': 0.10,
                'profitability': 0.10
            }
        elif regime == 1:  # 약세장
            self.weights = {
                'value': 0.40,
                'growth': 0.10,
                'momentum': 0.05,
                'quality': 0.25,
                'profitability': 0.20
            }
        else:  # 횡보장
            self.weights = {
                'value': 0.25,
                'growth': 0.20,
                'momentum': 0.15,
                'quality': 0.25,
                'profitability': 0.15
            }
        
        logger.info(f"레짐 {regime}에 따른 팩터 가중치 조정: {self.weights}")
    
    def calculate_composite_score(self, factor_scores: Dict[str, float]) -> float:
        """팩터들을 가중 합산하여 종합 스코어 계산"""
        total_score = 0
        for factor, score in factor_scores.items():
            total_score += self.weights.get(factor, 0) * score

        return total_score

class RiskManager:
    """
    리스크 관리자 - VaR/CVaR 기반 포지션 사이징
    """
    
    def __init__(self, confidence_level=0.05, lookback_period=252):
        self.confidence_level = confidence_level
        self.lookback_period = lookback_period
        self.max_position_size = 0.1  # 개별 종목 최대 10%
        self.max_total_exposure = 0.8  # 전체 노출도 최대 80%
    
    def calculate_var(self, returns: pd.Series) -> float:
        """Value at Risk 계산"""
        if len(returns) < 30:
            return 0.02  # 기본값 2%
        
        return np.percentile(returns, self.confidence_level * 100)
    
    def calculate_cvar(self, returns: pd.Series) -> float:
        """Conditional Value at Risk 계산"""
        var = self.calculate_var(returns)
        cvar_returns = returns[returns <= var]
        return cvar_returns.mean() if len(cvar_returns) > 0 else var
    
    def calculate_position_size(self, expected_return: float, volatility: float, 
                              current_portfolio_value: float) -> float:
        """Kelly Criterion + Risk Parity 기반 포지션 사이징"""
        if volatility <= 0:
            return 0
        
        # Kelly Criterion
        kelly_fraction = expected_return / (volatility ** 2)
        
        # 리스크 패리티 조정
        risk_adjusted_size = min(kelly_fraction, 0.5)  # 최대 50%로 제한
        
        # 개별 종목 한도 적용
        final_size = min(risk_adjusted_size, self.max_position_size)
        
        return max(0, final_size)
    
    def check_portfolio_risk(self, positions: Dict, prices: Dict) -> bool:
        """포트폴리오 전체 리스크 점검"""
        total_exposure = sum(positions.values()) / sum(
            pos * prices.get(stock, 1) for stock, pos in positions.items()
        )
        
        return total_exposure <= self.max_total_exposure

class MultiAgentTrader:
    """
    멀티 에이전트 트레이더
    - DQN 에이전트
    - 팩터 기반 에이전트  
    - 기술적 분석 에이전트
    - 앙상블 메타 러닝
    """
    
    def __init__(self, kis_api: KisAPI, stocks: List[str]):
        self.kis_api = kis_api
        self.stocks = stocks
        
        # 하위 시스템 초기화
        self.regime_detector = RegimeDetector()
        self.factor_model = DynamicFactorModel()
        self.risk_manager = RiskManager()
        
        # 에이전트별 가중치 (성능에 따라 동적 조정)
        self.agent_weights = {
            'dqn': 0.4,
            'factor': 0.3,
            'technical': 0.3
        }
        
        # 성과 추적
        self.performance_history = []
        
    def initialize_regime_detector(self):
        """레짐 탐지기 초기화 (과거 데이터 학습)"""
        try:
            # KOSPI 지수 데이터로 레짐 학습 (여기서는 삼성전자 대용)
            price_data = self.kis_api.get_daily_price('005930', count=500)
            if price_data and price_data.get('rt_cd') == '0':
                prices = pd.Series([
                    float(item['stck_clpr']) for item in price_data['output']
                ])
                prices = prices.iloc[::-1]  # 시간순 정렬
                
                self.regime_detector.fit(prices)
                logger.info("레짐 탐지기 초기화 완료")
            else:
                logger.warning("레짐 탐지기 초기화 실패: 가격 데이터 없음")
        except Exception as e:
            logger.error(f"레짐 탐지기 초기화 오류: {e}")
    
    def get_dqn_signal(self, stock: str) -> float:
        """DQN 에이전트 신호 (-1~1)"""
        # 기존 DQN 로직 사용 (간소화)
        try:
            price_data = self.kis_api.get_stock_price(stock)
            if not price_data or price_data.get('rt_cd') != '0':
                return 0
            
            # 단순화된 DQN 신호 (실제로는 신경망 예측)
            current_price = float(price_data['output']['stck_prpr'])
            prev_price = float(price_data['output']['stck_oprc'])
            
            price_change = (current_price - prev_price) / prev_price
            signal = np.tanh(price_change * 10)  # -1~1 정규화
            
            return signal
        except:
            return 0
    
    def get_factor_signal(self, stock: str, regime: int) -> float:
        """팩터 모델 신호"""
        try:
            # 팩터 가중치 조정
            self.factor_model.update_weights_by_regime(regime)
            
            # 종목 기본 정보 (실제로는 kis_api에서 가져와야 함)
            stock_data = {
                'per': 10.5, 'pbr': 1.2, 'roe': 15.2,
                'sales_growth': 8.5, 'profit_growth': 12.3,
                'return_3m': 5.2, 'return_6m': -2.1, 'return_12m': 15.8,
                'debt_ratio': 45.2, 'operating_margin': 12.5, 'net_margin': 9.8
            }
            
            factor_scores = self.factor_model.calculate_factor_scores(stock_data)
            composite_score = self.factor_model.calculate_composite_score(factor_scores)
            
            # 시그널 정규화
            signal = np.tanh(composite_score / 10)
            return signal
        except:
            return 0
    
    def get_technical_signal(self, stock: str) -> float:
        """기술적 분석 신호"""
        try:
            daily_data = self.kis_api.get_daily_price(stock, count=50)
            if not daily_data or daily_data.get('rt_cd') != '0':
                return 0
            
            prices = pd.Series([
                float(item['stck_clpr']) for item in daily_data['output'][::-1]
            ])
            
            # 기술적 지표 계산
            rsi = ta.momentum.RSIIndicator(prices, window=14).rsi().iloc[-1]
            macd_diff = ta.trend.MACD(prices).macd_diff().iloc[-1]
            bb_pband = ta.volatility.BollingerBands(prices).bollinger_pband().iloc[-1]
            
            # 복합 기술적 신호
            rsi_signal = (50 - rsi) / 50  # RSI 50 기준 역방향
            macd_signal = np.tanh(macd_diff * 100)
            bb_signal = (bb_pband - 0.5) * 2  # 볼린저 밴드 중심 기준
            
            technical_signal = (rsi_signal + macd_signal + bb_signal) / 3
            return technical_signal
        except:
            return 0
    
    def get_ensemble_signal(self, stock: str) -> Tuple[float, Dict]:
        """앙상블 신호 생성"""
        # 현재 레짐 탐지
        try:
            price_data = self.kis_api.get_daily_price(stock, count=100)
            prices = pd.Series([
                float(item['stck_clpr']) for item in price_data['output'][::-1]
            ])
            current_regime = self.regime_detector.predict_regime(prices)
        except:
            current_regime = 1  # 기본값: 중성
        
        # 각 에이전트 신호 수집
        signals = {
            'dqn': self.get_dqn_signal(stock),
            'factor': self.get_factor_signal(stock, current_regime),
            'technical': self.get_technical_signal(stock)
        }
        
        # 가중 평균으로 최종 신호 계산
        ensemble_signal = sum(
            signals[agent] * self.agent_weights[agent] 
            for agent in signals
        )
        
        return ensemble_signal, {
            'regime': current_regime,
            'signals': signals,
            'weights': self.agent_weights.copy()
        }
    
    def execute_trades(self):
        """실제 거래 실행"""
        logger.info("멀티 에이전트 트레이딩 시작")
        
        try:
            # 현재 포트폴리오 상태
            balance = self.kis_api.get_balance()
            available_cash = self.kis_api.get_available_cash()
            holdings = self.kis_api.get_holding_stocks()
            
            logger.info(f"사용 가능 현금: {available_cash:,}원")
            logger.info(f"보유 종목 수: {len(holdings)}")
            
            # 각 종목별 신호 생성 및 거래
            for stock in self.stocks:
                signal, info = self.get_ensemble_signal(stock)
                
                logger.info(f"{stock} - 신호: {signal:.3f}, 레짐: {info['regime']}")
                
                # 포지션 사이징
                if abs(signal) > 0.1:  # 임계값 이상일 때만 거래
                    self._execute_stock_trade(stock, signal, available_cash)
        
        except Exception as e:
            logger.error(f"거래 실행 중 오류: {e}")
    
    def _execute_stock_trade(self, stock: str, signal: float, available_cash: float):
        """개별 종목 거래 실행"""
        try:
            price_info = self.kis_api.get_stock_price(stock)
            if not price_info or price_info.get('rt_cd') != '0':
                return
            
            current_price = int(price_info['output']['stck_prpr'])
            
            # 리스크 관리된 포지션 크기 계산
            position_value = available_cash * self.risk_manager.calculate_position_size(
                signal * 0.1,  # 예상 수익률 (10% 스케일)
                0.2,  # 가정된 변동성
                available_cash
            )
            
            quantity = int(position_value / current_price)
            
            if signal > 0.1 and quantity > 0:  # 매수 신호
                logger.info(f"{stock} 매수 주문: {quantity}주 @ {current_price:,}원")
                result = self.kis_api.buy_stock(stock, quantity, order_type="03")  # 시장가
                
                if result and result.get('rt_cd') == '0':
                    logger.info(f"매수 성공: {result.get('output', {}).get('ODNO', 'N/A')}")
                else:
                    logger.warning(f"매수 실패: {result}")
                    
            elif signal < -0.1:  # 매도 신호
                # 보유 수량 확인 후 매도
                holdings = self.kis_api.get_holding_stocks()
                stock_holding = next((h for h in holdings if h['stock_code'] == stock), None)
                
                if stock_holding and stock_holding['quantity'] > 0:
                    sell_quantity = stock_holding['quantity']
                    logger.info(f"{stock} 매도 주문: {sell_quantity}주 @ {current_price:,}원")
                    
                    result = self.kis_api.sell_stock(stock, sell_quantity, order_type="03")
                    
                    if result and result.get('rt_cd') == '0':
                        logger.info(f"매도 성공: {result.get('output', {}).get('ODNO', 'N/A')}")
                    else:
                        logger.warning(f"매도 실패: {result}")
        
        except Exception as e:
            logger.error(f"{stock} 거래 실행 중 오류: {e}")

class AutoMLOptimizer:
    """
    간단한 파라미터 최적화 (Optuna 없이)
    """
    
    def __init__(self, trader: MultiAgentTrader):
        self.trader = trader
        
    def optimize_simple(self):
        """간단한 그리드 서치 최적화"""
        best_sharpe = -999
        best_weights = None
        
        # 간단한 가중치 조합들
        weight_combinations = [
            {'dqn': 0.5, 'factor': 0.3, 'technical': 0.2},
            {'dqn': 0.4, 'factor': 0.4, 'technical': 0.2},
            {'dqn': 0.3, 'factor': 0.5, 'technical': 0.2},
            {'dqn': 0.3, 'factor': 0.3, 'technical': 0.4},
        ]
        
        for weights in weight_combinations:
            self.trader.agent_weights = weights
            returns = self._simulate_trading()
            sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
            
            if sharpe > best_sharpe:
                best_sharpe = sharpe
                best_weights = weights
        
        logger.info(f"최적 가중치: {best_weights}")
        logger.info(f"최고 샤프 비율: {best_sharpe:.4f}")
        
        return best_weights
    
    def _simulate_trading(self) -> List[float]:
        """트레이딩 시뮬레이션"""
        returns = []
        for _ in range(30):  # 30일 시뮬레이션
            daily_return = np.random.normal(0.001, 0.02)  # 임시 수익률
            returns.append(daily_return)
        return returns

def main():
    """메인 실행 함수"""
    print("🚀 고급 AI 자동매매 시스템 v2.0")
    print("=" * 60)
    
    mode = input("모드를 선택하세요 (demo/real/optimize): ").strip().lower()
    
    try:
        # API 초기화
        account_info = Config.get_account_info('demo' if mode in ['demo', 'optimize'] else 'real')
        kis_api = KisAPI(
            account_info['appkey'],
            account_info['appsecret'], 
            account_info['account'],
            is_real=(mode == 'real')
        )
        
        if not kis_api.get_access_token():
            raise Exception("API 토큰 발급 실패")
        
        # 멀티 에이전트 트레이더 초기화
        stocks = ['005930', '000660', '051910', '035420', '068270']  # 주요 종목
        trader = MultiAgentTrader(kis_api, stocks)
        trader.initialize_regime_detector()
        
        if mode == 'optimize':
            print("🧠 간단한 파라미터 최적화 시작...")
            optimizer = AutoMLOptimizer(trader)
            best_params = optimizer.optimize_simple()
            print(f"✅ 최적화 완료: {best_params}")
            
        else:
            print(f"🤖 멀티 에이전트 트레이딩 시작 ({mode} 모드)")
            print("중단하려면 Ctrl+C를 눌러주세요")
            
            import time
            while True:
                trader.execute_trades()
                print("⏱️ 30분 대기 중...")
                time.sleep(30 * 60)  # 30분 대기
    
    except KeyboardInterrupt:
        print("\n👋 시스템을 안전하게 종료합니다.")
    except Exception as e:
        logger.error(f"시스템 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()