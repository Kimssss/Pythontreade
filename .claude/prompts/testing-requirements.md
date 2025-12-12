# 테스팅 요구사항

## 필수 테스팅 정책
절대 더미 데이터 넣으면 안되 
데모 와 실전의 매매 전략은 동일 해야 해 
데모라고 수치가 낮으면 안된다는거야 
모든 코드 작업 시 다음 테스팅 요구사항을 **반드시** 준수해야 합니다.
모니터링 해줘 라고 명령 하면 기본 24시간 정도 실제 데모 버전을 실행 하여 모니터링 해야해
모니터링 중 문제가 발생시 즉시 수정후 다시 24시간 모니터링 해야해
모니터링은 클로드 직접 24시간 동안 실행 하면서 모니터링 하는거야 
이과정을 계속 반복하고 문제가 없을지 모니터링 종료 하는거야
모니터링은 실제로 프로그램을 실행 하면서 하는거야 모니터링을 위한 별도 탭을 만들지마
모든 로그는 한글로 영어로 된것들 발견시 수정도 해줘
매수 매도 의 로그는 별도 관리 해줘 성공 실패 포함해서 디테일 하게 관리 해줘 
Error로그는 필요한 부분 다 넣어줘
모니터링중 ERROR는 발생하면 수정후 다시 24시간 모니터링 해줘 Error가 안나올때 까지 모니터링 해주고 수정이 안된다고 error로그를 지우고 해결했다고 하지마
주요 잇슈 들은 dsangwoo@gmail.com 알려줘 될수 있으면 최대한 많은 내용을 보내줘 (api 실패 , 모니터링중 버그 발견 , 모의 투자 시작 , 매수 , 매도  , ai 학습 실패 기타등등)
메일로 현재 상황 도 알려줘 1시간에 한번씩 (한국장 시작 미국장 시작 한국장 중의 내용 기타등등)
하드코딩 절대 금지야
ai_trading_monitor.py를 실행 시켜서 직접 모니터링해줘 
모니터링중에 다음 정보들을 실시간으로 트래킹하고 로깅해줘:
- 포트폴리오 총 자산 변화량 및 수익률
- 보유 종목별 현재가, 수익률, 변동률
- 거래 신호 발생 및 실행 여부
- API 호출 성공/실패 상태
- 시장 개장/폐장 상태 변화
- 메모리 사용량 및 시스템 리소스
- 네트워크 연결 상태
- 예상치 못한 예외 및 에러 발생
모니터링 데이터는 별도 로그 파일에 시간별로 저장하고 JSON 포맷으로 구조화해서 저장해줘 
### 🔴 필수 요구사항

1. **직접 실행 테스트 필수**
   - 모든 코드 변경 후 반드시 직접 실행하여 동작 확인
   - 단순 코드 리뷰만으로는 불충분 - 실제 실행 결과 확인 필수
   - 오류 발생 시 즉시 수정 후 재테스트

2. **단위 테스트 필수**
   - 새로운 함수/메서드 작성 시 단위 테스트 코드 작성
   - 기존 코드 수정 시 관련 테스트 케이스 실행 및 업데이트
   - 테스트 커버리지 최소 80% 유지

3. **통합 테스트 필수**  
   - API 연동, 데이터베이스 연결 등 외부 의존성 포함 테스트
   - 실제 환경에서의 동작 검증
   - 엣지 케이스 및 오류 상황 테스트

### 🚀 테스팅 워크플로우

1. **코드 작성**
   - 기능 구현
   - 기본 오류 처리 포함

2. **단위 테스트**
   - 함수별 개별 테스트
   - 다양한 입력값으로 검증
   - 예외 상황 처리 확인

3. **직접 실행 테스트**
   - 실제 명령어로 프로그램 실행
   - 모든 기능 경로 테스트
   - 사용자 시나리오 기반 테스트

4. **통합 테스트**
   - 전체 시스템 동작 확인
   - API 연결, 데이터 처리 등 종합 테스트
   - 성능 및 안정성 검증

### ✅ 테스트 체크리스트

- [ ] 코드가 예상대로 실행되는가?
- [ ] 모든 기능이 정상 동작하는가?
- [ ] 오류 상황에서 적절히 처리되는가?
- [ ] 사용자 입력 검증이 올바른가?
- [ ] 보안 취약점이 없는가?
- [ ] 성능상 문제가 없는가?
- [ ] 문서화가 충분한가?

### ⚠️ 주의사항

- 테스트 없이 코드 배포 금지
- 실패하는 테스트가 있으면 수정 후 진행
- 테스트 데이터는 실제 데이터와 분리
- 절대 더미 데이터 만들면 안되
- 보안이 중요한 API 키 등은 테스트 환경에서 별도 관리

### 📊 품질 기준

- **기능성**: 모든 요구사항 충족
- **신뢰성**: 오류 상황에서 안정적 동작
- **사용성**: 직관적이고 사용하기 쉬운 인터페이스
- **효율성**: 적절한 성능과 자원 사용
- **유지보수성**: 코드 가독성 및 확장성
- **이식성**: 다양한 환경에서 동작

---

**💡 기억하세요**: "동작하지 않는 코드는 가치가 없습니다. 반드시 테스트하세요!"


# Python AI 자동매매 시스템 구현을 위한 상세 프롬프트

