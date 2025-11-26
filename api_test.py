#!/usr/bin/env python3
"""
한국투자증권 API 전체 기능 테스트
- 데모/실전 계정 연결 테스트
- 모든 API 엔드포인트 동작 확인
- 매수/매도 주문 테스트 (모의투자)
"""

import sys
import traceback
from datetime import datetime
import json
from pathlib import Path

from kis_api import KisAPI
from config import Config

class APITester:
    def __init__(self):
        self.demo_api = None
        self.real_api = None
        self.test_results = {
            'demo': {},
            'real': {}
        }
        
    def initialize_apis(self):
        """API 초기화"""
        print("🔧 API 초기화 중...")
        
        try:
            # 데모 계정 초기화
            demo_account = Config.get_account_info('demo')
            self.demo_api = KisAPI(
                demo_account['appkey'],
                demo_account['appsecret'],
                demo_account['account'],
                is_real=False
            )
            
            # 실전 계정 초기화
            real_account = Config.get_account_info('real')
            self.real_api = KisAPI(
                real_account['appkey'],
                real_account['appsecret'],
                real_account['account'],
                is_real=True
            )
            
            print("✅ API 객체 초기화 완료")
            return True
            
        except Exception as e:
            print(f"❌ API 초기화 실패: {e}")
            return False
    
    def test_token_generation(self, api, mode):
        """토큰 발급 테스트"""
        print(f"\n📋 {mode.upper()} 토큰 발급 테스트")
        
        try:
            success = api.get_access_token()
            if success and api.access_token:
                print(f"✅ 토큰 발급 성공")
                print(f"   토큰: {api.access_token[:20]}...")
                print(f"   만료: {api.token_expire_time}")
                self.test_results[mode]['token'] = 'SUCCESS'
                return True
            else:
                print(f"❌ 토큰 발급 실패")
                self.test_results[mode]['token'] = 'FAILED'
                return False
                
        except Exception as e:
            print(f"❌ 토큰 발급 오류: {e}")
            self.test_results[mode]['token'] = f'ERROR: {e}'
            return False
    
    def test_balance_inquiry(self, api, mode):
        """잔고 조회 테스트"""
        print(f"\n💰 {mode.upper()} 잔고 조회 테스트")
        
        try:
            balance = api.get_balance()
            if balance and balance.get('rt_cd') == '0':
                print(f"✅ 잔고 조회 성공")
                
                # output2에서 현금 정보 추출
                output2 = balance.get('output2', [])
                if output2:
                    cash = int(output2[0].get('ord_psbl_cash', 0))
                    total_value = int(output2[0].get('tot_evlu_amt', 0))
                    print(f"   주문가능현금: {cash:,}원")
                    print(f"   총평가금액: {total_value:,}원")
                
                # output1에서 보유 종목 정보
                output1 = balance.get('output1', [])
                holding_count = sum(1 for stock in output1 if int(stock.get('hldg_qty', 0)) > 0)
                print(f"   보유종목수: {holding_count}개")
                
                self.test_results[mode]['balance'] = 'SUCCESS'
                return balance
            else:
                print(f"❌ 잔고 조회 실패: {balance}")
                self.test_results[mode]['balance'] = 'FAILED'
                return None
                
        except Exception as e:
            print(f"❌ 잔고 조회 오류: {e}")
            self.test_results[mode]['balance'] = f'ERROR: {e}'
            return None
    
    def test_stock_price(self, api, mode):
        """주식 현재가 조회 테스트"""
        print(f"\n📈 {mode.upper()} 주식 현재가 조회 테스트")
        
        test_stocks = ['005930', '000660', '035420']  # 삼성전자, SK하이닉스, NAVER
        stock_names = {'005930': '삼성전자', '000660': 'SK하이닉스', '035420': 'NAVER'}
        
        success_count = 0
        
        for stock_code in test_stocks:
            try:
                price_data = api.get_stock_price(stock_code)
                if price_data and price_data.get('rt_cd') == '0':
                    output = price_data['output']
                    current_price = int(output['stck_prpr'])
                    change = int(output['prdy_vrss'])
                    change_rate = float(output['prdy_ctrt'])
                    
                    print(f"✅ {stock_names[stock_code]} ({stock_code})")
                    print(f"   현재가: {current_price:,}원")
                    print(f"   전일대비: {change:+,}원 ({change_rate:+.2f}%)")
                    success_count += 1
                else:
                    print(f"❌ {stock_names[stock_code]} 조회 실패")
                    
            except Exception as e:
                print(f"❌ {stock_names[stock_code]} 조회 오류: {e}")
        
        if success_count == len(test_stocks):
            self.test_results[mode]['stock_price'] = 'SUCCESS'
            return True
        else:
            self.test_results[mode]['stock_price'] = f'PARTIAL: {success_count}/{len(test_stocks)}'
            return False
    
    def test_daily_price(self, api, mode):
        """일봉 데이터 조회 테스트"""
        print(f"\n📊 {mode.upper()} 일봉 데이터 조회 테스트")
        
        try:
            daily_data = api.get_daily_price('005930', count=10)
            if daily_data and daily_data.get('rt_cd') == '0':
                output = daily_data['output']
                print(f"✅ 일봉 데이터 조회 성공")
                print(f"   조회건수: {len(output)}건")
                
                # 최근 3일 데이터 출력
                for i, day in enumerate(output[:3]):
                    date = day['stck_bsop_date']
                    close = int(day['stck_clpr'])
                    volume = int(day['acml_vol'])
                    print(f"   {date}: {close:,}원 (거래량: {volume:,})")
                
                self.test_results[mode]['daily_price'] = 'SUCCESS'
                return True
            else:
                print(f"❌ 일봉 데이터 조회 실패")
                self.test_results[mode]['daily_price'] = 'FAILED'
                return False
                
        except Exception as e:
            print(f"❌ 일봉 데이터 조회 오류: {e}")
            self.test_results[mode]['daily_price'] = f'ERROR: {e}'
            return False
    
    def test_market_data(self, api, mode):
        """시장 데이터 조회 테스트 (거래량 순위, 등락률 순위)"""
        print(f"\n🏢 {mode.upper()} 시장 데이터 조회 테스트")
        
        success_count = 0
        
        # 거래량 순위 조회
        try:
            volume_rank = api.get_volume_rank()
            if volume_rank and volume_rank.get('rt_cd') == '0':
                output = volume_rank['output']
                print(f"✅ 거래량 순위 조회 성공 ({len(output)}건)")
                
                # 상위 3종목 출력
                for i, stock in enumerate(output[:3]):
                    name = stock.get('hts_kor_isnm', 'N/A')
                    volume = int(stock.get('acml_vol', 0))
                    print(f"   {i+1}. {name}: {volume:,}")
                
                success_count += 1
            else:
                print(f"❌ 거래량 순위 조회 실패")
        except Exception as e:
            print(f"❌ 거래량 순위 조회 오류: {e}")
        
        # 등락률 순위 조회
        try:
            fluctuation_rank = api.get_fluctuation_rank()
            if fluctuation_rank and fluctuation_rank.get('rt_cd') == '0':
                output = fluctuation_rank['output']
                print(f"✅ 등락률 순위 조회 성공 ({len(output)}건)")
                
                # 상위 3종목 출력
                for i, stock in enumerate(output[:3]):
                    name = stock.get('hts_kor_isnm', 'N/A')
                    rate = float(stock.get('prdy_ctrt', 0))
                    print(f"   {i+1}. {name}: {rate:+.2f}%")
                
                success_count += 1
            else:
                print(f"❌ 등락률 순위 조회 실패")
        except Exception as e:
            print(f"❌ 등락률 순위 조회 오류: {e}")
        
        if success_count == 2:
            self.test_results[mode]['market_data'] = 'SUCCESS'
            return True
        else:
            self.test_results[mode]['market_data'] = f'PARTIAL: {success_count}/2'
            return False
    
    def test_order_demo_only(self, api, mode):
        """주문 테스트 (모의투자만)"""
        if mode == 'real':
            print(f"\n⚠️ {mode.upper()} 실제 주문 테스트는 안전상 생략")
            self.test_results[mode]['order'] = 'SKIPPED_FOR_SAFETY'
            return True
            
        print(f"\n💹 {mode.upper()} 주문 테스트 (모의투자)")
        
        test_stock = '005930'  # 삼성전자
        test_quantity = 1
        
        try:
            # 현재가 조회
            price_data = api.get_stock_price(test_stock)
            if not price_data or price_data.get('rt_cd') != '0':
                print(f"❌ 현재가 조회 실패, 주문 테스트 불가")
                self.test_results[mode]['order'] = 'FAILED_NO_PRICE'
                return False
            
            current_price = int(price_data['output']['stck_prpr'])
            print(f"📋 삼성전자 현재가: {current_price:,}원")
            
            # 시장가 매수 주문
            print(f"📋 시장가 매수 주문 시도: {test_quantity}주")
            buy_result = api.buy_stock(test_stock, test_quantity, order_type="03")  # 시장가
            
            if buy_result and buy_result.get('rt_cd') == '0':
                order_no = buy_result.get('output', {}).get('ODNO', 'N/A')
                print(f"✅ 매수 주문 성공")
                print(f"   주문번호: {order_no}")
                print(f"   종목: 삼성전자 ({test_stock})")
                print(f"   수량: {test_quantity}주")
                
                # 잠시 대기 후 주문 내역 조회
                print(f"📋 주문 내역 조회 중...")
                import time
                time.sleep(2)
                
                orders = api.get_orders()
                if orders and orders.get('rt_cd') == '0':
                    print(f"✅ 주문 내역 조회 성공")
                    output = orders.get('output', [])
                    recent_orders = [o for o in output if o.get('pdno') == test_stock]
                    print(f"   삼성전자 관련 주문: {len(recent_orders)}건")
                    
                self.test_results[mode]['order'] = 'SUCCESS'
                return True
            else:
                print(f"❌ 매수 주문 실패: {buy_result}")
                self.test_results[mode]['order'] = 'FAILED'
                return False
                
        except Exception as e:
            print(f"❌ 주문 테스트 오류: {e}")
            self.test_results[mode]['order'] = f'ERROR: {e}'
            return False
    
    def test_comprehensive_api_functions(self, api, mode):
        """종합 API 기능 테스트"""
        print(f"\n🔍 {mode.upper()} 종합 API 기능 테스트")
        
        success_count = 0
        total_tests = 0
        
        # 보유 종목 조회
        total_tests += 1
        try:
            holdings = api.get_holding_stocks()
            print(f"✅ 보유 종목 조회: {len(holdings)}개 종목")
            for holding in holdings[:3]:  # 상위 3개만 출력
                name = holding['stock_name']
                qty = holding['quantity']
                profit = holding['profit_rate']
                print(f"   {name}: {qty}주 ({profit:+.2f}%)")
            success_count += 1
        except Exception as e:
            print(f"❌ 보유 종목 조회 오류: {e}")
        
        # 주문 가능 현금 조회
        total_tests += 1
        try:
            cash = api.get_available_cash()
            print(f"✅ 주문 가능 현금: {cash:,}원")
            success_count += 1
        except Exception as e:
            print(f"❌ 주문 가능 현금 조회 오류: {e}")
        
        # 시가총액 순위 조회
        total_tests += 1
        try:
            market_cap = api.get_market_cap_rank()
            if market_cap and market_cap.get('rt_cd') == '0':
                print(f"✅ 시가총액 순위 조회 성공")
                success_count += 1
            else:
                print(f"❌ 시가총액 순위 조회 실패")
        except Exception as e:
            print(f"❌ 시가총액 순위 조회 오류: {e}")
        
        self.test_results[mode]['comprehensive'] = f'{success_count}/{total_tests}'
        return success_count == total_tests
    
    def run_full_test(self):
        """전체 테스트 실행"""
        print("🚀 한국투자증권 API 전체 기능 테스트 시작")
        print("=" * 60)
        
        if not self.initialize_apis():
            return False
        
        # 데모 계정 테스트
        print("\n" + "="*30 + " 데모 계정 " + "="*30)
        demo_success = True
        demo_success = demo_success and self.test_token_generation(self.demo_api, 'demo')
        if demo_success:
            self.test_balance_inquiry(self.demo_api, 'demo')
            demo_success = demo_success and self.test_stock_price(self.demo_api, 'demo')
            demo_success = demo_success and self.test_daily_price(self.demo_api, 'demo')
            demo_success = demo_success and self.test_market_data(self.demo_api, 'demo')
            demo_success = demo_success and self.test_order_demo_only(self.demo_api, 'demo')
            demo_success = demo_success and self.test_comprehensive_api_functions(self.demo_api, 'demo')
        
        # 실전 계정 테스트
        print("\n" + "="*30 + " 실전 계정 " + "="*30)
        real_success = True
        real_success = real_success and self.test_token_generation(self.real_api, 'real')
        if real_success:
            self.test_balance_inquiry(self.real_api, 'real')
            real_success = real_success and self.test_stock_price(self.real_api, 'real')
            real_success = real_success and self.test_daily_price(self.real_api, 'real')
            real_success = real_success and self.test_market_data(self.real_api, 'real')
            real_success = real_success and self.test_order_demo_only(self.real_api, 'real')  # 실전은 주문 생략
            real_success = real_success and self.test_comprehensive_api_functions(self.real_api, 'real')
        
        # 결과 리포트
        self.generate_report()
        
        return demo_success and real_success
    
    def generate_report(self):
        """테스트 결과 리포트 생성"""
        print("\n" + "="*60)
        print("📊 테스트 결과 리포트")
        print("="*60)
        
        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"api_test_report_{timestamp}.json"
        
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'results': self.test_results
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        # 콘솔 출력
        for mode in ['demo', 'real']:
            print(f"\n🔍 {mode.upper()} 계정 결과:")
            results = self.test_results[mode]
            
            for test_name, result in results.items():
                status = "✅" if result == 'SUCCESS' else "❌" if 'ERROR' in str(result) or result == 'FAILED' else "⚠️"
                print(f"   {status} {test_name}: {result}")
        
        print(f"\n📋 상세 결과가 저장되었습니다: {report_file}")
        
        # 요약
        demo_tests = list(self.test_results['demo'].values())
        real_tests = list(self.test_results['real'].values())
        
        demo_success = sum(1 for r in demo_tests if r == 'SUCCESS')
        real_success = sum(1 for r in real_tests if r == 'SUCCESS')
        
        print(f"\n🎯 종합 결과:")
        print(f"   데모 계정: {demo_success}/{len(demo_tests)} 성공")
        print(f"   실전 계정: {real_success}/{len(real_tests)} 성공")
        
        if demo_success == len(demo_tests) and real_success >= len(real_tests) - 1:  # 실전 주문 제외
            print("🎉 모든 API 기능이 정상 동작합니다!")
        else:
            print("⚠️ 일부 API 기능에 문제가 있습니다. 로그를 확인하세요.")

def main():
    """메인 함수"""
    tester = APITester()
    
    try:
        success = tester.run_full_test()
        
        if success:
            print("\n🎊 API 테스트가 성공적으로 완료되었습니다!")
            return 0
        else:
            print("\n❌ API 테스트 중 문제가 발견되었습니다.")
            return 1
            
    except KeyboardInterrupt:
        print("\n👋 사용자에 의해 테스트가 중단되었습니다.")
        return 1
    except Exception as e:
        print(f"\n💥 예상치 못한 오류 발생: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)