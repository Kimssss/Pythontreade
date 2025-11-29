#!/usr/bin/env python3
"""
AI 자동매매 시스템 실행 스크립트
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 경로 설정
sys.path.insert(0, str(Path(__file__).parent))

# .env 파일 로드
load_dotenv()

from main_trading_system import main


def setup_environment(mode: str):
    """환경 설정"""
    # 로그 디렉토리 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 모델 디렉토리 생성
    model_dir = Path("models")
    model_dir.mkdir(exist_ok=True)
    
    # 캐시 디렉토리 생성
    cache_dir = Path("cache")
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
        print("Please run: pip install -r requirements.txt")
        return False


def main_cli():
    """CLI 메인 함수"""
    parser = argparse.ArgumentParser(description='AI Trading System')
    parser.add_argument(
        '--mode',
        choices=['demo', 'real'],
        default='demo',
        help='Trading mode (demo or real)'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check system configuration only'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AI TRADING SYSTEM")
    print("=" * 60)
    
    # 의존성 체크
    if not check_dependencies():
        sys.exit(1)
    
    # 환경 설정
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
        sys.exit(1)


if __name__ == "__main__":
    main_cli()