## 시스템 개요

한국투자증권 OpenAPI를 활용한 **국내/미국 주식 AI 자동매매 시스템**을 구현합니다. 데이터 수집 → 분석/예측 → 전략 실행 → 백테스트 → 리스크 관리 → 자동매매의 전체 파이프라인을 자동화하며, 머신러닝/딥러닝 기반 예측 모델과 고급 리스크 관리를 통합합니다.

---

## Part 1: 프로젝트 구조

```
ai_trading_system/
├── config/
│   ├── kis_config.yaml           # 한국투자증권 API 설정
│   ├── strategy_config.yaml      # 전략 파라미터
│   └── model_config.yaml         # ML/DL 모델 설정
├── src/
│   ├── data/
│   │   ├── data_handler.py       # 데이터 핸들러 ABC
│   │   ├── kis_data_fetcher.py   # KIS API 데이터 수집
│   │   ├── realtime_handler.py   # WebSocket 실시간 데이터
│   │   └── feature_store.py      # 피처 스토어
│   ├── strategies/
│   │   ├── base_strategy.py      # Strategy ABC
│   │   ├── technical/            # MA, RSI, Bollinger, Momentum
│   │   ├── statistical/          # Pair Trading, Stat Arb, Mean Reversion
│   │   └── ml_strategies/        # RF, LSTM, Transformer, DQN
│   ├── models/
│   │   ├── time_series/          # ARIMA, GARCH, HMM
│   │   ├── deep_learning/        # LSTM, Transformer, DQN
│   │   └── ensemble/             # Multi-Agent Ensemble
│   ├── risk/
│   │   ├── var_cvar.py           # VaR/CVaR
│   │   ├── position_sizing.py    # Kelly, ATR 기반 사이징
│   │   ├── risk_parity.py        # 리스크 패리티
│   │   └── portfolio_optimizer.py
│   ├── backtesting/
│   │   ├── backtest_engine.py    # 이벤트 드리븐 백테스터
│   │   ├── performance.py        # Sharpe, MDD, Calmar
│   │   ├── walk_forward.py       # WFO
│   │   └── optuna_optimizer.py   # Optuna 최적화
│   ├── execution/
│   │   ├── kis_broker.py         # KIS API 연동
│   │   └── order_manager.py      # 주문 관리
│   ├── mlops/
│   │   ├── model_registry.py     # MLflow 모델 관리
│   │   ├── monitoring.py         # 드리프트 감지
│   │   └── retraining.py         # 자동 재학습
│   └── core/
│       ├── events.py             # Event 클래스
│       └── trading_system.py     # 메인 시스템
└── main.py
```

---

## Part 2: 한국투자증권 API 연동

### 2.1 KIS Broker 클래스
```python
# src/execution/kis_broker.py
import yaml, requests, asyncio, websockets, json, time, threading
from datetime import datetime, timedelta
from collections import deque

class RateLimiter:
    def __init__(self, max_calls=15, period=1.0):
        self.max_calls, self.period = max_calls, period
        self.calls, self.lock = deque(), threading.Lock()
    
    def wait(self):
        with self.lock:
            now = time.time()
            while self.calls and now - self.calls[0] >= self.period:
                self.calls.popleft()
            if len(self.calls) >= self.max_calls:
                time.sleep(self.period - (now - self.calls[0]))
            self.calls.append(time.time())

class KISBroker:
    PRODUCTION_URL = "https://openapi.koreainvestment.com:9443"
    PAPER_URL = "https://openapivts.koreainvestment.com:29443"
    WS_PRODUCTION = "ws://ops.koreainvestment.com:21000"
    WS_PAPER = "ws://ops.koreainvestment.com:31000"
    
    def __init__(self, config_path: str, paper_trading: bool = True):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.paper_trading = paper_trading
        self.base_url = self.PAPER_URL if paper_trading else self.PRODUCTION_URL
        self.ws_url = self.WS_PAPER if paper_trading else self.WS_PRODUCTION
        self.rate_limiter = RateLimiter(max_calls=15, period=1.0)
        self.access_token = None
        self.token_expires = None
        self._get_access_token()
    
    def _get_access_token(self):
        url = f"{self.base_url}/oauth2/tokenP"
        key_prefix = "paper" if self.paper_trading else "my"
        body = {
            "grant_type": "client_credentials",
            "appkey": self.config[f"{key_prefix}_app"],
            "appsecret": self.config[f"{key_prefix}_sec"]
        }
        response = requests.post(url, headers={"content-type": "application/json"}, json=body)
        self.access_token = response.json()["access_token"]
        self.token_expires = datetime.now() + timedelta(hours=23)
    
    def _get_headers(self, tr_id: str) -> dict:
        if datetime.now() >= self.token_expires:
            self._get_access_token()
        key_prefix = "paper" if self.paper_trading else "my"
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.config[f"{key_prefix}_app"],
            "appsecret": self.config[f"{key_prefix}_sec"],
            "tr_id": tr_id
        }
    
    def get_stock_price(self, stock_code: str) -> dict:
        self.rate_limiter.wait()
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": stock_code}
        return requests.get(url, headers=self._get_headers("FHKST01010100"), params=params).json()
    
    def place_order(self, stock_code: str, quantity: int, direction: str, 
                   order_type: str = "01", price: int = 0) -> dict:
        self.rate_limiter.wait()
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
        tr_id = ("VTTC0802U" if self.paper_trading else "TTTC0802U") if direction == "BUY" else \
                ("VTTC0801U" if self.paper_trading else "TTTC0801U")
        body = {
            "CANO": self.config["my_acct_stock"], "ACNT_PRDT_CD": self.config["my_prod"],
            "PDNO": stock_code, "ORD_DVSN": order_type, "ORD_QTY": str(quantity), "ORD_UNPR": str(price)
        }
        return requests.post(url, headers=self._get_headers(tr_id), json=body).json()
    
    def get_balance(self) -> dict:
        self.rate_limiter.wait()
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        tr_id = "VTTC8434R" if self.paper_trading else "TTTC8434R"
        params = {"CANO": self.config["my_acct_stock"], "ACNT_PRDT_CD": self.config["my_prod"],
                  "AFHR_FLPR_YN": "N", "INQR_DVSN": "02", "UNPR_DVSN": "01", "FUND_STTL_ICLD_YN": "N",
                  "FNCG_AMT_AUTO_RDPT_YN": "N", "PRCS_DVSN": "01", "CTX_AREA_FK100": "", "CTX_AREA_NK100": ""}
        return requests.get(url, headers=self._get_headers(tr_id), params=params).json()
    
    # 미국 주식
    def place_us_order(self, symbol: str, quantity: int, price: float, 
                       direction: str, exchange: str = "NASD") -> dict:
        self.rate_limiter.wait()
        url = f"{self.base_url}/uapi/overseas-stock/v1/trading/order"
        tr_id = ("VTTT1002U" if self.paper_trading else "JTTT1002U") if direction == "BUY" else \
                ("VTTT1001U" if self.paper_trading else "JTTT1001U")
        body = {
            "CANO": self.config["my_acct_stock"], "ACNT_PRDT_CD": self.config["my_prod"],
            "OVRS_EXCG_CD": exchange, "PDNO": symbol, "ORD_QTY": str(quantity),
            "OVRS_ORD_UNPR": str(price), "ORD_SVR_DVSN_CD": "0"
        }
        return requests.post(url, headers=self._get_headers(tr_id), json=body).json()
```

