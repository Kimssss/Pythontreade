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
try:
    import yaml
except ImportError:
    print("❌ PyYAML 모듈이 설치되어 있지 않습니다.")
    import subprocess
    subprocess.check_call(["pip", "install", "PyYAML"])
    import yaml

# 표준 라이브러리만 사용해서 HTTP 요청
import urllib.request
import urllib.parse
import ssl
import sys
import importlib

def http_post(url: str, headers: dict, data: dict) -> dict:
    """urllib을 사용한 POST 요청"""
    try:
        # JSON 데이터 인코딩
        json_data = json.dumps(data).encode('utf-8')
        
        # 요청 생성
        req = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
        
        # SSL 컨텍스트 설정
        ctx = ssl.create_default_context()
        
        # 요청 실행
        with urllib.request.urlopen(req, context=ctx) as response:
            return json.loads(response.read().decode('utf-8'))
            
    except Exception as e:
        logger.error(f"HTTP POST 오류: {e}")
        raise

def http_get(url: str, headers: dict, params: dict) -> dict:
    """urllib을 사용한 GET 요청"""
    try:
        # 파라미터 인코딩
        query_string = urllib.parse.urlencode(params)
        full_url = f"{url}?{query_string}"
        
        # 요청 생성
        req = urllib.request.Request(full_url, headers=headers)
        
        # SSL 컨텍스트 설정
        ctx = ssl.create_default_context()
        
        # 요청 실행
        with urllib.request.urlopen(req, context=ctx) as response:
            return json.loads(response.read().decode('utf-8'))
            
    except Exception as e:
        logger.error(f"HTTP GET 오류: {e}")
        raise
import time
import threading
from collections import deque
import hashlib
import os
import json

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trading_system')

