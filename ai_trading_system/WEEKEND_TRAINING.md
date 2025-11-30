# 🧠 주말/장외시간 AI 학습 시스템

## 개요

시장이 닫혀있는 시간을 활용하여 AI 모델을 자동으로 학습시킵니다.

## 학습 시간

### 주말
- **매 3시간마다** 자동 학습
- 토요일 00:00 ~ 일요일 24:00

### 평일 장외시간
- **18:00 ~ 21:00** 집중 학습 시간
- 최적의 컴퓨팅 리소스 활용

## 학습 내용

### 1. DQN 강화학습 에이전트
```
- 과거 60일 데이터로 학습
- 거래량 상위 10종목 대상
- 에피소드별 반복 학습
- 모델 가중치 자동 저장
```

### 2. 팩터 가중치 최적화
```
- 가치(Value) 팩터
- 품질(Quality) 팩터
- 모멘텀(Momentum) 팩터
- 성장(Growth) 팩터
```

### 3. 기술적 지표 파라미터 최적화
```
- RSI 기간 최적화
- MACD 파라미터 튜닝
- 볼린저밴드 설정 최적화
```

### 4. 백테스팅
```
- 학습된 전략 검증
- 수익률 시뮬레이션
- 승률 계산
```

## 학습 로그 예시

```
=== Starting Weekend Training Session ===
1. Collecting historical data for training...
   Collecting data for 삼성전자 (005930)
   Collecting data for SK하이닉스 (000660)
   Collected data for 10 stocks

2. Training DQN Agent...
   DQN Training: 10 episodes, Avg Loss: 0.0234
   DQN Training: 20 episodes, Avg Loss: 0.0187
   DQN model saved to models/dqn_model_20251130_180000.pt

3. Optimizing factor weights...
   Analyzing factor performance...
   
4. Optimizing technical indicators...
   
5. Running backtesting...
   Running backtest simulation...
   
=== Training Complete ===
Duration: 1823 seconds
DQN Loss: 0.0156
Backtest Return: 12.35%
```

## 학습 결과 활용

### 1. 모델 업데이트
- 성능이 향상된 모델은 자동으로 실전 적용
- 기존 모델 백업 후 교체

### 2. 파라미터 조정
- 최적화된 파라미터는 다음 거래일부터 적용
- 설정 파일 자동 업데이트

### 3. 성과 추적
- 학습 이력은 `training_results/` 폴더에 저장
- 성과 개선 추이 모니터링

## 장점

1. **시간 활용**: 놀고 있는 시간에 AI가 똑똑해짐
2. **지속적 개선**: 매주 새로운 데이터로 학습
3. **자동화**: 사용자 개입 없이 자동 실행
4. **안전성**: 실제 거래는 하지 않고 시뮬레이션만

## 설정

### 학습 주기 변경
```python
# main_trading_system.py
if (datetime.now() - self.last_training_time).total_seconds() > 10800:  # 3시간
```

### 학습 종목 수 변경
```python
# weekend_trainer.py
stocks = volume_stocks.get('output', [])[:10]  # 상위 10종목
```

## 모니터링

학습 진행상황은 로그에서 실시간 확인 가능:
```
[Weekend Training] Starting AI model training...
🤖 Starting AI model training session...
✅ Training completed!
   - Duration: 1823s
   - DQN Loss: 0.0156
   - Backtest Return: 12.35%
```