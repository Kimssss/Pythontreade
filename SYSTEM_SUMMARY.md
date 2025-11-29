# AI 자동매매 시스템 - 프로젝트 요약

## 🎯 프로젝트 완료 상태

### ✅ 완료된 작업
1. **불필요한 파일 정리**
   - 기존 파일들을 `old_files_backup/` 디렉토리로 이동
   - 프로젝트 구조 정리 완료

2. **블로그 분석 문서**
   - `BLOG_ANALYSIS_COMPREHENSIVE.md` - 1874번 포스트 포함 6개 핵심 포스트 완전 분석
   - `BLOG_POST_1874_ANALYSIS.md` - 최신 AI 퀀트 트레이딩 시스템 분석

3. **AI 자동매매 시스템 구현** (`ai_trading_system/`)
   ```
   ai_trading_system/
   ├── config/
   │   ├── settings.py          # 시스템 설정
   │   └── config.py           # API 설정
   ├── models/
   │   ├── dqn_agent.py        # DQN 강화학습 에이전트
   │   └── ensemble_system.py   # 멀티 에이전트 앙상블
   ├── strategies/
   │   └── stock_screener.py    # 자동 종목 선정
   ├── utils/
   │   ├── kis_api.py          # 한국투자증권 API (강화 버전)
   │   ├── risk_manager.py      # VaR/CVaR 리스크 관리
   │   └── technical_indicators.py  # 기술적 지표
   ├── main_trading_system.py   # 메인 시스템
   ├── run_trading.py          # 실행 스크립트
   ├── test_system.py          # 기능 테스트
   ├── requirements.txt        # 의존성 패키지
   ├── README.md              # 사용 설명서
   ├── .env                   # 환경 변수 (API 키)
   └── .env.example           # 환경 변수 예시
   ```

4. **환경 설정 완료**
   - `.env` 파일에 한국투자증권 API 키 설정됨
   - 모의투자 및 실전투자 계정 정보 포함

## 🚀 시스템 실행 방법

### 1. 의존성 설치
```bash
cd ai_trading_system
pip install -r requirements.txt
```

### 2. 설정 확인
```bash
python run_trading.py --check
```

### 3. 모의투자 실행
```bash
python run_trading.py --mode demo
```

### 4. 기능 테스트
```bash
cd ai_trading_system
python test_system.py
```

## 💡 주요 기능

1. **멀티 에이전트 앙상블**
   - DQN 강화학습 (40%)
   - 팩터 투자 (30%)
   - 기술적 분석 (30%)

2. **자동 종목 선정**
   - 거래량 상위 종목 스크리닝
   - 팩터 점수 기반 선정
   - 시장 상황별 가중치 조정

3. **리스크 관리**
   - VaR/CVaR 계산
   - 동적 레버리지 조정
   - 포지션 사이징
   - 손절/익절 관리

4. **실시간 거래**
   - 한국투자증권 API 연동
   - 자동 토큰 갱신
   - Rate limiting 관리

## ⚠️ 주의사항

1. **직접 실행 금지**
   - `main_trading_system.py`를 직접 실행하지 마세요
   - 항상 `run_trading.py`를 통해 실행

2. **실전 투자 주의**
   - 반드시 모의투자로 충분히 테스트
   - 실전 모드는 실제 돈으로 거래됨

3. **환경 변수**
   - `.env` 파일의 API 키가 정확한지 확인
   - 절대 `.env` 파일을 공유하지 마세요

## 📊 성과 추적

- 일일 성과: `performance_*.json`
- 거래 내역: `trades_*.json`
- 시스템 로그: `logs/ai_trading.log`
- DQN 모델: `models/dqn_model_*.pt`

## 🔧 문제 해결

### Import 오류
- 프로젝트 루트에서 실행: `python ai_trading_system/run_trading.py`

### 토큰 오류
- `cache/` 디렉토리의 토큰 캐시 삭제
- 재실행하여 토큰 재발급

### API 오류
- `.env` 파일의 API 키 확인
- 네트워크 연결 확인

---

**프로젝트 완료일**: 2024년 11월 29일
**구현 기반**: 블로그 분석 (twentytwentyone.tistory.com)
**주요 기술**: DQN, 멀티 에이전트, VaR/CVaR, 한국투자증권 API