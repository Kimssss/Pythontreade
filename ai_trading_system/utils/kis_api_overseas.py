#!/usr/bin/env python3
"""
한국투자증권 해외주식 API 확장 모듈
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import time

# 로거 설정
api_logger = logging.getLogger('kis_api')


class KisAPIOverseas:
    """한국투자증권 해외주식 API 확장 클래스"""
    
    def __init__(self, kis_api_instance):
        """
        Args:
            kis_api_instance: KisAPIEnhanced 인스턴스
        """
        self.api = kis_api_instance
        
        # 지원 거래소 정보 (한국투자증권 API는 미국 시장만 지원)
        self.EXCHANGES = {
            "NASD": {"name": "나스닥", "currency": "USD", "code": "NAS"},
            "NYSE": {"name": "뉴욕증권거래소", "currency": "USD", "code": "NYS"},
            "AMEX": {"name": "아멕스", "currency": "USD", "code": "AMS"}
        }
    
    def get_overseas_price(self, exchange: str, symbol: str) -> Optional[Dict]:
        """해외주식 현재가 조회
        
        Args:
            exchange: 거래소 코드 (NASD, NYSE, AMEX 등)
            symbol: 종목 심볼 (AAPL, MSFT 등)
        
        Returns:
            현재가 정보 딕셔너리
        """
        if not self.api.ensure_valid_token():
            return None
            
        if exchange not in self.EXCHANGES:
            api_logger.error(f"지원하지 않는 거래소: {exchange}")
            return None
        
        exchange_info = self.EXCHANGES[exchange]
        url = f"{self.api.base_url}/uapi/overseas-price/v1/quotations/price"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.api.access_token}",
            "appkey": self.api.appkey,
            "appsecret": self.api.appsecret,
            "tr_id": "HHDFS00000300"  # 해외주식 현재가
        }
        
        params = {
            "AUTH": "",
            "EXCD": exchange_info["code"],  # 거래소 코드
            "SYMB": symbol  # 종목 심볼
        }
        
        response = self.api._make_api_request_with_retry(
            'GET', url, headers=headers, params=params, 
            endpoint_name="overseas_price"
        )
        
        if response:
            result = response.json()
            if result.get('rt_cd') == '0':
                output = result.get('output', {})
                return {
                    'symbol': symbol,
                    'exchange': exchange,
                    'currency': exchange_info["currency"],
                    'current_price': float(output.get('last', 0)),
                    'change': float(output.get('diff', 0)),
                    'change_rate': float(output.get('rate', 0)),
                    'volume': int(output.get('tvol', 0)),
                    'high': float(output.get('high', 0)),
                    'low': float(output.get('low', 0)),
                    'open': float(output.get('open', 0))
                }
        return None
    
    def get_overseas_balance(self, exchange: str = "ALL") -> Optional[Dict]:
        """해외주식 잔고 조회
        
        Args:
            exchange: 거래소 코드 (ALL: 전체)
        
        Returns:
            잔고 정보
        """
        if not self.api.ensure_valid_token():
            return None
        
        url = f"{self.api.base_url}/uapi/overseas-stock/v1/trading/inquire-balance"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.api.access_token}",
            "appkey": self.api.appkey,
            "appsecret": self.api.appsecret,
            "tr_id": "VTTS3012R" if not self.api.is_real else "TTTS3012R"
        }
        
        # 계좌번호 처리
        account_parts = self._parse_account_number()
        
        params = {
            "CANO": account_parts[0],
            "ACNT_PRDT_CD": account_parts[1],
            "OVRS_EXCG_CD": exchange if exchange != "ALL" else "NASD",
            "TR_CRCY_CD": "USD",  # 기본 USD
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        
        response = self.api._make_api_request_with_retry(
            'GET', url, headers=headers, params=params,
            endpoint_name="overseas_balance"
        )
        
        if response:
            result = response.json()
            if result.get('rt_cd') == '0':
                holdings = []
                for item in result.get('output1', []):
                    holdings.append({
                        'exchange': item.get('ovrs_excg_cd'),
                        'symbol': item.get('ovrs_pdno'),
                        'name': item.get('ovrs_item_name'),
                        'quantity': int(item.get('ovrs_cblc_qty', 0)),
                        'avg_price': float(item.get('pchs_avg_pric', 0)),
                        'current_price': float(item.get('now_pric2', 0)),
                        'eval_amount': float(item.get('ovrs_stck_evlu_amt', 0)),
                        'profit_loss': float(item.get('frcr_evlu_pfls_amt', 0)),
                        'profit_rate': float(item.get('evlu_pfls_rt', 0)),
                        'currency': item.get('tr_crcy_cd')
                    })
                
                balance = result.get('output2', {})
                return {
                    'holdings': holdings,
                    'total_eval_amount': float(balance.get('tot_evlu_pfls_amt', 0)),
                    'foreign_currency_amount': float(balance.get('frcr_dncl_amt_1', 0)),
                    'currency': 'USD'  # 기본 통화
                }
        return None
    
    def get_overseas_available_cash(self, currency: str = "USD") -> float:
        """해외주식 주문 가능 현금 조회
        
        Args:
            currency: 통화 코드 (USD, HKD, JPY 등)
        
        Returns:
            주문 가능 현금
        """
        balance = self.get_overseas_balance()
        if balance:
            return balance.get('foreign_currency_amount', 0)
        return 0
    
    def buy_overseas_stock(self, exchange: str, symbol: str, quantity: int, 
                          price: float = 0, order_type: str = "00") -> Optional[Dict]:
        """해외주식 매수 주문
        
        Args:
            exchange: 거래소 코드
            symbol: 종목 심볼
            quantity: 주문 수량
            price: 주문 가격 (0이면 시장가)
            order_type: "00" 시장가, "32" 지정가
        
        Returns:
            주문 결과
        """
        if not self.api.ensure_valid_token():
            return None
            
        if exchange not in self.EXCHANGES:
            api_logger.error(f"지원하지 않는 거래소: {exchange}")
            return None
        
        url = f"{self.api.base_url}/uapi/overseas-stock/v1/trading/order"
        
        # 계좌번호 처리
        account_parts = self._parse_account_number()
        
        # 주문 데이터
        data = {
            "CANO": account_parts[0],
            "ACNT_PRDT_CD": account_parts[1],
            "OVRS_EXCG_CD": exchange,
            "PDNO": symbol,
            "ORD_QTY": str(quantity),
            "OVRS_ORD_UNPR": str(price) if order_type == "32" else "0",
            "ORD_SVR_DVSN_CD": "0",  # 일반주문
            "ORD_DVSN": order_type   # 주문구분
        }
        
        # 해시키 생성
        hashkey = self.api._get_hashkey(data)
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.api.access_token}",
            "appkey": self.api.appkey,
            "appsecret": self.api.appsecret,
            "tr_id": "VTTT1002U" if getattr(self.api, 'mode', 'demo') == 'demo' else "TTTT1002U",  # 해외주식 매수
            "custtype": "P",
            "hashkey": hashkey
        }
        
        api_logger.info(f"해외주식 매수 주문: {exchange} {symbol} x {quantity}")
        
        response = self.api._make_api_request_with_retry(
            'POST', url, headers=headers, data=data,
            endpoint_name="overseas_order"
        )
        
        if response:
            return response.json()
        return None
    
    def sell_overseas_stock(self, exchange: str, symbol: str, quantity: int,
                           price: float = 0, order_type: str = "00") -> Optional[Dict]:
        """해외주식 매도 주문
        
        Args:
            exchange: 거래소 코드
            symbol: 종목 심볼
            quantity: 주문 수량
            price: 주문 가격 (0이면 시장가)
            order_type: "00" 시장가, "32" 지정가
        
        Returns:
            주문 결과
        """
        if not self.api.ensure_valid_token():
            return None
            
        if exchange not in self.EXCHANGES:
            api_logger.error(f"지원하지 않는 거래소: {exchange}")
            return None
        
        url = f"{self.api.base_url}/uapi/overseas-stock/v1/trading/order"
        
        # 계좌번호 처리
        account_parts = self._parse_account_number()
        
        # 주문 데이터
        data = {
            "CANO": account_parts[0],
            "ACNT_PRDT_CD": account_parts[1],
            "OVRS_EXCG_CD": exchange,
            "PDNO": symbol,
            "ORD_QTY": str(quantity),
            "OVRS_ORD_UNPR": str(price) if order_type == "32" else "0",
            "ORD_SVR_DVSN_CD": "0",
            "ORD_DVSN": order_type
        }
        
        # 해시키 생성
        hashkey = self.api._get_hashkey(data)
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.api.access_token}",
            "appkey": self.api.appkey,
            "appsecret": self.api.appsecret,
            "tr_id": "VTTT1001U" if getattr(self.api, 'mode', 'demo') == 'demo' else "TTTT1001U",  # 해외주식 매도
            "custtype": "P",
            "hashkey": hashkey
        }
        
        api_logger.info(f"해외주식 매도 주문: {exchange} {symbol} x {quantity}")
        
        response = self.api._make_api_request_with_retry(
            'POST', url, headers=headers, data=data,
            endpoint_name="overseas_order"
        )
        
        if response:
            return response.json()
        return None
    
    def get_overseas_daily_price(self, exchange: str, symbol: str, 
                                period: str = "D", count: int = 30) -> Optional[List[Dict]]:
        """해외주식 일봉/주봉/월봉 데이터 조회
        
        Args:
            exchange: 거래소 코드
            symbol: 종목 심볼
            period: "D" 일봉, "W" 주봉, "M" 월봉
            count: 조회 개수
        
        Returns:
            가격 데이터 리스트
        """
        if not self.api.ensure_valid_token():
            return None
            
        if exchange not in self.EXCHANGES:
            api_logger.error(f"지원하지 않는 거래소: {exchange}")
            return None
        
        exchange_info = self.EXCHANGES[exchange]
        url = f"{self.api.base_url}/uapi/overseas-price/v1/quotations/dailyprice"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.api.access_token}",
            "appkey": self.api.appkey,
            "appsecret": self.api.appsecret,
            "tr_id": "HHDFS76240000"  # 해외주식 일별 시세
        }
        
        # 오늘 날짜
        end_date = datetime.now().strftime("%Y%m%d")
        
        params = {
            "AUTH": "",
            "EXCD": exchange_info["code"],
            "SYMB": symbol,
            "GUBN": "0",  # 일/주/월 구분 (0: 일봉)
            "BYMD": end_date,  # 종료일자
            "MODP": "0"  # 수정주가 여부
        }
        
        response = self.api._make_api_request_with_retry(
            'GET', url, headers=headers, params=params,
            endpoint_name="overseas_daily_price"
        )
        
        if response:
            result = response.json()
            if result.get('rt_cd') == '0':
                price_list = []
                for item in result.get('output2', [])[:count]:
                    price_list.append({
                        'date': item.get('xymd'),
                        'open': float(item.get('open', 0)),
                        'high': float(item.get('high', 0)),
                        'low': float(item.get('low', 0)),
                        'close': float(item.get('clos', 0)),
                        'volume': int(item.get('tvol', 0))
                    })
                return price_list
        return None
    
    def _parse_account_number(self) -> List[str]:
        """계좌번호 파싱"""
        if '-' in self.api.account_no:
            return self.api.account_no.split('-')
        else:
            # 계좌번호가 하이픈 없이 연결된 경우
            return [self.api.account_no[:8], self.api.account_no[8:]]
    
    def get_overseas_holdings(self) -> Optional[Dict]:
        """해외주식 보유종목 조회"""
        if not self.api.ensure_valid_token():
            return None
            
        url = f"{self.api.base_url}/uapi/overseas-stock/v1/trading/inquire-balance"
        
        headers = {
            "authorization": f"Bearer {self.api.access_token}",
            "appkey": self.api.appkey,
            "appsecret": self.api.appsecret,
            "tr_id": "TTTS3012R",
            "custtype": "P",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        params = {
            "CANO": self.api.account_no.replace('-', '')[:8],
            "ACNT_PRDT_CD": self.api.account_no.split('-')[1],
            "OVRS_EXCG_CD": "NASD",  # 기본값으로 나스닥
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        
        try:
            response = self.api._make_api_request_with_retry(
                'GET', url, headers=headers, params=params,
                endpoint_name="overseas_holdings"
            )
            if response:
                return response.json()
            return None
        except Exception as e:
            api_logger.error(f"해외 보유종목 조회 실패: {e}")
            return None
    
    def get_overseas_balance(self) -> Optional[Dict]:
        """해외 계좌 잔고 조회"""
        if not self.api.ensure_valid_token():
            return None
            
        # 데모 모드는 다른 TR_ID 사용
        mode = getattr(self.api, 'mode', 'demo')  # KisAPIEnhanced에 mode가 없으면 demo로 가정
        if mode == 'demo':
            tr_id = "VTTS3007R"  # 모의투자용 TR_ID
        else:
            tr_id = "TTTS3007R"  # 실전용 TR_ID
            
        url = f"{self.api.base_url}/uapi/overseas-stock/v1/trading/inquire-psamount"
        
        headers = {
            "authorization": f"Bearer {self.api.access_token}",
            "appkey": self.api.appkey,
            "appsecret": self.api.appsecret,
            "tr_id": tr_id,
            "custtype": "P",
            "Content-Type": "application/json; charset=utf-8"
        }
        
        params = {
            "CANO": self.api.account_no.replace('-', '')[:8],
            "ACNT_PRDT_CD": self.api.account_no.split('-')[1],
            "OVRS_EXCG_CD": "NASD",
            "OVRS_ORD_UNPR": "",
            "ITEM_CD": ""
        }
        
        try:
            response = self.api._make_api_request_with_retry(
                'GET', url, headers=headers, params=params,
                endpoint_name="overseas_balance_check"
            )
            if not response:
                return None
            result = response.json()
            if result.get('rt_cd') == '0':
                return result
            else:
                api_logger.warning(f"해외 잔고 조회 실패: {result.get('msg1', 'Unknown error')}")
                # 데모 모드에서는 가상 잔고 반환
                if mode == 'demo':
                    return {'foreign_currency_amount': 10000.0}  # 가상 $10,000
                return None
        except Exception as e:
            api_logger.error(f"해외 잔고 조회 실패: {e}")
            # 데모 모드에서는 가상 잔고 반환
            if mode == 'demo':
                return {'foreign_currency_amount': 10000.0}  # 가상 $10,000
            return None