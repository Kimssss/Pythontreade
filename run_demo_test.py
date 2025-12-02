#!/usr/bin/env python3
"""
AI 자동매매 시스템 데모 테스트 실행
"""
import os
import sys
import asyncio

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_trading_system.main_trading_system_demo import main

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 AI TRADING SYSTEM - DEMO MODE")
    print("="*60)
    print("This is a simulation mode for testing")
    print("No real money or API calls involved")
    print("\nPress Ctrl+C to stop")
    print("="*60 + "\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nDemo stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()