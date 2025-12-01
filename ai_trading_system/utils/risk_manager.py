"""
리스크 관리 모듈
VaR/CVaR 계산 및 포지션 사이징
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime, timedelta

try:
    from ..config.settings import TRADING_CONFIG
except ImportError:
    from config.settings import TRADING_CONFIG

logger = logging.getLogger('ai_trading.risk')


class RiskManager:
    """리스크 관리 클래스"""
    
    def __init__(self, initial_capital=10000000, max_position_size=0.1, 
                 stop_loss_pct=0.03, take_profit_pct=0.05):
        try:
            self.config = TRADING_CONFIG
            self.max_position_size = self.config['max_position_size']
            self.max_sector_exposure = self.config['max_sector_exposure']
            self.max_drawdown_limit = self.config['max_drawdown_limit']
            self.var_limit = self.config['var_limit']
            self.stop_loss_rate = self.config['stop_loss_rate']
            self.take_profit_rate = self.config['take_profit_rate']
        except:
            # 기본값 사용
            self.max_position_size = max_position_size
            self.max_sector_exposure = 0.3
            self.max_drawdown_limit = 0.1
            self.var_limit = 0.02
            self.stop_loss_rate = stop_loss_pct
            self.take_profit_rate = take_profit_pct
        
        self.initial_capital = initial_capital
        
        # 리스크 메트릭 히스토리
        self.risk_history = []
        
    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        """Value at Risk (VaR) 계산
        
        Args:
            returns: 수익률 시계열
            confidence_level: 신뢰 수준 (기본 95%)
        
        Returns:
            VaR 값 (손실은 양수로 표현)
        """
        if len(returns) < 20:
            logger.warning("Insufficient data for VaR calculation")
            return 0.02  # 기본값
        
        # 역사적 VaR 계산
        var_percentile = (1 - confidence_level) * 100
        var = -np.percentile(returns, var_percentile)
        
        return var
    
    def calculate_cvar(self, returns: pd.Series, confidence_level: float = 0.95) -> float:
        """Conditional Value at Risk (CVaR) 계산
        
        Args:
            returns: 수익률 시계열
            confidence_level: 신뢰 수준
        
        Returns:
            CVaR 값
        """
        var = self.calculate_var(returns, confidence_level)
        
        # VaR를 초과하는 손실들의 평균
        extreme_losses = returns[returns <= -var]
        if len(extreme_losses) == 0:
            return var
        
        cvar = -extreme_losses.mean()
        return cvar
    
    def calculate_sharpe_ratio(self, returns: pd.Series, 
                             risk_free_rate: float = 0.02) -> float:
        """샤프 비율 계산
        
        Args:
            returns: 수익률 시계열
            risk_free_rate: 무위험 수익률 (연간)
        
        Returns:
            샤프 비율
        """
        if len(returns) < 20:
            return 0
        
        # 일간 수익률을 연간화
        annual_return = returns.mean() * 252
        annual_std = returns.std() * np.sqrt(252)
        
        if annual_std == 0:
            return 0
        
        sharpe = (annual_return - risk_free_rate) / annual_std
        return sharpe
    
    def calculate_max_drawdown(self, equity_curve: pd.Series) -> Tuple[float, int]:
        """최대 낙폭 계산
        
        Returns:
            (최대 낙폭 비율, 회복 기간)
        """
        # 누적 최고점
        rolling_max = equity_curve.expanding().max()
        
        # 낙폭
        drawdown = (equity_curve - rolling_max) / rolling_max
        
        # 최대 낙폭
        max_dd = drawdown.min()
        
        # 회복 기간 계산
        if max_dd == 0:
            recovery_period = 0
        else:
            dd_start = drawdown.idxmin()
            dd_series = drawdown.loc[dd_start:]
            recovery_idx = dd_series[dd_series >= -0.01].index
            
            if len(recovery_idx) > 0:
                recovery_period = (recovery_idx[0] - dd_start).days
            else:
                recovery_period = (drawdown.index[-1] - dd_start).days
        
        return max_dd, recovery_period
    
    def calculate_position_size(self, signal_strength: float, 
                              current_portfolio_value: float,
                              stock_price: float,
                              volatility: float) -> int:
        """포지션 사이즈 계산 (켈리 공식 변형)
        
        Args:
            signal_strength: 신호 강도 (0-1)
            current_portfolio_value: 현재 포트폴리오 가치
            stock_price: 주식 가격
            volatility: 변동성
        
        Returns:
            주식 수량
        """
        # 기본 포지션 크기 (포트폴리오의 일정 비율)
        base_position_value = current_portfolio_value * self.max_position_size
        
        # 신호 강도에 따른 조정
        adjusted_position_value = base_position_value * signal_strength
        
        # 변동성에 따른 조정 (변동성이 높으면 포지션 축소)
        if volatility > 0:
            volatility_adjustment = min(0.02 / volatility, 1.0)
            adjusted_position_value *= volatility_adjustment
        
        # 주식 수량 계산
        shares = int(adjusted_position_value / stock_price)
        
        # 최소 거래 단위 확인
        if shares < 1:
            shares = 0
        
        return shares
    
    def check_risk_limits(self, portfolio: Dict[str, Dict], 
                         new_position: Dict) -> Tuple[bool, str]:
        """리스크 한도 체크
        
        Args:
            portfolio: 현재 포트폴리오
            new_position: 신규 포지션
        
        Returns:
            (승인 여부, 거부 사유)
        """
        # 개별 종목 한도 체크
        total_value = sum(pos['value'] for pos in portfolio.values())
        if new_position['value'] > total_value * self.max_position_size:
            return False, f"Position size exceeds limit ({self.max_position_size*100}%)"
        
        # 포트폴리오 VaR 체크
        if 'returns' in portfolio:
            current_var = self.calculate_var(portfolio['returns'])
            if current_var > self.var_limit:
                return False, f"Portfolio VaR exceeds limit ({self.var_limit*100}%)"
        
        # 최대 낙폭 체크
        if 'equity_curve' in portfolio:
            max_dd, _ = self.calculate_max_drawdown(portfolio['equity_curve'])
            if abs(max_dd) > self.max_drawdown_limit:
                return False, f"Max drawdown exceeds limit ({self.max_drawdown_limit*100}%)"
        
        return True, "Approved"
    
    def calculate_stop_loss_price(self, entry_price: float, 
                                 position_type: str = 'long') -> float:
        """손절가 계산
        
        Args:
            entry_price: 진입가
            position_type: 포지션 타입 ('long' or 'short')
        
        Returns:
            손절가
        """
        if position_type == 'long':
            stop_loss = entry_price * (1 - self.stop_loss_rate)
        else:
            stop_loss = entry_price * (1 + self.stop_loss_rate)
        
        return stop_loss
    
    def calculate_take_profit_price(self, entry_price: float, 
                                   position_type: str = 'long') -> float:
        """익절가 계산
        
        Args:
            entry_price: 진입가
            position_type: 포지션 타입
        
        Returns:
            익절가
        """
        if position_type == 'long':
            take_profit = entry_price * (1 + self.take_profit_rate)
        else:
            take_profit = entry_price * (1 - self.take_profit_rate)
        
        return take_profit
    
    def adjust_leverage_by_risk(self, returns: pd.Series) -> float:
        """리스크 기반 레버리지 조정
        
        Returns:
            레버리지 비율 (0.0 ~ 1.0)
        """
        if len(returns) < 20:
            return 0.5  # 기본값
        
        # VaR와 CVaR 계산
        var = self.calculate_var(returns)
        cvar = self.calculate_cvar(returns)
        
        # 리스크 점수 계산
        risk_score = var + 0.5 * cvar
        
        # 레버리지 조정
        if risk_score > 0.05:
            leverage = 0.5  # 고위험: 50%
        elif risk_score > 0.03:
            leverage = 0.7  # 중위험: 70%
        else:
            leverage = 1.0  # 저위험: 100%
        
        logger.info(f"Risk-adjusted leverage: {leverage:.2f} (VaR: {var:.4f}, CVaR: {cvar:.4f})")
        
        return leverage
    
    def get_risk_metrics(self, portfolio: pd.DataFrame) -> Dict:
        """포트폴리오 리스크 메트릭 계산
        
        Returns:
            리스크 메트릭 딕셔너리
        """
        if 'returns' not in portfolio.columns:
            portfolio['returns'] = portfolio['value'].pct_change()
        
        returns = portfolio['returns'].dropna()
        
        metrics = {
            'var_95': self.calculate_var(returns, 0.95),
            'cvar_95': self.calculate_cvar(returns, 0.95),
            'sharpe_ratio': self.calculate_sharpe_ratio(returns),
            'max_drawdown': self.calculate_max_drawdown(portfolio['value'])[0],
            'volatility': returns.std() * np.sqrt(252),
            'downside_deviation': returns[returns < 0].std() * np.sqrt(252),
            'sortino_ratio': self.calculate_sortino_ratio(returns)
        }
        
        # 히스토리에 저장
        metrics['timestamp'] = datetime.now()
        self.risk_history.append(metrics)
        
        # 최근 100개만 유지
        if len(self.risk_history) > 100:
            self.risk_history = self.risk_history[-100:]
        
        return metrics
    
    def calculate_sortino_ratio(self, returns: pd.Series, 
                              target_return: float = 0) -> float:
        """소르티노 비율 계산"""
        excess_returns = returns - target_return/252  # 일간 목표 수익률
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0:
            return 0
        
        downside_deviation = np.sqrt((downside_returns**2).mean()) * np.sqrt(252)
        
        if downside_deviation == 0:
            return 0
        
        annual_return = returns.mean() * 252
        sortino = (annual_return - target_return) / downside_deviation
        
        return sortino