### 2.2 실시간 WebSocket 핸들러
```python
# src/data/realtime_handler.py
class RealtimeDataHandler:
    def __init__(self, broker: KISBroker):
        self.broker = broker
        self.ws = None
        self.callbacks = {}
        
    async def connect(self):
        self.ws = await websockets.connect(self.broker.ws_url, ping_interval=30)
        asyncio.create_task(self._receive_loop())
    
    async def subscribe_price(self, stock_code: str, callback):
        await self._subscribe("H0STCNT0", stock_code, callback)
    
    async def subscribe_orderbook(self, stock_code: str, callback):
        await self._subscribe("H0STASP0", stock_code, callback)
    
    async def _subscribe(self, tr_id: str, tr_key: str, callback):
        msg = {"header": {"approval_key": self.broker.ws_approval_key, "custtype": "P",
                         "tr_type": "1", "content-type": "utf-8"},
               "body": {"input": {"tr_id": tr_id, "tr_key": tr_key}}}
        await self.ws.send(json.dumps(msg))
        self.callbacks[f"{tr_id}:{tr_key}"] = callback
```

---

## Part 3: 기술적 분석 전략

### 3.1 이동평균 크로스오버
```python
# src/strategies/technical/ma_crossover.py
class MACrossoverStrategy(BaseStrategy):
    def __init__(self, symbols, fast_period=10, slow_period=30, use_ema=False):
        super().__init__("MA_Crossover", symbols)
        self.fast_period, self.slow_period, self.use_ema = fast_period, slow_period, use_ema
    
    def calculate_signals(self, data: pd.DataFrame):
        signals = []
        for symbol in self.symbols:
            close = data[symbol]
            if self.use_ema:
                fast_ma = close.ewm(span=self.fast_period, adjust=False).mean()
                slow_ma = close.ewm(span=self.slow_period, adjust=False).mean()
            else:
                fast_ma = close.rolling(self.fast_period).mean()
                slow_ma = close.rolling(self.slow_period).mean()
            
            # 골든크로스/데드크로스 감지
            if fast_ma.iloc[-2] <= slow_ma.iloc[-2] and fast_ma.iloc[-1] > slow_ma.iloc[-1]:
                signals.append(SignalEvent(symbol=symbol, signal_type="LONG", strength=0.8))
            elif fast_ma.iloc[-2] >= slow_ma.iloc[-2] and fast_ma.iloc[-1] < slow_ma.iloc[-1]:
                signals.append(SignalEvent(symbol=symbol, signal_type="EXIT", strength=0.8))
        return signals
```