# 모니터링 데이터 로거 설정
monitoring_logger = logging.getLogger('monitoring')
monitoring_handler = logging.FileHandler('monitoring_data.log', encoding='utf-8')
monitoring_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
monitoring_logger.addHandler(monitoring_handler)
monitoring_logger.setLevel(logging.INFO)

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
    
    def __init__(self, config_path: str = None, paper_trading: bool = True):
        """초기화"""
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
            except Exception as e:
                logger.warning(f"설정 파일 로드 실패: {e}, 기본 설정 사용")
                self.config = self._get_default_config()
        else:
            self.config = self._get_default_config()
        
        self.paper_trading = paper_trading
        self.base_url = "https://openapivts.koreainvestment.com:29443" if paper_trading else "https://openapi.koreainvestment.com:9443"
        self.rate_limiter = RateLimiter(max_calls=15, period=1.0)
        
        self.access_token = None
        self.token_expires = None
        
        # 초기 토큰 발급
        self._get_access_token()
        logger.info(f"KIS 브로커 초기화 완료 - {'모의투자' if paper_trading else '실전투자'}")
    
    def _get_default_config(self):
        """기본 설정 반환 (.env 파일에서 읽기)"""
        return {
            "paper_app": "PSTP8BTWgg4loa76mISQPzb2tHvjxtrBUDID",
            "paper_sec": "rc+xPU2Ya43Z7MgdiLNknR3QWQMc9yBHj9j4WuK63/XiBvusTUcRVhi3vl8tQdup5yUbRBJJ5+AHv1o3dUgdMdX3Xw5AN09go98Z2+BMeBfF/kaDCw9jHDH1RWhjBi5grVjfBkFArbt3lrP+pFkSdeiJxEPUgx+4nZ9gog744kyo5LEq3hI=",
            "my_app": "PSCqWTEJAst52ZjLzjv78vCj0eEUix0TNOzS", 
            "my_sec": "I9iBCx+BK++QFgq6mb6KPJj/x7I0jB/8L9xl79NGoFLvVknEpIST/yWwKuyoe9rwUIwAYVDmwip1+/ety0NTTtFrTNwV6Gym5sVRRN1r3iEC+/UsMN0POLH3Ba3OhwG96EqCCk2aI1CfOKS9AHf9i1lnPucAGOxGzXOVL2FqTsEZaUchOTI=",
            "my_acct_stock": "50157423",
            "my_prod": "01"
        }
    
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
            result = http_post(url, {"content-type": "application/json"}, body)
            
            logger.info(f"토큰 응답: {result}")
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.token_expires = datetime.now() + timedelta(hours=23)
                logger.info("✅ 액세스 토큰 발급 성공")
            elif result.get("error_code") == "EGW00133":
                logger.warning("⏰ API 요청 제한 - 1분 대기 후 재시도")
                time.sleep(60)
                return self._get_access_token()  # 재시도
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
            result = http_get(url, headers, params)
            
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
            result = http_get(url, headers, params)
            
            if result.get('rt_cd') == '0':
                return result
            else:
                logger.error(f"계좌 조회 실패: {result.get('msg1')}")
                return None
        except Exception as e:
            logger.error(f"계좌 조회 오류: {e}")
            return None
    
    def get_us_stock_price(self, symbol: str) -> dict:
        """미국 주식 현재가 조회"""
        self.rate_limiter.wait()
        
        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/price"
        headers = self._get_headers("HHDFS00000300")
        params = {
            "AUTH": "",
            "EXCD": "NAS",  # NASDAQ
            "SYMB": symbol
        }
        
        try:
            result = http_get(url, headers, params)
            
            if result.get('rt_cd') == '0':
                output = result['output']
                return {
                    'symbol': symbol,
                    'current_price': float(output['last']),
                    'change': float(output['diff']),
                    'change_rate': float(output['rate']),
                    'volume': int(output['tvol']) if output.get('tvol') else 0
                }
            else:
                logger.error(f"미국 주식 현재가 조회 실패: {result.get('msg1')}")
                return None
        except Exception as e:
            logger.error(f"미국 주식 현재가 조회 오류: {e}")
            return None
    
    def place_order(self, stock_code: str, quantity: int, direction: str, order_type: str = "01") -> dict:
        """한국 주식 매수/매도 주문"""
        self.rate_limiter.wait()
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
        tr_id = ("VTTC0802U" if self.paper_trading else "TTTC0802U") if direction == "BUY" else \
                ("VTTC0801U" if self.paper_trading else "TTTC0801U")
        
        body = {
            "CANO": self.config["my_acct_stock"],
            "ACNT_PRDT_CD": self.config["my_prod"],
            "PDNO": stock_code,
            "ORD_DVSN": order_type,
            "ORD_QTY": str(quantity),
            "ORD_UNPR": "0"  # 시장가
        }
        
        try:
            result = http_post(url, self._get_headers(tr_id), body)
            return result
        except Exception as e:
            logger.error(f"한국 주식 주문 오류: {e}")
            return {"rt_cd": "1", "msg1": str(e)}
    
    def place_us_order(self, symbol: str, quantity: int, price: float, direction: str) -> dict:
        """미국 주식 매수/매도 주문"""
        self.rate_limiter.wait()
        
        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/order"
        tr_id = ("VTTT1002U" if self.paper_trading else "JTTT1002U") if direction == "BUY" else \
                ("VTTT1001U" if self.paper_trading else "JTTT1001U")
        
        body = {
            "CANO": self.config["my_acct_stock"],
            "ACNT_PRDT_CD": self.config["my_prod"], 
            "OVRS_EXCG_CD": "NASD",
            "PDNO": symbol,
            "ORD_QTY": str(quantity),
            "OVRS_ORD_UNPR": str(price),
            "ORD_SVR_DVSN_CD": "0"
        }
        
        try:
            result = http_post(url, self._get_headers(tr_id), body)
            return result
        except Exception as e:
            logger.error(f"미국 주식 주문 오류: {e}")
            return {"rt_cd": "1", "msg1": str(e)}

class SimpleStrategy:
    """간단한 거래 전략 (한국/미국)"""
    
    def __init__(self, kr_symbols: List[str], us_symbols: List[str]):
        self.kr_symbols = kr_symbols  # 한국 주식
        self.us_symbols = us_symbols  # 미국 주식
        self.name = "Simple_Strategy"
    
    def generate_signals(self, broker: KISBroker, market_type: str = "KR") -> List[Dict]:
        """간단한 신호 생성 (한국/미국)"""
        signals = []
        
        # 현재 개장 중인 시장에 따라 종목 선택
        symbols = self.kr_symbols if market_type == "KR" else self.us_symbols
        
        for symbol in symbols:
            try:
                if market_type == "KR":
                    price_info = broker.get_stock_price(symbol)
                else:
                    price_info = broker.get_us_stock_price(symbol)
                    
                if price_info:
                    change_rate = price_info['change_rate']
                    
                    # 단순 신호 로직: 3% 이상 하락시 매수 신호
                    if change_rate < -3.0:
                        signals.append({
                            'symbol': symbol,
                            'action': 'BUY',
                            'reason': f'{market_type} 주식 {symbol} 하락률 {change_rate:.2f}%로 매수 신호',
                            'market': market_type
                        })
                
                time.sleep(0.2)  # API 호출 간격
                
            except Exception as e:
                logger.error(f"{market_type} 신호 생성 오류 ({symbol}): {e}")
        
        return signals

