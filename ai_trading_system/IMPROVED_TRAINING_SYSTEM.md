# 🚀 개선된 AI 학습 시스템

## 주요 개선사항

### 1. 영구 학습 기록 저장
- **위치**: `training_cache/training_history.json`
- **내용**: 
  - 학습한 종목 코드와 이름
  - 학습 날짜와 시간
  - 최근 7일간의 기록 유지
- **효과**: 프로그램 재시작 후에도 학습 기록 유지

### 2. 시가총액 순위대로 학습
```python
# 시가총액 순위대로 선택 (첫 번째 미학습 종목)
stock = available_stocks[0]  # 이미 시가총액 순으로 정렬되어 있음
```
- **효과**: 중요도가 높은 대형주부터 체계적으로 학습

### 3. 학습 격차 자동 보완
```python
# 놓친 기간 확인
last_training_date = self._get_last_training_date(stock_code)
days_since_last = (datetime.now() - last_training_date).days

# 놓친 기간만큼 추가 데이터 수집
if days_since_last > 1:
    days_to_collect = min(200, days_since_last + 30)  # 최대 200일
    
# 놓친 기간만큼 추가 학습
if days_missed > 7:
    episodes = min(50, 10 + days_missed)  # 기본 10 + 추가 에피소드
```

### 4. 일일 진행상황 추적
```
📊 Training on: 삼성전자 (005930)
📋 Today's progress: 5/30 stocks trained
```

## 학습 시나리오

### 정상 운영 (매일 실행)
1. 시가총액 상위 30개 종목을 순서대로 학습
2. 오늘 학습한 종목은 제외
3. 기본 10 에피소드 학습
4. 학습 완료 즉시 다음 종목 시작 (대기 시간 없음)

### 며칠 놓친 경우
1. 예: 3일 동안 실행 안함
2. 시스템이 자동으로 감지
3. 더 많은 데이터 수집 (60일 → 90일)
4. 추가 학습 수행 (10 → 13 에피소드)

### 오래 놓친 경우
1. 예: 30일 이상 미실행
2. 최대 200일 데이터 수집
3. 최대 50 에피소드까지 집중 학습
4. 놓친 기간 완전 보상

## 학습 기록 예시

### training_history.json
```json
{
  "trained_stocks": ["005930", "000660", "035720"],
  "history": [
    {
      "date": "20251130",
      "time": "14:45:23",
      "stock_code": "005930",
      "stock_name": "삼성전자",
      "timestamp": "2025-11-30T14:45:23"
    },
    {
      "date": "20251130",
      "time": "14:46:45",
      "stock_code": "000660",
      "stock_name": "SK하이닉스",
      "timestamp": "2025-11-30T14:46:45"
    }
  ],
  "last_updated": "2025-11-30T14:47:00"
}
```

## 효과

1. **중복 방지**: 같은 날 같은 종목 반복 학습 없음
2. **체계적 학습**: 시가총액 순으로 중요 종목부터 학습
3. **연속성 보장**: 놓친 기간 자동 보완
4. **효율성 향상**: 대기 시간 없이 연속 학습
5. **속도 개선**: 시간당 더 많은 종목 학습 가능

## 모니터링

```bash
# 학습 기록 확인
cat training_cache/training_history.json | jq .

# 오늘 학습한 종목 수
cat training_cache/training_history.json | jq '.trained_stocks | length'

# 최근 학습 이력
cat training_cache/training_history.json | jq '.history[-5:]'
```

## 설정 변경

### 일일 최대 학습 종목 수
```python
# main_trading_system.py
max_stocks_per_hour = 5  # 시간당 최대 종목 수
```

### 학습 기록 보관 기간
```python
# weekend_trainer.py
cutoff_date = (datetime.now() - timedelta(days=7))  # 7일 → 원하는 기간
```

### 최대 추가 학습 에피소드
```python
episodes = min(50, 10 + days_missed)  # 50 → 원하는 최대값
```

## 결론

이제 AI 학습 시스템이:
- ✅ 시가총액 순위대로 체계적으로 학습
- ✅ 학습 완료 즉시 다음 종목 시작 (대기 없음)
- ✅ 놓친 기간을 자동으로 보완
- ✅ 학습 기록을 영구 저장
- ✅ 시간당 더 많은 종목 학습 가능