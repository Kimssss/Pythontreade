#!/usr/bin/env python3
"""
AI 자동매매 시스템 실행 스크립트 (Import 문제 해결 버전)
"""
import os
import sys
import asyncio
import argparse
import logging
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
    parser.add_argument(
        '--no-ui',
        action='store_true',
        help='Run without web UI'
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
        print("3️⃣  백테스팅 (Backtest)")
        print("   📊 과거 데이터로 전략 검증")
        print("   - 가상 데이터로 성능 테스트")
        print("   - 리스크 없는 전략 평가")
        print("")
        
        while True:
            choice = input("선택하세요 (1, 2 또는 3): ").strip()
            if choice == '1':
                args.mode = 'demo'
                print("✅ 모의투자 모드 선택됨")
                break
            elif choice == '2':
                args.mode = 'real'
                print("⚠️  실전투자 모드 선택됨")
                break
            elif choice == '3':
                args.mode = 'backtest'
                print("📊 백테스팅 모드 선택됨")
                break
            else:
                print("❌ 1, 2 또는 3을 입력하세요")
        
        # 백테스팅이 아닌 경우만 UI 옵션 선택
        if args.mode != 'backtest':
            # UI 옵션 선택
            print("\n📊 UI 옵션을 선택하세요:")
            print("")
            print("1️⃣  웹 대시보드 포함 (추천)")
            print("   - 브라우저에서 실시간 모니터링")
            print("   - 차트와 거래 내역 확인")
            print("   - http://localhost:8080")
            print("")
            print("2️⃣  콘솔만 사용")
            print("   - 터미널에서만 로그 확인")
            print("   - 가벼운 실행")
            print("")
            
            while True:
                ui_choice = input("선택하세요 (1 또는 2): ").strip()
                if ui_choice == '1':
                    args.no_ui = False
                    print("✅ 웹 대시보드 활성화")
                    break
                elif ui_choice == '2':
                    args.no_ui = True
                    print("✅ 콘솔 모드 선택됨")
                    break
                else:
                    print("❌ 1 또는 2를 입력하세요")
        else:
            # 백테스팅은 콘솔만 사용
            args.no_ui = True
            print("✅ 백테스팅 모드는 콘솔로 실행됩니다")
    else:
        # 명령행 인자로 모드 지정시 기본값 설정
        if args.no_ui is None:
            args.no_ui = False  # 기본적으로 UI 활성화
    
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
    
    # 백테스팅 모드 처리
    if args.mode == 'backtest':
        print("\n📊 백테스팅 모드로 실행합니다...")
        print("과거 데이터를 사용한 전략 검증을 시작합니다.")
        run_backtest_mode()
        return
    
    # 실전 거래 경고 메시지
    if args.mode == 'real':
        print("\n⚠️  WARNING: Running in REAL trading mode!")
        print("This will execute actual trades with real money.")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
    
    # UI 포함 여부에 따라 다른 실행
    if not args.no_ui:
        # UI 포함 실행
        print("\nChecking UI dependencies...")
        try:
            import flask
            import flask_socketio
            import flask_cors
        except ImportError:
            print("Installing required UI packages...")
            os.system("pip install flask flask-socketio flask-cors")
            print("Please run the script again.")
            return
        
        print("\nStarting AI Trading System with Web UI...")
        print(f"Mode: {args.mode}")
        
        # UI 버전 실행
        run_with_ui(args.mode)
    else:
        # 기존 콘솔 버전 실행
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


def run_backtest_mode():
    """백테스팅 모드 실행"""
    print("\n📊 AI 트레이딩 백테스팅 설정")
    print("=" * 50)
    
    # 기본 설정값
    from datetime import datetime, timedelta
    default_end = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    default_start = default_end - timedelta(days=730)  # 2년 (365 * 2 = 730일)
    default_capital = 10000000  # 1천만원
    
    print(f"📅 기간: {default_start.strftime('%Y-%m-%d')} ~ {default_end.strftime('%Y-%m-%d')} (2년)")
    print(f"💰 초기자본: {default_capital:,}원")
    print(f"📈 대상: 국내+해외 주식")
    print("")
    
    # 사용자 확인
    while True:
        choice = input("기본 설정으로 시작하시겠습니까? (y/n): ").strip().lower()
        if choice in ['y', 'yes', '네', '']:
            # 기본값으로 실행
            start_date = default_start.strftime('%Y-%m-%d')
            end_date = default_end.strftime('%Y-%m-%d')
            capital = default_capital
            market = "both"
            break
        elif choice in ['n', 'no', '아니요']:
            # 사용자 정의 설정
            print("\n⚙️  사용자 정의 설정")
            
            # 기간 설정
            print("📅 백테스트 기간 설정:")
            start_input = input(f"시작일 (YYYY-MM-DD, 기본값: {default_start.strftime('%Y-%m-%d')}): ").strip()
            start_date = start_input if start_input else default_start.strftime('%Y-%m-%d')
            
            end_input = input(f"종료일 (YYYY-MM-DD, 기본값: {default_end.strftime('%Y-%m-%d')}): ").strip()
            end_date = end_input if end_input else default_end.strftime('%Y-%m-%d')
            
            # 자본 설정
            capital_input = input(f"초기자본 (원, 기본값: {default_capital:,}): ").strip()
            try:
                capital = int(capital_input.replace(',', '')) if capital_input else default_capital
            except:
                capital = default_capital
                
            # 시장 설정
            print("\n📈 백테스트 대상 선택:")
            print("1️⃣  국내만")
            print("2️⃣  해외만") 
            print("3️⃣  국내+해외 (추천)")
            
            market_choice = input("선택 (1-3, 기본값: 3): ").strip()
            if market_choice == '1':
                market = "domestic"
            elif market_choice == '2':
                market = "overseas"
            else:
                market = "both"
            break
        else:
            print("❌ y 또는 n을 입력하세요")
    
    print(f"\n🚀 백테스트 시작!")
    print(f"📅 기간: {start_date} ~ {end_date}")
    print(f"💰 자본: {capital:,}원")
    print(f"📈 대상: {market}")
    print("=" * 50)
    
    # 빠른 백테스트 실행
    print(f"\n⚡ 빠른 시뮬레이션 모드로 실행합니다...")
    print("(실제 API 호출 없이 시뮬레이션 데이터 사용)")
    
    try:
        from datetime import datetime
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # 빠른 백테스트 실행
        import subprocess
        result = subprocess.run(
            ["python", "fast_backtest.py", start_dt.strftime('%Y-%m-%d'), end_dt.strftime('%Y-%m-%d'), str(capital)],
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"❌ 오류 발생: {result.stderr}")
            
    except Exception as e:
        print(f"❌ 백테스트 실행 중 오류: {e}")
        print("\n수동 실행:")
        print("python fast_backtest.py")
    

def run_with_ui(mode):
    """UI와 함께 실행"""
    import threading
    import webbrowser
    import time
    
    # UI 모듈 임포트
    from ai_trading_system.web_dashboard import app, socketio, set_trading_system, emit_update
    from ai_trading_system.main_trading_system import AITradingSystem
    
    # 커스텀 로그 핸들러 추가
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
    
    # Flask 서버 실행 함수
    def run_flask():
        socketio.run(app, host='0.0.0.0', port=8080, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
    
    # 거래 시스템 실행 함수
    async def run_trading():
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
    
    # Flask 서버를 별도 스레드에서 실행
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # 잠시 대기 후 브라우저 열기
    time.sleep(2)
    
    # IP 주소 확인
    import socket
    
    def get_local_ip():
        try:
            # 외부 서버에 연결을 시도하여 로컬 IP 얻기
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"
    
    local_ip = get_local_ip()
    local_url = "http://127.0.0.1:8080"
    external_url = f"http://{local_ip}:8080"
    
    print(f"\n✅ Web UI available at:")
    print(f"   🏠 로컬 접속: {local_url}")
    if local_ip != "127.0.0.1":
        print(f"   🌐 외부 접속: {external_url}")
        print(f"   ℹ️  네트워크 상의 다른 기기에서 {external_url}로 접속 가능")
        print(f"   ⚠️  방화벽 설정을 확인하세요 (Port 8080)")
    print("Opening local browser...")
    
    try:
        webbrowser.open(local_url)
    except:
        print("Could not open browser automatically. Please open manually.")
    
    print("\nPress Ctrl+C to stop\n")
    
    try:
        # 거래 시스템 실행
        asyncio.run(run_trading())
    except KeyboardInterrupt:
        print("\n\nSystem stopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main_cli()