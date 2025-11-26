"""
AutoML 기반 전략 최적화
참조: https://twentytwentyone.tistory.com/1847

[주요 특징]
- Optuna를 활용한 하이퍼파라미터 자동 최적화
- MLflow로 실험 추적 및 모델 관리
- 자동으로 최적의 전략 파라미터 탐색
- 성능 기반 모델 자동 선택
"""

import optuna
import mlflow
import mlflow.pytorch
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os


class AutoMLOptimizer:
    """AutoML 기반 전략 최적화"""
    
    def __init__(self, api, strategy_name: str = "momentum"):
        self.api = api
        self.strategy_name = strategy_name
        
        # MLflow 설정
        mlflow.set_tracking_uri("file:///tmp/mlflow")
        mlflow.set_experiment(f"kis_trading_{strategy_name}")
        
        # 최적화 기록
        self.optimization_history = []
        self.best_params = None
        self.best_score = -float('inf')
        
    def objective(self, trial):
        """Optuna 목적 함수"""
        
        # 전략별 하이퍼파라미터 정의
        if self.strategy_name == "momentum":
            params = {
                'min_price': trial.suggest_int('min_price', 5000, 50000, step=5000),
                'max_price': trial.suggest_int('max_price', 50000, 500000, step=50000),
                'min_volume_ratio': trial.suggest_float('min_volume_ratio', 1.5, 5.0, step=0.5),
                'min_change_rate': trial.suggest_float('min_change_rate', 1.0, 5.0, step=0.5),
                'max_change_rate': trial.suggest_float('max_change_rate', 5.0, 20.0, step=1.0),
                'buy_rsi_min': trial.suggest_int('buy_rsi_min', 20, 40, step=5),
                'buy_rsi_max': trial.suggest_int('buy_rsi_max', 60, 80, step=5),
                'take_profit': trial.suggest_float('take_profit', 3.0, 10.0, step=1.0),
                'stop_loss': trial.suggest_float('stop_loss', -5.0, -1.0, step=0.5),
                'max_hold_days': trial.suggest_int('max_hold_days', 1, 5)
            }
        elif self.strategy_name == "volatility":
            params = {
                'k_value': trial.suggest_float('k_value', 0.3, 0.7, step=0.1),
                'min_price': trial.suggest_int('min_price', 5000, 50000, step=5000),
                'max_price': trial.suggest_int('max_price', 50000, 500000, step=50000),
                'min_volume_ratio': trial.suggest_float('min_volume_ratio', 1.0, 3.0, step=0.5),
                'target_stocks_count': trial.suggest_int('target_stocks_count', 3, 10)
            }
        elif self.strategy_name == "dqn":
            params = {
                'learning_rate': trial.suggest_loguniform('learning_rate', 1e-4, 1e-2),
                'gamma': trial.suggest_float('gamma', 0.9, 0.99),
                'epsilon_decay': trial.suggest_float('epsilon_decay', 0.99, 0.999),
                'hidden_size': trial.suggest_categorical('hidden_size', [64, 128, 256]),
                'batch_size': trial.suggest_categorical('batch_size', [16, 32, 64])
            }
        else:  # crewai
            params = {
                'scan_count': trial.suggest_int('scan_count', 30, 100, step=10),
                'buy_score_min': trial.suggest_int('buy_score_min', 50, 80, step=5),
                'min_volume_ratio': trial.suggest_float('min_volume_ratio', 1.5, 3.0, step=0.5),
                'max_stocks': trial.suggest_int('max_stocks', 3, 7),
                'position_ratio': trial.suggest_float('position_ratio', 0.1, 0.3, step=0.05)
            }
        
        # MLflow 실행 시작
        with mlflow.start_run():
            mlflow.log_params(params)
            
            # 백테스트 수행
            score = self.backtest_strategy(params)
            
            # 메트릭 기록
            mlflow.log_metric("sharpe_ratio", score['sharpe_ratio'])
            mlflow.log_metric("total_return", score['total_return'])
            mlflow.log_metric("max_drawdown", score['max_drawdown'])
            mlflow.log_metric("win_rate", score['win_rate'])
            
            # 결과 저장
            self.optimization_history.append({
                'trial': trial.number,
                'params': params,
                'score': score,
                'timestamp': datetime.now().isoformat()
            })
            
        return score['sharpe_ratio']  # 목적 함수는 샤프 비율 최대화
    
    def backtest_strategy(self, params: Dict) -> Dict:
        """전략 백테스트"""
        
        # 시뮬레이션 기간 (최근 3개월)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        # 초기 자금
        initial_balance = 10000000
        balance = initial_balance
        portfolio = {}
        trades = []
        daily_returns = []
        
        # 임시 전략 생성
        if self.strategy_name == "momentum":
            from strategies.momentum_strategy import MomentumStrategy
            strategy = MomentumStrategy(self.api, params)
        elif self.strategy_name == "volatility":
            from strategies.volatility_strategy import VolatilityStrategy
            strategy = VolatilityStrategy(self.api, params)
        elif self.strategy_name == "dqn":
            from strategies.dqn_strategy import DQNStrategy
            strategy = DQNStrategy(self.api, params)
        else:
            from strategies.crewai_strategy import CrewAIStrategy
            strategy = CrewAIStrategy(self.api, params)
        
        # 간단한 백테스트 시뮬레이션
        # 실제로는 과거 데이터로 정밀한 백테스트 필요
        simulated_trades = 30
        win_trades = 0
        
        for i in range(simulated_trades):
            # 랜덤 수익률 생성 (실제로는 전략 실행 결과 사용)
            trade_return = np.random.normal(0.002, 0.02)  # 평균 0.2%, 표준편차 2%
            
            # 전략 파라미터에 따른 조정
            if 'take_profit' in params:
                if trade_return > params['take_profit'] / 100:
                    trade_return = params['take_profit'] / 100
            if 'stop_loss' in params:
                if trade_return < params['stop_loss'] / 100:
                    trade_return = params['stop_loss'] / 100
            
            balance *= (1 + trade_return)
            daily_returns.append(trade_return)
            
            if trade_return > 0:
                win_trades += 1
                
        # 성과 지표 계산
        total_return = (balance - initial_balance) / initial_balance * 100
        
        if daily_returns:
            returns_array = np.array(daily_returns)
            sharpe_ratio = np.sqrt(252) * returns_array.mean() / (returns_array.std() + 1e-10)
            
            # 최대 낙폭 계산
            cumulative = np.cumprod(1 + returns_array)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = np.min(drawdown) * 100
        else:
            sharpe_ratio = 0
            max_drawdown = 0
            
        win_rate = (win_trades / simulated_trades * 100) if simulated_trades > 0 else 0
        
        return {
            'sharpe_ratio': sharpe_ratio,
            'total_return': total_return,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate
        }
    
    def optimize(self, n_trials: int = 100):
        """하이퍼파라미터 최적화 실행"""
        print(f"\n🔧 {self.strategy_name} 전략 AutoML 최적화 시작...")
        print(f"   목표: Sharpe Ratio 최대화")
        print(f"   시도 횟수: {n_trials}")
        
        # Optuna 스터디 생성
        study = optuna.create_study(
            direction='maximize',
            study_name=f'{self.strategy_name}_optimization'
        )
        
        # 최적화 실행
        study.optimize(self.objective, n_trials=n_trials)
        
        # 최적 파라미터 저장
        self.best_params = study.best_params
        self.best_score = study.best_value
        
        print(f"\n✅ 최적화 완료!")
        print(f"   최고 Sharpe Ratio: {self.best_score:.3f}")
        print(f"   최적 파라미터:")
        for key, value in self.best_params.items():
            print(f"      {key}: {value}")
            
        # 최적화 결과 저장
        self.save_results()
        
        return self.best_params
    
    def save_results(self):
        """최적화 결과 저장"""
        results = {
            'strategy': self.strategy_name,
            'best_params': self.best_params,
            'best_score': self.best_score,
            'optimization_history': self.optimization_history,
            'timestamp': datetime.now().isoformat()
        }
        
        # JSON 파일로 저장
        filename = f"optimization_{self.strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        print(f"   결과 저장: {filename}")
    
    def load_best_params(self, strategy_name: str) -> Optional[Dict]:
        """저장된 최적 파라미터 로드"""
        import glob
        
        # 가장 최근 최적화 결과 찾기
        pattern = f"optimization_{strategy_name}_*.json"
        files = glob.glob(pattern)
        
        if not files:
            return None
            
        # 가장 최근 파일
        latest_file = max(files, key=os.path.getmtime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
            
        return results.get('best_params')
    
    def continuous_optimization(self, interval_hours: int = 24):
        """지속적인 최적화 (주기적으로 실행)"""
        import time
        
        print(f"\n🔄 지속적 최적화 모드 시작 (주기: {interval_hours}시간)")
        
        while True:
            try:
                # 최적화 실행
                self.optimize(n_trials=50)
                
                # MLflow에 모델 등록
                if self.best_params:
                    with mlflow.start_run():
                        mlflow.log_params(self.best_params)
                        mlflow.log_metric("best_sharpe_ratio", self.best_score)
                        
                        # 모델 아티팩트 저장
                        mlflow.log_dict(self.best_params, "best_params.json")
                        
                print(f"\n💤 다음 최적화까지 {interval_hours}시간 대기...")
                time.sleep(interval_hours * 3600)
                
            except KeyboardInterrupt:
                print("\n최적화 중단")
                break
            except Exception as e:
                print(f"\n❌ 최적화 오류: {e}")
                print(f"💤 {interval_hours}시간 후 재시도...")
                time.sleep(interval_hours * 3600)
    
    def compare_strategies(self):
        """전략 간 성능 비교"""
        strategies = ["momentum", "volatility", "dqn", "crewai"]
        results = {}
        
        print("\n📊 전략 성능 비교 시작...")
        
        for strategy in strategies:
            print(f"\n{strategy} 전략 평가 중...")
            self.strategy_name = strategy
            
            # 기본 파라미터로 백테스트
            score = self.backtest_strategy({})
            results[strategy] = score
            
        # 결과 출력
        print("\n📈 전략 비교 결과:")
        print("-" * 60)
        print(f"{'전략':^15} {'Sharpe':^10} {'수익률(%)':^10} {'최대낙폭(%)':^12} {'승률(%)':^10}")
        print("-" * 60)
        
        for strategy, score in results.items():
            print(f"{strategy:^15} {score['sharpe_ratio']:^10.3f} "
                  f"{score['total_return']:^10.2f} {score['max_drawdown']:^12.2f} "
                  f"{score['win_rate']:^10.2f}")
                  
        # 최고 전략
        best_strategy = max(results.items(), key=lambda x: x[1]['sharpe_ratio'])
        print("\n🏆 최고 성능 전략:", best_strategy[0])