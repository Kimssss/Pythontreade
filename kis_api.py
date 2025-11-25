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
        self.token_expire_time = None
        
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
                        # 토큰 만료시간 설정 (일반적으로 24시간 유효)
                        expires_in = result.get('expires_in', 86400)  # 기본 24시간
                        self.token_expire_time = datetime.now() + timedelta(seconds=expires_in - 300)  # 5분 여유
                        print(f"토큰 발급 성공: {self.access_token[:20]}...")
                        print(f"토큰 만료시간: {self.token_expire_time}")
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
    
    def is_token_expired(self):
        """토큰 만료 여부 확인"""
        if not self.access_token or not self.token_expire_time:
            return True
        return datetime.now() >= self.token_expire_time
    
    def refresh_token_if_needed(self):
        """필요시 토큰 갱신"""
        if self.is_token_expired():
            print("토큰이 만료되어 재발급을 시도합니다...")
            return self.get_access_token()
        return True
    
    def ensure_valid_token(self):
        """유효한 토큰 확보 (만료시 자동 갱신)"""
        if not self.access_token or self.is_token_expired():
            return self.get_access_token()
        return True
    
    def set_token_expiry_for_testing(self, minutes_from_now):
        """테스트용: 토큰 만료시간 설정"""
        if self.token_expire_time:
            self.token_expire_time = datetime.now() + timedelta(minutes=minutes_from_now)
            print(f"테스트용 토큰 만료시간 설정: {self.token_expire_time}")
    
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
    
    def _make_api_request(self, method, url, headers=None, params=None, data=None, retry_on_auth_error=True):
        """
        인증 에러 시 토큰 갱신하여 재시도하는 공통 API 요청 메서드
        
        Args:
            method: HTTP 메서드 ('GET', 'POST')
            url: 요청 URL
            headers: 요청 헤더
            params: 쿼리 파라미터 (GET 요청시)
            data: 요청 데이터 (POST 요청시)
            retry_on_auth_error: 인증 에러시 재시도 여부
        
        Returns:
            응답 객체 또는 None
        """
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params)
            else:
                response = requests.post(url, headers=headers, data=data)
            
            # 인증 에러 처리 (401, 403) - 500 에러는 토큰 문제일 수 있음
            if response.status_code in [401, 403, 500] and retry_on_auth_error:
                error_msg = ""
                try:
                    error_data = response.json()
                    error_msg = error_data.get('error_description', '')
                except:
                    pass
                
                # 토큰 관련 에러인지 확인
                if any(keyword in error_msg.lower() for keyword in ['token', '토큰', 'auth', 'unauthorized']):
                    print(f"토큰 관련 에러 발생 (HTTP {response.status_code}). 토큰 갱신 후 재시도...")
                    if self.get_access_token():
                        # 헤더의 토큰 갱신
                        if headers and 'authorization' in headers:
                            headers['authorization'] = f"Bearer {self.access_token}"
                        # 재시도
                        if method.upper() == 'GET':
                            response = requests.get(url, headers=headers, params=params)
                        else:
                            response = requests.post(url, headers=headers, data=data)
                    else:
                        print("토큰 갱신 실패")
                        return None
                elif response.status_code in [401, 403]:
                    print(f"인증 에러 발생 (HTTP {response.status_code}): {error_msg}")
                    return None
            
            response.raise_for_status()
            return response
            
        except Exception as e:
            print(f"API 요청 중 오류 발생: {e}")
            return None
    
    def get_balance(self):
        """계좌 잔고 조회"""
        if not self.ensure_valid_token():
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
        
        response = self._make_api_request('GET', url, headers=headers, params=params)
        if response:
            return response.json()
        return None
    
    def get_stock_price(self, stock_code):
        """주식 현재가 조회"""
        if not self.ensure_valid_token():
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
        
        response = self._make_api_request('GET', url, headers=headers, params=params)
        if response:
            return response.json()
        return None
    
    def buy_stock(self, stock_code, quantity, price=0, order_type="01"):
        """주식 매수 주문"""
        if not self.ensure_valid_token():
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
        
        response = self._make_api_request('POST', url, headers=headers, data=json.dumps(order_data))
        if response:
            return response.json()
        return None
    
    def sell_stock(self, stock_code, quantity, price=0, order_type="01"):
        """주식 매도 주문"""
        if not self.ensure_valid_token():
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
        
        response = self._make_api_request('POST', url, headers=headers, data=json.dumps(order_data))
        if response:
            return response.json()
        return None
    
    def get_orders(self):
        """주문 내역 조회"""
        if not self.ensure_valid_token():
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
        
        response = self._make_api_request('GET', url, headers=headers, params=params)
        if response:
            return response.json()
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
        if not self.ensure_valid_token():
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

        response = self._make_api_request('GET', url, headers=headers, params=params)
        if response:
            return response.json()
        return None

    def get_volume_rank(self, market="J"):
        """
        거래량 순위 조회

        Args:
            market: 시장구분 (J:코스피, Q:코스닥)

        Returns:
            거래량 순위 데이터
        """
        if not self.ensure_valid_token():
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

        response = self._make_api_request('GET', url, headers=headers, params=params)
        if response:
            return response.json()
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
        if not self.ensure_valid_token():
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

        response = self._make_api_request('GET', url, headers=headers, params=params)
        if response:
            return response.json()
        return None

    def get_market_cap_rank(self, market="J"):
        """
        시가총액 상위 종목 조회

        Args:
            market: 시장구분 (J:코스피, Q:코스닥)

        Returns:
            시가총액 순위 데이터
        """
        if not self.ensure_valid_token():
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

        response = self._make_api_request('GET', url, headers=headers, params=params)
        if response:
            return response.json()
        return None

    def get_stock_info(self, stock_code):
        """
        종목 기본 정보 조회

        Args:
            stock_code: 종목코드

        Returns:
            종목 기본 정보
        """
        if not self.ensure_valid_token():
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

        response = self._make_api_request('GET', url, headers=headers, params=params)
        if response:
            return response.json()
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