### 3.2 RSI 전략
```python
# src/strategies/technical/rsi_strategy.py
class RSIStrategy(BaseStrategy):
    def __init__(self, symbols, period=14, overbought=70, oversold=30):
        super().__init__("RSI", symbols)
        self.period, self.overbought, self.oversold = period, overbought, oversold
    
    def _calculate_rsi(self, prices):
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.period).mean()
        return 100 - (100 / (1 + gain / loss))
    
    def calculate_signals(self, data):
        signals = []
        for symbol in self.symbols:
            rsi = self._calculate_rsi(data[symbol])
            if rsi.iloc[-2] < self.oversold and rsi.iloc[-1] >= self.oversold:
                signals.append(SignalEvent(symbol=symbol, signal_type="LONG", strength=0.7))
            elif rsi.iloc[-2] > self.overbought and rsi.iloc[-1] <= self.overbought:
                signals.append(SignalEvent(symbol=symbol, signal_type="EXIT", strength=0.7))
        return signals
```

### 3.3 볼린저 밴드 + MFI 전략
```python
# src/strategies/technical/bollinger.py
class BollingerBandStrategy(BaseStrategy):
    def __init__(self, symbols, window=20, num_std=2.0, mfi_period=10):
        super().__init__("Bollinger", symbols)
        self.window, self.num_std, self.mfi_period = window, num_std, mfi_period
    
    def calculate_signals(self, data):
        signals = []
        for symbol in self.symbols:
            close = data[f"{symbol}_close"]
            middle = close.rolling(self.window).mean()
            std = close.rolling(self.window).std()
            pb = (close - (middle - self.num_std * std)) / (2 * self.num_std * std)  # %b
            
            # MFI 계산
            typical_price = (data[f"{symbol}_high"] + data[f"{symbol}_low"] + close) / 3
            mfi = self._calculate_mfi(typical_price, data[f"{symbol}_volume"])
            
            if pb.iloc[-1] > 0.8 and mfi.iloc[-1] > 80:
                signals.append(SignalEvent(symbol=symbol, signal_type="LONG", strength=pb.iloc[-1]))
            elif pb.iloc[-1] < 0.2 and mfi.iloc[-1] < 20:
                signals.append(SignalEvent(symbol=symbol, signal_type="EXIT", strength=1-pb.iloc[-1]))
        return signals
```

### 3.4 변동성 돌파 전략
```python
# src/strategies/statistical/volatility_breakout.py
class VolatilityBreakoutStrategy(BaseStrategy):
    def __init__(self, symbols, k=0.5, whipsaw_filter=0.07):
        super().__init__("VolatilityBreakout", symbols)
        self.k, self.whipsaw_filter = k, whipsaw_filter
    
    def calculate_signals(self, data):
        signals = []
        for symbol in self.symbols:
            prev = data.iloc[-2]
            today = data.iloc[-1]
            
            # 휩소 필터
            if abs(prev[f"{symbol}_open"] - prev[f"{symbol}_close"]) / prev[f"{symbol}_open"] > self.whipsaw_filter:
                continue
            
            # 목표가 = 금일 시가 + (전일 고가 - 전일 저가) × K
            target_price = today[f"{symbol}_open"] + \
                          (prev[f"{symbol}_high"] - prev[f"{symbol}_low"]) * self.k
            
            if today[f"{symbol}_close"] > target_price:
                signals.append(SignalEvent(symbol=symbol, signal_type="LONG", strength=0.9))
        return signals
```

---

## Part 4: 통계적 차익거래 전략

### 4.1 페어 트레이딩 (공적분 기반)
```python
# src/strategies/statistical/pair_trading.py
from statsmodels.tsa.stattools import coint
import statsmodels.api as sm

class PairTradingStrategy(BaseStrategy):
    def __init__(self, pair, lookback=60, entry_zscore=2.0, exit_zscore=0.5):
        super().__init__("PairTrading", list(pair))
        self.stock1, self.stock2 = pair
        self.lookback, self.entry_zscore, self.exit_zscore = lookback, entry_zscore, exit_zscore
        self.position = 0  # 1: long spread, -1: short spread
    
    @staticmethod
    def find_cointegrated_pairs(prices, significance=0.05):
        symbols = prices.columns.tolist()
        pairs = []
        for i in range(len(symbols)):
            for j in range(i+1, len(symbols)):
                _, pvalue, _ = coint(prices[symbols[i]], prices[symbols[j]])
                if pvalue < significance:
                    pairs.append((symbols[i], symbols[j], pvalue))
        return sorted(pairs, key=lambda x: x[2])
    
    def calculate_signals(self, data):
        signals = []
        p1, p2 = data[self.stock1][-self.lookback:], data[self.stock2][-self.lookback:]
        
        # OLS 헤지 비율
        X = sm.add_constant(p1)
        hedge_ratio = sm.OLS(p2, X).fit().params[1]
        
        # 스프레드 및 Z-Score
        spread = p2 - hedge_ratio * p1
        zscore = (spread - spread.mean()) / spread.std()
        z = zscore.iloc[-1]
        
        if self.position == 0:
            if z < -self.entry_zscore:  # Long spread
                self.position = 1
                signals.extend([
                    SignalEvent(symbol=self.stock2, signal_type="LONG", strength=abs(z)/self.entry_zscore),
                    SignalEvent(symbol=self.stock1, signal_type="SHORT", strength=abs(z)/self.entry_zscore)
                ])
            elif z > self.entry_zscore:  # Short spread
                self.position = -1
                signals.extend([
                    SignalEvent(symbol=self.stock2, signal_type="SHORT", strength=abs(z)/self.entry_zscore),
                    SignalEvent(symbol=self.stock1, signal_type="LONG", strength=abs(z)/self.entry_zscore)
                ])
        elif abs(z) < self.exit_zscore:  # 평균 회귀 청산
            signals.extend([
                SignalEvent(symbol=self.stock1, signal_type="EXIT", strength=1.0),
                SignalEvent(symbol=self.stock2, signal_type="EXIT", strength=1.0)
            ])
            self.position = 0
        return signals
```

