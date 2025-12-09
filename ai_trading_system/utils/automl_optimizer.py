#!/usr/bin/env python3
"""
AutoML 기반 하이퍼파라미터 최적화
블로그 분석 기반 구현
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
import json
from pathlib import Path

try:
    import optuna
    from optuna.samplers import TPESampler
    HAS_OPTUNA = True
except ImportError:
    HAS_OPTUNA = False
    print("⚠️ Optuna 미설치로 기본 최적화만 가능합니다.")

logger = logging.getLogger('ai_trading.automl')


class AutoMLOptimizer:
    """AutoML 기반 하이퍼파라미터 최적화"""
    
    def __init__(self):
        self.optimization_history = []
        self.best_params = {}
        self.best_score = -float('inf')
        
        # 결과 저장 디렉토리
        self.results_dir = Path('optimization_results')
        self.results_dir.mkdir(exist_ok=True)
        
        logger.info("AutoML Optimizer initialized")
    
    def optimize_dqn_params(self, 
                           training_data: List[Dict],
                           n_trials: int = 50) -> Dict:
        """DQN 하이퍼파라미터 최적화"""
        
        if not HAS_OPTUNA:
            return self._fallback_dqn_optimization()
        
        def objective(trial):
            # DQN 하이퍼파라미터 공간 정의
            params = {
                'learning_rate': trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True),
                'batch_size': trial.suggest_categorical('batch_size', [16, 32, 64, 128]),
                'gamma': trial.suggest_float('gamma', 0.9, 0.999),
                'epsilon_decay': trial.suggest_float('epsilon_decay', 0.990, 0.999),
                'memory_size': trial.suggest_categorical('memory_size', [1000, 5000, 10000]),
                'update_target_freq': trial.suggest_int('update_target_freq', 10, 100),
                'reward_scale': trial.suggest_float('reward_scale', 10.0, 1000.0)
            }
            
            # 백테스트 성능 평가
            score = self._evaluate_dqn_params(params, training_data)
            
            return score
        
        # Optuna 스터디 생성
        study = optuna.create_study(
            direction='maximize',
            sampler=TPESampler(seed=42)
        )
        
        logger.info(f"DQN 하이퍼파라미터 최적화 시작: {n_trials} trials")
        
        study.optimize(objective, n_trials=n_trials)
        
        best_params = study.best_params
        best_score = study.best_value
        
        # 결과 저장
        self._save_optimization_results('dqn', best_params, best_score, study.trials)
        
        logger.info(f"DQN 최적화 완료: Best Score = {best_score:.4f}")
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'n_trials': len(study.trials)
        }
    
    def optimize_transformer_params(self,
                                  price_data: pd.DataFrame,
                                  n_trials: int = 30) -> Dict:
        """Transformer 하이퍼파라미터 최적화"""
        
        if not HAS_OPTUNA:
            return self._fallback_transformer_optimization()
        
        def objective(trial):
            params = {
                'd_model': trial.suggest_categorical('d_model', [32, 64, 128, 256]),
                'num_heads': trial.suggest_categorical('num_heads', [4, 8, 16]),
                'num_layers': trial.suggest_int('num_layers', 2, 8),
                'ff_dim': trial.suggest_categorical('ff_dim', [128, 256, 512]),
                'seq_length': trial.suggest_int('seq_length', 10, 60),
                'learning_rate': trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True),
                'dropout': trial.suggest_float('dropout', 0.0, 0.3)
            }
            
            score = self._evaluate_transformer_params(params, price_data)
            return score
        
        study = optuna.create_study(direction='minimize')  # Loss 최소화
        
        logger.info(f"Transformer 하이퍼파라미터 최적화 시작: {n_trials} trials")
        
        study.optimize(objective, n_trials=n_trials)
        
        best_params = study.best_params
        best_score = study.best_value
        
        self._save_optimization_results('transformer', best_params, best_score, study.trials)
        
        logger.info(f"Transformer 최적화 완료: Best Loss = {best_score:.6f}")
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'n_trials': len(study.trials)
        }
    
    def optimize_ensemble_weights(self,
                                validation_data: List[Dict],
                                n_trials: int = 100) -> Dict:
        """앙상블 가중치 최적화"""
        
        if not HAS_OPTUNA:
            return self._fallback_ensemble_optimization()
        
        def objective(trial):
            # 가중치 샘플링 (합이 1이 되도록)
            w_dqn = trial.suggest_float('w_dqn', 0.0, 1.0)
            w_technical = trial.suggest_float('w_technical', 0.0, 1.0 - w_dqn)
            w_factor = trial.suggest_float('w_factor', 0.0, 1.0 - w_dqn - w_technical)
            w_transformer = 1.0 - w_dqn - w_technical - w_factor
            
            weights = {
                'dqn_agent': w_dqn,
                'technical_agent': w_technical,
                'factor_agent': w_factor,
                'transformer_agent': w_transformer
            }
            
            score = self._evaluate_ensemble_weights(weights, validation_data)
            return score
        
        study = optuna.create_study(direction='maximize')
        
        logger.info(f"앙상블 가중치 최적화 시작: {n_trials} trials")
        
        study.optimize(objective, n_trials=n_trials)
        
        best_params = study.best_params
        best_score = study.best_value
        
        # 가중치 정규화
        best_weights = {
            'dqn_agent': best_params['w_dqn'],
            'technical_agent': best_params['w_technical'],
            'factor_agent': best_params['w_factor'],
            'transformer_agent': 1.0 - best_params['w_dqn'] - best_params['w_technical'] - best_params['w_factor']
        }
        
        self._save_optimization_results('ensemble', best_weights, best_score, study.trials)
        
        logger.info(f"앙상블 최적화 완료: Best Score = {best_score:.4f}")
        
        return {
            'best_weights': best_weights,
            'best_score': best_score,
            'n_trials': len(study.trials)
        }
    
    def _evaluate_dqn_params(self, params: Dict, training_data: List[Dict]) -> float:
        """DQN 파라미터 평가 (간단한 시뮬레이션)"""
        try:
            # 간단한 백테스팅 시뮬레이션
            total_return = 0
            trade_count = 0
            
            for data in training_data[:5]:  # 샘플만 사용
                returns = np.random.normal(0.001, 0.02, 30)  # 30일 시뮬레이션
                
                # 파라미터에 따른 성능 추정
                lr_factor = min(params['learning_rate'] * 1000, 1.0)
                gamma_factor = params['gamma']
                batch_factor = min(params['batch_size'] / 64, 2.0)
                
                performance = lr_factor * gamma_factor * batch_factor
                simulated_return = np.mean(returns) * performance
                
                total_return += simulated_return
                trade_count += 1
            
            return total_return / max(trade_count, 1)
            
        except Exception as e:
            logger.error(f"DQN 파라미터 평가 오류: {e}")
            return -1.0
    
    def _evaluate_transformer_params(self, params: Dict, price_data: pd.DataFrame) -> float:
        """Transformer 파라미터 평가 (간단한 손실 추정)"""
        try:
            # 모델 복잡도에 따른 손실 추정
            complexity = params['d_model'] * params['num_layers'] * params['num_heads']
            data_fit = min(len(price_data) / params['seq_length'], 10.0)
            
            # 복잡도와 데이터 적합도에 따른 손실 추정
            estimated_loss = 0.1 / (1 + data_fit) + complexity / 100000
            
            # 학습률에 따른 조정
            lr_factor = abs(np.log(params['learning_rate']))
            estimated_loss *= lr_factor / 10
            
            return estimated_loss
            
        except Exception as e:
            logger.error(f"Transformer 파라미터 평가 오류: {e}")
            return 1.0
    
    def _evaluate_ensemble_weights(self, weights: Dict, validation_data: List[Dict]) -> float:
        """앙상블 가중치 평가"""
        try:
            # 간단한 가중치 균형 평가
            weight_balance = 1.0 - np.std(list(weights.values()))
            
            # 다양성 보너스 (모든 에이전트가 참여하는지)
            diversity_bonus = len([w for w in weights.values() if w > 0.1]) / len(weights)
            
            return weight_balance * diversity_bonus
            
        except Exception as e:
            logger.error(f"앙상블 가중치 평가 오류: {e}")
            return 0.0
    
    def _fallback_dqn_optimization(self) -> Dict:
        """Optuna 미설치 시 기본 DQN 최적화"""
        logger.warning("Optuna 미설치로 기본 DQN 파라미터 사용")
        return {
            'best_params': {
                'learning_rate': 0.001,
                'batch_size': 64,
                'gamma': 0.99,
                'epsilon_decay': 0.995,
                'memory_size': 10000,
                'update_target_freq': 50,
                'reward_scale': 100.0
            },
            'best_score': 0.0,
            'n_trials': 0
        }
    
    def _fallback_transformer_optimization(self) -> Dict:
        """Optuna 미설치 시 기본 Transformer 최적화"""
        logger.warning("Optuna 미설치로 기본 Transformer 파라미터 사용")
        return {
            'best_params': {
                'd_model': 64,
                'num_heads': 8,
                'num_layers': 4,
                'ff_dim': 256,
                'seq_length': 30,
                'learning_rate': 0.001,
                'dropout': 0.1
            },
            'best_score': 0.1,
            'n_trials': 0
        }
    
    def _fallback_ensemble_optimization(self) -> Dict:
        """Optuna 미설치 시 기본 앙상블 가중치"""
        logger.warning("Optuna 미설치로 기본 앙상블 가중치 사용")
        return {
            'best_weights': {
                'dqn_agent': 0.3,
                'technical_agent': 0.25,
                'factor_agent': 0.25,
                'transformer_agent': 0.2
            },
            'best_score': 0.0,
            'n_trials': 0
        }
    
    def _save_optimization_results(self, 
                                 model_type: str, 
                                 best_params: Dict, 
                                 best_score: float,
                                 trials: List) -> None:
        """최적화 결과 저장"""
        result = {
            'model_type': model_type,
            'best_params': best_params,
            'best_score': best_score,
            'n_trials': len(trials),
            'timestamp': datetime.now().isoformat(),
            'optimization_history': [
                {
                    'trial_number': i,
                    'value': trial.value,
                    'params': trial.params
                }
                for i, trial in enumerate(trials)
            ]
        }
        
        filename = self.results_dir / f"{model_type}_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"최적화 결과 저장: {filename}")
    
    def load_best_params(self, model_type: str) -> Optional[Dict]:
        """저장된 최적 파라미터 로드"""
        pattern = f"{model_type}_optimization_*.json"
        files = list(self.results_dir.glob(pattern))
        
        if not files:
            logger.warning(f"{model_type} 최적화 결과 없음")
            return None
        
        # 가장 최근 파일 사용
        latest_file = max(files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            logger.info(f"{model_type} 최적 파라미터 로드: {latest_file}")
            return result['best_params']
            
        except Exception as e:
            logger.error(f"최적 파라미터 로드 실패: {e}")
            return None
    
    def schedule_optimization(self, 
                            schedule_config: Dict) -> Dict:
        """최적화 스케줄링 (주간/월간 자동 실행)"""
        
        # 스케줄링 로직 (실제 환경에서는 Airflow 등 사용)
        schedule_info = {
            'next_dqn_optimization': datetime.now() + timedelta(weeks=1),
            'next_transformer_optimization': datetime.now() + timedelta(weeks=2),
            'next_ensemble_optimization': datetime.now() + timedelta(days=3),
            'schedule_config': schedule_config
        }
        
        logger.info("최적화 스케줄 설정 완료")
        
        return schedule_info


class HyperparameterManager:
    """하이퍼파라미터 관리 클래스"""
    
    def __init__(self):
        self.optimizer = AutoMLOptimizer()
        self.current_params = {}
    
    def update_model_params(self, model_type: str, new_params: Dict) -> bool:
        """모델 파라미터 업데이트"""
        try:
            self.current_params[model_type] = new_params
            logger.info(f"{model_type} 파라미터 업데이트 완료")
            return True
        except Exception as e:
            logger.error(f"파라미터 업데이트 실패: {e}")
            return False
    
    def get_optimal_params(self, model_type: str) -> Dict:
        """최적 파라미터 조회"""
        # 저장된 최적 파라미터 우선 로드
        saved_params = self.optimizer.load_best_params(model_type)
        
        if saved_params:
            return saved_params
        
        # 없으면 기본값 사용
        fallback_methods = {
            'dqn': self.optimizer._fallback_dqn_optimization,
            'transformer': self.optimizer._fallback_transformer_optimization,
            'ensemble': self.optimizer._fallback_ensemble_optimization
        }
        
        if model_type in fallback_methods:
            result = fallback_methods[model_type]()
            return result.get('best_params', {})
        
        return {}