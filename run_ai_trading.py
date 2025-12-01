#!/usr/bin/env python3
"""
AI 자동매매 시스템 실행 스크립트 (Import 문제 해결 버전)
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 경로를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / 'ai_trading_system'))

# .env 파일 로드
env_path = current_dir / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    # 기본 환경변수가 없으면 로드 시도
    load_dotenv()

# 이제 import
try:
    from ai_trading_system.main_trading_system import main, AITradingSystem
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're in the correct directory and dependencies are installed")
    sys.exit(1)


def setup_environment(mode: str):
    """환경 설정"""
    # 로그 디렉토리 생성
    log_dir = current_dir / "ai_trading_system" / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 모델 디렉토리 생성
    model_dir = current_dir / "ai_trading_system" / "models"
    model_dir.mkdir(exist_ok=True)
    
    # 캐시 디렉토리 생성
    cache_dir = current_dir / "ai_trading_system" / "cache"
    cache_dir.mkdir(exist_ok=True)
    
    # 트레이딩 모드 설정
    os.environ['TRADING_MODE'] = mode
    
    print(f"Environment set up for {mode} mode")


def check_dependencies():
    """의존성 체크"""
    try:
        import numpy
        import pandas
        import torch
        import requests
        print("✓ All core dependencies installed")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r ai_trading_system/requirements.txt")
        return False


def main_cli():
    """CLI 메인 함수"""
    parser = argparse.ArgumentParser(description='AI Trading System')
    parser.add_argument(
        '--mode',
        choices=['demo', 'real'],
        default=None,
        help='Trading mode (demo or real)'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check system configuration only'
    )
    
    args = parser.parse_args()
    
    # 모드가 지정되지 않으면 대화형으로 선택
    if not args.check and args.mode is None:
        print("\n🚀 AI 자동매매 시스템")
        print("=" * 40)
        print("거래 모드를 선택하세요:")
        print("")
        print("1️⃣  모의투자 (Demo)")
        print("   - 가상 머니로 안전한 테스트")
        print("   - 실제 돈을 잃을 위험 없음")
        print("   - 시스템 검증 및 학습용")
        print("")
        print("2️⃣  실전투자 (Real)")
        print("   ⚠️  실제 돈으로 거래합니다!")
        print("   - 실제 수익/손실 발생")
        print("   - 신중한 선택 필요")
        print("")
        
        while True:
            choice = input("선택하세요 (1 또는 2): ").strip()
            if choice == '1':
                args.mode = 'demo'
                print("✅ 모의투자 모드 선택됨")
                break
            elif choice == '2':
                args.mode = 'real'
                print("⚠️  실전투자 모드 선택됨")
                break
            else:
                print("❌ 1 또는 2를 입력하세요")
    
    print("=" * 60)
    print("AI TRADING SYSTEM")
    print("=" * 60)
    
    # 의존성 체크
    if not check_dependencies():
        sys.exit(1)
    
    # 환경 설정
    if args.mode:
        setup_environment(args.mode)
    
    # 설정 체크 모드
    if args.check:
        print("\nSystem Configuration:")
        print(f"- Mode: {args.mode}")
        print(f"- App Key: {'✓' if os.environ.get(f'KIS_{args.mode.upper()}_APPKEY') else '✗'}")
        print(f"- App Secret: {'✓' if os.environ.get(f'KIS_{args.mode.upper()}_APPSECRET') else '✗'}")
        print(f"- Account: {'✓' if os.environ.get(f'KIS_{args.mode.upper()}_ACCOUNT') else '✗'}")
        print("\nConfiguration check complete")
        return
    
    # 경고 메시지
    if args.mode == 'real':
        print("\n⚠️  WARNING: Running in REAL trading mode!")
        print("This will execute actual trades with real money.")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
    
    print(f"\nStarting AI Trading System in {args.mode} mode...")
    print("Press Ctrl+C to stop\n")
    
    try:
        # 메인 시스템 실행
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSystem stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main_cli()