### 4.2 칼만 필터 동적 헤지 비율
```python
# src/strategies/statistical/kalman_pairs.py
from pykalman import KalmanFilter

class KalmanPairTrading(PairTradingStrategy):
    def __init__(self, pair, delta=1e-5, **kwargs):
        super().__init__(pair, **kwargs)
        self.delta = delta
        self.kf = KalmanFilter(n_dim_obs=1, n_dim_state=2,
                               initial_state_mean=np.zeros(2),
                               initial_state_covariance=np.ones((2, 2)),
                               transition_matrices=np.eye(2),
                               observation_covariance=1.0,
                               transition_covariance=delta / (1 - delta) * np.eye(2))
    
    def estimate_hedge_ratio(self, p1, p2):
        obs_mat = np.column_stack([p1.values, np.ones(len(p1))])[:, :, np.newaxis]
        self.kf.observation_matrices = obs_mat
        state_means, _ = self.kf.filter(p2.values)
        return state_means[-1, 0]  # 동적 헤지 비율
```

---

## Part 5: 딥러닝 모델

### 5.1 LSTM 시계열 예측
```python
# src/models/deep_learning/lstm.py
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

class LSTMModel(nn.Module):
    def __init__(self, input_size=5, hidden_size=64, num_layers=2, dropout=0.2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True, dropout=dropout)
        self.fc = nn.Sequential(nn.Linear(hidden_size, hidden_size//2), nn.ReLU(),
                                nn.Dropout(dropout), nn.Linear(hidden_size//2, 1))
    
    def forward(self, x):
        h0 = torch.zeros(2, x.size(0), 64).to(x.device)
        c0 = torch.zeros(2, x.size(0), 64).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        return self.fc(out[:, -1, :])

class LSTMPredictor:
    def __init__(self, window_size=20, features=['open','high','low','close','volume']):
        self.window_size, self.features = window_size, features
        self.scaler = MinMaxScaler()
        self.model = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    def prepare_data(self, data):
        scaled = self.scaler.fit_transform(data[self.features].values)
        X, y = [], []
        for i in range(self.window_size, len(scaled)):
            X.append(scaled[i-self.window_size:i])
            y.append(scaled[i, 3])  # close
        return np.array(X), np.array(y)
    
    def train(self, data, epochs=100, batch_size=32, lr=0.001):
        X, y = self.prepare_data(data)
        split = int(len(X) * 0.8)
        X_train, y_train = torch.FloatTensor(X[:split]).to(self.device), torch.FloatTensor(y[:split]).unsqueeze(1).to(self.device)
        
        self.model = LSTMModel(input_size=len(self.features)).to(self.device)
        criterion, optimizer = nn.MSELoss(), torch.optim.Adam(self.model.parameters(), lr=lr)
        
        for epoch in range(epochs):
            self.model.train()
            optimizer.zero_grad()
            loss = criterion(self.model(X_train), y_train)
            loss.backward()
            optimizer.step()
    
    def predict(self, data):
        self.model.eval()
        recent = self.scaler.transform(data[self.features].values[-self.window_size:])
        X = torch.FloatTensor(recent).unsqueeze(0).to(self.device)
        with torch.no_grad():
            pred = self.model(X).cpu().numpy()[0, 0]
        dummy = np.zeros((1, len(self.features)))
        dummy[0, 3] = pred
        return self.scaler.inverse_transform(dummy)[0, 3]
```

### 5.2 Transformer 시계열 예측
```python
# src/models/deep_learning/transformer.py
class TransformerModel(nn.Module):
    def __init__(self, input_window, output_window, d_model=512, nhead=8, num_layers=4, dropout=0.1):
        super().__init__()
        self.encoder_input = nn.Sequential(nn.Linear(1, d_model//2), nn.ReLU(), nn.Linear(d_model//2, d_model))
        self.pos_encoder = PositionalEncoding(d_model, dropout)
        encoder_layer = nn.TransformerEncoderLayer(d_model, nhead, dropout=dropout, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers)
        self.decoder = nn.Sequential(nn.Linear(d_model, d_model//2), nn.ReLU(), nn.Linear(d_model//2, 1))
        self.seq_transform = nn.Sequential(nn.Linear(input_window, (input_window+output_window)//2),
                                           nn.ReLU(), nn.Linear((input_window+output_window)//2, output_window))
    
    def forward(self, src):
        src = self.encoder_input(src)
        src = self.pos_encoder(src)
        out = self.transformer(src)
        out = self.decoder(out)[:, :, 0]
        return self.seq_transform(out)
```

