#!/usr/bin/env python3
"""
AI 자동매매 시스템 기능 점검 스크립트
"""
import os
import sys
from pathlib import Path

# 프로젝트 경로 설정
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root.parent))

print("=" * 60)
print("AI TRADING SYSTEM - FUNCTIONALITY CHECK")
print("=" * 60)

# 1. Import 테스트
print("\n1. Testing imports...")
try:
    from config.settings import KIS_CONFIG, TRADING_CONFIG
    print("✓ Config settings imported")
except Exception as e:
    print(f"✗ Config import error: {e}")

try:
    from utils.kis_api import KisAPIEnhanced
    print("✓ KIS API imported")
except Exception as e:
    print(f"✗ KIS API import error: {e}")

try:
    from utils.technical_indicators import TechnicalIndicators
    print("✓ Technical indicators imported")
except Exception as e:
    print(f"✗ Technical indicators import error: {e}")

try:
    from utils.risk_manager import RiskManager
    print("✓ Risk manager imported")
except Exception as e:
    print(f"✗ Risk manager import error: {e}")

try:
    from models.dqn_agent import DQNAgent
    print("✓ DQN agent imported")
except Exception as e:
    print(f"✗ DQN agent import error: {e}")

try:
    from models.ensemble_system import MultiAgentEnsemble
    print("✓ Ensemble system imported")
except Exception as e:
    print(f"✗ Ensemble system import error: {e}")

try:
    from strategies.stock_screener import StockScreener
    print("✓ Stock screener imported")
except Exception as e:
    print(f"✗ Stock screener import error: {e}")

# 2. 환경 변수 체크
print("\n2. Checking environment variables...")
env_vars = {
    'Demo App Key': os.environ.get('KIS_DEMO_APPKEY'),
    'Demo App Secret': os.environ.get('KIS_DEMO_APPSECRET'),
    'Demo Account': os.environ.get('KIS_DEMO_ACCOUNT')
}

for key, value in env_vars.items():
    if value:
        print(f"✓ {key}: {'*' * 10}")
    else:
        print(f"✗ {key}: Not set")

# 3. 기능 테스트
print("\n3. Testing core functionalities...")

# 기술적 지표 테스트
try:
    import pandas as pd
    import numpy as np
    
    # 더미 데이터 생성
    dates = pd.date_range(start='2024-01-01', periods=100)
    prices = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000000, 5000000, 100)
    }, index=dates)
    
    indicators = TechnicalIndicators()
    result = indicators.calculate_all_indicators(prices)
    print(f"✓ Technical indicators: {len(result.columns)} indicators calculated")
except Exception as e:
    print(f"✗ Technical indicators test error: {e}")

# 리스크 관리 테스트
try:
    risk_manager = RiskManager()
    returns = pd.Series(np.random.randn(100) * 0.01)
    var = risk_manager.calculate_var(returns)
    cvar = risk_manager.calculate_cvar(returns)
    sharpe = risk_manager.calculate_sharpe_ratio(returns)
    
    print(f"✓ Risk metrics: VaR={var:.3f}, CVaR={cvar:.3f}, Sharpe={sharpe:.2f}")
except Exception as e:
    print(f"✗ Risk manager test error: {e}")

# DQN 에이전트 테스트
try:
    dqn_agent = DQNAgent()
    state = np.random.randn(31)
    action = dqn_agent.act(state, training=False)
    print(f"✓ DQN agent: Action={action} for random state")
except Exception as e:
    print(f"✗ DQN agent test error: {e}")

# 4. 디렉토리 구조 체크
print("\n4. Checking directory structure...")
directories = ['logs', 'models', 'cache']
for dir_name in directories:
    dir_path = project_root / dir_name
    if dir_path.exists():
        print(f"✓ {dir_name}/ directory exists")
    else:
        dir_path.mkdir(exist_ok=True, parents=True)
        print(f"✓ {dir_name}/ directory created")

# 5. 파일 권한 체크
print("\n5. Checking file permissions...")
try:
    run_script = project_root / 'run_trading.py'
    if run_script.exists():
        os.chmod(run_script, 0o755)
        print("✓ run_trading.py is executable")
except Exception as e:
    print(f"✗ Permission error: {e}")

print("\n" + "=" * 60)
print("FUNCTIONALITY CHECK COMPLETE")
print("=" * 60)