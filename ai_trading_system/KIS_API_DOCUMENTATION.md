# 한국투자증권 OpenAPI 구현 문서

## 개요

이 문서는 한국투자증권 OpenAPI를 활용한 AI 자동매매 시스템의 API 구현 상세 내역을 설명합니다.

## API 엔드포인트 및 기능

### 1. 인증 (Authentication)

**토큰 발급**
- Endpoint: `/oauth2/tokenP`
- Method: POST
- 용도: API 사용을 위한 액세스 토큰 발급

### 2. 주식 주문 (Stock Orders)

#### 매수 주문 (Buy Order)
- Endpoint: `/uapi/domestic-stock/v1/trading/order-cash`
- Method: POST
- TR_ID: 
  - 실전: `TTTC0802U`
  - 모의: `VTTC0802U`

#### 매도 주문 (Sell Order)
- Endpoint: `/uapi/domestic-stock/v1/trading/order-cash`
- Method: POST
- TR_ID:
  - 실전: `TTTC0801U`
  - 모의: `VTTC0801U`

#### 주문 취소 (Cancel Order)
- Endpoint: `/uapi/domestic-stock/v1/trading/order-rvsecncl`
- Method: POST
- TR_ID:
  - 실전: `TTTC0803U`
  - 모의: `VTTC0803U`

### 3. 조회 기능 (Query Functions)

#### 계좌 잔고 조회
- Endpoint: `/uapi/domestic-stock/v1/trading/inquire-balance`
- Method: GET
- TR_ID:
  - 실전: `TTTC8434R`
  - 모의: `VTTC8434R`

#### 주식 현재가 조회
- Endpoint: `/uapi/domestic-stock/v1/quotations/inquire-price`
- Method: GET
- TR_ID: `FHKST01010100`

#### 호가 정보 조회
- Endpoint: `/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn`
- Method: GET
- TR_ID: `FHKST01010200`

#### 일봉 데이터 조회
- Endpoint: `/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice`
- Method: GET
- TR_ID: `FHKST03010100`

#### 거래량 상위 종목
- Endpoint: `/uapi/domestic-stock/v1/quotations/volume-rank`
- Method: GET
- TR_ID: `FHPST01710000`

#### 주문 체결 내역
- Endpoint: `/uapi/domestic-stock/v1/trading/inquire-daily-ccld`
- Method: GET
- TR_ID:
  - 실전: `TTTC8001R`
  - 모의: `VTTC8001R`

#### 시장 지수 조회
- Endpoint: `/uapi/domestic-stock/v1/quotations/inquire-index-price`
- Method: GET
- TR_ID: `FHKUP03500100`

## 주요 파라미터

### 주문 파라미터 (Order Parameters)
- **CANO**: 종합계좌번호 (앞 8자리)
- **ACNT_PRDT_CD**: 계좌상품코드 (뒤 2자리)
- **PDNO**: 종목코드 (6자리)
- **ORD_DVSN**: 주문구분
  - `01`: 지정가
  - `03`: 시장가
- **ORD_QTY**: 주문수량
- **ORD_UNPR**: 주문단가 (지정가: 가격, 시장가: 0)

### 조회 파라미터 (Query Parameters)
- **FID_COND_MRKT_DIV_CODE**: 시장구분코드 (보통 "J")
- **FID_INPUT_ISCD**: 종목코드

## 보안 기능

### 해시키 (HashKey)
매수/매도/취소 주문 시 보안을 위해 해시키가 필요합니다:
- Endpoint: `/uapi/hashkey`
- 주문 데이터를 암호화하여 전송

### Rate Limiting
API 호출 제한 방지를 위한 기능:
- 최소 요청 간격: 0.2초
- 429 에러 시 자동 재시도
- 지수 백오프 (Exponential Backoff) 구현

### 토큰 관리
- 토큰 자동 갱신
- 토큰 캐싱으로 불필요한 재발급 방지
- 토큰 만료 5분 전 자동 갱신

## 에러 처리

### HTTP 상태 코드
- **200**: 성공
- **401/403**: 인증 오류 → 토큰 재발급
- **429**: Rate Limit 초과 → 대기 후 재시도
- **500**: 서버 오류 → 지수 백오프로 재시도

### API 응답 코드
- **rt_cd = "0"**: 정상 처리
- **rt_cd != "0"**: 오류 발생 (msg1 확인)

## 구현 특징

1. **자동 재시도**: 네트워크 오류나 서버 오류 시 최대 3회 자동 재시도
2. **토큰 캐싱**: 토큰을 파일로 저장하여 재사용
3. **Rate Limiting**: API 호출 간격 자동 조절
4. **에러 핸들링**: 다양한 오류 상황 자동 처리

## 사용 예시

### 매수 주문
```python
# 삼성전자 10주 시장가 매수
result = api.buy_stock("005930", 10, order_type="03")

# 삼성전자 10주 85,000원 지정가 매수
result = api.buy_stock("005930", 10, price=85000, order_type="01")
```

### 매도 주문
```python
# 삼성전자 10주 시장가 매도
result = api.sell_stock("005930", 10, order_type="03")

# 삼성전자 10주 90,000원 지정가 매도
result = api.sell_stock("005930", 10, price=90000, order_type="01")
```

### 계좌 조회
```python
# 계좌 잔고 조회
balance = api.get_balance()

# 보유 주식 조회
holdings = api.get_holding_stocks()

# 매수 가능 금액 조회
cash = api.get_available_cash()
```

### 시세 조회
```python
# 현재가 조회
price = api.get_stock_price("005930")

# 일봉 데이터 조회 (최근 30일)
daily = api.get_daily_price("005930", count=30)

# 거래량 상위 20종목
top_stocks = api.get_top_volume_stocks(count=20)
```

## 참고 자료

- [한국투자증권 KIS Developers](https://apiportal.koreainvestment.com/intro)
- [파이썬을 이용한 한국/미국 주식 자동매매 시스템](https://wikidocs.net/book/7845)
- [GitHub - koreainvestment/open-trading-api](https://github.com/koreainvestment/open-trading-api)

## 업데이트 내역

### 2024년 최신 업데이트
- 해시키 기능 추가 (매수/매도 주문 시 필수)
- 주문 체결 조회 API 추가
- 시장 지수 조회 API 추가
- 주문 취소 기능 구현
- Rate Limiting 강화