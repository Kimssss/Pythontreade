#!/usr/bin/env python3
"""
AI 자동매매 시스템 메인 실행 파일
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path

# 프로젝트 루트 경로를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from ai_trading_system.src.core.trading_system import TradingSystem

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='AI 자동매매 시스템')
    parser.add_argument(
        '--mode',
        choices=['demo', 'real'],
        default='demo',
        help='거래 모드 (demo: 모의투자, real: 실전투자)'
    )
    parser.add_argument(
        '--config',
        default='ai_trading_system/config/kis_config.yaml',
        help='설정 파일 경로'
    )
    
    args = parser.parse_args()
    
    # 안전 확인
    if args.mode == 'real':
        print("⚠️  실전투자 모드입니다!")
        print("실제 돈으로 거래가 실행됩니다.")
        confirm = input("정말 실행하시겠습니까? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("실행을 취소합니다.")
            return
    
    # 모드 안내
    mode_name = "모의투자" if args.mode == 'demo' else "실전투자"
    print(f"""
╔══════════════════════════════════════════════════╗
║              AI 자동매매 시스템                    ║
╠══════════════════════════════════════════════════╣
║ 모드: {mode_name:^20}                     ║
║ 설정: {args.config:<30}           ║
╚══════════════════════════════════════════════════╝
    """)
    
    try:
        # 거래 시스템 초기화 및 실행
        paper_trading = (args.mode == 'demo')
        trading_system = TradingSystem(args.config, paper_trading)
        
        print("시스템을 시작합니다...")
        print("중지하려면 Ctrl+C를 눌러주세요.")
        print()
        
        # 비동기 실행
        asyncio.run(trading_system.run())
        
    except KeyboardInterrupt:
        print("\n\n✅ 사용자에 의해 시스템이 중지되었습니다.")
    except Exception as e:
        print(f"\n❌ 시스템 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()