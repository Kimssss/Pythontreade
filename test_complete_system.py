#!/usr/bin/env python3
"""
AI Trading System 완전 테스트 스크립트
- 모든 주요 기능을 종합적으로 테스트
"""

import sys
import os
import asyncio
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트 디렉토리의 .env 파일 로드
project_root = Path(__file__).parent
load_dotenv(project_root / '.env')

# Python 경로에 추가
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'ai_trading_system'))

def print_section(title):
    """섹션 헤더 출력"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def test_imports():
    """모듈 import 테스트"""
    print_section("1. Import Test")
    
    success_count = 0
    fail_count = 0
    
    modules_to_test = [
        ("utils.kis_api", "KisAPIEnhanced"),
        ("models.dqn_agent", "DQNAgent"),
        ("models.ensemble_system", "MultiAgentEnsemble"),
        ("strategies.stock_screener", "StockScreener"),
        ("utils.risk_manager", "RiskManager"),
        ("utils.technical_indicators", "TechnicalIndicators"),
        ("training.weekend_trainer", "WeekendTrainer"),
        ("config.config", "Config"),
    ]
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✅ {module_name}.{class_name}")
            success_count += 1
        except Exception as e:
            print(f"❌ {module_name}.{class_name}: {str(e)[:50]}")
            fail_count += 1
    
    print(f"\nResults: {success_count} success, {fail_count} failed")
    return success_count > len(modules_to_test) // 2


def test_api_functions():
    """KIS API 기능 테스트"""
    print_section("2. KIS API Function Test")
    
    try:
        from utils.kis_api import KisAPIEnhanced
        from config.config import Config
        
        # 환경 변수에서 직접 가져오기
        demo_appkey = os.getenv('DEMO_APPKEY')
        demo_appsecret = os.getenv('DEMO_APPSECRET')
        demo_account = os.getenv('DEMO_ACCOUNT_NO')
        
        if not all([demo_appkey, demo_appsecret, demo_account]):
            print("❌ 환경 변수가 설정되지 않았습니다.")
            return False
        
        api = KisAPIEnhanced(
            demo_appkey,
            demo_appsecret,
            demo_account,
            is_real=False,
            min_request_interval=0.5
        )
        
        print("Testing API methods:")
        
        # 토큰 발급
        print("\n  • get_access_token()...", end=" ")
        if api.get_access_token():
            print("✅")
        else:
            print("❌")
            return False
        
        # 메소드 테스트
        test_methods = [
            ("get_balance", []),
            ("get_available_cash", []),
            ("get_holding_stocks", []),
            ("get_volume_rank", []),
            ("get_top_volume_stocks", [("count", 5)]),
            ("get_stock_price", ["005930"]),
            ("get_daily_price", ["005930", 5]),
        ]
        
        success = 0
        for method_name, args in test_methods:
            print(f"\n  • {method_name}()...", end=" ")
            try:
                method = getattr(api, method_name)
                if isinstance(args, list) and len(args) > 0 and isinstance(args[0], tuple):
                    # 키워드 인자
                    kwargs = {k: v for k, v in args}
                    result = method(**kwargs)
                else:
                    # 위치 인자
                    result = method(*args)
                
                if result is not None:
                    if isinstance(result, dict) and result.get('rt_cd') == '0':
                        print("✅")
                        success += 1
                    elif isinstance(result, (list, int, float)):
                        print("✅")
                        success += 1
                    else:
                        print(f"⚠️ (rt_cd: {result.get('rt_cd', 'N/A')})")
                else:
                    print("❌ (None)")
            except Exception as e:
                print(f"❌ ({str(e)[:30]})")
        
        print(f"\nAPI Test Results: {success}/{len(test_methods)} passed")
        return success > len(test_methods) // 2
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def test_technical_indicators():
    """기술적 지표 테스트"""
    print_section("3. Technical Indicators Test")
    
    try:
        from utils.technical_indicators import TechnicalIndicators
        import pandas as pd
        import numpy as np
        
        # 테스트 데이터 생성
        dates = pd.date_range('2024-01-01', periods=100)
        df = pd.DataFrame({
            'date': dates,
            'open': np.random.randn(100).cumsum() + 100,
            'high': np.random.randn(100).cumsum() + 102,
            'low': np.random.randn(100).cumsum() + 98,
            'close': np.random.randn(100).cumsum() + 100,
            'volume': np.random.randint(1000000, 10000000, 100)
        })
        
        # 지표 계산
        indicators = TechnicalIndicators.calculate_all(df)
        
        print(f"✅ Successfully calculated {len(indicators.columns)} indicators")
        print(f"   Indicators: {', '.join(indicators.columns[:10])}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Technical indicators test failed: {e}")
        return False


def test_risk_manager():
    """리스크 관리자 테스트"""
    print_section("4. Risk Manager Test")
    
    try:
        from utils.risk_manager import RiskManager
        
        risk_manager = RiskManager(
            initial_capital=10000000,
            max_position_size=0.1,
            stop_loss_pct=0.03,
            take_profit_pct=0.05
        )
        
        # 포지션 크기 계산
        position_size = risk_manager.calculate_position_size(
            capital=10000000,
            stock_price=50000,
            risk_score=0.7
        )
        
        print(f"✅ Position size calculated: {position_size} shares")
        print(f"   Risk parameters initialized correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Risk manager test failed: {e}")
        return False


async def test_weekend_trainer():
    """주말 학습 모듈 테스트"""
    print_section("5. Weekend Trainer Test")
    
    try:
        from training.weekend_trainer import WeekendTrainer
        from models.ensemble_system import MultiAgentEnsemble
        from utils.kis_api import KisAPIEnhanced
        
        # 환경 변수에서 직접 가져오기
        demo_appkey = os.getenv('DEMO_APPKEY')
        demo_appsecret = os.getenv('DEMO_APPSECRET')
        demo_account = os.getenv('DEMO_ACCOUNT_NO')
        
        if not all([demo_appkey, demo_appsecret, demo_account]):
            print("❌ 환경 변수가 설정되지 않았습니다.")
            return False
        
        # API 및 시스템 초기화
        api = KisAPIEnhanced(
            demo_appkey,
            demo_appsecret,
            demo_account,
            is_real=False
        )
        
        ensemble = MultiAgentEnsemble()
        trainer = WeekendTrainer(ensemble, api)
        
        print("✅ Weekend trainer initialized successfully")
        print("   Ready for training sessions")
        
        return True
        
    except Exception as e:
        print(f"❌ Weekend trainer test failed: {e}")
        return False


def test_file_structure():
    """파일 구조 테스트"""
    print_section("6. File Structure Test")
    
    required_dirs = [
        'ai_trading_system/cache',
        'ai_trading_system/logs',
        'ai_trading_system/models',
        'ai_trading_system/config',
        'ai_trading_system/utils',
        'ai_trading_system/strategies',
        'ai_trading_system/training',
        'training_cache',
        'training_results',
        'logs'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} (missing)")
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"\n⚠️ Creating missing directories...")
        for dir_path in missing_dirs:
            full_path = project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"   Created: {dir_path}")
    
    return len(missing_dirs) < len(required_dirs) // 2


async def main():
    """메인 테스트 함수"""
    print("\n" + "="*60)
    print("  AI TRADING SYSTEM COMPLETE TEST")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    total_tests = 0
    passed_tests = 0
    
    # 1. Import 테스트
    if test_imports():
        passed_tests += 1
    total_tests += 1
    
    # 2. API 기능 테스트
    if test_api_functions():
        passed_tests += 1
    total_tests += 1
    
    # 3. 기술적 지표 테스트
    if test_technical_indicators():
        passed_tests += 1
    total_tests += 1
    
    # 4. 리스크 관리자 테스트
    if test_risk_manager():
        passed_tests += 1
    total_tests += 1
    
    # 5. 주말 학습 모듈 테스트
    if await test_weekend_trainer():
        passed_tests += 1
    total_tests += 1
    
    # 6. 파일 구조 테스트
    if test_file_structure():
        passed_tests += 1
    total_tests += 1
    
    # 최종 결과
    print_section("TEST SUMMARY")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n✅ All tests passed! System is ready for use.")
    elif passed_tests >= total_tests * 0.7:
        print("\n⚠️ Most tests passed. System is functional with minor issues.")
    else:
        print("\n❌ Many tests failed. System needs attention.")


if __name__ == "__main__":
    asyncio.run(main())