class TradingSystem:
    """AI 자동매매 시스템"""
    
    def __init__(self, config_path: str = None, paper_trading: bool = True):
        """초기화"""
        logger.info("=== AI 자동매매 시스템 초기화 ===")
        
        self.broker = KISBroker(config_path, paper_trading)
        # 한국 주식과 미국 주식 모니터링
        self.strategy = SimpleStrategy(
            kr_symbols=['005930', '000660'],  # 삼성전자, SK하이닉스
            us_symbols=['AAPL', 'TSLA', 'MSFT']  # 애플, 테슬라, 마이크로소프트
        )
        
        self.portfolio = {}
        self.cash_balance = 0
        self.total_value = 0
        self.is_running = False
        
        logger.info("AI 자동매매 시스템 초기화 완료")
    
    def log_monitoring_data(self, event_type: str, data: dict):
        """모니터링 데이터 JSON 로그"""
        monitoring_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        monitoring_logger.info(json.dumps(monitoring_data, ensure_ascii=False))
    
    async def execute_trade(self, signal: dict):
        """실제 매수/매도 실행"""
        try:
            symbol = signal['symbol']
            action = signal['action']
            market = signal['market']
            
            # 기본 주문 수량 계산 (포트폴리오의 1% 투자)
            order_amount = int(self.cash_balance * 0.01)
            
            if action == "BUY":
                if market == "KR":
                    # 한국 주식 현재가 조회
                    price_info = self.broker.get_stock_price(symbol)
                    if price_info:
                        current_price = price_info['current_price']
                        quantity = max(1, order_amount // current_price)
                        
                        logger.info(f"💰 한국 주식 매수 시도: {symbol} {quantity}주 @ {current_price:,}원")
                        
                        # 실제 매수 주문
                        result = self.broker.place_order(symbol, quantity, "BUY", "01")  # 시장가 주문
                        
                        if result and result.get('rt_cd') == '0':
                            logger.info(f"✅ 매수 성공: {symbol} {quantity}주")
                            self.log_monitoring_data("trade_success", {
                                "type": "BUY",
                                "market": "KR",
                                "symbol": symbol,
                                "quantity": quantity,
                                "price": current_price,
                                "amount": quantity * current_price
                            })
                        else:
                            logger.error(f"❌ 매수 실패: {symbol} - {result.get('msg1', 'Unknown error')}")
                            self.log_monitoring_data("trade_failure", {
                                "type": "BUY",
                                "market": "KR", 
                                "symbol": symbol,
                                "error": result.get('msg1', 'Unknown error')
                            })
                else:  # US 주식
                    # 미국 주식 현재가 조회
                    price_info = self.broker.get_us_stock_price(symbol)
                    if price_info:
                        current_price = price_info['current_price']
                        quantity = max(1, int(order_amount // (current_price * 1300)))  # 달러 환율 고려
                        
                        logger.info(f"💰 미국 주식 매수 시도: {symbol} {quantity}주 @ ${current_price:.2f}")
                        
                        # 실제 매수 주문
                        result = self.broker.place_us_order(symbol, quantity, current_price, "BUY")
                        
                        if result and result.get('rt_cd') == '0':
                            logger.info(f"✅ 미국 주식 매수 성공: {symbol} {quantity}주")
                            self.log_monitoring_data("trade_success", {
                                "type": "BUY",
                                "market": "US",
                                "symbol": symbol,
                                "quantity": quantity,
                                "price": current_price,
                                "amount": quantity * current_price
                            })
                        else:
                            logger.error(f"❌ 미국 주식 매수 실패: {symbol} - {result.get('msg1', 'Unknown error')}")
                            self.log_monitoring_data("trade_failure", {
                                "type": "BUY",
                                "market": "US",
                                "symbol": symbol, 
                                "error": result.get('msg1', 'Unknown error')
                            })
                            
        except Exception as e:
            logger.error(f"매매 실행 오류: {e}")
            self.log_monitoring_data("trade_error", {
                "symbol": symbol,
                "action": action,
                "error": str(e)
            })
    
    async def update_portfolio(self):
        """포트폴리오 상태 업데이트"""
        start_time = time.time()
        api_success = False
        
        try:
            balance_info = self.broker.get_balance()
            
            if balance_info and balance_info.get('rt_cd') == '0':
                api_success = True
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
        """장 개장 여부 확인 (한국/미국)"""
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour
        minute = now.minute
        
        # 한국 장: 평일 09:00 ~ 15:30
        if weekday < 5 and (9 <= hour < 15 or (hour == 15 and minute <= 30)):
            return True
        
        # 미국 장: 한국시간 기준
        # 서머타임 (3월 둘째 주일 ~ 11월 첫째 주일): 21:30 ~ 04:00
        # 일반시간: 22:30 ~ 05:00
        if self.is_us_summer_time():
            # 서머타임: 21:30 ~ 익일 04:00
            if weekday < 5 and hour >= 21 and minute >= 30:
                return True
            elif weekday < 6 and hour < 4:  # 익일 새벽
                return True
        else:
            # 일반시간: 22:30 ~ 익일 05:00
            if weekday < 5 and hour >= 22 and minute >= 30:
                return True
            elif weekday < 6 and hour < 5:  # 익일 새벽
                return True
        
        return False
    
    def is_us_summer_time(self) -> bool:
        """미국 서머타임 여부 확인"""
        now = datetime.now()
        year = now.year
        
        # 3월 둘째 주 일요일
        march = datetime(year, 3, 1)
        second_sunday_march = march + timedelta(days=(6-march.weekday() + 7))
        
        # 11월 첫째 주 일요일
        november = datetime(year, 11, 1)
        first_sunday_november = november + timedelta(days=(6-november.weekday()))
        
        return second_sunday_march <= now < first_sunday_november
    
    def get_market_type(self) -> str:
        """현재 개장 중인 시장 종류 반환"""
        now = datetime.now()
        hour = now.hour
        
        # 한국 장 시간
        if 9 <= hour < 16:
            return "KR"
        # 미국 장 시간
        elif hour >= 21 or hour < 6:
            return "US"
        else:
            return "CLOSED"
    
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
                        market_type = self.get_market_type()
                        market_name = "한국장" if market_type == "KR" else "미국장"
                        logger.info(f"📊 {market_name} 중 모니터링 - {current_time.strftime('%H:%M:%S')}")
                        
                        # 신호 생성 (현재 개장 중인 시장에 따라)
                        signals = self.strategy.generate_signals(self.broker, market_type)
                        
                        if signals:
                            logger.info(f"🎯 {market_name} {len(signals)}개 거래 신호 감지")
                            for signal in signals:
                                logger.info(f"   📈 {signal['market']} {signal['symbol']}: {signal['action']} - {signal['reason']}")
                                
                                # 실제 매수/매도 실행
                                await self.execute_trade(signal)
                        else:
                            logger.info(f"   📍 {market_name} 현재 거래 신호 없음")
                        
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

def main():
    """메인 함수"""
    print(f"""
╔══════════════════════════════════════════════════╗
║              🚀 AI 자동매매 시스템                 ║
║                                                  ║
║  시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                    ║
╚══════════════════════════════════════════════════╝
    """)
    
    try:
        # 프롬프트 요구사항: 모의투자 모드로 자동 설정
        print("\n✅ 프롬프트 요구사항에 따라 모의투자 모드로 자동 초기화합니다...")
        trading_system = TradingSystem(paper_trading=True)
        
        print(f"""
╔══════════════════════════════════════════════════╗
║  초기화 완료 - 모의투자 모드                        ║
║  프롬프트 요구사항에 따라 자동으로 24시간 모니터링 시작  ║
╚══════════════════════════════════════════════════╝
        """)
        
        print("\n🚀 24시간 모니터링을 시작합니다...")
        print("📊 한국장/미국장 자동 감지 및 모니터링")
        print("⚠️  모니터링 중지: Ctrl+C")
        print("=" * 60)
        
        try:
            asyncio.run(trading_system.run())
        except KeyboardInterrupt:
            print("\n⏹️  모니터링이 중지되었습니다.")
        
    except Exception as e:
        print(f"\n❌ 시스템 오류: {e}")
        logger.error(f"시스템 오류: {e}")

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
        # 프롬프트 요구사항: 모의투자 모드로 자동 설정
        print("\n✅ 프롬프트 요구사항에 따라 모의투자 모드로 자동 초기화합니다...")
        trading_system = TradingSystem(paper_trading=True)
        
        print(f"""
╔══════════════════════════════════════════════════╗
║  초기화 완료 - 모의투자 모드                        ║
║  프롬프트 요구사항에 따라 자동으로 24시간 모니터링 시작  ║
╚══════════════════════════════════════════════════╝
        """)
        
        print("\n🚀 24시간 모니터링을 시작합니다...")
        print("📊 한국장/미국장 자동 감지 및 모니터링")
        print("⚠️  모니터링 중지: Ctrl+C")
        print("=" * 60)
        
        try:
            asyncio.run(trading_system.run())
        except KeyboardInterrupt:
            print("\n⏹️  모니터링이 중지되었습니다.")
        
    except Exception as e:
        print(f"\n❌ 시스템 오류: {e}")
        logger.error(f"시스템 오류: {e}")

if __name__ == "__main__":
    main()
