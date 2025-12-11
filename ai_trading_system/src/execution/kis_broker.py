#!/usr/bin/env python3
"""
한국투자증권 API 브로커 클래스
실시간 데이터 수집 및 주문 실행
"""

import yaml
import requests
import asyncio
import websockets
import json
import time
import threading
import hashlib
import hmac
import logging
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional

# 로거 설정
logger = logging.getLogger('kis_broker')
logger.setLevel(logging.INFO)

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
    
    PRODUCTION_URL = "https://openapi.koreainvestment.com:9443"
    PAPER_URL = "https://openapivts.koreainvestment.com:29443"
    WS_PRODUCTION = "ws://ops.koreainvestment.com:21000"
    WS_PAPER = "ws://ops.koreainvestment.com:31000"
    
    def __init__(self, config_path: str, paper_trading: bool = True):
        """초기화
        
        Args:
            config_path: 설정 파일 경로
            paper_trading: 모의투자 여부
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.paper_trading = paper_trading
        self.base_url = self.PAPER_URL if paper_trading else self.PRODUCTION_URL
        self.ws_url = self.WS_PAPER if paper_trading else self.WS_PRODUCTION
        self.rate_limiter = RateLimiter(max_calls=15, period=1.0)
        
        self.access_token = None
        self.token_expires = None
        self.approval_key = None
        
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
        
        headers = {"content-type": "application/json"}
        
        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            
            result = response.json()
            self.access_token = result["access_token"]
            self.token_expires = datetime.now() + timedelta(hours=23)
            
            logger.info("액세스 토큰 발급 성공")
            
        except Exception as e:
            logger.error(f"토큰 발급 실패: {e}")
            raise
    
    def _get_websocket_approval(self):
        """웹소켓 승인키 발급"""
        url = f"{self.base_url}/oauth2/Approval"
        key_prefix = "paper" if self.paper_trading else "my"
        
        body = {
            "grant_type": "client_credentials",
            "appkey": self.config[f"{key_prefix}_app"],
            "secretkey": self.config[f"{key_prefix}_sec"]
        }
        
        headers = {"content-type": "application/json"}
        
        try:
            response = requests.post(url, headers=headers, json=body)
            result = response.json()
            self.approval_key = result["approval_key"]
            logger.info("웹소켓 승인키 발급 성공")
            
        except Exception as e:
            logger.error(f"웹소켓 승인키 발급 실패: {e}")
    
    def _get_headers(self, tr_id: str, hashkey: str = "") -> Dict:
        """API 헤더 생성"""
        if not self.access_token or datetime.now() >= self.token_expires:
            self._get_access_token()
        
        key_prefix = "paper" if self.paper_trading else "my"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config[f"{key_prefix}_app"],
            "appsecret": self.config[f"{key_prefix}_sec"],
            "tr_id": tr_id,
            "custtype": "P"
        }
        
        if hashkey:
            headers["hashkey"] = hashkey
        
        return headers
    
    def _get_hashkey(self, data: Dict) -> str:
        """해시키 생성"""
        url = f"{self.base_url}/uapi/hashkey"
        headers = {
            "content-type": "application/json",
            "appkey": self.config["paper_app" if self.paper_trading else "my_app"],
            "appsecret": self.config["paper_sec" if self.paper_trading else "my_sec"]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            return response.json()["HASH"]
        except Exception as e:
            logger.error(f"해시키 생성 실패: {e}")
            return ""
    
    def get_stock_price(self, stock_code: str) -> Optional[Dict]:
        """주식 현재가 조회
        
        Args:
            stock_code: 종목코드
            
        Returns:
            현재가 정보
        """
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
                    'volume': int(output['acml_vol']),
                    'high': int(output['stck_hgpr']),
                    'low': int(output['stck_lwpr']),
                    'open': int(output['stck_oprc'])
                }
            else:
                logger.error(f"주식 현재가 조회 실패: {result.get('msg1')}")
                return None
                
        except Exception as e:
            logger.error(f"주식 현재가 조회 오류: {e}")
            return None
    
    def place_order(self, stock_code: str, quantity: int, direction: str, 
                   order_type: str = "01", price: int = 0) -> Optional[Dict]:
        """주식 주문
        
        Args:
            stock_code: 종목코드
            quantity: 주문수량  
            direction: BUY/SELL
            order_type: 01(지정가), 03(시장가)
            price: 주문가격
            
        Returns:
            주문 결과
        """
        self.rate_limiter.wait()
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
        
        # TR_ID 설정
        if direction.upper() == "BUY":
            tr_id = "VTTC0802U" if self.paper_trading else "TTTC0802U"
        else:
            tr_id = "VTTC0801U" if self.paper_trading else "TTTC0801U"
        
        body = {
            "CANO": self.config["my_acct_stock"],
            "ACNT_PRDT_CD": self.config["my_prod"],
            "PDNO": stock_code,
            "ORD_DVSN": order_type,
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price)
        }
        
        hashkey = self._get_hashkey(body)
        headers = self._get_headers(tr_id, hashkey)
        
        try:
            response = requests.post(url, headers=headers, json=body)
            result = response.json()
            
            if result.get('rt_cd') == '0':
                logger.info(f"주문 성공: {stock_code} {direction} {quantity}주 @ {price}원")
                return result
            else:
                logger.error(f"주문 실패: {result.get('msg1')}")
                return None
                
        except Exception as e:
            logger.error(f"주문 오류: {e}")
            return None
    
    def get_balance(self) -> Optional[Dict]:
        """계좌 잔고 조회
        
        Returns:
            계좌 정보
        """
        self.rate_limiter.wait()
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        tr_id = "VTTC8434R" if self.paper_trading else "TTTC8434R"
        
        headers = self._get_headers(tr_id)
        params = {
            "CANO": self.config["my_acct_stock"],
            "ACNT_PRDT_CD": self.config["my_prod"],
            "AFHR_FLPR_YN": "N",
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
    
    def get_daily_price(self, stock_code: str, period: str = "D", count: int = 100) -> Optional[List[Dict]]:
        """일별 시세 조회
        
        Args:
            stock_code: 종목코드
            period: 기간 (D, W, M)
            count: 조회 개수
            
        Returns:
            일별 시세 데이터
        """
        self.rate_limiter.wait()
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        headers = self._get_headers("FHKST03010100")
        
        end_date = datetime.now().strftime("%Y%m%d")
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
            "FID_INPUT_DATE_1": "19000101",
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": period
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            
            if result.get('rt_cd') == '0':
                output = result.get('output2', [])[:count]
                data = []
                
                for item in output:
                    data.append({
                        'date': item['stck_bsop_date'],
                        'open': int(item['stck_oprc']),
                        'high': int(item['stck_hgpr']),
                        'low': int(item['stck_lwpr']),
                        'close': int(item['stck_clpr']),
                        'volume': int(item['acml_vol']),
                        'amount': int(item['acml_tr_pbmn'])
                    })
                
                return sorted(data, key=lambda x: x['date'])
            else:
                logger.error(f"일별 시세 조회 실패: {result.get('msg1')}")
                return None
                
        except Exception as e:
            logger.error(f"일별 시세 조회 오류: {e}")
            return None
    
    def get_top_volume_stocks(self, count: int = 100) -> Optional[List[Dict]]:
        """거래량 상위 종목 조회
        
        Args:
            count: 조회 개수
            
        Returns:
            거래량 상위 종목 목록
        """
        self.rate_limiter.wait()
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/volume-rank"
        headers = self._get_headers("FHPST01710000")
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_COND_SCR_DIV_CODE": "20171",
            "FID_INPUT_ISCD": "0000",
            "FID_DIV_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "0",
            "FID_TRGT_CLS_CODE": "111111111",
            "FID_TRGT_EXLS_CLS_CODE": "0000000000",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",
            "FID_INPUT_DATE_1": ""
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            result = response.json()
            
            if result.get('rt_cd') == '0':
                output = result.get('output', [])[:count]
                stocks = []
                
                for item in output:
                    stocks.append({
                        'code': item['mksc_shrn_iscd'],
                        'name': item['hts_kor_isnm'],
                        'current_price': int(item['stck_prpr']),
                        'change_rate': float(item['prdy_ctrt']),
                        'volume': int(item['acml_vol']),
                        'amount': int(item['acml_tr_pbmn'])
                    })
                
                return stocks
            else:
                logger.error(f"거래량 상위 종목 조회 실패: {result.get('msg1')}")
                return None
                
        except Exception as e:
            logger.error(f"거래량 상위 종목 조회 오류: {e}")
            return None