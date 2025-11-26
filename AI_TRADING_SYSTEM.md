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

## 📚 블로그 분석 결과 종합 (67개 URL 완전 분석)

### 🔍 분석된 블로그 URL 목록
```
최신 → 과거 순서 (번호가 높을수록 최신)
https://twentytwentyone.tistory.com/1873 (최신)
https://twentytwentyone.tistory.com/1847
https://twentytwentyone.tistory.com/1842
https://twentytwentyone.tistory.com/1835
https://twentytwentyone.tistory.com/1831
https://twentytwentyone.tistory.com/1830
https://twentytwentyone.tistory.com/1822
https://twentytwentyone.tistory.com/1821
https://twentytwentyone.tistory.com/1810
https://twentytwentyone.tistory.com/1780
https://twentytwentyone.tistory.com/1766
https://twentytwentyone.tistory.com/1759
https://twentytwentyone.tistory.com/1738
https://twentytwentyone.tistory.com/1734
https://twentytwentyone.tistory.com/1714
https://twentytwentyone.tistory.com/1690
https://twentytwentyone.tistory.com/1689
https://twentytwentyone.tistory.com/1688
https://twentytwentyone.tistory.com/1674
https://twentytwentyone.tistory.com/1661
https://twentytwentyone.tistory.com/1651
https://twentytwentyone.tistory.com/1641
https://twentytwentyone.tistory.com/1612
https://twentytwentyone.tistory.com/1606
https://twentytwentyone.tistory.com/1595
https://twentytwentyone.tistory.com/1581
https://twentytwentyone.tistory.com/1576
https://twentytwentyone.tistory.com/1564
https://twentytwentyone.tistory.com/1554
https://twentytwentyone.tistory.com/1545
https://twentytwentyone.tistory.com/1538
https://twentytwentyone.tistory.com/1526
https://twentytwentyone.tistory.com/1520
https://twentytwentyone.tistory.com/1511
https://twentytwentyone.tistory.com/1500
https://twentytwentyone.tistory.com/1492
https://twentytwentyone.tistory.com/1481
https://twentytwentyone.tistory.com/1473
https://twentytwentyone.tistory.com/1465
https://twentytwentyone.tistory.com/1460
https://twentytwentyone.tistory.com/1447
https://twentytwentyone.tistory.com/1446
https://twentytwentyone.tistory.com/1433
https://twentytwentyone.tistory.com/1431
https://twentytwentyone.tistory.com/1392
https://twentytwentyone.tistory.com/1391
https://twentytwentyone.tistory.com/1374
https://twentytwentyone.tistory.com/1372
https://twentytwentyone.tistory.com/1356
https://twentytwentyone.tistory.com/1355
https://twentytwentyone.tistory.com/1352
https://twentytwentyone.tistory.com/1350
https://twentytwentyone.tistory.com/1332
https://twentytwentyone.tistory.com/1325
https://twentytwentyone.tistory.com/1314
https://twentytwentyone.tistory.com/1305
https://twentytwentyone.tistory.com/1290
https://twentytwentyone.tistory.com/1287
https://twentytwentyone.tistory.com/1271
https://twentytwentyone.tistory.com/1254
https://twentytwentyone.tistory.com/1252
https://twentytwentyone.tistory.com/1238
https://twentytwentyone.tistory.com/1221
https://twentytwentyone.tistory.com/1195
https://twentytwentyone.tistory.com/1182
https://twentytwentyone.tistory.com/1165
https://twentytwentyone.tistory.com/1163 (가장 오래된 분석 대상)
```

### 📊 AI/ML 전략 진화 패턴 (시간순 분석)
- **1단계 (1163~1300)**: 기초 퀀트 팩터 투자 + 기술적 지표
- **2단계 (1300~1500)**: LSTM 시계열 예측 + 멀티팩터 모델
- **3단계 (1500~1700)**: DQN 강화학습 + 리스크 패리티
- **4단계 (1700~1873)**: Transformer + AutoML + 실시간 모니터링

### 🎯 핵심 성공 전략 (블로그 실증 분석)
1. **Dynamic Factor Model**: 시장 상황별 팩터 가중치 동적 조정
2. **Multi-Agent Ensemble**: DQN + Factor + Technical 앙상블
3. **Regime Detection**: HMM 기반 강세/약세/횡보 구분
4. **Risk Parity**: VaR/CVaR 기반 동적 포지션 사이징
5. **AutoML Pipeline**: Optuna + MLflow 자동 최적화

### 🛠 기술 스택 진화 (블로그 추적)
#### 초기 (2023 상반기)
- **백테스팅**: Backtrader, Zipline
- **ML**: scikit-learn, XGBoost
- **시각화**: Matplotlib, Plotly

#### 중기 (2023 하반기)
- **딥러닝**: TensorFlow, PyTorch
- **강화학습**: Stable-Baselines3, Ray
- **최적화**: Optuna, Hyperopt

#### 최신 (2024~현재)
- **모델 관리**: MLflow, Weights & Biases
- **인프라**: Docker, Kubernetes, Airflow
- **모니터링**: Streamlit, Grafana, Prometheus
- **고급 AI**: Transformer, Multi-Agent RL

### 📈 성과 벤치마크 (블로그 실증 결과)
| 기간 | 전략 | 연간수익률 | MDD | 샤프비율 | 정보비율 |
|------|------|-----------|-----|----------|----------|
| 초기 | Factor Only | 8-12% | 15-20% | 0.8-1.0 | 0.5-0.7 |
| 중기 | LSTM + Factor | 12-15% | 12-18% | 1.2-1.4 | 0.8-1.0 |
| 고급 | DQN Ensemble | 15-18% | 8-12% | 1.5-1.8 | 1.2-1.5 |
| 최신 | Multi-Agent + AutoML | 17-20% | 6-10% | 1.6-2.0 | 1.4-1.7 |

### 🧠 구현된 핵심 알고리즘 (블로그 기반)
1. **Regime Detection**: Hidden Markov Model로 시장 상태 분류
2. **Dynamic Factor Weighting**: 레짐별 팩터 가중치 자동 조정
3. **Multi-Agent Architecture**: 3개 에이전트 앙상블 의사결정
4. **Risk Management**: Kelly Criterion + VaR 포지션 사이징
5. **AutoML Optimization**: 베이지안 최적화 하이퍼파라미터 튜닝

### 🎯 블로그 분석에서 추출한 핵심 인사이트
- **데이터 품질이 80%**: 좋은 데이터 > 복잡한 모델
- **앙상블의 힘**: 단일 모델보다 다양성이 중요
- **리스크 우선**: 수익률보다 손실 제한이 우선
- **자동화 필수**: 감정 배제한 시스템적 접근
- **지속적 학습**: 시장 변화에 적응하는 모델

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