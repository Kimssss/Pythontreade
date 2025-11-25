import requests
import json
import time
from datetime import datetime

class USStockAPI:
    def __init__(self, appkey, appsecret, account_no, is_real=False):
        """
        미국주식 API 클래스
        
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
        self.token_expires = None
        
    def get_access_token(self, retry_count=3):
        """액세스 토큰 발급"""
        # 토큰이 있고 아직 유효하면 재사용
        if self.access_token and self.token_expires:
            if datetime.now() < self.token_expires:
                return True
        
        url = f"{self.base_url}/oauth2/tokenP"
        
        headers = {
            "content-type": "application/json"
        }
        
        body = {
            "grant_type": "client_credentials",
            "appkey": self.appkey,
            "appsecret": self.appsecret
        }
        
        for attempt in range(retry_count):
            try:
                print(f"토큰 발급 시도 {attempt + 1}/{retry_count}...")
                response = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'access_token' in result:
                        self.access_token = result['access_token']
                        # 토큰 만료 시간 설정 (24시간 - 안전마진 1시간)
                        import datetime
                        self.token_expires = datetime.datetime.now() + datetime.timedelta(hours=23)
                        print(f"토큰 발급 성공: {self.access_token[:20]}...")
                        return True
                    else:
                        print(f"토큰 발급 실패: {result}")
                        return False
                elif response.status_code == 403:
                    error_data = response.json()
                    error_code = error_data.get('error_code', '')
                    if 'EGW00133' in error_code:  # 1분당 1회 제한
                        print(f"토큰 발급 제한 (1분당 1회) - 60초 대기...")
                        if attempt < retry_count - 1:
                            time.sleep(60)
                            continue
                    print(f"403 오류 - API 키나 권한을 확인하세요: {response.text}")
                    return False
                else:
                    response.raise_for_status()
                
            except requests.exceptions.Timeout:
                print(f"타임아웃 오류 (시도 {attempt + 1}/{retry_count})")
                if attempt < retry_count - 1:
                    time.sleep(2)
                    continue
            except Exception as e:
                print(f"토큰 발급 중 오류 발생: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2)
                    continue
        
        return False
    
    def get_us_stock_price(self, symbol, exchange="NAS"):
        """미국주식 현재가 조회
        
        Args:
            symbol (str): 종목 심볼 (예: AAPL, TSLA)
            exchange (str): 거래소 (NAS=나스닥, NYS=뉴욕증권거래소)
        """
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        url = f"{self.base_url}/uapi/overseas-price/v1/quotations/price"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "HHDFS00000300"
        }
        
        params = {
            "AUTH": "",
            "EXCD": exchange,
            "SYMB": symbol
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except Exception as e:
            print(f"미국주식 현재가 조회 중 오류 발생: {e}")
            return None
    
    def get_us_stock_balance(self):
        """미국주식 계좌 잔고 조회"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/inquire-balance"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "VTRP6504R" if not self.is_real else "CTRP6504R"
        }
        
        params = {
            "CANO": self.account_no.split('-')[0],
            "ACNT_PRDT_CD": self.account_no.split('-')[1],
            "OVRS_EXCG_CD": "NASD",
            "TR_CRCY_CD": "USD",
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": ""
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except Exception as e:
            print(f"미국주식 잔고 조회 중 오류 발생: {e}")
            return None
    
    def buy_us_stock(self, symbol, quantity, price=0, order_type="00"):
        """미국주식 매수 주문
        
        Args:
            symbol (str): 종목 심볼
            quantity (int): 수량
            price (float): 주문가격 (0이면 시장가)
            order_type (str): 주문구분 (00=지정가, 32=시장가)
        """
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/order"
        
        order_data = {
            "CANO": self.account_no.split('-')[0],
            "ACNT_PRDT_CD": self.account_no.split('-')[1],
            "OVRS_EXCG_CD": "NASD",  # 나스닥
            "PDNO": symbol,
            "ORD_QTY": str(quantity),
            "OVRS_ORD_UNPR": str(price) if price > 0 else "0",
            "ORD_SVR_DVSN_CD": "0",
            "ORD_DVSN": order_type
        }
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "VTTT1002U" if not self.is_real else "JTTT1002U"
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(order_data))
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except Exception as e:
            print(f"미국주식 매수 주문 중 오류 발생: {e}")
            return None
    
    def sell_us_stock(self, symbol, quantity, price=0, order_type="00"):
        """미국주식 매도 주문"""
        if not self.access_token:
            if not self.get_access_token():
                return None
        
        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/order"
        
        order_data = {
            "CANO": self.account_no.split('-')[0],
            "ACNT_PRDT_CD": self.account_no.split('-')[1],
            "OVRS_EXCG_CD": "NASD",  # 나스닥
            "PDNO": symbol,
            "ORD_QTY": str(quantity),
            "OVRS_ORD_UNPR": str(price) if price > 0 else "0",
            "ORD_SVR_DVSN_CD": "0",
            "ORD_DVSN": order_type
        }
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "VTTT1001U" if not self.is_real else "JTTT1001U"  # 매도용 TR_ID
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(order_data))
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except Exception as e:
            print(f"미국주식 매도 주문 중 오류 발생: {e}")
            return None
    
    def search_us_stock(self, keyword):
        """미국주식 종목 검색 (인기 종목 매핑)"""
        popular_stocks = {
            "애플": "AAPL", "apple": "AAPL", "aapl": "AAPL",
            "테슬라": "TSLA", "tesla": "TSLA", "tsla": "TSLA", 
            "마이크로소프트": "MSFT", "microsoft": "MSFT", "msft": "MSFT",
            "구글": "GOOGL", "google": "GOOGL", "googl": "GOOGL", "alphabet": "GOOGL",
            "아마존": "AMZN", "amazon": "AMZN", "amzn": "AMZN",
            "메타": "META", "meta": "META", "facebook": "META",
            "엔비디아": "NVDA", "nvidia": "NVDA", "nvda": "NVDA",
            "넷플릭스": "NFLX", "netflix": "NFLX", "nflx": "NFLX"
        }
        
        keyword_lower = keyword.lower()
        return popular_stocks.get(keyword_lower, keyword.upper())

# 사용 예시
if __name__ == "__main__":
    from config import Config
    
    # 환경 변수에서 계좌 정보 로드
    demo_account_info = Config.get_account_info('demo')
    
    print("=== 미국주식 API 테스트 ===")
    us_api = USStockAPI(
        demo_account_info['appkey'],
        demo_account_info['appsecret'], 
        demo_account_info['account'],
        is_real=False
    )
    
    # 토큰 발급 테스트
    if us_api.get_access_token():
        print("✅ 미국주식 토큰 발급 성공!")
        
        # 애플 주식 현재가 조회
        price_result = us_api.get_us_stock_price("AAPL")
        if price_result and price_result.get('rt_cd') == '0':
            output = price_result.get('output', {})
            print(f"🍎 애플 현재가: ${output.get('last', 'N/A')}")
        
        # 미국주식 잔고 조회
        balance_result = us_api.get_us_stock_balance()
        if balance_result:
            print(f"💰 미국주식 잔고 조회 결과: {balance_result.get('rt_cd', 'N/A')}")
    else:
        print("❌ 미국주식 토큰 발급 실패!")