#!/usr/bin/env python3
"""
간단한 AI 자동매매 시스템
테스트 및 모니터링용
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yaml
import requests
import time
import threading
from collections import deque
import hashlib

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trading_system')

class RateLimiter:
    """API 호출 제한 관리"""
    def __init__(self, max_calls=15, period=1.0):
        self.max_calls, self.period = max_calls, period
        self.calls, self.lock = deque(), threading.Lock()
    
    def wait(self):
        with self.lock:
            now = time.time()
            while self.calls and now - self.calls[0] >= self.period:
                self.calls.popleft()
            if len(self.calls) >= self.max_calls:
                time.sleep(self.period - (now - self.calls[0]))
            self.calls.append(time.time())

class KISBroker:
    """한국투자증권 API 브로커"""
    
    def __init__(self, config_path: str, paper_trading: bool = True):
        """초기화"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.paper_trading = paper_trading
        self.base_url = "https://openapivts.koreainvestment.com:29443" if paper_trading else "https://openapi.koreainvestment.com:9443"
        self.rate_limiter = RateLimiter(max_calls=15, period=1.0)
        
        self.access_token = None
        self.token_expires = None
        
        # 초기 토큰 발급
        self._get_access_token()
        logger.info(f"KIS 브로커 초기화 완료 - {'모의투자' if paper_trading else '실전투자'}")
    
    def _get_access_token(self):
        """액세스 토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"
        key_prefix = "paper" if self.paper_trading else "my"
        
        body = {
            "grant_type": "client_credentials",
            "appkey": self.config[f"{key_prefix}_app"],
            "appsecret": self.config[f"{key_prefix}_sec"]
        }
        
        try:
            response = requests.post(url, headers={"content-type": "application/json"}, json=body)
            result = response.json()
            
            logger.info(f"토큰 응답: {result}")
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.token_expires = datetime.now() + timedelta(hours=23)
                logger.info("✅ 액세스 토큰 발급 성공")
            else:
                logger.error(f"❌ 토큰 발급 실패: {result}")
                raise Exception(f"토큰 발급 실패: {result}")
                
        except Exception as e:
            logger.error(f"토큰 발급 오류: {e}")
            raise
    
    def _get_headers(self, tr_id: str) -> Dict:
        """API 헤더 생성"""
        if not self.access_token or datetime.now() >= self.token_expires:
            self._get_access_token()
        
        key_prefix = "paper" if self.paper_trading else "my"
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config[f"{key_prefix}_app"],
            "appsecret": self.config[f"{key_prefix}_sec"],
            "tr_id": tr_id,
            "custtype": "P"
        }
    
    def get_stock_price(self, stock_code: str) -> Optional[Dict]:
        """주식 현재가 조회"""
        self.rate_limiter.wait()
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = self._get_headers("FHKST01010100")
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            
            if result.get('rt_cd') == '0':
                output = result['output']
                return {
                    'stock_code': stock_code,
                    'current_price': int(output['stck_prpr']),
                    'change': int(output['prdy_vrss']),
                    'change_rate': float(output['prdy_ctrt']),
                    'volume': int(output['acml_vol'])
                }
            else:
                logger.error(f"주식 현재가 조회 실패: {result.get('msg1')}")
                return None
        except Exception as e:
            logger.error(f"주식 현재가 조회 오류: {e}")
            return None
    
    def get_balance(self) -> Optional[Dict]:
        """계좌 잔고 조회"""
        self.rate_limiter.wait()
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        tr_id = "VTTC8434R" if self.paper_trading else "TTTC8434R"
        
        headers = self._get_headers(tr_id)
        params = {
            "CANO": self.config["my_acct_stock"],
            "ACNT_PRDT_CD": self.config["my_prod"],
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            
            if result.get('rt_cd') == '0':
                return result
            else:
                logger.error(f"계좌 조회 실패: {result.get('msg1')}")
                return None
        except Exception as e:
            logger.error(f"계좌 조회 오류: {e}")
            return None

class SimpleStrategy:
    """간단한 거래 전략"""
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.name = "Simple_Strategy"
    
    def generate_signals(self, broker: KISBroker) -> List[Dict]:
        """간단한 신호 생성"""
        signals = []
        
        for symbol in self.symbols:
            try:
                price_info = broker.get_stock_price(symbol)
                if price_info:
                    change_rate = price_info['change_rate']
                    
                    # 단순 신호 로직: 3% 이상 하락시 매수 신호
                    if change_rate < -3.0:
                        signals.append({
                            'symbol': symbol,
                            'action': 'BUY',
                            'reason': f'하락률 {change_rate:.2f}%로 매수 신호'
                        })
                
                time.sleep(0.2)  # API 호출 간격
                
            except Exception as e:
                logger.error(f"신호 생성 오류 ({symbol}): {e}")
        
        return signals

class TradingSystem:
    """AI 자동매매 시스템"""
    
    def __init__(self, config_path: str = "ai_trading_system/config/kis_config.yaml", paper_trading: bool = True):
        """초기화"""
        logger.info("=== AI 자동매매 시스템 초기화 ===")
        
        self.broker = KISBroker(config_path, paper_trading)
        self.strategy = SimpleStrategy(['005930', '000660'])  # 삼성전자, SK하이닉스
        
        self.portfolio = {}
        self.cash_balance = 0
        self.total_value = 0
        self.is_running = False
        
        logger.info("AI 자동매매 시스템 초기화 완료")
    
    async def update_portfolio(self):
        """포트폴리오 상태 업데이트"""
        try:
            balance_info = self.broker.get_balance()
            
            if balance_info and balance_info.get('rt_cd') == '0':
                # 현금 잔고
                output2 = balance_info.get('output2', [{}])
                if output2:
                    self.cash_balance = float(output2[0].get('dnca_tot_amt', 0))
                    self.total_value = float(output2[0].get('tot_evlu_amt', 0))
                
                # 보유 종목
                output1 = balance_info.get('output1', [])
                self.portfolio = {}
                
                for holding in output1:
                    if int(holding.get('hldg_qty', 0)) > 0:
                        stock_code = holding['pdno']
                        self.portfolio[stock_code] = {
                            'name': holding['prdt_name'],
                            'quantity': int(holding['hldg_qty']),
                            'avg_price': float(holding['pchs_avg_pric']),
                            'current_price': float(holding['prpr']),
                            'eval_amount': float(holding['evlu_amt']),
                            'profit_rate': float(holding['evlu_pfls_rt'])
                        }
                
                logger.info("📊 포트폴리오 상태 업데이트 완료")
                logger.info(f"   💰 총 자산: {self.total_value:,.0f}원")
                logger.info(f"   💵 현금: {self.cash_balance:,.0f}원")
                logger.info(f"   📈 보유 종목: {len(self.portfolio)}개")
                
                for code, info in self.portfolio.items():
                    logger.info(f"   - {info['name']}: {info['quantity']}주, 수익률 {info['profit_rate']:.2f}%")
                
        except Exception as e:
            logger.error(f"포트폴리오 업데이트 오류: {e}")
    
    def is_market_open(self) -> bool:
        """장 개장 여부 확인"""
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour
        minute = now.minute
        
        # 평일 09:00 ~ 15:30
        if weekday < 5 and (9 <= hour < 15 or (hour == 15 and minute <= 30)):
            return True
        
        return False
    
    async def run(self):
        """메인 실행 루프"""
        logger.info("🚀 AI 자동매매 시스템 시작")
        
        try:
            await self.update_portfolio()
            self.is_running = True
            
            while self.is_running:
                try:
                    current_time = datetime.now()
                    
                    if self.is_market_open():
                        logger.info(f"📊 장중 모니터링 - {current_time.strftime('%H:%M:%S')}")
                        
                        # 신호 생성
                        signals = self.strategy.generate_signals(self.broker)
                        
                        if signals:
                            logger.info(f"🎯 {len(signals)}개 거래 신호 감지")
                            for signal in signals:
                                logger.info(f"   📈 {signal['symbol']}: {signal['action']} - {signal['reason']}")
                        else:
                            logger.info("   📍 현재 거래 신호 없음")
                        
                        # 포트폴리오 업데이트
                        await self.update_portfolio()
                        
                        # 5분 대기
                        await asyncio.sleep(300)
                    else:
                        logger.info(f"😴 장외시간 대기 - {current_time.strftime('%H:%M:%S')}")
                        
                        # 간단한 상태 체크
                        await self.update_portfolio()
                        
                        # 30분 대기
                        await asyncio.sleep(1800)
                
                except KeyboardInterrupt:
                    logger.info("사용자 중지 요청")
                    break
                except Exception as e:
                    logger.error(f"메인 루프 오류: {e}")
                    await asyncio.sleep(300)  # 5분 후 재시도
        
        finally:
            self.is_running = False
            logger.info("AI 자동매매 시스템 종료")

def get_user_choice():
    """사용자 선택 메뉴"""
    print("""
