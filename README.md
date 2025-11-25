# 한국투자증권 자동매매 시스템

한국투자증권 Open API를 활용한 주식 자동매매 시스템입니다.

## ✨ 주요 기능

- 🟡 **모의투자 모드**: 가상 자금으로 안전한 테스트
- 🔴 **실전투자 모드**: 실제 자금으로 거래 (주의 필요)
- 💰 **계좌 정보 조회**: 잔고 및 평가 손익 확인
- 📈 **주식 현재가 조회**: 실시간 주식 가격 정보
- 🛒 **주식 매수/매도**: 지정가/시장가 주문
- 📊 **주문 내역 조회**: 거래 내역 확인
- 🔒 **보안 강화**: 환경 변수로 API 키 관리

## 🚀 빠른 시작

### 1. 설치

```bash
git clone <repository-url>
cd PythonProject1

# 자동 설치 스크립트 실행
python3 setup.py
```

### 2. 수동 설치 (선택사항)

```bash
# 패키지 설치
pip install -r requirements.txt

# 환경 설정 파일 생성
cp .env.example .env
# .env 파일을 열어서 API 키 정보 입력
```

### 3. 실행

```bash
python3 trading_ui.py
```

## ⚙️ 환경 설정

`.env` 파일에 한국투자증권 API 키를 설정해야 합니다:

```env
# 실전투자 계좌
REAL_APPKEY=your_real_appkey_here
REAL_APPSECRET=your_real_appsecret_here
REAL_ACCOUNT_NO=your_real_account_number_here

# 모의투자 계좌
DEMO_APPKEY=your_demo_appkey_here
DEMO_APPSECRET=your_demo_appsecret_here
DEMO_ACCOUNT_NO=your_demo_account_number_here
```

## 📁 파일 구조

```
PythonProject1/
├── kis_api.py          # 한국투자증권 API 클래스
├── trading_ui.py       # 메인 UI 프로그램
├── config.py           # 환경 변수 설정 관리
├── test_trading.py     # API 기능 테스트
├── demo_ui.py          # UI 데모
├── setup.py            # 자동 설치 스크립트
├── requirements.txt    # 패키지 의존성
├── .env.example        # 환경 설정 예시
├── .env               # 환경 설정 (git에서 제외)
└── .gitignore         # git 무시 파일
```

## 🛡️ 보안 주의사항

- ⚠️ **API 키 보안**: `.env` 파일은 절대 공개하지 마세요
- 🔴 **실전투자 주의**: 실제 자금 손실 위험이 있습니다
- 🟡 **모의투자 권장**: 충분한 테스트 후 실전 사용
- 📝 **백업**: 중요한 설정은 별도 백업 권장

## 🎯 사용법

1. **모드 선택**: 프로그램 시작 시 실전/모의투자 모드 선택
2. **계좌 조회**: 현재 잔고와 보유 주식 확인
3. **주식 조회**: 종목코드로 실시간 가격 확인
4. **매수/매도**: 주문 수량과 가격 입력하여 거래
5. **내역 확인**: 주문 결과 및 거래 내역 확인

## 📋 요구사항

- Python 3.7+
- 한국투자증권 계좌 및 API 키
- 인터넷 연결

## 🐛 문제 해결

### 패키지 설치 오류
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### API 연결 오류
- `.env` 파일의 API 키 정보 확인
- 한국투자증권 Open API 서비스 상태 확인
- 계좌 상태 및 권한 확인

## ⚖️ 라이선스 및 면책조항

이 소프트웨어는 교육 및 학습 목적으로 제공됩니다. 실제 투자로 인한 손실에 대해서는 책임지지 않습니다. 투자는 본인의 판단과 책임 하에 진행하시기 바랍니다.