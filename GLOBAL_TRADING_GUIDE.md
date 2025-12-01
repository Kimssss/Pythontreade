# 글로벌 주식 거래 시스템 가이드

## 개요
한국투자증권 API를 활용한 국내/해외 통합 주식 거래 시스템입니다.

## 지원 거래소

### 국내 주식
- KOSPI (코스피)
- KOSDAQ (코스닥)

### 해외 주식 (미국만 지원)
- **NASDAQ** (나스닥)
- **NYSE** (뉴욕증권거래소)
- **AMEX** (아멕스)

## 주요 기능

### 1. 해외주식 API (KisAPIOverseas)

```python
from ai_trading_system.utils.kis_api import KisAPIEnhanced

# API 초기화
api = KisAPIEnhanced(appkey, appsecret, account_no, is_real=False)
api.initialize_overseas_api()  # 해외주식 API 활성화

# 해외주식 현재가 조회
price_info = api.overseas.get_overseas_price('NASD', 'AAPL')

# 해외주식 매수
result = api.overseas.buy_overseas_stock(
    exchange='NASD',
    symbol='AAPL',
    quantity=10,
    price=0,  # 시장가
    order_type='00'  # 00: 시장가, 32: 지정가
)

# 해외주식 잔고 조회
balance = api.overseas.get_overseas_balance()
```

### 2. 글로벌 스크리너 (GlobalStockScreener)

```python
from ai_trading_system.strategies.global_screener import GlobalStockScreener

# 스크리너 초기화
screener = GlobalStockScreener(api)

# 글로벌 종목 스크리닝
results = await screener.screen_global_stocks(
    markets=['KOSPI', 'KOSDAQ', 'NASDAQ', 'NYSE']
)

# 결과 확인
domestic_stocks = results['domestic']  # 국내 추천 종목
overseas_stocks = results['overseas']  # 해외 추천 종목
```

## 거래소별 코드

### 미국
- `NASD`: 나스닥
- `NYSE`: 뉴욕증권거래소
- `AMEX`: 아멕스

## 주문 유형

### 국내 주식
- `01`: 지정가
- `03`: 시장가
- `05`: 조건부지정가
- `06`: 최유리지정가
- `07`: 최우선지정가

### 해외 주식
- `00`: 시장가
- `32`: 지정가
- `34`: 지정가(외화)

## 통화 코드
- `USD`: 미국 달러 (미국 주식)
- `KRW`: 한국 원 (국내 주식)

## 주의사항

1. **거래 시간**
   - 한국: 09:00 ~ 15:30 KST
   - 미국: 한국시간 23:30 ~ 06:00 (서머타임 22:30 ~ 05:00)

2. **환율**
   - 해외주식 거래시 환율 변동 리스크 고려
   - 매수/매도 시점의 환율 차이 발생 가능

3. **수수료 및 세금**
   - 거래소별로 수수료 체계가 다름
   - 양도소득세, 배당세 등 세금 고려

4. **API 제한**
   - Rate limiting 적용 (초당 거래건수 제한)
   - 장외시간 주문은 예약주문으로 처리

## 에러 처리

### 공통 에러 코드
- `EGW00123`: 초당 거래건수 초과
- `EGW00002`: 서버 에러
- `APIM0001`: 인증 실패

### 해외주식 특수 에러
- `OVSE0001`: 해외주식 거래 불가 계좌
- `OVSE0002`: 거래소 휴장
- `OVSE0003`: 환전 한도 초과

## 사용 예시

### 통합 거래 시스템
```python
async def global_trading_example():
    # API 초기화
    api = KisAPIEnhanced(appkey, appsecret, account_no)
    api.initialize_overseas_api()
    
    # 글로벌 스크리너
    screener = GlobalStockScreener(api)
    
    # 전체 시장 스크리닝
    results = await screener.screen_global_stocks()
    
    # 국내 주식 매수
    if results['domestic']:
        top_domestic = results['domestic'][0]
        api.buy_stock(
            stock_code=top_domestic['code'],
            quantity=10,
            order_type='03'  # 시장가
        )
    
    # 해외 주식 매수
    if results['overseas']:
        top_overseas = results['overseas'][0]
        api.overseas.buy_overseas_stock(
            exchange='NASD',
            symbol=top_overseas['code'],
            quantity=5,
            order_type='00'  # 시장가
        )
```

## 개발 로드맵

1. ✅ 미국 주식 API 기본 구현
2. ✅ 국내/미국 통합 스크리너 구현
3. ✅ 시간대별 자동 거래 시스템
4. 🔲 실시간 시세 연동
5. 🔲 환율 정보 연동
6. 🔲 글로벌 포트폴리오 관리

## 자동 거래 시간표

프로그램은 각 시장의 거래 시간에 맞춰 자동으로 거래를 수행합니다:

- **09:00 ~ 15:30**: 🇰🇷 한국 주식 거래
- **22:30 ~ 05:00**: 🇺🇸 미국 주식 거래 (서머타임)
- **23:30 ~ 06:00**: 🇺🇸 미국 주식 거래 (표준시간)

시장이 열려있는 시간에는 5분마다 자동으로 종목을 스크리닝하고 거래를 실행합니다.