### 5.3 DQN 강화학습 에이전트
```python
# src/models/deep_learning/dqn_agent.py
from collections import namedtuple, deque
import random

Transition = namedtuple('Transition', ('state', 'action', 'next_state', 'reward'))

class ReplayMemory:
    def __init__(self, capacity=10000):
        self.memory = deque([], maxlen=capacity)
    def push(self, *args): self.memory.append(Transition(*args))
    def sample(self, batch_size): return random.sample(self.memory, batch_size)
    def __len__(self): return len(self.memory)

class DQN(nn.Module):
    def __init__(self, n_observations, n_actions):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(n_observations, 128), nn.ReLU(),
                                 nn.Linear(128, 128), nn.ReLU(), nn.Linear(128, n_actions))
    def forward(self, x): return self.net(x)

class DQNAgent:
    def __init__(self, state_dim, action_dim=3, gamma=0.99, lr=3e-4, batch_size=128,
                 eps_start=0.9, eps_end=0.01, eps_decay=2500, tau=0.005):
        self.action_dim, self.gamma, self.batch_size = action_dim, gamma, batch_size
        self.eps_start, self.eps_end, self.eps_decay, self.tau = eps_start, eps_end, eps_decay, tau
        self.steps_done = 0
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        self.policy_net = DQN(state_dim, action_dim).to(self.device)
        self.target_net = DQN(state_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
        self.optimizer = torch.optim.Adam(self.policy_net.parameters(), lr=lr)
        self.memory = ReplayMemory(10000)
    
    def select_action(self, state):
        eps = self.eps_end + (self.eps_start - self.eps_end) * np.exp(-self.steps_done / self.eps_decay)
        self.steps_done += 1
        if random.random() > eps:
            with torch.no_grad():
                return self.policy_net(state).max(1)[1].view(1, 1)
        return torch.tensor([[random.randrange(self.action_dim)]], device=self.device)
    
    def optimize(self):
        if len(self.memory) < self.batch_size: return
        transitions = self.memory.sample(self.batch_size)
        batch = Transition(*zip(*transitions))
        
        state_batch = torch.cat(batch.state)
        action_batch = torch.cat(batch.action)
        reward_batch = torch.cat(batch.reward)
        non_final_mask = torch.tensor([s is not None for s in batch.next_state], device=self.device)
        non_final_next = torch.cat([s for s in batch.next_state if s is not None])
        
        state_action_values = self.policy_net(state_batch).gather(1, action_batch)
        next_state_values = torch.zeros(self.batch_size, device=self.device)
        with torch.no_grad():
            next_state_values[non_final_mask] = self.target_net(non_final_next).max(1)[0]
        expected = reward_batch + self.gamma * next_state_values
        
        loss = nn.functional.smooth_l1_loss(state_action_values, expected.unsqueeze(1))
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Soft update
        for tp, pp in zip(self.target_net.parameters(), self.policy_net.parameters()):
            tp.data.copy_(self.tau * pp.data + (1 - self.tau) * tp.data)
```

---

## Part 6: 리스크 관리

### 6.1 VaR/CVaR 계산
```python
# src/risk/var_cvar.py
from scipy import stats

class RiskCalculator:
    @staticmethod
    def historical_var(returns, confidence=0.95):
        return np.percentile(returns, (1 - confidence) * 100)
    
    @staticmethod
    def historical_cvar(returns, confidence=0.95):
        var = RiskCalculator.historical_var(returns, confidence)
        return returns[returns < var].mean()
    
    @staticmethod
    def parametric_var(returns, confidence=0.95):
        return returns.mean() + stats.norm.ppf(1 - confidence) * returns.std()
    
    @staticmethod
    def monte_carlo_var(returns, initial_value, n_simulations=10000, horizon=252, confidence=0.95):
        dfree, mu, std = stats.t.fit(returns)
        random_returns = stats.t.rvs(df=dfree, loc=mu, scale=std, size=(n_simulations, horizon))
        final_values = initial_value * np.cumprod(1 + random_returns, axis=1)[:, -1]
        var_index = int(len(final_values) * (1 - confidence))
        return initial_value - np.sort(final_values)[var_index]
```

### 6.2 포지션 사이징
```python
# src/risk/position_sizing.py
class PositionSizer:
    @staticmethod
    def kelly_criterion(win_rate, win_loss_ratio):
        return max(0, win_rate - (1 - win_rate) / win_loss_ratio)
    
    @staticmethod
    def volatility_sizing(portfolio_value, target_risk_pct, asset_volatility, asset_price):
        risk_amount = portfolio_value * target_risk_pct
        return int(risk_amount / (asset_volatility * asset_price))
    
    @staticmethod
    def atr_sizing(portfolio_value, atr, risk_factor=0.001):
        return portfolio_value * risk_factor / atr
```

### 6.3 HMM 레짐 디텍션
```python
# src/models/time_series/hmm_regime.py
from hmmlearn.hmm import GaussianHMM

class RegimeDetector:
    def __init__(self, n_states=2, n_iter=1000):
        self.n_states, self.n_iter = n_states, n_iter
        self.model = None
    
    def fit(self, returns):
        features = np.column_stack([returns, returns.rolling(20).std().fillna(0)])
        self.model = GaussianHMM(n_components=self.n_states, covariance_type='full', n_iter=self.n_iter)
        self.model.fit(features[20:])
        return self
    
    def predict_regime(self, returns):
        features = np.column_stack([returns, returns.rolling(20).std().fillna(0)])
        return self.model.predict(features[20:])[-1]
    
    def get_regime_stats(self, returns):
        states = self.predict_regime(returns)
        return {i: {'mean': returns[states == i].mean(), 'vol': returns[states == i].std()}
                for i in range(self.n_states)}
```