╔══════════════════════════════════════════════════╗
║              🤖 AI 자동매매 시스템                 ║
╠══════════════════════════════════════════════════╣
║  1️⃣  24시간 모니터링 시작                          ║
║  2️⃣  포트폴리오 상태 확인                          ║
║  3️⃣  현재가 조회                                   ║
║  4️⃣  시스템 종료                                   ║
╚══════════════════════════════════════════════════╝
    """)
    
    while True:
        try:
            choice = input("선택하세요 (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return choice
            else:
                print("❌ 1, 2, 3, 4 중에서 선택해주세요.")
        except KeyboardInterrupt:
            return '4'

def select_trading_mode():
    """거래 모드 선택"""
    print("""
╔══════════════════════════════════════════════════╗
║              💰 거래 모드 선택                     ║
╠══════════════════════════════════════════════════╣
║  1️⃣  모의투자 (Demo)                               ║
║      - 가상 머니로 안전한 테스트                    ║
║      - 실제 돈 손실 위험 없음                       ║
║                                                  ║
║  2️⃣  실전투자 (Real) ⚠️                           ║
║      - 실제 돈으로 거래                            ║
║      - 실제 수익/손실 발생                         ║
╚══════════════════════════════════════════════════╝
    """)
    
    while True:
        try:
            choice = input("거래 모드를 선택하세요 (1 또는 2): ").strip()
            if choice == '1':
                return True  # 모의투자
            elif choice == '2':
                print("\n⚠️  실전투자 모드를 선택하셨습니다!")
                print("실제 돈으로 거래가 실행됩니다.")
                confirm = input("정말 실전투자로 진행하시겠습니까? (yes/no): ").strip().lower()
                if confirm in ['yes', 'y', '네', 'ㅇ']:
                    return False  # 실전투자
                elif confirm in ['no', 'n', '아니오', 'ㄴ']:
                    continue
                else:
                    print("yes 또는 no로 답해주세요.")
            else:
                print("❌ 1 또는 2를 선택해주세요.")
        except KeyboardInterrupt:
            print("\n시스템을 종료합니다.")
            exit(0)
        except EOFError:
            print("\n시스템을 종료합니다.")
            exit(0)

def main_interactive():
    """대화형 메인 함수"""
    print(f"""
