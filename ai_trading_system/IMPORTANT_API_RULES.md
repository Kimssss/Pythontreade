# 🚨 중요: API 데이터 사용 규칙

## 절대 규칙

### ❌ 금지 사항
1. **더미 데이터 사용 금지**
   - 하드코딩된 기본값 사용 금지
   - 가짜 잔고나 임의의 금액 설정 금지
   - 테스트용 더미 포트폴리오 생성 금지

2. **임의 값 설정 금지**
   - 초기 자본금을 임의로 설정하지 않음
   - 잔고가 0이어도 임의의 값으로 변경하지 않음

### ✅ 필수 사항
1. **모든 데이터는 API를 통해서만**
   - 계좌 잔고: `get_balance()` API 호출
   - 보유 주식: `get_holding_stocks()` API 호출
   - 주문 가능 금액: `get_available_cash()` API 호출

2. **API 응답 그대로 사용**
   - API가 0을 반환하면 실제 잔고가 0인 것
   - 에러가 발생해도 임의의 값을 대입하지 않음

## 구현 원칙

### 1. 계좌 정보 조회
```python
# ✅ 올바른 예
cash_balance = self.kis_api.get_available_cash()  # API 호출
holdings = self.kis_api.get_holding_stocks()      # API 호출

# ❌ 잘못된 예
if cash_balance == 0:
    cash_balance = 10000000  # 더미 데이터 사용 금지!
```

### 2. 에러 처리
```python
# ✅ 올바른 예
try:
    balance = api.get_balance()
    if not balance:
        logger.error("API returned no data")
        # 그대로 None이나 0 사용
except Exception as e:
    logger.error(f"API error: {e}")
    # 에러 상태 유지, 더미값 대입 금지

# ❌ 잘못된 예
if not balance:
    balance = {"dummy": 1000000}  # 금지!
```

### 3. 모의투자와 실전투자
- **동일한 API 사용**: 모의투자와 실전투자 모두 같은 API 엔드포인트 사용
- **tr_id만 다름**: 모의투자는 'V'로 시작, 실전투자는 'T'로 시작
- **데이터 형식 동일**: 응답 형식과 처리 방법 완전히 동일

## 주말/장외시간 처리

### API 제한사항
- **Rate Limiting**: 주말에는 더 엄격한 호출 제한
- **500 에러**: "초당 거래건수 초과" 메시지
- **해결책**: 호출 간격을 2초 이상으로 설정

### 권장 설정
```python
# 주말/장외시간용 설정
min_request_interval = 2.0  # 2초 간격
max_retries = 3
```

## 로깅 규칙

### 모든 API 호출 로그 기록
1. **요청 정보**
   - 시간, 엔드포인트, 파라미터
   - 헤더 (인증 정보 제외)

2. **응답 정보**
   - 상태 코드, 응답 메시지
   - 성공/실패 여부

3. **에러 정보**
   - 에러 코드, 메시지
   - 재시도 횟수

### 로그 파일 위치
- API 실패: `logs/api_failures_YYYYMMDD.log`
- 일반 로그: `logs/ai_trading.log`
- 에러 로그: `logs/errors.log`

## 체크리스트

- [ ] 모든 금액 정보는 API에서만 가져오는가?
- [ ] 더미 데이터나 하드코딩된 값이 없는가?
- [ ] API 에러 시 임의의 값을 대입하지 않는가?
- [ ] 모든 API 호출이 로그에 기록되는가?
- [ ] 주말/장외시간 Rate Limiting을 고려했는가?

## 결론

**"API가 주는 값이 진실이다. 임의로 바꾸지 마라."**