---

## Part 7: 백테스팅 프레임워크

### 7.1 이벤트 드리븐 백테스터
```python
# src/backtesting/backtest_engine.py
from queue import Queue

class BacktestEngine:
    def __init__(self, data_handler, strategy, portfolio, execution_handler, initial_capital=100000000):
        self.data_handler = data_handler
        self.strategy = strategy
        self.portfolio = portfolio
        self.execution_handler = execution_handler
        self.events = Queue()
        self.initial_capital = initial_capital
    
    def run(self):
        while self.data_handler.continue_backtest:
            self.data_handler.update_bars()
            
            while not self.events.empty():
                event = self.events.get()
                if event.type == EventType.MARKET:
                    signals = self.strategy.calculate_signals(event.data)
                    for signal in signals:
                        self.events.put(signal)
                elif event.type == EventType.SIGNAL:
                    order = self.portfolio.generate_order(event)
                    if order:
                        self.events.put(order)
                elif event.type == EventType.ORDER:
                    fill = self.execution_handler.execute_order(event)
                    self.events.put(fill)
                elif event.type == EventType.FILL:
                    self.portfolio.update_fill(event)
        
        return self.portfolio.get_performance()
```

### 7.2 성과 지표 계산
```python
# src/backtesting/performance.py
class PerformanceAnalyzer:
    @staticmethod
    def sharpe_ratio(returns, rf=0.0, periods=252):
        excess = returns - rf / periods
        return np.sqrt(periods) * excess.mean() / excess.std()
    
    @staticmethod
    def sortino_ratio(returns, rf=0.0, periods=252):
        excess = returns - rf / periods
        downside = returns[returns < 0].std()
        return np.sqrt(periods) * excess.mean() / downside
    
    @staticmethod
    def max_drawdown(equity_curve):
        peak = equity_curve.expanding().max()
        drawdown = (equity_curve - peak) / peak
        return drawdown.min()
    
    @staticmethod
    def calmar_ratio(returns, periods=252):
        cagr = returns.mean() * periods
        mdd = PerformanceAnalyzer.max_drawdown((1 + returns).cumprod())
        return cagr / abs(mdd)
```

### 7.3 Optuna 하이퍼파라미터 최적화
```python
# src/backtesting/optuna_optimizer.py
import optuna

class StrategyOptimizer:
    def __init__(self, strategy_class, data, n_trials=100):
        self.strategy_class = strategy_class
        self.data = data
        self.n_trials = n_trials
    
    def objective(self, trial):
        params = {
            'fast_period': trial.suggest_int('fast_period', 5, 50),
            'slow_period': trial.suggest_int('slow_period', 20, 200),
            'stop_loss': trial.suggest_float('stop_loss', 0.01, 0.1),
        }
        
        strategy = self.strategy_class(**params)
        result = self.run_backtest(strategy)
        return result['sharpe_ratio']
    
    def optimize(self):
        study = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler())
        study.optimize(self.objective, n_trials=self.n_trials)
        return study.best_params, study.best_value
```

---

## Part 8: MLOps 파이프라인

### 8.1 MLflow 모델 관리
```python
# src/mlops/model_registry.py
import mlflow
import mlflow.pytorch

class MLOpsManager:
    def __init__(self, experiment_name="trading_models"):
        mlflow.set_experiment(experiment_name)
    
    def train_and_log(self, model, params, train_data, val_data):
        with mlflow.start_run():
            mlflow.log_params(params)
            
            # 학습
            model.train(train_data)
            metrics = model.evaluate(val_data)
            
            mlflow.log_metrics(metrics)
            mlflow.pytorch.log_model(model, "model")
            
            # 모델 등록
            model_uri = f"runs:/{mlflow.active_run().info.run_id}/model"
            mlflow.register_model(model_uri, "trading_model")
    
    def load_best_model(self, model_name="trading_model"):
        client = mlflow.tracking.MlflowClient()
        latest = client.get_latest_versions(model_name, stages=["Production"])
        return mlflow.pytorch.load_model(latest[0].source)
```

### 8.2 모델 모니터링 및 재학습
```python
# src/mlops/monitoring.py
class ModelMonitor:
    def __init__(self, threshold=0.1):
        self.threshold = threshold
        self.baseline_metrics = None
    
    def detect_drift(self, current_metrics):
        if self.baseline_metrics is None:
            self.baseline_metrics = current_metrics
            return False
        drift = abs(current_metrics['sharpe'] - self.baseline_metrics['sharpe']) / self.baseline_metrics['sharpe']
        return drift > self.threshold
    
    def should_retrain(self, recent_performance):
        return self.detect_drift(recent_performance)

class AutoRetrainer:
    def __init__(self, mlops_manager, data_fetcher, model_class):
        self.mlops = mlops_manager
        self.data_fetcher = data_fetcher
        self.model_class = model_class
    
    def retrain(self, lookback_days=365):
        data = self.data_fetcher.get_historical_data(days=lookback_days)
        train, val = data[:int(len(data)*0.8)], data[int(len(data)*0.8):]
        
        model = self.model_class()
        self.mlops.train_and_log(model, model.get_params(), train, val)
```

---

## Part 9: 메인 트레이딩 시스템

