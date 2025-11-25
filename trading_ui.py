import os
import sys
import subprocess
from kis_api import KisAPI
from config import Config

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
        print("\n📋 메인 메뉴:")
        print()
        print("1. 💰 계좌 정보 조회")
        print("2. 📈 주식 현재가 조회")
        print("3. 🛒 주식 매수")
        print("4. 🛍️  주식 매도") 
        print("5. 📊 주문 내역 조회")
        print("6. 🔄 모드 변경")
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
    
    def run(self):
        try:
            # 패키지 설치 확인
            install_requirements()
            
            self.select_mode()
            
            while True:
                self.show_main_menu()
                choice = input("메뉴를 선택하세요 (0-6): ").strip()
                
                if choice == '0':
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