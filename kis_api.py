import requests
import json
import hashlib
import hmac
import base64
import time
from datetime import datetime, timedelta

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
        
    def get_access_token(self, retry_count=3):
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
        
        for attempt in range(retry_count):
            try:
                print(f"토큰 발급 시도 {attempt + 1}/{retry_count}...")
                response = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'access_token' in result:
                        self.access_token = result['access_token']
                        print(f"토큰 발급 성공: {self.access_token[:20]}...")
                        return True
                    else:
                        print(f"토큰 발급 실패: {result}")
                        return False
                elif response.status_code == 403:
                    print(f"403 오류 - API 키나 권한을 확인하세요")
                    print(f"응답: {response.text}")
                    if attempt < retry_count - 1:
                        import time
                        print(f"5초 후 재시도...")
                        time.sleep(5)
                        continue
                    return False
                else:
                    response.raise_for_status()
                
            except requests.exceptions.Timeout:
                print(f"타임아웃 오류 (시도 {attempt + 1}/{retry_count})")
                if attempt < retry_count - 1:
                    import time
                    time.sleep(2)
                    continue
            except requests.exceptions.RequestException as e:
                print(f"네트워크 오류: {e}")
                if attempt < retry_count - 1:
                    import time
                    time.sleep(2)
                    continue
            except Exception as e:
                print(f"토큰 발급 중 오류 발생: {e}")
                if attempt < retry_count - 1:
                    import time
                    time.sleep(2)
                    continue
        
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

    def get_daily_price(self, stock_code, period_type="D", count=30):
        """
        주식 일별 시세 조회

        Args:
            stock_code: 종목코드
            period_type: 기간분류 (D:일, W:주, M:월)
            count: 조회 개수

        Returns:
            일별 시세 데이터
        """
        if not self.access_token:
            if not self.get_access_token():
                return None

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-price"

        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "FHKST01010400"
        }

        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
            "FID_PERIOD_DIV_CODE": period_type,
            "FID_ORG_ADJ_PRC": "0"
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"일별 시세 조회 중 오류 발생: {e}")
            return None

    def get_volume_rank(self, market="J"):
        """
        거래량 순위 조회

        Args:
            market: 시장구분 (J:코스피, Q:코스닥)

        Returns:
            거래량 순위 데이터
        """
        if not self.access_token:
            if not self.get_access_token():
                return None

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/volume-rank"

        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "FHPST01710000"
        }

        params = {
            "FID_COND_MRKT_DIV_CODE": market,
            "FID_COND_SCR_DIV_CODE": "20101",
            "FID_INPUT_ISCD": "0000",
            "FID_DIV_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "0",
            "FID_TRGT_CLS_CODE": "111111111",
            "FID_TRGT_EXLS_CLS_CODE": "000000",
            "FID_INPUT_PRICE_1": "0",
            "FID_INPUT_PRICE_2": "0",
            "FID_VOL_CNT": "0",
            "FID_INPUT_DATE_1": ""
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"거래량 순위 조회 중 오류 발생: {e}")
            return None

    def get_fluctuation_rank(self, market="J", sort_type="0"):
        """
        등락률 순위 조회

        Args:
            market: 시장구분 (J:코스피, Q:코스닥)
            sort_type: 정렬 (0:상승률, 1:하락률)

        Returns:
            등락률 순위 데이터
        """
        if not self.access_token:
            if not self.get_access_token():
                return None

        url = f"{self.base_url}/uapi/domestic-stock/v1/ranking/fluctuation"

        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "FHPST01700000"
        }

        params = {
            "fid_cond_mrkt_div_code": market,
            "fid_cond_scr_div_code": "20170",
            "fid_input_iscd": "0000",
            "fid_rank_sort_cls_code": sort_type,
            "fid_input_cnt_1": "0",
            "fid_prc_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": "",
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
            "fid_div_cls_code": "0",
            "fid_rsfl_rate1": "",
            "fid_rsfl_rate2": ""
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"등락률 순위 조회 중 오류 발생: {e}")
            return None

    def get_market_cap_rank(self, market="J"):
        """
        시가총액 상위 종목 조회

        Args:
            market: 시장구분 (J:코스피, Q:코스닥)

        Returns:
            시가총액 순위 데이터
        """
        if not self.access_token:
            if not self.get_access_token():
                return None

        url = f"{self.base_url}/uapi/domestic-stock/v1/ranking/market-cap"

        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "FHPST01740000"
        }

        params = {
            "fid_cond_mrkt_div_code": market,
            "fid_cond_scr_div_code": "20174",
            "fid_input_iscd": "0000",
            "fid_div_cls_code": "0",
            "fid_trgt_cls_code": "0",
            "fid_trgt_exls_cls_code": "0",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": ""
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"시가총액 순위 조회 중 오류 발생: {e}")
            return None

    def get_stock_info(self, stock_code):
        """
        종목 기본 정보 조회

        Args:
            stock_code: 종목코드

        Returns:
            종목 기본 정보
        """
        if not self.access_token:
            if not self.get_access_token():
                return None

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/search-stock-info"

        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "CTPF1002R"
        }

        params = {
            "PRDT_TYPE_CD": "300",
            "PDNO": stock_code
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"종목 정보 조회 중 오류 발생: {e}")
            return None

    def get_holding_stocks(self):
        """
        보유 종목 리스트 조회 (잔고에서 추출)

        Returns:
            보유 종목 리스트
        """
        balance = self.get_balance()
        if not balance or balance.get('rt_cd') != '0':
            return []

        holdings = []
        output1 = balance.get('output1', [])

        for stock in output1:
            if int(stock.get('hldg_qty', 0)) > 0:
                holdings.append({
                    'stock_code': stock.get('pdno', ''),
                    'stock_name': stock.get('prdt_name', ''),
                    'quantity': int(stock.get('hldg_qty', 0)),
                    'buy_price': float(stock.get('pchs_avg_pric', 0)),
                    'current_price': float(stock.get('prpr', 0)),
                    'profit_rate': float(stock.get('evlu_pfls_rt', 0)),
                    'profit_amount': int(stock.get('evlu_pfls_amt', 0))
                })

        return holdings

    def get_available_cash(self):
        """
        주문 가능 현금 조회

        Returns:
            주문 가능 현금
        """
        balance = self.get_balance()
        if not balance or balance.get('rt_cd') != '0':
            return 0

        output2 = balance.get('output2', [{}])
        if output2:
            return int(output2[0].get('ord_psbl_cash', 0))
        return 0

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