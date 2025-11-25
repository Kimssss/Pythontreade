import requests
import json
import hashlib
import hmac
import base64
from datetime import datetime

class KisAPI:
    def __init__(self, appkey, appsecret, account_no, is_real=False):
        """
        한국투자증권 API 클래스
        
        Args:
            appkey (str): API Key
            appsecret (str): API Secret
            account_no (str): 계좌번호
            is_real (bool): 실전투자 여부 (True: 실전, False: 모의)
        """
        self.appkey = appkey
        self.appsecret = appsecret
        self.account_no = account_no
        self.is_real = is_real
        
        # URL 설정
        if is_real:
            self.base_url = "https://openapi.koreainvestment.com:9443"
        else:
            self.base_url = "https://openapivts.koreainvestment.com:29443"
        
        self.access_token = None
        
    def get_access_token(self):
        """액세스 토큰 발급"""
        url = f"{self.base_url}/oauth2/tokenP"
        
        headers = {
            "content-type": "application/json"
        }
        
        body = {
            "grant_type": "client_credentials",
            "appkey": self.appkey,
            "appsecret": self.appsecret
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(body))
            response.raise_for_status()
            
            result = response.json()
            if 'access_token' in result:
                self.access_token = result['access_token']
                print(f"토큰 발급 성공: {self.access_token[:20]}...")
                return True
            else:
                print(f"토큰 발급 실패: {result}")
                return False
                
        except Exception as e:
            print(f"토큰 발급 중 오류 발생: {e}")
            return False
    
    def get_hashkey(self, data):
        """해시키 생성"""
        url = f"{self.base_url}/uapi/hashkey"
        
        headers = {
            "content-type": "application/json",
            "appKey": self.appkey,
            "appSecret": self.appsecret
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            
            result = response.json()
            return result.get('HASH', '')
            
        except Exception as e:
            print(f"해시키 생성 중 오류 발생: {e}")
            return ""
    
    def get_balance(self):
        """계좌 잔고 조회"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "VTTC8434R" if not self.is_real else "TTTC8434R"
        }
        
        params = {
            "CANO": self.account_no.split('-')[0],
            "ACNT_PRDT_CD": self.account_no.split('-')[1],
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
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except Exception as e:
            print(f"잔고 조회 중 오류 발생: {e}")
            return None
    
    def get_stock_price(self, stock_code):
        """주식 현재가 조회"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "FHKST01010100"
        }
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except Exception as e:
            print(f"주식 현재가 조회 중 오류 발생: {e}")
            return None
    
    def buy_stock(self, stock_code, quantity, price=0, order_type="01"):
        """주식 매수 주문"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
        
        order_data = {
            "CANO": self.account_no.split('-')[0],
            "ACNT_PRDT_CD": self.account_no.split('-')[1],
            "PDNO": stock_code,
            "ORD_DVSN": order_type,  # 01: 지정가, 03: 시장가
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price) if price > 0 else "0"
        }
        
        hashkey = self.get_hashkey(order_data)
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "VTTC0802U" if not self.is_real else "TTTC0802U",
            "hashkey": hashkey
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(order_data))
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except Exception as e:
            print(f"매수 주문 중 오류 발생: {e}")
            return None
    
    def sell_stock(self, stock_code, quantity, price=0, order_type="01"):
        """주식 매도 주문"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
        
        order_data = {
            "CANO": self.account_no.split('-')[0],
            "ACNT_PRDT_CD": self.account_no.split('-')[1],
            "PDNO": stock_code,
            "ORD_DVSN": order_type,  # 01: 지정가, 03: 시장가
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price) if price > 0 else "0"
        }
        
        hashkey = self.get_hashkey(order_data)
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "VTTC0801U" if not self.is_real else "TTTC0801U",
            "hashkey": hashkey
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(order_data))
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except Exception as e:
            print(f"매도 주문 중 오류 발생: {e}")
            return None
    
    def get_orders(self):
        """주문 내역 조회"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-psbl-order"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "VTTC8001R" if not self.is_real else "TTTC8001R"
        }
        
        params = {
            "CANO": self.account_no.split('-')[0],
            "ACNT_PRDT_CD": self.account_no.split('-')[1],
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
            "INQR_DVSN_1": "0",
            "INQR_DVSN_2": "0"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except Exception as e:
            print(f"주문 내역 조회 중 오류 발생: {e}")
            return None

# 사용 예시
if __name__ == "__main__":
    from config import Config
    
    # 환경 변수에서 계좌 정보 로드
    real_account_info = Config.get_account_info('real')
    demo_account_info = Config.get_account_info('demo')
    
    print("=== 모의투자 계좌 테스트 ===")
    demo_api = KisAPI(
        demo_account_info['appkey'], 
        demo_account_info['appsecret'], 
        demo_account_info['account'], 
        is_real=False
    )
    
    # 토큰 발급 테스트
    if demo_api.get_access_token():
        print("모의투자 토큰 발급 성공!")
        
        # 잔고 조회 테스트
        balance = demo_api.get_balance()
        if balance:
            print("모의투자 잔고 조회 성공!")
        
        # 삼성전자 현재가 조회 테스트
        price = demo_api.get_stock_price("005930")
        if price:
            print("삼성전자 현재가 조회 성공!")
    
    print("\n=== 실전투자 계좌 테스트 ===")
    real_api = KisAPI(
        real_account_info['appkey'], 
        real_account_info['appsecret'], 
        real_account_info['account'], 
        is_real=True
    )
    
    # 토큰 발급 테스트
    if real_api.get_access_token():
        print("실전투자 토큰 발급 성공!")
        
        # 잔고 조회 테스트  
        balance = real_api.get_balance()
        if balance:
            print("실전투자 잔고 조회 성공!")
    
    print("\n=== 매매 기능 테스트 (모의투자) ===")
    # 삼성전자 1주 매수 테스트 (시장가)
    buy_result = demo_api.buy_stock("005930", 1, order_type="03")
    if buy_result and buy_result.get('rt_cd') == '0':
        print("매수 주문 성공!")
        print(f"주문번호: {buy_result.get('output', {}).get('ODNO', 'N/A')}")
    else:
        print("매수 주문 실패:", buy_result)
    
    # 주문 내역 조회
    orders = demo_api.get_orders()
    if orders:
        print("주문 내역 조회 성공!")