#!/usr/bin/env python3
"""
한국투자증권 API - 500 에러 방지 기능 강화 버전
- Rate limiting 방지
- 자동 재시도 로직
- 호출 간격 제어
"""

import requests
import json
import time
import pickle
import os
import hashlib
import base64
from datetime import datetime, timedelta
from pathlib import Path
import threading
from collections import defaultdict
import logging

# API 실패 로거 설정
api_logger = logging.getLogger('kis_api')
api_logger.setLevel(logging.DEBUG)

# 파일 핸들러 설정
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

file_handler = logging.FileHandler(log_dir / f'api_failures_{datetime.now().strftime("%Y%m%d")}.log')
file_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

api_logger.addHandler(file_handler)


class KisAPIEnhanced:
    def __init__(self, appkey, appsecret, account_no, is_real=False, min_request_interval=0.2):
        """
        한국투자증권 API 클래스 - 강화 버전
        
        Args:
            appkey (str): API Key
            appsecret (str): API Secret
            account_no (str): 계좌번호
            is_real (bool): 실전투자 여부 (True: 실전, False: 모의)
            min_request_interval (float): 최소 요청 간격 (초)
        """
        self.appkey = appkey
        self.appsecret = appsecret
        self.account_no = account_no
        self.is_real = is_real
        self.min_request_interval = min_request_interval
        
        # URL 설정
        if is_real:
            self.base_url = "https://openapi.koreainvestment.com:9443"
        else:
            self.base_url = "https://openapivts.koreainvestment.com:29443"
        
        self.access_token = None
        self.token_expire_time = None
        
        # Rate limiting 관리
        self.last_request_time = defaultdict(float)
        self.request_lock = threading.Lock()
        
        # 토큰 캐시 파일 경로
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        mode_str = "real" if is_real else "demo"
        self.token_cache_file = self.cache_dir / f"token_{mode_str}_{appkey[:10]}.pkl"
        
        # 캐시된 토큰 로드 시도
        self._load_cached_token()
    
    def _load_cached_token(self):
        """캐시된 토큰 로드"""
        try:
            if self.token_cache_file.exists():
                with open(self.token_cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                
                self.access_token = cache_data.get('access_token')
                self.token_expire_time = cache_data.get('token_expire_time')
                
                # 토큰이 유효한지 확인
                if self.access_token and self.token_expire_time:
                    if datetime.now() < self.token_expire_time:
                        print(f"✅ 캐시된 토큰 로드 성공 (만료: {self.token_expire_time})")
                        return True
                    else:
                        print(f"⚠️ 캐시된 토큰이 만료됨 (만료: {self.token_expire_time})")
                        self._clear_cached_token()
                        
        except Exception as e:
            print(f"⚠️ 토큰 캐시 로드 실패: {e}")
            self._clear_cached_token()
        
        return False
    
    def _save_cached_token(self):
        """토큰 캐시에 저장"""
        try:
            cache_data = {
                'access_token': self.access_token,
                'token_expire_time': self.token_expire_time,
                'saved_at': datetime.now()
            }
            
            with open(self.token_cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            print(f"💾 토큰 캐시 저장 완료: {self.token_cache_file}")
            
        except Exception as e:
            print(f"⚠️ 토큰 캐시 저장 실패: {e}")
    
    def _clear_cached_token(self):
        """토큰 캐시 삭제"""
        try:
            if self.token_cache_file.exists():
                self.token_cache_file.unlink()
            self.access_token = None
            self.token_expire_time = None
        except Exception as e:
            print(f"⚠️ 토큰 캐시 삭제 실패: {e}")
    
    def _wait_for_rate_limit(self, endpoint):
        """Rate limiting을 위한 대기"""
        with self.request_lock:
            now = time.time()
            last_request = self.last_request_time[endpoint]
            elapsed = now - last_request
            
            if elapsed < self.min_request_interval:
                wait_time = self.min_request_interval - elapsed
                print(f"⏰ Rate limit 대기: {wait_time:.2f}초")
                time.sleep(wait_time)
            
            self.last_request_time[endpoint] = time.time()
    
    def get_access_token(self, retry_count=3):
        """액세스 토큰 발급 (캐시 우선 사용)"""
        # 먼저 캐시된 토큰이 유효한지 확인
        if self.access_token and self.token_expire_time:
            if datetime.now() < self.token_expire_time:
                print(f"🔄 기존 토큰 재사용 (만료: {self.token_expire_time})")
                return True
        
        # 캐시된 토큰이 없거나 만료된 경우에만 새로 발급
        print("🔑 새로운 토큰 발급 요청...")
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
                        
                        # 토큰을 캐시에 저장
                        self._save_cached_token()
                        return True
                    else:
                        print(f"토큰 발급 실패: {result}")
                        return False
                elif response.status_code == 403:
                    print(f"403 오류 - API 키나 권한을 확인하세요")
                    print(f"응답: {response.text}")
                    if attempt < retry_count - 1:
                        print(f"5초 후 재시도...")
                        time.sleep(5)
                        continue
                    return False
                else:
                    response.raise_for_status()
                
            except requests.exceptions.Timeout:
                print(f"타임아웃 오류 (시도 {attempt + 1}/{retry_count})")
                if attempt < retry_count - 1:
                    time.sleep(2)
                    continue
            except requests.exceptions.RequestException as e:
                print(f"네트워크 오류: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2)
                    continue
            except Exception as e:
                print(f"토큰 발급 중 오류 발생: {e}")
                if attempt < retry_count - 1:
                    time.sleep(2)
                    continue
        
        return False
    
    def ensure_valid_token(self):
        """유효한 토큰 확보 (만료시 자동 갱신)"""
        if not self.access_token or self.is_token_expired():
            return self.get_access_token()
        return True
    
    def is_token_expired(self):
        """토큰 만료 여부 확인"""
        if not self.access_token or not self.token_expire_time:
            return True
        return datetime.now() >= self.token_expire_time
    
    def _get_hashkey(self, data):
        """해시키 생성 (매수/매도 주문 시 필요)"""
        url = f"{self.base_url}/uapi/hashkey"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "appkey": self.appkey,
            "appsecret": self.appsecret
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
            if response.status_code == 200:
                result = response.json()
                return result.get('HASH', '')
        except Exception as e:
            print(f"⚠️ 해시키 생성 실패: {e}")
        return ""
    
    def _log_api_request(self, request_log):
        """API 요청 로그 저장"""
        try:
            # 실패한 요청만 파일로 저장
            if not request_log.get('success', False):
                api_logger.error(f"API Request Failed: {json.dumps(request_log, indent=2, ensure_ascii=False)}")
            else:
                # 성공한 요청은 디버그 레벨로
                api_logger.debug(f"API Request Success: {request_log['endpoint']} - {request_log['method']}")
        except Exception as e:
            print(f"로그 기록 실패: {e}")
    
    def _make_api_request_with_retry(self, method, url, headers=None, params=None, data=None, 
                                   endpoint_name="unknown", max_retries=3):
        """
        Rate limiting과 재시도 로직이 포함된 API 요청 메서드
        
        Args:
            method: HTTP 메서드 ('GET', 'POST')
            url: 요청 URL
            headers: 요청 헤더
            params: 쿼리 파라미터 (GET 요청시)
            data: 요청 데이터 (POST 요청시)
            endpoint_name: 엔드포인트 이름 (rate limiting용)
            max_retries: 최대 재시도 횟수
        
        Returns:
            응답 객체 또는 None
        """
        
        # API 요청 로그 기록
        request_log = {
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'endpoint': endpoint_name,
            'url': url,
            'headers': {k: v if k not in ['authorization', 'appsecret'] else '***' for k, v in (headers or {}).items()},
            'params': params,
            'data': data if not data or 'pwd' not in str(data).lower() else 'REDACTED',
            'retries': 0,
            'success': False,
            'error': None,
            'response_code': None,
            'response_msg': None
        }
        
        for retry in range(max_retries):
            try:
                # Rate limiting 적용
                self._wait_for_rate_limit(endpoint_name)
                
                # API 요청 수행
                if method.upper() == 'GET':
                    response = requests.get(url, headers=headers, params=params, timeout=30)
                else:
                    response = requests.post(url, headers=headers, data=data, timeout=30)
                
                # 성공 응답
                if response.status_code == 200:
                    request_log['success'] = True
                    request_log['response_code'] = 200
                    self._log_api_request(request_log)
                    return response
                
                # 500 에러 처리
                elif response.status_code == 500:
                    request_log['response_code'] = 500
                    request_log['retries'] = retry + 1
                    try:
                        error_data = response.json()
                        request_log['response_msg'] = error_data.get('msg1', '')
                        request_log['error'] = f"500: {error_data.get('msg_cd', '')} - {error_data.get('msg1', '')}"
                    except:
                        request_log['error'] = f"500: {response.text[:100]}"
                    
                    if retry < max_retries - 1:
                        wait_time = 2 ** retry  # 지수 백오프
                        print(f"⚠️ 500 에러 발생 ({request_log.get('response_msg', '')}), {wait_time}초 후 재시도 ({retry + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ 500 에러 - 최대 재시도 횟수 초과")
                        self._log_api_request(request_log)
                        return None
                
                # 429 Too Many Requests
                elif response.status_code == 429:
                    wait_time = 5 * (retry + 1)  # 점진적 증가
                    print(f"⚠️ 요청 빈도 제한 (429), {wait_time}초 후 재시도")
                    time.sleep(wait_time)
                    continue
                
                # 인증 에러 처리 (401, 403)
                elif response.status_code in [401, 403]:
                    request_log['response_code'] = response.status_code
                    request_log['error'] = f"{response.status_code}: Authorization error"
                    print(f"⚠️ 인증 에러 ({response.status_code}) - 토큰 갱신 시도")
                    if self.get_access_token() and headers and 'authorization' in headers:
                        headers['authorization'] = f"Bearer {self.access_token}"
                        continue
                    else:
                        print("❌ 토큰 갱신 실패")
                        self._log_api_request(request_log)
                        return None
                
                # 기타 HTTP 에러
                else:
                    request_log['response_code'] = response.status_code
                    request_log['error'] = f"{response.status_code}: {response.text[:100]}"
                    print(f"❌ HTTP 에러 {response.status_code}: {response.text[:100]}")
                    self._log_api_request(request_log)
                    return None
                    
            except requests.exceptions.Timeout:
                request_log['error'] = f"Timeout error"
                request_log['retries'] = retry + 1
                print(f"⚠️ 타임아웃 (재시도 {retry + 1}/{max_retries})")
                if retry < max_retries - 1:
                    time.sleep(1)
                    continue
            except requests.exceptions.RequestException as e:
                request_log['error'] = f"Network error: {str(e)}"
                request_log['retries'] = retry + 1
                print(f"⚠️ 네트워크 오류: {e}")
                if retry < max_retries - 1:
                    time.sleep(1)
                    continue
            except Exception as e:
                request_log['error'] = f"Unexpected error: {str(e)}"
                request_log['retries'] = retry + 1
                print(f"⚠️ 기타 오류: {e}")
                if retry < max_retries - 1:
                    time.sleep(1)
                    continue
        
        # 모든 재시도 실패 시 로그
        self._log_api_request(request_log)
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
        
        response = self._make_api_request_with_retry(
            'GET', url, headers=headers, params=params, endpoint_name="balance"
        )
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
        
        response = self._make_api_request_with_retry(
            'GET', url, headers=headers, params=params, endpoint_name="price"
        )
        if response:
            return response.json()
        return None
    
    def get_orderbook(self, stock_code):
        """주식 호가 정보 조회"""
        if not self.ensure_valid_token():
            return None
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "FHKST01010200"
        }
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code
        }
        
        response = self._make_api_request_with_retry(
            'GET', url, headers=headers, params=params, endpoint_name="orderbook"
        )
        if response:
            return response.json()
        return None
    
    def get_holding_stocks(self):
        """보유 종목 조회"""
        api_logger.info("get_holding_stocks() called")
        
        balance = self.get_balance()
        if not balance:
            api_logger.warning("get_balance() returned None")
            return []
            
        if balance.get('rt_cd') != '0':
            api_logger.error(f"get_balance() failed: rt_cd={balance.get('rt_cd')}, msg={balance.get('msg1', '')}")
            return []
        
        holdings = []
        output1 = balance.get('output1', [])
        api_logger.debug(f"output1 count: {len(output1)} items")
        
        for item in output1:
            # 보유 수량이 0보다 큰 종목만 포함
            quantity = int(item.get('hldg_qty', 0))
            if quantity > 0:
                holding = {
                    'stock_code': item.get('pdno', ''),
                    'stock_name': item.get('prdt_name', ''),
                    'quantity': quantity,
                    'avg_price': float(item.get('pchs_avg_pric', 0)),
                    'current_price': float(item.get('prpr', 0)),
                    'eval_amt': float(item.get('evlu_amt', 0)),
                    'profit_loss': float(item.get('evlu_pfls_amt', 0)),
                    'profit_rate': float(item.get('evlu_pfls_rt', 0))
                }
                holdings.append(holding)
                api_logger.info(f"Holding found: {holding['stock_name']} ({holding['stock_code']}) - {quantity}주, 평가금액: {holding['eval_amt']:,.0f}원")
        
        api_logger.info(f"Total holdings: {len(holdings)} stocks")
        return holdings
    
    def get_available_cash(self):
        """매수 가능 현금 조회"""
        api_logger.info("get_available_cash() called")
        
        balance = self.get_balance()
        if not balance:
            api_logger.warning("get_balance() returned None")
            return 0
            
        if balance.get('rt_cd') != '0':
            api_logger.error(f"get_balance() failed: rt_cd={balance.get('rt_cd')}, msg={balance.get('msg1', '')}")
            return 0
        
        # output2 데이터 확인
        output2 = balance.get('output2', [])
        api_logger.debug(f"output2 data: {output2}")
        
        if output2 and len(output2) > 0:
            cash_data = output2[0]
            # 다양한 필드 확인
            ord_psbl_cash = float(cash_data.get('ord_psbl_cash', 0))  # 주문가능현금
            dnca_tot_amt = float(cash_data.get('dnca_tot_amt', 0))    # 예수금총금액
            
            api_logger.info(f"Cash available: ord_psbl_cash={ord_psbl_cash:,.0f}, dnca_tot_amt={dnca_tot_amt:,.0f}")
            
            # 주문가능현금이 0이면 예수금총금액 사용
            return ord_psbl_cash if ord_psbl_cash > 0 else dnca_tot_amt
        
        api_logger.warning("No cash data found in output2")
        return 0
    
    def buy_stock(self, stock_code: str, quantity: int, price: int = 0, order_type: str = "01"):
        """주식 매수 주문
        
        Args:
            stock_code: 종목 코드
            quantity: 주문 수량
            price: 주문 가격 (0이면 시장가)
            order_type: 주문 구분 ("01": 지정가, "03": 시장가)
        """
        if not self.ensure_valid_token():
            return None
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
        
        # 해시키 생성을 위한 데이터
        data = {
            "CANO": self.account_no.split('-')[0],
            "ACNT_PRDT_CD": self.account_no.split('-')[1],
            "PDNO": stock_code,
            "ORD_DVSN": order_type,
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price) if order_type == "01" else "0",
            "CTAC_TLNO": "",
            "SLL_TYPE": "01",
            "ALGO_NO": ""
        }
        
        # 해시키 생성 (매수/매도 시 필요)
        hashkey = self._get_hashkey(data)
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "VTTC0802U" if not self.is_real else "TTTC0802U",
            "custtype": "P",
            "hashkey": hashkey
        }
        
        response = self._make_api_request_with_retry(
            'POST', url, headers=headers, data=json.dumps(data), endpoint_name="order"
        )
        if response:
            return response.json()
        return None
    
    def sell_stock(self, stock_code: str, quantity: int, price: int = 0, order_type: str = "01"):
        """주식 매도 주문
        
        Args:
            stock_code: 종목 코드
            quantity: 주문 수량
            price: 주문 가격 (0이면 시장가)
            order_type: 주문 구분 ("01": 지정가, "03": 시장가)
        """
        if not self.ensure_valid_token():
            return None
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
        
        # 해시키 생성을 위한 데이터
        data = {
            "CANO": self.account_no.split('-')[0],
            "ACNT_PRDT_CD": self.account_no.split('-')[1],
            "PDNO": stock_code,
            "ORD_DVSN": order_type,
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price) if order_type == "01" else "0",
            "CTAC_TLNO": "",
            "SLL_TYPE": "01",
            "ALGO_NO": ""
        }
        
        # 해시키 생성 (매수/매도 시 필요)
        hashkey = self._get_hashkey(data)
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "VTTC0801U" if not self.is_real else "TTTC0801U",
            "custtype": "P",
            "hashkey": hashkey
        }
        
        response = self._make_api_request_with_retry(
            'POST', url, headers=headers, data=json.dumps(data), endpoint_name="order"
        )
        if response:
            return response.json()
        return None
    
    def get_daily_price(self, stock_code: str, count: int = 30):
        """일봉 가격 정보 조회"""
        if not self.ensure_valid_token():
            return None
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "FHKST03010100"
        }
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code,
            "FID_INPUT_DATE_1": "",
            "FID_INPUT_DATE_2": "",
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "1"
        }
        
        response = self._make_api_request_with_retry(
            'GET', url, headers=headers, params=params, endpoint_name="daily_price"
        )
        if response:
            result = response.json()
            if result.get('rt_cd') == '0' and 'output2' in result:
                # count 개수만큼만 반환
                result['output'] = result['output2'][:count]
            return result
        return None
    
    def get_top_volume_stocks(self, market: str = "ALL", count: int = 20):
        """거래량 상위 종목 조회"""
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
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_COND_SCR_DIV_CODE": "20171",
            "FID_INPUT_ISCD": "0000",
            "FID_DIV_CLS_CODE": "0",
            "FID_BLNG_CLS_CODE": "0",
            "FID_TRGT_CLS_CODE": "111111111",
            "FID_TRGT_EXLS_CLS_CODE": "000000",
            "FID_INPUT_PRICE_1": "",
            "FID_INPUT_PRICE_2": "",
            "FID_VOL_CNT": "",
            "FID_INPUT_DATE_1": ""
        }
        
        response = self._make_api_request_with_retry(
            'GET', url, headers=headers, params=params, endpoint_name="volume_rank"
        )
        if response:
            result = response.json()
            if result.get('rt_cd') == '0' and 'output' in result:
                # count 개수만큼만 반환
                result['output'] = result['output'][:count]
            return result
        return None
    
    def get_order_history(self, start_date: str = None, end_date: str = None):
        """주문 체결 조회
        
        Args:
            start_date: 시작일자 (YYYYMMDD)
            end_date: 종료일자 (YYYYMMDD)
        """
        if not self.ensure_valid_token():
            return None
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "VTTC8001R" if not self.is_real else "TTTC8001R",
            "custtype": "P"
        }
        
        if not start_date:
            start_date = datetime.now().strftime('%Y%m%d')
        if not end_date:
            end_date = start_date
        
        params = {
            "CANO": self.account_no.split('-')[0],
            "ACNT_PRDT_CD": self.account_no.split('-')[1],
            "INQR_STRT_DT": start_date,
            "INQR_END_DT": end_date,
            "SLL_BUY_DVSN_CD": "00",
            "INQR_DVSN": "01",
            "PDNO": "",
            "CCLD_DVSN": "00",
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "INQR_DVSN_3": "00",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        response = self._make_api_request_with_retry(
            'GET', url, headers=headers, params=params, endpoint_name="order_history"
        )
        if response:
            return response.json()
        return None
    
    def cancel_order(self, order_no: str, order_qty: str, order_price: str = "0", 
                    order_type: str = "00", qty_all_yn: str = "Y"):
        """주문 취소
        
        Args:
            order_no: 주문번호
            order_qty: 주문수량
            order_price: 주문가격
            order_type: 주문구분 (00:분류표 참조)
            qty_all_yn: 전량취소여부 (Y/N)
        """
        if not self.ensure_valid_token():
            return None
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-rvsecncl"
        
        # 해시키 생성을 위한 데이터
        data = {
            "CANO": self.account_no.split('-')[0],
            "ACNT_PRDT_CD": self.account_no.split('-')[1],
            "KRX_FWDG_ORD_ORGNO": "",
            "ORGN_ODNO": order_no,
            "ORD_DVSN": order_type,
            "RVSE_CNCL_DVSN_CD": "02",  # 02:취소
            "ORD_QTY": order_qty,
            "ORD_UNPR": order_price,
            "QTY_ALL_ORD_YN": qty_all_yn,
            "ALGO_NO": ""
        }
        
        # 해시키 생성
        hashkey = self._get_hashkey(data)
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "VTTC0803U" if not self.is_real else "TTTC0803U",
            "custtype": "P",
            "hashkey": hashkey
        }
        
        response = self._make_api_request_with_retry(
            'POST', url, headers=headers, data=json.dumps(data), endpoint_name="cancel_order"
        )
        if response:
            return response.json()
        return None
    
    def get_market_index(self, index_code: str = "0001"):
        """주요 지수 조회
        
        Args:
            index_code: 지수코드 (0001:KOSPI, 1001:KOSDAQ, 2001:KOSPI200)
        """
        if not self.ensure_valid_token():
            return None
        
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-index-price"
        
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": "FHKUP03500100",
            "custtype": "P"
        }
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "U",
            "FID_INPUT_ISCD": index_code
        }
        
        response = self._make_api_request_with_retry(
            'GET', url, headers=headers, params=params, endpoint_name="market_index"
        )
        if response:
            return response.json()
        return None


def test_enhanced_api():
    """강화된 API 테스트"""
    from config import Config
    
    print("🧪 강화된 KIS API 테스트")
    print("=" * 50)
    
    # 모의투자 계정으로 테스트
    demo_account = Config.get_account_info('demo')
    api = KisAPIEnhanced(
        demo_account['appkey'],
        demo_account['appsecret'],
        demo_account['account'],
        is_real=False,
        min_request_interval=0.3  # 300ms 간격
    )
    
    if not api.get_access_token():
        print("❌ 토큰 발급 실패")
        return
    
    print("✅ 토큰 발급 성공")
    
    # 연속 호출 테스트 (10회)
    print("\n🔄 연속 호출 테스트 (10회, 300ms 간격)")
    success_count = 0
    
    for i in range(10):
        print(f"  테스트 {i+1}/10...", end=" ")
        result = api.get_balance()
        
        if result and result.get('rt_cd') == '0':
            print("✅")
            success_count += 1
        else:
            print("❌")
    
    print(f"\n📊 성공률: {success_count}/10 ({success_count/10*100:.1f}%)")


if __name__ == "__main__":
    test_enhanced_api()