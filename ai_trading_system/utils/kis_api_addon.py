"""
KIS API 추가 메서드들
원본 kis_api_enhanced.py에 없는 메서드들 구현
"""

def get_holding_stocks(self):
    """보유 종목 조회"""
    balance = self.get_balance()
    if not balance or balance.get('rt_cd') != '0':
        return []
    
    holdings = []
    output1 = balance.get('output1', [])
    
    for item in output1:
        # 보유 수량이 0보다 큰 종목만 포함
        quantity = int(item.get('hldg_qty', 0))
        if quantity > 0:
            holdings.append({
                'stock_code': item.get('pdno', ''),
                'stock_name': item.get('prdt_name', ''),
                'quantity': quantity,
                'avg_price': float(item.get('pchs_avg_pric', 0)),
                'current_price': float(item.get('prpr', 0)),
                'eval_amt': float(item.get('evlu_amt', 0)),
                'profit_loss': float(item.get('evlu_pfls_amt', 0)),
                'profit_rate': float(item.get('evlu_pfls_rt', 0))
            })
    
    return holdings

def get_available_cash(self):
    """매수 가능 현금 조회"""
    balance = self.get_balance()
    if not balance or balance.get('rt_cd') != '0':
        return 0
    
    output2 = balance.get('output2', [{}])
    if output2:
        # 주문 가능 현금
        return float(output2[0].get('ord_psbl_cash', 0))
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
    
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {self.access_token}",
        "appkey": self.appkey,
        "appsecret": self.appsecret,
        "tr_id": "VTTC0802U" if not self.is_real else "TTTC0802U",
        "custtype": "P",
        "hashkey": ""
    }
    
    # 시장가 주문인 경우 가격을 0으로 설정
    if order_type == "03":
        price = 0
    
    data = {
        "CANO": self.account_no.split('-')[0],
        "ACNT_PRDT_CD": self.account_no.split('-')[1],
        "PDNO": stock_code,
        "ORD_DVSN": order_type,
        "ORD_QTY": str(quantity),
        "ORD_UNPR": str(price),
        "CTAC_TLNO": "",
        "SLL_TYPE": "01",
        "ALGO_NO": ""
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
    
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {self.access_token}",
        "appkey": self.appkey,
        "appsecret": self.appsecret,
        "tr_id": "VTTC0801U" if not self.is_real else "TTTC0801U",
        "custtype": "P",
        "hashkey": ""
    }
    
    # 시장가 주문인 경우 가격을 0으로 설정
    if order_type == "03":
        price = 0
    
    data = {
        "CANO": self.account_no.split('-')[0],
        "ACNT_PRDT_CD": self.account_no.split('-')[1],
        "PDNO": stock_code,
        "ORD_DVSN": order_type,
        "ORD_QTY": str(quantity),
        "ORD_UNPR": str(price),
        "CTAC_TLNO": "",
        "SLL_TYPE": "01",
        "ALGO_NO": ""
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