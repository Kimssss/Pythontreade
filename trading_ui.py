import os
import sys
import subprocess
import time
from datetime import datetime
from kis_api import KisAPI
from us_stock_api import USStockAPI
from config import Config
from strategy import TradingStrategy, TechnicalAnalysis
from screener import StockScreener

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
        self.us_api = None
        self.current_mode = None
        self.screener = None
        self.strategy = None
        self.auto_trading_enabled = False
        self.portfolio = {}  # {종목코드: {수량, 평균매수가, ...}}

        # 자동매매 설정 (기본값: 1000만원, 중립)
        self.auto_config = {
            'total_capital': 10000000,
            'style': 'neutral',
            'stop_loss': -0.05,
            'take_profit': 0.10,
            'max_positions': 5,
            'position_size': 0.10
        }
    
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
            
            # 미국주식 API도 함께 초기화
            self.us_api = USStockAPI(
                account_info['appkey'],
                account_info['appsecret'],
                account_info['account'],
                is_real=is_real
            )

            # 자동매매용 전략 및 스크리너 초기화
            self.strategy = TradingStrategy(style=self.auto_config['style'])
            self.screener = StockScreener(self.api, style=self.auto_config['style'])
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
        print("\n📋 메인 메뉴:")
        print()
        print("🇰🇷 국내주식:")
        print("1. 💰 계좌 정보 조회")
        print("2. 📈 주식 현재가 조회")
        print("3. 🛒 주식 매수")
        print("4. 🛍️  주식 매도")
        print("5. 📊 주문 내역 조회")
        print()
        print("🇺🇸 미국주식:")
        print("6. 🍎 미국주식 현재가 조회")
        print("7. 🛒 미국주식 매수")
        print("8. 🛍️  미국주식 매도")
        print("9. 💼 미국주식 잔고 조회")
        print()
        print("🤖 자동매매:")
        auto_status = "🟢 실행중" if self.auto_trading_enabled else "🔴 중지"
        print(f"10. 📊 자동매매 메뉴 [{auto_status}]")
        print()
        print("⚙️  시스템:")
        print("88. 🔄 모드 변경")
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
    
    def get_us_stock_price_info(self):
        """미국주식 현재가 조회"""
        symbol = input("\n🍎 미국주식 심볼을 입력하세요 (예: AAPL, TSLA): ").strip().upper()
        if not symbol:
            print("❌ 심볼이 입력되지 않았습니다.")
            return
        
        # 한글 검색 지원
        if symbol in ["애플", "APPLE"]:
            symbol = "AAPL"
        elif symbol in ["테슬라", "TESLA"]:
            symbol = "TSLA"
        elif symbol in ["구글", "GOOGLE"]:
            symbol = "GOOGL"
        elif symbol in ["아마존", "AMAZON"]:
            symbol = "AMZN"
        elif symbol in ["마이크로소프트", "MICROSOFT"]:
            symbol = "MSFT"
        
        print(f"\n🔄 {symbol} 현재가를 조회합니다...")
        price = self.us_api.get_us_stock_price(symbol)
        
        if price and price.get('rt_cd') == '0':
            output = price.get('output', {})
            print(f"\n✅ {symbol} 현재가 정보:")
            
            last_price = output.get('last', 'N/A')
            diff = output.get('diff', 'N/A')
            rate = output.get('rate', 'N/A')
            tvol = output.get('tvol', 'N/A')
            open_price = output.get('open', 'N/A')
            high = output.get('high', 'N/A')
            low = output.get('low', 'N/A')
            
            print(f"   💰 현재가: ${last_price}")
            print(f"   📊 전일대비: ${diff} ({rate}%)")
            print(f"   📈 거래량: {tvol}")
            print(f"   🌅 시가: ${open_price}")
            print(f"   ⬆️  고가: ${high}")
            print(f"   ⬇️  저가: ${low}")
        else:
            print("❌ 현재가 조회 실패")
            if price:
                print(f"   오류: {price.get('msg1', 'Unknown error')}")
    
    def buy_us_stock_menu(self):
        """미국주식 매수 메뉴"""
        print(f"\n🛒 미국주식 매수 - {('실전투자' if self.current_mode == 'real' else '모의투자')} 모드")
        
        if self.current_mode == 'real':
            print("⚠️  실제 자금으로 미국주식 매수 주문을 실행합니다!")
            confirm = input("정말 진행하시겠습니까? (y/N): ").strip().lower()
            if confirm != 'y':
                print("매수 주문을 취소했습니다.")
                return
        
        symbol = input("심볼 (예: AAPL): ").strip().upper()
        if not symbol:
            print("❌ 심볼이 입력되지 않았습니다.")
            return
        
        # 인기주식 자동완성
        symbol = self.us_api.search_us_stock(symbol)
        
        try:
            quantity = int(input("수량: "))
            order_type = input("주문구분 (00:지정가, 32:시장가) [기본값:32]: ").strip() or "32"
            
            if order_type == "00":
                price = float(input("주문가격($): "))
            else:
                price = 0
                order_type = "32"
            
            print(f"\n🔄 {symbol} {quantity}주 매수 주문을 실행합니다...")
            result = self.us_api.buy_us_stock(symbol, quantity, price, order_type)
            
            if result and result.get('rt_cd') == '0':
                print("✅ 미국주식 매수 주문 성공!")
                output = result.get('output', {})
                print(f"   📋 주문번호: {output.get('ODNO', 'N/A')}")
            else:
                print("❌ 미국주식 매수 주문 실패")
                if result:
                    print(f"   오류: {result.get('msg1', 'Unknown error')}")
                
        except ValueError:
            print("❌ 잘못된 입력입니다.")
    
    def sell_us_stock_menu(self):
        """미국주식 매도 메뉴"""
        print(f"\n🛍️  미국주식 매도 - {('실전투자' if self.current_mode == 'real' else '모의투자')} 모드")
        
        if self.current_mode == 'real':
            print("⚠️  실제 자금으로 미국주식 매도 주문을 실행합니다!")
            confirm = input("정말 진행하시겠습니까? (y/N): ").strip().lower()
            if confirm != 'y':
                print("매도 주문을 취소했습니다.")
                return
        
        symbol = input("심볼 (예: AAPL): ").strip().upper()
        if not symbol:
            print("❌ 심볼이 입력되지 않았습니다.")
            return
        
        # 인기주식 자동완성
        symbol = self.us_api.search_us_stock(symbol)
        
        try:
            quantity = int(input("수량: "))
            order_type = input("주문구분 (00:지정가, 32:시장가) [기본값:32]: ").strip() or "32"
            
            if order_type == "00":
                price = float(input("주문가격($): "))
            else:
                price = 0
                order_type = "32"
            
            print(f"\n🔄 {symbol} {quantity}주 매도 주문을 실행합니다...")
            result = self.us_api.sell_us_stock(symbol, quantity, price, order_type)
            
            if result and result.get('rt_cd') == '0':
                print("✅ 미국주식 매도 주문 성공!")
                output = result.get('output', {})
                print(f"   📋 주문번호: {output.get('ODNO', 'N/A')}")
            else:
                print("❌ 미국주식 매도 주문 실패")
                if result:
                    print(f"   오류: {result.get('msg1', 'Unknown error')}")
                
        except ValueError:
            print("❌ 잘못된 입력입니다.")
    
    def get_us_balance_info(self):
        """미국주식 잔고 조회"""
        print("\n🔄 미국주식 계좌 정보를 조회합니다...")
        balance = self.us_api.get_us_stock_balance()
        
        if balance and balance.get('rt_cd') == '0':
            print("\n✅ 미국주식 계좌 정보:")
            output2 = balance.get('output2', [{}])
            if output2:
                summary = output2[0]
                total_amt = summary.get('frcr_evlu_tota', 'N/A')
                print(f"   💵 총 평가금액: ${total_amt}")
                
            # 보유 종목 목록
            output1 = balance.get('output1', [])
            if output1:
                print(f"\n📊 보유 종목 ({len(output1)}개):")
                for stock in output1[:5]:  # 최대 5개만 표시
                    symbol = stock.get('ovrs_pdno', 'N/A')
                    qty = stock.get('ovrs_cblc_qty', 'N/A')
                    price = stock.get('now_pric2', 'N/A')
                    print(f"   • {symbol}: {qty}주 @ ${price}")
            else:
                print("   보유 종목이 없습니다.")
        else:
            print("❌ 미국주식 계좌 정보 조회 실패")
            if balance:
                print(f"   오류: {balance.get('msg1', 'Unknown error')}")

    # ==================== 자동매매 메뉴 ====================

    def show_auto_trading_menu(self):
        """자동매매 서브메뉴"""
        while True:
            self.clear_screen()
            print("=" * 60)
            print("🤖 자동매매 시스템 - 이동평균선 크로스 전략")
            print("=" * 60)
            auto_status = "🟢 실행중" if self.auto_trading_enabled else "🔴 중지"
            print(f"상태: {auto_status}")
            print(f"투자금: {self.auto_config['total_capital']:,}원")
            print(f"전략: 이동평균선 골든/데드 크로스")
            print(f"손절: {self.auto_config['stop_loss']*100:.0f}% / 익절: {self.auto_config['take_profit']*100:.0f}%")
            print("-" * 60)
            print()
            print("1. ▶️  자동매매 1회 실행")
            print("2. 🔄 자동매매 연속 실행 (30분 주기)")
            print("3. 📊 매수 후보 종목 스크리닝")
            print("4. 💼 현재 포트폴리오 확인")
            print("5. ⚙️  설정 변경")
            print("0. ⬅️  메인 메뉴로")
            print()

            choice = input("선택하세요: ").strip()

            if choice == '0':
                break
            elif choice == '1':
                self.run_auto_trading_once()
            elif choice == '2':
                self.run_auto_trading_loop()
            elif choice == '3':
                self.screen_buy_candidates()
            elif choice == '4':
                self.show_portfolio()
            elif choice == '5':
                self.configure_auto_trading()
            else:
                print("❌ 잘못된 선택입니다.")

            input("\n엔터를 눌러 계속...")

    def configure_auto_trading(self):
        """자동매매 설정"""
        print("\n⚙️  자동매매 설정")
        print("-" * 40)

        # 투자금 설정
        capital_input = input(f"투자금 (현재: {self.auto_config['total_capital']:,}원): ").strip()
        if capital_input:
            try:
                self.auto_config['total_capital'] = int(capital_input)
            except ValueError:
                print("잘못된 입력, 기존 값 유지")

        # 손절선 설정
        sl_input = input(f"손절선 % (현재: {self.auto_config['stop_loss']*100:.0f}%): ").strip()
        if sl_input:
            try:
                self.auto_config['stop_loss'] = -abs(float(sl_input)) / 100
            except ValueError:
                print("잘못된 입력, 기존 값 유지")

        # 익절선 설정
        tp_input = input(f"익절선 % (현재: {self.auto_config['take_profit']*100:.0f}%): ").strip()
        if tp_input:
            try:
                self.auto_config['take_profit'] = abs(float(tp_input)) / 100
            except ValueError:
                print("잘못된 입력, 기존 값 유지")

        # 전략 재초기화
        self.strategy = TradingStrategy(style=self.auto_config['style'])
        self.strategy.params['stop_loss'] = self.auto_config['stop_loss']
        self.strategy.params['take_profit'] = self.auto_config['take_profit']

        print("\n✅ 설정이 저장되었습니다.")

    def sync_portfolio(self):
        """실제 잔고와 포트폴리오 동기화"""
        balance = self.api.get_balance()

        if not balance or balance.get('rt_cd') != '0':
            return

        holdings = balance.get('output1', [])
        self.portfolio = {}

        for item in holdings:
            code = item.get('pdno', '')
            if not code:
                continue

            quantity = int(item.get('hldg_qty', 0))
            if quantity > 0:
                self.portfolio[code] = {
                    'name': item.get('prdt_name', code),
                    'quantity': quantity,
                    'avg_price': float(item.get('pchs_avg_pric', 0)),
                    'current_price': int(item.get('prpr', 0)),
                    'profit_rate': float(item.get('evlu_pfls_rt', 0))
                }

    def show_portfolio(self):
        """포트폴리오 현황"""
        print("\n📊 현재 포트폴리오")
        print("-" * 50)

        self.sync_portfolio()

        if not self.portfolio:
            print("보유 종목이 없습니다.")
            return

        total_value = 0
        total_profit = 0

        for code, holding in self.portfolio.items():
            value = holding['current_price'] * holding['quantity']
            profit = (holding['current_price'] - holding['avg_price']) * holding['quantity']
            total_value += value
            total_profit += profit

            print(f"\n{holding['name']} ({code})")
            print(f"  수량: {holding['quantity']}주")
            print(f"  평균매수가: {holding['avg_price']:,.0f}원")
            print(f"  현재가: {holding['current_price']:,}원")
            print(f"  수익률: {holding['profit_rate']:+.2f}%")
            print(f"  평가손익: {profit:+,.0f}원")

        print(f"\n{'='*50}")
        print(f"총 평가금액: {total_value:,}원")
        print(f"총 평가손익: {total_profit:+,.0f}원")

    def screen_buy_candidates(self):
        """매수 후보 스크리닝"""
        print("\n🔍 매수 후보 종목 스크리닝 중...")
        print("(이동평균선 골든크로스 + RSI 과매도 기준)")
        print("-" * 50)

        try:
            candidates = self.screener.screen_buy_candidates(max_candidates=5)

            if not candidates:
                print("\n현재 매수 신호가 있는 종목이 없습니다.")
                return

            print(f"\n✅ 매수 추천 종목 ({len(candidates)}개)")
            for i, stock in enumerate(candidates, 1):
                print(f"\n{i}. {stock['name']} ({stock['code']})")
                print(f"   현재가: {stock['price']:,}원 ({stock['change_rate']:+.2f}%)")
                print(f"   추천: {stock['recommendation']} (점수: {stock['score']:.1f})")
                signals = stock['analysis'].get('signals', [])[:3]
                print(f"   시그널: {', '.join(signals)}")

        except Exception as e:
            print(f"❌ 스크리닝 실패: {e}")

    def run_auto_trading_once(self):
        """자동매매 1회 실행"""
        print("\n🤖 자동매매 1회 실행")
        print("=" * 50)

        if self.current_mode == 'real':
            print("⚠️  실전투자 모드입니다. 실제 매매가 실행됩니다!")
            confirm = input("계속하시겠습니까? (y/N): ").strip().lower()
            if confirm != 'y':
                print("취소되었습니다.")
                return

        # 1. 포트폴리오 동기화
        print("\n1️⃣ 포트폴리오 동기화 중...")
        self.sync_portfolio()
        print(f"   현재 보유: {len(self.portfolio)}개 종목")

        # 2. 보유 종목 매도 신호 확인
        print("\n2️⃣ 매도 신호 확인 중...")
        self.check_sell_signals()

        # 3. 매수 신호 확인
        print("\n3️⃣ 매수 신호 확인 중...")
        self.check_buy_signals()

        print("\n✅ 자동매매 1회 실행 완료")

    def check_sell_signals(self):
        """보유 종목 매도 신호 확인"""
        for code, holding in list(self.portfolio.items()):
            try:
                name = holding['name']
                avg_price = holding['avg_price']
                quantity = holding['quantity']

                # 현재가 조회
                price_data = self.api.get_stock_price(code)
                if not price_data or price_data.get('rt_cd') != '0':
                    continue

                current_price = int(price_data['output'].get('stck_prpr', 0))
                profit_rate = (current_price - avg_price) / avg_price

                print(f"\n   {name}: {profit_rate*100:+.2f}%", end="")

                # 손절 확인
                if profit_rate <= self.auto_config['stop_loss']:
                    print(f" => 손절!")
                    self.execute_sell(code, name, quantity, "STOP_LOSS")
                    continue

                # 익절 확인
                if profit_rate >= self.auto_config['take_profit']:
                    print(f" => 익절!")
                    self.execute_sell(code, name, quantity, "TAKE_PROFIT")
                    continue

                # 기술적 분석 매도 신호
                analysis = self.screener.analyze_single_stock(code)
                if analysis and self.strategy.should_sell(analysis['analysis']):
                    print(f" => 기술적 매도 신호!")
                    self.execute_sell(code, name, quantity, "SIGNAL")

                time.sleep(0.3)

            except Exception as e:
                print(f"\n   {code} 확인 실패: {e}")

    def check_buy_signals(self):
        """매수 신호 확인"""
        current_positions = len(self.portfolio)
        max_positions = self.auto_config['max_positions']

        if current_positions >= max_positions:
            print(f"   최대 보유 종목 수 도달 ({current_positions}/{max_positions})")
            return

        # 매수 후보 스크리닝
        try:
            candidates = self.screener.screen_buy_candidates(
                max_candidates=max_positions - current_positions
            )

            # 이미 보유 중인 종목 제외
            candidates = [c for c in candidates if c['code'] not in self.portfolio]

            if not candidates:
                print("   매수 후보 없음")
                return

            for candidate in candidates:
                if len(self.portfolio) >= max_positions:
                    break

                code = candidate['code']
                name = candidate['name']
                price = candidate['price']

                # 매수 수량 계산
                position_amount = self.auto_config['total_capital'] * self.auto_config['position_size']
                quantity = int(position_amount / price)

                if quantity < 1:
                    continue

                print(f"\n   {name}: 매수 신호 (점수: {candidate['score']:.1f})")
                self.execute_buy(code, name, quantity, price)
                time.sleep(1)

        except Exception as e:
            print(f"   매수 확인 실패: {e}")

    def execute_buy(self, code: str, name: str, quantity: int, price: int):
        """매수 실행"""
        print(f"   => {name} {quantity}주 매수 주문...")

        result = self.api.buy_stock(code, quantity, order_type="03")

        if result and result.get('rt_cd') == '0':
            print(f"   ✅ 매수 성공!")
            self.portfolio[code] = {
                'name': name,
                'quantity': quantity,
                'avg_price': price,
                'current_price': price,
                'profit_rate': 0
            }
        else:
            error = result.get('msg1', 'Unknown') if result else 'No response'
            print(f"   ❌ 매수 실패: {error}")

    def execute_sell(self, code: str, name: str, quantity: int, reason: str):
        """매도 실행"""
        print(f"   => {name} {quantity}주 매도 주문 ({reason})...")

        result = self.api.sell_stock(code, quantity, order_type="03")

        if result and result.get('rt_cd') == '0':
            print(f"   ✅ 매도 성공!")
            if code in self.portfolio:
                del self.portfolio[code]
        else:
            error = result.get('msg1', 'Unknown') if result else 'No response'
            print(f"   ❌ 매도 실패: {error}")

    def run_auto_trading_loop(self):
        """자동매매 연속 실행"""
        print("\n🔄 자동매매 연속 실행 (30분 주기)")
        print("=" * 50)

        if self.current_mode == 'real':
            print("⚠️  실전투자 모드입니다. 실제 매매가 실행됩니다!")
            confirm = input("계속하시겠습니까? (y/N): ").strip().lower()
            if confirm != 'y':
                print("취소되었습니다.")
                return

        print("\n중지하려면 Ctrl+C를 누르세요.")
        self.auto_trading_enabled = True

        try:
            while self.auto_trading_enabled:
                now = datetime.now()
                hour = now.hour

                # 장 시간 체크 (09:00 ~ 15:30)
                if 9 <= hour < 16:
                    print(f"\n[{now.strftime('%H:%M:%S')}] 자동매매 실행...")
                    self.sync_portfolio()
                    self.check_sell_signals()
                    self.check_buy_signals()
                else:
                    print(f"\n[{now.strftime('%H:%M')}] 장 마감 시간 (09:00~15:30 외)")

                print("\n다음 실행: 30분 후 (Ctrl+C로 중지)")
                time.sleep(30 * 60)

        except KeyboardInterrupt:
            print("\n\n⏹️ 자동매매 중지됨")
            self.auto_trading_enabled = False

    def run(self):
        try:
            # 패키지 설치 확인
            install_requirements()
            
            self.select_mode()
            
            while True:
                self.show_main_menu()
                choice = input("메뉴를 선택하세요 (0-88): ").strip()
                
                if choice == '0':
                    print("\n👋 프로그램을 종료합니다.")
                    break
                # 국내주식 메뉴
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
                # 미국주식 메뉴
                elif choice == '6':
                    self.get_us_stock_price_info()
                elif choice == '7':
                    self.buy_us_stock_menu()
                elif choice == '8':
                    self.sell_us_stock_menu()
                elif choice == '9':
                    self.get_us_balance_info()
                # 자동매매 메뉴
                elif choice == '10':
                    self.show_auto_trading_menu()
                    continue
                # 시스템 메뉴
                elif choice == '88':
                    self.select_mode()
                    continue
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