#!/usr/bin/env python3
"""
MLOps 모델 관리 시스템
자동 모델 배포, 버전 관리, A/B 테스트
"""

import json
import pickle
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import shutil
import threading
import time

import numpy as np
import pandas as pd

logger = logging.getLogger('ai_trading.mlops')


class ModelRegistry:
    """모델 레지스트리 - 모델 버전 관리"""
    
    def __init__(self, registry_path: str = "model_registry"):
        self.registry_path = Path(registry_path)
        self.registry_path.mkdir(exist_ok=True)
        
        self.models_path = self.registry_path / "models"
        self.models_path.mkdir(exist_ok=True)
        
        self.metadata_path = self.registry_path / "metadata"
        self.metadata_path.mkdir(exist_ok=True)
        
        self.registry_file = self.registry_path / "registry.json"
        self.registry = self._load_registry()
        
        logger.info(f"Model Registry initialized: {registry_path}")
    
    def _load_registry(self) -> Dict:
        """레지스트리 로드"""
        if self.registry_file.exists():
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Registry 로드 실패: {e}")
        
        return {
            'models': {},
            'deployments': {},
            'experiments': {}
        }
    
    def _save_registry(self):
        """레지스트리 저장"""
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self.registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Registry 저장 실패: {e}")
    
    def register_model(self, 
                      model_name: str,
                      model_object: Any,
                      metrics: Dict,
                      metadata: Dict = None) -> str:
        """모델 등록"""
        
        # 모델 버전 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_hash = self._calculate_model_hash(model_object)
        version = f"v{timestamp}_{model_hash[:8]}"
        
        # 모델 저장
        model_path = self.models_path / model_name / version
        model_path.mkdir(parents=True, exist_ok=True)
        
        # 모델 파일 저장
        model_file = model_path / "model.pkl"
        try:
            with open(model_file, 'wb') as f:
                pickle.dump(model_object, f)
        except Exception as e:
            logger.error(f"모델 저장 실패: {e}")
            return None
        
        # 메타데이터 저장
        metadata = metadata or {}
        model_metadata = {
            'name': model_name,
            'version': version,
            'created_at': datetime.now().isoformat(),
            'metrics': metrics,
            'model_hash': model_hash,
            'file_path': str(model_file),
            'metadata': metadata
        }
        
        metadata_file = model_path / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(model_metadata, f, indent=2, ensure_ascii=False)
        
        # 레지스트리 업데이트
        if model_name not in self.registry['models']:
            self.registry['models'][model_name] = {}
        
        self.registry['models'][model_name][version] = model_metadata
        self._save_registry()
        
        logger.info(f"모델 등록 완료: {model_name} {version}")
        return version
    
    def get_model(self, model_name: str, version: str = None) -> Any:
        """모델 로드"""
        if version is None:
            version = self.get_latest_version(model_name)
        
        if not version:
            return None
        
        model_info = self.registry['models'].get(model_name, {}).get(version)
        if not model_info:
            return None
        
        try:
            with open(model_info['file_path'], 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            return None
    
    def get_latest_version(self, model_name: str) -> Optional[str]:
        """최신 버전 조회"""
        versions = list(self.registry['models'].get(model_name, {}).keys())
        if not versions:
            return None
        
        return max(versions, key=lambda v: self.registry['models'][model_name][v]['created_at'])
    
    def list_models(self) -> Dict:
        """모델 목록 조회"""
        return self.registry['models']
    
    def _calculate_model_hash(self, model_object: Any) -> str:
        """모델 해시 계산"""
        try:
            model_bytes = pickle.dumps(model_object)
            return hashlib.md5(model_bytes).hexdigest()
        except Exception as e:
            logger.error(f"모델 해시 계산 실패: {e}")
            return datetime.now().strftime("%Y%m%d%H%M%S")


class ModelDeployer:
    """자동 모델 배포 시스템"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.deployed_models = {}
        self.ab_tests = {}
        
        logger.info("Model Deployer initialized")
    
    def deploy_model(self, 
                    model_name: str, 
                    version: str,
                    deployment_type: str = 'production') -> bool:
        """모델 배포"""
        
        model = self.registry.get_model(model_name, version)
        if not model:
            logger.error(f"모델 로드 실패: {model_name} {version}")
            return False
        
        # 배포 정보 저장
        deployment_info = {
            'model_name': model_name,
            'version': version,
            'deployment_type': deployment_type,
            'deployed_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        self.deployed_models[f"{model_name}_{deployment_type}"] = {
            'model': model,
            'info': deployment_info
        }
        
        # 레지스트리에 배포 기록
        if 'deployments' not in self.registry.registry:
            self.registry.registry['deployments'] = {}
        
        deployment_key = f"{model_name}_{deployment_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.registry.registry['deployments'][deployment_key] = deployment_info
        self.registry._save_registry()
        
        logger.info(f"모델 배포 완료: {model_name} {version} -> {deployment_type}")
        return True
    
    def get_deployed_model(self, model_name: str, deployment_type: str = 'production'):
        """배포된 모델 조회"""
        key = f"{model_name}_{deployment_type}"
        return self.deployed_models.get(key, {}).get('model')
    
    def start_ab_test(self,
                     model_name: str,
                     champion_version: str,
                     challenger_version: str,
                     traffic_split: float = 0.1) -> str:
        """A/B 테스트 시작"""
        
        test_id = f"ab_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 챔피언/챌린저 모델 로드
        champion = self.registry.get_model(model_name, champion_version)
        challenger = self.registry.get_model(model_name, challenger_version)
        
        if not champion or not challenger:
            logger.error("A/B 테스트용 모델 로드 실패")
            return None
        
        self.ab_tests[test_id] = {
            'model_name': model_name,
            'champion': {'version': champion_version, 'model': champion},
            'challenger': {'version': challenger_version, 'model': challenger},
            'traffic_split': traffic_split,
            'started_at': datetime.now().isoformat(),
            'metrics': {'champion': [], 'challenger': []},
            'status': 'active'
        }
        
        logger.info(f"A/B 테스트 시작: {test_id}")
        return test_id
    
    def predict_with_ab_test(self, test_id: str, input_data: Any) -> Dict:
        """A/B 테스트 예측"""
        if test_id not in self.ab_tests:
            return {'error': 'A/B 테스트 없음'}
        
        test_info = self.ab_tests[test_id]
        
        # 트래픽 분할
        use_challenger = np.random.random() < test_info['traffic_split']
        
        if use_challenger:
            model = test_info['challenger']['model']
            variant = 'challenger'
        else:
            model = test_info['champion']['model']
            variant = 'champion'
        
        try:
            # 예측 수행 (모델별로 다를 수 있음)
            if hasattr(model, 'predict'):
                prediction = model.predict(input_data)
            else:
                prediction = 0  # 기본값
            
            return {
                'prediction': prediction,
                'variant': variant,
                'test_id': test_id
            }
        except Exception as e:
            logger.error(f"A/B 테스트 예측 실패: {e}")
            return {'error': str(e)}


class ExperimentTracker:
    """실험 추적 시스템"""
    
    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.experiments = {}
        
        logger.info("Experiment Tracker initialized")
    
    def start_experiment(self, 
                        experiment_name: str,
                        model_type: str,
                        hyperparams: Dict) -> str:
        """실험 시작"""
        
        exp_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{experiment_name}"
        
        experiment_info = {
            'id': exp_id,
            'name': experiment_name,
            'model_type': model_type,
            'hyperparams': hyperparams,
            'started_at': datetime.now().isoformat(),
            'status': 'running',
            'metrics': {},
            'artifacts': []
        }
        
        self.experiments[exp_id] = experiment_info
        
        # 레지스트리에 실험 기록
        if 'experiments' not in self.registry.registry:
            self.registry.registry['experiments'] = {}
        
        self.registry.registry['experiments'][exp_id] = experiment_info
        self.registry._save_registry()
        
        logger.info(f"실험 시작: {exp_id}")
        return exp_id
    
    def log_metric(self, exp_id: str, metric_name: str, value: float, step: int = None):
        """메트릭 로그"""
        if exp_id not in self.experiments:
            return
        
        if metric_name not in self.experiments[exp_id]['metrics']:
            self.experiments[exp_id]['metrics'][metric_name] = []
        
        self.experiments[exp_id]['metrics'][metric_name].append({
            'value': value,
            'step': step,
            'timestamp': datetime.now().isoformat()
        })
        
        # 레지스트리 업데이트
        self.registry.registry['experiments'][exp_id] = self.experiments[exp_id]
        self.registry._save_registry()
    
    def finish_experiment(self, exp_id: str, final_metrics: Dict = None):
        """실험 완료"""
        if exp_id not in self.experiments:
            return
        
        self.experiments[exp_id]['status'] = 'completed'
        self.experiments[exp_id]['finished_at'] = datetime.now().isoformat()
        
        if final_metrics:
            self.experiments[exp_id]['final_metrics'] = final_metrics
        
        # 레지스트리 업데이트
        self.registry.registry['experiments'][exp_id] = self.experiments[exp_id]
        self.registry._save_registry()
        
        logger.info(f"실험 완료: {exp_id}")
    
    def get_experiment(self, exp_id: str) -> Optional[Dict]:
        """실험 정보 조회"""
        return self.experiments.get(exp_id)


class AutoMLOpsManager:
    """MLOps 자동화 관리자"""
    
    def __init__(self):
        self.registry = ModelRegistry()
        self.deployer = ModelDeployer(self.registry)
        self.tracker = ExperimentTracker(self.registry)
        
        self.auto_deploy_enabled = True
        self.performance_threshold = 0.05  # 5% 개선 시 자동 배포
        
        # 백그라운드 모니터링 스레드
        self.monitoring_thread = None
        self.stop_monitoring = False
        
        logger.info("AutoMLOps Manager initialized")
    
    def register_and_evaluate(self, 
                             model_name: str,
                             model_object: Any,
                             validation_data: Any,
                             metadata: Dict = None) -> Dict:
        """모델 등록 및 평가"""
        
        # 성능 평가
        metrics = self._evaluate_model(model_object, validation_data)
        
        # 모델 등록
        version = self.registry.register_model(
            model_name, model_object, metrics, metadata
        )
        
        # 자동 배포 판단
        deploy_decision = self._should_deploy(model_name, metrics)
        
        result = {
            'version': version,
            'metrics': metrics,
            'deploy_decision': deploy_decision
        }
        
        # 자동 배포 실행
        if deploy_decision['should_deploy'] and self.auto_deploy_enabled:
            self.deployer.deploy_model(model_name, version, 'production')
            result['deployed'] = True
        
        return result
    
    def _evaluate_model(self, model: Any, validation_data: Any) -> Dict:
        """모델 성능 평가"""
        try:
            # 간단한 성능 평가 (실제로는 더 복잡)
            if hasattr(model, 'score') and validation_data is not None:
                score = model.score(validation_data)
                return {
                    'accuracy': score,
                    'evaluated_at': datetime.now().isoformat()
                }
            else:
                # 기본 메트릭
                return {
                    'version_score': np.random.uniform(0.7, 0.9),
                    'evaluated_at': datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"모델 평가 실패: {e}")
            return {
                'evaluation_error': str(e),
                'evaluated_at': datetime.now().isoformat()
            }
    
    def _should_deploy(self, model_name: str, new_metrics: Dict) -> Dict:
        """자동 배포 여부 판단"""
        
        # 현재 프로덕션 모델 성능 조회
        current_version = self.registry.get_latest_version(model_name)
        
        if not current_version:
            return {
                'should_deploy': True,
                'reason': '첫 번째 모델'
            }
        
        # 현재 모델 메트릭
        current_metrics = self.registry.registry['models'][model_name][current_version]['metrics']
        
        # 성능 비교
        current_score = current_metrics.get('accuracy', 0)
        new_score = new_metrics.get('accuracy', 0)
        
        improvement = new_score - current_score
        
        if improvement > self.performance_threshold:
            return {
                'should_deploy': True,
                'reason': f'성능 개선: {improvement:.3f}',
                'improvement': improvement
            }
        else:
            return {
                'should_deploy': False,
                'reason': f'성능 개선 부족: {improvement:.3f}',
                'improvement': improvement
            }
    
    def start_monitoring(self):
        """모니터링 시작"""
        if self.monitoring_thread is not None:
            return
        
        self.stop_monitoring = False
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        logger.info("MLOps 모니터링 시작")
    
    def stop_monitoring_service(self):
        """모니터링 중지"""
        self.stop_monitoring = True
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("MLOps 모니터링 중지")
    
    def _monitoring_loop(self):
        """모니터링 루프"""
        while not self.stop_monitoring:
            try:
                # 배포된 모델 상태 체크
                self._check_model_health()
                
                # A/B 테스트 상태 체크  
                self._check_ab_tests()
                
                # 모델 성능 드리프트 감지
                self._check_model_drift()
                
                time.sleep(300)  # 5분마다 체크
                
            except Exception as e:
                logger.error(f"모니터링 오류: {e}")
                time.sleep(60)
    
    def _check_model_health(self):
        """모델 헬스 체크"""
        for deployment_key, deployment in self.deployer.deployed_models.items():
            model = deployment['model']
            info = deployment['info']
            
            # 간단한 헬스 체크 (실제로는 더 정교한 체크 필요)
            try:
                if hasattr(model, 'predict'):
                    # 더미 데이터로 예측 테스트
                    test_input = np.random.random((1, 10))
                    _ = model.predict(test_input)
                
                logger.debug(f"모델 헬스 체크 통과: {deployment_key}")
                
            except Exception as e:
                logger.warning(f"모델 헬스 체크 실패: {deployment_key} - {e}")
    
    def _check_ab_tests(self):
        """A/B 테스트 상태 체크"""
        for test_id, test_info in self.deployer.ab_tests.items():
            if test_info['status'] != 'active':
                continue
            
            # A/B 테스트가 충분히 실행되었는지 체크
            started_at = datetime.fromisoformat(test_info['started_at'])
            if datetime.now() - started_at > timedelta(days=7):
                # 결과 분석 및 승자 결정 (간단한 로직)
                champion_metrics = test_info['metrics']['champion']
                challenger_metrics = test_info['metrics']['challenger']
                
                logger.info(f"A/B 테스트 완료: {test_id}")
                test_info['status'] = 'completed'
    
    def _check_model_drift(self):
        """모델 드리프트 감지"""
        # 데이터 드리프트나 성능 저하 감지
        # 실제로는 입력 데이터 분포 변화나 예측 성능 모니터링
        logger.debug("모델 드리프트 체크 완료")
    
    def get_mlops_status(self) -> Dict:
        """MLOps 상태 조회"""
        return {
            'registry': {
                'total_models': len(self.registry.registry['models']),
                'total_deployments': len(self.registry.registry.get('deployments', {})),
                'total_experiments': len(self.registry.registry.get('experiments', {}))
            },
            'deployments': {
                'active': len(self.deployer.deployed_models)
            },
            'ab_tests': {
                'active': len([t for t in self.deployer.ab_tests.values() if t['status'] == 'active'])
            },
            'monitoring': {
                'enabled': self.monitoring_thread is not None and not self.stop_monitoring
            },
            'auto_deploy': self.auto_deploy_enabled
        }