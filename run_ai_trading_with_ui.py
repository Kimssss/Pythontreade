#!/usr/bin/env python3
"""
AI 자동매매 시스템 실행 스크립트 (UI 포함 버전)
"""
import os
import sys
import asyncio
import threading
import webbrowser
from pathlib import Path
from dotenv import load_dotenv
import logging

# 프로젝트 경로를 Python 경로에 추가
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# .env 파일 로드
load_dotenv()

# Import 시도
try:
    from ai_trading_system.main_trading_system import AITradingSystem
    from ai_trading_system.web_dashboard import app, socketio, set_trading_system, emit_update
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're in the correct directory and dependencies are installed")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 커스텀 로그 핸들러 추가 (UI로 로그 전송)
class UILogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        try:
            from ai_trading_system.web_dashboard import message_queue
            message_queue.put(log_entry)
        except:
            pass

ui_handler = UILogHandler()
ui_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger('ai_trading').addHandler(ui_handler)

# 전역 거래 시스템 인스턴스
trading_system = None

async def run_trading_system(mode='demo'):
    """거래 시스템 실행"""
    global trading_system
    
    # 시스템 초기화
    trading_system = AITradingSystem(mode=mode)
    set_trading_system(trading_system)
    
    # 원래 메서드들을 래핑하여 UI 업데이트 추가
    original_update_portfolio = trading_system.update_portfolio_status
    original_execute_trades = trading_system.execute_trades
    original_record_performance = trading_system.record_performance
    
    async def update_portfolio_with_ui():
        await original_update_portfolio()
        emit_update('portfolio_update', {
            'total_value': trading_system.total_value,
            'cash_balance': trading_system.cash_balance,
            'portfolio': trading_system.portfolio
        })
    
    async def execute_trades_with_ui(signals):
        result = await original_execute_trades(signals)
        if result:
            emit_update('trade_executed', {'trades': result})
        return result
    
    def record_performance_with_ui():
        original_record_performance()
        if trading_system.performance_history:
            emit_update('performance_update', {
                'performance': trading_system.performance_history[-1]
            })
    
    # 메서드 교체
    trading_system.update_portfolio_status = update_portfolio_with_ui
    trading_system.execute_trades = execute_trades_with_ui
    trading_system.record_performance = record_performance_with_ui
    
    # 거래 시스템 실행
    await trading_system.run()

def run_flask_server():
    """Flask 서버 실행"""
    socketio.run(app, host='127.0.0.1', port=5000, debug=False, use_reloader=False)

def main():
    """메인 실행 함수"""
    print("\n" + "="*60)
    print("🚀 AI TRADING SYSTEM WITH WEB UI")
    print("="*60)
    
    # 모드 선택
    print("\nSelect trading mode:")
    print("1. Demo (Simulated trading)")
    print("2. Real (Live trading)")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == '1':
        mode = 'demo'
        print("✅ Demo mode selected")
    elif choice == '2':
        mode = 'real'
        print("⚠️  Real mode selected - This will use real money!")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return
    else:
        print("Invalid choice")
        return
    
    # 환경 변수 설정
    os.environ['TRADING_MODE'] = mode
    
    print("\nStarting services...")
    
    # Flask 서버를 별도 스레드에서 실행
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()
    
    # 잠시 대기 후 브라우저 열기
    import time
    time.sleep(2)
    
    url = "http://127.0.0.1:5000"
    print(f"\n✅ Web UI available at: {url}")
    print("Opening browser...")
    
    try:
        webbrowser.open(url)
    except:
        print("Could not open browser automatically. Please open manually.")
    
    print("\nStarting trading system...")
    print("Press Ctrl+C to stop\n")
    
    try:
        # 거래 시스템 실행
        asyncio.run(run_trading_system(mode))
    except KeyboardInterrupt:
        print("\n\nSystem stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 필요한 패키지 확인
    try:
        import flask
        import flask_socketio
        import flask_cors
    except ImportError:
        print("Missing required packages. Installing...")
        os.system("pip install flask flask-socketio flask-cors")
        print("Please run the script again.")
        sys.exit(1)
    
    main()