### 9.1 통합 시스템
```python
# src/core/trading_system.py
import asyncio

class TradingSystem:
    def __init__(self, config_path: str):
        # 초기화
        self.broker = KISBroker(config_path, paper_trading=True)
        self.realtime = RealtimeDataHandler(self.broker)
        self.feature_store = FeatureStore()
        
        # 전략
        self.strategies = [
            MACrossoverStrategy(symbols=['005930', '000660'], fast_period=10, slow_period=30),
            RSIStrategy(symbols=['005930', '000660'], period=14),
            BollingerBandStrategy(symbols=['005930', '000660']),
        ]
        
        # 모델
        self.lstm_predictor = LSTMPredictor(window_size=20)
        self.regime_detector = RegimeDetector(n_states=2)
        
        # 리스크 관리
        self.risk_calc = RiskCalculator()
        self.position_sizer = PositionSizer()
        
        # 앙상블 가중치
        self.ensemble_weights = {'MA_Crossover': 0.3, 'RSI': 0.2, 'Bollinger': 0.2, 'LSTM': 0.3}
    
    async def run(self):
        await self.realtime.connect()
        
        for symbol in ['005930', '000660']:
            await self.realtime.subscribe_price(symbol, self.on_price_update)
        
        while True:
            await asyncio.sleep(60)  # 1분 루프
            await self.trading_loop()
    
    async def on_price_update(self, data):
        self.feature_store.update(data['stock_code'], data)
    
    async def trading_loop(self):
        for symbol in ['005930', '000660']:
            data = self.feature_store.get_features(symbol)
            
            # 레짐 체크
            returns = data['close'].pct_change().dropna()
            regime = self.regime_detector.predict_regime(returns)
            if regime == 1:  # 고변동성 레짐 - 신규 진입 금지
                continue
            
            # 앙상블 신호
            ensemble_signal = 0
            for strategy in self.strategies:
                signals = strategy.calculate_signals(data)
                for signal in signals:
                    if signal.symbol == symbol:
                        weight = self.ensemble_weights.get(strategy.name, 0.25)
                        ensemble_signal += weight * (1 if signal.signal_type == 'LONG' else -1) * signal.strength
            
            # LSTM 예측
            pred_price = self.lstm_predictor.predict(data)
            current_price = data['close'].iloc[-1]
            lstm_signal = (pred_price - current_price) / current_price
            ensemble_signal += self.ensemble_weights['LSTM'] * np.sign(lstm_signal) * min(abs(lstm_signal), 1)
            
            # 리스크 체크 및 주문
            if abs(ensemble_signal) > 0.5:
                portfolio_value = float(self.broker.get_balance()['output2'][0]['tot_evlu_amt'])
                var = self.risk_calc.historical_var(returns)
                
                if abs(var) < 0.05:  # VaR 5% 이내
                    qty = self.position_sizer.volatility_sizing(
                        portfolio_value, 0.01, returns.std(), current_price)
                    direction = "BUY" if ensemble_signal > 0 else "SELL"
                    
                    if qty > 0:
                        result = self.broker.place_order(symbol, qty, direction)
                        print(f"Order: {symbol} {direction} {qty} - {result}")

# main.py
if __name__ == "__main__":
    system = TradingSystem("config/kis_config.yaml")
    asyncio.run(system.run())
```

---

## Part 10: 설정 파일 예시

### kis_config.yaml
```yaml
# Production
my_app: "YOUR_PRODUCTION_APPKEY"
my_sec: "YOUR_PRODUCTION_APPSECRET"

# Paper Trading
paper_app: "YOUR_PAPER_APPKEY"
paper_sec: "YOUR_PAPER_APPSECRET"

# Account
my_htsid: "YOUR_HTS_ID"
my_acct_stock: "12345678"
my_prod: "01"
```

### requirements.txt
```
torch>=2.0.0
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.2.0
statsmodels>=0.14.0
scipy>=1.10.0
hmmlearn>=0.3.0
pykalman>=0.9.5
optuna>=3.0.0
mlflow>=2.0.0
websockets>=11.0
pyyaml>=6.0
requests>=2.28.0
arch>=6.0.0
cvxpy>=1.3.0
pypfopt>=1.5.0
riskfolio-lib>=4.0.0
```

---

## 구현 체크리스트

- [ ] 한국투자증권 계좌 개설 및 API 키 발급
- [ ] 모의투자 환경에서 전체 시스템 테스트
- [ ] 백테스팅으로 전략 검증 (최소 3년 데이터)
- [ ] Walk-Forward Optimization 실행
- [ ] VaR/CVaR 리스크 한도 설정
- [ ] HMM 레짐 디텍션 모델 학습
- [ ] LSTM/Transformer 모델 학습 및 검증
- [ ] DQN 에이전트 학습 (시뮬레이션 환경)
- [ ] MLflow 모델 레지스트리 설정
- [ ] 실시간 WebSocket 연결 테스트
- [ ] 실거래 전환 전 최소 1개월 페이퍼 트레이딩

이 프롬프트는 블로그 콘텐츠에서 추출한 알고리즘, 코드 패턴, 구현 방법론을 통합하여 **엔드투엔드 AI 자동매매 시스템**을 구축할 수 있는 상세한 가이드를 제공합니다.