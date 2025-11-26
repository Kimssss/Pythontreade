# AI 자동매매 시스템 개발 문서

## 프로젝트 개요
한국투자증권 API를 활용한 AI 기반 자동매매 시스템 구축

## 시스템 아키텍처

### 1. 핵심 구성 요소
- **DQN 강화학습 에이전트**: 시장 상황에 따른 최적 매매 결정
- **AutoML 최적화**: Optuna를 활용한 하이퍼파라미터 자동 튜닝
- **자동 모델 관리**: MLflow를 통한 모델 버전 관리 및 배포
- **실시간 모니터링**: 성과 추적 및 리스크 관리

### 2. 기술 스택
- **API**: 한국투자증권 OpenAPI
- **AI/ML**: 
  - TensorFlow/PyTorch (DQN 구현)
  - Optuna (하이퍼파라미터 최적화)
  - MLflow (모델 관리)
- **데이터**: pandas, numpy
- **모니터링**: Streamlit 대시보드

## 블로그 분석 결과 종합

### 📊 AI/ML 전략 진화 패턴
- **기초 퀀트**: 팩터 투자 → 기술적 지표 → 멀티팩터 모델
- **중급 AI**: LSTM 시계열 예측 → DQN 강화학습 → Transformer 모델
- **고급 시스템**: AutoML 파이프라인 → MLOps 자동화 → 실시간 모니터링

### 🎯 핵심 성공 전략 (블로그 분석)
1. **Dynamic Factor Model**: 시장 상황별 팩터 가중치 동적 조정
2. **Multi-Agent RL**: 여러 에이전트 앙상블로 위험 분산
3. **Regime Detection**: 강세/약세/횡보 구분하여 전략 전환
4. **Risk Parity**: VaR/CVaR 기반 동적 포지션 사이징

### 🛠 기술 스택 (최신 트렌드)
- **ML**: PyTorch, Transformer, Stable-Baselines3, Optuna
- **인프라**: MLflow, Airflow, Docker, Kubernetes
- **모니터링**: Streamlit, Grafana, Prometheus
- **백테스팅**: Backtrader, Zipline, VectorBT

### 📈 성과 벤치마크 (블로그 실증 결과)
- **연간 수익률**: 15-18% (KOSPI 대비 +5~8%)
- **최대손실(MDD)**: 8-12% (Buy&Hold 19% → 개선)
- **샤프 비율**: 1.5-1.8 (기존 1.0 → 크게 개선)
- **정보 비율**: 1.2-1.5 (알파 생성 능력 우수)

## 구현 계획 (8주 로드맵)

### Week 1-2: 기초 인프라 구축
1. 데이터 파이프라인 (실시간 + 과거 데이터)
2. 백테스팅 프레임워크 구축
3. 한국투자증권 API 완전 연동

### Week 3-4: 멀티 팩터 모델
1. 가치/성장/모멘텀/품질 팩터 구현
2. 동적 팩터 가중치 시스템
3. 리짐 디텍션 모델 (Hidden Markov)

### Week 5-6: AI 강화학습 시스템  
1. DQN/A3C 멀티 에이전트 구현
2. Transformer 기반 시계열 예측
3. 앙상블 메타 러닝 구조

### Week 7-8: MLOps 자동화
1. Optuna AutoML 파이프라인
2. MLflow 모델 관리 시스템
3. 실시간 모니터링 대시보드

## 개발 진행 상황

### ✅ 완료된 작업
- [x] 블로그 분석 및 요구사항 파악 (67개 URL 전체 분석)
- [x] 기존 코드베이스 분석 (한국투자증권 API 기반)
- [x] 시스템 아키텍처 설계 (8주 로드맵)
- [x] DQN 강화학습 트레이딩 시스템 구현
- [x] 멀티 에이전트 시스템 (DQN + Factor + Technical)
- [x] 레짐 디텍션 (Hidden Markov Model)
- [x] 동적 팩터 모델 (가치/성장/모멘텀/품질/수익성)
- [x] 리스크 관리 시스템 (VaR/CVaR 기반)
- [x] AutoML 최적화 (Optuna 하이퍼파라미터 튜닝)
- [x] 자동 패키지 설치 시스템
- [x] 실시간 모니터링 대시보드

### 📁 생성된 파일들
1. **run_system.py** - 통합 실행 스크립트 (메인)
2. **ai_trading_system.py** - 기본 DQN 자동매매 시스템  
3. **advanced_ai_system.py** - 멀티 에이전트 고급 시스템
4. **dashboard.py** - Streamlit 모니터링 대시보드
5. **auto_install.py** - 자동 패키지 설치
6. **requirements.txt** - 정리된 의존성
7. **backup_old_files/** - 기존 파일들 백업

### 🚀 실행 방법

#### 🎯 간단한 실행 (권장)
```bash
# 통합 실행 스크립트
python run_system.py
```

#### 🔧 개별 실행
```bash
# 1. 패키지 설치 먼저
python auto_install.py

# 2. 기본 DQN 시스템
python ai_trading_system.py

# 3. 고급 멀티 에이전트 시스템
python advanced_ai_system.py

# 4. 모니터링 대시보드
streamlit run dashboard.py
```

### 💡 주요 특징
- **67개 블로그 분석** 결과 반영된 최신 AI 전략
- **Multi-Agent 앙상블**: DQN + Factor + Technical Analysis
- **Dynamic Regime Detection**: HMM 기반 시장 상황 판별
- **Risk Parity**: VaR/CVaR 기반 포지션 사이징
- **AutoML 최적화**: Optuna 하이퍼파라미터 튜닝
- **실시간 모니터링**: 성과/리스크/포트폴리오 추적

---
*업데이트: 2025-11-26*