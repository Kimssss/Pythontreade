# 모의투자 계좌 설정 가이드

## 현재 상태
- 계좌번호: 50144239-01
- 계좌 잔고: 9,842,748원
- API 연결: 정상
- 주문 가능 여부: ❌ 불가 (모의투자 참가 신청 필요)

## 문제점
"모의투자 주문이 불가한 계좌입니다" 오류 발생

## 해결 방법

### 1. 한국투자증권 웹사이트/앱 접속
- 웹: https://www.truefriend.com
- 모바일: 한국투자 앱

### 2. 모의투자 참가 신청
1. 로그인 후 모의투자 메뉴 접속
2. 모의투자 참가 신청
3. 모의투자 약관 동의
4. 가상머니 신청 (보통 1억원)

### 3. 모의투자 계좌 활성화 확인
- 가상머니가 입금되었는지 확인
- 모의투자 거래 가능 상태인지 확인

### 4. 프로그램 재실행
```bash
# 테스트 실행
python test_mock_account.py

# 전체 거래 시스템 실행 (모의투자 모드)
python -m ai_trading_system.main_trading_system --mode demo
```

## API 키 정보
- APPKEY: PSpRavS44ke8s1UZ8sn8VuOiXIXEE2QcMj2I
- APPSECRET: 저장됨
- 계좌번호: 50144239-01

## 주의사항
1. 모의투자는 실제 돈이 아닌 가상머니로 거래
2. 실시간 시세는 실제와 동일
3. 거래 수수료는 실제와 다를 수 있음
4. 일부 종목은 모의투자에서 거래 제한될 수 있음

## 환경 변수 설정
`.env` 파일:
```
DEMO_APPKEY=PSpRavS44ke8s1UZ8sn8VuOiXIXEE2QcMj2I
DEMO_APPSECRET=acvrN9QSZYfam2V2rAEyFsUisSv1dyDo8kXD3JXHeGQUqxLtZrQYngSlb/RVqhsxuAhPnbJodPXyakzqrxbsBX54ZOZnkduxKFnqqEqxgFte+UjmZvxgyRPx4BrxzUnZY6zEH3qh9n8tzDm6J6oEdyVURXIES26lIEca5BZ7+YyHgG87YKQ=
DEMO_ACCOUNT_NO=50144239-01
```