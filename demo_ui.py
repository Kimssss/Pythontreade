from trading_ui import TradingUI

def demo_ui():
    """UI 데모 실행"""
    print("=== 한국투자증권 자동매매 UI 데모 ===\n")
    
    print("사용 가능한 모드:")
    print("1. 🟡 모의투자 모드")
    print("   - 가상 자금으로 안전한 테스트")
    print("   - 실제 손실 위험 없음")
    print("   - 전략 검증 및 학습용")
    print()
    print("2. 🔴 실전투자 모드") 
    print("   - 실제 자금으로 거래")
    print("   - ⚠️  실제 손실 위험 있음")
    print("   - 충분한 검증 후 사용 권장")
    print()
    
    print("메인 메뉴 기능:")
    print("• 💰 계좌 정보 조회")
    print("• 📈 주식 현재가 조회") 
    print("• 🛒 주식 매수")
    print("• 🛍️  주식 매도")
    print("• 📊 주문 내역 조회")
    print("• 🔄 모드 변경")
    print()
    
    print("실행 방법:")
    print("python3 trading_ui.py")
    print()
    
    print("UI 특징:")
    print("✅ 직관적인 이모지 메뉴")
    print("✅ 실전/모의투자 모드 구분")
    print("✅ 안전장치 (실전투자 시 재확인)")
    print("✅ 깔끔한 화면 정리")
    print("✅ 오류 처리 및 사용자 안내")

if __name__ == "__main__":
    demo_ui()