╔══════════════════════════════════════════════════╗
║              🚀 AI 자동매매 시스템                 ║
║                                                  ║
║  시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    ║
╚══════════════════════════════════════════════════╝
    """)
    
    try:
        # 거래 모드 선택
        paper_trading = select_trading_mode()
        mode_name = "모의투자" if paper_trading else "실전투자"
        
        print(f"\n✅ {mode_name} 모드로 시스템을 초기화합니다...")
        trading_system = TradingSystem(paper_trading=paper_trading)
        
        print(f"""
╔══════════════════════════════════════════════════╗
║  초기화 완료 - {mode_name} 모드                    ║
╚══════════════════════════════════════════════════╝
        """)
        
        while True:
            choice = get_user_choice()
            
            if choice == '1':
                print("\n🚀 24시간 모니터링을 시작합니다...")
                print("⚠️  모니터링 중지: Ctrl+C")
                print("=" * 60)
                
                try:
                    asyncio.run(trading_system.run())
                except KeyboardInterrupt:
                    print("\n⏹️  모니터링이 중지되었습니다.")
                    continue
            
            elif choice == '2':
                print("\n📊 포트폴리오 상태를 확인합니다...")
                try:
                    asyncio.run(trading_system.update_portfolio())
                    input("\n계속하려면 Enter를 누르세요...")
                except Exception as e:
                    print(f"❌ 포트폴리오 조회 오류: {e}")
            
            elif choice == '3':
                symbols = ['005930', '000660', '035420']  # 삼성전자, SK하이닉스, NAVER
                print("\n💰 주요 종목 현재가 조회...")
                
                for symbol in symbols:
                    try:
                        price_info = trading_system.broker.get_stock_price(symbol)
                        if price_info:
                            print(f"📈 {symbol}: {price_info['current_price']:,}원 ({price_info['change_rate']:+.2f}%)")
                        else:
                            print(f"❌ {symbol}: 현재가 조회 실패")
                        time.sleep(0.2)
                    except Exception as e:
                        print(f"❌ {symbol}: {e}")
                
                input("\n계속하려면 Enter를 누르세요...")
            
            elif choice == '4':
                print("\n👋 AI 자동매매 시스템을 종료합니다.")
                break
        
    except Exception as e:
        print(f"\n❌ 시스템 초기화 오류: {e}")
        logger.error(f"시스템 오류: {e}")
        print("API 설정을 확인해주세요.")

def main_monitoring():
    """자동 모니터링 함수 (모의투자 모드)"""
    print(f"""
╔══════════════════════════════════════════════════╗
║           🤖 AI 자동 모니터링 시작                 ║
║                                                  ║
║  모드: 모의투자 (Demo)                            ║
║  시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    ║
╚══════════════════════════════════════════════════╝
    """)
    
    try:
        # 모의투자 모드로 초기화
        trading_system = TradingSystem(paper_trading=True)
        
        print("✅ 시스템 초기화 완료")
        print("🚀 24시간 모니터링을 시작합니다...")
        print("⚠️  모니터링 중지: Ctrl+C")
        print("=" * 60)
        
        # 바로 모니터링 시작
        asyncio.run(trading_system.run())
        
    except KeyboardInterrupt:
        print("\n⏹️  모니터링이 중지되었습니다.")
    except Exception as e:
        print(f"\n❌ 시스템 오류: {e}")
        logger.error(f"시스템 오류: {e}")

def main():
    """메인 함수"""
    import sys
    
    # 명령행 인수 확인
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        main_monitoring()
    else:
        main_interactive()

if __name__ == "__main__":
    main()