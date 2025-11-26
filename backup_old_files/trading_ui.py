import os
import sys
import subprocess
import time
from datetime import datetime
from kis_api import KisAPI
from config import Config
from auto_trader import AutoTrader, AutoTraderManager

# 필요한 패키지 자동 설치
def install_requirements():
    """필요한 패키지 자동 설치"""
    try:
        import requests
        import dotenv
        print("✅ 모든 필요한 패키지가 설치되어 있습니다.")
    except ImportError as e:
        print(f"🔄 필요한 패키지를 설치합니다: {e.name}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ 패키지 설치 완료!")

class TradingUI:
    def __init__(self):
        self.api = None
        self.current_mode = None
        self.auto_trader_manager = None
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        print("=" * 60)
        print("🏦 한국투자증권 자동매매 시스템")
        print("=" * 60)
        if self.current_mode:
            mode_text = "🔴 실전투자" if self.current_mode == 'real' else "🟡 모의투자"
            print(f"현재 모드: {mode_text}")
            print("-" * 60)
    
    def show_mode_selection(self):
        self.clear_screen()
        self.print_header()
        print("\n📊 투자 모드를 선택해주세요:")
        print()
        print("1. 🟡 모의투자 모드")
        print("   - 가상 자금으로 안전하게 테스트")
        print("   - 실제 손실 위험 없음")
        print("   - 전략 검증 및 학습용")
        print()
        print("2. 🔴 실전투자 모드")
        print("   - 실제 자금으로 거래")
        print("   - ⚠️  실제 손실 위험 있음")
        print("   - 충분한 검증 후 사용 권장")
        print()
        print("0. ❌ 종료")
        print()
    
    def select_mode(self):
        while True:
            self.show_mode_selection()
            choice = input("선택하세요 (0-2): ").strip()
            
            if choice == '0':
                print("\n👋 프로그램을 종료합니다.")
                sys.exit()
            elif choice == '1':
                self.current_mode = 'demo'
                self.setup_api('demo')
                break
            elif choice == '2':
                print("\n⚠️  실전투자 모드를 선택하셨습니다.")
                confirm = input("실제 자금 손실 위험이 있습니다. 계속하시겠습니까? (y/N): ").strip().lower()
                if confirm == 'y':
                    self.current_mode = 'real'
                    self.setup_api('real')
                    break
                else:
                    print("모의투자 모드로 전환합니다.")
                    self.current_mode = 'demo'
                    self.setup_api('demo')
                    break
            else:
                print("❌ 잘못된 선택입니다. 다시 선택해주세요.")
                input("엔터를 눌러 계속...")
    
    def setup_api(self, mode):
        try:
            account_info = Config.get_account_info(mode)
            is_real = (mode == 'real')
            
            self.api = KisAPI(
                account_info['appkey'],
                account_info['appsecret'], 
                account_info['account'],
                is_real=is_real
            )
        except ValueError as e:
            print(f"❌ 설정 오류: {e}")
            print("📝 .env 파일을 확인하고 필요한 API 키를 설정해주세요.")
            input("엔터를 눌러 종료...")
            sys.exit(1)
        
        print(f"\n🔄 {('실전투자' if is_real else '모의투자')} API 연결 중...")
        if self.api.get_access_token():
            print("✅ API 연결 성공!")
            print("💡 팁: 모든 기능이 준비되었습니다!")
            input("\n엔터를 눌러 메인 메뉴로...")
        else:
            print("❌ API 연결 실패!")
            print("🔍 문제 해결 방법:")
            print("   1. 인터넷 연결 상태 확인")
            print("   2. .env 파일의 API 키 정보 확인")
            print("   3. 한국투자증권 API 서비스 상태 확인")
            print("   4. 계정의 API 사용 권한 확인")
            
            choice = input("\n다시 시도하시겠습니까? (y/N): ").strip().lower()
            if choice == 'y':
                self.setup_api(self.current_mode)
            else:
                print("모드 선택으로 돌아갑니다.")
                self.select_mode()
    
    def show_main_menu(self):
        self.clear_screen()
        self.print_header()

        # 자동매매 상태 표시
        if self.auto_trader_manager and self.auto_trader_manager.trader:
            status = self.auto_trader_manager.get_status()
            if status.get('is_running'):
                if status.get('is_paused'):
                    print("🟡 자동매매: 일시정지")
                else:
                    print("🟢 자동매매: 실행 중")
            else:
                print("⚪ 자동매매: 중지됨")
            print("-" * 60)

        print("\n📋 메인 메뉴:")
        print()
        print("1. 💰 계좌 정보 조회")
        print("2. 📈 주식 현재가 조회")
        print("3. 🛒 주식 매수")
        print("4. 🛍️  주식 매도")
        print("5. 📊 주문 내역 조회")
        print("6. 🔄 모드 변경")
        print()
        print("━" * 40)
        print("🤖 자동매매")
        print("━" * 40)
        print("7. 🚀 자동매매 시작/중지")
        print("8. ⚙️  자동매매 설정")
        print("9. 📜 자동매매 상태/로그")
        print()
        print("0. ❌ 종료")
        print()
    
    def get_balance_info(self):
        print("\n🔄 계좌 정보를 조회합니다...")
        balance = self.api.get_balance()
        
        if balance and balance.get('rt_cd') == '0':
            output2 = balance.get('output2', [{}])[0]
            print("\n✅ 계좌 정보:")
            tot_amt = output2.get('tot_evlu_amt', 'N/A')
            ord_cash = output2.get('ord_psbl_cash', 'N/A')
            evlu_pf = output2.get('evlu_pfls_smtl_amt', 'N/A')
            
            if tot_amt != 'N/A':
                print(f"   💵 총 평가 금액: {int(tot_amt):,}원")
            else:
                print(f"   💵 총 평가 금액: {tot_amt}원")
                
            print(f"   💳 주문 가능 현금: {ord_cash}원")
            print(f"   📈 총 평가 손익: {evlu_pf}원")
        else:
            print("❌ 계좌 정보 조회 실패")
    
    def get_stock_price_info(self):
        stock_code = input("\n📈 주식 종목코드를 입력하세요 (예: 005930): ").strip()
        if not stock_code:
            print("❌ 종목코드가 입력되지 않았습니다.")
            return
        
        print(f"\n🔄 {stock_code} 현재가를 조회합니다...")
        price = self.api.get_stock_price(stock_code)
        
        if price and price.get('rt_cd') == '0':
            output = price.get('output', {})
            print(f"\n✅ {stock_code} 현재가 정보:")
            price = output.get('stck_prpr', 'N/A')
            rate = output.get('prdy_ctrt', 'N/A')
            vol = output.get('acml_vol', 'N/A')
            
            if price != 'N/A':
                print(f"   💰 현재가: {int(price):,}원")
            else:
                print(f"   💰 현재가: {price}원")
                
            print(f"   📊 등락율: {rate}%")
            
            if vol != 'N/A':
                print(f"   📈 거래량: {int(vol):,}")
            else:
                print(f"   📈 거래량: {vol}")
        else:
            print("❌ 현재가 조회 실패")
    
    def buy_stock_menu(self):
        print(f"\n🛒 주식 매수 - {('실전투자' if self.current_mode == 'real' else '모의투자')} 모드")
        
        if self.current_mode == 'real':
            print("⚠️  실제 자금으로 매수 주문을 실행합니다!")
            confirm = input("정말 진행하시겠습니까? (y/N): ").strip().lower()
            if confirm != 'y':
                print("매수 주문을 취소했습니다.")
                return
        
        stock_code = input("종목코드: ").strip()
        if not stock_code:
            print("❌ 종목코드가 입력되지 않았습니다.")
            return
            
        try:
            quantity = int(input("수량: "))
            order_type = input("주문구분 (1:지정가, 3:시장가) [기본값:3]: ").strip() or "03"
            
            if order_type == "1" or order_type == "01":
                price = int(input("주문가격: "))
                order_type = "01"
            else:
                price = 0
                order_type = "03"
            
            print(f"\n🔄 매수 주문을 실행합니다...")
            result = self.api.buy_stock(stock_code, quantity, price, order_type)
            
            if result and result.get('rt_cd') == '0':
                print("✅ 매수 주문 성공!")
                output = result.get('output', {})
                print(f"   📋 주문번호: {output.get('ODNO', 'N/A')}")
            else:
                print("❌ 매수 주문 실패:", result.get('msg1', 'Unknown error'))
                
        except ValueError:
            print("❌ 잘못된 입력입니다.")
    
    def sell_stock_menu(self):
        print(f"\n🛍️  주식 매도 - {('실전투자' if self.current_mode == 'real' else '모의투자')} 모드")
        
        if self.current_mode == 'real':
            print("⚠️  실제 자금으로 매도 주문을 실행합니다!")
            confirm = input("정말 진행하시겠습니까? (y/N): ").strip().lower()
            if confirm != 'y':
                print("매도 주문을 취소했습니다.")
                return
        
        stock_code = input("종목코드: ").strip()
        if not stock_code:
            print("❌ 종목코드가 입력되지 않았습니다.")
            return
            
        try:
            quantity = int(input("수량: "))
            order_type = input("주문구분 (1:지정가, 3:시장가) [기본값:3]: ").strip() or "03"
            
            if order_type == "1" or order_type == "01":
                price = int(input("주문가격: "))
                order_type = "01"
            else:
                price = 0
                order_type = "03"
            
            print(f"\n🔄 매도 주문을 실행합니다...")
            result = self.api.sell_stock(stock_code, quantity, price, order_type)
            
            if result and result.get('rt_cd') == '0':
                print("✅ 매도 주문 성공!")
                output = result.get('output', {})
                print(f"   📋 주문번호: {output.get('ODNO', 'N/A')}")
            else:
                print("❌ 매도 주문 실패:", result.get('msg1', 'Unknown error'))
                
        except ValueError:
            print("❌ 잘못된 입력입니다.")
    
    def get_orders_info(self):
        print("\n🔄 주문 내역을 조회합니다...")
        orders = self.api.get_orders()

        if orders and orders.get('rt_cd') == '0':
            order_list = orders.get('output', [])
            print(f"\n✅ 주문 내역 ({len(order_list)}건):")

            if order_list:
                for i, order in enumerate(order_list[:5], 1):
                    print(f"   {i}. {order.get('pdno', 'N/A')} | "
                          f"{order.get('ord_qty', 'N/A')}주 | "
                          f"{order.get('ord_unpr', 'N/A')}원")
            else:
                print("   주문 내역이 없습니다.")
        else:
            print("❌ 주문 내역 조회 실패")

    def auto_trade_menu(self):
        """자동매매 시작/중지 메뉴"""
        self.clear_screen()
        print("=" * 60)
        print("🤖 자동매매 시작/중지")
        print("=" * 60)

        # 자동매매 관리자 초기화
        if not self.auto_trader_manager:
            self.auto_trader_manager = AutoTraderManager(self.api)

        status = self.auto_trader_manager.get_status()

        if status.get('is_running'):
            print(f"\n현재 상태: {'일시정지' if status.get('is_paused') else '실행 중'}")
            print()
            print("1. ⏸️  일시정지" if not status.get('is_paused') else "1. ▶️  재개")
            print("2. ⏹️  완전 중지")
            print("3. 🔄 1회 즉시 실행")
            print("0. 뒤로가기")
            print()

            choice = input("선택: ").strip()

            if choice == '1':
                if status.get('is_paused'):
                    self.auto_trader_manager.trader.resume()
                    print("✅ 자동매매가 재개되었습니다.")
                else:
                    self.auto_trader_manager.trader.pause()
                    print("✅ 자동매매가 일시정지되었습니다.")
            elif choice == '2':
                self.auto_trader_manager.stop_trading()
                print("✅ 자동매매가 중지되었습니다.")
            elif choice == '3':
                print("\n🔄 전략을 즉시 실행합니다...")
                result = self.auto_trader_manager.trader.run_once_now()
                print(f"\n매수: {len(result.get('buys', []))}건")
                print(f"매도: {len(result.get('sells', []))}건")
                print(f"오류: {len(result.get('errors', []))}건")
        else:
            print("\n현재 상태: 중지됨")
            print()

            if self.current_mode == 'real':
                print("⚠️  경고: 실전투자 모드입니다!")
                print("   실제 자금으로 자동 매매가 실행됩니다.")
                print()

            print("1. ▶️  자동매매 시작")
            print("2. 🔄 1회만 실행 (테스트)")
            print("0. 뒤로가기")
            print()

            choice = input("선택: ").strip()

            if choice == '1':
                if self.current_mode == 'real':
                    confirm = input("실전투자 모드로 자동매매를 시작합니다. 계속하시겠습니까? (y/N): ").strip().lower()
                    if confirm != 'y':
                        print("취소되었습니다.")
                        return

                interval = input("체크 간격 (초, 기본 60): ").strip()
                interval = int(interval) if interval.isdigit() else 60

                self.auto_trader_manager.start_trading(interval)
                print(f"✅ 자동매매가 시작되었습니다! (체크 간격: {interval}초)")
                print("💡 백그라운드에서 실행됩니다. 메인 메뉴에서 상태를 확인하세요.")

            elif choice == '2':
                print("\n🔄 전략을 1회 실행합니다...")
                if not self.auto_trader_manager.trader:
                    self.auto_trader_manager.create_trader()
                result = self.auto_trader_manager.trader.run_once_now()
                print(f"\n결과:")
                print(f"   매수: {len(result.get('buys', []))}건")
                print(f"   매도: {len(result.get('sells', []))}건")
                print(f"   오류: {len(result.get('errors', []))}건")

    def auto_trade_settings(self):
        """자동매매 설정 메뉴"""
        self.clear_screen()
        print("=" * 60)
        print("⚙️  자동매매 설정")
        print("=" * 60)

        if not self.auto_trader_manager:
            self.auto_trader_manager = AutoTraderManager(self.api)
        if not self.auto_trader_manager.trader:
            self.auto_trader_manager.create_trader()

        config = self.auto_trader_manager.trader.get_config()

        print("\n📋 현재 설정:")
        print()
        print("[ 종목 선택 조건 ]")
        print(f"   최소 주가: {config['min_price']:,}원")
        print(f"   최대 주가: {config['max_price']:,}원")
        print(f"   최소 거래량 비율: {config['min_volume_ratio']}배")
        print(f"   등락률 범위: +{config['min_change_rate']}% ~ +{config['max_change_rate']}%")
        print()
        print("[ 매수 조건 ]")
        print(f"   RSI 범위: {config['buy_rsi_min']} ~ {config['buy_rsi_max']}")
        print()
        print("[ 매도 조건 ]")
        print(f"   익절: +{config['take_profit']}%")
        print(f"   손절: {config['stop_loss']}%")
        print(f"   최대 보유 기간: {config['max_hold_days']}일")
        print()
        print("[ 자금 관리 ]")
        print(f"   최대 보유 종목: {config['max_stocks']}개")
        print(f"   종목당 투자 비율: {config['position_ratio'] * 100}%")
        print(f"   일일 최대 매수: {config['max_buy_per_day']}회")
        print()
        print("-" * 60)
        print()
        print("1. 익절/손절 설정 변경")
        print("2. 최대 보유 종목 수 변경")
        print("3. 종목당 투자 비율 변경")
        print("4. 거래량 비율 변경")
        print("5. 기본값으로 초기화")
        print("0. 뒤로가기")
        print()

        choice = input("선택: ").strip()

        if choice == '1':
            try:
                take_profit = input(f"익절 % (현재 {config['take_profit']}): ").strip()
                stop_loss = input(f"손절 % (현재 {config['stop_loss']}): ").strip()

                updates = {}
                if take_profit:
                    updates['take_profit'] = float(take_profit)
                if stop_loss:
                    updates['stop_loss'] = float(stop_loss)

                if updates:
                    self.auto_trader_manager.trader.update_config(updates)
                    print("✅ 설정이 변경되었습니다.")
            except ValueError:
                print("❌ 잘못된 입력입니다.")

        elif choice == '2':
            try:
                max_stocks = input(f"최대 보유 종목 수 (현재 {config['max_stocks']}): ").strip()
                if max_stocks:
                    self.auto_trader_manager.trader.update_config({'max_stocks': int(max_stocks)})
                    print("✅ 설정이 변경되었습니다.")
            except ValueError:
                print("❌ 잘못된 입력입니다.")

        elif choice == '3':
            try:
                ratio = input(f"종목당 투자 비율 % (현재 {config['position_ratio'] * 100}): ").strip()
                if ratio:
                    self.auto_trader_manager.trader.update_config({'position_ratio': float(ratio) / 100})
                    print("✅ 설정이 변경되었습니다.")
            except ValueError:
                print("❌ 잘못된 입력입니다.")

        elif choice == '4':
            try:
                ratio = input(f"최소 거래량 비율 (현재 {config['min_volume_ratio']}배): ").strip()
                if ratio:
                    self.auto_trader_manager.trader.update_config({'min_volume_ratio': float(ratio)})
                    print("✅ 설정이 변경되었습니다.")
            except ValueError:
                print("❌ 잘못된 입력입니다.")

        elif choice == '5':
            self.auto_trader_manager.create_trader()
            print("✅ 기본값으로 초기화되었습니다.")

    def auto_trade_status(self):
        """자동매매 상태/로그 메뉴"""
        self.clear_screen()
        print("=" * 60)
        print("📜 자동매매 상태 및 로그")
        print("=" * 60)

        if not self.auto_trader_manager:
            print("\n자동매매가 초기화되지 않았습니다.")
            return

        status = self.auto_trader_manager.get_status()

        # 실행 상태
        print("\n[ 실행 상태 ]")
        if status.get('is_running'):
            state = "일시정지" if status.get('is_paused') else "실행 중"
            print(f"   상태: 🟢 {state}")
        else:
            print("   상태: ⚪ 중지됨")

        print(f"   장 상태: {'개장' if status.get('is_market_open') else '폐장'}")
        print(f"   체크 간격: {status.get('check_interval', 60)}초")

        # 전략 상태
        strategy_status = status.get('strategy_status', {})
        if strategy_status:
            print("\n[ 포트폴리오 ]")
            print(f"   보유 종목: {strategy_status.get('holdings_count', 0)}개")
            print(f"   가용 현금: {strategy_status.get('available_cash', 0):,}원")
            print(f"   오늘 매수: {strategy_status.get('daily_buy_count', 0)}회")

            holdings = strategy_status.get('holdings', [])
            if holdings:
                print("\n[ 보유 종목 ]")
                for h in holdings:
                    profit_emoji = "📈" if h['profit_rate'] >= 0 else "📉"
                    print(f"   {profit_emoji} {h['stock_name']} ({h['stock_code']})")
                    print(f"      {h['quantity']}주 | 평균가: {h['buy_price']:,.0f}원 | "
                          f"현재가: {h['current_price']:,.0f}원 | {h['profit_rate']:+.2f}%")

        # 최근 거래
        trade_history = strategy_status.get('trade_history', [])
        if trade_history:
            print("\n[ 최근 거래 ]")
            for trade in trade_history[-5:]:
                emoji = "🛒" if trade['type'] == 'BUY' else "🛍️"
                print(f"   {emoji} {trade['type']} | {trade.get('name', trade['code'])} | "
                      f"{trade['quantity']}주 | {trade['timestamp'][:16]}")

        # 최근 로그
        logs = status.get('recent_logs', [])
        if logs:
            print("\n[ 최근 로그 ]")
            for log in logs[-10:]:
                print(f"   {log}")

        print()
        print("-" * 60)
        print("1. 🔄 새로고침")
        print("2. 📊 전체 거래 내역")
        print("0. 뒤로가기")

        choice = input("\n선택: ").strip()

        if choice == '1':
            self.auto_trade_status()
        elif choice == '2':
            self.show_trade_history()

    def show_trade_history(self):
        """전체 거래 내역 표시"""
        self.clear_screen()
        print("=" * 60)
        print("📊 전체 거래 내역")
        print("=" * 60)

        if not self.auto_trader_manager or not self.auto_trader_manager.trader:
            print("\n거래 내역이 없습니다.")
            input("\n엔터를 눌러 계속...")
            return

        history = self.auto_trader_manager.trader.get_trade_history()

        if not history:
            print("\n거래 내역이 없습니다.")
        else:
            print(f"\n총 {len(history)}건의 거래\n")

            # 통계
            buys = [t for t in history if t['type'] == 'BUY']
            sells = [t for t in history if t['type'] == 'SELL']

            print(f"매수: {len(buys)}건 | 매도: {len(sells)}건")
            print("-" * 60)

            for i, trade in enumerate(reversed(history[-20:]), 1):
                emoji = "🛒" if trade['type'] == 'BUY' else "🛍️"
                print(f"{i}. {emoji} {trade['type']:4} | {trade.get('name', trade['code']):10} | "
                      f"{trade['quantity']:5}주 | {trade['timestamp'][:16]}")

                if trade['type'] == 'SELL':
                    print(f"       수익률: {trade.get('profit_rate', 0):+.2f}% | "
                          f"사유: {trade.get('reason', 'N/A')}")

        input("\n엔터를 눌러 계속...")

    def run(self):
        try:
            # 패키지 설치 확인
            install_requirements()
            
            self.select_mode()
            
            while True:
                self.show_main_menu()
                choice = input("메뉴를 선택하세요 (0-9): ").strip()

                if choice == '0':
                    # 자동매매 중지 후 종료
                    if self.auto_trader_manager:
                        self.auto_trader_manager.stop_trading()
                    print("\n👋 프로그램을 종료합니다.")
                    break
                elif choice == '1':
                    self.get_balance_info()
                elif choice == '2':
                    self.get_stock_price_info()
                elif choice == '3':
                    self.buy_stock_menu()
                elif choice == '4':
                    self.sell_stock_menu()
                elif choice == '5':
                    self.get_orders_info()
                elif choice == '6':
                    self.select_mode()
                    continue
                elif choice == '7':
                    self.auto_trade_menu()
                elif choice == '8':
                    self.auto_trade_settings()
                elif choice == '9':
                    self.auto_trade_status()
                else:
                    print("❌ 잘못된 선택입니다.")

                input("\n엔터를 눌러 계속...")
                
        except KeyboardInterrupt:
            print("\n\n👋 프로그램을 종료합니다.")
        except Exception as e:
            print(f"\n❌ 오류 발생: {e}")

if __name__ == "__main__":
    ui = TradingUI()
    ui.run()