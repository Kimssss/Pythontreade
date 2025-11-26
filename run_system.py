#!/usr/bin/env python3
"""
AI 자동매매 시스템 실행 스크립트
- 간단한 실행을 위한 래퍼
- 오류 처리 및 로깅
"""

import sys
import os
from pathlib import Path

def main():
    """메인 실행 함수"""
    print("🤖 AI 자동매매 시스템 v2.1")
    print("=" * 60)
    print("🚀 기본 시스템")
    print("1. 기본 DQN 시스템 (ai_trading_system.py)")
    print("2. 고급 멀티 에이전트 시스템 (advanced_ai_system.py)")
    print()
    print("📊 대시보드")
    print("3. 모니터링 대시보드 (dashboard.py)")
    print("4. 간소 대시보드 (simple_dashboard.py) 🔥 추천")
    print()
    print("🔬 고급 기능 (NEW!)")
    print("6. Transformer 시계열 예측 (transformer_predictor.py)")
    print("7. 고빈도 거래 시스템 (high_frequency_trader.py)")
    print("8. 감성 분석 시스템 (sentiment_analyzer.py)")
    print()
    print("🔧 유틸리티")
    print("5. 패키지 설치 (auto_install.py)")
    print("-" * 60)
    
    choice = input("실행할 시스템을 선택하세요 (1-8): ").strip()
    
    try:
        if choice == "1":
            print("🚀 기본 DQN 시스템 실행...")
            import ai_trading_system
            ai_trading_system.main()
            
        elif choice == "2":
            print("🚀 고급 멀티 에이전트 시스템 실행...")
            import advanced_ai_system
            advanced_ai_system.main()
            
        elif choice == "3":
            print("🚀 모니터링 대시보드 실행...")
            os.system("streamlit run dashboard.py")
            
        elif choice == "4":
            print("🚀 간소 대시보드 실행 (토큰 캐싱 적용)...")
            os.system("streamlit run simple_dashboard.py")
            
        elif choice == "5":
            print("🔧 패키지 설치 실행...")
            import auto_install
            auto_install.main()
            
        elif choice == "6":
            print("🧠 Transformer 시계열 예측 시스템 실행...")
            import transformer_predictor
            transformer_predictor.main()
            
        elif choice == "7":
            print("⚡ 고빈도 거래 시스템 실행...")
            import high_frequency_trader
            high_frequency_trader.main()
            
        elif choice == "8":
            print("📰 감성 분석 시스템 실행...")
            import sentiment_analyzer
            sentiment_analyzer.main()
            
        else:
            print("❌ 올바른 선택지를 입력하세요.")
            return
    
    except ImportError as e:
        print(f"❌ 모듈 임포트 오류: {e}")
        print("필요한 패키지를 먼저 설치해주세요: python auto_install.py")
    except Exception as e:
        print(f"❌ 실행 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()