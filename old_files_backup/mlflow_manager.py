#!/usr/bin/env python3
"""
MLflow 모델 관리 시스템
- 모델 버전 관리
- 성능 메트릭 추적
- 자동 모델 배포
"""

import os
import json
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

# MLflow 대체 - 간단한 로컬 모델 관리
class SimpleMLflowManager:
    """
    간단한 MLflow 대체 시스템
    - 로컬 파일 시스템 기반 모델 관리
    - 성능 메트릭 추적
    - 모델 버전 관리
    """
    
    def __init__(self, base_path: str = "./models"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        self.experiments_path = self.base_path / "experiments"
        self.experiments_path.mkdir(exist_ok=True)
        
        self.models_path = self.base_path / "saved_models"
        self.models_path.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
    def create_experiment(self, experiment_name: str) -> str:
        """실험 생성"""
        exp_path = self.experiments_path / experiment_name
        exp_path.mkdir(exist_ok=True)
        
        experiment_info = {
            'name': experiment_name,
            'created_at': datetime.now().isoformat(),
            'runs': []
        }
        
        with open(exp_path / 'experiment.json', 'w') as f:
            json.dump(experiment_info, f, indent=2)
            
        self.logger.info(f"실험 생성: {experiment_name}")
        return str(exp_path)
    
    def start_run(self, experiment_name: str, run_name: str) -> str:
        """런 시작"""
        exp_path = self.experiments_path / experiment_name
        if not exp_path.exists():
            self.create_experiment(experiment_name)
            
        run_id = f"{run_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        run_path = exp_path / run_id
        run_path.mkdir(exist_ok=True)
        
        run_info = {
            'run_id': run_id,
            'run_name': run_name,
            'experiment_name': experiment_name,
            'start_time': datetime.now().isoformat(),
            'status': 'RUNNING',
            'params': {},
            'metrics': {},
            'artifacts': []
        }
        
        with open(run_path / 'run.json', 'w') as f:
            json.dump(run_info, f, indent=2)
            
        self.logger.info(f"런 시작: {experiment_name}/{run_name}")
        return run_id
    
    def log_param(self, run_id: str, key: str, value: Any):
        """파라미터 로깅"""
        run_path = self._get_run_path(run_id)
        if not run_path:
            return
            
        with open(run_path / 'run.json', 'r') as f:
            run_info = json.load(f)
            
        run_info['params'][key] = value
        
        with open(run_path / 'run.json', 'w') as f:
            json.dump(run_info, f, indent=2)
    
    def log_metric(self, run_id: str, key: str, value: float, step: int = 0):
        """메트릭 로깅"""
        run_path = self._get_run_path(run_id)
        if not run_path:
            return
            
        with open(run_path / 'run.json', 'r') as f:
            run_info = json.load(f)
            
        if key not in run_info['metrics']:
            run_info['metrics'][key] = []
            
        run_info['metrics'][key].append({
            'value': value,
            'step': step,
            'timestamp': datetime.now().isoformat()
        })
        
        with open(run_path / 'run.json', 'w') as f:
            json.dump(run_info, f, indent=2)
    
    def log_model(self, run_id: str, model, model_name: str):
        """모델 저장"""
        run_path = self._get_run_path(run_id)
        if not run_path:
            return
            
        model_path = run_path / f"{model_name}.pkl"
        
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
            
        # 런 정보 업데이트
        with open(run_path / 'run.json', 'r') as f:
            run_info = json.load(f)
            
        run_info['artifacts'].append({
            'name': model_name,
            'path': str(model_path),
            'type': 'model',
            'created_at': datetime.now().isoformat()
        })
        
        with open(run_path / 'run.json', 'w') as f:
            json.dump(run_info, f, indent=2)
            
        self.logger.info(f"모델 저장: {model_name} -> {model_path}")
    
    def load_model(self, run_id: str, model_name: str):
        """모델 로드"""
        run_path = self._get_run_path(run_id)
        if not run_path:
            return None
            
        model_path = run_path / f"{model_name}.pkl"
        if not model_path.exists():
            self.logger.warning(f"모델 파일 없음: {model_path}")
            return None
            
        with open(model_path, 'rb') as f:
            return pickle.load(f)
    
    def end_run(self, run_id: str, status: str = "FINISHED"):
        """런 종료"""
        run_path = self._get_run_path(run_id)
        if not run_path:
            return
            
        with open(run_path / 'run.json', 'r') as f:
            run_info = json.load(f)
            
        run_info['status'] = status
        run_info['end_time'] = datetime.now().isoformat()
        
        with open(run_path / 'run.json', 'w') as f:
            json.dump(run_info, f, indent=2)
            
        self.logger.info(f"런 종료: {run_id} ({status})")
    
    def get_best_model(self, experiment_name: str, metric_name: str = "sharpe_ratio") -> Optional[Dict]:
        """최고 성능 모델 조회"""
        exp_path = self.experiments_path / experiment_name
        if not exp_path.exists():
            return None
            
        best_run = None
        best_metric = -float('inf')
        
        for run_dir in exp_path.iterdir():
            if run_dir.is_dir() and (run_dir / 'run.json').exists():
                with open(run_dir / 'run.json', 'r') as f:
                    run_info = json.load(f)
                    
                if metric_name in run_info['metrics']:
                    latest_metric = run_info['metrics'][metric_name][-1]['value']
                    if latest_metric > best_metric:
                        best_metric = latest_metric
                        best_run = run_info
                        
        return best_run
    
    def list_experiments(self) -> List[str]:
        """실험 목록 조회"""
        experiments = []
        for exp_dir in self.experiments_path.iterdir():
            if exp_dir.is_dir():
                experiments.append(exp_dir.name)
        return experiments
    
    def list_runs(self, experiment_name: str) -> List[Dict]:
        """런 목록 조회"""
        exp_path = self.experiments_path / experiment_name
        if not exp_path.exists():
            return []
            
        runs = []
        for run_dir in exp_path.iterdir():
            if run_dir.is_dir() and (run_dir / 'run.json').exists():
                with open(run_dir / 'run.json', 'r') as f:
                    run_info = json.load(f)
                    runs.append(run_info)
                    
        return sorted(runs, key=lambda x: x['start_time'], reverse=True)
    
    def _get_run_path(self, run_id: str) -> Optional[Path]:
        """런 경로 조회"""
        for exp_dir in self.experiments_path.iterdir():
            if exp_dir.is_dir():
                run_path = exp_dir / run_id
                if run_path.exists():
                    return run_path
        
        self.logger.warning(f"런을 찾을 수 없음: {run_id}")
        return None
    
    def generate_report(self, experiment_name: str) -> str:
        """실험 리포트 생성"""
        runs = self.list_runs(experiment_name)
        if not runs:
            return f"실험 '{experiment_name}'에 런이 없습니다."
            
        report = f"# 실험 리포트: {experiment_name}\n\n"
        report += f"총 런 수: {len(runs)}\n\n"
        
        # 성능 요약
        metrics_summary = {}
        for run in runs:
            for metric_name, metric_data in run.get('metrics', {}).items():
                if metric_data:
                    latest_value = metric_data[-1]['value']
                    if metric_name not in metrics_summary:
                        metrics_summary[metric_name] = []
                    metrics_summary[metric_name].append(latest_value)
        
        report += "## 성능 메트릭 요약\n"
        for metric_name, values in metrics_summary.items():
            if values:
                report += f"- {metric_name}: 평균 {np.mean(values):.4f}, 최고 {max(values):.4f}\n"
        
        # 최고 성능 런
        best_run = self.get_best_model(experiment_name)
        if best_run:
            report += f"\n## 최고 성능 런\n"
            report += f"- 런 ID: {best_run['run_id']}\n"
            report += f"- 런 이름: {best_run['run_name']}\n"
            
        return report

# 전역 매니저 인스턴스
mlflow_manager = SimpleMLflowManager()

def get_manager() -> SimpleMLflowManager:
    """매니저 인스턴스 반환"""
    return mlflow_manager
