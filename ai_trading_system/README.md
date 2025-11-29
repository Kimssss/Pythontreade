# 🤖 AI 자동매매 시스템

블로그 분석 기반 AI 자동매매 시스템 - 완전 자동화된 주식 거래 봇

## 주요 기능

- **멀티 에이전트 앙상블**: DQN, 팩터 투자, 기술적 분석 통합
- **자동 종목 선정**: 팩터 기반 스크리닝
- **리스크 관리**: VaR/CVaR 기반 동적 레버리지
- **실시간 거래**: 한국투자증권 API 연동
- **자동 리밸런싱**: 월 1회 포트폴리오 최적화

## 시스템 구조

```
ai_trading_system/
├── config/
│   └── settings.py          # 시스템 설정
├── models/
│   ├── dqn_agent.py        # DQN 강화학습 에이전트
│   └── ensemble_system.py   # 멀티 에이전트 앙상블
├── strategies/
│   └── stock_screener.py    # 종목 스크리닝
├── utils/
│   ├── kis_api.py          # 한국투자증권 API
│   ├── risk_manager.py      # 리스크 관리
│   └── technical_indicators.py  # 기술적 지표
├── main_trading_system.py   # 메인 시스템
└── run_trading.py          # 실행 스크립트
```

## 설치 방법

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 열어서 API 키 입력
```

### 3. 한국투자증권 API 키 발급
- [한국투자증권 OpenAPI](https://apiportal.koreainvestment.com) 가입
- 앱 키와 시크릿 발급
- 모의투자 신청 (실전 투자는 별도)

## 🚀 실행 방법

### 방법 1: 새로운 통합 실행 스크립트 (권장)
```bash
# 프로젝트 루트에서 실행
python run_ai_trading.py --mode demo

# 또는 대화형 모드 선택
python run_ai_trading.py
```

### 방법 2: 기존 실행 스크립트
```bash
cd ai_trading_system
python run_trading.py --mode demo
```

### 설정 확인
```bash
python run_ai_trading.py --check
```

### 실전투자 실행 (⚠️ 주의!)
```bash
python run_ai_trading.py --mode real
# 실제 돈으로 거래됩니다! 충분한 테스트 후 사용하세요.
```

## 주요 설정

### `config/settings.py`
- `max_position_size`: 개별 종목 최대 비중 (기본 10%)
- `max_drawdown_limit`: 최대 낙폭 한도 (기본 15%)
- `min_confidence`: 최소 신호 신뢰도 (기본 70%)

## 거래 전략

### 1. 종목 선정
- 거래량 상위 종목 중 팩터 점수 계산
- 가치, 품질, 모멘텀, 성장 팩터 종합 평가

### 2. 매매 신호
- **DQN Agent**: 강화학습 기반 매매 결정
- **Factor Agent**: 팩터 점수 기반 매매
- **Technical Agent**: 기술적 지표 신호

### 3. 리스크 관리
- VaR 95% 신뢰수준으로 일일 손실 제한
- 동적 레버리지 조정
- 개별 종목 및 섹터 한도 관리

## 📈 자동화된 트레이딩 워크플로우

블로그 포스트 1874번에서 소개된 최신 AI 퀀트 트레이딩 시스템을 완벽하게 구현했습니다:

### 워크플로우 다이어그램
```
[ Pre-market ] → 시장 분석, 종목 스크리닝
      ↓
[ AI 전략결정 ] → DQN + 팩터 + 기술적 분석
      ↓
[ 리스크 매니저 ] → VaR/CVaR 동적 레버리지
      ↓
[ 주문 생성 ] → 포지션 사이징, 신호 필터링
      ↓
[ 주문 실행 ] → 한국투자증권 API 자동 주문
      ↓
[ 실시간 모니터링 ] → 5분 단위 포트폴리오 체크
      ↓
[ 장 마감 ] → 일일 정산, 성과 기록
      ↓
[ 강화학습 → AutoML → 모델 승격 ] → 지속적 개선
      ↓
[ 다음날 다시 시작 ] → 완전 자동화
```

## 📊 성과 모니터링

- **실시간 대시보드**: Streamlit 기반 (개발 예정)
- **일일 성과**: `performance_*.json` 파일
- **거래 내역**: `trades_*.json` 파일
- **시스템 로그**: `logs/ai_trading.log`
- **DQN 모델**: `models/dqn_model_*.pt`

## 주의사항

⚠️ **실전 투자 시 주의**
- 반드시 모의투자로 충분히 테스트 후 사용
- 초기에는 소액으로 시작
- 시스템 오류 시 즉시 중단

## 문제 해결

### 토큰 오류
- 토큰이 만료되면 자동 갱신됨
- `cache/` 디렉토리의 토큰 캐시 삭제 후 재시도

### API 오류
- Rate limit 초과 시 자동 대기
- 500 에러 시 자동 재시도 (최대 3회)

## API 문서

한국투자증권 OpenAPI 구현에 대한 자세한 내용은 [KIS_API_DOCUMENTATION.md](./KIS_API_DOCUMENTATION.md)를 참조하세요.

### 주요 API 기능
- **주식 주문**: 매수/매도/취소 주문
- **계좌 조회**: 잔고, 보유종목, 매수가능금액
- **시세 조회**: 현재가, 호가, 일봉, 거래량 상위
- **주문 내역**: 체결 내역 조회
- **시장 지수**: KOSPI, KOSDAQ 지수 조회

## 최신 업데이트 (2024)

### API 개선사항
- ✅ 해시키 기능 추가 (보안 강화)
- ✅ Rate Limiting 고도화 (429 에러 자동 처리)
- ✅ 토큰 캐싱으로 성능 최적화
- ✅ 주문 체결 조회 기능 추가
- ✅ 시장 지수 실시간 조회

## 라이선스

이 프로젝트는 교육 및 연구 목적으로만 사용하세요.
실제 투자에 따른 손실은 사용자 책임입니다.